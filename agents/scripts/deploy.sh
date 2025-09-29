#!/bin/bash
# 🚀 Builds, deploys, and registers the Data Agent from your local machine.
# Usage: bash scripts/deploy.sh <config_file> <action> [options]

# --- Pre-flight Checks ---
if [ "$#" -lt 2 ]; then
    echo "🤔 Oops! Looks like you're missing some arguments."
    echo ""
    echo "Usage: $0 <path_to_config_file> <action> [options]"
    echo ""
    echo "Actions:"
    echo "  create [register]    🤖 Create an Agent Engine and optionally register it."
    echo "  register <name>      📝 Register an existing Agent Engine."
    echo "  delete <name>        🗑️  Delete an Agent Engine."
    exit 1
fi

CONFIG_FILE=$1
# Pass all arguments from the second one onwards to the python script
PYTHON_ARGS="${@:2}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Can't find that config file! Looked for: $CONFIG_FILE"
    exit 1
fi

echo "---"
echo "⚙️  Loading configuration from $CONFIG_FILE..."
source "$CONFIG_FILE"
echo "✅ ${DISPLAY_NAME} environment configured."
echo "---"

echo "📦 Building the Python package (the 'wheel')..."
python3 -m build --wheel --outdir deployment
# Find the name of the wheel we just built to pass to the python script
AGENT_WHL_FILE=$(find deployment -name "*.whl" | head -n 1)
export AGENT_WHL_FILE
echo "✅ Build complete! Wheel is ready at ${AGENT_WHL_FILE}"
echo "---"

echo "🚀 Handing off to the Python deployment script with args: ${PYTHON_ARGS}..."
export PYTHONPATH="${PYTHONPATH:-}:${PWD}"
python3 deployment/deploy_agentengine.py $PYTHON_ARGS

echo "---"
echo "🎉 Local deployment process finished!"
echo "---"
