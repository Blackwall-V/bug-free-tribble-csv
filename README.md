# CSV AI Generator 📊

An AI-powered synthetic dataset generator developed with **Python**, **Streamlit**, and **Groq Cloud API**. This tool enables users to design custom database schemas using simple natural language prompts, modify suggested schemas in real-time, and generate realistic datasets in batch increments using ultra-fast LLM inference.

## Features
- **AI Schema Architect**: Input natural language instructions (e.g., *"SaaS customer list with pricing"*), and receive a structured database schema with column types, generation rules, and mock examples.
- **Dynamic Schema Editor**: Customise column names, change data types, edit description rules, or add new columns on-the-fly inside an interactive grid before starting generation.
- **Batch synthesis**: Generates rows in configurable batches to prevent LLM context errors and track exact progress in real-time.
- **Data Preview & Visualization**: Preview dataframes, inspect estimated file sizes, and view instant distribution charts.
- **Export Formats**: Direct download support for `.csv` and `.json`.

## Quick Start

### 1. Prerequisites
Make sure you have Python 3.8+ installed.

### 2. Setup Virtual Environment & Install Dependencies
Run the following commands to set up the environment and install package dependencies:
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root directory and add your Groq API key:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key
```
*(Alternatively, you can paste your Groq API key directly into the sidebar text field inside the web application UI).*

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
The application will open automatically in your browser (typically at `http://localhost:8501`).
