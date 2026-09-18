import os

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from dotenv import load_dotenv

from agents.planner import (
    create_plan,
    InvestigationStep
)

from agents.analyst import (
    execute_investigation_step,
    build_investigation_summary,
    generate_final_analysis,
    choose_chart
)

from agents.decision_agent import (
    decide_next_investigation
)

from agents.sql_validator import (
    validate_sql
)

from utils.preprocessing import (
    preprocess_data,
    run_data_quality_check,
    build_data_profile
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Autonomous AI Data Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid #e5e7eb;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

gemini_api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not gemini_api_key:

    st.error(
        "GEMINI_API_KEY is not configured."
    )

    st.info(
        "Add your Gemini API key to the environment "
        "before running the application."
    )

    st.stop()



# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "🤖 AI Data Analyst"
    )

    st.caption(
        "Autonomous business intelligence powered by AI."
    )

    st.divider()

    st.subheader(
        "⚡ How it works"
    )

    st.markdown(
        """
        **1. 📂 Upload**

        Upload CSV or Excel data.

        **2. 🧹 Clean**

        Detect data quality issues.

        **3. 🧠 Ask**

        Ask a business question.

        **4. 💻 Analyze**

        AI generates analytical SQL.

        **5. 🔎 Investigate**

        AI interprets actual results.

        **6. 🤔 Adapt**

        AI decides what to investigate next.

        **7. 📄 Report**

        Generate the final analyst report.
        """
    )

    st.divider()

    st.subheader(
        "🔒 Data Safety"
    )

    st.caption(
        "The analytical dataset is read-only. "
        "AI-generated SQL is validated before execution."
    )

    st.divider()

    st.subheader(
        "🧰 Technology"
    )

    st.caption(
        "Python • Streamlit • Gemini • DuckDB • "
        "Pandas • Plotly"
    )


# ============================================================
# HERO SECTION
# ============================================================

st.title(
    "🤖 Autonomous AI Data Analyst"
)

st.subheader(
    "Turn raw datasets into business insights."
)

st.write(
    "Upload a CSV or Excel dataset, ask a business question, "
    "and let AI investigate the data using SQL, "
    "adaptive reasoning, and automated visualization."
)

st.divider()


# ============================================================
# FEATURE OVERVIEW
# ============================================================

st.subheader(
    "🚀 What this application can do"
)

feature_col1, feature_col2, feature_col3, feature_col4 = (
    st.columns(4)
)


with feature_col1:

    st.info(
        """
        ### 🧹 Data Quality

        Detect missing values, duplicates,
        dates, categories and potential outliers.
        """
    )


with feature_col2:

    st.info(
        """
        ### 🧠 Autonomous Analysis

        Convert business questions into
        multi-step analytical investigations.
        """
    )


with feature_col3:

    st.info(
        """
        ### 💻 Advanced SQL

        CTEs, window functions, joins,
        subqueries, rankings and more.
        """
    )


with feature_col4:

    st.info(
        """
        ### 📊 AI Insights

        Findings, visualizations and a
        business-focused analyst report.
        """
    )


st.divider()


# ============================================================
# DATASET UPLOAD
# ============================================================

st.markdown(
    '<div class="section-title">📂 Upload Your Dataset</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Upload a CSV or Excel file to begin the analysis.'
    '</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Choose a dataset",
    type=[
        "csv",
        "xlsx"
    ],
    label_visibility="collapsed"
)


# ============================================================
# NO DATASET
# ============================================================

if uploaded_file is None:

    st.info(
        "👆 Upload a CSV or Excel dataset to get started."
    )

    st.markdown(
        """
        ### 💡 Example questions

        Try asking questions such as:

        - **Why did profit decline?**
        - **Which products are underperforming?**
        - **Which region contributes most to revenue?**
        - **What changed after April?**
        - **Which customers generate the most revenue?**
        - **Are discounts affecting profitability?**
        """
    )

    st.markdown(
        """
        <div class="footer">
            Autonomous AI Data Analyst
        </div>
        """,
        unsafe_allow_html=True
    )

    st.stop()


# ============================================================
# LOAD DATASET
# ============================================================

with st.spinner(
    "📂 Loading dataset..."
):

    try:

        if uploaded_file.name.lower().endswith(
            ".csv"
        ):

            df = pd.read_csv(
                uploaded_file
            )

        else:

            df = pd.read_excel(
                uploaded_file
            )

    except Exception as e:

        st.error(
            f"❌ Could not read the uploaded file:\n\n{e}"
        )

        st.stop()


# ============================================================
# BASIC VALIDATION
# ============================================================

if df.empty:

    st.error(
        "❌ The uploaded dataset is empty."
    )

    st.stop()


if len(df.columns) == 0:

    st.error(
        "❌ The dataset does not contain any columns."
    )

    st.stop()


# ============================================================
# PREPROCESSING
# ============================================================

with st.spinner(
    "🧹 Preprocessing dataset..."
):

    try:

        df, detected_dates = (
            preprocess_data(df)
        )

    except Exception as e:

        st.error(
            f"❌ Preprocessing failed:\n\n{e}"
        )

        st.stop()


# ============================================================
# DATA QUALITY
# ============================================================

with st.spinner(
    "🔍 Running data quality checks..."
):

    try:

        df, quality_report = (
            run_data_quality_check(df)
        )

    except Exception as e:

        st.error(
            f"❌ Data quality check failed:\n\n{e}"
        )

        st.stop()


# ============================================================
# DATA PROFILE
# ============================================================

try:

    data_profile = build_data_profile(
        df,
        quality_report
    )

except Exception as e:

    st.error(
        f"❌ Could not build data profile:\n\n{e}"
    )

    st.stop()


# ============================================================
# DATASET STATUS
# ============================================================

st.success(
    f"✅ {uploaded_file.name} loaded successfully"
)


# ============================================================
# DATASET METRICS
# ============================================================

st.markdown(
    '<div class="section-title">📊 Dataset Health</div>',
    unsafe_allow_html=True
)

metric1, metric2, metric3, metric4 = (
    st.columns(4)
)

metric1.metric(
    "Rows",
    f"{len(df):,}"
)

metric2.metric(
    "Columns",
    f"{len(df.columns):,}"
)

metric3.metric(
    "Missing Values",
    f"{int(df.isna().sum().sum()):,}"
)

metric4.metric(
    "Duplicates Removed",
    f"{quality_report.get('duplicate_rows', 0):,}"
)


# ============================================================
# DATA QUALITY DETAILS
# ============================================================

with st.expander(
    "🔍 View Data Quality Details"
):

    quality_tab1, quality_tab2, quality_tab3 = (
        st.tabs(
            [
                "⚠️ Missing Values",
                "📈 Outliers",
                "🏷️ Categories"
            ]
        )
    )

    # --------------------------------------------------------
    # Missing
    # --------------------------------------------------------

    with quality_tab1:

        missing_values = quality_report.get(
            "missing_values"
        )

        if (
            missing_values is not None
            and len(missing_values) > 0
        ):

            missing_rows = []

            for column, count in (
                missing_values.items()
            ):

                missing_rows.append({
                    "Column": column,
                    "Missing Values": int(count),
                    "Missing %": round(
                        count / len(df) * 100,
                        2
                    )
                })

            st.dataframe(
                pd.DataFrame(
                    missing_rows
                ),
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "Missing values are detected but not automatically filled."
            )

        else:

            st.success(
                "✅ No missing values detected."
            )

    # --------------------------------------------------------
    # Outliers
    # --------------------------------------------------------

    with quality_tab2:

        outliers = quality_report.get(
            "outliers",
            {}
        )

        if outliers:

            outlier_rows = []

            for column, details in (
                outliers.items()
            ):

                outlier_rows.append({
                    "Column": column,
                    "Potential Outliers": (
                        details["count"]
                    ),
                    "Lower Bound": (
                        details["lower_bound"]
                    ),
                    "Upper Bound": (
                        details["upper_bound"]
                    )
                })

            st.dataframe(
                pd.DataFrame(
                    outlier_rows
                ),
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "Potential outliers are detected but not removed."
            )

        else:

            st.success(
                "✅ No major statistical outliers detected."
            )

    # --------------------------------------------------------
    # Categories
    # --------------------------------------------------------

    with quality_tab3:

        category_summary = quality_report.get(
            "category_summary",
            {}
        )

        if category_summary:

            category_rows = []

            for column, details in (
                category_summary.items()
            ):

                category_rows.append({
                    "Column": column,
                    "Unique Values": (
                        details["unique_values"]
                    ),
                    "Sample Values": ", ".join(
                        map(
                            str,
                            details["sample_values"]
                        )
                    )
                })

            st.dataframe(
                pd.DataFrame(
                    category_rows
                ),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No categorical columns detected."
            )


# ============================================================
# DATA PREVIEW
# ============================================================

with st.expander(
    "👀 Preview Preprocessed Dataset"
):

    st.dataframe(
        df.head(20),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "This is the dataset used for all analytical queries."
    )


# ============================================================
# AI DATA PROFILE
# ============================================================

with st.expander(
    "🧠 View Data Profile Sent to AI"
):

    st.json(
        data_profile
    )


# ============================================================
# DUCKDB
# ============================================================

con = duckdb.connect(
    database=":memory:"
)

con.register(
    "sales",
    df
)


# ============================================================
# ANALYSIS
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">🔎 Analyze Your Data</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Choose autonomous AI investigation or write SQL yourself.'
    '</div>',
    unsafe_allow_html=True
)

tab_ai, tab_sql = st.tabs(
    [
        "🧠 Ask AI",
        "💻 SQL Playground"
    ]
)


# ============================================================
# ASK AI
# ============================================================

with tab_ai:

    st.markdown(
        "### 🧠 Ask a Business Question"
    )

    question = st.text_area(
        "What would you like to understand?",
        placeholder=(
            "Example: Why did profit decline?"
        ),
        height=120,
        key="business_question"
    )

    st.caption(
        "Ask a question in natural language. "
        "The AI will determine how to investigate it."
    )

    example_col1, example_col2, example_col3 = (
        st.columns(3)
    )

    with example_col1:

        st.markdown(
            "**📉 Performance**"
        )

        st.caption(
            "Why did profit decline?"
        )

    with example_col2:

        st.markdown(
            "**🌍 Segments**"
        )

        st.caption(
            "Which region performs best?"
        )

    with example_col3:

        st.markdown(
            "**📦 Products**"
        )

        st.caption(
            "Which products are underperforming?"
        )

    investigate = st.button(
        "🚀 Start Investigation",
        type="primary",
        use_container_width=True,
        key="investigate_button"
    )

    if investigate:

        if not question.strip():

            st.warning(
                "⚠️ Please enter a business question."
            )

            st.stop()

        # ====================================================
        # SCHEMA
        # ====================================================

        schema_lines = []

        for column in df.columns:

            schema_lines.append(
                f"{column}: {df[column].dtype}"
            )

        schema = "\n".join(
            schema_lines
        )

        # ====================================================
        # INITIAL PLAN
        # ====================================================

        st.divider()

        st.markdown(
            "### 🧠 Initial AI Direction"
        )

        with st.spinner(
            "Gemini is understanding the question..."
        ):

            try:

                plan = create_plan(
                    schema=schema,
                    question=question,
                    data_profile=data_profile
                )

            except Exception as e:

                st.error(
                    f"❌ Planner error:\n\n{e}"
                )

                st.stop()

        st.success(
            "✅ Initial investigation direction created."
        )

        st.markdown(
            f"**Objective:** {plan.objective}"
        )

        for step in plan.steps:

            st.markdown(
                f"""
                <div class="investigation-card">

                    <div class="step-number">
                        Direction {step.step}
                    </div>

                    <div>
                        {step.analysis}
                    </div>

                    <div style="color:#6b7280; margin-top:5px;">
                        Why: {step.reason}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        if not plan.steps:

            st.error(
                "❌ No investigation direction was generated."
            )

            st.stop()

        # ====================================================
        # AUTONOMOUS INVESTIGATION
        # ====================================================

        st.divider()

        st.markdown(
            "### 🤖 Autonomous Investigation"
        )

        st.caption(
            "After every investigation, the AI examines the "
            "actual evidence and decides what to investigate next."
        )

        investigation_results = []

        previous_evidence = ""

        current_step = plan.steps[0]

        max_steps = 8

        progress_bar = st.progress(
            0
        )

        for iteration in range(
            max_steps
        ):

            # =================================================
            # STEP HEADER
            # =================================================

            st.markdown(
                f"#### 🔎 Step {current_step.step}"
            )

            st.write(
                f"**Investigation:** "
                f"{current_step.analysis}"
            )

            st.caption(
                f"Why this matters: {current_step.reason}"
            )

            # =================================================
            # EXECUTION
            # =================================================

            with st.spinner(
                f"Running investigation step "
                f"{current_step.step}..."
            ):

                try:

                    step_result = (
                        execute_investigation_step(
                            con=con,
                            schema=schema,
                            question=question,
                            step=current_step,
                            previous_evidence=(
                                previous_evidence
                            )
                        )
                    )

                except Exception as e:

                    step_result = {
                        "step": current_step.step,
                        "analysis": current_step.analysis,
                        "reason": current_step.reason,
                        "sql": None,
                        "result": None,
                        "finding": None,
                        "error": str(e)
                    }

            investigation_results.append(
                step_result
            )

            # =================================================
            # SQL
            # =================================================

            if step_result["sql"]:

                with st.expander(
                    "💻 View Generated SQL"
                ):

                    st.code(
                        step_result["sql"],
                        language="sql"
                    )

            # =================================================
            # ERROR
            # =================================================

            if step_result["error"]:

                st.error(
                    f"❌ Step failed:\n\n"
                    f"{step_result['error']}"
                )

                break

            # =================================================
            # RESULT
            # =================================================

            result_df = step_result[
                "result"
            ]

            st.markdown(
                "**📊 Evidence**"
            )

            if (
                result_df is not None
                and not result_df.empty
            ):

                st.dataframe(
                    result_df,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "The query returned no rows."
                )

            # =================================================
            # FINDING
            # =================================================

            finding = step_result[
                "finding"
            ]

            if finding:

                st.markdown(
                    "**🧠 AI Finding**"
                )

                st.success(
                    finding
                )

                previous_evidence += (
                    f"\n\n"
                    f"Step {current_step.step} Finding:\n"
                    f"{finding}"
                )

            # =================================================
            # VISUALIZATION
            # =================================================

            if (
                result_df is not None
                and not result_df.empty
            ):

                try:

                    chart_config = (
                        choose_chart(
                            question=question,
                            step=current_step,
                            result=result_df
                        )
                    )

                except Exception:

                    chart_config = {
                        "chart_type": "none",
                        "x_column": None,
                        "y_column": None,
                        "title": None
                    }

                chart_type = chart_config.get(
                    "chart_type",
                    "none"
                )

                x_column = chart_config.get(
                    "x_column"
                )

                y_column = chart_config.get(
                    "y_column"
                )

                chart_title = chart_config.get(
                    "title"
                )

                try:

                    if chart_type == "line":

                        fig = px.line(
                            result_df,
                            x=x_column,
                            y=y_column,
                            title=chart_title
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                    elif chart_type == "bar":

                        fig = px.bar(
                            result_df,
                            x=x_column,
                            y=y_column,
                            title=chart_title
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                    elif chart_type == "scatter":

                        fig = px.scatter(
                            result_df,
                            x=x_column,
                            y=y_column,
                            title=chart_title
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                    elif chart_type == "pie":

                        fig = px.pie(
                            result_df,
                            names=x_column,
                            values=y_column,
                            title=chart_title
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                except Exception as e:

                    st.warning(
                        f"Visualization could not be generated: {e}"
                    )

            # =================================================
            # DECISION AGENT
            # =================================================

            st.markdown(
                "**🤔 AI Decision**"
            )

            with st.spinner(
                "AI is deciding what to investigate next..."
            ):

                try:

                    decision = (
                        decide_next_investigation(
                            question=question,
                            data_profile=data_profile,
                            investigation_history=(
                                investigation_results
                            )
                        )
                    )

                except Exception as e:

                    st.warning(
                        "The Decision Agent could not "
                        "continue the investigation."
                    )

                    break

            # =================================================
            # STOP
            # =================================================

            if not decision.continue_investigation:

                st.success(
                    "🛑 The AI determined that the available "
                    "evidence is sufficient."
                )

                st.caption(
                    decision.reason
                )

                break

            # =================================================
            # CONTINUE
            # =================================================

            if not decision.next_analysis:

                st.warning(
                    "The AI chose to continue but did not "
                    "provide another investigation."
                )

                break

            st.info(
                f"➡️ **Next:** {decision.next_analysis}"
            )

            st.caption(
                f"Reason: {decision.reason}"
            )

            current_step = InvestigationStep(
                step=len(
                    investigation_results
                ) + 1,
                analysis=decision.next_analysis,
                reason=decision.reason
            )

            progress_bar.progress(
                min(
                    int(
                        (
                            (iteration + 1)
                            / max_steps
                        ) * 100
                    ),
                    100
                )
            )

        # ====================================================
        # COMPLETE
        # ====================================================

        progress_bar.progress(
            100
        )

        st.divider()

        st.markdown(
            "### 🛑 Investigation Complete"
        )

        st.success(
            f"Completed {len(investigation_results)} "
            f"adaptive investigation step(s)."
        )

        # ====================================================
        # EVIDENCE
        # ====================================================

        if investigation_results:

            evidence_summary = (
                build_investigation_summary(
                    investigation_results
                )
            )

            with st.expander(
                "📚 View Full Investigation Evidence"
            ):

                st.text_area(
                    "Evidence",
                    evidence_summary,
                    height=500,
                    key="evidence_output"
                )

            # =================================================
            # FINAL REPORT
            # =================================================

            st.divider()

            st.markdown(
                "### 📄 Final Analyst Report"
            )

            with st.spinner(
                "Gemini is synthesizing the final business analysis..."
            ):

                try:

                    final_analysis = (
                        generate_final_analysis(
                            question=question,
                            investigation_summary=(
                                evidence_summary
                            )
                        )
                    )

                except Exception as e:

                    st.error(
                        f"❌ Final analysis failed:\n\n{e}"
                    )

                    final_analysis = None

            if final_analysis:

                st.success(
                    "✅ Final analyst report generated."
                )

                st.markdown(
                    final_analysis
                )

            else:

                st.warning(
                    "The final report could not be generated."
                )


# ============================================================
# SQL PLAYGROUND
# ============================================================

with tab_sql:

    st.markdown(
        "### 💻 SQL Playground"
    )

    st.caption(
        "Write analytical SQL directly against the "
        "preprocessed dataset."
    )

    st.info(
        "Table name: `sales`"
    )

    st.markdown(
        """
        **Supported analytical SQL**

        CTEs • Multiple CTEs • Window Functions •
        Subqueries • JOINs • CASE WHEN • GROUP BY •
        HAVING • UNION • Date Functions • Rankings •
        Running Totals • Moving Averages •
        Period-over-Period Analysis
        """
    )

    query = st.text_area(
        "SQL Query",
        value=(
            "WITH monthly_profit AS (\n"
            "    SELECT\n"
            "        DATE_TRUNC('month', order_date) AS month,\n"
            "        SUM(profit) AS profit\n"
            "    FROM sales\n"
            "    GROUP BY 1\n"
            ")\n"
            "SELECT\n"
            "    month,\n"
            "    profit,\n"
            "    profit - LAG(profit) OVER (\n"
            "        ORDER BY month\n"
            "    ) AS profit_change\n"
            "FROM monthly_profit\n"
            "ORDER BY month;"
        ),
        height=320,
        key="sql_query"
    )

    run_query = st.button(
        "▶ Run SQL",
        type="primary",
        use_container_width=True,
        key="run_sql_button"
    )

    if run_query:

        if not query.strip():

            st.warning(
                "⚠️ Please enter a SQL query."
            )

        else:

            # =================================================
            # VALIDATION
            # =================================================

            with st.spinner(
                "🔒 Validating SQL..."
            ):

                try:

                    is_valid, error_message = (
                        validate_sql(
                            con,
                            query
                        )
                    )

                except Exception as e:

                    is_valid = False
                    error_message = str(e)

            if not is_valid:

                st.error(
                    f"❌ Query blocked:\n\n{error_message}"
                )

            else:

                # =============================================
                # EXECUTION
                # =============================================

                with st.spinner(
                    "⚙️ Executing SQL..."
                ):

                    try:

                        result = (
                            con.execute(
                                query
                            )
                            .df()
                        )

                        st.success(
                            f"✅ Query executed successfully — "
                            f"{len(result):,} rows returned."
                        )

                        st.markdown(
                            "### 📊 Query Result"
                        )

                        st.dataframe(
                            result,
                            use_container_width=True,
                            hide_index=True
                        )

                        st.caption(
                            "This result comes directly from your SQL. "
                            "No AI interpretation or AI-generated "
                            "finding is performed in the SQL Playground."
                        )

                    except Exception as e:

                        st.error(
                            f"❌ SQL execution error:\n\n{e}"
                        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        🤖 Autonomous AI Data Analyst
        &nbsp;•&nbsp;
        Gemini + DuckDB + Streamlit
        &nbsp;•&nbsp;
        Read-only analytical environment
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CLOSE CONNECTION
# ============================================================

con.close()