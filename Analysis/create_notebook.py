import json

# Create the complete notebook structure
notebook_content = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {
                "name": "ipython",
                "version": 3
            },
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Read the existing notebook
with open('Result.ipynb', 'r') as f:
    existing = json.load(f)
    
# Keep the existing cells
notebook_content['cells'] = existing.get('cells', [])

# Write back
with open('Result.ipynb', 'w') as f:
    json.dump(notebook_content, f, indent=1)

print("Notebook structure updated successfully")
