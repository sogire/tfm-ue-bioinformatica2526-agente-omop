> 🏠 **[Main README](../../../README.en.md)** › **[Multi-Agent Ecosystem](../../README.en.md)** · 🌐 **Language / Idioma:** [Español](README.md) | **English**

# omop_06_r_scripts

This agent acts as a lead R development architect for the OHDSI and DARWIN EU ecosystems, specialized in creating reproducible, evidence-based analytical scripts for studies over OMOP CDM. Its workflow is grounded in a *Search-First* strategy via `get_search_results`, directly extracting code snippets, official vignettes, and function signatures from libraries such as CDMConnector, CohortMethod, and Capr to ensure maximum accuracy and compatibility.

The agent's objective is to synthesize complete, executable R scripts that incorporate explicit namespace calls (`package::function()`), database connection logic, cohort generation, execution of the primary analysis, and standardized CSV result export, explaining key parameters and citing the documentary sources used without executing the code in the environment.

