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

from setuptools import setup, find_packages
import os

# Function to parse the requirements.txt file
def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    with open(os.path.join(os.path.dirname(__file__), filename), 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return lines

setup(
    # This is the name of your package
    name="data_agent",

    # This version must match the version in your deployment script
    version="0.1.0",

    # Automatically find the 'data_agent' package directory
    packages=find_packages(),

    # Include non-code files specified here
    package_data={
        # Ensure that the instructions.yaml file is included in the package
        "data_agent": ["instructions.yaml"],
    },

    # Read dependencies from your requirements.txt file
    install_requires=parse_requirements('requirements.txt'),

    # Metadata for your project
    author="Your Name",
    author_email="your.email@example.com",
    description="A BigQuery NL2SQL Agent for data analysis.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.12',
)
