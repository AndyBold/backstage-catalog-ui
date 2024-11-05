#!/usr/bin/env python3

REQUIRED_FIELDS = {
    "apiVersion": str,
    "kind": str,
    "metadata": {"name": str, "namespace": str, "description": str, "owner": str},
    "spec": {"type": str, "lifecycle": str, "system": str},
}

CATALOG_FIELDS = {
    "apiVersion": {
        "type": "text",
        "label": "API Version",
        "required": True,
        "default": "backstage.io/v1alpha1",
    },
    "kind": {
        "type": "select",
        "label": "Kind",
        "required": True,
        "options": [
            "Component",
            "Template",
            "API",
            "Resource",
            "System",
            "Domain",
            "Location",
        ],
    },
    "metadata": {
        "name": {
            "type": "text",
            "label": "Name",
            "required": True,
            "help": "Unique name of the entity",
        },
        "namespace": {
            "type": "text",
            "label": "Namespace",
            "required": True,
            "help": "Namespace the entity belongs to",
        },
        "title": {
            "type": "text",
            "label": "Title",
            "required": False,
            "help": "Display title of the entity",
        },
        "description": {
            "type": "textarea",
            "label": "Description",
            "required": True,
            "help": "A description of the entity",
        },
        "labels": {
            "type": "key-value",
            "label": "Labels",
            "required": False,
            "help": "Key-value pairs for organizing entities",
        },
        "tags": {
            "type": "array",
            "label": "Tags",
            "required": False,
            "help": "Tags for the entity",
        },
        "owner": {
            "type": "text",
            "label": "Owner",
            "required": True,
            "help": "Owner of the entity (e.g., team-name)",
        },
    },
    "spec": {
        "type": {
            "type": "text",
            "label": "Type",
            "required": True,
            "help": "Type of the entity",
        },
        "lifecycle": {
            "type": "select",
            "label": "Lifecycle",
            "required": True,
            "options": ["experimental", "production", "deprecated"],
        },
        "system": {
            "type": "text",
            "label": "System",
            "required": True,
            "help": "System the entity belongs to",
        },
    },
}


def validate_entity(data):
    errors = []

    # Check required fields
    if not isinstance(data, dict):
        return ["Invalid YAML format"]

    for field, field_type in REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
            continue

        if field == "metadata" or field == "spec":
            for subfield, subfield_type in REQUIRED_FIELDS[field].items():
                if subfield not in data[field]:
                    errors.append(f"Missing required field: {field}.{subfield}")

    return errors
