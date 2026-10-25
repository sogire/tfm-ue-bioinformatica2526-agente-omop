import os
from typing import Dict, Any, Optional
from google.cloud import bigquery
import re
# Import the config module from the current package
from . import config_agent
from .utils import retry_on_quota_limit


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

