from __future__ import annotations

from typing import List, Dict, Any
import io
import csv
import streamlit as st
from streamlit_app.state import clear_logs


def render_live_logs(logs: List[str]) -> None:
    """Render live logs with UX controls and download option."""
    st.subheader("Live Logs")
    colA, colB, colC, colD = st.columns([1, 1, 1, 2])
    with colA:
        max_lines = st.selectbox("Lines", options=[100, 200, 500, 1000], index=1)
    with colB:
        wrap = st.toggle("Wrap", value=True)
    with colC:
        if st.button("Clear"):
            clear_logs()
            st.experimental_rerun() if hasattr(st, "experimental_rerun") else st.rerun()
    with colD:
        st.caption("Tip: Streamlit updates logs when new lines arrive. Use Clear to reset view.")

    if not logs:
        st.info("No logs yet.")
        return

    text = "\n".join(logs[-int(max_lines):])
    if wrap:
        st.text_area("Logs", value=text, height=240, label_visibility="collapsed")
    else:
        st.code(text, language="text")

    # Download full logs
    buf = io.StringIO("\n".join(logs))
    st.download_button(
        label="Download Full Logs",
        data=buf.getvalue(),
        file_name="dice_automation_logs.txt",
        mime="text/plain",
    )


def _summary_to_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not summary:
        return rows
    # If future runs include detailed items, adapt here
    rows.append({
        "metric": "applied",
        "value": summary.get("applied", 0),
    })
    rows.append({
        "metric": "failed",
        "value": summary.get("failed", 0),
    })
    if summary.get("failed_jobs"):
        rows.append({
            "metric": "failed_jobs_count",
            "value": len(summary["failed_jobs"]),
        })
    return rows


def render_summary(summary: Dict[str, Any] | None) -> None:
    st.subheader("Summary")
    if not summary:
        st.info("No summary available yet.")
        return
    rows = _summary_to_rows(summary)
    st.table(rows)
    if summary.get("failed_jobs"):
        with st.expander("Failed Jobs"):
            st.write(summary["failed_jobs"]) 

    # Export button (CSV)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["metric", "value"]) 
    for r in rows:
        writer.writerow([r["metric"], r["value"]])
    st.download_button(
        label="Download Summary CSV",
        data=buf.getvalue(),
        file_name="dice_automation_summary.csv",
        mime="text/csv",
    )
