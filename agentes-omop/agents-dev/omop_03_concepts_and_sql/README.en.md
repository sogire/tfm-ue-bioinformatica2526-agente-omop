> 🏠 **[Main README](../../../README.en.md)** › **[Multi-Agent Ecosystem](../../README.en.md)** · 🌐 **Language / Idioma:** [Español](README.md) | **English**

# omop_03_concepts_and_sql

This agent operates as a senior data scientist specialized in translating clinical intents into Google BigQuery-compatible SQL queries over the OMOP CDM v5.4 model. Its priority objective is to ensure maximum terminological and syntactic fidelity through a two-phase collaborative workflow: first, it locates and disambiguates standard medical concepts via the `search_omop_official_concepts` tool, presenting a tabulated shortlist for explicit, mandatory user confirmation before proceeding to write any code.

Once the clinical concepts are validated, the agent builds the SQL query adapted to native Google BigQuery syntax, applying the appropriate data types (`FLOAT64`, `BIGNUMERIC`), resolving joins across clinical tables, and mandatorily verifying the executability of the statement via the `validate_omop_sql` tool before presenting the final result.

