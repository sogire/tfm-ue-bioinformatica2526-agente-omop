> 🏠 **[Main README](../../../README.en.md)** › **[Multi-Agent Ecosystem](../../README.en.md)** · 🌐 **Language / Idioma:** [Español](README.md) | **English**

# omop_05_research

This agent serves as a senior clinical epidemiologist and OHDSI phenotyping specialist, with the mission of transforming high-level clinical ideas into rigorously structured research questions ready for subsequent translation into SQL. To achieve this, it classifies the study design according to the corresponding epidemiological paradigm (clinical characterization, population-level causal estimation, or patient-level prediction).

Its workflow methodology implements the formal T-C-O-TAR framework (*Target* cohort, *Comparator*, *Outcome* of interest, and *Time-at-Risk* temporal window). In addition, it maps clinical entities onto the master tables of OMOP CDM v5.4 and generates a *SQL Logic Blueprint* detailing the inclusion criteria, exclusion criteria, and joins required for the analytical materialization of the study.

