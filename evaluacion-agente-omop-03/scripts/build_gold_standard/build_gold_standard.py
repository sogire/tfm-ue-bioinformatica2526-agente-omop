#!/usr/bin/env python3
"""
build_gold_standard.py

Builds Gold Standard YAML evaluation benchmark files from OMOP Query Library
markdown documentation files, translating queries to Google BigQuery SQL format
and assigning complexity, domain classifications, and natural language questions.

Usage:
    python3 scripts/build_gold_standard/build_gold_standard.py [options]

Examples:
    # Process all markdown files
    python3 scripts/build_gold_standard/build_gold_standard.py

    # Process only files within a specific subfolder (e.g. condition)
    python3 scripts/build_gold_standard/build_gold_standard.py --subfolder condition

    # Process a single specific evaluation case
    python3 scripts/build_gold_standard/build_gold_standard.py --id C01
"""

import argparse
import glob
import os
import re
import sys
import yaml

# Ensure local import of spanish_questions from same package/directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from spanish_questions import QUESTIONS_ES
except ImportError:
    from scripts.build_gold_standard.spanish_questions import QUESTIONS_ES


FOLDER_MAIN_DOMAIN = {
    "care_site": "care_site",
    "condition": "concept",
    "condition_era": "condition_era",
    "condition_occurence": "condition_occurrence",
    "condition_occurrence_combinations": "condition_era",
    "drug": "concept",
    "drug_cost": "cost",
    "drug_era": "drug_era",
    "drug_exposure": "drug_exposure",
    "general": "concept",
    "obervation_period": "observation_period",
    "observation": "concept",
    "payer_plan": "payer_plan_period",
    "person": "person",
    "procedure": "concept",
}


def classify_complexity(sql: str) -> str:
    """
    Evaluates SQL complexity and assigns: 'baja', 'intermedia', or 'compleja'.

    - baja: Direct queries with basic filters; can be single table or include at least
            one simple table join (e.g., standard lookup join with concept or concept_synonym),
            without complex subqueries, nested logic, or heavy aggregations.
    - intermedia: Moderate queries with multiple joins, subqueries, conditional logic (CASE),
                  GROUP BY, ORDER BY, or string/date manipulations.
    - compleja: Advanced queries with multiple complex joins, nested subqueries, CTEs (WITH),
                window functions, or aggregate computations across large OMOP tables.
    """
    clean = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL)

    has_cte = bool(re.search(r"\bWITH\b", clean, re.IGNORECASE))
    has_window = bool(re.search(r"\bOVER\s*\(", clean, re.IGNORECASE))
    explicit_joins = len(re.findall(r"\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b", clean, re.IGNORECASE))
    table_refs = len(re.findall(r"@(?:cdm|vocab)\.[a-zA-Z0-9_]+", clean, re.IGNORECASE))
    subqueries = len(re.findall(r"\(\s*SELECT\b", clean, re.IGNORECASE))
    has_percentile_or_stats = bool(
        re.search(r"\b(percentile|stddev|stdev|median)\b", clean, re.IGNORECASE)
    ) or ("order_nr" in clean.lower())

    has_group_by = bool(re.search(r"\bGROUP\s+BY\b", clean, re.IGNORECASE))
    has_having = bool(re.search(r"\bHAVING\b", clean, re.IGNORECASE))
    has_case = bool(re.search(r"\bCASE\b", clean, re.IGNORECASE))
    has_union = bool(re.search(r"\bUNION\b", clean, re.IGNORECASE))
    has_date_manip = bool(
        re.search(
            r"\b(DATEDIFF|DATEADD|DATEFROMPARTS|YEAR|MONTH|DAY|CONVERT|EXTRACT|DATE_ADD|DATE_DIFF|GETDATE|SYSDATE)\b",
            clean,
            re.IGNORECASE,
        )
    )

    effective_joins = max(explicit_joins, table_refs - 1 if table_refs > 1 else 0)

    is_trivial_wrapper = False
    if subqueries == 1 and re.search(
        r"FROM\s*\(\s*SELECT\b.*?\)\s*(?:AS\s+)?[a-zA-Z0-9_]+\s*(?:ORDER\s+BY|\s*;?\s*$)",
        clean,
        re.IGNORECASE | re.DOTALL,
    ):
        is_trivial_wrapper = True

    if (
        has_cte
        or has_window
        or effective_joins >= 3
        or subqueries >= 2
        or (effective_joins >= 2 and subqueries >= 1)
        or has_percentile_or_stats
    ):
        return "compleja"
    elif (
        effective_joins >= 2
        or (subqueries >= 1 and not is_trivial_wrapper)
        or has_having
        or has_union
        or has_group_by
        or has_case
        or (effective_joins == 1 and has_date_manip)
    ):
        return "intermedia"
    else:
        return "baja"


def extract_domains(sql: str, folder: str) -> tuple[str, str]:
    """
    Extracts the main OMOP table domain and secondary joined domains.
    Returns (domain_main, domain_others_as_comma_separated_string).
    """
    raw_tables = [t.lower() for t in re.findall(r"@(?:cdm|vocab)\.([a-zA-Z0-9_]+)", sql, re.IGNORECASE)]
    tables = list(dict.fromkeys(raw_tables))

    expected_main = FOLDER_MAIN_DOMAIN.get(folder, tables[0] if tables else "")
    if expected_main in tables:
        main_domain = expected_main
        other_domains = [t for t in tables if t != main_domain]
    elif tables:
        main_domain = tables[0]
        other_domains = tables[1:]
    else:
        main_domain = ""
        other_domains = []

    return main_domain, ", ".join(other_domains)


def extract_concept_ids(sql: str) -> list[str]:
    """
    Extracts explicit concept ID integers hardcoded in WHERE or JOIN clauses.
    """
    clean = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL)

    found = []
    # Pattern 1: concept_id IN (123, 456)
    for match in re.finditer(
        r"([a-zA-Z0-9_]*concept_id[a-zA-Z0-9_]*)\s+(?:NOT\s+)?IN\s*\(([^)]+)\)", clean, re.IGNORECASE
    ):
        nums = re.findall(r"\b([0-9]{3,})\b", match.group(2))
        for n in nums:
            if n not in found:
                found.append(n)

    # Pattern 2: concept_id = 123456
    for match in re.finditer(
        r"([a-zA-Z0-9_]*concept_id[a-zA-Z0-9_]*)\s*=\s*([0-9]{3,})\b", clean, re.IGNORECASE
    ):
        n = match.group(2)
        if n not in found:
            found.append(n)

    # Pattern 3: 123456 = concept_id
    for match in re.finditer(
        r"\b([0-9]{3,})\s*=\s*([a-zA-Z0-9_]*concept_id[a-zA-Z0-9_]*)", clean, re.IGNORECASE
    ):
        n = match.group(1)
        if n not in found:
            found.append(n)

    # Pattern 4: BETWEEN <num1> AND <num2>
    for match in re.finditer(
        r"([a-zA-Z0-9_]*concept_id[a-zA-Z0-9_]*)\s+BETWEEN\s+(\b[0-9]{3,}\b)\s+AND\s+(\b[0-9]{3,}\b)",
        clean,
        re.IGNORECASE,
    ):
        for n in [match.group(2), match.group(3)]:
            if n not in found:
                found.append(n)

    return found


def translate_sql_to_bigquery(sql: str) -> str:
    """
    Translates @cdm.<tbl> and @vocab.<tbl> to `bio-med-480108.OMOP_54_A.<tbl>`.
    Translates dialect-specific date math (e.g. current_date() + 1 year) to BigQuery syntax.
    """
    def repl(m):
        tbl = m.group(1).lower()
        return f"`bio-med-480108.OMOP_54_A.{tbl}`"

    sql = re.sub(r"@(?:cdm|vocab)\.([a-zA-Z0-9_]+)", repl, sql, flags=re.IGNORECASE)
    sql = re.sub(r"current_date\(\)\s*\+\s*1\s+year", "DATE_ADD(CURRENT_DATE(), INTERVAL 1 YEAR)", sql, flags=re.IGNORECASE)
    return sql


def format_yaml(
    eval_id: str,
    complexity: str,
    domain_main: str,
    domain_others: str,
    question_es: str,
    translated_sql: str,
    concept_ids_str: str,
) -> str:
    """
    Formats the evaluation case as a clean YAML document following the template.
    Uses folded scalar (>-) for question and literal scalar (|) for SQL.
    """
    question_indented = "  " + question_es.strip()

    sql_lines = translated_sql.strip().split("\n")
    indented_sql_lines = []
    for line in sql_lines:
        clean_line = line.replace("\t", "  ")
        indented_sql_lines.append(f"  {clean_line}" if clean_line.strip() else "")
    indented_sql = "\n".join(indented_sql_lines)

    yaml_content = f"""id_evaluacion: "{eval_id}"
nivel_complejidad: "{complexity}"
domain_main: "{domain_main}"
domain_others: "{domain_others}"
pregunta_lenguaje_natural: >-
{question_indented}
sql_base_gold_standard: |
{indented_sql}
concept_ids_gold_standard: "{concept_ids_str}"
"""
    return yaml_content


def process_file(
    fpath: str,
    output_dir: str,
    source_name: str = "querylibrary",
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[str, str, str]:
    """
    Processes a single markdown file and outputs the corresponding YAML.
    Returns (file_id, complexity, domain_main).
    """
    fname = os.path.basename(fpath)
    file_id = os.path.splitext(fname)[0]
    folder = os.path.basename(os.path.dirname(fpath))

    with open(fpath, "r", encoding="utf-8") as fp:
        content = fp.read()

    sql_match = re.search(r"```(?:sql)?\s*\n(.*?)```", content, re.DOTALL | re.IGNORECASE)
    if not sql_match:
        raise ValueError(f"No SQL block found in {fpath}")

    raw_sql = sql_match.group(1).strip()
    eval_id = f"{source_name}_{file_id}"

    if file_id in QUESTIONS_ES:
        question_es = QUESTIONS_ES[file_id]
    else:
        # Fallback: extract title or description from markdown header
        header_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        question_es = header_match.group(1).strip() if header_match else f"Consulta clínica sobre {file_id}"

    complexity = classify_complexity(raw_sql)
    domain_main, domain_others = extract_domains(raw_sql, folder)
    concept_ids = extract_concept_ids(raw_sql)
    concept_ids_str = ", ".join(concept_ids)
    translated_sql = translate_sql_to_bigquery(raw_sql)

    yaml_content = format_yaml(
        eval_id=eval_id,
        complexity=complexity,
        domain_main=domain_main,
        domain_others=domain_others,
        question_es=question_es,
        translated_sql=translated_sql,
        concept_ids_str=concept_ids_str,
    )

    # Validate syntax with safe_load
    parsed = yaml.safe_load(yaml_content)
    assert parsed["id_evaluacion"] == eval_id
    assert parsed["nivel_complejidad"] == complexity
    assert parsed["domain_main"] == domain_main
    assert parsed["domain_others"] == domain_others
    assert "fichero_csv_resultados_gold_standard" not in parsed

    if not dry_run:
        out_fpath = os.path.join(output_dir, f"{file_id}.yaml")
        with open(out_fpath, "w", encoding="utf-8") as out_fp:
            out_fp.write(yaml_content)

    if verbose:
        print(f" -> {file_id:8} | Complejidad: {complexity:10} | Dominio: {domain_main:20}")

    return file_id, complexity, domain_main


def main():
    parser = argparse.ArgumentParser(
        description="Build Gold Standard YAML evaluations from OMOP Query Library markdown files."
    )
    parser.add_argument(
        "--source", "-s",
        default="querylibrary",
        help="Identifier/name of query source to process (default: 'querylibrary')",
    )
    parser.add_argument(
        "--source-dir",
        default=None,
        help="Path to root source directory containing query markdown files (default: evaluation/sources/<source>)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Path to output directory for YAML evaluation files (default: evaluation/gold_standard/<source>)",
    )
    parser.add_argument(
        "--subfolder",
        default=None,
        help="Filter execution to a specific subfolder (e.g. 'condition', 'drug_exposure')",
    )
    parser.add_argument(
        "--id",
        default=None,
        help="Filter execution to a single file ID (e.g. 'C01', 'CO05')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate without writing YAML files to disk",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Display detailed per-file output during execution",
    )

    args = parser.parse_args()

    # Determine base directory
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    source = args.source

    if args.source_dir:
        source_dir = os.path.abspath(args.source_dir if os.path.isabs(args.source_dir) else os.path.join(root_dir, args.source_dir))
    else:
        source_dir = os.path.join(root_dir, "evaluation/sources", source)

    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir if os.path.isabs(args.output_dir) else os.path.join(root_dir, args.output_dir))
    else:
        output_dir = os.path.join(root_dir, "evaluation/gold_standard", source)

    if not os.path.exists(source_dir):
        print(f"ERROR: Source directory '{source_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    if args.id:
        pattern = os.path.join(source_dir, f"**/{args.id}.md")
    elif args.subfolder:
        pattern = os.path.join(source_dir, args.subfolder, "*.md")
    else:
        pattern = os.path.join(source_dir, "**/*.md")

    files = sorted(glob.glob(pattern, recursive=True))

    if not files:
        print(f"No markdown files found matching pattern: {pattern}")
        sys.exit(1)

    print("=" * 80)
    print("CONSTRUCCIÓN DE EVALUACIONES GOLD STANDARD (OMOP CDM 5.4)")
    print("=" * 80)
    print(f"Fuente (source):    {source}")
    print(f"Directorio fuente:  {source_dir}")
    print(f"Directorio salida:  {output_dir}")
    print(f"Archivos a tratar:  {len(files)}")
    if args.dry_run:
        print("MODO: DRY-RUN (no se escribirán cambios a disco)")
    print("-" * 80)

    complexity_counts = {"baja": 0, "intermedia": 0, "compleja": 0}
    domain_counts = {}

    for fpath in files:
        file_id, complexity, domain_main = process_file(
            fpath=fpath,
            output_dir=output_dir,
            source_name=source,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        complexity_counts[complexity] += 1
        domain_counts[domain_main] = domain_counts.get(domain_main, 0) + 1

    print("-" * 80)
    print(f"PROCESADOS CON ÉXITO: {len(files)} archivos.")
    print(f"Distribución de complejidad: {complexity_counts}")
    print("Distribución de dominio principal (domain_main):")
    for d, c in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"  • {d:22}: {c}")
    print("=" * 80)


if __name__ == "__main__":
    main()
