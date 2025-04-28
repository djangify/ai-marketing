#!/usr/bin/env python
"""
Production-safe NLTK setup script.
Use this to ensure NLTK models are downloaded safely into your project directory.
"""

import os
import sys
import nltk

# Where to place the nltk_data folder (inside the project root)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
NLTK_DATA_PATH = os.path.join(PROJECT_ROOT, 'nltk_data')

# Make sure the directory exists
os.makedirs(NLTK_DATA_PATH, exist_ok=True)

# Add it to nltk's search paths
if NLTK_DATA_PATH not in nltk.data.path:
    nltk.data.path.insert(0, NLTK_DATA_PATH)

# List of required resources
REQUIRED_RESOURCES = {
    'punkt': 'tokenizers/punkt',
    'stopwords': 'corpora/stopwords',
    # Add more here if needed, like 'averaged_perceptron_tagger'
}

def ensure_nltk_resource(resource_name, resource_path):
    try:
        nltk.data.find(resource_path)
        print(f"[ok] {resource_name} already available.")
    except LookupError:
        print(f"[!] {resource_name} not found. Downloading to {NLTK_DATA_PATH}...")
        nltk.download(resource_name, download_dir=NLTK_DATA_PATH)
        # Verify download
        try:
            nltk.data.find(resource_path)
            print(f"[ok] Successfully downloaded {resource_name}.")
        except LookupError:
            print(f"[X] Failed to download {resource_name}. Please check your network or disk permissions.")
            sys.exit(1)

if __name__ == "__main__":
    print(f"Verifying NLTK resources in: {NLTK_DATA_PATH}")
    for resource_name, resource_path in REQUIRED_RESOURCES.items():
        ensure_nltk_resource(resource_name, resource_path)
    print("All required NLTK resources are ready.")
