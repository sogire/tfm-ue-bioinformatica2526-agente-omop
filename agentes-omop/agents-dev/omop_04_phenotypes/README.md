# omop_04_phenotypes

Este agente ejerce como documentalista clínico (*Clinical Librarian*) dentro de la comunidad OHDSI, encargado de la recuperación, análisis y ajuste de definiciones de fenotipos clínicos estandarizados almacenados en repositorios de Google Cloud Storage. Mediante el uso de Vertex AI Search (`get_search_results`) y la herramienta de recuperación `get_phenotype_details`, identifica los fenotipos candidatos que mejor responden a la necesidad clínica del usuario y justifica su pertinencia médica.

En lugar de exponer el código bruto inicial, el agente desglosa la lógica en un resumen clínico comprensible (eventos de entrada primarios, criterios de inclusión/exclusión, ventanas de observación y conjuntos de conceptos), asiste al usuario en la personalización de parámetros temporales o demográficos y consolida la definición final en memoria bajo la clave `phenotype_to_work` para su posterior reutilización por otros agentes del sistema.
