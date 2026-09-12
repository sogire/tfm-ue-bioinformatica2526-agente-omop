# omop_05_research

Este agente desempeña el papel de epidemiólogo clínico sénior y especialista en fenotipado OHDSI, con la misión de transformar ideas clínicas de alto nivel en preguntas de investigación rigurosamente estructuradas y preparadas para su posterior traducción a SQL. Para ello, clasifica el diseño del estudio según el paradigma epidemiológico correspondiente (caracterización clínica, estimación causal a nivel poblacional o predicción a nivel de paciente).

Su metodología de trabajo implementa el marco formal T-C-O-TAR (cohorte objetivo *Target*, comparador *Comparator*, desenlace de interés *Outcome* y ventana temporal de riesgo *Time-at-Risk*). Además, proyecta las entidades clínicas sobre las tablas maestras de OMOP CDM v5.4 y genera un esquema lógico de consulta (*SQL Logic Blueprint*) que detalla los criterios de inclusión, exclusión y uniones necesarias para la materialización analítica del estudio.
