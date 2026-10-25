import os
from typing import Dict, Any, Optional
from google.cloud import bigquery
import re
from .utils import retry_on_quota_limit


# Import the config module from the current package
from . import config_agent


def get_credentials():
    """Retrieves default Google Cloud credentials.

    Uses the application-default credentials to authenticate and refreshes the
    token. This is useful for authenticating with Google Cloud services.

    Returns:
        A tuple containing:
        - credentials: The authenticated credentials object.
        - project_credentials: The project ID associated with the credentials.
        - auth_req: The authenticated request object.
    """
    import google.auth
    import google.auth.transport.requests
    import google.auth.impersonated_credentials
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    #Maybe the SA requires: Service Account Token Creator
    credentials, project_credentials = google.auth.default(scopes=scopes)
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    access_token = credentials.token
    return credentials, project_credentials, auth_req, access_token 

@retry_on_quota_limit
def search_omop_official_concepts(
    query: str, 
    vocabulary_id: str = 'SNOMED',
    domain_id: str = 'Condition',
) -> Dict[str, Any]:
    """
    Search for standard clinical concepts within the OMOP Common Data Model.

    This function queries the CONCEPT table in BigQuery to find 'Standard' 
    Concept IDs (standard_concept = 'S') that are active and valid. 
    It is the primary tool for mapping natural language clinical terms 
    to the structured IDs required for OMOP event table queries.

    Args:
        query: The clinical term or code to search for (e.g., 'Type 2 Diabetes', 'Lisinopril', or '443238').
        vocabulary_id: The source vocabulary filter. Options: 'SNOMED' (default for conditions), 
                      'RxNorm' (medications)
        domain_id: The clinical domain filter. Options: 'Condition', 'Device', 'Drug', 'Gender', 
                    'Geography', 'Language', 'Meas Value', 'Meas Value Operator', 'Measurement', 'Metadata', 
                    'Observation', 'Procedure', 'Provider', 'Race', 'Relationship', 'Route', 'Spec Anatomic Site', 
                    'Specimen', 'Type Concept', 'Unit', 'Visit'

    Returns:
        Dict containing the search status, a list of found concepts, the filters 
        applied, and the debug SQL executed for verification.

    Example:
        >>> search_omop_concepts("Hypertension", "SNOMED", "Condition", False)
        {
            'status': 'success',
            'count': 1,
            'concepts': [
                {
                    'concept_id': 316866, 
                    'concept_name': 'Hypertensive disorder', 
                    'domain_id': 'Condition', 
                    'vocabulary_id': 'SNOMED',
                }
            ],
            'applied_filters': {'vocabulary_id': 'SNOMED', 'domain_id': 'Condition'},
            'debug_sql': 'SELECT ... FROM ...concept WHERE ...'
        }
    
    If no results are found after 3 attempts with different vocabulary/domain combinations,
    stop and request more specific information from the user.
    """
    from google.auth import default

    credentials, project_credentials, auth_req, access_token = get_credentials()


    
    client = bigquery.Client()
    
    # Updated to use the config_agent namespace
    sql = f"""
        SELECT concept_id, concept_name, domain_id, vocabulary_id
        FROM `{config_agent.DATASET_TABLE_CONCEPTS}`
        WHERE invalid_reason IS NULL
        AND standard_concept = 'S'
    """
    

    sql += " AND (LOWER(concept_name) LIKE LOWER(@query))"

    if vocabulary_id:
        sql += " AND vocabulary_id = @vocab"
    if domain_id:
        sql += " AND domain_id = @domain"
    
    sql += " ORDER BY LENGTH(concept_name) ASC LIMIT 40"
    query_for_like = query.replace(' ','%')
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("query", "STRING", f"%{query_for_like}%"),
            bigquery.ScalarQueryParameter("vocab", "STRING", vocabulary_id),
            bigquery.ScalarQueryParameter("domain", "STRING", domain_id)
        ]
    )
    
    try:
        #print(sql)
        query_job = client.query(sql, job_config=job_config)
        results = query_job.result()
        concept_list = [dict(row) for row in results]
        
        return {
            "status": "success",
            "count": len(concept_list),
            "concepts": concept_list,
            "filters": {"vocab": vocabulary_id, "domain": domain_id},
            "debug_sql": sql.strip()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def validate_omop_sql(sql_query: str) -> Dict[str, Any]:
    """
    Validates a BigQuery SQL query against the OMOP v5.4 schema.

    This tool performs a 'Dry Run' to check for syntax errors and table 
    existence. It validates the query against the production-grade 
    dataset specified in the configuration.

    Args:
        sql_query: The full BigQuery SQL string to be validated.

    Returns:
        Dict with validation results, including cost estimates and error details.
    
    Example:
        >>> validate_omop_sql("SELECT count(*) FROM `condition_occurrence`")
        {
            'status': 'success',
            'is_valid': True,
            'estimated_cost_mb': 10.5,
            'verified_against': 'bio-med-480108.OMOP_54_A'
        }
    """
    client = bigquery.Client()
    
    # We use QueryJobConfig to perform a dry run (costs $0)
    job_config = bigquery.QueryJobConfig(
        dry_run=True, 
        use_query_cache=False,
        # Setting default_dataset allows the agent to write shorter queries
        default_dataset=config_agent.DATASET_FOR_VALIDATIONS 
    )

    try:

        sanitized_sql = sql_query
        pattern = r"`?([\w-]+)\.([\w-]+)\.([\w-]+)`?"
        replacement = f"`{config_agent.DATASET_FOR_VALIDATIONS}.\\3`"
        sanitized_sql = re.sub(pattern, replacement, sql_query)
        query_job = client.query(sanitized_sql, job_config=job_config)
        
        return {
            "status": "success",
            "is_valid": True,
            "estimated_bytes": query_job.total_bytes_processed,
            "estimated_cost_mb": round(query_job.total_bytes_processed / (1024 * 1024), 2),
            "referenced_tables": [str(t) for t in query_job.referenced_tables],
            "verified_against": config_agent.DATASET_FOR_VALIDATIONS
        }
    except Exception as e:
        return {
            "status": "error",
            "is_valid": False,
            "error_message": str(e),
            "note": f"Ensure tables belong to {config_agent.DATASET_FOR_VALIDATIONS}"
        }