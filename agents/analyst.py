import os
import json

from google import genai
from dotenv import load_dotenv

from agents.sql_agent import (
    generate_sql,
    correct_sql
)

from agents.sql_validator import (
    validate_sql
)

from agents.decision_agent import (
    decide_next_investigation
)

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# SETTINGS
# ============================================================

MAX_SQL_RETRIES = 3


# ============================================================
# DATAFRAME → TEXT
# ============================================================

def dataframe_to_text(
    df,
    max_rows=20
):
    """
    Convert a query result into text
    for Gemini analysis.
    """

    if df is None:
        return "No result available."

    if df.empty:
        return "Query returned zero rows."

    return df.head(max_rows).to_string(
        index=False
    )


# ============================================================
# GENERATE FINDING
# ============================================================

def generate_finding(
    question,
    step,
    sql,
    result,
    previous_evidence
):
    """
    Analyze the actual SQL result and generate
    one analytical finding.
    """

    result_text = dataframe_to_text(
        result
    )

    prompt = f"""
You are an expert Data Analyst.

You are performing a multi-step investigation
of a business question.

Interpret the ACTUAL SQL result and produce
a concise analytical finding.

============================================================
BUSINESS QUESTION
============================================================

{question}

============================================================
CURRENT INVESTIGATION STEP
============================================================

Step {step.step}

Analysis:
{step.analysis}

Reason:
{step.reason}

============================================================
SQL EXECUTED
============================================================

{sql}

============================================================
ACTUAL SQL RESULT
============================================================

{result_text}

============================================================
PREVIOUS INVESTIGATION EVIDENCE
============================================================

{previous_evidence}

============================================================
RULES
============================================================

1. Base the finding only on the actual result.

2. Do not invent numbers.

3. Do not invent columns.

4. Compare values when useful.

5. Identify meaningful trends or differences.

6. Explain what the result means for the
   original business question.

7. Do not recommend actions yet.

8. If the result is insufficient, explicitly
   say that the evidence is insufficient.

9. Do not claim causation unless the data
   actually supports it.

============================================================
OUTPUT
============================================================

Return one concise analytical finding.
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        store=False
    )

    return interaction.output_text.strip()


# ============================================================
# EXECUTE ONE INVESTIGATION STEP
# ============================================================

def execute_investigation_step(
    con,
    schema,
    question,
    step,
    previous_evidence=""
):
    """
    Execute one autonomous investigation step.

    Flow:

    Gemini SQL
        ↓
    Validator
        ↓
    DuckDB
        ↓
    Result
        ↓
    Gemini Finding

    If SQL fails:

    Error
        ↓
    Gemini SQL Correction
        ↓
    Validator
        ↓
    DuckDB
    """

    current_sql = None
    error_message = None

    # ========================================================
    # GENERATE INITIAL SQL
    # ========================================================

    try:

        current_sql = generate_sql(
            schema=schema,
            analysis_step=step.analysis,
            question=question,
            previous_evidence=previous_evidence
        )

    except Exception as e:

        return {
            "step": step.step,
            "analysis": step.analysis,
            "reason": step.reason,
            "sql": None,
            "result": None,
            "finding": None,
            "error": f"SQL generation failed: {e}"
        }

    # ========================================================
    # VALIDATE + EXECUTE
    # ========================================================

    for attempt in range(MAX_SQL_RETRIES):

        # ----------------------------------------------------
        # Validate SQL
        # ----------------------------------------------------

        is_valid, validation_error = validate_sql(
            con,
            current_sql
        )

        if not is_valid:

            error_message = validation_error

        else:

            # ------------------------------------------------
            # Execute SQL
            # ------------------------------------------------

            try:

                result = (
                    con.execute(
                        current_sql
                    )
                    .df()
                )

                # --------------------------------------------
                # Generate analytical finding
                # --------------------------------------------

                finding = generate_finding(
                    question=question,
                    step=step,
                    sql=current_sql,
                    result=result,
                    previous_evidence=previous_evidence
                )

                return {
                    "step": step.step,
                    "analysis": step.analysis,
                    "reason": step.reason,
                    "sql": current_sql,
                    "result": result,
                    "finding": finding,
                    "error": None
                }

            except Exception as e:

                error_message = str(e)

        # ====================================================
        # SQL CORRECTION
        # ====================================================

        if attempt < MAX_SQL_RETRIES - 1:

            try:

                current_sql = correct_sql(
                    schema=schema,
                    original_sql=current_sql,
                    error_message=error_message,
                    analysis_step=step.analysis,
                    question=question,
                    previous_evidence=previous_evidence
                )

            except Exception as e:

                return {
                    "step": step.step,
                    "analysis": step.analysis,
                    "reason": step.reason,
                    "sql": current_sql,
                    "result": None,
                    "finding": None,
                    "error": (
                        "SQL correction failed: "
                        f"{e}"
                    )
                }

    # ========================================================
    # ALL RETRIES FAILED
    # ========================================================

    return {
        "step": step.step,
        "analysis": step.analysis,
        "reason": step.reason,
        "sql": current_sql,
        "result": None,
        "finding": None,
        "error": error_message
    }


# ============================================================
# BUILD INVESTIGATION SUMMARY
# ============================================================

def build_investigation_summary(
    investigation_results
):
    """
    Build a detailed evidence package
    for the final analyst.
    """

    summaries = []

    for item in investigation_results:

        result_text = dataframe_to_text(
            item["result"]
        )

        summary = f"""
============================================================
STEP {item['step']}
============================================================

Analysis:
{item['analysis']}

Reason:
{item['reason']}

SQL:
{item['sql']}

Actual Result:
{result_text}

Finding:
{item['finding']}

Error:
{item['error']}
"""

        summaries.append(summary)

    return "\n".join(
        summaries
    )


# ============================================================
# FINAL ANALYSIS
# ============================================================

def generate_final_analysis(
    question,
    investigation_summary
):
    """
    Synthesize all investigation evidence
    into a final business report.
    """

    prompt = f"""
You are a senior Data Analyst.

You have completed a multi-step investigation
of a business question.

Your task is to synthesize the investigation
into a clear, evidence-based business analysis.

============================================================
BUSINESS QUESTION
============================================================

{question}

============================================================
INVESTIGATION EVIDENCE
============================================================

{investigation_summary}

============================================================
YOUR TASK
============================================================

Analyze the evidence and produce a final analyst report.

The report should contain:

1. EXECUTIVE SUMMARY

Give a concise answer to the original business question.

2. KEY FINDINGS

List the most important findings discovered during
the investigation.

3. ROOT CAUSE ANALYSIS

Explain the likely drivers behind the observed outcome.

Separate strong evidence from weaker signals.

4. SUPPORTING EVIDENCE

Use actual numbers from the investigation results
where available.

5. BUSINESS RECOMMENDATIONS

Provide practical actions that follow from the evidence.

6. LIMITATIONS

Mention important limitations or missing information
that could affect the conclusion.

============================================================
STRICT RULES
============================================================

1. Use ONLY the evidence provided above.

2. Do NOT invent data.

3. Do NOT invent numbers.

4. Do NOT claim causation when the data only shows
   correlation.

5. Clearly distinguish observation from interpretation.

6. Recommendations must be connected to observed evidence.

7. If evidence is insufficient, say so.

8. Do not repeat the same finding unnecessarily.

9. Write for a business stakeholder rather than a programmer.

============================================================
OUTPUT FORMAT
============================================================

# Executive Summary

...

# Key Findings

- ...
- ...
- ...

# Root Cause Analysis

...

# Supporting Evidence

- ...
- ...
- ...

# Business Recommendations

1. ...
2. ...
3. ...

# Limitations

- ...
- ...
"""
    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        store=False
    )

    return interaction.output_text.strip()


# ============================================================
# CHART SELECTION
# ============================================================

def choose_chart(
    question,
    step,
    result
):
    """
    Ask Gemini whether the query result
    should be visualized and which chart
    type is appropriate.
    """

    if result is None or result.empty:

        return {
            "chart_type": "none",
            "x_column": None,
            "y_column": None,
            "title": None
        }

    columns = list(
        result.columns
    )

    result_text = dataframe_to_text(
        result,
        max_rows=20
    )

    prompt = f"""
You are an expert Data Visualization Analyst.

You need to decide whether a query result
should be visualized.

============================================================
BUSINESS QUESTION
============================================================

{question}

============================================================
INVESTIGATION STEP
============================================================

{step.analysis}

============================================================
AVAILABLE COLUMNS
============================================================

{columns}

============================================================
QUERY RESULT
============================================================

{result_text}

============================================================
CHART OPTIONS
============================================================

Choose ONE:

- line
- bar
- scatter
- pie
- none

============================================================
GUIDELINES
============================================================

LINE:
Use for trends over time.

BAR:
Use for comparisons between categories.

SCATTER:
Use for relationships between two numeric variables.

PIE:
Use only when there are a small number of categories
representing parts of a whole.

NONE:
Use when visualization does not add meaningful value.

============================================================
RULES
============================================================

1. Use ONLY columns present in the result.

2. Do not invent column names.

3. For line charts, x should normally be a date/time column.

4. For bar charts, x should normally be categorical.

5. For scatter plots, x and y should be numeric.

6. Do not visualize identifiers unnecessarily.

7. Keep the visualization simple.

8. Return JSON only.

============================================================
OUTPUT
============================================================

Return exactly:

{{
    "chart_type": "line",
    "x_column": "column_name",
    "y_column": "column_name",
    "title": "Chart title"
}}

For no chart:

{{
    "chart_type": "none",
    "x_column": null,
    "y_column": null,
    "title": null
}}
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        store=False
    )

    response_text = (
        interaction.output_text
        .strip()
    )

    # --------------------------------------------------------
    # Clean JSON Markdown
    # --------------------------------------------------------

    if response_text.startswith("```json"):

        response_text = response_text[
            len("```json"):
        ]

    elif response_text.startswith("```"):

        response_text = response_text[
            len("```"):
        ]

    if response_text.endswith("```"):

        response_text = response_text[:-3]

    response_text = response_text.strip()

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        chart_config = json.loads(
            response_text
        )

    except Exception:

        return {
            "chart_type": "none",
            "x_column": None,
            "y_column": None,
            "title": None
        }

    # --------------------------------------------------------
    # Extract values
    # --------------------------------------------------------

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

    title = chart_config.get(
        "title"
    )

    # --------------------------------------------------------
    # Validate chart type
    # --------------------------------------------------------

    allowed_chart_types = [
        "line",
        "bar",
        "scatter",
        "pie",
        "none"
    ]

    if chart_type not in allowed_chart_types:

        chart_type = "none"

    # --------------------------------------------------------
    # Validate columns
    # --------------------------------------------------------

    if x_column not in columns:

        x_column = None

    if y_column not in columns:

        y_column = None

    # --------------------------------------------------------
    # Validate chart configuration
    # --------------------------------------------------------

    if chart_type != "none":

        if x_column is None:

            chart_type = "none"

        elif chart_type != "pie" and y_column is None:

            chart_type = "none"

    return {
        "chart_type": chart_type,
        "x_column": x_column,
        "y_column": y_column,
        "title": title
    }
    
def run_adaptive_investigation(
    con,
    schema,
    question,
    data_profile,
    initial_steps,
    max_steps=8
):
    """
    Run an adaptive autonomous investigation.

    The agent:

    1. Executes an investigation step.
    2. Observes the actual result.
    3. Generates a finding.
    4. Decides what to investigate next.
    5. Repeats until the evidence is sufficient.
    """

    investigation_results = []

    previous_evidence = ""

    # --------------------------------------------------------
    # First step comes from the initial planner
    # --------------------------------------------------------

    if not initial_steps:

        return investigation_results

    current_step = initial_steps[0]

    # --------------------------------------------------------
    # Adaptive loop
    # --------------------------------------------------------

    for iteration in range(max_steps):

        # ----------------------------------------------------
        # Execute current step
        # ----------------------------------------------------

        result = execute_investigation_step(
            con=con,
            schema=schema,
            question=question,
            step=current_step,
            previous_evidence=previous_evidence
        )

        investigation_results.append(
            result
        )

        # ----------------------------------------------------
        # If step succeeded, update evidence
        # ----------------------------------------------------

        if result["finding"]:

            previous_evidence += (
                f"\n\n"
                f"Step {result['step']} Finding:\n"
                f"{result['finding']}"
            )

        # ----------------------------------------------------
        # Decide whether to continue
        # ----------------------------------------------------

        try:

            decision = decide_next_investigation(
                question=question,
                data_profile=data_profile,
                investigation_history=(
                    investigation_results
                )
            )

        except Exception:

            break

        # ----------------------------------------------------
        # Stop investigation
        # ----------------------------------------------------

        if not decision.continue_investigation:

            break

        # ----------------------------------------------------
        # Create next investigation step
        # ----------------------------------------------------

        from agents.planner import InvestigationStep

        current_step = InvestigationStep(
            step=len(
                investigation_results
            ) + 1,
            analysis=decision.next_analysis,
            reason=decision.reason
        )

    return investigation_results