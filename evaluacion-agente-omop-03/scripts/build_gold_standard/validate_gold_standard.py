#!/usr/bin/env python3
"""
validate_gold_standard.py

Validates that all generated Gold Standard YAML files conform to the specification:
- 100% valid YAML syntax.
- Exact schema compliance (required keys, correct types, no obsolete keys).
- BigQuery SQL prefix validity (`bio-med-480108.OMOP_54_A.<table_name>`).
- Multiline scalar styles (>- for question, | for SQL).
- Summarizes complexity and domain distribution.

Usage:
    python3 scripts/build_gold_standard/validate_gold_standard.py [options]

Examples:
    python3 scripts/build_gold_standard/validate_gold_standard.py
    python3 scripts/build_gold_standard/validate_gold_standard.py --eval-dir evaluation/querylibrary
"""

import argparse
import glob
import os
import re
import sys
import yaml


def validate_evaluation_file(fpath: str, source_name: str = "querylibrary") -> list[str]:
    """
    Validates a single evaluation YAML file against Gold Standard requirements.
    Returns a list of error messages (empty if valid).
    """
    fname = os.path.basename(fpath)
    file_id = os.path.splitext(fname)[0]
    errors = []

    with open(fpath, "r", encoding="utf-8") as fp:
        raw_content = fp.read()

    # 1. Syntax check
    try:
        data = yaml.safe_load(raw_content)
    except Exception as exc:
        return [f"{fname}: Error sintáctico YAML: {exc}"]

    if not isinstance(data, dict):
        return [f"{fname}: El contenido YAML raíz debe ser un diccionario/mapeo."]

    # 2. Check id_evaluacion
    expected_id = f"{source_name}_{file_id}"
    if data.get("id_evaluacion") != expected_id:
        errors.append(f"{fname}: 'id_evaluacion' no coincide. Esperado: '{expected_id}', obtenido: '{data.get('id_evaluacion')}'")

    # 3. Check nivel_complejidad
    complexity = data.get("nivel_complejidad")
    if complexity not in ["baja", "intermedia", "compleja"]:
        errors.append(f"{fname}: 'nivel_complejidad' inválido: '{complexity}'. Debe ser baja, intermedia o compleja.")

    # 4. Check domain_main
    domain_main = data.get("domain_main")
    if not domain_main or not isinstance(domain_main, str):
        errors.append(f"{fname}: 'domain_main' debe ser una cadena no vacía.")

    # 5. Check domain_others
    if "domain_others" not in data or not isinstance(data["domain_others"], str):
        errors.append(f"{fname}: 'domain_others' debe ser una cadena (puede ser vacía '').")

    # 6. Check pregunta_lenguaje_natural
    question = data.get("pregunta_lenguaje_natural")
    if not question or not isinstance(question, str):
        errors.append(f"{fname}: 'pregunta_lenguaje_natural' falta o no es texto.")
    elif not re.search(r"^pregunta_lenguaje_natural:\s*>-", raw_content, re.MULTILINE):
        errors.append(f"{fname}: 'pregunta_lenguaje_natural' debe usar estilo folded scalar (>-).")
    else:
        # Check that concept_ids are replaced by clinical names
        if re.search(r"\bconcept_ids?\b", question, re.IGNORECASE):
            errors.append(f"{fname}: 'pregunta_lenguaje_natural' contiene menciones a 'concept_id'. Deben sustituirse por su nombre clínico equivalente.")
        cids_val = data.get("concept_ids_gold_standard", "")
        if cids_val and isinstance(cids_val, str):
            cids_list = [c.strip() for c in cids_val.split(",") if c.strip() and c.strip().isdigit()]
            found_cids = [cid for cid in cids_list if re.search(r"(?<!\d)" + cid + r"(?!\d)", question)]
            if found_cids:
                errors.append(f"{fname}: 'pregunta_lenguaje_natural' contiene identificadores numéricos de concepto ({', '.join(found_cids)}). Deben sustituirse por su nombre clínico equivalente.")

    # 7. Check sql_base_gold_standard
    sql = data.get("sql_base_gold_standard")
    if not sql or not isinstance(sql, str):
        errors.append(f"{fname}: 'sql_base_gold_standard' falta o no es texto.")
    else:
        if not re.search(r"^sql_base_gold_standard:\s*\|", raw_content, re.MULTILINE):
            errors.append(f"{fname}: 'sql_base_gold_standard' debe usar estilo literal scalar (|).")
        if "@cdm." in raw_content or "@vocab." in raw_content:
            errors.append(f"{fname}: contiene referencias no traducidas (@cdm. o @vocab.).")
        if "`bio-med-480108.OMOP_54_A." not in raw_content:
            errors.append(f"{fname}: falta el prefijo BigQuery `bio-med-480108.OMOP_54_A.` en las tablas.")

    # 8. Check obsolete fields
    if "fichero_csv_resultados_gold_standard" in data:
        errors.append(f"{fname}: 'fichero_csv_resultados_gold_standard' es un campo obsoleto y NO debe estar presente.")

    # 9. Check concept_ids_gold_standard
    if "concept_ids_gold_standard" not in data or not isinstance(data["concept_ids_gold_standard"], str):
        errors.append(f"{fname}: 'concept_ids_gold_standard' debe ser una cadena (puede ser vacía '').")

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate Gold Standard YAML evaluations for OMOP CDM 5.4."
    )
    parser.add_argument(
        "--source", "-s",
        default="querylibrary",
        help="Identifier/name of query source to validate (default: 'querylibrary')",
    )
    parser.add_argument(
        "--eval-dir",
        default=None,
        help="Path to evaluation directory containing YAML files (default: evaluation/gold_standard/<source>)",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=201,
        help="Expected number of evaluation files (default: 201)",
    )

    args = parser.parse_args()

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    source = args.source

    if args.eval_dir:
        eval_dir = os.path.abspath(args.eval_dir if os.path.isabs(args.eval_dir) else os.path.join(root_dir, args.eval_dir))
    else:
        eval_dir = os.path.join(root_dir, "evaluation/gold_standard", source)

    if not os.path.exists(eval_dir):
        print(f"ERROR: Evaluation directory '{eval_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    yaml_files = sorted(glob.glob(os.path.join(eval_dir, "*.yaml")))

    print("=" * 80)
    print("VALIDACIÓN DE ARCHIVOS GOLD STANDARD")
    print("=" * 80)
    print(f"Fuente (source):          {source}")
    print(f"Directorio de evaluación: {eval_dir}")
    print(f"Total de archivos YAML:   {len(yaml_files)} (esperados: {args.expected_count})")
    print("-" * 80)

    if args.expected_count and len(yaml_files) != args.expected_count:
        print(f"AVISO: Se esperaban {args.expected_count} archivos pero se encontraron {len(yaml_files)}.")

    total_errors = []
    complexity_counts = {"baja": 0, "intermedia": 0, "compleja": 0}
    domain_counts = {}

    for yf in yaml_files:
        errors = validate_evaluation_file(yf, source_name=source)
        if errors:
            total_errors.extend(errors)
        else:
            with open(yf, "r", encoding="utf-8") as fp:
                d = yaml.safe_load(fp)
            comp = d.get("nivel_complejidad", "desconocida")
            domain = d.get("domain_main", "desconocido")
            complexity_counts[comp] = complexity_counts.get(comp, 0) + 1
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    if total_errors:
        print(f"FALLO DE VALIDACIÓN: Se encontraron {len(total_errors)} errores:")
        for err in total_errors[:25]:
            print(f"  [ERROR] {err}")
        if len(total_errors) > 25:
            print(f"  ... y {len(total_errors) - 25} errores adicionales.")
        print("=" * 80)
        sys.exit(1)
    else:
        print(f"TODOS LOS {len(yaml_files)} ARCHIVOS PASARON LA VALIDACIÓN CON 0 ERRORES.")
        print("-" * 80)
        print("Métricas de los archivos validados:")
        print(f" • Complejidad: {complexity_counts}")
        print(" • Dominio principal (domain_main):")
        for d, c in sorted(domain_counts.items(), key=lambda x: -x[1]):
            print(f"     - {d:22}: {c}")
        print("=" * 80)


if __name__ == "__main__":
    main()
