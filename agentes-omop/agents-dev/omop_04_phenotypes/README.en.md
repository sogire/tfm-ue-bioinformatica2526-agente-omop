> 🏠 **[Main README](../../../README.en.md)** › **[Multi-Agent Ecosystem](../../README.en.md)** · 🌐 **Language / Idioma:** [Español](README.md) | **English**

# omop_04_phenotypes

This agent acts as a *Clinical Librarian* within the OHDSI community, responsible for retrieving, analyzing, and tailoring standardized clinical phenotype definitions stored in Google Cloud Storage repositories. Using Vertex AI Search (`get_search_results`) and the `get_phenotype_details` retrieval tool, it identifies candidate phenotypes that best address the user's clinical need and justifies their medical relevance.

Rather than exposing raw code upfront, the agent breaks down the logic into an understandable clinical summary (primary entry events, inclusion/exclusion criteria, observation windows, and concept sets), assists the user in customizing temporal or demographic parameters, and consolidates the final definition in memory under the `phenotype_to_work` key for downstream reuse by other agents in the system.

