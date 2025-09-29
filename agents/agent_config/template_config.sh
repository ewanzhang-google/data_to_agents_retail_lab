#!/bin/bash
# -----------------------------------------------------------------------------
# A template for configuring the BigQuery Data Agent for a new environment.
# -----------------------------------------------------------------------------

# --- Global Environment Variables ---
export MODEL="gemini-2.5-pro"                                 # The generative model for the agent (e.g., "gemini-2.5-pro").
export PROJECT_ID="<your_project_id>"                         # Your Google Cloud Project ID.
export PROJECT_NUMBER="<your_gcp_project_number>"             # Your Google Cloud Project Number.

# --- BigQuery Environment Variables ---
export BQ_LOCATION="<bigquery_data_location>"                 # The GCP region where your BigQuery data is located (e.g., "asia-southeast1").
export DATASET_NAME="<your_dataset_name>"                     # The BigQuery dataset the agent will analyze.
export TABLE_NAMES=""                                         # Optional: A comma-separated list of tables. Leave empty for all.
export DATA_PROFILES_TABLE_FULL_ID="${PROJECT_ID}.<profiles_dataset.profiles_table>" # Full BQ table ID for data profiles.
export FEW_SHOT_EXAMPLES_TABLE_FULL_ID="${PROJECT_ID}.agent_aux.few_shot_examples" # Full BQ table ID for few-shot examples.

# --- Deployment Environment Variables ---
export AE_LOCATION="us-central1"                              # The GCP region for Agent Engine deployment (must be supported).
export AUTH_LOCATION="global"                                 # The location for the Agentspace Authorization resource ("global" is common).
export BUCKET_NAME="${PROJECT_ID}-${DATASET_NAME}-staging"    # The GCS bucket for staging deployment artifacts.
export DISPLAY_NAME="<Your_Agent_Display_Name>"               # A unique, user-friendly name for the agent in the GCP console.
export AGENT_DESCRIPTION="<A helpful description for your agent>" # A description for the agent.
export AGENTSPACE_ID="<your-network-agentspace-id>"           # The ID of an existing Agentspace application to which the app will be registered
export AUTH_ID="<your-unique-auth-id>"                        # The OAuth Authorization ID registered in Agentspace.
export OAUTH_CLIENT_ID="<your-oauth-client-id>"               # The OAuth Client ID.
export OAUTH_CLIENT_SECRET="<your-oauth-client-secret>"       # The OAuth Client Secret (retrieved from Secret Manager in Cloud Build).


echo "${DISPLAY_NAME} environment configured."

