# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import time

from google.adk.tools.tool_context import ToolContext
from google.cloud import bigquery
from google.oauth2.credentials import Credentials

from .constants import AUTH_ID, DISPLAY_NAME, PROJECT_ID

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def execute_bigquery_query(sql_query: str, tool_context: ToolContext) -> str:
    """
    Executes a given SQL query on Google BigQuery and returns the results.

    It checks the ToolContext for an OAuth access token. If present, it uses the
    user's credentials to run the query. Otherwise, it falls back to using the
    agent's default service account credentials.

    Args:
        sql_query: The SQL query string to execute.
        tool_context: The context object provided by the ADK framework.

    Returns:
        A JSON string representing the list of result rows. In case of an
        error, returns a string with the error message.
    """
    logger.info(f"[{DISPLAY_NAME}] --- Starting BigQuery query execution ---")
    start_time = time.time()
    credentials = None
    auth_token_key = f"temp:{AUTH_ID}"

    # Check for OAuth token in the tool context
    if AUTH_ID and auth_token_key in tool_context.state:
        access_token = tool_context.state[auth_token_key]
        credentials = Credentials(token=access_token)
        logger.info(
            f"[{DISPLAY_NAME}] Found OAuth token for '{AUTH_ID}'. Executing query with user credentials."
        )
    else:
        logger.info(
            f"[{DISPLAY_NAME}] No user-provided OAuth token found. Executing query with service account credentials."
        )

    try:
        # Instantiate BQ client with user credentials if available, otherwise default
        client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
        logger.info(f"[{DISPLAY_NAME}] BigQuery client created successfully.")

        logger.info(f"[{DISPLAY_NAME}] Submitting query to BigQuery...")
        query_job = client.query(sql_query)

        results = query_job.result()
        data = [dict(row.items()) for row in results]
        num_rows = len(data)

        end_time = time.time()
        duration = end_time - start_time
        logger.info(
            f"[{DISPLAY_NAME}] --- BigQuery query execution successful ({num_rows} rows, Duration: {duration:.2f} seconds) ---"
        )

        # On success, return the data as a JSON string
        return json.dumps(data, indent=2)

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(
            f"[{DISPLAY_NAME}] --- BigQuery query execution failed after {duration:.2f} seconds ---",
            exc_info=True,  # This automatically adds exception info (like traceback)
        )
        # On failure, return the error message as a string
        return f"An error occurred while executing the BigQuery query: {e}"

