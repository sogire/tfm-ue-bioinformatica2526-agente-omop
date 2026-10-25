import os
from typing import Dict, Any, Optional
from google.cloud import bigquery
import re
from google.api_core import exceptions

from . import config_agent

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)

# Import the config module from the current package


# Standard Configurations
## Limits

# Use this decorator on any tool or function that calls Vertex AI/Gemini
retry_on_quota_limit = retry(
    # Wait with exponential backoff: 1s, 2s, 4s, 8s... up to 30s
    wait=wait_random_exponential(min=1, max=30),
    # Stop trying after 5 attempts
    stop=stop_after_attempt(5),
    # Only retry on 429 (Quota) or 503 (Server Busy)
    retry=retry_if_exception_type((exceptions.ResourceExhausted, exceptions.ServiceUnavailable)),
    reraise=True
)


# Standard Configurations
## Limits
## https://google.github.io/adk-docs/runtime/runconfig/#max_llm_calls
from google.adk.agents import RunConfig
runtime_config_agent = RunConfig(
    max_llm_calls=5
)
## Logging
## https://google.github.io/adk-docs/integrations/bigquery-agent-analytics/
from google.adk.plugins.bigquery_agent_analytics_plugin import BigQueryAgentAnalyticsPlugin, BigQueryLoggerConfig
bq_logging_plugin = BigQueryAgentAnalyticsPlugin(
    project_id=config_agent.BQ_LOG_PROJECT,
    dataset_id=config_agent.BQ_LOG_DATASET,
    table_id=config_agent.BQ_LOG_TABLE,
    location=config_agent.BQ_LOG_LOCATION,
    config=BigQueryLoggerConfig(
        enabled=True,
        batch_size=1,
        max_content_length=(500 * 1024),
        custom_tags={
            "env": os.getenv("ENV", "local"),
            "role":"tester",
            "user_email":"sbs@example.com"
        }
    )
)
