# example of how to generate a glossary from the docs

import os
import re

docs_path = "./docs"
definitions = {}

# Define terms and their definitions
terms = {
    "Container": "A lightweight, standalone, and executable software package...",
    "Module": "A self-contained unit of functionality...",
    # Add more terms as needed
}

# Scan all .md files for defined terms
for root, dirs, files in os.walk(docs_path):
    for file in files:
        if file.endswith(".md"):
            with open(os.path.join(root, file), "r") as f:
                content = f.read()
                for term in terms:
                    if re.search(rf"\b{term}\b", content):
                        definitions[term] = terms[term]

# Write to definitions.md
with open(os.path.join(docs_path, "definitions.md"), "w") as f:
    f.write("# Definitions\n\n")
    for term, definition in definitions.items():
        f.write(f"- **{term}**: {definition}\n")
