"""Compact Database Export component.

Driven by the driver registry: any new BaseDatabaseDriver that registers
itself at import time automatically shows up in the target dropdown, with
its ``fields`` rendered as inputs. This keeps the UI in sync with the
backend without touching this function when a new driver is added.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

import streamlit as st

from ...drivers import available_drivers, get_driver
from ...drivers.base import BaseDatabaseDriver, DriverField


def render_db_export(schema: Dict[str, Any],
                     data: List[Dict[str, Any]],
                     default_target: str,
                     if_exists_options: Sequence[str]) -> None:
    """Render the compact DB export block and handle the push action."""
    drivers = available_drivers()
    if not drivers:
        st.warning("No database drivers are registered.")
        return

    db_type = st.selectbox("Target", drivers)
    driver_cls = get_driver(db_type)

    use_uri = "connection_uri" in [f.key for f in driver_cls.fields] and st.checkbox(
        "Use connection URI", value=False
    )

    params: Dict[str, Any] = _collect_fields(driver_cls, use_uri)

    target_label = "Collection name" if not driver_cls.supports_table else "Table name"
    target = st.text_input(target_label, value=default_target)

    if_exists = st.selectbox("If target exists", list(if_exists_options), index=0)

    if st.button("Push to database", type="primary", disabled=not data):
        driver = driver_cls(params=params, use_uri=use_uri)
        ok, msg = driver.export(target=target, schema=schema, data=data,
                                if_exists=if_exists)
        (st.success if ok else st.error)(msg)


def _collect_fields(driver_cls: type, use_uri: bool) -> Dict[str, Any]:
    """Render Streamlit inputs for each DriverField, return collected values."""
    params: Dict[str, Any] = {}

    def render_field(field: DriverField) -> None:
        kwargs = {"label": field.label, "value": field.default}
        # SQLite has no separate port row; keep it inline.
        if field.kind == "password":
            params[field.key] = st.text_input(type="password", **kwargs)
        elif field.kind == "int":
            params[field.key] = st.text_input(**kwargs)  # keep as str; cast in driver
        else:
            params[field.key] = st.text_input(**kwargs)

    # If using URI, show only the URI field.
    if use_uri and any(f.key == "connection_uri" for f in driver_cls.fields):
        uri_field = next(f for f in driver_cls.fields if f.key == "connection_uri")
        render_field(uri_field)
        return params

    # Otherwise show every field except URI/collection.
    to_show = [f for f in driver_cls.fields
               if f.key not in ("connection_uri",)]
    for field in to_show:
        render_field(field)

    return params