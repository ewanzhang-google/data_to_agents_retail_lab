#!/bin/bash
# -----------------------------------------------------------------------------
# This script creates or updates an OAuth 2.0 authorization configuration in
# Agentspace (Discovery Engine API). It is idempotent.
#
# USAGE:
# 1. Fill in the placeholder values in the "CONFIGURATION" section below.
# 2. Run the script: bash scripts/agentspace_auth.sh
# -----------------------------------------------------------------------------

# --- CONFIGURATION ---
# These values are used if the corresponding environment variables are not already set.
# In Cloud Build, these are provided by the build environment.

PROJECT_ID=${PROJECT_ID:-"data-to-agents"}
AUTH_ID=${AUTH_ID:-"agent-auth"}
AUTH_LOCATION=${AUTH_LOCATION:-"global"}
OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID:-"991395937688-emt4tuqjl0995bffueqmq5ucqmle35f8.apps.googleusercontent.com"}
OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET:-"<your-oauth-client-secret-here>"}
OAUTH_TOKEN_URI=${OAUTH_TOKEN_URI:-"https://oauth2.googleapis.com/token"}
REQUESTED_SCOPES=${REQUESTED_SCOPES:-"openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/bigquery https://www.googleapis.com/auth/cloud-platform"}


# --- END CONFIGURATION ---

echo "🔐 Attempting to create or update OAuth configuration '$AUTH_ID' in location '${AUTH_LOCATION}'..."

# Programmatically URL-encode the scopes, replacing spaces with '+'
ENCODED_SCOPES=$(printf %s "${REQUESTED_SCOPES}" | sed 's/ /+/g')

# The final authorization URI, built using best practices from documentation.
OAUTH_AUTH_URI="https://accounts.google.com/o/oauth2/v2/auth?scope=${ENCODED_SCOPES}&include_granted_scopes=true&response_type=code&access_type=offline&prompt=consent"


# --- API Endpoints ---
# The API endpoint hostname depends on whether the location is global or regional.
if [ "$AUTH_LOCATION" == "global" ]; then
  API_HOSTNAME="discoveryengine.googleapis.com"
else
  API_HOSTNAME="${AUTH_LOCATION}-discoveryengine.googleapis.com"
fi

CREATE_API_ENDPOINT="https://${API_HOSTNAME}/v1alpha/projects/${PROJECT_ID}/locations/${AUTH_LOCATION}/authorizations?authorizationId=${AUTH_ID}"
UPDATE_API_ENDPOINT="https://${API_HOSTNAME}/v1alpha/projects/${PROJECT_ID}/locations/${AUTH_LOCATION}/authorizations/${AUTH_ID}"


# --- JSON Payload ---
# The same payload is used for both creation and update.
JSON_PAYLOAD=$(cat <<EOF
{
  "name": "projects/${PROJECT_ID}/locations/${AUTH_LOCATION}/authorizations/${AUTH_ID}",
  "serverSideOauth2": {
    "clientId": "${OAUTH_CLIENT_ID}",
    "clientSecret": "${OAUTH_CLIENT_SECRET}",
    "authorizationUri": "${OAUTH_AUTH_URI}",
    "tokenUri": "${OAUTH_TOKEN_URI}"
  }
}
EOF
)

# --- Execute Curl Command ---
# We capture the HTTP status code to handle the response programmatically.
# The response body is stored in a temporary file.
RESPONSE_FILE=$(mktemp)
HTTP_STATUS=$(curl --silent --show-error --output "$RESPONSE_FILE" --write-out "%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  --data "${JSON_PAYLOAD}" \
  "${CREATE_API_ENDPOINT}"
)

# --- Handle Response ---
if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "✅ Successfully created new authorization configuration."
  cat "$RESPONSE_FILE"
elif [ "$HTTP_STATUS" -eq 409 ]; then
  echo "⚠️ Authorization already exists. Attempting to update it instead..."
  
  # Send a PATCH request to update the existing resource.
  UPDATE_HTTP_STATUS=$(curl --silent --show-error --output "$RESPONSE_FILE" --write-out "%{http_code}" \
    -X PATCH \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    --data "${JSON_PAYLOAD}" \
    "${UPDATE_API_ENDPOINT}"
  )

  if [ "$UPDATE_HTTP_STATUS" -eq 200 ]; then
    echo "✅ Successfully updated existing authorization configuration."
    # cat "$RESPONSE_FILE"
  else
    echo "❌ Failed to update the existing authorization. Status: ${UPDATE_HTTP_STATUS}"
    cat "$RESPONSE_FILE"
    exit 1
  fi
else
  echo "❌ An unexpected error occurred during creation. Status: ${HTTP_STATUS}"
  cat "$RESPONSE_FILE"
  exit 1
fi

# Clean up the temporary file.
rm -f "$RESPONSE_FILE"
echo -e "\n\nProcess complete."

