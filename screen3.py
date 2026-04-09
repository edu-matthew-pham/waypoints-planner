import streamlit as st
from utils import standards_map, get_prior_chain, generate_pdf
from prompts import build_diagnostic_prompt, build_assessment_prompt

def show():
    selected_codes = st.session_state.selected_codes
    assessments = st.session_state.get("assessments", [])

    if st.button("← Back"):
        st.session_state.page = "s2_nodes"
        st.rerun()

    st.subheader("Assessment Setup")
    st.caption(f"Standards: {', '.join(selected_codes)} · {len(assessments)} assessment item(s)")

    # ── Diagnostic ───────────────────────────────────────────────────────────
    st.subheader("Diagnostic Assessment")
    st.caption("Pre-unit task to probe prior knowledge before teaching begins. Informs starting point and pace profile.")

    existing_diagnostic = st.text_area(
        "Existing diagnostic task (optional)",
        value=st.session_state.get("existing_diagnostic", ""),
        height=100,
        placeholder="Paste existing diagnostic to review, or leave blank to draft new..."
    )
    st.session_state["existing_diagnostic"] = existing_diagnostic

    if st.button("Generate Diagnostic Prompt", use_container_width=True):
        st.session_state["last_diagnostic_prompt"] = build_diagnostic_prompt(
            selected_codes, existing_diagnostic
        )

    if st.session_state.get("last_diagnostic_prompt"):
        st.code(st.session_state["last_diagnostic_prompt"], language=None)
        st.caption("Copy and paste into Claude.ai, ChatGPT, or Gemini.")

    diagnostic_task = st.text_area(
        "Diagnostic task (paste AI output)",
        value=st.session_state.get("diagnostic_task", ""),
        height=120,
        placeholder="Paste the diagnostic task here...",
        label_visibility="collapsed"
    )
    st.session_state["diagnostic_task"] = diagnostic_task

    st.divider()

    # ── Step 1: Generate combined prompt ─────────────────────────────────────
    st.subheader("Step 1 — Generate Assessment Prompt")
    st.caption("Optionally paste existing tasks/summary — the prompt will review them. Leave blank to draft from scratch.")

    # Optional existing inputs per assessment item
    existing_tasks = {}
    with st.expander("Paste existing tasks (optional)"):
        for a in assessments:
            val = st.text_area(
                f"{a['label']} ({a['type']}, {a['timing']})",
                value=st.session_state.get(f"existing_task_{a['id']}", ""),
                height=120,
                placeholder=f"Paste existing {a['label']} task to review, or leave blank...",
                key=f"existing_task_input_{a['id']}"
            )
            st.session_state[f"existing_task_{a['id']}"] = val
            existing_tasks[a["id"]] = val

    existing_summary = st.text_area(
        "Existing summary (optional)",
        value=st.session_state.get("existing_summary", ""),
        height=80,
        placeholder="Paste existing summary to review, or leave blank..."
    )
    st.session_state["existing_summary"] = existing_summary

    if st.button("Generate Assessment Prompt", type="primary", use_container_width=True):
        st.session_state["last_assessment_prompt"] = build_assessment_prompt(
            selected_codes, assessments, existing_tasks, existing_summary
        )

    if st.session_state.get("last_assessment_prompt"):
        st.code(st.session_state["last_assessment_prompt"], language=None)
        st.caption("Copy and paste into Claude.ai, ChatGPT, or Gemini.")

    # ── Step 2: Paste outputs ─────────────────────────────────────────────────
    st.divider()
    st.subheader("Step 2 — Paste AI Outputs")

    for a in assessments:
        task_val = st.text_area(
            f"Output {a['id']}: {a['label']} ({a['type']}, {a['timing']})",
            value=st.session_state.get(f"finalised_task_{a['id']}", ""),
            height=160,
            placeholder=f"Paste Output {a['id']} — {a['label']} task here...",
            key=f"finalised_task_input_{a['id']}"
        )
        st.session_state[f"finalised_task_{a['id']}"] = task_val

    assessment_summary = st.text_area(
        "Combined assessment summary",
        value=st.session_state.get("assessment_summary", ""),
        height=100,
        placeholder="Paste the combined summary here...",
    )
    st.session_state["assessment_summary"] = assessment_summary

    # ── Confirm and export ────────────────────────────────────────────────────
    st.divider()
    all_tasks_filled = all(
        st.session_state.get(f"finalised_task_{a['id']}", "").strip()
        for a in assessments
    )
    task_confirmed = st.checkbox(
        "All assessment tasks and summary are finalised — ready for class planning",
        disabled=not (all_tasks_filled and assessment_summary.strip())
    )

    if task_confirmed:
        st.divider()
        st.subheader("Download Unit Plan")
        st.caption("Class-agnostic PDF — teachers annotate with their friction level.")
        assessment_type = assessments[0]["type"] if assessments else "Test"
        pdf_buf = generate_pdf(
            selected_codes=selected_codes,
            num_lessons=st.session_state.num_lessons,
            assessment_type=assessment_type,
            assessment_summary=assessment_summary
        )
        st.download_button(
            label="⬇ Download Unit Plan PDF",
            data=pdf_buf,
            file_name=f"unit_plan_{'_'.join(selected_codes)}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    st.divider()
    if st.button("Continue to Class Planning →", type="primary",
                 disabled=not task_confirmed, use_container_width=True):
        st.session_state.page = "s4_planning"
        st.rerun()