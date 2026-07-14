"""Schema Design tab: prompt + editor + lock step."""
from __future__ import annotations

import streamlit as st

from ...config import SUPPORTED_TYPES
from ...generator import SchemaGenerator


def render_schema_tab(api_key: str, model: str) -> None:
    """Render the schema design flow."""
    st.subheader("Describe your dataset")
    st.write("Specify what columns, properties, or overall dataset you want to create.")

    user_prompt = st.text_area(
        "Dataset Generation Prompt",
        value=st.session_state.last_prompt,
        placeholder="E.g., A list of 100 sales leads with company name, industry, "
                    "contact name, and phone number.",
        height=100,
    )
    if user_prompt:
        st.session_state.last_prompt = user_prompt

    if st.button("Generate Schema Blueprint", type="primary", disabled=not api_key):
        if not user_prompt:
            st.warning("Please enter a prompt first.")
        else:
            _run_schema_generation(api_key, model, user_prompt)

    if st.session_state.schema:
        _render_schema_editor()


def _run_schema_generation(api_key: str, model: str, prompt: str) -> None:
    with st.spinner("Extracting schema structure..."):
        try:
            generator = SchemaGenerator(api_key=api_key, model=model)
            st.session_state.schema = generator.suggest(prompt)
            st.success("Schema suggestion created.")
        except Exception as exc:
            st.error(f"Failed to generate schema. Error: {exc}")


def _render_schema_editor() -> None:
    st.markdown("---")
    st.subheader("Modify schema fields")

    schema = st.session_state.schema
    cols_list = schema.get("columns", [])

    for col in cols_list:
        col.setdefault("name", "")
        col.setdefault("type", "String")
        col.setdefault("description", "")
        col.setdefault("examples", [])
        if isinstance(col["examples"], list):
            col["examples"] = ", ".join(map(str, col["examples"]))

    edited = st.data_editor(
        cols_list,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Column Name", required=True),
            "type": st.column_config.SelectboxColumn(
                "Data Type", options=SUPPORTED_TYPES, required=True
            ),
            "description": st.column_config.TextColumn(
                "Generation Instruction", required=True, width="large"
            ),
            "examples": st.column_config.TextColumn("Examples", width="medium"),
        },
    )

    if st.button("Apply and Lock Schema Changes", use_container_width=True):
        updated = []
        for row in edited:
            examples_str = str(row.get("examples", ""))
            examples_list = [x.strip() for x in examples_str.split(",") if x.strip()]
            updated.append({
                "name": row.get("name", ""),
                "type": row.get("type", "String"),
                "description": row.get("description", ""),
                "examples": examples_list,
            })
        st.session_state.schema["columns"] = updated
        st.toast("Schema updated and locked.")