import json
from enum import Enum


class ContributionRole(Enum):
    """
    ContributionRole Enum generated from the LOC relators file.
    """
    pass


def generate_enum_from_json(file_path: str):
    """
    Reads a JSON file and generates a Python Enum class for roles.

    Args:
        file_path (str): Path to the relators.json file.

    Returns:
        str: Python code for the generated Enum.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    enum_items = []

    for item in data:
        label = item.get("http://www.loc.gov/mads/rdf/v1#authoritativeLabel", [{}])[0].get("@value")
        uri = item.get("@id", "")

        if not label or not uri:
            continue

        # Convert the label to a valid Python variable name
        enum_name = label.upper().replace(" ", "_").replace("-", "_").replace("/", "_")

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
file_path = "relators.json"

# Generate the Enum code
enum_code = generate_enum_from_json(file_path)

# Save the Enum code to a file or print it
output_file = "contribution_role_enum.py"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(enum_code)

print(f"Enum class saved to {output_file}")
