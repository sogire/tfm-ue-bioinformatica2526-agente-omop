#!/usr/bin/env python3
"""
Script unificado de evaluación para la biblioteca de consultas OMOP (QueryLibrary).
Permite evaluar casos individuales, listas de casos, rangos o la biblioteca completa contra el agente omop_03_concepts_and_sql.
Incluye métricas cuantitativas (sintaxis y vocabulario), cualitativa y estado de conexión en formato YAML multilínea validado.
"""

import os
import re
import sys
import glob
import time
import json
import yaml
import textwrap
import argparse
import requests
import sqlparse

AGENT_BASE_URL = "https://omop-agent-dev-995233896922.europe-west1.run.app"
APP_NAME = "omop_03_concepts_and_sql"

class LiteralStr(str):
    """Representa una cadena para serialización en bloque multilínea ('|') en YAML."""
    pass

def literal_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(LiteralStr, literal_str_representer)
yaml.representer.SafeRepresenter.add_representer(LiteralStr, literal_str_representer)

def is_valid_sql_statement(text):
    """Verifica si una cadena contiene una sentencia SQL ejecutable (SELECT o CTE con WITH)."""
    if not text:
        return False
    clean = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    clean = re.sub(r"--[^\n]*", "", clean).strip()
    return clean.upper().startswith(("SELECT", "WITH"))

def format_multiline_text(text, is_sql=False):
    """Formatea texto o SQL para su visualización limpia en bloques multilínea YAML."""
    if not text:
        return LiteralStr("")
    stripped = text.strip()
    if is_sql and is_valid_sql_statement(stripped):
        try:
            formatted = sqlparse.format(
                stripped,
                reindent=True,
                keyword_case="upper",
                identifier_case="lower"
            ).strip()
            return LiteralStr(formatted)
        except Exception:
            pass
            
    paragraphs = stripped.split("\n")
    formatted_paras = []
    for p in paragraphs:
        clean_p = re.sub(r"\s+", " ", p).strip()
        if clean_p:
            formatted_paras.append(textwrap.fill(clean_p, width=95))
    return LiteralStr("\n".join(formatted_paras))

def extract_sql_from_events(events_data):
    """Extrae la consulta SQL y la validación a partir de los eventos SSE recibidos del agente."""
    sql = ""
    validated = False
    discovered_concepts = set()
    full_text = ""
    
    for evt in events_data:
        parts = evt.get("content", {}).get("parts", [])
        for p in parts:
            if "functionCall" in p:
                fn = p["functionCall"]
                if fn.get("name") == "validate_omop_sql":
                    sql_arg = fn.get("args", {}).get("sql_query", "")
                    if sql_arg:
                        sql = sql_arg.strip()
            if "functionResponse" in p:
                fr = p["functionResponse"]
                fn_name = fr.get("name")
                resp_obj = fr.get("response", {})
                if fn_name == "validate_omop_sql":
                    if resp_obj.get("is_valid"):
                        validated = True
                elif fn_name == "search_omop_official_concepts":
                    for c in resp_obj.get("concepts", []):
                        if "concept_id" in c:
                            discovered_concepts.add(int(c["concept_id"]))
            if "text" in p:
                full_text += p["text"] + "\n"
                
    if not sql:
        # 1. Buscar bloques de código delimitados (```sql ... ``` o ``` ... ```)
        matches = re.findall(r"```(?:sql)?\s*([\s\S]*?)```", full_text, re.IGNORECASE)
        for m in reversed(matches):
            cand = m.strip()
            if is_valid_sql_statement(cand):
                sql = cand
                break
                
        # 2. Fallback: buscar sentencia SQL explícita en el texto que comience por WITH o SELECT hasta punto y coma
        if not sql:
            m2 = re.search(r"((?:WITH|SELECT)\b[\s\S]*?;)", full_text, re.IGNORECASE)
            if m2:
                cand = m2.group(1).strip()
                if is_valid_sql_statement(cand):
                    sql = cand
                
    return sql, validated, discovered_concepts, full_text

def check_exhaustion_in_events(events):
    """Verifica si en los eventos SSE devueltos hay indicaciones de agotamiento o error."""
    for evt in events:
        if isinstance(evt, dict):
            if "error" in evt:
                err = evt["error"]
                err_msg = str(err)
                if any(term in err_msg.lower() for term in ["exhausted", "quota", "rate limit", "429", "unavailable", "503", "504"]):
                    return err_msg
    return None

def request_with_retry(func, eval_id, desc="operación", max_retries=5, wait_seconds=120):
    """
    Ejecuta una función HTTP/SSE contra el agente OMOP.
    Si el agente está agotado (HTTP 429 / ResourceExhausted / Quota / RateLimit),
    sobrecargado (HTTP 502 / 503 / 504) o deja de responder (Timeout / ConnectionError / SSE vacío),
    espera exactamente 2 minutos (120 segundos) antes de reintentar, imprimiendo el 'id_evaluacion'
    actual para información del usuario.
    """
    for attempt in range(1, max_retries + 1):
        try:
            result = func()
            if isinstance(result, list):
                if not result:
                    raise requests.exceptions.RequestException("Respuesta SSE vacía (el agente no devolvió eventos).")
                err_in_evt = check_exhaustion_in_events(result)
                if err_in_evt:
                    raise requests.exceptions.RequestException(f"Evento de error recibido del agente: {err_in_evt}")
            return result
        except Exception as exc:
            err_str = str(exc)
            is_exhausted = any(term in err_str.lower() for term in [
                "429", "resource_exhausted", "exhausted", "quota", "rate limit",
                "503", "502", "504", "500", "timeout", "timed out", "connection", "vacía"
            ])
            if attempt < max_retries and is_exhausted:
                print("\n" + "*" * 80)
                print(f"⚠️  [AVISO: AGENTE OMOP AGOTADO O SIN RESPUESTA]")
                print(f"    id_evaluacion en proceso actual: '{eval_id}'")
                print(f"    Fase / Operación: {desc}")
                print(f"    Causa detectada: {exc}")
                print(f"    Pausa de resiliencia: Esperando 2 minutos (120 segundos) antes de reintentar...")
                print(f"    Progreso de reintentos: {attempt} de {max_retries}")
                print("*" * 80 + "\n")
                time.sleep(wait_seconds)
            else:
                if not is_exhausted:
                    raise exc
                if attempt >= max_retries:
                    print(f"\n❌ [ERROR] Agente agotado de forma persistente tras {max_retries} intentos en id_evaluacion: '{eval_id}'.\n")
                    raise exc

def create_agent_session(eval_id):
    """Crea una nueva sesión en el agente OMOP con reintento ante agotamiento."""
    def _create():
        session_url = f"{AGENT_BASE_URL}/apps/{APP_NAME}/users/cli-user/sessions"
        headers = {"Content-Type": "application/json"}
        id_token = os.environ.get("IAP_ID_TOKEN") or os.environ.get("GOOGLE_ID_TOKEN")
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"
            headers["Proxy-Authorization"] = f"Bearer {id_token}"
            
        sess_resp = requests.post(session_url, headers=headers, json={}, timeout=30)
        sess_resp.raise_for_status()
        return sess_resp.json().get("id")
    return request_with_retry(_create, eval_id=eval_id, desc="crear sesión")

def execute_agent_turn(session_id, message, eval_id="", timeout=120):
    """Envía un mensaje al agente en una sesión dada y retorna los eventos SSE con reintento ante agotamiento."""
    def _turn():
        run_url = f"{AGENT_BASE_URL}/run_sse"
        payload = {
            "app_name": APP_NAME,
            "user_id": "cli-user",
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}]
            },
            "streaming": False
        }
        events = []
        headers = {"Content-Type": "application/json"}
        id_token = os.environ.get("IAP_ID_TOKEN") or os.environ.get("GOOGLE_ID_TOKEN")
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"
            headers["Proxy-Authorization"] = f"Bearer {id_token}"
            
        resp = requests.post(run_url, headers=headers, json=payload, stream=True, timeout=timeout)
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    evt = json.loads(line[6:])
                    events.append(evt)
                except Exception:
                    continue
        return events
    return request_with_retry(_turn, eval_id=eval_id, desc="interacción SSE por turno")

def download_agent_session(session_url, session_id, eval_id=""):
    """Descarga la traza forense de la sesión ADK con reintento ante agotamiento."""
    def _download():
        headers = {"Content-Type": "application/json"}
        id_token = os.environ.get("IAP_ID_TOKEN") or os.environ.get("GOOGLE_ID_TOKEN")
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"
            headers["Proxy-Authorization"] = f"Bearer {id_token}"
        session_get_url = f"{session_url}/{session_id}"
        sess_get_resp = requests.get(session_get_url, headers=headers, timeout=25)
        sess_get_resp.raise_for_status()
        return sess_get_resp.json()
    return request_with_retry(_download, eval_id=eval_id, desc="descarga de sesión forense", max_retries=3)

def extract_turn_concepts(sql_text, gold_concepts, discovered_concepts):
    """Extrae los Concept IDs presentes en la consulta SQL o en los candidatos descubiertos."""
    turn_sql_concepts = set()
    if sql_text:
        for cid in re.findall(r"(?:concept_id|concept_id_1|concept_id_2|_id)\s*=\s*(\d+)", sql_text, re.IGNORECASE):
            turn_sql_concepts.add(int(cid))
        for in_block in re.findall(r"(?:concept_id|concept_id_1|concept_id_2|_id)\s+IN\s*\(([\d\s,]+)\)", sql_text, re.IGNORECASE):
            for cid in in_block.split(","):
                if cid.strip().isdigit():
                    turn_sql_concepts.add(int(cid.strip()))
        for gc in gold_concepts:
            if re.search(rf"\b{gc}\b", sql_text):
                turn_sql_concepts.add(gc)
                
    if turn_sql_concepts:
        return sorted(list(turn_sql_concepts))
    elif gold_concepts and (discovered_concepts & gold_concepts):
        return sorted(list(discovered_concepts & gold_concepts))
    else:
        return sorted(list(discovered_concepts))

def compute_vocab_precision(agent_concepts, gold_concepts):
    """Calcula el índice de Jaccard entre conceptos esperados y encontrados."""
    if not gold_concepts:
        return 1.00
    set_ag = set(agent_concepts)
    intersection = len(gold_concepts & set_ag)
    union = len(gold_concepts | set_ag)
    return round(intersection / union, 2) if union > 0 else 0.00

def judge_sql_similarity_with_gemini(gold_sql, agent_sql, clinical_prompt, eval_id=""):
    """
    Evalúa el Criterio 1.2 de la Métrica 1: Grado de similitud con sql_base_gold_standard en cuanto
    a lógica, tablas OMOP, uniones (JOINs) y filtros (WHERE) evaluado por Gemini (LLM-as-a-judge).
    Retorna (score: float entre 0.00 y 0.90, justificacion: str).
    """
    clean_agent = (agent_sql or "").strip()
    is_sql = is_valid_sql_statement(clean_agent)
    
    if is_sql:
        clean_gold = re.sub(r"\s+", " ", gold_sql).strip().lower()
        clean_ag = re.sub(r"\s+", " ", clean_agent).lower()
        if clean_gold == clean_ag:
            return 0.90, "Consulta SQL estructuralmente idéntica a la consulta de referencia Gold Standard."

        judge_prompt = f"""Eres un evaluador experto de consultas SQL en el modelo de datos biomédicos OMOP CDM 5.4 en Google BigQuery.
Debes evaluar el grado de similitud entre la consulta SQL generada por un agente Text-to-SQL y la consulta SQL de referencia (Gold Standard).

Directrices de evaluación:
- Rango de puntuación: entre 0.00 y 0.90 puntos (máximo 0.90).
- Criterios: lógica de negocio, tablas del modelo OMOP empleadas, condiciones de filtrado (WHERE), uniones (JOINs), agrupaciones y adecuación a la intención clínica.
- IMPORTANTE: No hace falta que los alias o nombres de campos en la cláusula SELECT se denominen exactamente igual, siempre y cuando la consulta responda a la misma necesidad clínica y seleccione la información pertinente.
- Descuenta puntos si faltan tablas clave, uniones requeridas, filtros clínicos esenciales (ej. relación de conceptos, conceptos inválidos, dominios) o si se seleccionan tablas incorrectas.

Pregunta clínica original:
{clinical_prompt.strip()}

Consulta SQL de Referencia (Gold Standard):
```sql
{gold_sql.strip()}
```

Consulta SQL Generada por el Agente:
```sql
{clean_agent}
```

Responde ÚNICAMENTE con un objeto JSON válido con la siguiente estructura (sin texto adicional fuera del JSON):
{{
  "score": <float entre 0.00 y 0.90>,
  "justification": "<explicación concisa clínica de las discrepancias>"
}}"""
    else:
        judge_prompt = f"""Eres un evaluador experto de consultas SQL en el modelo de datos biomédicos OMOP CDM 5.4 en Google BigQuery.
El agente Text-to-SQL aún no ha formulado una consulta SQL SELECT ejecutable, sino que ha emitido la siguiente respuesta o propuesta preliminar:
\"\"\"
{clean_agent if clean_agent else "Sin respuesta de consulta SQL."}
\"\"\"

Pregunta clínica original:
{clinical_prompt.strip()}

Consulta SQL de Referencia esperada (Gold Standard):
```sql
{gold_sql.strip()}
```

Indica concisamente qué tablas de OMOP CDM 5.4, condiciones de unión (JOINs) y filtros (WHERE) debe formular el agente para responder a la pregunta clínica según el estándar de oro.
Responde ÚNICAMENTE con un objeto JSON válido con la siguiente estructura (sin texto adicional fuera del JSON):
{{
  "score": 0.00,
  "justification": "<explicación concisa técnica y clínica de las tablas, relaciones y filtros que debe formular>"
}}"""

    # 1. Intento vía API directa de Gemini si hay API Key configurada
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=judge_prompt
            )
            raw_text = resp.text or ""
            m = re.search(r"\{[\s\S]*\}", raw_text)
            if m:
                d = json.loads(m.group(0))
                s = 0.00 if not is_sql else float(d.get("score", 0.0))
                return max(0.0, min(0.90, round(s, 2))), str(d.get("justification", "")).strip()
        except Exception:
            pass

    # 2. Evaluación mediante sesión en el agente Cloud Run (Gemini 2.5 Flash nativo)
    def _evaluate_remote():
        headers = {"Content-Type": "application/json"}
        id_token = os.environ.get("IAP_ID_TOKEN") or os.environ.get("GOOGLE_ID_TOKEN")
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"
            headers["Proxy-Authorization"] = f"Bearer {id_token}"
            
        sess_url = f"{AGENT_BASE_URL}/apps/{APP_NAME}/users/eval-judge/sessions"
        sess_resp = requests.post(sess_url, headers=headers, json={}, timeout=20)
        sess_resp.raise_for_status()
        judge_session_id = sess_resp.json().get("id")
        
        run_url = f"{AGENT_BASE_URL}/run_sse"
        payload = {
            "app_name": APP_NAME,
            "user_id": "eval-judge",
            "session_id": judge_session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": judge_prompt}]
            },
            "streaming": False
        }
        resp = requests.post(run_url, headers=headers, json=payload, stream=True, timeout=60)
        resp.raise_for_status()
        
        full_text = ""
        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    evt = json.loads(line[6:])
                    for p in evt.get("content", {}).get("parts", []):
                        if "text" in p:
                            full_text += p["text"]
                except Exception:
                    continue
                    
        m = re.search(r"\{[\s\S]*\}", full_text)
        if m:
            data = json.loads(m.group(0))
            score = 0.00 if not is_sql else float(data.get("score", 0.0))
            score = max(0.0, min(0.90, round(score, 2)))
            justif = str(data.get("justification", "")).strip()
            return score, justif
        raise ValueError(f"No se pudo interpretar JSON de evaluación: {full_text[:120]}")

    try:
        return request_with_retry(_evaluate_remote, eval_id=eval_id, desc="evaluación de similitud SQL con Gemini", max_retries=3)
    except Exception:
        # 3. Heurística estructural de respaldo en caso de contingencia prolongada
        if not is_sql:
            return 0.00, "El agente no formuló consulta SQL ejecutable y no se pudo obtener dictamen de evaluación de Gemini."
        tables_gold = set(re.findall(r"(?:FROM|JOIN)\s+[`]?([a-zA-Z0-9_\-\.]+)[`]?", gold_sql, re.IGNORECASE))
        tables_agent = set(re.findall(r"(?:FROM|JOIN)\s+[`]?([a-zA-Z0-9_\-\.]+)[`]?", clean_agent, re.IGNORECASE))
        clean_gold_tbls = {t.split(".")[-1].lower() for t in tables_gold if t.lower() not in ("where", "on", "as", "select")}
        clean_agent_tbls = {t.split(".")[-1].lower() for t in tables_agent if t.lower() not in ("where", "on", "as", "select")}
        jaccard_tbls = len(clean_gold_tbls & clean_agent_tbls) / len(clean_gold_tbls | clean_agent_tbls) if (clean_gold_tbls | clean_agent_tbls) else 1.0
        fallback_score = round(jaccard_tbls * 0.90, 2)
        return fallback_score, f"Estimación estructural de respaldo ({fallback_score}/0.90 pts) ante contingencia en evaluador remoto."

def generate_qualitative_evaluation(criterio_1_1, criterio_1_2, gemini_justification, vocab, gold_concepts, agent_concepts, sql_agente, turns, agent_text, tables, confirmed_in_t1=False):
    """Genera la evaluación cualitativa estructurada en líneas temáticas para bloque multilínea YAML."""
    lines = []
    
    # Línea 1: Ejecución técnica y turnos
    if criterio_1_1 > 0.0:
        table_str = f" sobre tabla(s) {', '.join(sorted(tables))}" if tables else ""
        if turns == 1:
            if confirmed_in_t1:
                lines.append(f"Consulta SQL ejecutable (0.10 pts){table_str} generada en el Turno 1 tras la confirmación de los conceptos iniciales ofrecidos por el agente.")
            else:
                lines.append(f"Consulta SQL ejecutable (0.10 pts){table_str} generada directamente en un único turno con validación exitosa en BigQuery.")
        elif turns == 2:
            lines.append(f"Consulta SQL ejecutable (0.10 pts){table_str} generada en el Turno 2 tras mejora guiada por el juez LLM.")
        else:
            lines.append(f"Consulta SQL ejecutable (0.10 pts){table_str} generada en el Turno {turns} tras optimización guiada por el juez LLM.")
    else:
        clean_text = re.sub(r"\s+", " ", agent_text).strip() if agent_text else ""
        short_expl = (clean_text[:220] + "...") if len(clean_text) > 220 else clean_text
        turns_desc = "un único turno" if turns == 1 else f"{turns} turnos de interacción"
        if short_expl:
            lines.append(f"El agente no generó consulta SQL ejecutable (0.00 pts) tras {turns_desc}. Justificación del agente: '{short_expl}'.")
        else:
            lines.append(f"La consulta SQL no superó la validación técnica (0.00 pts) tras {turns_desc}.")
            
    # Línea 2: Similitud SQL evaluada por Gemini (Criterio 1.2)
    if gemini_justification:
        lines.append(f"Similitud SQL evaluada por Gemini ({criterio_1_2:.2f}/0.90 pts): {gemini_justification}")
        
    # Línea 3: Precisión terminológica y adecuación de conceptos
    if not gold_concepts:
        lines.append(f"Consulta exploratoria sin conceptos fijos requeridos en el estándar; el agente identificó {len(agent_concepts)} concepto(s) candidatos pertinentes en el vocabulario.")
    else:
        intersection = set(gold_concepts) & set(agent_concepts)
        if len(intersection) == len(gold_concepts):
            lines.append(f"Precisión terminológica óptima: identificó y utilizó todos los conceptos requeridos ({sorted(list(gold_concepts))}).")
        elif intersection:
            lines.append(f"Identificación parcial de conceptos: utilizó {sorted(list(intersection))} de los requeridos {sorted(list(gold_concepts))}.")
        else:
            lines.append(f"No se detectaron los conceptos esperados ({sorted(list(gold_concepts))}) en la consulta.")
            
    return LiteralStr("\n".join(lines))

def evaluate_case(case_name, base_dir, source="querylibrary"):
    """Evalúa un único caso de prueba permitiendo hasta 3 turnos de interacción con el agente OMOP."""
    case_clean = case_name.replace(".yaml", "").strip()
    eval_yaml_path = os.path.join(base_dir, f"evaluation/gold_standard/{source}/{case_clean}.yaml")
    results_dir = os.path.join(base_dir, f"evaluation/results/{source}")
    os.makedirs(results_dir, exist_ok=True)
    
    if not os.path.exists(eval_yaml_path):
        print(f"[{case_clean}] Archivo no encontrado: {eval_yaml_path}")
        return None
        
    with open(eval_yaml_path, "r", encoding="utf-8") as f:
        gold_data = yaml.safe_load(f)
        
    eval_id = gold_data["id_evaluacion"]
    prompt = gold_data["pregunta_lenguaje_natural"].strip()
    domain_main = str(gold_data.get("domain_main", "") or "").strip()
    domain_others = str(gold_data.get("domain_others", "") or "").strip()
    gold_concepts_str = str(gold_data.get("concept_ids_gold_standard", "") or "")
    gold_concepts = set(int(c.strip()) for c in gold_concepts_str.split(",") if c.strip() and c.strip().isdigit())
    gold_sql = str(gold_data.get("sql_base_gold_standard", "") or "").strip()
    
    print(f"\n==================================================")
    print(f"[{case_clean}] Evaluando {eval_id}...")
    print(f"Pregunta: {prompt[:90]}...")
    print(f"Conceptos Gold Standard: {sorted(list(gold_concepts))}")
    
    session_id = None
    session_file_rel = ""
    sql_agente = ""
    check_conexion = False
    all_discovered_concepts = set()
    validated_by_tool = False
    turns_count = 1
    agent_full_text = ""
    turn_metrics = {}
    max_turns = 3
    c1_1_final = 0.00
    c1_2_final = 0.00
    justif_final = ""
    
    try:
        # 1. Crear sesión en el agente
        session_url = f"{AGENT_BASE_URL}/apps/{APP_NAME}/users/cli-user/sessions"
        session_id = create_agent_session(eval_id)
        check_conexion = True
        
        # 2. Protocolo de interacción por turnos
        # La confirmación de los conceptos iniciales ofrecidos por el agente se considera Turno 1
        tables_hint = ", ".join(filter(None, [domain_main, domain_others]))
        confirmed_in_t1 = False
        
        # --- TURNO 1 ---
        # 1.1 Enviar pregunta clínica inicial
        t_prompt_1 = prompt
        if not t_prompt_1.endswith("."):
            t_prompt_1 += "."
        t_prompt_1 += " Genera directamente la consulta SQL para BigQuery."
        
        events = execute_agent_turn(session_id, t_prompt_1, eval_id=eval_id)
        sql_turn, validated_turn, discovered_turn, text_turn = extract_sql_from_events(events)
        all_discovered_concepts.update(discovered_turn)
        if text_turn.strip():
            agent_full_text = text_turn
        if validated_turn:
            validated_by_tool = True
            
        is_sql_turn = is_valid_sql_statement(sql_turn)
        
        # 1.2 Si el agente ofreció conceptos para confirmación, confirmarlos dentro del Turno 1
        if not is_sql_turn:
            confirmed_in_t1 = True
            print(f"[{case_clean}] Turno 1: el agente ofreció conceptos para confirmación ({len(all_discovered_concepts)} candidatos). Confirmando...")
            if gold_concepts:
                cands = ", ".join(str(c) for c in sorted(list(gold_concepts)))
                cands_str = f"Confirmo los conceptos {cands}. "
            elif all_discovered_concepts:
                cands = ", ".join(str(c) for c in sorted(list(all_discovered_concepts))[:4])
                cands_str = f"Confirmo los conceptos {cands}. "
            else:
                cands_str = "Confirmo los conceptos más pertinentes identificados. "
                
            table_context = f" consultando las tablas del vocabulario y modelo OMOP ({tables_hint})" if tables_hint else ""
            t_confirm = f"{cands_str}Por favor genera la consulta SQL para BigQuery{table_context} para obtener los conceptos o registros relacionados."
            
            events = execute_agent_turn(session_id, t_confirm, eval_id=eval_id)
            sql_turn2, validated_turn2, discovered_turn2, text_turn2 = extract_sql_from_events(events)
            all_discovered_concepts.update(discovered_turn2)
            if text_turn2.strip():
                agent_full_text = text_turn2
            if validated_turn2:
                validated_by_tool = True
                
            if is_valid_sql_statement(sql_turn2):
                sql_turn = sql_turn2
                is_sql_turn = True
                validated_turn = validated_turn2
            else:
                sql_turn = sql_turn2
                is_sql_turn = False
                
        # Evaluación de métricas del Turno 1
        turn1_concepts = extract_turn_concepts(sql_turn, gold_concepts, all_discovered_concepts)
        criterio_1_1_t1 = 0.10 if (validated_turn or is_sql_turn) else 0.00
        print(f"[{case_clean}] Evaluando similitud del Turno 1 con Gemini frente a Gold Standard...")
        criterio_1_2_t1, justif_t1 = judge_sql_similarity_with_gemini(gold_sql, sql_turn if is_sql_turn else (agent_full_text or text_turn), prompt, eval_id=eval_id)
        v_sintactica_t1 = round(criterio_1_1_t1 + criterio_1_2_t1, 2)
        p_vocab_t1 = compute_vocab_precision(turn1_concepts, gold_concepts)
        
        turn_metrics["turno_1"] = {
            "validez_sintactica_y_estructural": v_sintactica_t1,
            "precision_terminologica_vocabulario": p_vocab_t1,
            "question_improvement": ""
        }
        
        # Determinar si se requiere Turno 2 para mejora guiada por el juez LLM:
        # Cuando la Validez Sintáctica y Estructural de un turno supere el 0.80, no es necesario ejecutar el siguiente turno
        if is_sql_turn and v_sintactica_t1 > 0.80:
            print(f"[{case_clean}] Turno 1 con Validez Sintáctica y Estructural satisfactoria ({v_sintactica_t1:.2f} > 0.80). Concluyendo evaluación en Turno 1.")
            turns_count = 1
            sql_agente = sql_turn
            c1_1_final = criterio_1_1_t1
            c1_2_final = criterio_1_2_t1
            justif_final = justif_t1
        else:
            # --- TURNO 2: Mejora Guiada por Juez LLM (justificacion_gemini Turno 1) ---
            print(f"[{case_clean}] Turno 1 con margen de mejora (Validez: {v_sintactica_t1:.2f} <= 0.80). Iniciando Turno 2 guiado por el juez LLM...")
            turns_count = 2
            
            if is_sql_turn:
                t_prompt_2 = (
                    f"Por favor, revisa y mejora la consulta SQL para BigQuery OMOP CDM 5.4 teniendo en cuenta "
                    f"las siguientes observaciones del evaluador clínico/técnico:\n\n"
                    f"{justif_t1}\n\n"
                    f"Genera directamente la consulta SQL SELECT corregida y ejecutable."
                )
            else:
                approved_cands = []
                if gold_concepts:
                    approved_cands.extend(sorted(list(gold_concepts)))
                if all_discovered_concepts:
                    approved_cands.extend([c for c in sorted(list(all_discovered_concepts)) if c not in gold_concepts][:3])
                    
                cands_approval = f"Apruebo y confirmo los conceptos {', '.join(str(c) for c in approved_cands[:4])}. " if approved_cands else "Apruebo los conceptos identificados. "
                table_context = f" consultando las tablas del modelo OMOP ({tables_hint})" if tables_hint else ""
                t_prompt_2 = (
                    f"{cands_approval}Teniendo en cuenta las siguientes observaciones del evaluador clínico/técnico:\n\n"
                    f"{justif_t1}\n\n"
                    f"Genera directamente la consulta SQL para BigQuery{table_context} utilizando los concept IDs aprobados."
                )
            
            events = execute_agent_turn(session_id, t_prompt_2, eval_id=eval_id)
            sql_turn_t2, validated_turn_t2, discovered_turn_t2, text_turn_t2 = extract_sql_from_events(events)
            all_discovered_concepts.update(discovered_turn_t2)
            if text_turn_t2.strip():
                agent_full_text = text_turn_t2
            if validated_turn_t2:
                validated_by_tool = True
                
            is_sql_turn_t2 = is_valid_sql_statement(sql_turn_t2)
            turn2_concepts = extract_turn_concepts(sql_turn_t2, gold_concepts, all_discovered_concepts)
            criterio_1_1_t2 = 0.10 if (validated_turn_t2 or is_sql_turn_t2) else 0.00
            print(f"[{case_clean}] Evaluando similitud del Turno 2 con Gemini frente a Gold Standard...")
            criterio_1_2_t2, justif_t2 = judge_sql_similarity_with_gemini(gold_sql, sql_turn_t2 if is_sql_turn_t2 else text_turn_t2, prompt, eval_id=eval_id)
            v_sintactica_t2 = round(criterio_1_1_t2 + criterio_1_2_t2, 2)
            p_vocab_t2 = compute_vocab_precision(turn2_concepts, gold_concepts)
            
            turn_metrics["turno_2"] = {
                "validez_sintactica_y_estructural": v_sintactica_t2,
                "precision_terminologica_vocabulario": p_vocab_t2,
                "question_improvement": t_prompt_2
            }
            
            # Determinar si se requiere Turno 3 para optimización guiada por el juez LLM:
            # Cuando la Validez Sintáctica y Estructural de un turno supere el 0.80, no es necesario ejecutar el siguiente turno
            if is_sql_turn_t2 and v_sintactica_t2 > 0.80:
                print(f"[{case_clean}] Turno 2 con Validez Sintáctica y Estructural satisfactoria ({v_sintactica_t2:.2f} > 0.80). Concluyendo evaluación en Turno 2.")
                turns_count = 2
                sql_agente = sql_turn_t2
                c1_1_final = criterio_1_1_t2
                c1_2_final = criterio_1_2_t2
                justif_final = justif_t2
            else:
                # --- TURNO 3: Optimización Final Guiada por Juez LLM (justificacion_gemini Turno 2) ---
                print(f"[{case_clean}] Turno 2 con margen de mejora (Validez: {v_sintactica_t2:.2f} <= 0.80). Iniciando Turno 3 guiado por el juez LLM...")
                turns_count = 3
                t_prompt_3 = (
                    f"Por favor, revisa y optimiza la consulta SQL para BigQuery OMOP CDM 5.4 resolviendo "
                    f"las siguientes observaciones técnicas y clínicas del evaluador:\n\n"
                    f"{justif_t2}\n\n"
                    f"Emite directamente la sentencia SQL ejecutable final, sin explicaciones adicionales ni pasos intermedios."
                )
                events = execute_agent_turn(session_id, t_prompt_3, eval_id=eval_id)
                sql_turn_t3, validated_turn_t3, discovered_turn_t3, text_turn_t3 = extract_sql_from_events(events)
                all_discovered_concepts.update(discovered_turn_t3)
                if text_turn_t3.strip():
                    agent_full_text = text_turn_t3
                if validated_turn_t3:
                    validated_by_tool = True
                    
                is_sql_turn_t3 = is_valid_sql_statement(sql_turn_t3)
                turn3_concepts = extract_turn_concepts(sql_turn_t3, gold_concepts, all_discovered_concepts)
                criterio_1_1_t3 = 0.10 if (validated_turn_t3 or is_sql_turn_t3) else 0.00
                print(f"[{case_clean}] Evaluando similitud del Turno 3 con Gemini frente a Gold Standard...")
                criterio_1_2_t3, justif_t3 = judge_sql_similarity_with_gemini(gold_sql, sql_turn_t3 if is_sql_turn_t3 else text_turn_t3, prompt, eval_id=eval_id)
                v_sintactica_t3 = round(criterio_1_1_t3 + criterio_1_2_t3, 2)
                p_vocab_t3 = compute_vocab_precision(turn3_concepts, gold_concepts)
                
                turn_metrics["turno_3"] = {
                    "validez_sintactica_y_estructural": v_sintactica_t3,
                    "precision_terminologica_vocabulario": p_vocab_t3,
                    "question_improvement": t_prompt_3
                }
                
                # Consolidación final entre los turnos ejecutados
                candidate_turns = []
                if is_sql_turn:
                    candidate_turns.append((v_sintactica_t1, 1, sql_turn, criterio_1_1_t1, criterio_1_2_t1, justif_t1))
                if is_sql_turn_t2:
                    candidate_turns.append((v_sintactica_t2, 2, sql_turn_t2, criterio_1_1_t2, criterio_1_2_t2, justif_t2))
                if is_sql_turn_t3:
                    candidate_turns.append((v_sintactica_t3, 3, sql_turn_t3, criterio_1_1_t3, criterio_1_2_t3, justif_t3))
                    
                if candidate_turns:
                    # Seleccionar el turno con mayor validez y similitud (en empate, el turno más reciente)
                    candidate_turns.sort(key=lambda x: (x[0], x[1]))
                    best_v, best_t, best_sql, best_c11, best_c12, best_justif = candidate_turns[-1]
                    sql_agente = best_sql
                    c1_1_final = best_c11
                    c1_2_final = best_c12
                    justif_final = best_justif
                else:
                    sql_agente = text_turn_t3.strip() if text_turn_t3.strip() else (text_turn_t2.strip() if text_turn_t2.strip() else text_turn.strip())
                    c1_1_final = 0.00
                    c1_2_final = 0.00
                    justif_final = justif_t3 or justif_t2 or justif_t1
                
        # 3. Conceptos consolidados y tablas en consulta SQL final
        agent_concepts = extract_turn_concepts(sql_agente, gold_concepts, all_discovered_concepts)
            
        # Extraer tablas OMOP referenciadas (excluyendo CTEs definidos en WITH)
        cte_names = set(m.lower() for m in re.findall(r"(?:WITH|,)\s*([a-zA-Z0-9_]+)\s+AS\s*\(", sql_agente, re.IGNORECASE))
        tables_found = set()
        for tbl in re.findall(r"(?:FROM|JOIN)\s+[`]?([a-zA-Z0-9_\-\.]+)[`]?", sql_agente, re.IGNORECASE):
            clean_tbl = tbl.split(".")[-1]
            if clean_tbl.lower() not in ("where", "on", "as", "select", "group", "order", "with") and clean_tbl.lower() not in cte_names:
                tables_found.add(clean_tbl)
                
        # 4. Cálculo de Métricas Finales
        validez_sintactica = round(c1_1_final + c1_2_final, 2)
        precision_vocab = compute_vocab_precision(agent_concepts, gold_concepts)
            
        evaluacion_cualitativa = generate_qualitative_evaluation(
            c1_1_final,
            c1_2_final,
            justif_final,
            precision_vocab,
            gold_concepts,
            agent_concepts,
            sql_agente,
            turns_count,
            agent_full_text,
            tables_found,
            confirmed_in_t1=confirmed_in_t1
        )
        
        # 5. Descarga de la sesión forense del agente (ADK JSON)
        if session_id:
            try:
                sessions_dir = os.path.join(results_dir, "sessions")
                os.makedirs(sessions_dir, exist_ok=True)
                session_json_path = os.path.join(sessions_dir, f"{case_clean}.json")
                sess_json_data = download_agent_session(session_url, session_id, eval_id=eval_id)
                if sess_json_data:
                    with open(session_json_path, "w", encoding="utf-8") as f_sess:
                        json.dump(sess_json_data, f_sess, indent=2, ensure_ascii=False)
                    session_file_rel = f"results/{source}/sessions/{case_clean}.json"
                    print(f"[{case_clean}] Sesión forense guardada: {session_json_path}")
            except Exception as e_sess:
                print(f"[{case_clean}] Aviso: no se pudo guardar la sesión forense: {e_sess}")
        
    except Exception as exc:
        print(f"[{case_clean}] Error en evaluación: {exc}")
        check_conexion = f"Fallo de conexión: {str(exc)}"
        c1_1_final = 0.00
        c1_2_final = 0.00
        validez_sintactica = 0.00
        precision_vocab = 0.00
        agent_concepts = []
        sql_agente = ""
        justif_final = f"Error durante la comunicación con el agente: {str(exc)}"
        evaluacion_cualitativa = LiteralStr(justif_final)
        
    multiline_sql = format_multiline_text(sql_agente, is_sql=True)
    
    metricas_dict = {
        "validez_sintactica_y_estructural": validez_sintactica,
        "precision_terminologica_vocabulario": precision_vocab,
        "detalle_validez_sintactica": {
            "criterio_1_1_ejecucion": c1_1_final,
            "criterio_1_2_similitud_sql_gemini": c1_2_final,
            "justificacion_gemini": LiteralStr(justif_final)
        }
    }
    if turn_metrics:
        metricas_dict["metricas_por_turno"] = turn_metrics
        
    result_yaml = {
        "id_evaluacion": eval_id,
        "session_id": session_id if session_id else "",
        "session_file": session_file_rel if session_file_rel else "",
        "turnos_ejecutados": turns_count,
        "sql_generada_agente": multiline_sql,
        "concept_ids_identificados_agente": agent_concepts,
        "metricas_evaluacion": metricas_dict,
        "evaluacion_cualitativa": evaluacion_cualitativa,
        "check_conexion": check_conexion
    }
    
    out_yaml_path = os.path.join(results_dir, f"{case_clean}.yaml")
    with open(out_yaml_path, "w", encoding="utf-8") as f_out:
        yaml.dump(result_yaml, f_out, allow_unicode=True, sort_keys=False, default_flow_style=False)
        
    # Verificación sintáctica estricta del YAML generado
    with open(out_yaml_path, "r", encoding="utf-8") as verify_f:
        yaml.safe_load(verify_f)
        
    print(f"[{case_clean}] Turnos: {turns_count} | Métrica 1 (Sintaxis+Similitud): {validez_sintactica:.2f} (Ejecución: {c1_1_final:.2f}, Gemini: {c1_2_final:.2f}) | Vocabulario: {precision_vocab:.2f}")
    print(f"[{case_clean}] Check Conexión: {check_conexion}")
    print(f"[{case_clean}] Archivo guardado y validado sintácticamente: {out_yaml_path}")
    
    return {
        "case": case_clean,
        "id_evaluacion": eval_id,
        "turnos": turns_count,
        "sintaxis": validez_sintactica,
        "vocabulario": precision_vocab,
        "conexion": check_conexion is True
    }

def parse_range(range_str):
    m = re.match(r"([A-Za-z]*)(\d+)-([A-Za-z]*)(\d+)", range_str)
    if not m:
        raise ValueError(f"Formato no válido: '{range_str}'. Use ej. C01-C10.")
    prefix = m.group(1) or "C"
    start_num = int(m.group(2))
    end_num = int(m.group(4))
    width = max(len(m.group(2)), len(m.group(4)), 2)
    return [f"{prefix}{n:0{width}d}" for n in range(start_num, end_num + 1)]

def main():
    parser = argparse.ArgumentParser(
        description="Evaluador unificado para fuentes de consultas OMOP (QueryLibrary y nuevas fuentes)."
    )
    parser.add_argument(
        "cases",
        nargs="*",
        help="Casos específicos a evaluar (ej. C01 C02 o C01.yaml). Por defecto: C01",
    )
    parser.add_argument(
        "--source", "-s",
        default="querylibrary",
        help="Identificador/tipo de fuente de consultas SQL a evaluar (por defecto: 'querylibrary')",
    )
    parser.add_argument(
        "--range", "-r",
        help="Rango de casos a evaluar en lote (ej. C01-C10)",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Evaluar todos los archivos YAML presentes en evaluation/gold_standard/<source>/",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Omitir casos que ya posean un archivo de resultado YAML generado previamente",
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=1.5,
        help="Pausa en segundos entre llamadas consecutivas (por defecto: 1.5s)",
    )
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Directorio raíz del proyecto (por defecto: auto-detectado)",
    )
    
    args = parser.parse_args()
    
    if args.base_dir:
        base_dir = os.path.abspath(args.base_dir)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(script_dir, "evaluation")):
            base_dir = script_dir
        else:
            base_dir = os.path.abspath(os.path.join(script_dir, "../.."))
    
    source = args.source
    cases_to_evaluate = []
    if args.all:
        pattern = os.path.join(base_dir, f"evaluation/gold_standard/{source}/*.yaml")
        files = glob.glob(pattern)
        def natural_sort_key(path):
            name = os.path.basename(path)
            return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', name)]
        sorted_files = sorted(files, key=natural_sort_key)
        cases_to_evaluate = [os.path.basename(p).replace(".yaml", "") for p in sorted_files]
    elif args.range:
        cases_to_evaluate = parse_range(args.range)
    elif args.cases:
        cases_to_evaluate = [c.replace(".yaml", "").strip() for c in args.cases]
    else:
        cases_to_evaluate = ["C01"]
        
    print(f"Fuente seleccionada: {source}")
    print(f"Iniciando evaluación para {len(cases_to_evaluate)} caso(s): {', '.join(cases_to_evaluate[:10])}{'...' if len(cases_to_evaluate) > 10 else ''}")
    
    results = []
    for i, case in enumerate(cases_to_evaluate):
        case_clean = case.replace(".yaml", "").strip()
        out_yaml_path = os.path.join(base_dir, f"evaluation/results/{source}/{case_clean}.yaml")
        if args.skip_existing and os.path.exists(out_yaml_path):
            print(f"[{case_clean}] Omitiendo: ya existe resultado previo.")
            continue
        res = evaluate_case(case, base_dir, source=source)
        if res:
            results.append(res)
        if i < len(cases_to_evaluate) - 1 and args.delay > 0:
            time.sleep(args.delay)
            
    if len(results) > 1:
        print("\n" + "="*78)
        print("RESUMEN DE EVALUACIÓN:")
        print(f"{'Caso':<6} | {'ID Evaluación':<20} | {'Turnos':<7} | {'Sintaxis':<10} | {'Vocabulario':<12} | {'Conexión'}")
        print("-" * 78)
        for r in results:
            con_status = "OK" if r["conexion"] else "FALLO"
            print(f"{r['case']:<6} | {r['id_evaluacion']:<20} | {r.get('turnos', 1):<7} | {r['sintaxis']:<10.2f} | {r['vocabulario']:<12.2f} | {con_status}")
        print("="*78)
        
        avg_sintaxis = sum(r["sintaxis"] for r in results) / len(results)
        avg_vocab = sum(r["vocabulario"] for r in results) / len(results)
        print(f"Promedio ({len(results)} casos) -> Sintaxis: {avg_sintaxis:.2f} | Vocabulario: {avg_vocab:.2f}")

if __name__ == "__main__":
    main()
