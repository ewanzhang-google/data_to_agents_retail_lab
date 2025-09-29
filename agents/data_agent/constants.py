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

import os

# Get values from environment variables
MODEL = os.getenv("MODEL", "gemini-2.5-pro")
PROJECT_ID = os.getenv("PROJECT_ID")
PROJECT_NUMBER = os.getenv("PROJECT_NUMBER")
# Location for BigQuery data, sourced from BQ_LOCATION env var
LOCATION = os.getenv("BQ_LOCATION", "us-central1")
DATASET_NAME = os.getenv("DATASET_NAME")
# Optional list of table names, comma-separated in the env var
TABLE_NAMES = (
    os.getenv("TABLE_NAMES", "").split(",") if os.getenv("TABLE_NAMES") else []
)
DATA_PROFILES_TABLE_FULL_ID = os.getenv("DATA_PROFILES_TABLE_FULL_ID")
# A unique name for the agent, used for logging and identification.
DISPLAY_NAME = os.getenv("DISPLAY_NAME", "DATA_AGENT")
AGENT_DESCRIPTION = os.getenv(
    "AGENT_DESCRIPTION",
    "An agent that can answer questions about data in BigQuery.",
)
FEW_SHOT_EXAMPLES_TABLE_FULL_ID = os.getenv("FEW_SHOT_EXAMPLES_TABLE_FULL_ID")
AUTH_ID = os.getenv("AUTH_ID")
