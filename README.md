# CSV AI Generator

A Python and Streamlit web application that generates synthetic datasets using the Groq API. 

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

Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

## Running the App

```bash
streamlit run app.py
```
