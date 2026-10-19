import os

import pandas as pd
import streamlit as st

from orchestrator import (
    PipelineError,
    execute_query,
    new_state,
    run_phase1,
    run_phase2,
    run_phase3,
    run_phase4,
)

st.set_page_config(page_title="Retail Medallion Pipeline", layout="wide")

st.title("Retail Medallion Pipeline")
st.write(
    "Upload a raw retail CSV file and run it through the Bronze → Silver → Gold "
    "medallion pipeline. At the end of each layer, review the AI-generated "
    "source-to-target mapping (STTM) and approve it before the next phase runs. "
    "Once the Gold layer is ready, ask a business question against it."
)

PHASES = [
    ("Phase 1 — Profile raw data & generate Bronze STTM", run_phase1, "bronze_sttm_path"),
    ("Phase 2 — Ingest Bronze data & generate Silver STTM", run_phase2, "silver_sttm_path"),
    ("Phase 3 — Ingest Silver data & generate Gold STTM", run_phase3, "gold_sttm_path"),
    ("Phase 4 — Materialize Gold tables", run_phase4, None),
]

if "state" not in st.session_state:
    st.session_state.state = None
if "phase_index" not in st.session_state:
    st.session_state.phase_index = 0
if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False

st.subheader("1. Upload raw data")
uploaded_file = st.file_uploader("Upload a raw CSV file", type="csv")

object_name = None
if uploaded_file is not None:
    object_name = os.path.splitext(uploaded_file.name)[0]
    os.makedirs("data/raw", exist_ok=True)
    raw_path = f"data/raw/{object_name}.csv"
    with open(raw_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Saved upload to {raw_path}")

st.subheader("2. Run pipeline")

col1, col2 = st.columns(2)
with col1:
    if st.button(
        "Start Pipeline",
        type="primary",
        disabled=object_name is None or st.session_state.state is not None,
    ):
        st.session_state.state = new_state(object_name)
        st.session_state.phase_index = 0
        st.session_state.awaiting_approval = False
        st.rerun()
with col2:
    if st.button("Reset"):
        st.session_state.state = None
        st.session_state.phase_index = 0
        st.session_state.awaiting_approval = False
        st.rerun()

st.markdown("**Progress**")
for i, (label, _, _) in enumerate(PHASES):
    if st.session_state.state is None or i > st.session_state.phase_index:
        st.write(f"⬜ {label}")
    elif i < st.session_state.phase_index:
        st.write(f"✅ {label}")
    elif st.session_state.awaiting_approval:
        st.write(f"⏸️ {label} — awaiting your approval")
    else:
        st.write(f"🔄 {label} — running")

if st.session_state.state is not None and st.session_state.phase_index < len(PHASES):
    label, phase_fn, sttm_key = PHASES[st.session_state.phase_index]

    if not st.session_state.awaiting_approval:
        with st.spinner(f"Running {label}..."):
            try:
                st.session_state.state = phase_fn(st.session_state.state)
            except PipelineError as e:
                st.error(f"Pipeline aborted: {e}")
                st.session_state.state = None
                st.stop()
        if sttm_key:
            st.session_state.awaiting_approval = True
        else:
            st.session_state.phase_index += 1
        st.rerun()

    if st.session_state.awaiting_approval and sttm_key:
        sttm_path = st.session_state.state[sttm_key]
        st.markdown(f"**Review generated STTM:** `{sttm_path}`")
        st.dataframe(pd.read_csv(sttm_path), use_container_width=True)

        approve_col, reject_col = st.columns(2)
        with approve_col:
            if st.button("✅ Approve & Continue", type="primary"):
                st.session_state.awaiting_approval = False
                st.session_state.phase_index += 1
                st.rerun()
        with reject_col:
            if st.button("❌ Reject & Stop"):
                st.session_state.state = None
                st.session_state.phase_index = 0
                st.session_state.awaiting_approval = False
                st.warning("Pipeline halted — STTM rejected.")
                st.stop()

if st.session_state.state is not None and st.session_state.phase_index >= len(PHASES):
    st.success("Pipeline completed successfully! Gold tables are ready to query.")

st.divider()

st.subheader("3. Ask a business question")
question = st.text_input("Question", value="Which product has the least sales?")

if st.button("Run Query"):
    gold_pq_folder = (st.session_state.state or {}).get("gold_pq_folder")
    if not gold_pq_folder:
        st.warning("Complete the pipeline (through approval) before querying Gold data.")
    else:
        with st.spinner("Generating and executing SQL query..."):
            try:
                object_name = st.session_state.state.get("object", "pipeline")
                result_df, report_path = execute_query(gold_pq_folder, question, object_name)
                st.dataframe(result_df, use_container_width=True)

                with open(report_path, "rb") as f:
                    st.download_button(
                        "Download HTML Report",
                        data=f,
                        file_name=os.path.basename(report_path),
                        mime="text/html",
                    )
            except Exception as e:
                st.error(f"Query failed: {e}")
