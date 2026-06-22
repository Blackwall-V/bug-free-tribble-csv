import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from src.generator import CsvGenerator

# Load environment variables if present
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI CSV Dataset Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium UI Styling using Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    /* Main Font Overrides */
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Custom Header Styles */
    .hero-container {
        padding: 2.5rem 1.5rem;
        background: linear-gradient(135deg, rgba(26, 21, 44, 0.9) 0%, rgba(13, 11, 23, 0.95) 100%);
        border-radius: 20px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }
    
    .hero-title {
        background: linear-gradient(90deg, #a78bfa 0%, #ec4899 50%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.25rem;
        font-weight: 400;
        max-width: 700px;
        margin: 0 auto;
        line-height: 1.6;
    }
    
    /* Elegant Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(139, 92, 246, 0.4);
        background: rgba(139, 92, 246, 0.05);
    }
    
    .metric-val {
        font-size: 2rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Interactive Pills */
    .suggestion-chip {
        display: inline-block;
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.3);
        color: #c084fc;
        padding: 0.4rem 1rem;
        border-radius: 50px;
        font-size: 0.9rem;
        margin: 0.3rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .suggestion-chip:hover {
        background: rgba(139, 92, 246, 0.25);
        color: #e9d5ff;
        border-color: rgba(139, 92, 246, 0.6);
        transform: scale(1.03);
    }
    
    /* Sidebar styling tweaks */
    .css-163gfae {
        background-color: #0f172a;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    /* Status Messages */
    .success-banner {
        padding: 1rem;
        background-color: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34d399;
        border-radius: 8px;
        margin-bottom: 1.5rem;
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

# Hero Section
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">CSV AI Generator</h1>
    <p class="hero-subtitle">Design custom schemas and generate synthetic, realistic datasets on-demand powered by Groq's ultra-fast LLM APIs.</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Settings & Keys
st.sidebar.markdown("### ⚙️ Engine Settings")

# Retrieve default API key
default_api_key = os.getenv("GROQ_API_KEY", "")
groq_api_key = st.sidebar.text_input(
    "Groq API Key",
    type="password",
    value=default_api_key,
    help="Enter your Groq API key. You can also define the GROQ_API_KEY environment variable in a .env file."
)

model_options = [
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]
selected_model = st.sidebar.selectbox(
    "AI Model",
    options=model_options,
    index=0,
    help="Llama 3 70B is highly recommended for creating complex schemas and logical rows. 8B models are faster but less precise."
)

batch_size = st.sidebar.slider(
    "Generation Batch Size",
    min_value=5,
    max_value=25,
    value=10,
    step=5,
    help="Number of rows generated per API request. Smaller batches improve model consistency and prevent token truncation."
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 💡 Best Practices
1. Define clear columns and value descriptions.
2. For high-quality text fields, provide explicit formatting rules (e.g. *'Format as standard email: user@domain.com'*).
3. Use **Llama 3 70B** for schema extraction and final generation for highest consistency.
""")

# Setup tabs
tab_schema, tab_generate = st.tabs(["📋 1. Design Schema", "⚡ 2. Generate Dataset"])

# Check API Key
if not groq_api_key:
    st.info("⚠️ Please enter your Groq API Key in the sidebar to get started.")

# TAB 1: DESIGN SCHEMA
with tab_schema:
    st.subheader("Define What Dataset You Need")
    st.write("Write a description of the dataset or schema you want. The AI will analyze your query and suggest a structured schema.")
    
    # Prompt presets / Chips
    st.markdown("**Or choose a quick template starter:**")
    
    presets = [
        "SaaS user accounts with signup dates, emails, subscription plans, and active status",
        "E-commerce product inventory with categories, SKUs, wholesale price, retail price, and stock levels",
        "Hospital patient admissions listing ages, symptoms, primary doctors, triage level, and stay length",
        "Smart home IoT device logs containing device IDs, temperatures, battery status, and online alerts"
    ]
    
    # Render suggestion chips
    cols_chips = st.columns(len(presets))
    clicked_preset = None
    for i, preset in enumerate(presets):
        with cols_chips[i]:
            short_name = preset.split(" with ")[0].split(" listing ")[0].capitalize()
            if st.button(short_name, key=f"chip_{i}", use_container_width=True):
                clicked_preset = preset

    # Prompt text area
    user_prompt = st.text_area(
        "Dataset Request Prompt",
        value=clicked_preset if clicked_preset else st.session_state.last_prompt,
        placeholder="E.g., A list of 100 sales leads with company name, website, industry, contact name, email, and phone number.",
        height=100
    )
    
    if user_prompt:
        st.session_state.last_prompt = user_prompt

    if st.button("✨ Suggest Schema & Columns", type="primary", disabled=not groq_api_key):
        if not user_prompt:
            st.warning("Please type a request prompt first.")
        else:
            with st.spinner("Analyzing request and drafting schema structure..."):
                try:
                    generator = CsvGenerator(api_key=groq_api_key)
                    schema_suggestion = generator.suggest_schema(
                        user_prompt=user_prompt,
                        model=selected_model
                    )
                    st.session_state.schema = schema_suggestion
                    st.success("Successfully generated dataset schema!")
                except Exception as e:
                    st.error(f"Failed to generate schema. Please verify your Groq API key and connection. Error: {e}")

    # Display and Edit Schema
    if st.session_state.schema:
        st.markdown("---")
        st.subheader("🔧 Customize suggested schema")
        st.write("Edit the table below to rename columns, change data types, or refine instructions before generating rows.")
        
        schema = st.session_state.schema
        
        # Load schema into a DataFrame for easy editing in st.data_editor
        cols_list = schema.get("columns", [])
        df_cols = pd.DataFrame(cols_list)
        
        # Make sure columns have expected keys
        expected_keys = ["name", "type", "description", "examples"]
        for key in expected_keys:
            if key not in df_cols.columns:
                df_cols[key] = ""
                
        # Cast examples to string for display in editor
        df_cols["examples"] = df_cols["examples"].apply(
            lambda x: ", ".join(map(str, x)) if isinstance(x, list) else str(x)
        )
        
        # Streamlit Data Editor for direct manipulation
        edited_df = st.data_editor(
            df_cols,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Column Name", required=True, help="Database-safe column name"),
                "type": st.column_config.SelectboxColumn(
                    "Data Type",
                    options=["String", "Integer", "Float", "Date", "Boolean", "Email", "Category"],
                    required=True
                ),
                "description": st.column_config.TextColumn("Generation Rules", required=True, width="large"),
                "examples": st.column_config.TextColumn("Example Values", width="medium")
            }
        )
        
        # Save edits back to session state schema
        if st.button("💾 Lock In Schema", use_container_width=True):
            updated_columns = []
            for _, row in edited_df.iterrows():
                # Split examples string back to list
                examples_str = str(row["examples"])
                examples_list = [x.strip() for x in examples_str.split(",") if x.strip()]
                
                updated_columns.append({
                    "name": row["name"],
                    "type": row["type"],
                    "description": row["description"],
                    "examples": examples_list
                })
                
            st.session_state.schema["columns"] = updated_columns
            st.toast("Schema locked in! Head over to the 'Generate Dataset' tab.", icon="🔓")


# TAB 2: GENERATE & EXPORT
with tab_generate:
    if not st.session_state.schema:
        st.info("👈 Please define and lock in a schema in the '1. Design Schema' tab first.")
    else:
        schema = st.session_state.schema
        st.subheader(f"Generate Rows for: {schema.get('dataset_name', 'Custom Dataset')}")
        st.caption(schema.get("description", ""))
        
        # Display Schema summary cards
        st.write("**Columns in Schema:**")
        cols_summary = st.columns(min(len(schema["columns"]), 6))
        for idx, col in enumerate(schema["columns"]):
            col_block = cols_summary[idx % 6]
            col_block.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{col['type']}</div>
                <div class="metric-val" style="font-size: 1.15rem; color: #a78bfa; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{col['name']}</div>
                <div style="font-size: 0.75rem; color: #64748b; height: 32px; overflow: hidden; text-overflow: ellipsis;" title="{col['description']}">{col['description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Generation inputs
        col_gen_1, col_gen_2 = st.columns([1, 2])
        with col_gen_1:
            total_rows = st.number_input(
                "Total Rows to Generate",
                min_value=5,
                max_value=1000,
                value=50,
                step=10,
                help="Maximum rows to generate. Generates in chunks using your batch size configuration."
            )
            
        with col_gen_2:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_generate = st.button("🚀 Begin Dataset Generation", type="primary", use_container_width=True, disabled=not groq_api_key)
            
        # Generation logic
        if btn_generate:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(current, total):
                percent = int((current / total) * 100)
                percent = min(percent, 100)
                progress_bar.progress(percent)
                status_text.markdown(f"**Progress:** Generative Engine has synthesised `{current}` of `{total}` rows... ({percent}%)")

            try:
                generator = CsvGenerator(api_key=groq_api_key)
                
                # Perform Generation
                df_generated = generator.generate_all(
                    schema=schema,
                    total_rows=total_rows,
                    batch_size=batch_size,
                    model=selected_model,
                    progress_callback=update_progress
                )
                
                st.session_state.df = df_generated
                status_text.markdown(f"✨ **Generation Complete!** Synthesized `{len(df_generated)}` rows successfully.")
                st.balloons()
                
            except Exception as e:
                st.error(f"Error during dataset generation: {e}")
                
        # Data View & Export section
        if st.session_state.df is not None:
            df = st.session_state.df
            st.markdown("---")
            
            # Show summary stats
            st.markdown("### 📊 Dataset Overview")
            meta_col1, meta_col2, meta_col3 = st.columns(3)
            with meta_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{len(df)}</div>
                    <div class="metric-label">Generated Rows</div>
                </div>
                """, unsafe_allow_html=True)
            with meta_col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{len(df.columns)}</div>
                    <div class="metric-label">Dataset Columns</div>
                </div>
                """, unsafe_allow_html=True)
            with meta_col3:
                # Estimate CSV file size
                csv_data = df.to_csv(index=False)
                size_kb = len(csv_data.encode('utf-8')) / 1024
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{size_kb:.2f} KB</div>
                    <div class="metric-label">Estimated File Size</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Interactive Grid Preview
            st.markdown("### 🔍 Dataset Preview")
            st.dataframe(df, use_container_width=True)
            
            # Export Options
            st.markdown("### 📥 Download & Export")
            exp_col1, exp_col2 = st.columns(2)
            
            with exp_col1:
                # CSV Download Button
                csv_bytes = csv_data.encode('utf-8')
                filename_csv = f"{schema.get('dataset_name', 'dataset').lower().replace(' ', '_')}.csv"
                st.download_button(
                    label="📥 Download CSV Dataset",
                    data=csv_bytes,
                    file_name=filename_csv,
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )
                
            with exp_col2:
                # JSON Download Button
                json_data = df.to_json(orient="records", indent=2)
                json_bytes = json_data.encode('utf-8')
                filename_json = f"{schema.get('dataset_name', 'dataset').lower().replace(' ', '_')}.json"
                st.download_button(
                    label="📥 Download JSON Dataset",
                    data=json_bytes,
                    file_name=filename_json,
                    mime="application/json",
                    use_container_width=True
                )
                
            # Quick Visualizations
            st.markdown("---")
            st.markdown("### 📈 Visual Explorer")
            st.write("Here are quick distributions of the columns generated in your dataset.")
            
            # Filter categorical columns and numeric columns
            cat_cols = []
            num_cols = []
            
            # Attempt to automatically type columns based on pandas
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    num_cols.append(col)
                else:
                    # Categorical if low unique count
                    if df[col].nunique() < min(len(df), 20):
                        cat_cols.append(col)
                        
            # Plot charts
            if cat_cols or num_cols:
                viz_tab1, viz_tab2 = st.tabs(["📊 Category Distributions", "📈 Numeric Trends"])
                
                with viz_tab1:
                    if cat_cols:
                        selected_cat = st.selectbox("Select Column to Chart", cat_cols)
                        val_counts = df[selected_cat].value_counts().reset_index()
                        val_counts.columns = [selected_cat, 'Count']
                        st.bar_chart(val_counts.set_index(selected_cat))
                    else:
                        st.info("No clear categorical fields suitable for charting.")
                        
                with viz_tab2:
                    if num_cols:
                        selected_num = st.selectbox("Select Numeric Field to Chart", num_cols)
                        st.area_chart(df[selected_num])
                    else:
                        st.info("No numerical fields found in dataset for numerical plots.")
            else:
                st.info("Generate some data fields with repeating categories or numerical values to see visualizations.")
