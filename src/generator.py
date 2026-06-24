import json
import logging
from typing import Dict, List, Any, Optional
from groq import Groq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prompt templates inline (ponytail: eliminated templates.py file to minimize files)
SCHEMA_SYSTEM_PROMPT = """
You are an expert data architect and data engineer.
Your task is to design a clean relational/tabular data schema (list of columns) based on the user's natural language request.
For the requested dataset, determine the columns, types (String|Integer|Float|Date|Boolean|Email|Category), and descriptions.
Respond with a JSON object containing:
{
  "dataset_name": "Name of the dataset",
  "description": "Brief description of what this dataset represents",
  "columns": [
    {"name": "col", "type": "String", "description": "generation rule", "examples": ["ex1"]}
  ]
}
"""

SCHEMA_USER_PROMPT = 'Request: "{prompt}"\nSuggest a schema for this dataset.'

DATA_GENERATION_SYSTEM_PROMPT = """
You are a data generation engine. Generate realistic mock data rows matching a schema.
Respond with a JSON object containing a list of records under the "data" key:
{"data": [{"col": "val"}]}
Generate exactly {row_count} rows.
"""

DATA_GENERATION_USER_PROMPT = """
Schema Description: {schema_description}
Schema Columns: {schema_json}
Generate exactly {row_count} rows. Exclude previously generated: {exclude_context}
"""

# ponytail: simplified CsvGenerator class to top-level functions to avoid class boilerplate
def suggest_schema(api_key: str, user_prompt: str, model: str = "llama3-70b-8192") -> Dict[str, Any]:
    """Suggest dataset schema using Groq."""
    logger.info(f"Generating schema for: '{user_prompt}' using model {model}")
    client = Groq(api_key=api_key)
    
    # ponytail: Groq's response_format={"type": "json_object"} ensures clean JSON,
    # so we don't need speculative regex markdown cleaning logic.
    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SCHEMA_SYSTEM_PROMPT},
            {"role": "user", "content": SCHEMA_USER_PROMPT.format(prompt=user_prompt)}
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return json.loads(chat_completion.choices[0].message.content)

def generate_batch(
    api_key: str,
    schema: Dict[str, Any],
    row_count: int,
    model: str = "llama3-70b-8192",
    existing_data: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """Generate a single batch of mock data rows matching the schema."""
    client = Groq(api_key=api_key)
    exclude_context = "None"
    if existing_data:
        # Provide a sample of existing values to help LLM diversify
        exclude_context = json.dumps(existing_data[-15:], indent=2)

    schema_json = json.dumps(schema.get("columns", []), indent=2)
    schema_desc = schema.get("description", "No description provided")
    
    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": DATA_GENERATION_SYSTEM_PROMPT.format(row_count=row_count)},
            {"role": "user", "content": DATA_GENERATION_USER_PROMPT.format(
                schema_description=schema_desc,
                schema_json=schema_json,
                row_count=row_count,
                exclude_context=exclude_context
            )}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    response_json = json.loads(chat_completion.choices[0].message.content)
    return response_json.get("data", [])

def generate_all(
    api_key: str,
    schema: Dict[str, Any],
    total_rows: int,
    batch_size: int = 10,
    model: str = "llama3-70b-8192",
    progress_callback=None
) -> List[Dict[str, Any]]:
    """Generate complete dataset in batches and return list of dictionaries (ponytail: eliminated pandas)."""
    all_rows = []
    remaining = total_rows
    
    while remaining > 0:
        current_batch_size = min(batch_size, remaining)
        logger.info(f"Generating batch of {current_batch_size} rows. Remaining: {remaining}")
        
        try:
            batch_rows = generate_batch(
                api_key=api_key,
                schema=schema,
                row_count=current_batch_size,
                model=model,
                existing_data=all_rows
            )
            
            if not batch_rows:
                logger.warning("Empty batch returned, retrying once...")
                batch_rows = generate_batch(
                    api_key=api_key,
                    schema=schema,
                    row_count=current_batch_size,
                    model=model,
                    existing_data=all_rows
                )
            
            all_rows.extend(batch_rows)
            remaining -= len(batch_rows)
            
            if len(batch_rows) == 0:
                logger.error("LLM continuously returned 0 rows. Aborting loop.")
                break
                
            if progress_callback:
                progress_callback(len(all_rows), total_rows)
                
        except Exception as e:
            logger.error(f"Batch generation failed: {e}")
            if len(all_rows) > 0:
                logger.warning("Returning partially generated dataset due to error.")
                break
            else:
                raise e
                
    # Clean up keys to match exactly schema column names
    valid_columns = [col["name"] for col in schema.get("columns", [])]
    cleaned_rows = []
    for row in all_rows:
        cleaned_row = {}
        for col in valid_columns:
            cleaned_row[col] = row.get(col, None)
        cleaned_rows.append(cleaned_row)
        
    return cleaned_rows
