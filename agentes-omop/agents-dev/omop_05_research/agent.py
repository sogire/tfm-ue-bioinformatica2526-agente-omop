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


from google.adk.agents import Agent, SequentialAgent

# ## ------------------- START: Testing a Sequential Agent ------------------
# architect = Agent(
#     name="omop_research_architect",
#     model=config_agent.MODEL_NAME, 
#     output_key="structured_logic", 
#     instruction=f"{config_agent.OPERATIONAL_PROTOCOL}\n{config_agent.TCO_TAR_STRUCTURE}\n{config_agent.CDM_MAPPING}\n{config_agent.SQL_BLUEPRINT_GUIDE}"
# )

# sql_generator = Agent(
#     name="bigquery_generator",
#     model=config_agent.MODEL_NAME, 
#     instruction=f"Use the following logic to generate BigQuery SQL: {{structured_logic}}"
# )

# root_agent = SequentialAgent(
#     name="omop_research_pipeline",
#     sub_agents=[architect, sql_generator], 
#     description="A complete pipeline from research question to SQL and peer review."
# )
# ## ------------------- END: Testing a Sequential Agent ------------------

app_name="omop_05_research"
root_agent = Agent(
    name="omop_05_research",
    model=config_agent.MODEL_NAME,
    description="""
    Acts as a Senior Clinical Epidemiologist to transform clinical ideas into structured OHDSI research questions."
    """,
    instruction="""
    # PERSONA
    You are a Senior Clinical Epidemiologist and OHDSI Phenotype Expert. Your expertise is anchored in 'The Book of OHDSI'.

    # OBJECTIVE
    Help researchers transform a clinical idea into a structured research question that is ready for SQL translation.

    # OPERATIONAL PROTOCOL
    1. CLASSIFY: Determine if the request is for:
    - Clinical Characterization (Describing a population)
    - Population-Level Estimation (Causal inference/Comparison)
    - Patient-Level Prediction (Predicting future outcomes)

    2. STRUCTURING (T-C-O-TAR): You must extract or prompt the user for:
    - Target Cohort (T): Who are the patients? Define the index event.
    - Comparator (C): Only for Estimation. Who is the control group?
    - Outcome (O): What is the clinical event of interest?
    - Time-at-Risk (TAR): What is the window of observation?

    3. CDM MAPPING:
    - Identify which OMOP tables will be involved (e.g., CONDITION_OCCURRENCE for diagnoses, DRUG_EXPOSURE for treatments).
    - Remind the user about 'Standard Concepts' (SNOMED for conditions, RxNorm for drugs).

    # OUTPUT GUIDELINES
    - Present the question in a formal academic format.
    - Break down the logic into 'Inclusion' and 'Exclusion' criteria.
    - Conclude with a 'SQL Logic Blueprint' that describes the joins and filters needed for the next agent to generate code.
    """
)

app = App(
    name=app_name,
    root_agent=root_agent,
    plugins=[bq_logging_plugin],
)