# CSV AI Generator

A Python + Streamlit application that generates synthetic datasets using the
Groq API, with one-click export to CSV, SQLite, PostgreSQL, MySQL, and MongoDB.

## Features
- Natural-language → schema blueprint (editable)
- Batched synthetic data generation with progress
- Download as CSV
- Push directly to a database via pluggable drivers

## Requirements
- Python 3.8+
- Groq API Key

## Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the project root (already gitignored):

```env
GROQ_API_KEY=your_groq_api_key_here
```

## Running the App

```bash
streamlit run app.py
```

## Project Layout

```
app.py              # Streamlit entrypoint (thin)
src/
  config.py         # App constants + config dataclasses
  prompts.py        # Groq prompt templates (brace-escaped)
  generator.py      # SchemaGenerator + DataGenerator
  drivers/          # Pluggable database drivers (BaseDatabaseDriver)
    base.py
    registry.py
    sqlite_driver.py
    postgres_driver.py
    mysql_driver.py
    mongodb_driver.py
  ui/               # Modular Streamlit UI
    app_shell.py
    tabs/
      schema_tab.py
      generate_tab.py
    components/
      db_export.py
```

## Extending

### Add a new database target
1. Subclass `BaseDatabaseDriver` in `src/drivers/<name>_driver.py`.
2. Implement `connect`, `create_target`, `insert_rows`, `prepare_existence`.
3. Decorate the class with `@register_driver("YourDB")`.
4. Import it in `src/drivers/__init__.py` so it registers on startup.

The UI picks it up automatically — no UI changes needed.

### Add a new Groq model
Append it to `SUPPORTED_MODELS` in `src/config.py`.