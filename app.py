import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from src.generator import CsvGenerator
from src.connector import (
    test_sql_connection,
    export_to_sql,
    test_mongo_connection,
    export_to_mongo
)

# Load environment variables if present
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI CSV Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimalist UI Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Font Overrides */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Minimalist Header Container */
    .header-container {
        padding: 2rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        color: #64748b;
        font-size: 1rem;
        font-weight: 400;
        margin: 0;
    }
    
    /* Clean Metric Cards */
    .metric-card {
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    .metric-val {
        font-size: 1.75rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Preset Buttons / Chips */
    .suggestion-chip {
        display: inline-block;
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.15);
        padding: 0.35rem 0.85rem;
        border-radius: 4px;
        font-size: 0.85rem;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    
    .suggestion-chip:hover {
        background: rgba(99, 102, 241, 0.08);
        border-color: rgba(99, 102, 241, 0.3);
    }
    
    /* Button Customizations */
    .stButton>button {
        border-radius: 6px !important;
        font-weight: 500 !important;
    }
    
    /* Alert styling tweaks */
    .stAlert {
        border-radius: 6px !important;
    }
</style>
""", unsafe_allow_html=True)

# App state management
if "schema" not in st.session_state:
    st.session_state.schema = None
if "df" not in st.session_state:
    st.session_state.df = None
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""

# Header Section
st.markdown("""
<div class="header-container">
    <h1 class="header-title">Generador de Datos Con IA</h1>
    <p class="header-subtitle">Genera Data sintetica Para test con la API de Groq.</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Configuration
st.sidebar.markdown("### Settings")

# Retrieve default API key
default_api_key = os.getenv("GROQ_API_KEY", "")
groq_api_key = st.sidebar.text_input(
    "Groq API Key",
    type="password",
    value=default_api_key,
    # help="Enter your Groq API key. You can also define the GROQ_API_KEY variable in a local .env file."
)

model_options = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b"
]
selected_model = st.sidebar.selectbox(
    "Model Selection",
    options=model_options,
    index=0,
    # help="Llama 3 70B is recommended for structured schema design and row generation."
)

batch_size = st.sidebar.slider(
    "Batch size",
    min_value=5,
    max_value=25,
    value=10,
    step=5,
    help="Number of rows generated per API request. Lower values prevent model truncation."
)
#
# st.sidebar.markdown("---")
# st.sidebar.markdown("""
# ### Best Practices
# - Describe columns and generation rules clearly.
# - Mention specific formats in descriptions (e.g. *'Format as standard email: user@domain.com'*).
# - Use Llama 3 70B for the highest structural accuracy.
# """)

# Setup tabs
tab_schema, tab_generate, tab_database = st.tabs(["1. Schema Design", "2. Data Generation", "3. Export to Database"])

# Check API Key
if not groq_api_key:
    st.info("Please enter your Groq API Key in the sidebar to configure the generation engine.")

# TAB 1: DESIGN SCHEMA
with tab_schema:
    st.subheader("Describe your dataset")
    st.write("Specify what columns, properties, or overall dataset you want to create. The engine will extract a starting schema.")
    
    # Prompt presets / Chips
    st.write("Dataset presets:")
    
    presets = [
        "SaaS user accounts with signup dates, emails, subscription plans, and active status",
        "E-commerce product inventory with categories, SKUs, wholesale price, retail price, and stock levels",
        "Hospital patient admissions listing ages, symptoms, primary doctors, triage level, and stay length",
        "Smart home IoT device logs containing device IDs, temperatures, battery status, and online alerts"
    ]
    
    # Render suggestion chips as clean columns of buttons
    cols_chips = st.columns(len(presets))
    clicked_preset = None
    for i, preset in enumerate(presets):
        with cols_chips[i]:
            short_name = preset.split(" with ")[0].split(" listing ")[0].capitalize()
            if st.button(short_name, key=f"chip_{i}", use_container_width=True):
                clicked_preset = preset

    # Prompt text area
    user_prompt = st.text_area(
        "Dataset Generation Prompt",
        value=clicked_preset if clicked_preset else st.session_state.last_prompt,
        placeholder="E.g., A list of 100 sales leads with company name, industry, contact name, and phone number.",
        height=100
    )
    
    if user_prompt:
        st.session_state.last_prompt = user_prompt

    if st.button("Generate Schema Blueprint", type="primary", disabled=not groq_api_key):
        if not user_prompt:
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Extracting schema structure..."):
                try:
                    generator = CsvGenerator(api_key=groq_api_key)
                    schema_suggestion = generator.suggest_schema(
                        user_prompt=user_prompt,
                        model=selected_model
                    )
                    st.session_state.schema = schema_suggestion
                    st.success("Schema suggestion created.")
                except Exception as e:
                    st.error(f"Failed to generate schema. Please verify your connection. Error: {e}")

    # Display and Edit Schema
    if st.session_state.schema:
        st.markdown("---")
        st.subheader("Modify schema fields")
        st.write("Adjust column names, select data types, or edit generation instructions inside the table below.")
        
        schema = st.session_state.schema
        cols_list = schema.get("columns", [])
        df_cols = pd.DataFrame(cols_list)
        
        # Verify columns exist
        expected_keys = ["name", "type", "description", "examples"]
        for key in expected_keys:
            if key not in df_cols.columns:
                df_cols[key] = ""
                
        # Format examples list to comma separated string for cleaner UI table view
        df_cols["examples"] = df_cols["examples"].apply(
            lambda x: ", ".join(map(str, x)) if isinstance(x, list) else str(x)
        )
        
        # Streamlit Data Editor
        edited_df = st.data_editor(
            df_cols,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Column Name", required=True),
                "type": st.column_config.SelectboxColumn(
                    "Data Type",
                    options=["String", "Integer", "Float", "Date", "Boolean", "Email", "Category"],
                    required=True
                ),
                "description": st.column_config.TextColumn("Generation Instruction", required=True, width="large"),
                "examples": st.column_config.TextColumn("Examples", width="medium")
            }
        )
        
        # Lock schema
        if st.button("Apply and Lock Schema Changes", use_container_width=True):
            updated_columns = []
            for _, row in edited_df.iterrows():
                examples_str = str(row["examples"])
                examples_list = [x.strip() for x in examples_str.split(",") if x.strip()]
                
                updated_columns.append({
                    "name": row["name"],
                    "type": row["type"],
                    "description": row["description"],
                    "examples": examples_list
                })
                
            st.session_state.schema["columns"] = updated_columns
            st.toast("Schema updated and locked. Ready for data generation.")


# TAB 2: GENERATE & EXPORT
with tab_generate:
    if not st.session_state.schema:
        st.info("Please define and lock your schema in the '1. Schema Design' tab first.")
    else:
        schema = st.session_state.schema
        st.subheader(f"Dataset: {schema.get('dataset_name', 'Custom Dataset')}")
        st.write(schema.get("description", ""))
        
        # Show column overview
        st.markdown("##### Columns in Schema")
        cols_summary = st.columns(min(len(schema["columns"]), 6))
        for idx, col in enumerate(schema["columns"]):
            col_block = cols_summary[idx % 6]
            col_block.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{col['type']}</div>
                <div class="metric-val" style="font-size: 1.05rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{col['name']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Generator controls
        col_gen_1, col_gen_2 = st.columns([1, 2])
        with col_gen_1:
            total_rows = st.number_input(
                "Number of rows",
                min_value=5,
                max_value=1000,
                value=50,
                step=10,
                help="Enter total rows to generate."
            )
            
        with col_gen_2:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_generate = st.button("Generate Dataset", type="primary", use_container_width=True, disabled=not groq_api_key)
            
        # Run generation
        if btn_generate:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(current, total):
                percent = int((current / total) * 100)
                percent = min(percent, 100)
                progress_bar.progress(percent)
                status_text.write(f"Synthesised {current} of {total} rows ({percent}%)")

            try:
                generator = CsvGenerator(api_key=groq_api_key)
                df_generated = generator.generate_all(
                    schema=schema,
                    total_rows=total_rows,
                    batch_size=batch_size,
                    model=selected_model,
                    progress_callback=update_progress
                )
                
                st.session_state.df = df_generated
                status_text.write(f"Completed. Synthesized {len(df_generated)} rows.")
                
            except Exception as e:
                st.error(f"Error during data generation: {e}")
                
        # Data View & Export section
        if st.session_state.df is not None:
            df = st.session_state.df
            st.markdown("---")
            
            # Show summary stats
            st.subheader("Dataset Statistics")
            meta_col1, meta_col2, meta_col3 = st.columns(3)
            with meta_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{len(df)}</div>
                    <div class="metric-label">Rows</div>
                </div>
                """, unsafe_allow_html=True)
            with meta_col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{len(df.columns)}</div>
                    <div class="metric-label">Columns</div>
                </div>
                """, unsafe_allow_html=True)
            with meta_col3:
                csv_data = df.to_csv(index=False)
                size_kb = len(csv_data.encode('utf-8')) / 1024
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{size_kb:.2f} KB</div>
                    <div class="metric-label">Size</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Data Preview
            st.subheader("Preview")
            st.dataframe(df, use_container_width=True)
            
            # Export Options
            st.subheader("Download Options")
            exp_col1, exp_col2 = st.columns(2)
            
            with exp_col1:
                csv_bytes = csv_data.encode('utf-8')
                filename_csv = f"{schema.get('dataset_name', 'dataset').lower().replace(' ', '_')}.csv"
                st.download_button(
                    label="Download CSV",
                    data=csv_bytes,
                    file_name=filename_csv,
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )
                
            with exp_col2:
                json_data = df.to_json(orient="records", indent=2)
                json_bytes = json_data.encode('utf-8')
                filename_json = f"{schema.get('dataset_name', 'dataset').lower().replace(' ', '_')}.json"
                st.download_button(
                    label="Download JSON",
                    data=json_bytes,
                    file_name=filename_json,
                    mime="application/json",
                    use_container_width=True
                )
                
            # Quick Visualizations
            st.markdown("---")
            st.subheader("Distribution Analysis")
            st.write("Visual distributions of generated fields.")
            
            # Filter categorical columns and numeric columns
            cat_cols = []
            num_cols = []
            
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    num_cols.append(col)
                else:
                    if df[col].nunique() < min(len(df), 20):
                        cat_cols.append(col)
                        
            if cat_cols or num_cols:
                viz_tab1, viz_tab2 = st.tabs(["Categorical Fields", "Numeric Fields"])
                
                with viz_tab1:
                    if cat_cols:
                        selected_cat = st.selectbox("Select column to display", cat_cols)
                        val_counts = df[selected_cat].value_counts().reset_index()
                        val_counts.columns = [selected_cat, 'Count']
                        st.bar_chart(val_counts.set_index(selected_cat))
                    else:
                        st.info("No categorical fields suitable for charting.")
                        
                with viz_tab2:
                    if num_cols:
                        selected_num = st.selectbox("Select column to plot", num_cols)
                        st.area_chart(df[selected_num])
                    else:
                        st.info("No numeric fields found in dataset.")
            else:
                st.info("No suitable repeating categories or numeric fields found for automatic plotting.")


# TAB 3: EXPORT TO DATABASE
with tab_database:
    if st.session_state.df is None:
        st.info("Please generate your dataset in the '2. Data Generation' tab first.")
    else:
        st.subheader("Database Connector")
        st.write("Export your synthesized dataset directly to a database.")
        
        df = st.session_state.df
        schema = st.session_state.schema
        
        col_db_1, col_db_2 = st.columns([1, 2])
        with col_db_1:
            selected_db = st.selectbox(
                "Database Type",
                options=["PostgreSQL", "MySQL", "SQL Server", "MongoDB", "SQLite"],
                help="Select the database you want to export to."
            )
            
        params = {}
        use_uri = False
        
        # SQLite gets its own simpler parameter input
        if selected_db == "SQLite":
            st.markdown("##### Connection Settings")
            sqlite_path = st.text_input(
                "SQLite Database Path",
                value="local_database.db",
                help="Provide path to the .db file. To use an in-memory database, enter ':memory:'."
            )
            params["sqlite_path"] = sqlite_path
        else:
            col_mode_1, col_mode_2 = st.columns([1, 2])
            with col_mode_1:
                connection_mode = st.radio(
                    "Connection Mode",
                    options=["Parameters", "Connection URI / Connection String"],
                    help="Select 'Parameters' to enter host/port/credentials or 'Connection URI' to paste a single URL connection string."
                )
            
            if connection_mode == "Parameters":
                st.markdown("##### Connection Parameters")
                col_param_1, col_param_2 = st.columns(2)
                
                # Default ports based on DB type
                default_ports = {
                    "PostgreSQL": 5432,
                    "MySQL": 3306,
                    "SQL Server": 1433,
                    "MongoDB": 27017
                }
                default_port = default_ports.get(selected_db, 5432)
                
                with col_param_1:
                    params["host"] = st.text_input("Host", value="localhost")
                    params["username"] = st.text_input("Username", value="")
                    
                with col_param_2:
                    params["port"] = st.number_input("Port", value=default_port, step=1)
                    params["password"] = st.text_input("Password", type="password", value="")
                
                if selected_db == "MongoDB":
                    params["auth_db"] = st.text_input(
                        "Authentication Database",
                        value="admin",
                        help="Database to authenticate against (usually 'admin')"
                    )
                elif selected_db in ["PostgreSQL", "MySQL", "SQL Server"]:
                    params["database"] = st.text_input("Database Name", value="master" if selected_db == "SQL Server" else "")
            
            else:
                use_uri = True
                st.markdown("##### Connection URL / URI")
                
                # Help strings for URI format
                uri_helpers = {
                    "PostgreSQL": "postgresql://username:password@host:port/database",
                    "MySQL": "mysql://username:password@host:port/database",
                    "SQL Server": "mssql://username:password@host:port/database",
                    "MongoDB": "mongodb://username:password@host:port/database_name?authSource=admin"
                }
                
                params["connection_uri"] = st.text_input(
                    "Connection URI",
                    placeholder=uri_helpers.get(selected_db, ""),
                    help=f"Example format: {uri_helpers.get(selected_db, '')}"
                )
                
                if selected_db == "MongoDB":
                    # MongoDB URI doesn't force database target inside the URI for writing
                    params["database"] = st.text_input("Database Name", value="mock_data_db")
        
        st.markdown("---")
        st.markdown("##### Destination Settings")
        
        # Schema name derived table/collection names
        default_name = "synthesized_dataset"
        if schema and schema.get("dataset_name"):
            default_name = schema["dataset_name"].lower().strip().replace(" ", "_")
            
        if selected_db == "MongoDB":
            db_name_to_use = params.get("database", "mock_data_db") if use_uri else st.text_input("Database Name", value="mock_data_db")
            collection_name = st.text_input("Collection Name", value=default_name)
            
            if_exists = st.selectbox(
                "Write Behavior (If Collection Exists)",
                options=["append", "replace", "fail"],
                index=0,
                help="'append': Insert records. 'replace': Clear collection before inserting. 'fail': Stop and raise error if collection has data."
            )
        else:
            table_name = st.text_input("Table Name", value=default_name)
            if_exists = st.selectbox(
                "Write Behavior (If Table Exists)",
                options=["append", "replace", "fail"],
                index=0,
                help="'append': Add rows. 'replace': Drop and recreate table. 'fail': Stop and raise error if table already exists."
            )
            
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn_1, col_btn_2 = st.columns(2)
        
        with col_btn_1:
            btn_test = st.button("Test Connection", use_container_width=True)
        with col_btn_2:
            btn_export = st.button("Export to Database", type="primary", use_container_width=True)
            
        if btn_test:
            with st.spinner("Testing connection..."):
                if selected_db == "MongoDB":
                    success, msg = test_mongo_connection(params, use_uri)
                else:
                    success, msg = test_sql_connection(selected_db, params, use_uri)
                
                if success:
                    st.success(msg)
                else:
                    st.error(f"Connection failed: {msg}")
                    
        if btn_export:
            with st.spinner("Exporting dataset to database..."):
                if selected_db == "MongoDB":
                    success, msg = export_to_mongo(
                        df=df,
                        params=params,
                        db_name=db_name_to_use,
                        collection_name=collection_name,
                        if_exists=if_exists,
                        use_uri=use_uri
                    )
                else:
                    success, msg = export_to_sql(
                        df=df,
                        db_type=selected_db,
                        params=params,
                        table_name=table_name,
                        if_exists=if_exists,
                        use_uri=use_uri
                    )
                
                if success:
                    st.success(msg)
                else:
                    st.error(f"Export failed: {msg}")
