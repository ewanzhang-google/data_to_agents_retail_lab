#!/bin/bash

# This script sets up the environment using a specified config file
# and then launches the ADK web server.

# Check if a config file was provided.
if [ -z "$1" ]; then
    echo "Usage: $0 path/to/your_config.sh"
    echo "Example: $0 agent_configs/cem_config.sh"
    exit 1
fi

CONFIG_FILE=$1

# Check if the config file exists.
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at '$CONFIG_FILE'"
    exit 1
fi

echo "Sourcing environment variables from $CONFIG_FILE..."
source "$CONFIG_FILE"

# Launch the ADK web interface.
# The agent will now use the environment variables set by the config file.
echo "Starting ADK web server..."
adk web
