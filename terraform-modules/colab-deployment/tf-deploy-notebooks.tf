####################################################################################
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
####################################################################################

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google-beta"
      version = "5.35.0"
    }
  }
}


####################################################################################
# Variables
####################################################################################
variable "project_id" {}
variable "vertex_ai_region" {}
variable "bigquery_chocoate_ai_dataset" {}
variable "chocoate_ai_bucket" {}
variable "data_beans_code_bucket" {}
variable "dataform_region" {}
variable "cloud_function_region" {}
variable "workflow_region" {}
variable "random_extension" {}
variable "gcp_account_name" {}

data "google_client_config" "current" {
}


# Define the list of notebook files to be created
locals {
  db_gma_notebooks = [ 
    for s in fileset("../colab-enterprise/", "*.ipynb") : trimsuffix(s, ".ipynb")
  ]  

  notebook_names = local.db_gma_notebooks # concat(local.TTTT, local.db_gma_notebooks)
}

# Setup Dataform repositories to host notebooks
# Create the Dataform repos.  This will create all the repos across all directories
resource "google_dataform_repository" "notebook_repo" {
  count        = length(local.notebook_names)
  provider     = google-beta
  project      = var.project_id
  region       = var.dataform_region
  name         = local.notebook_names[count.index]
  display_name = local.notebook_names[count.index]
  labels = {
    "single-file-asset-type" = "notebook"
  }
}


# Template Substitution - You need one of these blocks per Notebook Directory
resource "local_file" "local_file_db_gma_notebooks" {
  count    = length(local.db_gma_notebooks)
  filename = "../terraform-modules/colab-deployment/notebooks/${local.db_gma_notebooks[count.index]}.ipynb" 
  content = templatefile("../colab-enterprise/${local.db_gma_notebooks[count.index]}.ipynb",
   {
    project_id = var.project_id
    vertex_ai_region = var.vertex_ai_region
    bigquery_chocoate_ai_dataset = var.bigquery_chocoate_ai_dataset
    chocoate_ai_bucket = var.chocoate_ai_bucket
    data_beans_code_bucket = var.data_beans_code_bucket
    }
  )
}


# Deploy notebooks -  You need one of these blocks per Notebook Directory
# https://cloud.google.com/dataform/reference/rest/v1beta1/projects.locations.repositories/commit#WriteFile
#json='{
#  "commitMetadata": {
#    "author": {
#      "name": "Google Data Bean",
#      "emailAddress": "no-reply@google.com"
#    },
#    "commitMessage": "Committing Chocolate A.I. notebook"
#  },
#  "fileOperations": {
#      "content.ipynb": {
#         "writeFile": {
#           "contents" : "eyJjZWxscyI6W3siY2VsbF90eXBlIjoiY29kZSIsImV4ZWN1dGlvbl9jb3VudCI6bnVsbCwibWV0YWRhdGEiOnt9LCJvdXRwdXRzIjpbXSwic291cmNlIjpbXX1dLCJtZXRhZGF0YSI6eyJjb2xhYiI6eyJjZWxsX2V4ZWN1dGlvbl9zdHJhdGVneSI6InNldHVwIiwibmFtZSI6IkJpZ1F1ZXJ5IHRhYmxlIiwicHJvdmVuYW5jZSI6W119LCJrZXJuZWxzcGVjIjp7ImRpc3BsYXlfbmFtZSI6IlB5dGhvbiAzIiwibmFtZSI6InB5dGhvbjMifSwibGFuZ3VhZ2VfaW5mbyI6eyJuYW1lIjoicHl0aG9uIn19LCJuYmZvcm1hdCI6NCwibmJmb3JtYXRfbWlub3IiOjB9Cg=="
#       }
#    }
#  }
#}'
resource "null_resource" "commit_db_gma_notebooks" {
  count        = length(local.db_gma_notebooks)
  provisioner "local-exec" {
    
    when    = create
    command = <<EOF
curl -X POST \
  https://dataform.googleapis.com/v1beta1/projects/${var.project_id}/locations/${var.workflow_region}/repositories/${replace(local.db_gma_notebooks[count.index], ".ipynb", "")}:commit \
  --header "Authorization: Bearer ${data.google_client_config.current.access_token}" \
  --header "Content-Type: application/json" \
  --data "{\"commitMetadata\": {\"author\": {\"name\": \"Google Data Bean\",\"emailAddress\": \"no-reply@google.com\"},\"commitMessage\": \"Committing Chocolate A.I. notebook\"},\"fileOperations\": {\"content.ipynb\": {\"writeFile\": {\"contents\" : \"${base64encode(local_file.local_file_db_gma_notebooks[count.index].content)}\"}}}}"
EOF
  }
  depends_on = [
    google_dataform_repository.notebook_repo
  ]
}