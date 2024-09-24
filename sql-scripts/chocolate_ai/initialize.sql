/*##################################################################################
# Copyright 2024 Google LLC
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
###################################################################################*/

/*
Author: Adam Paternostro 

Use Cases:
    - Initializes the system (you can re-run this)

Description: 
    - Copies all tables (from analytics hub) and intializes the system with local data

References:
    - 

Clean up / Reset script:

*/


------------------------------------------------------------------------------------------------------------
-- Create GenAI / Vertex AI connections
------------------------------------------------------------------------------------------------------------
CREATE MODEL IF NOT EXISTS `${project_id}.${bigquery_chocoate_ai_dataset}.gemini_pro`
  REMOTE WITH CONNECTION `${project_id}.us.vertex-ai`
  OPTIONS (endpoint = 'gemini-pro');

CREATE MODEL IF NOT EXISTS `${project_id}.${bigquery_chocoate_ai_dataset}.gemini_pro_1_5`
  REMOTE WITH CONNECTION `${project_id}.us.vertex-ai`
  OPTIONS (endpoint = 'gemini-1.5-pro-001');
