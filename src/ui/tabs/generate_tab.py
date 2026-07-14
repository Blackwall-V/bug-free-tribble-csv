"""Data Generation tab: generate rows, preview, CSV download, DB export."""
from __future__ import annotations

import csv
import io

import streamlit as st

from ...config import IF_EXISTS_OPTIONS
from ...generator import DataGenerator
from ..components.db_export import render_db_export
from ..styles import section_header, stat_caption, vertical_space


def render_generate_tab(api_key: str, model: str, batch_size: int) -> None:
    """Render the data generation + export flow."""
    schema = st.session_state.schema
    if not schema:
        st.info("Define and lock your schema in the 'Schema Design' tab first.")
        return

    section_header(f"Dataset: {schema.get('dataset_name', 'Custom Dataset')}")
    st.write(schema.get("description", ""))

    col_rows, col_btn = st.columns([1, 2])
    with col_rows:
        total_rows = st.number_input(
            "Number of rows", min_value=5, max_value=1000, value=50, step=10
        )
    with col_btn:
        vertical_space("8")
        clicked = st.button(
            "Generate Dataset", type="primary", use_container_width=True,
            disabled=not api_key,
        )

    if clicked:
        _run_generation(api_key, model, schema, total_rows, batch_size)

    if st.session_state.data is not None:
        _render_data_and_export(schema, st.session_state.data)


def _run_generation(api_key, model, schema, total_rows, batch_size) -> None:
    progress = st.progress(0)
    status = st.empty()

    def cb(current: int, total: int) -> None:
        pct = min(int((current / total) * 100), 100)
        progress.progress(pct)
        status.write(f"Synthesized {current} of {total} rows ({pct}%)")

    try:
        generator = DataGenerator(api_key=api_key, model=model)
        data = generator.generate_all(
            schema=schema,
            total_rows=int(total_rows),
            batch_size=batch_size,
            progress_callback=cb,
        )
        st.session_state.data = data
        status.write(f"Completed. Synthesized {len(data)} rows.")
    except Exception as exc:
        st.error(f"Error during data generation: {exc}")


def _render_data_and_export(schema, data) -> None:
    st.markdown("---")

    headers = [col["name"] for col in schema.get("columns", [])]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data)
    csv_data = buf.getvalue()
    size_kb = len(csv_data.encode("utf-8")) / 1024

    stat_caption(f"{len(data)} rows · {len(headers)} cols · {size_kb:.2f} KB")
    st.dataframe(data, use_container_width=True)

    vertical_space("16")

    base_name = schema.get("dataset_name", "dataset").lower().replace(" ", "_")

    st.download_button(
        label="Download CSV",
        data=csv_data.encode("utf-8"),
        file_name=f"{base_name}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    vertical_space("16")
    section_header("Export to Database")
    render_db_export(
        schema=schema,
        data=data,
        default_target=base_name,
        if_exists_options=IF_EXISTS_OPTIONS,
    )