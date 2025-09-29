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

import datetime
import json
import logging
import os

import yaml

from .constants import DATASET_NAME, DISPLAY_NAME, PROJECT_ID, TABLE_NAMES
from .utils import (
    fetch_bigquery_data_profiles,
    fetch_dataset_description,
    fetch_few_shot_examples,
    fetch_sample_data_for_tables,
    fetch_table_entry_metadata,
)

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def json_serial_default(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def return_instructions_bigquery() -> str:
    """
    Fetches table metadata, data profiles (and conditionally sample data),
    formats them, and injects them into the main instruction template.
    """
    dataset_description = fetch_dataset_description()
    dataset_description_string_for_prompt = (
        dataset_description
        if dataset_description
        else "Dataset description is not available."
    )

    table_metadata_raw = fetch_table_entry_metadata()
    if not table_metadata_raw:
        table_metadata_string_for_prompt = "Table metadata information is not available."
    else:
        formatted_metadata = []
        for metadata in table_metadata_raw:
            try:
                metadata_str = json.dumps(
                    metadata, indent=2, ensure_ascii=False, default=json_serial_default
                )
                formatted_metadata.append(
                    f"**Table Entry Metadata:**\n```json\n{metadata_str}\n```"
                )
            except TypeError as e:
                logger.warning(
                    f"[{DISPLAY_NAME}] Could not serialize table metadata: {e}"
                )
                formatted_metadata.append(
                    "Table metadata contains non-serializable data."
                )
        table_metadata_string_for_prompt = "\n\n---\n\n".join(formatted_metadata)

    data_profiles_raw = fetch_bigquery_data_profiles()
    if data_profiles_raw:
        formatted_profiles = []
        for profile in data_profiles_raw:
            try:
                profile_str = json.dumps(
                    profile, indent=2, ensure_ascii=False, default=json_serial_default
                )
            except TypeError as e:
                logger.warning(
                    f"[{DISPLAY_NAME}] Could not serialize profile part: {e}. Profile: {profile}"
                )
                profile_str = f"Profile for column '{profile.get('column_name')}' in table '{profile.get('source_table_id')}' contains non-serializable data."
            column_key = profile.get("column_name")
            table_key = profile.get("source_table_id")
            formatted_profiles.append(
                f"Data profile for column '{column_key}' in table '{table_key}':\n{profile_str}"
            )
        data_profiles_string_for_prompt = "\n\n---\n\n".join(formatted_profiles)
        samples_string_for_prompt = "Full data profiles are provided; sample data section is omitted for brevity."
    else:
        logger.info(
            f"[{DISPLAY_NAME}] Data profiles not found. Attempting to fetch sample data..."
        )
        data_profiles_string_for_prompt = "Data profile information is not available. Please refer to the sample data below."
        sample_data_raw = fetch_sample_data_for_tables(num_rows=3)
        if sample_data_raw:
            formatted_samples = []
            for item in sample_data_raw:
                try:
                    sample_rows_str = json.dumps(
                        item["sample_rows"],
                        indent=2,
                        ensure_ascii=False,
                        default=json_serial_default,
                    )
                except TypeError as e:
                    logger.warning(
                        f"[{DISPLAY_NAME}] Could not serialize sample_rows for table {item.get('table_name')}: {e}."
                    )
                    sample_rows_str = f"Sample rows for table {item.get('table_name')} contain non-serializable data."
                formatted_samples.append(
                    f"**Sample Data for table `{item['table_name']}` (first {len(item.get('sample_rows',[]))} rows):**\n```json\n{sample_rows_str}\n```"
                )
            samples_string_for_prompt = "\n\n---\n\n".join(formatted_samples)
        else:
            logger.warning(
                f"[{DISPLAY_NAME}] Could not fetch sample data for the target scope: {PROJECT_ID}.{DATASET_NAME} (Tables: {TABLE_NAMES if TABLE_NAMES else 'All'})."
            )
            samples_string_for_prompt = f"Could not fetch sample data for the target scope: {PROJECT_ID}.{DATASET_NAME} (Tables: {TABLE_NAMES if TABLE_NAMES else 'All'})."

    few_shot_examples_raw = fetch_few_shot_examples()
    if few_shot_examples_raw:
        # The examples are already formatted as strings, so we just join them.
        few_shot_examples_string_for_prompt = "\n\n---\n\n".join(few_shot_examples_raw)
    else:
        few_shot_examples_string_for_prompt = "Few-shot examples are not available for this dataset."

    script_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_file_path = os.path.join(script_dir, "instructions.yaml")
    try:
        with open(yaml_file_path, "r") as f:
            instructions_yaml = yaml.safe_load(f)
            instruction_template_from_yaml = "\n".join(
                [
                    instructions_yaml.get("overall_workflow", ""),
                    instructions_yaml.get("bigquery_data_schema_and_context", ""),
                    instructions_yaml.get("table_schema_and_join_information", ""),
                    instructions_yaml.get("critical_joining_logic_and_context", ""),
                    instructions_yaml.get("data_profile_information", ""),
                    instructions_yaml.get("sample_data", ""),
                    instructions_yaml.get("few_shot_examples", ""),
                ]
            )
            if not instruction_template_from_yaml.strip():
                logger.error(
                    f"[{DISPLAY_NAME}] Instruction template loaded from YAML is empty."
                )
                raise ValueError("Instruction template loaded from YAML is empty.")
    except FileNotFoundError:
        logger.error(f"[{DISPLAY_NAME}] instructions.yaml not found.")
        raise
    except yaml.YAMLError as e:
        logger.error(f"[{DISPLAY_NAME}] Error loading instructions.yaml: {e}")
        raise

    final_instruction = instruction_template_from_yaml.format(
        dataset_description=dataset_description_string_for_prompt,
        table_metadata=table_metadata_string_for_prompt,
        data_profiles=data_profiles_string_for_prompt,
        samples=samples_string_for_prompt,
        few_shot_examples=few_shot_examples_string_for_prompt,
    )
    return final_instruction
