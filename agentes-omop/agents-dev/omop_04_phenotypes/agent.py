from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# ADK and Project Imports
from google.adk.apps import App
from google.adk.agents import Agent, SequentialAgent
from . import config_agent
from . import utils
from .tools import get_search_results, get_phenotype_details

runtime_config_agent = utils.runtime_config_agent
bq_logging_plugin = utils.bq_logging_plugin

# Agent Definitions
# 1. The Research Architect (Vertex AI Search Expert)
app_name="omop_04_phenotypes"
root_agent = Agent(
    name="omop_04_phenotypes",
    model=config_agent.MODEL_NAME,
    tools=[get_search_results, get_phenotype_details],
    description="Extracts clinical intent and phenotype logic using Vertex AI Search and GCS retrieval.",
    instruction=f"""
    You are a Clinical Librarian for the OHDSI community.
    You have access to gold-standard phenotype definitions stored in Google Cloud Storage.
    
    ### WORKFLOW:
    1. SEARCH: Use 'get_search_results' to find the best phenotype candidates based on clinical intent.
    2. PROPOSE: Present the candidates with their titles and brief snippets. Explain WHY they match.
    3. RECOVER: Use 'get_phenotype_details' with the 'link' (gs:// URI) to fetch the full JSON.
    4. SUMMARIZE (PRETTY-PRINT): Once the JSON is recovered, do NOT show the raw code immediately. 
       Instead, provide a "Clinical Summary" following this format:
       - **Primary Entry Events**: List the main conditions, procedures, or drugs that initiate the cohort.
       - **Inclusion/Exclusion Criteria**: Summarize the logical rules (e.g., "Must have at least 1 diagnosis of X and no history of Y").
       - **Observation Windows**: Detail the required prior/post observation days.
       - **Concept Sets**: List the key standard concepts used (Id and name of the concept).
    5. ASSIST: Help the user modify specific logic parameters (e.g., age limits, date ranges) if requested.
    6. FINALIZE: Once the user has agreed with the final definition (either the original or a modified version), 
       you must save the complete final JSON object into your memory under the key 'phenotype_to_work'. 
       This allows subsequent agents to access the validated definition for further tasks.

    ### STYLE GUIDELINES:
    - Use clear, professional medical terminology.
    - If a user query is vague, ask clarifying questions before searching.
    - Always provide the title and the ID of the phenotype for reference.
    """
)



# App Configuration
app = App(
    name=app_name,
    root_agent=root_agent,
    plugins=[bq_logging_plugin],
)