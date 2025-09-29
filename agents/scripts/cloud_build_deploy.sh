#!/bin/bash
# 🚀 Deployment script specifically for use within Google Cloud Build.
# It assumes all environment variables (PROJECT_ID, DISPLAY_NAME, etc.)
# are passed in from the build trigger's substitution variables.

set -e # Exit immediately if a command fails.

echo "---"
echo "🔧 Step 1: Setting up Python execution paths..."
# This is a crucial step in Cloud Build. We tell the shell where to find the Python
# packages that were installed with --user in the previous build step.
export PATH=$(python3 -m site --user-base)/bin:$PATH
export PYTHONPATH=$(python3 -m site --user-site)
echo "✅ Paths configured."
echo "---"

echo "🔧 Step 2: Constructing dynamic environment variables..."
# export DATA_PROFILES_TABLE_FULL_ID="${PROJECT_ID}.chocolate_ai.data_insights"
export BUCKET_NAME="${PROJECT_ID}-${DATASET_NAME}-staging"
echo "✅ Dynamic variables are set."
echo "---"

echo "📦 Step 3: Building the Python wheel..."
python3 -m build --wheel --outdir deployment
echo "✅ Wheel built successfully!"
echo "---"

# Determine the generated wheel file name and export it.
AGENT_WHL_FILE=$(find deployment -name "*.whl" | head -n 1)
if [ -z "$AGENT_WHL_FILE" ]; then
    echo "❌ Error: Could not find the built wheel file in the 'deployment' directory."
    exit 1
fi
export AGENT_WHL_FILE

echo "✨ Step 4: All systems go! Running the main Python deployment script..."
export PYTHONPATH="${PYTHONPATH:-}:${PWD}"
python3 deployment/deploy_agentengine.py create register
echo "---"
echo "🎉 Cloud Build deployment process complete!"
echo "---"

