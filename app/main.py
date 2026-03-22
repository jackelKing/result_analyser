import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tempfile
import pandas as pd
import streamlit as st
from io import BytesIO

from app.pipeline import run_student, SEM_COLS
from utils.db import get_credit, save_credit, all_subjects
from utils.calculator import compute_sgpa, compute_cgpa

# ---- Page config ----
st.set_page_config(
    page_title="VTU Performance Analyser",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 High-Speed Academic Performance Analyser")
st.caption("VTU | SGPA · CGPA · Batch Processing | Powered by OCR + Concurrent Downloads")

# ---- Sidebar: subject-credit registry ----
with st.sidebar:
    st.header("📚 Subject-Credit Registry")
    st.caption("Credits are saved permanently — enter once, reused forever.")
    existing = all_subjects()
    if existing:
        st.dataframe(
            pd.DataFrame(list(existing.items()), columns=["Subject Code", "Credits"]),
            use_container_width=True, hide_index=True
        )
    with st.expander("➕ Add / update a subject"):
        sc = st.text_input("Subject Code (e.g. 21CS42)").strip().upper()
        cr = st.number_input("Credits", min_value=1, max_value=5, value=4)
        if st.button("Save"):
            if sc:
                save_credit(sc, int(cr))
                st.success(f"Saved {sc} → {cr} credits")
                st.rerun()

# ---- Main: file upload ----
uploaded = st.file_uploader(
    "Upload Excel sheet (Name, USN, Class, Section, Sem1–Sem6 links)",
    type=["xlsx"],
)

if not uploaded:
    st.info("👆 Upload an Excel file with Google Drive result links to get started.")
    st.stop()

df = pd.read_excel(uploaded)
st.success(f"Loaded **{len(df)} student(s)**")
st.dataframe(df[["Name", "USN", "Class", "Section"]].head(20), use_container_width=True)

# ---- Collect any unknown subjects up-front (optional pre-fill) ----
st.divider()
st.subheader("⚙️ Step 1 — Verify & Run")

run_btn = st.button("🚀 Start Processing", type="primary", use_container_width=True)

if run_btn:
    results_rows = []
    progress = st.progress(0, text="Starting…")
    log_area  = st.empty()
    logs = []

    tmp_dir = tempfile.mkdtemp()

    for idx, row in df.iterrows():
        name = row.get("Name", f"Row {idx+1}")
        usn  = row.get("USN", "")
        progress.progress((idx) / len(df), text=f"Processing {name} ({usn})…")
        logs.append(f"▶ {name} | {usn}")
        log_area.code("\n".join(logs[-15:]))

        sem_results = run_student(row.to_dict(), tmp_dir)

        sgpa_list = []
        sem_detail = {}
        missing_subjects = set()
        credit_map = all_subjects()

        for sem_idx in range(1, 7):
            res = sem_results.get(sem_idx, {})
            if res.get("error"):
                logs.append(f"   Sem{sem_idx}: ⚠ {res['error']}")
                sgpa_list.append(None)
                sem_detail[f"Sem{sem_idx}_SGPA"] = None
                continue

            sgpa, missing = compute_sgpa(res.get("grades", {}), credit_map)
            if missing:
                missing_subjects.update(missing)
            sgpa_list.append(sgpa)
            sem_detail[f"Sem{sem_idx}_SGPA"] = sgpa
            logs.append(f"   Sem{sem_idx}: SGPA={sgpa}  missing_credits={missing}")

        cgpa = compute_cgpa(sgpa_list)
        log_area.code("\n".join(logs[-20:]))

        row_out = {
            "Name": name, "USN": usn,
            "Class": row.get("Class"), "Section": row.get("Section"),
            **sem_detail,
            "CGPA": cgpa,
            "Missing Credits For": ", ".join(sorted(missing_subjects)) if missing_subjects else "",
        }
        results_rows.append(row_out)

    progress.progress(1.0, text="✅ Done!")

    # ---- Results table ----
    result_df = pd.DataFrame(results_rows)
    st.divider()
    st.subheader("📊 Results")
    st.dataframe(result_df, use_container_width=True)

    # ---- Warning: missing credits ----
    missing_all = set()
    for r in results_rows:
        if r["Missing Credits For"]:
            missing_all.update(r["Missing Credits For"].split(", "))
    if missing_all:
        st.warning(
            f"⚠️ Credits missing for: **{', '.join(sorted(missing_all))}**\n\n"
            "Enter them in the sidebar and re-run for accurate results."
        )

    # ---- Download button ----
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False, sheet_name="Results")
    buf.seek(0)
    st.download_button(
        "⬇️ Download Results Excel",
        data=buf,
        file_name="vtu_performance_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
