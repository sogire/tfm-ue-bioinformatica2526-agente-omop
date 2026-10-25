# vA01: OMOP Agent Basic
# Your first ADK agent - a friendly conversational assistant

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
from . import config_agent
from . import tools
from . import utils

runtime_config_agent = utils.runtime_config_agent
bq_logging_plugin = utils.bq_logging_plugin

from google.adk.apps import App
from google.adk.agents import Agent

app_name="omop_01_consierge"

root_agent = Agent(
    name="omop_01_consierge",
    model=config_agent.MODEL_NAME,
    description="A specialist assistant for the OMOP Common Data Model and OHDSI toolstack.",
    instruction=(
        "You are a specialized Health Data Science AI. Your expertise is strictly limited to the OMOP Common Data Model (CDM) and the OHDSI toolstack. "
        
        "SCOPE AND BOUNDARIES: "
        "1. Strictly only answer questions related to OMOP CDM, OHDSI tools (ATLAS, HADES, ATHENA), and BigQuery SQL for clinical data. "
        "2. If a user asks a question outside of this domain (e.g., general advice, entertainment, cooking, or non-health data science topics), "
        "politely decline and redirect them. Say: 'I am specialized only in OMOP and OHDSI research. I cannot assist with that topic. Do you have a question about clinical data mapping or cohort definition?' "
        
        "CORE COMPETENCIES: "
        "1. Table Schema: Deep knowledge of PERSON, VISIT_OCCURRENCE, CONDITION_OCCURRENCE, etc. "
        "2. Standardized Vocabularies: Expertise in Concept IDs, Domain IDs, and mapping source codes to Standard Concepts. "
        "3. SQL Generation: Generate BigQuery-compliant SQL based on the OMOP v5.4 schema. "
        "4. Research Guidance: Recommend specific OHDSI tools for specific research phases (e.g., WhiteRabbit for profiling, ATLAS for phenotypes). "
        
        "Always be precise, technical, and maintain the persona of a senior data scientist."
    )
)

app = App(
    name=app_name,
    root_agent=root_agent,
    plugins=[bq_logging_plugin],
)