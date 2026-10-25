> 🏠 **[Main README](../README.en.md)** · 🌐 **Language / Idioma:** [Español](README.md) | **English**

# OMOP CDM Multi-Agent Ecosystem (`omop-agent-path`)

Multi-agent framework built on the **Google Agent Development Kit (ADK)** designed to assist in biomedical research, clinical phenotyping, analytical query formulation, and observational study design over the **OMOP CDM 5.4** common data model hosted on **Google BigQuery** (`bio-med-480108.OMOP_54_A`).

The system comprises a suite of specialized agents that collaborate to cover the entire health research lifecycle, from defining the epidemiological question to generating SQL code and R scripts based on official **OHDSI** (*Observational Health Data Sciences and Informatics*) methodologies.

---

## 📁 Repository Structure

```text
agentes-omop/
├── README.md                     # Spanish documentation
├── README.en.md                  # This document (English)
├── Dockerfile.dev                # Container image for Cloud Run deployment with ADK Web
├── cloudbuild.yaml               # Google Cloud Build configuration
├── config-dev.sh                 # Environment variables and GCP project configuration
├── config-dev.template.sh        # De-identified and commented template for new deployments
├── deploy_cloudrun.sh            # Automated build and deployment script for Cloud Run
├── deploy_iap_cloudrun.sh        # Security configuration with Identity-Aware Proxy (IAP)
├── deploy_roles_cloudrun.sh      # IAM role and service account assignment
├── deploy_enable_apis.sh         # Enabling required Google Cloud APIs
├── start-command.sh              # Local development environment initialization
└── agents-dev/                   # Specialized subagents directory
    ├── requirements.txt          # Python dependencies for the agent suite
    ├── omop_01_consierge/        # Conversational concierge and scope definition
    ├── omop_02_book_of_ohdsi/    # Methodological specialist in 'The Book of OHDSI'
    ├── omop_03_concepts_and_sql/ # Text-to-SQL agent with BigQuery validation
    ├── omop_04_phenotypes/       # Clinical librarian and phenotype manager
    ├── omop_05_research/         # Clinical epidemiologist and T-C-O-TAR structuring
    └── omop_06_r_scripts/        # R architect for OHDSI and DARWIN EU packages
```

---

## 🤖 Agent Catalog (`agents-dev/`)

> [!IMPORTANT]
> **Target Agent of the Master's Thesis and its Evaluation:**
> The **core agent subject of the research and evaluated in the experimental benchmark of the Master's Thesis is [`omop_03_concepts_and_sql`](agents-dev/omop_03_concepts_and_sql/README.en.md)**.
> The remaining agents present in this directory (`omop_01_consierge`, `omop_02_book_of_ohdsi`, `omop_04_phenotypes`, `omop_05_research`, and `omop_06_r_scripts`) were developed as **parallel experiments** to explore solving other types of challenges within the OMOP/OHDSI ecosystem. They served as personal learning and a source of future ideas, but **are not subject to formal evaluation in the Master's Thesis report**.

Each subagent features its own configuration, tool assignments, and detailed documentation in its corresponding `README.en.md` (and Spanish `README.md`):

### ⭐ Core Agent of the Master's Thesis (Formally Evaluated)

#### [`omop_03_concepts_and_sql`](agents-dev/omop_03_concepts_and_sql/README.en.md) — OMOP BigQuery Text-to-SQL Agent
* **Profile:** Technical data scientist with a guided collaborative workflow.
* **Objective:** Translates clinical needs into accurate, optimized SQL queries for Google BigQuery on OMOP CDM 5.4. It operates under a strict two-phase protocol: first, it searches for and disambiguates medical concepts via `search_omop_official_concepts`, requiring explicit user approval on a Markdown table; next, it formulates the SQL statement applying native BigQuery types (`FLOAT64`, `BIGNUMERIC`) and mandatorily verifies its syntax with `validate_omop_sql` before presenting the final result.

---

### 🧪 Parallel Exploratory Experiments (Outside the Master's Thesis Scope)

#### 1. [`omop_01_consierge`](agents-dev/omop_01_consierge/README.en.md) — Concierge and General Coordinator
* **Profile:** Conversational assistant and biomedical advisor.
* **Objective:** Acts as the initial point of contact for the user, ensuring that all interactions remain strictly within the scope of OMOP CDM and OHDSI tools (ATLAS, HADES, ATHENA). Provides guidance on the OMOP v5.4 table schema, data domains, and standardized vocabularies, politely redirecting any query unrelated to clinical analysis.

#### 2. [`omop_02_book_of_ohdsi`](agents-dev/omop_02_book_of_ohdsi/README.en.md) — OHDSI Methodological Specialist
* **Profile:** Senior health data scientist grounded in official literature.
* **Objective:** Provides evidence-based methodological guidance on observational study design, *Population-Level Estimation*, and *Patient-Level Prediction*. Its knowledge is anchored in *The Book of OHDSI* through the semantic search tool `get_search_results`, while also instructing on ATHENA and HADES suite best practices.

#### 3. [`omop_04_phenotypes`](agents-dev/omop_04_phenotypes/README.en.md) — Clinical Librarian and Phenotype Manager
* **Profile:** *Clinical Librarian* for standardized cohorts.
* **Objective:** Discovers, retrieves, and evaluates standard phenotype definitions stored in Google Cloud Storage using Vertex AI Search (`get_search_results`) and `get_phenotype_details`. Presents structured summaries (entry events, logical criteria, observation windows, and concept sets), assists in filter parameterization, and stores the final definition in memory (`phenotype_to_work`) for downstream analyses.

#### 4. [`omop_05_research`](agents-dev/omop_05_research/README.en.md) — Clinical Epidemiologist and Research Design
* **Profile:** Senior clinical epidemiologist and observational study consultant.
* **Objective:** Transforms preliminary clinical ideas into rigorously structured research questions. Classifies the study (characterization, estimation, or prediction), breaks down cohort components using the formal **T-C-O-TAR** (*Target, Comparator, Outcome, Time-at-Risk*) framework, maps variables to OMOP master tables, and generates a *SQL Logic Blueprint* with the required criteria and joins.

#### 5. [`omop_06_r_scripts`](agents-dev/omop_06_r_scripts/README.en.md) — R Architect for OHDSI and DARWIN EU
* **Profile:** Senior R statistical software developer for life sciences.
* **Objective:** Generates reproducible, robust, and evidence-based R scripts for studies on OMOP CDM. Applies a *Search-First* strategy with `get_search_results` to incorporate official syntax and vignettes from libraries such as CDMConnector, CohortMethod, and Capr, producing executable code with explicit namespace calls, database connection logic, cohort generation, and standardized CSV export.

---

## 🔄 Integrated Multi-Agent Workflow

The agents are designed to complement one another sequentially throughout a clinical investigation:

| Research Stage | Responsible Agent | Main Inputs | Key Outputs |
| :--- | :--- | :--- | :--- |
| **1. Intake and Scope Definition** | [`omop_01_consierge`](agents-dev/omop_01_consierge/README.en.md) | User's initial medical query or question | Defined scope and guidance on tables/tools |
| **2. Epidemiological Structuring** | [`omop_05_research`](agents-dev/omop_05_research/README.en.md) | Clinical research question | T-C-O-TAR definition and *SQL Logic Blueprint* |
| **3. Cohort Search and Tuning** | [`omop_04_phenotypes`](agents-dev/omop_04_phenotypes/README.en.md) | Study clinical criteria | Standard phenotype JSON in memory (`phenotype_to_work`) |
| **4. Text-to-SQL Formulation (TFM Core)** | [`omop_03_concepts_and_sql`](agents-dev/omop_03_concepts_and_sql/README.en.md) | Analytical intent or *Blueprint* | Approved Concept IDs and validated BigQuery SQL query |
| **5. Methodological Advisory** | [`omop_02_book_of_ohdsi`](agents-dev/omop_02_book_of_ohdsi/README.en.md) | Questions on design, inference, or bias | Recommendations grounded in *The Book of OHDSI* |
| **6. R Implementation** | [`omop_06_r_scripts`](agents-dev/omop_06_r_scripts/README.en.md) | Cohort design or analytical requirement | Complete R scripts using HADES and DARWIN EU libraries |

---

## 🚀 Deployment on Google Cloud Platform

The agent suite is deployed on **Google Cloud Run** running the ADK application server (`adk web`), packaged via a multi-stage Docker container.

### Prerequisites
* Configured Google Cloud project (in a region supporting Vertex AI and Cloud Run).
* Authenticated Google Cloud CLI (`gcloud`) with appropriate deployment permissions.
* Configured environment variables file. A de-identified and documented template is included: [`config-dev.template.sh`](config-dev.template.sh) (copy to `config-dev.sh` and populate with project credentials and datasets).
* Configured subagent settings files (`agents-dev/*/config_agent.py`), created from their respective de-identified `config_agent.template.py` templates.

### Infrastructure Management Scripts

1. **Enable GCP Services:**
   ```bash
   ./deploy_enable_apis.sh
   ```
   Enables Cloud Run, Cloud Build, Artifact Registry, Vertex AI, and Identity-Aware Proxy APIs.

2. **Configure IAM Permissions and Roles:**
   ```bash
   ./deploy_roles_cloudrun.sh
   ```
   Grants the required roles to the service account (`omop-training@bio-med-480108.iam.gserviceaccount.com`).

3. **Build and Deploy to Cloud Run:**
   ```bash
   ./deploy_cloudrun.sh dev
   ```
   Builds the container image via Google Cloud Build using [`cloudbuild.yaml`](cloudbuild.yaml) and [`Dockerfile.dev`](Dockerfile.dev), and deploys the service to Cloud Run with the environment variables associated with Vertex AI and BigQuery.

4. **Security and Access Control with IAP:**
   ```bash
   ./deploy_iap_cloudrun.sh
   ```
   Configures the load balancer and perimeter protection via Identity-Aware Proxy for restricted access to authorized users.

### Running in a Local Development Environment
To spin up the agents locally with hot-reloading:
```bash
# Activate virtual environment and install dependencies
source ../.venv/bin/activate
pip install -r agents-dev/requirements.txt

# Run the ADK server
adk web --host 127.0.0.1 --port 8080 agents-dev
```

