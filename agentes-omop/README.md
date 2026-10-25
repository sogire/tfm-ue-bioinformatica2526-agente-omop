> 🏠 **[README Principal](../README.md)** · 🌐 **Idioma / Language:** **Español** | [English](README.en.md)

# Ecosistema Multiagente OMOP CDM (`omop-agent-path`)

Marco multiagente basado en **Google Agent Development Kit (ADK)** diseñado para asistir en la investigación biomédica, el fenotipado clínico, la formulación de consultas analíticas y el diseño de estudios observacionales sobre el modelo común de datos **OMOP CDM 5.4** alojado en **Google BigQuery** (`bio-med-480108.OMOP_54_A`).

El sistema se compone de una suite de agentes especializados que colaboran para cubrir todo el ciclo de vida de la investigación en salud, desde la definición de la pregunta epidemiológica hasta la generación de código SQL y scripts en R basados en las metodologías oficiales de **OHDSI** (*Observational Health Data Sciences and Informatics*).

---

## 📁 Estructura del Repositorio

```text
agentes-omop/
├── README.md                     # Este documento
├── Dockerfile.dev                # Imagen de contenedor para despliegue en Cloud Run con ADK Web
├── cloudbuild.yaml               # Configuración de compilación con Google Cloud Build
├── config-dev.sh                 # Variables de entorno y configuración del proyecto en GCP
├── config-dev.template.sh        # Plantilla desidentificada y comentada para nuevos despliegues
├── deploy_cloudrun.sh            # Script automatizado de compilación y despliegue en Cloud Run
├── deploy_iap_cloudrun.sh        # Configuración de seguridad con Identity-Aware Proxy (IAP)
├── deploy_roles_cloudrun.sh      # Asignación de roles IAM y cuentas de servicio
├── deploy_enable_apis.sh         # Habilitación de APIs requeridas en Google Cloud
├── start-command.sh              # Inicialización de entorno local de desarrollo
└── agents-dev/                   # Directorio de los subagentes especializados
    ├── requirements.txt          # Dependencias de Python del conjunto de agentes
    ├── omop_01_consierge/        # Conserje conversacional y delimitación de alcance
    ├── omop_02_book_of_ohdsi/    # Especialista metodológico en 'The Book of OHDSI'
    ├── omop_03_concepts_and_sql/ # Agente Text-to-SQL con validación en BigQuery
    ├── omop_04_phenotypes/       # Documentalista clínico y gestor de fenotipos
    ├── omop_05_research/         # Epidemiólogo clínico y estructuración T-C-O-TAR
    └── omop_06_r_scripts/        # Arquitecto en R para paquetes OHDSI y DARWIN EU
```

---

## 🤖 Catálogo de Agentes (`agents-dev/`)

> [!IMPORTANT]
> **Agente Objeto del TFM y su Evaluación:**
> El **agente central objeto de la investigación y sometido al banco de pruebas experimental del TFM es [`omop_03_concepts_and_sql`](agents-dev/omop_03_concepts_and_sql/README.md)**.
> El resto de agentes presentes en este directorio (`omop_01_consierge`, `omop_02_book_of_ohdsi`, `omop_04_phenotypes`, `omop_05_research` y `omop_06_r_scripts`) han sido **experimentos paralelos** implementados para explorar la resolución de otras tipologías de retos dentro del ecosistema OMOP/OHDSI. Han servido como aprendizaje personal y fuente de ideas futuras, pero **no son objeto de evaluación en la memoria del Trabajo Fin de Máster**.

Cada subagente cuenta con su propia configuración, asignación de herramientas (*tools*) y documentación detallada en su correspondiente `README.md`:

### ⭐ Agente Central del TFM (Evaluado Formalmente)

#### [`omop_03_concepts_and_sql`](agents-dev/omop_03_concepts_and_sql/README.md) — Agente Text-to-SQL OMOP BigQuery
* **Perfil:** Científico de datos técnico con flujo colaborativo guiado.
* **Objetivo:** Traduce necesidades clínicas en consultas SQL precisas y optimizadas para Google BigQuery sobre OMOP CDM 5.4. Opera en un protocolo estricto de dos fases: en primer lugar, busca y desambigua conceptos médicos mediante `search_omop_official_concepts`, requiriendo la aprobación explícita del usuario sobre una tabla Markdown; a continuación, formula la sentencia SQL aplicando tipos nativos de BigQuery (`FLOAT64`, `BIGNUMERIC`) y verifica obligatoriamente su sintaxis con `validate_omop_sql` antes de presentar el resultado.

---

### 🧪 Experimentos Exploratorios Paralelos (Fuera del Alcance del TFM)

#### 1. [`omop_01_consierge`](agents-dev/omop_01_consierge/README.md) — Conserje y Coordinador General
* **Perfil:** Asistente conversacional y orientador biomédico.
* **Objetivo:** Actúa como punto de contacto inicial para el usuario, asegurando que todas las interacciones se circunscriban estrictamente al ámbito de OMOP CDM y las herramientas de OHDSI (ATLAS, HADES, ATHENA). Orienta sobre el esquema de tablas OMOP v5.4, dominios de datos y vocabularios estandarizados, redirigiendo con cortesía cualquier consulta externa al análisis clínico.

#### 2. [`omop_02_book_of_ohdsi`](agents-dev/omop_02_book_of_ohdsi/README.md) — Especialista Metodológico OHDSI
* **Perfil:** Científico de datos de salud sénior fundamentado en la literatura oficial.
* **Objetivo:** Proporciona orientación metodológica contrastada sobre diseño de estudios observacionales, estimación a nivel poblacional (*Population-Level Estimation*) y predicción a nivel de paciente (*Patient-Level Prediction*). Su conocimiento está anclado en *The Book of OHDSI* mediante la herramienta de búsqueda semántica `get_search_results`, instruyendo además en las mejores prácticas de ATHENA y la suite HADES.

#### 3. [`omop_04_phenotypes`](agents-dev/omop_04_phenotypes/README.md) — Documentalista Clínico y Gestor de Fenotipos
* **Perfil:** Documentalista clínico (*Clinical Librarian*) para cohortes estandarizadas.
* **Objetivo:** Descubre, recupera y evalúa definiciones estándar de fenotipos almacenadas en Google Cloud Storage mediante Vertex AI Search (`get_search_results`) y `get_phenotype_details`. Presenta resúmenes estructurados (eventos de entrada, criterios lógicos, ventanas de observación y conjuntos de conceptos), asiste en la parametrización de filtros y almacena la definición final en memoria (`phenotype_to_work`) para su uso en análisis posteriores.

#### 4. [`omop_05_research`](agents-dev/omop_05_research/README.md) — Epidemiólogo Clínico y Diseño de Investigación
* **Perfil:** Epidemiólogo clínico sénior y consultor de estudios observacionales.
* **Objetivo:** Transforma ideas clínicas preliminares en preguntas de investigación rigurosamente estructuradas. Clasifica el estudio (caracterización, estimación o predicción), desglosa los componentes de la cohorte empleando el marco formal **T-C-O-TAR** (*Target, Comparator, Outcome, Time-at-Risk*), mapea las variables a tablas maestras de OMOP y genera un esquema lógico de consulta (*SQL Logic Blueprint*) con los criterios y uniones requeridos.

#### 5. [`omop_06_r_scripts`](agents-dev/omop_06_r_scripts/README.md) — Arquitecto en R para OHDSI y DARWIN EU
* **Perfil:** Desarrollador sénior de software estadístico en R para ciencias de la vida.
* **Objetivo:** Genera scripts en R reproducibles, robustos y basados en evidencia para estudios sobre OMOP CDM. Aplica una estrategia de búsqueda previa (*Search-First*) con `get_search_results` para incorporar sintaxis y viñetas oficiales de librerías como CDMConnector, CohortMethod y Capr, produciendo código ejecutable con llamadas explícitas a espacios de nombres, conexión a base de datos, generación de cohortes y exportación estandarizada a CSV.

---

## 🔄 Flujo de Trabajo Integrado entre Agentes

Los agentes están concebidos para complementarse secuencialmente a lo largo de una investigación clínica:

| Etapa de la Investigación | Agente Responsable | Entradas Principales | Salidas Clave |
| :--- | :--- | :--- | :--- |
| **1. Acogida y Delimitación** | [`omop_01_consierge`](agents-dev/omop_01_consierge/README.md) | Consulta o inquietud médica inicial del usuario | Alcance delimitado y orientación sobre tablas/herramientas |
| **2. Estructuración Epidemiológica** | [`omop_05_research`](agents-dev/omop_05_research/README.md) | Pregunta de investigación clínica | Definición T-C-O-TAR y esquema lógico (*SQL Logic Blueprint*) |
| **3. Búsqueda y Ajuste de Cohortes** | [`omop_04_phenotypes`](agents-dev/omop_04_phenotypes/README.md) | Criterios clínicos del estudio | JSON de fenotipo estándar en memoria (`phenotype_to_work`) |
| **4. Formulación Text-to-SQL (Núcleo del TFM)** | [`omop_03_concepts_and_sql`](agents-dev/omop_03_concepts_and_sql/README.md) | Intención analítica o *Blueprint* | Concept IDs aprobados y consulta SQL BigQuery validada |
| **5. Asesoría Metodológica** | [`omop_02_book_of_ohdsi`](agents-dev/omop_02_book_of_ohdsi/README.md) | Dudas sobre diseño, inferencia o sesgos | Recomendaciones fundamentadas en *The Book of OHDSI* |
| **6. Implementación en R** | [`omop_06_r_scripts`](agents-dev/omop_06_r_scripts/README.md) | Diseño de cohorte o necesidad analítica | Scripts en R completos con librerías HADES y DARWIN EU |

---

## 🚀 Despliegue en Google Cloud Platform

El despliegue del conjunto de agentes se realiza sobre **Google Cloud Run** ejecutando el servidor de aplicaciones de ADK (`adk web`), empaquetado mediante un contenedor Docker multietapa.

### Requisitos Previos
* Proyecto en Google Cloud configurado (región con soporte para Vertex AI y Cloud Run).
* Google Cloud CLI (`gcloud`) autenticado y con los permisos de despliegue adecuados.
* Archivo de variables de entorno configurado. Se incluye una plantilla desidentificada y documentada: [`config-dev.template.sh`](config-dev.template.sh) (copiar a `config-dev.sh` y rellenar con las credenciales y datasets del proyecto).
* Archivos de configuración de cada subagente configurados (`agents-dev/*/config_agent.py`), generados a partir de sus respectivas plantillas desidentificadas `config_agent.template.py`.

### Scripts de Gestión de Infraestructura

1. **Habilitación de Servicios en GCP:**
   ```bash
   ./deploy_enable_apis.sh
   ```
   Activa las APIs de Cloud Run, Cloud Build, Artifact Registry, Vertex AI e Identity-Aware Proxy.

2. **Configuración de Permisos y Roles IAM:**
   ```bash
   ./deploy_roles_cloudrun.sh
   ```
   Otorga los roles necesarios a la cuenta de servicio (`omop-training@bio-med-480108.iam.gserviceaccount.com`).

3. **Compilación y Despliegue en Cloud Run:**
   ```bash
   ./deploy_cloudrun.sh dev
   ```
   Compila la imagen del contenedor mediante Google Cloud Build utilizando [`cloudbuild.yaml`](cloudbuild.yaml) y [`Dockerfile.dev`](Dockerfile.dev), y despliega el servicio en Cloud Run con las variables de entorno asociadas a Vertex AI y BigQuery.

4. **Seguridad y Control de Acceso con IAP:**
   ```bash
   ./deploy_iap_cloudrun.sh
   ```
   Configura el balanceador de carga y la protección perimetral mediante Identity-Aware Proxy para acceso restringido a usuarios autorizados.

### Ejecución en Entorno Local de Desarrollo
Para levantar los agentes localmente con recarga en caliente:
```bash
# Activar entorno virtual e instalar dependencias
source ../.venv/bin/activate
pip install -r agents-dev/requirements.txt

# Ejecutar el servidor ADK
adk web --host 127.0.0.1 --port 8080 agents-dev
```
