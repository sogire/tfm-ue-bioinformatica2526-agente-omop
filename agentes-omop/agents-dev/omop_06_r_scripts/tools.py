import os, json
import requests
from typing import Dict, Any, Optional
from google.cloud import storage
import re
# Import the config module from the current package
from . import config_agent
from .utils import retry_on_quota_limit
from dotenv import load_dotenv

load_dotenv()

def get_credentials():
    """Retrieves default Google Cloud credentials and refreshes the token."""
    import google.auth
    import google.auth.transport.requests
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials, project_credentials = google.auth.default(scopes=scopes)
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    access_token = credentials.token
    return credentials, project_credentials, auth_req, access_token 

@retry_on_quota_limit
def get_search_results(question: str) -> dict:
    """Queries Vertex AI Search with optimized RAG and Extractive Content specs.

    Args:
        question (str): The search query provided by the user.

    Returns:
        dict: A structured dictionary containing the AI summary, citations, 
              and processed document segments (verbatim code).
    """
    try:
        credentials, project_credentials, auth_req, access_token = get_credentials()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Payload optimized for v1 Discovery Engine API
        data = {
            "query": question,
            "pageSize": 5,
            "queryExpansionSpec": {"condition": "AUTO"},
            "spellCorrectionSpec": {"mode": "AUTO"},
            "contentSearchSpec": {
                "snippetSpec": {"returnSnippet": True},
                "extractiveContentSpec": {
                    #"maxExtractiveAnswerCount": 1,
                    "maxExtractiveSegmentCount": 3,
                    "numPreviousSegments": 1,
                    "numNextSegments": 1,
                    "returnExtractiveSegmentScore": True
                },
                "summarySpec": {
                    "summaryResultCount": 5,
                    "includeCitations": True,
                    "ignoreAdversarialQuery": True,
                    "modelSpec": {"version": "stable"}
                }
            }
        }

        response = requests.post(config_agent.DISCOVERY_ENGINE_URL, headers=headers, json=data)
        
        if response.status_code != 200:
            # This will print the specific field error from Google (e.g., validation errors)
            print(f"Discovery Engine API Error: {response.status_code} - {response.text}")
            response.raise_for_status()
            
        response_json = response.json()
        
        output = {
            "answer": response_json.get("summary", {}).get("summaryText", "No summary available."),
            "citations": [],
            "references": {}
        }
        
        summary_obj = response_json.get("summary", {})
        if "summaryWithMetadata" in summary_obj:
            output["citations"] = summary_obj.get("summaryWithMetadata", {}).get("citationMetadata", {}).get("citations", [])

        if 'results' in response_json:
            for i, result in enumerate(response_json['results']):
                doc = result.get('document', {})
                struct_data = doc.get('derivedStructData', {})

                # Extract high-fidelity code from segments
                segments = struct_data.get('extractive_segments', [])
                if segments:
                    content = "\n\n".join([s.get('content', '') for s in segments])
                else:
                    snippets = struct_data.get('snippets', [])
                    content = snippets[0].get('snippet', 'No snippet available') if snippets else 'No content found'

                output["references"][str(i+1)] = {
                    "title": struct_data.get('title', 'Unknown Source'),
                    "link": struct_data.get('link', doc.get('uri', '#')),
                    "content": content,
                    "repository": struct_data.get('repository', 'Unknown'),
                    "id": doc.get('id')
                }
                
        return output

    except Exception as e:
        print(f"Discovery Engine Exception: {e}")
        return {"error": str(e)}