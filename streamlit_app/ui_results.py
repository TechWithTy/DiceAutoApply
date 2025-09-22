from __future__ import annotations

from typing import List, Dict, Any
import io
import csv
import streamlit as st


def render_live_logs(logs: List[str]) -> None:
    """Render the last N lines of logs with auto-scroll behavior."""
    st.subheader("Live Logs")
    if not logs:
        st.info("No logs yet.")
        return
    # Show last 200 lines to keep UI fast
    st.code("\n".join(logs[-200:]), language="text")


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
