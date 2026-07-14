"""Prompt templates for schema suggestion and data generation.

All templates use str.format placeholders. Literal JSON braces in the
examples are escaped as {{ }} so .format() never raises KeyError on
keys like "data" or "columns".
"""
from __future__ import annotations

SCHEMA_SYSTEM_PROMPT = (
    "You are an expert data architect and data engineer.\n"
    "Your task is to design a clean relational/tabular data schema (list of columns) "
    "based on the user's natural language request.\n"
    "For the requested dataset, determine the columns, types "
    "(String|Integer|Float|Date|Boolean|Email|Category), and descriptions.\n"
    "Respond with a JSON object containing:\n"
    "{{\n"
    "  \"dataset_name\": \"Name of the dataset\",\n"
    "  \"description\": \"Brief description of what this dataset represents\",\n"
    "  \"columns\": [\n"
    "    {{\"name\": \"col\", \"type\": \"String\", \"description\": \"generation rule\", \"examples\": [\"ex1\"]}}\n"
    "  ]\n"
    "}}"
)

SCHEMA_USER_PROMPT = 'Request: "{prompt}"\nSuggest a schema for this dataset.'


DATA_GENERATION_SYSTEM_PROMPT = (
    "You are a data generation engine. Generate realistic mock data rows matching a schema.\n"
    "Respond with a JSON object containing a list of records under the \"data\" key "
    "structured as: {{\"data\": [{{\"col\": \"val\"}}]}}.\n"
    "Generate exactly {row_count} rows."
)

DATA_GENERATION_USER_PROMPT = (
    "Schema Description: {schema_description}\n"
    "Schema Columns: {schema_json}\n"
    "Generate exactly {row_count} rows. Exclude previously generated: {exclude_context}"
)
