import json
import re
from enum import Enum


class ContributionRole(Enum):
    """
    ContributionRole Enum generated from the LOC relators file.
    """

def generate_enum_from_json(json_file_file_path: str):
    """
    Reads a JSON file and generates a Python Enum class for roles.

    Args:
        json_file_file_path (str): Path to the relators.json file.

    Returns:
        str: Python code for the generated Enum.
    """
    with open(json_file_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    enum_items = []

    for item in data:
        label = item.get("http://www.loc.gov/mads/rdf/v1#authoritativeLabel", [{}])[0].get("@value")
        uri = item.get("@id", "")

        if not label or not uri:
            continue

        # Convert the label to a valid Python variable name using a regex
        enum_name = re.sub(r"[ ./,\-]", "_", label.upper())

        # Append the enum entry as a string
        enum_items.append(f"    {enum_name} = '{uri}'")

    # Create the enum class as a string
    enum_class_code = "class ContributionRole(Enum):\n" + "\n".join(enum_items)

    # Add a utility method to get enum from URI
    enum_class_code += ("\n\n    @staticmethod\n    def from_uri(uri: str):\n        \"\"\"\n"
                        "        Get the Enum entry from a URI.\n        \"\"\"\n        try:\n"
                        "            return ContributionRole(uri)\n        except ValueError:\n"
                        "            return None")

    return enum_class_code


# Specify the path to the relators.json file
FILE_PATH = "relators.json"

# Save the Enum code to a file or print it
OUTPUT_FILE_NAME = "contribution_role_enum.py"
with open(OUTPUT_FILE_NAME, "w", encoding="utf-8") as f:
    f.write(generate_enum_from_json(FILE_PATH))

print(f"Enum class saved to {OUTPUT_FILE_NAME}")
