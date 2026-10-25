> 🌐 **Language / Idioma:** [Español](README.md) | **English**

# OMOP ANALYTICAL AGENT
## CONVERSATIONAL AI APPLICATION TO DEMOCRATIZE DATA ANALYSIS ON OMOP CDM 5.4 CLINICAL DATABASES

**MASTER'S THESIS (TFM)** · Master's Degree in Bioinformatics 2025/2026 · Universidad Europea de Madrid  
*Author: <a href="https://www.linkedin.com/in/sergio-bermudez-sanchez" target="_blank" rel="noopener noreferrer">Sergio Bermúdez Sánchez</a>* | *Supervisor: Isidoro Gutiérrez Álvarez*  

Access to standardized health data under the OMOP CDM common data model remains constrained by the requirement for advanced technical knowledge in SQL and familiarity with the structure and hierarchies of OHDSI vocabularies. To overcome this barrier, in this Master's Thesis I developed the OMOP Analytical Agent, a conversational AI proof of concept that enables healthcare professionals and researchers to formulate cohort characterization and incidence analytical questions in natural language.

The **general objective** of the project is to develop and evaluate a Large Language Model (LLM)-based multi-agent conversational system capable of autonomously interacting with databases conforming to the OMOP CDM 5.4 standard (hosted on Google BigQuery), enabling the formulation of cohort characterization and incidence calculation queries in natural language.

As **specific objectives**, the work encompasses: (1) adapting and enriching the OMOP CDM schema metadata for interpretation by intelligent agents; (2) integrating standardized terminological search engines (SNOMED CT, RxNorm) through RAG architectures to validate medical concepts without hallucinations; and (3) automatically generating and syntactically validating SQL statements compliant with the BigQuery clinical catalog based on standardized collections such as the *OHDSI QueryLibrary*.

The project directly aligns with the Sustainable Development Goals (SDGs), fostering data literacy among healthcare personnel (SDG 4: Quality Education), democratizing analytical access across organizations regardless of their bioinformatics resources (SDG 10: Reduced Inequalities), optimizing hospital technical infrastructure (SDG 9: Industry, Innovation and Infrastructure), and accelerating the generation of clinical evidence for patient benefit (SDG 3: Good Health and Well-being).

The technical architecture of the system is organized into two main interconnected modules:

* **Agents Module ([`agentes-omop/`](agentes-omop/README.en.md)):** Hosts the suite of developments built on the Google Agent Development Kit (ADK) and Gemini models deployed on Google Cloud Run. The **core agent subject of the Master's Thesis and formally evaluated is [`omop_03_concepts_and_sql`](agentes-omop/agents-dev/omop_03_concepts_and_sql/README.en.md)**, specialized in OMOP concept search/validation and Text-to-SQL formulation for BigQuery. The remaining subagents in the directory (`omop_01_consierge`, `omop_02_book_of_ohdsi`, `omop_04_phenotypes`, `omop_05_research`, and `omop_06_r_scripts`) constitute parallel exploratory experiments and prototypes addressing other challenges within the OMOP/OHDSI ecosystem (serving as personal learning and a source of future ideas) and are outside the scope formally evaluated in the academic thesis. For further details, see [`agentes-omop/README.en.md`](agentes-omop/README.en.md).

* **Experimental Evaluation Framework ([`evaluacion-agente-omop-03/`](evaluacion-agente-omop-03/README.en.md)):** Automated testing environment (*benchmark*) designed to evaluate the performance of the Text-to-SQL agent against a *Gold Standard* of 201 clinical queries categorized by complexity level and OMOP domain. It includes the LLM-as-a-judge multi-turn execution protocol, objective metric extraction, and consolidated inferential statistical analysis. For more information, see [`evaluacion-agente-omop-03/README.en.md`](evaluacion-agente-omop-03/README.en.md).

The experimental evaluation results confirm the validity of the solution: the agent achieved a vocabulary terminological precision of **92.5%** (with 90.0% perfect concept assignments), a technical executability rate of **93.5%**, and an overall Syntactic and Structural Validity that progressed from **23.9%** on the first turn (*zero-shot*) to **84.9%** (81.6% operational success) following interactive conversational refinement. Based on the first-turn error analysis, optimization guidelines for the *system prompt* have been documented in [`recomendaciones_mejora_agente.en.md`](evaluacion-agente-omop-03/evaluation/results/querylibrary_analisis_202609061551/recomendaciones_mejora_agente.en.md) ([Spanish version](evaluacion-agente-omop-03/evaluation/results/querylibrary_analisis_202609061551/recomendaciones_mejora_agente.md)).

## Thesis Reports and Annexes (`tfm-anexos/`)

The full project reports and documentary/experimental annexes are available in the [`tfm-anexos/`](tfm-anexos/) directory:

* **Master's Thesis Report — Original Submitted Version ([English Markdown](tfm-anexos/TFM-AgenteOMOP_SergioBermudez_Version-ProfesionalSolucion.en.md) | [Spanish PDF (`TFM-AgenteOMOP_SergioBermudez_Version-ProfesionalSolucion.pdf`)](tfm-anexos/TFM-AgenteOMOP_SergioBermudez_Version-ProfesionalSolucion.pdf)):** Initial submitted report focused on technical architecture, solution design, and practical implementation of the multi-agent system.
* **Master's Thesis Report — Academic Version ([English Markdown](tfm-anexos/TFM-AgenteOMOP_SergioBermudez_Version-MemoriaAcademica.en.md) | [Spanish PDF (`TFM-AgenteOMOP_SergioBermudez_Version-MemoriaAcademica.pdf`)](tfm-anexos/TFM-AgenteOMOP_SergioBermudez_Version-MemoriaAcademica.pdf)):** Formal academic thesis document structured according to university regulations (introduction, hypothesis and objectives, methodology, statistical results, discussion, and conclusions).


* **Annex A — Demonstration Video ([`Anexo-A_TFM_AgenteOMOP_Video-Demostracion.mp4`](tfm-anexos/Anexo-A_TFM_AgenteOMOP_Video-Demostracion.mp4)):** Multimedia video demonstration of the interactive operation of the OMOP Analytical Agent resolving clinical queries in natural language.
* **Annex B — System Prompts ([`Anexo-B_TFM_AgenteOMOP_Prompts-sistema-agente.docx`](tfm-anexos/Anexo-B_TFM_AgenteOMOP_Prompts-sistema-agente.docx)):** Formal specification of the *system prompts* designed for the orchestrator agent and each of the specialized subagents.
* **Annex C — Question List and Individual Evaluation ([`Anexo-C_TFM_AgenteOMOP_Listado-preguntas-y-evaluacion-individual.xlsx`](tfm-anexos/Anexo-C_TFM_AgenteOMOP_Listado-preguntas-y-evaluacion-individual.xlsx)):** Complete benchmark of the 201 reference clinical queries (*Gold Standard*) along with the detailed breakdown of individual evaluation by question and conversational turn.
* **Annex D — Quantitative Evaluation Results ([`Anexo-D_AgenteOMOP_Resultados-evaluacion-cuantitativa.xlsx`](tfm-anexos/Anexo-D_AgenteOMOP_Resultados-evaluacion-cuantitativa.xlsx)):** Consolidated tabular records and descriptive/inferential statistical tables from the automated quantitative evaluation.


* **Agent Improvement Recommendations ([`recomendaciones_mejora_agente.en.md`](evaluacion-agente-omop-03/evaluation/results/querylibrary_analisis_202609061551/recomendaciones_mejora_agente.en.md)):** Architectural, clinical, and SQL syntax guidelines proposed to optimize the `omop_03_concepts_and_sql` agent *system prompt* based on experimental evaluation findings.

## How to Cite

If you use this agent, its evaluation framework, or the findings of this study in other research or scientific publications, please cite it:

**In English (Vancouver / NLM style):**
> Bermudez-Sanchez S. OMOP Analytical Agent: conversational AI application to democratize data analysis on OMOP CDM 5.4 clinical databases [master's thesis in Bioinformatics]. Madrid: Universidad Europea de Madrid; 2026 [cited YYYY Mon DD]. Available in English and Spanish from: https://github.com/sogire/tfm-ue-bioinformatica2526-agente-omop

**In Spanish (En español):**
> Bermúdez Sánchez S. Agente Analítico OMOP: aplicación de IA conversacional para democratizar el análisis de datos de bases de datos clínicas OMOP CDM 5.4 [Trabajo Fin de Máster en Bioinformática]. Madrid: Universidad Europea de Madrid; 2026 [citado AAAA Mes DD]. Disponible en español e inglés en: https://github.com/sogire/tfm-ue-bioinformatica2526-agente-omop

**BibTeX (English):**
```bibtex
@mastersthesis{bermudez2026omop,
  author  = {Bermudez-Sanchez, Sergio},
  title   = {{OMOP Analytical Agent: Conversational AI Application to Democratize Data Analysis on OMOP CDM 5.4 Clinical Databases}},
  school  = {Universidad Europea de Madrid},
  address = {Madrid, Spain},
  year    = {2026},
  type    = {Master's Thesis in Bioinformatics},
  url     = {https://github.com/sogire/tfm-ue-bioinformatica2526-agente-omop},
  note    = {Available in English and Spanish}
}
```

**BibTeX (Español):**
```bibtex
@mastersthesis{bermudez2026omop,
  author  = {Bermudez-Sanchez, Sergio},
  title   = {{Agente Anal{\'i}tico OMOP: aplicaci{\'o}n de IA conversacional para democratizar el an{\'a}lisis de datos de bases de datos cl{\'i}nicas OMOP CDM 5.4}},
  school  = {Universidad Europea de Madrid},
  address = {Madrid, Spain},
  year    = {2026},
  type    = {Trabajo Fin de M{\'a}ster en Bioinform{\'a}tica},
  url     = {https://github.com/sogire/tfm-ue-bioinformatica2526-agente-omop},
  note    = {Disponible en espa{\~n}ol e ingl{\'e}s / Available in Spanish and English}
}
```

