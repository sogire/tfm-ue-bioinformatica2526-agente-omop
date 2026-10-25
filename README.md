> 🌐 **Idioma / Language:** **Español** | [English](README.en.md)

# AGENTE ANALÍTICO OMOP
## APLICACIÓN DE IA CONVERSACIONAL PARA DEMOCRATIZAR EL ANÁLISIS DE DATOS DE BASES DE DATOS CLÍNICAS OMOP CDM 5.4

**TRABAJO FIN DE MÁSTER** · Máster Universitario en Bioinformática 2025/2026 · Universidad Europea de Madrid  
*Autor: <a href="https://www.linkedin.com/in/sergio-bermudez-sanchez" target="_blank" rel="noopener noreferrer">Sergio Bermúdez Sánchez</a>* | *Tutor: Isidoro Gutiérrez Álvarez*  

El acceso a los datos de salud estandarizados bajo el modelo de datos común OMOP CDM sigue limitado por la necesidad de contar con conocimientos técnicos avanzados en SQL y conocer la estructura y jerarquías de los vocabularios OHDSI. Para resolver esta barrera, en este Trabajo Fin de Máster he desarrollado el Agente Analítico OMOP, una prueba de concepto basada en IA conversacional que permite a profesionales sanitarios e investigadores formular preguntas analíticas de caracterización e incidencia en lenguaje natural.

El **objetivo general** del proyecto es desarrollar y evaluar un sistema conversacional multiagente basado en Modelos de Lenguaje Masivos (LLM) capaz de interactuar de forma autónoma con bases de datos que cumplen el estándar OMOP CDM 5.4 (alojadas en Google BigQuery), posibilitando la formulación de consultas analíticas de caracterización de cohortes y cálculo de incidencia en lenguaje natural.

Como **objetivos específicos**, el trabajo contempla: (1) adaptar y enriquecer los metadatos del esquema OMOP CDM para su interpretación por agentes inteligentes; (2) integrar motores de búsqueda terminológica estandarizada (SNOMED CT, RxNorm) mediante arquitecturas RAG para validar conceptos médicos sin alucinaciones; y (3) generar y validar sintácticamente de manera automatizada sentencias SQL conformes al catálogo clínico de BigQuery tomando como base colecciones estandarizadas como la *OHDSI QueryLibrary*.

El proyecto se alinea de forma directa con los Objetivos de Desarrollo Sostenible (ODS), facilitando la alfabetización en datos del personal sanitario (ODS 4: Educación de calidad), democratizando el acceso analítico entre organizaciones con independencia de sus recursos bioinformáticos (ODS 10: Reducción de las desigualdades), optimizando la infraestructura técnica hospitalaria (ODS 9: Industria, innovación e infraestructura) y agilizando la obtención de evidencia clínica en beneficio del paciente (ODS 3: Salud y bienestar).

La arquitectura técnica del sistema se organiza en dos módulos principales interconectados:

* **Módulo de Agentes ([`agentes-omop/`](agentes-omop/README.md)):** Alberga el conjunto de desarrollos basados en Google Agent Development Kit (ADK) y modelos Gemini desplegados en Google Cloud Run. El **agente central objeto del Trabajo Fin de Máster y sometido a evaluación formal es [`omop_03_concepts_and_sql`](agentes-omop/agents-dev/omop_03_concepts_and_sql/README.md)**, especializado en la búsqueda/validación de conceptos OMOP y formulación Text-to-SQL para BigQuery. El resto de subagentes del directorio (`omop_01_consierge`, `omop_02_book_of_ohdsi`, `omop_04_phenotypes`, `omop_05_research` y `omop_06_r_scripts`) constituyen experimentos y prototipos exploratorios paralelos que abordaron otros retos del ecosistema OMOP/OHDSI (como aprendizaje personal y fuente de ideas futuras), no formando parte del alcance evaluado en la memoria académica. Para más detalles, consulte [`agentes-omop/README.md`](agentes-omop/README.md).

* **Marco de Evaluación Experimental ([`evaluacion-agente-omop-03/`](evaluacion-agente-omop-03/README.md)):** Entorno automatizado de pruebas (*benchmark*) diseñado para contrastar el desempeño del agente Text-to-SQL frente a un estándar de oro (*Gold Standard*) de 201 consultas clínicas categorizadas por nivel de complejidad y dominio OMOP. Incluye el protocolo de ejecución multiturno guiado por LLM como juez, extracción de métricas objetivas y análisis estadístico inferencial consolidado. Para más información, consulte [`evaluacion-agente-omop-03/README.md`](evaluacion-agente-omop-03/README.md).

Los resultados de la evaluación experimental confirman la validez de la solución: el agente alcanzó una precisión terminológica del vocabulario del **92.5%** (con un 90.0% de asignaciones conceptuales perfectas), una tasa de ejecutabilidad técnica del **93.5%** y una Validez Sintáctica y Estructural global que progresó desde el **23.9%** en el primer turno (*zero-shot*) hasta el **84.9%** (81.6% de éxito operativo) tras el refinamiento conversacional interactivo. A partir del análisis de errores del primer turno, se han documentado las directrices de optimización del *system prompt* en [`recomendaciones_mejora_agente.md`](evaluacion-agente-omop-03/evaluation/results/querylibrary_analisis_202609061551/recomendaciones_mejora_agente.md).

## Memorias y Anexos del TFM (`tfm-anexos/`)

En el directorio [`tfm-anexos/`](tfm-anexos/) se encuentran disponibles las memorias completas del proyecto y los anexos documentales y experimentales:

* **Memoria del TFM — Versión Original Entregada ([`TFM-AgenteOMOP_SergioBermudez_Version-ProfesionalSolucion.pdf`](tfm-anexos/TFM-AgenteOMOP_SergioBermudez_Version-ProfesionalSolucion.pdf) | [English Markdown](tfm-anexos/TFM-AgenteOMOP_SergioBermudez_Version-ProfesionalSolucion.en.md)):** Memoria inicial entregada, orientada a la arquitectura técnica, diseño de la solución e implementación práctica del sistema multiagente.
* **Memoria del TFM — Versión Académica ([`TFM-AgenteOMOP_SergioBermudez_Version-MemoriaAcademica.pdf`](tfm-anexos/TFM-AgenteOMOP_SergioBermudez_Version-MemoriaAcademica.pdf) | [English Markdown](tfm-anexos/TFM-AgenteOMOP_SergioBermudez_Version-MemoriaAcademica.en.md)):** Documento formal de la memoria académica del Trabajo Fin de Máster estructurado según la normativa universitaria (introducción, hipótesis y objetivos, metodología, resultados estadísticos, discusión y conclusiones).


* **Anexo A — Vídeo de Demostración ([`Anexo-A_TFM_AgenteOMOP_Video-Demostracion.mp4`](tfm-anexos/Anexo-A_TFM_AgenteOMOP_Video-Demostracion.mp4)):** Demostración multimedia en vídeo del funcionamiento interactivo del Agente Analítico OMOP resolviendo consultas clínicas en lenguaje natural.
* **Anexo B — Prompts del Sistema ([`Anexo-B_TFM_AgenteOMOP_Prompts-sistema-agente.docx`](tfm-anexos/Anexo-B_TFM_AgenteOMOP_Prompts-sistema-agente.docx)):** Especificación formal de las instrucciones de sistema (*system prompts*) diseñadas para el agente orquestador y cada uno de los subagentes especializados.
* **Anexo C — Listado de Preguntas y Evaluación Individual ([`Anexo-C_TFM_AgenteOMOP_Listado-preguntas-y-evaluacion-individual.xlsx`](tfm-anexos/Anexo-C_TFM_AgenteOMOP_Listado-preguntas-y-evaluacion-individual.xlsx)):** Banco completo de las 201 consultas clínicas de referencia (*Gold Standard*) junto con el desglose detallado de la evaluación individual por pregunta y turno conversacional.
* **Anexo D — Resultados de la Evaluación Cuantitativa ([`Anexo-D_AgenteOMOP_Resultados-evaluacion-cuantitativa.xlsx`](tfm-anexos/Anexo-D_AgenteOMOP_Resultados-evaluacion-cuantitativa.xlsx)):** Registros tabulares consolidados y tablas estadísticas descriptivas e inferenciales de la evaluación cuantitativa automatizada.


* **Recomendaciones de Mejora del Agente ([`recomendaciones_mejora_agente.md`](evaluacion-agente-omop-03/evaluation/results/querylibrary_analisis_202609061551/recomendaciones_mejora_agente.md)):** Directrices arquitectónicas, clínicas y de sintaxis SQL propuestas para optimizar el *system prompt* del agente `omop_03_concepts_and_sql` a partir de los hallazgos de la evaluación experimental.

## Cómo Citar este Trabajo

Si utiliza este agente, su marco de evaluación o los resultados de este estudio en otras investigaciones o publicaciones científicas, por favor referéncielo:

**En español (estilo Vancouver / NLM):**
> Bermúdez Sánchez S. Agente Analítico OMOP: aplicación de IA conversacional para democratizar el análisis de datos de bases de datos clínicas OMOP CDM 5.4 [Trabajo Fin de Máster en Bioinformática]. Madrid: Universidad Europea de Madrid; 2026 [citado AAAA Mes DD]. Disponible en español e inglés en: https://github.com/sogire/tfm-ue-bioinformatica2526-agente-omop

**En inglés (English):**
> Bermudez-Sanchez S. OMOP Analytical Agent: conversational AI application to democratize data analysis on OMOP CDM 5.4 clinical databases [master's thesis in Bioinformatics]. Madrid: Universidad Europea de Madrid; 2026 [cited YYYY Mon DD]. Available in English and Spanish from: https://github.com/sogire/tfm-ue-bioinformatica2526-agente-omop

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
