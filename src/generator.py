import json
import logging
import re
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from groq import Groq
from src.templates import (
    SCHEMA_SYSTEM_PROMPT,
    SCHEMA_USER_PROMPT,
    DATA_GENERATION_SYSTEM_PROMPT,
    DATA_GENERATION_USER_PROMPT
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CsvGenerator:
    def __init__(self, api_key: str):
        """Initialize the CSV Generator with a Groq API Key."""
        self.client = Groq(api_key=api_key)

    def _clean_json_response(self, response_text: str) -> str:
        """Extract JSON content from LLM response, stripping markdown blocks if present."""
        text = response_text.strip()
        # Find JSON block if wrapped in markdown code fence
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1).strip()
        return text

    def suggest_schema(self, user_prompt: str, model: str = "llama3-70b-8192") -> Dict[str, Any]:
        """Ask Groq to suggest a dataset schema based on the user's prompt."""
        try:
            logger.info(f"Generating schema for: '{user_prompt}' using model {model}")
            
            chat_completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SCHEMA_SYSTEM_PROMPT},
                    {"role": "user", "content": SCHEMA_USER_PROMPT.format(prompt=user_prompt)}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            
            raw_content = chat_completion.choices[0].message.content
            cleaned_content = self._clean_json_response(raw_content)
            schema = json.loads(cleaned_content)
            
            # Basic validation of schema structure
            if not isinstance(schema, dict) or "columns" not in schema:
                raise ValueError("Response is missing 'columns' key or is not a JSON object")
                
            return schema
            
        except Exception as e:
            logger.error(f"Error suggesting schema: {e}")
            raise e

    def generate_batch(
        self,
        schema: Dict[str, Any],
        row_count: int,
        model: str = "llama3-70b-8192",
        existing_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Generate a single batch of mock data rows matching the schema."""
        try:
            # Prepare context about what has already been generated to prevent exact duplicates
            exclude_context = "None"
            if existing_data and len(existing_data) > 0:
                # Provide a sample of existing values to help LLM diversify
                sample_size = min(15, len(existing_data))
                sample_rows = existing_data[-sample_size:]
                exclude_context = json.dumps(sample_rows, indent=2)

            schema_json = json.dumps(schema.get("columns", []), indent=2)
            schema_desc = schema.get("description", "No description provided")
            
            user_prompt = DATA_GENERATION_USER_PROMPT.format(
                schema_description=schema_desc,
                schema_json=schema_json,
                row_count=row_count,
                exclude_context=exclude_context
            )

            chat_completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": DATA_GENERATION_SYSTEM_PROMPT.format(row_count=row_count)},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7, # slightly higher temperature for diversity in data
            )

            raw_content = chat_completion.choices[0].message.content
            cleaned_content = self._clean_json_response(raw_content)
            response_json = json.loads(cleaned_content)
            
            data_rows = response_json.get("data", [])
            if not isinstance(data_rows, list):
                raise ValueError("Response 'data' key is not a list")
                
            return data_rows
            
        except Exception as e:
            logger.error(f"Error generating data batch: {e}")
            raise e

    def generate_all(
        self,
        schema: Dict[str, Any],
        total_rows: int,
        batch_size: int = 10,
        model: str = "llama3-70b-8192",
        progress_callback=None
    ) -> pd.DataFrame:
        """Generate complete dataset in batches and return a pandas DataFrame."""
        all_rows = []
        remaining = total_rows
        
        while remaining > 0:
            current_batch_size = min(batch_size, remaining)
            logger.info(f"Generating batch of {current_batch_size} rows. Remaining: {remaining}")
            
            try:
                # Try to generate batch
                batch_rows = self.generate_batch(
                    schema=schema,
                    row_count=current_batch_size,
                    model=model,
                    existing_data=all_rows
                )
                
                # Verify we got rows back
                if not batch_rows:
                    logger.warning("Empty batch returned, retrying once...")
                    batch_rows = self.generate_batch(
                        schema=schema,
                        row_count=current_batch_size,
                        model=model,
                        existing_data=all_rows
                    )
                
                all_rows.extend(batch_rows)
                remaining -= len(batch_rows)
                
                # If we're stuck in an infinite loop returning 0 rows
                if len(batch_rows) == 0:
                    logger.error("LLM continuously returned 0 rows. Aborting loop to avoid infinite API charges.")
                    break
                    
                if progress_callback:
                    progress_callback(len(all_rows), total_rows)
                    
            except Exception as e:
                logger.error(f"Batch generation failed: {e}")
                # If we have some data, we can return it. If not, raise.
                if len(all_rows) > 0:
                    logger.warning("Returning partially generated dataset due to error.")
                    break
                else:
                    raise e
                    
        # Clean up keys to match exactly schema column names
        valid_columns = [col["name"] for col in schema.get("columns", [])]
        cleaned_rows = []
        for row in all_rows:
            # Map columns cleanly, fill missing with None
            cleaned_row = {}
            for col in valid_columns:
                cleaned_row[col] = row.get(col, None)
            cleaned_rows.append(cleaned_row)
            
        return pd.DataFrame(cleaned_rows)
