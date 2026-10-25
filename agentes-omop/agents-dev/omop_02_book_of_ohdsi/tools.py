import os
from typing import Dict, Any, Optional
from google.cloud import bigquery
import re
from .utils import retry_on_quota_limit
# Import the config module from the current package
from . import config_agent
from google.adk.tools import VertexAiSearchTool
from dotenv import load_dotenv



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


def get_search_results(question: str) -> dict:
    """Queries Vertex AI Search for website data and returns structured results.

    Args:
        question (str): The search query provided by the user.

    Returns:
        dict: A dictionary of search results with titles, snippets, and links.
              Returns an empty dictionary if an error occurs.
    """

    import requests
    import json
    from google.auth import default

    try:
        credentials, project_credentials, auth_req, access_token = get_credentials()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Configuration for basic website search
        data = {
            "query": question,
            "pageSize": 5, # Maximum for basic web search is 25
            "queryExpansionSpec": {"condition": "AUTO"},
            "spellCorrectionSpec": {"mode": "AUTO"},
            "contentSearchSpec": {
                "snippetSpec": {"returnSnippet": True} # Ensures snippets are returned
            }
        }

        response = requests.post(config_agent.DISCOVERY_ENGINE_URL, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        
        processed_results = {}
        
        if 'results' in response_json:
            for i, result in enumerate(response_json['results']):
                # Website data is typically found in 'document' -> 'derivedStructData'
                doc = result.get('document', {})
                # For basic website indexing, metadata is often in derivedStructData
                metadata = doc.get('derivedStructData', {})
                
                processed_results[str(i+1)] = {
                    "title": metadata.get('title', 'No Title Found'),
                    "link": metadata.get('link', doc.get('uri', 'No Link Found')),
                    "snippet": metadata.get('snippets', [{}])[0].get('snippet', 'No Snippet Available'),
                    # If Advanced Indexing is on, you can also grab extractive answers here
                    "id": doc.get('id')
                }
        return processed_results

    except Exception as e:
        print(f"Error: {e}")
        return {}