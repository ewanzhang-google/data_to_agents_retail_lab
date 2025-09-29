# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
🚀 Deployment script for Data Agent to Vertex AI Agent Engine and registration
with Agentspace. Handles all the cloud magic!
"""

import argparse
import logging
import os
import requests
import google.auth
import sys

import vertexai
from data_agent.agent import root_agent
from google.api_core import exceptions as google_exceptions
from google.cloud import storage
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_staging_bucket(
    project_id: str, location: str, bucket_name: str, agent_display_name: str
) -> str:
    """Checks if the staging bucket exists, creates it if not."""
    logger.info(
        f"[{agent_display_name}] ☁️  Checking for Cloud Storage bucket: gs://{bucket_name}..."
    )
    storage_client = storage.Client(project=project_id)
    try:
        bucket = storage_client.lookup_bucket(bucket_name)
        if bucket:
            logger.info(
                f"[{agent_display_name}] ✅ Bucket gs://{bucket_name} already exists. Moving on!"
            )
        else:
            logger.info(
                f"[{agent_display_name}] Bucket gs://{bucket_name} not found. Let's create it..."
            )
            new_bucket = storage_client.create_bucket(
                bucket_name, project=project_id, location=location
            )
            logger.info(
                f"[{agent_display_name}] 🎉 Successfully created gs://{new_bucket.name} in {location}."
            )
            new_bucket.iam_configuration.uniform_bucket_level_access_enabled = True
            new_bucket.patch()
            logger.info(
                f"[{agent_display_name}] 🔒 Enabled uniform bucket-level access."
            )

    except google_exceptions.Forbidden as e:
        logger.error(
            (
                f"[{agent_display_name}] ❌ Permission Denied! Could not access bucket gs://{bucket_name}. "
                "Please ensure the service account has the 'Storage Admin' role. Error: %s"
            ),
            e,
        )
        raise
    except google_exceptions.ClientError as e:
        logger.error(
            f"[{agent_display_name}] ❌ Failed to create or access bucket gs://{bucket_name}. Error: %s",
            e,
        )
        raise

    return f"gs://{bucket_name}"


def create_agent_engine(env_vars: dict) -> str | None:
    """Creates and deploys the agent to Vertex AI Agent Engine."""
    agent_display_name = env_vars.get("DISPLAY_NAME", "Data-Agent-Default")
    agent_whl_file = os.getenv("AGENT_WHL_FILE")

    logger.info(f"[{agent_display_name}] 🤖 Starting Agent Engine creation process...")

    if not agent_whl_file or not os.path.exists(agent_whl_file):
        error_msg = f"[{agent_display_name}] ❌ Critical Error: Agent wheel file not found at '{agent_whl_file}'. Did the build step fail?"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.info(f"[{agent_display_name}] Found agent package: {agent_whl_file}")

    adk_app = AdkApp(agent=root_agent, enable_tracing=True)

    try:
        logger.info(
            f"[{agent_display_name}] Deploying to Vertex AI... This may take several minutes."
        )
        remote_agent = agent_engines.create(
            adk_app,
            requirements=[agent_whl_file],
            extra_packages=[agent_whl_file],
            env_vars=env_vars,
            display_name=agent_display_name,
            description=env_vars.get("AGENT_DESCRIPTION"),
        )

        print("\n" + "=" * 80)
        print(f"✅ SUCCESS! Agent Engine '{agent_display_name}' is created!")
        print(f"   Resource Name: {remote_agent.resource_name}")
        print("=" * 80 + "\n")
        return remote_agent.resource_name

    except Exception as e:
        print("\n" + "!" * 80)
        print(f"❌ ERROR! Failed to create Agent Engine '{agent_display_name}'.")
        print(f"   Details: {e}")
        print("!" * 80 + "\n")
        logger.error(
            f"[{agent_display_name}] Failed to create Agent Engine.", exc_info=True
        )
        return None


def register_with_agentspace(reasoning_engine_resource: str, env_vars: dict):
    """Registers an existing Agent Engine with Agentspace."""
    display_name = env_vars.get("DISPLAY_NAME")
    project_id = env_vars.get("PROJECT_ID")
    project_number = env_vars.get("PROJECT_NUMBER")
    agentspace_id = env_vars.get("AGENTSPACE_ID")
    auth_id = env_vars.get("AUTH_ID")
    agent_description = env_vars.get(
        "AGENT_DESCRIPTION",
        f"An AI agent for the {display_name} use case.",
    )

    logger.info(f"[{display_name}] 📝 Registering with Agentspace...")

    if not all([agentspace_id, project_number]):
        logger.error(
            f"[{display_name}] ⚠️  Warning: AGENTSPACE_ID or PROJECT_NUMBER not set. Skipping registration."
        )
        return

    logger.info(f"[{display_name}] Target Agentspace App ID: {agentspace_id}")

    try:
        credentials, _ = google.auth.default()
        credentials.refresh(google.auth.transport.requests.Request())
        token = credentials.token

        api_endpoint = (
            f"https://discoveryengine.googleapis.com/v1alpha/"
            f"projects/{project_id}/locations/global/collections/default_collection/"
            f"engines/{agentspace_id}/assistants/default_assistant/agents"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": project_id,
        }

        payload = {
            "displayName": display_name,
            "description": agent_description,
            "adk_agent_definition": {
                "tool_settings": {
                    "tool_description": agent_description
                },
                "provisionedReasoningEngine": {
                    "reasoningEngine": reasoning_engine_resource
                },
            },
        }

        # If an AUTH_ID is provided, add the authorization block to the payload
        if auth_id:
            payload["authorizations"] = [
                f"projects/{project_number}/locations/global/authorizations/{auth_id}"
            ]
            logger.info(f"[{display_name}] Including authorization setting: {auth_id}")

        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()

        response_json = response.json()
        agent_resource_name = response_json.get("name")
        print("\n" + "=" * 80)
        print(f"✅ SUCCESS! Agent '{display_name}' is registered with Agentspace!")
        print(f"   Agent Resource Name: {agent_resource_name}")
        print("=" * 80 + "\n")

    except requests.exceptions.HTTPError as e:
        print("\n" + "!" * 80)
        print(f"❌ ERROR! Failed to register '{display_name}' with Agentspace.")
        print(f"   Status: {e.response.status_code}, Response: {e.response.text}")
        print("!" * 80 + "\n")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred during Agentspace registration: {e}")
        logger.error(
            f"[{display_name}] An unexpected error occurred during Agentspace registration.",
            exc_info=True,
        )


def delete_agent_engine(resource_name: str, agent_display_name: str) -> None:
    """Deletes the specified agent engine."""
    logger.info(
        f"[{agent_display_name}] 🗑️  Attempting to delete agent engine: {resource_name}"
    )
    try:
        remote_agent = agent_engines.get(resource_name)
        remote_agent.delete(force=True)
        print(f"\n✅ Successfully deleted agent engine: {resource_name}")
    except google_exceptions.NotFound:
        print(f"\n❌ Error: Agent Engine with resource ID {resource_name} not found.")
    except Exception as e:
        print(f"\n❌ An error occurred while deleting agent engine {resource_name}: {e}")
        logger.error(
            f"[{agent_display_name}] An error occurred while deleting agent engine.",
            exc_info=True,
        )


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Deploy and manage the BigQuery Data Agent."
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    create_parser = subparsers.add_parser(
        "create",
        help="Create an Agent Engine and optionally register with Agentspace.",
    )
    create_parser.add_argument(
        "register",
        nargs="?",
        choices=["register"],
        help="Optional: Type 'register' to also register with Agentspace after creation.",
    )

    register_parser = subparsers.add_parser(
        "register", help="Register an existing Agent Engine with Agentspace."
    )
    register_parser.add_argument(
        "resource_name",
        help="The full resource name of the Agent Engine to register.",
    )

    delete_parser = subparsers.add_parser("delete", help="Delete an Agent Engine.")
    delete_parser.add_argument(
        "resource_name", help="The full resource name of the Agent Engine to delete."
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # --- Environment Variable Setup ---
    raw_env_vars = {
        "MODEL": os.getenv("MODEL"),
        "PROJECT_ID": os.getenv("PROJECT_ID"),
        "PROJECT_NUMBER": os.getenv("PROJECT_NUMBER"),
        "BQ_LOCATION": os.getenv("BQ_LOCATION"),
        "AE_LOCATION": os.getenv("AE_LOCATION"),
        "DATASET_NAME": os.getenv("DATASET_NAME"),
        "TABLE_NAMES": os.getenv("TABLE_NAMES"),
        "DATA_PROFILES_TABLE_FULL_ID": os.getenv("DATA_PROFILES_TABLE_FULL_ID"),
        "DISPLAY_NAME": os.getenv("DISPLAY_NAME", "Data-Agent-Default"),
        "BUCKET_NAME": os.getenv("BUCKET_NAME"),
        "AGENTSPACE_ID": os.getenv("AGENTSPACE_ID"),
        "AGENT_DESCRIPTION": os.getenv("AGENT_DESCRIPTION"),
        "FEW_SHOT_EXAMPLES_TABLE_FULL_ID": os.getenv(
            "FEW_SHOT_EXAMPLES_TABLE_FULL_ID"
        ),
        "AUTH_ID": os.getenv("AUTH_ID"),
    }
    env_vars = {k: v for k, v in raw_env_vars.items() if v is not None and v != ""}
    display_name = env_vars.get("DISPLAY_NAME")
    project_id = env_vars.get("PROJECT_ID")
    ae_location = env_vars.get("AE_LOCATION")
    bucket_name = env_vars.get("BUCKET_NAME")

    if not all([project_id, ae_location, bucket_name]):
        print(
            "\n❌ Error: Missing required environment variables (PROJECT_ID, AE_LOCATION, BUCKET_NAME)."
        )
        print("Please check your _config.sh file or Cloud Build substitutions.")
        return

    # --- Vertex AI Initialization ---
    staging_bucket_uri = None
    if args.action == "create":
        staging_bucket_uri = setup_staging_bucket(
            project_id, ae_location, bucket_name, display_name
        )

    vertexai.init(
        project=project_id,
        location=ae_location,
        staging_bucket=staging_bucket_uri,
    )

    # --- Action Dispatch ---
    try:
        if args.action == "create":
            resource_name = create_agent_engine(env_vars)
            if args.register and resource_name:
                register_with_agentspace(resource_name, env_vars)
        elif args.action == "register":
            register_with_agentspace(args.resource_name, env_vars)
        elif args.action == "delete":
            delete_agent_engine(args.resource_name, display_name)
    except Exception as e:
        print(f"An unexpected fatal error occurred: {e}")
        logger.error(f"[{display_name}] Unhandled exception in main:", exc_info=True)


if __name__ == "__main__":
    main()
