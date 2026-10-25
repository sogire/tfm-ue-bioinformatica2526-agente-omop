> 🏠 **[Main README](../README.en.md)** · 📄 **Report Version:** **Academic Thesis Version (EN)** | [Original PDF (ES)](TFM-AgenteOMOP_SergioBermudez_Version-MemoriaAcademica.pdf) · 🔄 **Companion Report:** [Professional Solution Version (EN)](TFM-AgenteOMOP_SergioBermudez_Version-ProfesionalSolucion.en.md) ([PDF (ES)](TFM-AgenteOMOP_SergioBermudez_Version-ProfesionalSolucion.pdf))

<div align="center">

![Universidad Europea de Madrid](figures/ue_logo.png)

# MASTER'S THESIS
### *Master's Degree in Bioinformatics (2025/2026)*
#### **Academic Thesis Version**

---

# OMOP ANALYTICAL AGENT
## CONVERSATIONAL AI APPLICATION TO DEMOCRATIZE DATA ANALYSIS ON OMOP CDM 5.4 CLINICAL DATABASES

**Author:** [Sergio Bermúdez Sánchez](https://www.linkedin.com/in/sergio-bermudez-sanchez/)  
**Supervisor:** Isidoro Gutiérrez Álvarez  

*Villaviciosa de Odón, October 2026*

</div>

---

## Table of Contents

- [Abstract](#abstract)
- [1. Introduction](#1-introduction)
  - [1.1. Context and Problem Statement](#11-context-and-problem-statement)
  - [1.2. The OMOP CDM Common Data Model and the OHDSI Ecosystem](#12-the-omop-cdm-common-data-model-and-the-ohdsi-ecosystem)
  - [1.3. Conversational Artificial Intelligence and Text-to-SQL in Biomedicine](#13-conversational-artificial-intelligence-and-text-to-sql-in-biomedicine)
- [2. Hypothesis and Objectives](#2-hypothesis-and-objectives)
  - [2.1. Hypothesis](#21-hypothesis)
  - [2.2. Objectives](#22-objectives)
    - [2.2.1. General Objective](#221-general-objective)
    - [2.2.2. Specific Objectives](#222-specific-objectives)
  - [2.3. Alignment with the Sustainable Development Goals (SDGs)](#23-alignment-with-the-sustainable-development-goals-sdgs)
- [3. Materials and Methods](#3-materials-and-methods)
  - [3.1. Multi-Agent Functional Architecture](#31-multi-agent-functional-architecture)
  - [3.2. Technical Infrastructure and Data Persistence](#32-technical-infrastructure-and-data-persistence)
  - [3.3. Evaluation Methodology](#33-evaluation-methodology)
    - [3.3.1. Reference Dataset (Gold Standard)](#331-reference-dataset-gold-standard)
    - [3.3.2. Evaluation Metrics and Indices](#332-evaluation-metrics-and-indices)
    - [3.3.3. Execution Protocol and Statistical Analysis](#333-execution-protocol-and-statistical-analysis)
- [4. Results](#4-results)
  - [4.1. Qualitative Evaluation](#41-qualitative-evaluation)
  - [4.2. Overall Quantitative Evaluation](#42-overall-quantitative-evaluation)
  - [4.3. Performance by Complexity Level](#43-performance-by-complexity-level)
  - [4.4. Performance by OMOP CDM Domain](#44-performance-by-omop-cdm-domain)
  - [4.5. Resolution Dynamics and Benefit of Interactive Refinement](#45-resolution-dynamics-and-benefit-of-interactive-refinement)
- [5. Discussion](#5-discussion)
  - [5.1. Interpretation of Findings](#51-interpretation-of-findings)
  - [5.2. Prompt Engineering Optimization Guidelines](#52-prompt-engineering-optimization-guidelines)
  - [5.3. Study Limitations](#53-study-limitations)
- [6. Conclusions and Future Work](#6-conclusions-and-future-work)
  - [6.1. Conclusions](#61-conclusions)
  - [6.2. Future Work](#62-future-work)
- [7. References](#7-references)
- [8. Annexes](#8-annexes)

<details>
<summary><strong>📊 Index of Figures and Tables</strong></summary>

**Figures**
- [Figure 1. OMOP Common Data Model adoption](#figure-1)
- [Figure 2. OMOP Common Data Model standardized tables and schema](#figure-2)
- [Figure 3. Interaction flow between the agents and the user](#figure-3)
- [Figure 4. Technical architecture](#figure-4)
- [Figure 5. Distribution of OMOP Agent Performance by Complexity Level](#figure-5)
- [Figure 6. Mean Performance of the Agent by Primary OMOP CDM Domain](#figure-6)
- [Figure 7. Conversational Effort Required by Query Complexity (N = 201)](#figure-7)
- [Figure 8. Trajectory of result improvement across conversational turns](#figure-8)
- [Figure 9. Cumulative Efficacy Curve of Conversational Refinement (N = 201)](#figure-9)

**Tables**
- [Table 1. Overall Descriptive Statistics of Agent Performance (N = 201)](#table-1)
- [Table 2. Comparative Performance by Complexity Level](#table-2)
- [Table 3. Agent Performance Stratified by Primary OMOP CDM 5.4 Domain](#table-3)
- [Table 4. Contingency Table: Complexity Level × Executed Conversational Turns](#table-4)
- [Table 5. Performance Progression and Net Gain (Delta) by Turn](#table-5)

</details>

---

## Abstract

Analytical access to standardized observational health data under the OMOP CDM (*Observational Medical Outcomes Partnership Common Data Model*) remains constrained by the requirement for advanced technical proficiency in SQL and exhaustive knowledge of OHDSI ontologies and hierarchies. To mitigate this adoption barrier in healthcare and research settings, this Master's Thesis designed and implemented the **OMOP Analytical Agent**, a proof of concept grounded in conversational agent architectures and generative artificial intelligence, aimed at resolving clinical cohort characterization and incidence queries formulated in natural language.

The solution was structured around a modular multi-agent system built on the Google ADK (*Agent Development Kit*) framework, orchestrating Gemini-2.5-Flash foundation models alongside a Retrieval-Augmented Generation (RAG) mechanism specialized in terminological resolution against standardized vocabularies (SNOMED CT and RxNorm). The system functionally decouples ontological extraction, canonical identifier validation (`concept_id`), relational syntax construction, and semantic-structural verification against the OMOP 5.4 relational schema.

Experimental evaluation was conducted on a standardized benchmark (*Gold Standard*) of $N = 201$ clinical queries extracted and adapted from the OHDSI *QueryLibrary*, stratified by domain and computational complexity. Results demonstrate an initial (*zero-shot*) Syntactic and Structural Validity of 23.9%, which progressively converges to a consolidated mean of 84.9% ($\pm 0.271$) through an iterative refinement protocol of up to three turns. Meanwhile, Vocabulary Terminological Precision reached an overall mean of 92.5% ($\pm 0.239$), with 90.0% optimal assignments. These findings confirm the technical and operational feasibility of multi-agent systems as an interface to democratize biomedical observational analysis, while delineating the prompt engineering and schema control requirements needed to handle complex relational queries.

**Keywords:** OMOP CDM, OHDSI, Conversational Artificial Intelligence, Multi-Agent Systems, Text-to-SQL, Controlled Vocabularies, RAG, Clinical Bioinformatics.

---

## 1. Introduction

### 1.1. Context and Problem Statement

Direct analytical exploitation of electronic health records (EHRs) and observational databases represents a recurring challenge for clinicians and biomedical researchers unfamiliar with relational storage architectures. Frequently, high-value epidemiological and healthcare questions—such as the proportion of patients with atrial fibrillation receiving oral anticoagulation therapy, or the stratified incidence rate of pneumonia in geriatric cohorts—require constant technical intermediation.

In current hospital ecosystems and research centers, resolving such questions is typically channeled through three main pathways:

1. **Closed Business Intelligence (BI) tools and analytical platforms:** Preconfigured interfaces (e.g., OHDSI Atlas, Power BI, Tableau) which, while robust, often lack the flexibility required for *ad-hoc* exploratory queries not contemplated in predefined dashboards.
2. **Reliance on bioinformatics support units:** Formal data extraction requests submitted to specialized technical teams—a process that frequently introduces operational latencies and overloads analytical groups.
3. **Direct technical interaction via declarative languages (SQL):** An approach restricted to users proficient in SQL syntax, clinical schema normalization, and data anonymization and personal data protection guidelines (GDPR/PII).

This technical stratification creates an asymmetry in biomedical data exploitation, preventing clinical staff from agilely accessing evidence derived from real-world clinical practice.

### 1.2. The OMOP CDM Common Data Model and the OHDSI Ecosystem

The Observational Health Data Sciences and Informatics (OHDSI) consortium maintains the *Observational Medical Outcomes Partnership Common Data Model* (OMOP CDM) (Hripcsak et al., 2015; OHDSI Collaborative, 2021). This open standard homogenizes the structure, format, and terminology of heterogeneous clinical sources, enabling the deployment of multicenter, reproducible studies at an international scale.

<a id="figure-1"></a>
<div align="center">

![Figure 1. OMOP Common Data Model adoption](figures/fig01_omop_adoption_map.png)

*Figure 1. Taken from State of the OHDSI community (p. 16), by G. Hripcsak, 2025, Observational Health Data Sciences and Informatics (https://www.ohdsi.org/wp-content/uploads/2025/10/OHDSI2025-Hripcsak-State-of-Community.pdf).*

</div>

Under this model, clinical information is not only organized into uniform relational tables (such as `condition_occurrence`, `drug_exposure`, or `measurement`), but also rests upon a standardized ontological repository. This system translates local codes and heterogeneous classifications—such as the International Classification of Diseases (World Health Organization, 2018) or ICPC—into normalized, unambiguous concepts from standardized clinical terminologies such as SNOMED CT (SNOMED International, 2024), RxNorm, or LOINC, numerically identified via `concept_id`.

Despite its notable advantages, the complexity inherent to the entity-relationship design and the temporal and ontological validity rules of the OMOP model impose a steep learning curve for non-bioinformatics users (OHDSI, 2024a).

<a id="figure-2"></a>
<div align="center">

![Figure 2. OMOP Common Data Model](figures/fig02_omop_cdm_schema.png)

*Figure 2. Note. Adapted from Data standardization: OMOP Common Data Model, by Observational Health Data Sciences and Informatics (OHDSI), n.d. (https://www.ohdsi.org/data-standardization/).*

</div>

### 1.3. Conversational Artificial Intelligence and Text-to-SQL in Biomedicine

The convergence between Large Language Models (LLMs) and natural language processing (NLP) has driven the paradigm of *Conversational Analytics*. This discipline pursues the formulation of analytical queries over data warehouses using natural language, translating semantic directives into executable SQL statements (*Text-to-SQL*).

However, transposing *Text-to-SQL* to the biomedical domain poses unique challenges:

- **Ontological dispersion and polysemy:** The need to map ambiguous clinical expressions to specific standard identifiers without incurring terminological hallucinations.
- **Complex relational topology:** The need to join event tables with taxonomic hierarchies (`concept_ancestor`) and aggregated temporal persistence tables (`condition_era`, `drug_era`).

To address these difficulties in a structured manner, the **OMOP Analytical Agent** proof of concept was conceived as a multi-agent system focused on processing population characterization and epidemiological incidence questions through a modular and verifiable workflow.

---

## 2. Hypothesis and Objectives

### 2.1. Hypothesis

The implementation of a Large Language Model-based multi-agent architecture, combined with a Retrieval-Augmented Generation (RAG) engine specialized in OHDSI vocabularies and an in-loop syntactic validation mechanism, makes it possible to translate natural language questions into SQL statements compliant with the OMOP CDM 5.4 standard, achieving a syntactic-structural validity above 80% and overcoming technical querying barriers for users without database programming training.

### 2.2. Objectives

#### 2.2.1. General Objective

To design, implement, and evaluate a conversational artificial intelligence system capable of interpreting clinical analytical queries formulated in natural language and generating reproducible, semantically correct, and executable SQL statements over databases structured according to OMOP CDM 5.4.

#### 2.2.2. Specific Objectives

1. **OMOP metadata modeling and contextualization:** Adapt the relational schema and integrity constraints of the OMOP 5.4 standard into semantic representations interpretable by AI agents.
2. **Integration of RAG-supported terminological engines:** Implement an ontological search and validation subagent coupled to vector and relational databases to map natural language terms to canonical codes (`concept_id`).
3. **Multi-agent construction and orchestration of relational queries:** Design a decoupled workflow for generating, iteratively correcting syntax, and verifying SQL queries against real analytical engines.
4. **Comparative experimental validation:** Quantitatively and qualitatively evaluate the performance of the architecture using a standardized benchmark (*Gold Standard*) of 201 clinical queries, measuring terminological precision, syntactic validity, and conversational effort.

### 2.3. Alignment with the Sustainable Development Goals (SDGs)

- **SDG 3 (Good Health and Well-being):** Facilitates agile generation of clinical evidence from secondary data, supporting epidemiological research and data-driven decision-making.
- **SDG 4 (Quality Education):** Contributes to digital literacy and familiarizes medical staff with the formal structure of clinical data and biomedical ontologies.
- **SDG 9 (Industry, Innovation and Infrastructure):** Fosters the adoption of open, advanced artificial intelligence technologies in healthcare analytical infrastructures.
- **SDG 10 (Reduced Inequalities):** Narrows the operational gap between large consortia with extensive bioinformatics teams and healthcare centers with limited technical resources.

---

## 3. Materials and Methods

### 3.1. Multi-Agent Functional Architecture

The solution was designed following a hierarchical multi-agent architecture with strict separation of responsibilities, implemented on Google Cloud Platform using the *Agent Development Kit* (ADK) (Google, 2024) and the Gemini-2.5-Flash foundation model, whose coordinated interaction workflow between the user and the subagents is detailed in [Figure 3](#figure-3).

<a id="figure-3"></a>
<div align="center">

![Figure 3. Interaction flow between the agents and the user](figures/fig03_acad_fig04_prof_interaction_flow.png)

*Figure 3. Interaction flow between the agents and the user.*

</div>

1. **OMOP Orchestrator Agent (*Agente OMOP Orquestador*):** Acts as the central communication interface and task workflow coordinator. It decomposes the incoming query, delegates analytical subtasks to operational agents, and consolidates the final SQL statement, accompanying it with a structured didactic explanation.
2. **SNOMED Searcher Subagent (*Subagente SNOMED Buscador*):** Specialized in linguistic processing of nosological and therapeutic entities. It employs a RAG system on Google Cloud Vertex AI Search to index and query standardized clinical vocabularies, retrieving the corresponding canonical identifiers (`concept_id`).
3. **SNOMED Validator Subagent (*Subagente SNOMED Validador*):** Deterministic control mechanism designed to verify that retrieved `concept_id` values exist in the catalog and prevent generative hallucinations from the foundation model.
4. **OMOP SQL Constructor Subagent (*Subagente OMOP SQL Constructor*):** Transforms the clinical intent and validated identifiers into a formal SQL query compatible with the OMOP CDM 5.4 standard.
5. **SQL Validator Subagent (*Subagente SQL Validador*):** Executes the proposed syntax against a controlled environment in Google Cloud BigQuery. It detects syntactic errors, relational or type inconsistencies, feeding back in real time to the Constructor for reformulation if the query is invalid.

### 3.2. Technical Infrastructure and Data Persistence

The supporting infrastructure and the relational storage and vector indexing layer were natively implemented on the Google Cloud Platform ecosystem (as illustrated in [Figure 4](#figure-4)), structured into two main components:

<a id="figure-4"></a>
<div align="center">

![Figure 4. Technical architecture](figures/fig04_acad_fig05_prof_technical_architecture.png)

*Figure 4. Technical architecture.*

</div>

- **Compute and deployment layer:** The solution was packaged in Docker containers and deployed on Google Cloud Run via Cloud Build pipelines.
- **Persistence layer:** Hosts three datasets in Google Cloud BigQuery:
  - *Terminological Repository:* Normalized ontological tables from the OHDSI ecosystem (`concept`, `concept_ancestor`, `concept_relationship`, `vocabulary`).
  - *Validation Schema:* Catalog containing the metadata structure, primary/foreign keys, and constraints of the OMOP 5.4 model.
  - *Synthetic Database:* Schema populated with synthetically simulated patients to certify the analytical and volumetric executability of the queries.

### 3.3. Evaluation Methodology

The experimental evaluation framework was divided into a qualitative traceability demonstration and a systematic quantitative analysis using the automated [`tfm-eval`](../evaluacion-agente-omop-03/README.en.md) framework.

#### 3.3.1. Reference Dataset (Gold Standard)

An experimental cohort of $N = 201$ clinical queries in Spanish was constructed from the analytical templates of the OHDSI *QueryLibrary*. Each test case included:

- Natural language statement.
- Canonical reference SQL statement optimized for BigQuery.
- Set of expected `concept_id` identifiers.
- Classification by functional domain (`concept`, `condition_occurrence`, `drug_exposure`, `condition_era`, among others).
- Structural complexity level:
  - **Low ($N = 26$):** Direct single-table queries or elementary dictionary joins.
  - **Intermediate ($N = 71$):** Queries with multiple `JOIN` clauses, analytical aggregations, or uncorrelated subqueries.
  - **Complex ($N = 104$):** Queries structured with Common Table Expressions (CTEs), recursive ancestor hierarchies, analytical partitions, or window functions.

#### 3.3.2. Evaluation Metrics and Indices

1. **Syntactic and Structural Validity (VSE / SSV):** Normalized metric in $[0, 1]$ calculated from two components:

$$\text{VSE} = w_1 \cdot C_{\text{executability}} + w_2 \cdot C_{\text{similarity}}$$

Where $C_{\text{executability}} \in \{0, 0.10\}$ evaluates whether the statement executes successfully in the BigQuery engine without compilation or runtime errors; and $C_{\text{similarity}} \in [0, 0.90]$ quantifies the structural correspondence (clauses, joined tables, and projections) relative to the *Gold Standard*.

2. **Vocabulary Terminological Precision (PTV / VTP):** Proportion of clinical concepts correctly identified against the reference identifiers:

$$\text{PTV} = \frac{|C_{\text{generated}} \cap C_{\text{reference}}|}{|C_{\text{reference}}|}$$

3. **Conversational Effort:** Number of interactive turns (from 1 to 3) required to achieve satisfactory query resolution (operationally defined as $\text{VSE} \ge 0.80$).

#### 3.3.3. Execution Protocol and Statistical Analysis

The conversational interaction was executed through a sequential iterative protocol:

- **Turn 1 (*Zero-Shot*):** Submission of the medical question without additional contextual hints.
- **Turn 2 (Semantic refinement):** If the query does not reach the resolution threshold, the system injects explicit confirmation of the involved domains (`domain_main`, `domain_others`).
- **Turn 3 (Declarative concretization):** If failure persists, a direct emission instruction is enforced requiring the isolated final `SELECT` statement.

Comparisons across complexity groups and domains were tested using non-parametric tests (Kruskal-Wallis, Mann-Whitney, and paired-sample Wilcoxon signed-rank tests), setting the significance level at $\alpha = 0.05$.

---

## 4. Results

### 4.1. Qualitative Evaluation

Interactive behavior demonstrated the agent's ability to maintain ontological coherence and technical traceability in structured clinical queries.

```text
[User]
  "Generate a SQL query to visualize the cumulative number of patients with
   diabetes mellitus grouped by year."

[OMOP Agent - Turn 1]
  1. Terminological identification:
     - Canonical concept: 201820 | Diabetes mellitus | SNOMED | Standard: S
  2. SQL Generation (BigQuery):
     SELECT
       EXTRACT(YEAR FROM condition_start_date) AS anio_diagnostico,
       COUNT(DISTINCT person_id) AS total_pacientes
     FROM `bio-med-480108.omop_54_a.condition_occurrence`
     WHERE condition_concept_id = 201820
     GROUP BY anio_diagnostico
     ORDER BY anio_diagnostico ASC;
  3. Explanatory breakdown:
     - Filter by single standard condition (201820).
     - Grouping by calendar year and distinct aggregation of person_id.

[User - Turn 2]
  "Modify the previous query to include all descendant forms and subtypes
   of the condition."

[OMOP Agent - Turn 2]
  1. Reformulation with taxonomic expansion:
     SELECT
       EXTRACT(YEAR FROM co.condition_start_date) AS anio_diagnostico,
       COUNT(DISTINCT co.person_id) AS total_pacientes
     FROM `bio-med-480108.omop_54_a.condition_occurrence` co
     JOIN `bio-med-480108.omop_54_a.concept_ancestor` ca
       ON co.condition_concept_id = ca.descendant_concept_id
     WHERE ca.ancestor_concept_id = 201820
     GROUP BY anio_diagnostico
     ORDER BY anio_diagnostico ASC;
  2. Validation: Executable without errors in BigQuery (Time: 412 ms).
```

### 4.2. Overall Quantitative Evaluation

Analysis across the full sample ($N = 201$) demonstrated high system effectiveness, achieving a final mean Syntactic and Structural Validity of $0.849$ ($\pm 0.271$) and a median of $0.950$ [IQR: $0.130$]. Vocabulary Terminological Precision reached $0.925$ ($\pm 0.239$), requiring an average of $2.100$ conversational turns ($\pm 0.755$).

<a id="table-1"></a>
**Table 1.** *Overall Descriptive Statistics of Agent Performance ($N = 201$).*

| Evaluated Metric | N | Mean ± SD | Median [IQR] | Min – Max | 95% CI Mean |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Syntactic and Structural Validity (Final)** | 201 | 0.849 ± 0.271 | 0.950 [0.130] | 0.00 – 1.00 | [0.811 – 0.887] |
| ↳ Criterion 1.1: SQL Executability (Max. 0.10) | 201 | 0.094 ± 0.025 | 0.100 [0.000] | 0.00 – 0.10 | [0.090 – 0.097] |
| ↳ Criterion 1.2: Gold Standard Structural Similarity (Max. 0.90) | 201 | 0.756 ± 0.251 | 0.850 [0.130] | 0.00 – 0.90 | [0.721 – 0.790] |
| **Vocabulary Terminological Precision (Final)** | 201 | 0.925 ± 0.239 | 1.000 [0.000] | 0.00 – 1.00 | [0.892 – 0.958] |
| **Executed Conversational Turns** | 201 | 2.100 ± 0.755 | 2.000 [1.000] | 1.00 – 3.00 | [1.994 – 2.205] |

*Notes: N: Sample Size. SD: Standard Deviation. IQR: Interquartile Range. Min – Max: Minimum and maximum observed values. 95% CI Mean: 95% confidence interval for the mean.*

### 4.3. Performance by Complexity Level

Stratification by computational difficulty level showed marked stability at low and intermediate levels, contrasted with degradation in high-complexity queries.

<a id="table-2"></a>
**Table 2.** *Comparative Performance by Complexity Level.*

| Complexity Level | N (% total) | Mean Syntactic Validity (± SD) | Median Validity [IQR] | Mean Vocabulary (± SD) | Resolution Rate (Validity > 0.80) | Perfect Vocabulary Precision (= 1.00) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Low** | 26 (12.9%) | 0.928 ± 0.146 | 0.980 [0.040] | 1.000 ± 0.000 | 92.3% (24/26) | 100.0% (26/26) |
| **Intermediate** | 71 (35.3%) | 0.932 ± 0.167 | 0.980 [0.040] | 0.967 ± 0.139 | 95.8% (68/71) | 94.4% (67/71) |
| **Complex** | 104 (51.7%) | 0.773 ± 0.326 | 0.950 [0.242] | 0.877 ± 0.304 | 69.2% (72/104) | 84.6% (88/104) |

*Notes: N: Sample Size. SD: Standard Deviation. IQR: Interquartile Range. Min – Max: Minimum and maximum observed values. 95% CI Mean: 95% confidence interval for the mean.*

<a id="figure-5"></a>
<div align="center">

![Figure 5. Distribution of OMOP Agent Performance by Complexity Level](figures/fig05_acad_fig12_prof_performance_by_complexity.png)

*Figure 5. Distribution of OMOP Agent Performance by Complexity Level. Panel A: Final Syntactic and Structural Validity Score. Dashed lines represent the thresholds for operational success (0.80) and perfect assignment (1.00).*

</div>

The Kruskal-Wallis test confirmed significant differences across complexity levels for both Syntactic Validity ($H = 23.61;\ p < 0.001$) and Terminological Precision ($H = 8.12;\ p = 0.017$). *Post-hoc* analysis demonstrated no significant discrepancy between low and intermediate complexity ($Z = 0.28;\ p_{\text{adj}} = 0.782$), whereas complex queries experienced a significant decline compared to both intermediate ($Z = 4.34;\ p_{\text{adj}} < 0.001$) and low complexity ($Z = 3.33;\ p_{\text{adj}} = 0.002$), as reflected in the score distribution shown in [Figure 5](#figure-5).

### 4.4. Performance by OMOP CDM Domain

Analysis by primary relational table reflected noticeable variations associated with the nature of the clinical records.

<a id="table-3"></a>
**Table 3.** *Agent Performance Stratified by Primary OMOP CDM 5.4 Domain.*

| Primary OMOP Domain | N (% total) | Mean Syntactic Validity (± SD) | Median Validity | Mean Vocabulary Precision | Mean Turns | Success Rate (> 0.80) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`concept`** | 51 (25.4%) | 0.879 ± 0.194 | 0.950 | 0.975 | 2.140 | 0.824 |
| **`drug_exposure`** | 43 (21.4%) | 0.798 ± 0.355 | 0.980 | 0.956 | 2.230 | 0.791 |
| **`condition_era`** | 26 (12.9%) | 0.662 ± 0.387 | 0.850 | 0.795 | 2.580 | 0.577 |
| **`condition_occurrence`** | 23 (11.4%) | 0.945 ± 0.058 | 0.980 | 0.830 | 1.570 | 0.957 |
| **`drug_era`** | 20 (10.0%) | 0.821 ± 0.303 | 0.980 | 0.866 | 2.600 | 0.700 |
| **`observation_period`** | 20 (10.0%) | 0.931 ± 0.113 | 0.980 | 1.000 | 1.650 | 0.950 |
| **`person`** | 9 (4.5%) | 0.984 ± 0.005 | 0.980 | 1.000 | 1.220 | 1.000 |
| **`cost`** | 3 (1.5%) | 0.947 ± 0.045 | 0.950 | 1.000 | 2.330 | 1.000 |
| **`care_site`** | 2 (1.0%) | 0.975 ± 0.035 | 0.975 | 1.000 | 1.000 | 1.000 |
| **`payer_plan_period`** | 2 (1.0%) | 0.970 ± 0.028 | 0.970 | 1.000 | 1.500 | 1.000 |
| **`vocabulary`** | 2 (1.0%) | 0.965 ± 0.021 | 0.965 | 1.000 | 3.000 | 1.000 |

*Notes: N: Sample Size. SD: Standard Deviation. IQR: Interquartile Range. Min – Max: Minimum and maximum observed values. 95% CI Mean: 95% confidence interval for the mean.*

<a id="figure-6"></a>
<div align="center">

![Figure 6. Mean Performance of the Agent by Primary OMOP CDM Domain](figures/fig06_acad_fig13_prof_performance_by_domain.png)

*Figure 6. Mean Performance of the Agent by Primary OMOP CDM Domain. Comparison between Mean Syntactic Validity and Vocabulary Terminological Precision against the 80% cutoff threshold.*

</div>

Differences across domains were statistically significant ($H = 15.65;\ p = 0.016$). While direct entity domains (`person`, `condition_occurrence`, `observation_period`) achieved success rates $\ge 95\%$, aggregated clinical persistence tables posed the greatest challenge. Direct comparison between the discrete event table (`condition_occurrence`) and its corresponding temporal derived table (`condition_era`) revealed a statistically significant penalty in agent performance ($U = 167.0;\ p = 0.0078$) ([Figure 6](#figure-6)).

### 4.5. Resolution Dynamics and Benefit of Interactive Refinement

The distribution of required conversational turns exhibited a strong dependence on query complexity ($\chi^2 = 23.11;\ p = 0.0001$) ([Figure 7](#figure-7)). At the low complexity level, 46.2% of problems were resolved in the first turn (*zero-shot*); conversely, in the complex stratum, only 15.4% achieved immediate resolution, with 46.2% requiring all three dialogue turns.

<a id="table-4"></a>
**Table 4.** *Contingency Table: Complexity Level × Executed Conversational Turns.*

| Complexity Level (N, Row %) | Turn 1 | Turn 2 | Turn 3 | Total |
| :--- | :---: | :---: | :---: | :---: |
| **Low** | 12 (46.2%) | 7 (26.9%) | 7 (26.9%) | 26 (100.0%) |
| **Intermediate** | 20 (28.2%) | 38 (53.5%) | 13 (18.3%) | 71 (100.0%) |
| **Complex** | 16 (15.4%) | 40 (38.5%) | 48 (46.2%) | 104 (100.0%) |
| **Overall Total** | **48 (23.9%)** | **85 (42.3%)** | **68 (33.8%)** | **201 (100.0%)** |

*Notes: N: Sample Size. SD: Standard Deviation. IQR: Interquartile Range. Min – Max: Minimum and maximum observed values. 95% CI Mean: 95% confidence interval for the mean.*

<a id="figure-7"></a>
<div align="center">

![Figure 7. Conversational Effort Required by Query Complexity (N = 201)](figures/fig07_acad_fig14_prof_conversational_effort.png)

*Figure 7. Conversational Effort Required by Query Complexity ($N = 201$). Proportion of cases resolved in Turn 1 (direct resolution), Turn 2 (moderate refinement), and Turn 3 (maximum interaction).*

</div>

The progressive evolution of validity scores across successive interventions describes a steady upward trajectory in both mean and median, as illustrated in [Figure 8](#figure-8).

<a id="figure-8"></a>
<div align="center">

![Figure 8. Trajectory of result improvement across conversational turns](figures/fig08_acad_fig15_prof_turn_improvement_trajectory.png)

*Figure 8. Trajectory of result improvement across conversational turns.*

</div>

Supervised conversational refinement acted as a corrective mechanism against initial ambiguities, rising from 23.9% initial success to a cumulative 81.6% ($164/201$) by the third turn ($\Delta = +57.7$ percentage points; $\chi^2 = 114.01;\ p < 0.001$). This progression along the cumulative efficacy curve across the three interaction turns is graphically detailed in [Figure 9](#figure-9).

<a id="figure-9"></a>
<div align="center">

![Figure 9. Cumulative Efficacy Curve of Conversational Refinement (N = 201)](figures/fig09_acad_fig16_prof_cumulative_efficacy_curve.png)

*Figure 9. Cumulative Efficacy Curve of Conversational Refinement ($N = 201$). Evolution of operational resolution rate ($\text{Validity} > 0.80$) from the initial Zero-Shot response to the third turn of interaction.*

</div>

<a id="table-5"></a>
**Table 5.** *Performance Progression and Net Gain (Delta) by Turn.*

| Evaluated Transition | Cohort (N) | Initial Validity | Final Validity | Mean (Median) Validity Delta | Improved Cases (N, %) | Wilcoxon Test ($W, p$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Turn 1 → Turn 2** | 153 | 0.316 ± 0.318 | 0.708 ± 0.356 | +0.392 (+0.350) | 118 (77.1%) | $W = 264.0$, $p < 0.001$ |
| **Turn 2 → Turn 3** | 68 | 0.394 ± 0.352 | 0.579 ± 0.421 | +0.185 (+0.195) | 45 (66.2%) | $W = 247.5$, $p < 0.001$ |
| **Turn 1 → Final Consolidated** | **201** | **0.468 ± 0.369** | **0.849 ± 0.271** | **+0.381 (+0.340)** | **133 (66.2%)** | **$W = 0.0$, $p < 0.001$** |

---

## 5. Discussion

### 5.1. Interpretation of Findings

The results confirm that modular decomposition via multi-agent systems effectively reduces the structural error rate in biomedical *Text-to-SQL* tasks. Using a deterministic validator agent against a live relational engine substantially mitigates the propagation of hallucinations in generated SQL code.

However, the gap between initial resolution in Turn 1 (23.9%) and the consolidated rate (81.6%) reveals that the base model tends to oversimplify relational formulations in the absence of explicit constraints. Analysis of the 37 cases (18.4%) unresolved after Turn 3 showed that failures did not stem from linguistic reasoning limitations of Gemini-2.5-Flash, but rather from the lack of specific guidelines in the Constructor subagent's *System Prompt* regarding OMOP CDM conventions.

### 5.2. Prompt Engineering Optimization Guidelines

Based on the error analysis, six priority guidelines were formalized for integration into the system:

1. **Strict differentiation of persistence domains:** Establish as a mandatory heuristic the use of `_era` tables in response to terms such as "episode", "persistence", or "duration", restricting occurrence tables to discrete events or dosage analyses.
2. **Automatic injection of taxonomic expansions:** Systematically integrate the `concept_ancestor` table in aggregated nosological or therapeutic analyses, preventing the omission of specific clinical subtypes.
3. **Integrity constraints on ontological catalogs:** Include explicit semantic invariants (`standard_concept = 'S'` and `invalid_reason IS NULL`) scoped by `domain_id` and `vocabulary_id`.
4. **Homogenization of aggregations:** Standardize the translation of patient counts using `COUNT(DISTINCT person_id)` and event counts using `COUNT(*)`.
5. **Parametric lexical search:** Preserve the use of case-insensitive clauses (`LOWER()`, `REGEXP_CONTAINS`) when handling non-canonical exploratory terms.
6. **Structuring via Common Table Expressions (CTEs):** Require the concatenation of modular logical blocks with explicit aliases in complex temporal aggregation queries.

Adopting these directives is projected to raise the *zero-shot* success rate above 55%, placing final overall validity around 92–94%.

### 5.3. Study Limitations

- **Terminological complexity of the *Gold Standard*:** The high vocabulary precision (92.5%) was evaluated on questions written using formal clinical terminology. Lower precision is to be expected when facing inputs containing hospital slang, non-standardized abbreviations, or spelling errors.
- **SQL dialect heterogeneity:** Although the solution was validated on BigQuery, real-world deployments across hospital consortia employ diverse database engines (PostgreSQL, SQL Server, Oracle, Snowflake), which will require a multi-dialect adaptation layer (e.g., OHDSI *SqlRender*).
- **Isolation from the live data environment:** In the current architecture, the agent provides the SQL query for subsequent execution by the clinician, interrupting the interactive workflow of direct result visualization.
- **Data governance and personal data protection:** The current system does not integrate a biomedical Named Entity Recognition (NER) de-identification layer prior to LLM processing—a *sine qua non* condition for strict GDPR compliance in clinical care settings.

---

## 6. Conclusions and Future Work

### 6.1. Conclusions

1. The technical and operational feasibility of the **OMOP Analytical Agent** as a natural language interface for querying clinical databases under the OMOP CDM 5.4 standard was demonstrated, achieving an overall syntactic validity of 84.9%.
2. The decoupled multi-agent architecture, reinforced with semantic retrieval (RAG) and runtime validation, demonstrated high ontological precision (92.5%) and guaranteed the executability of SQL statements in real analytical environments.
3. Iterative conversational refinement increased resolution by $+57.7$ percentage points over the initial response, demonstrating that guided interaction is an effective mechanism for correcting semantic ambiguities.
4. Complex queries and temporal aggregation domains (`_era`) constitute the primary computational bottleneck, delineating the need to incorporate schema heuristics and rules into the orchestration prompts.

### 6.2. Future Work

- **Migration to ADK 2.0 and transactional support:** Incorporate deterministic orchestration patterns guaranteeing mandatory passage through all syntactic validation stages.
- **Multi-dialect translation:** Integrate libraries such as *SqlRender* to dynamically compile statements across diverse relational engines (PostgreSQL, Snowflake, Databricks).
- **Client-side differential privacy and anonymization mechanisms:** Design a privacy auditing subagent that filters Personally Identifiable Information (PII) prior to transmission to foundation models.
- **Interactive data interrogation and report generation:** Securely connect the execution of validated queries with automated graphical visualization and statistical calculation modules for clinical users.

---

## 7. References

- Google. (2024). *Agent Development Kit (ADK) documentation*. Google Cloud Developers. https://cloud.google.com/products/agent-development-kit
- Hripcsak, G., Duke, J. D., Shah, N. H., Reich, C. G., Schilling, V. P., Schuemie, M. J., Suchard, M. A., Zorych, I., & Ryan, P. B. (2015). Observational Health Data Sciences and Informatics (OHDSI): Opportunities for observational researchers. *Studies in Health Technology and Informatics*, 216, 574–578.
- Observational Health Data Sciences and Informatics (OHDSI) Collaborative. (2021). *The Book of OHDSI: Observational Health Data Sciences and Informatics*. OHDSI Community. https://ohdsi.github.io/TheBookOfOhdsi/
- Observational Health Data Sciences and Informatics. (2024). *OMOP Common Data Model specification version 5.4*. OHDSI Community. https://ohdsi.github.io/CommonDataModel/cdm54.html
- Observational Health Data Sciences and Informatics. (2024). *QueryLibrary: Predefined queries for OMOP CDM*. GitHub repository. https://github.com/OHDSI/QueryLibrary
- SNOMED International. (2024). *SNOMED CT: Systematized Nomenclature of Medicine -- Clinical Terms*. https://www.snomed.org/
- World Health Organization. (2018). *ICD-11: International Classification of Diseases 11th Revision*. WHO.

---

## 8. Annexes

- **Source Code Repository:** https://github.com/sogire/tfm-ue-bioinformatica2526-agente-omop
- **Annex A:** Video demonstration of the OMOP Analytical Agent in operation ([Online Multimedia Resource](https://drive.google.com/file/d/1X5LAdfPPc92Amx8OGB7D8k7gLjz-4G9q/view?usp=sharing) | [Local File](Anexo-A_TFM_AgenteOMOP_Video-Demostracion.mp4)).
- **Annex B:** Formal specification of system prompts for subagents ([`Anexo-B_TFM_AgenteOMOP_Prompts-sistema-agente.docx`](Anexo-B_TFM_AgenteOMOP_Prompts-sistema-agente.docx)).
- **Annex C:** Reference query benchmark (*Gold Standard*, $N = 201$) ([`Anexo-C_TFM_AgenteOMOP_Listado-preguntas-y-evaluacion-individual.xlsx`](Anexo-C_TFM_AgenteOMOP_Listado-preguntas-y-evaluacion-individual.xlsx)).
- **Annex D:** Detailed tabular records of the automated quantitative evaluation ([`Anexo-D_AgenteOMOP_Resultados-evaluacion-cuantitativa.xlsx`](Anexo-D_AgenteOMOP_Resultados-evaluacion-cuantitativa.xlsx)).

---

<div align="right">

*October 2026. Sergio Bermúdez Sánchez ([LinkedIn](https://www.linkedin.com/in/sergio-bermudez-sanchez/))*

</div>
