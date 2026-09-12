# omop_06_r_scripts

Este agente actúa como arquitecto principal de desarrollo en R para el ecosistema OHDSI y DARWIN EU, especializado en la creación de scripts analíticos reproducibles y basados en la evidencia para estudios sobre OMOP CDM. Su flujo de trabajo se fundamenta en una estrategia de búsqueda previa (*Search-First*) mediante `get_search_results`, extrayendo directamente fragmentos de código, viñetas oficiales y signaturas de funciones de librerías como CDMConnector, CohortMethod y Capr para garantizar la máxima exactitud y compatibilidad.

El objetivo del agente es sintetizar scripts completos y ejecutables en R que incorporan llamadas explícitas a espacios de nombres (`paquete::funcion()`), lógica de conexión a la base de datos, generación de cohortes, ejecución del análisis principal y exportación estándar de resultados a formato CSV, explicando los parámetros clave y citando las fuentes documentales utilizadas sin ejecutar el código en el entorno.
