import os

from google import genai
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. "
        "Please add GEMINI_API_KEY to your .env file."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# SQL CLEANING
# ============================================================

def clean_sql(sql):
    """
    Clean Gemini's SQL response.

    Removes Markdown code fences if Gemini returns them.
    """

    if not sql:
        return ""

    sql = sql.strip()

    # Remove ```sql
    if sql.startswith("```sql"):
        sql = sql[len("```sql"):]

    # Remove ```SQL
    elif sql.startswith("```SQL"):
        sql = sql[len("```SQL"):]

    # Remove generic ```
    elif sql.startswith("```"):
        sql = sql[len("```"):]

    # Remove ending ```
    if sql.endswith("```"):
        sql = sql[:-3]

    return sql.strip()


# ============================================================
# GENERATE SQL
# ============================================================

def generate_sql(
    schema,
    analysis_step,
    question=None,
    previous_evidence=""
):
    """
    Generate a read-only analytical SQL query.

    Gemini is allowed to use advanced SQL techniques such as:
    - CTEs
    - Multiple CTEs
    - Window functions
    - Subqueries
    - Nested queries
    - CASE WHEN
    - JOINs
    - UNION
    - HAVING
    - Date functions
    - Ranking
    - Rolling calculations
    - Period-over-period analysis

    The dataset itself must never be modified.
    """

    if question is None:
        question = "Not provided."

    if not previous_evidence:
        previous_evidence = "No previous evidence is available."

    prompt = f"""
You are an expert Data Analyst and DuckDB SQL Engineer.

Your task is to generate ONE SQL query that performs
the requested investigation step.

The dataset is already preprocessed and registered
in DuckDB as the table:

sales

============================================================
ORIGINAL BUSINESS QUESTION
============================================================

{question}

============================================================
DATASET SCHEMA
============================================================

{schema}

============================================================
CURRENT INVESTIGATION STEP
============================================================

Analysis:
{analysis_step}

============================================================
PREVIOUS INVESTIGATION EVIDENCE
============================================================

{previous_evidence}

Use previous evidence when it is relevant.

For example:

- If an earlier step identified a declining month,
  investigate that period in the current step.

- If an earlier step identified a weak region,
  drill into that region.

- If an earlier step identified a product problem,
  investigate that product further.

Do not blindly repeat previous analyses.

============================================================
SQL CAPABILITIES
============================================================

You are encouraged to use advanced analytical SQL
whenever it improves the investigation.

You may use:

- CTEs
- Multiple CTEs
- Recursive CTEs when genuinely useful
- Window functions
- LAG()
- LEAD()
- RANK()
- DENSE_RANK()
- ROW_NUMBER()
- NTILE()
- PARTITION BY
- ORDER BY
- Subqueries
- Nested subqueries
- Correlated subqueries
- CASE WHEN
- COALESCE
- NULLIF
- Conditional aggregation
- GROUP BY
- HAVING
- JOIN
- LEFT JOIN
- RIGHT JOIN
- FULL JOIN
- UNION
- UNION ALL
- INTERSECT
- EXCEPT
- Date functions
- DATE_TRUNC
- Date differences
- Running totals
- Moving averages
- Percentage changes
- Period-over-period comparisons
- Ranking
- Percentiles
- Aggregations

Do NOT avoid advanced SQL just to make the query simple.

Choose the SQL structure that provides the strongest
analytical answer to the investigation step.

============================================================
READ-ONLY REQUIREMENT
============================================================

CRITICAL:

The uploaded dataset must NEVER be modified.

The query must only READ data.

DO NOT use:

INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
CREATE
REPLACE
MERGE
COPY
ATTACH
DETACH
GRANT
REVOKE

Do not create permanent tables.

Do not create temporary tables.

Do not modify the `sales` table.

Do not modify any database object.

============================================================
DATA INTEGRITY
============================================================

The dataset has already gone through preprocessing.

Do not perform destructive preprocessing inside SQL.

Do not delete rows.

Do not update values.

Do not overwrite columns.

Do not modify the dataset.

If missing values, outliers, or unusual values are relevant,
analyze them rather than deleting them.

============================================================
COLUMN RULES
============================================================

1. Use ONLY columns that exist in the schema.

2. Never invent column names.

3. The table name is exactly:

   sales

4. If a date column exists, use DuckDB-compatible
   date functions.

5. If a date column is stored as VARCHAR,
   cast it appropriately before using date functions.

6. Use meaningful column aliases.

7. Return only the columns necessary for the analysis.

8. Avoid SELECT * unless it is genuinely useful.

============================================================
ANALYTICAL QUALITY
============================================================

The SQL must directly answer the investigation step.

Prefer analytical queries that reveal:

- trends
- changes
- drivers
- comparisons
- rankings
- contribution
- anomalies
- relationships
- segments
- period-over-period changes

When comparing periods, calculate useful metrics such as:

- absolute change
- percentage change
- contribution
- growth rate
- rank
- share of total

when appropriate.

Do not invent business logic that cannot be supported
by the available columns.

============================================================
OUTPUT
============================================================

Return ONLY the executable SQL query.

Do not return:

- Markdown
- ```sql
- explanations
- comments
- analysis
- bullet points

Return ONLY SQL.
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        store=False
    )

    sql = interaction.output_text

    sql = clean_sql(sql)

    if not sql:
        raise ValueError(
            "Gemini returned an empty SQL query."
        )

    return sql


# ============================================================
# CORRECT SQL
# ============================================================

def correct_sql(
    schema,
    original_sql,
    error_message,
    analysis_step,
    question=None,
    previous_evidence=""
):
    """
    Ask Gemini to correct a failed SQL query.

    The corrected query must remain read-only and may use
    advanced SQL techniques.
    """

    if question is None:
        question = "Not provided."

    if not previous_evidence:
        previous_evidence = "No previous evidence is available."

    prompt = f"""
You are an expert DuckDB SQL Engineer and Data Analyst.

A SQL query generated for an analytical investigation
failed to execute or failed validation.

Your task is to correct the query.

============================================================
ORIGINAL BUSINESS QUESTION
============================================================

{question}

============================================================
DATASET SCHEMA
============================================================

{schema}

============================================================
CURRENT INVESTIGATION STEP
============================================================

{analysis_step}

============================================================
PREVIOUS INVESTIGATION EVIDENCE
============================================================

{previous_evidence}

============================================================
ORIGINAL SQL
============================================================

{original_sql}

============================================================
DUCKDB / VALIDATION ERROR
============================================================

{error_message}

============================================================
YOUR TASK
============================================================

Fix the SQL query so that it correctly performs
the requested investigation.

Do not simply remove analytical logic to make the query
simpler.

Use advanced SQL whenever appropriate, including:

- CTEs
- Multiple CTEs
- Recursive CTEs when appropriate
- Window functions
- LAG()
- LEAD()
- RANK()
- DENSE_RANK()
- ROW_NUMBER()
- PARTITION BY
- Subqueries
- Nested queries
- Correlated subqueries
- CASE WHEN
- Conditional aggregation
- GROUP BY
- HAVING
- JOINs
- UNION / UNION ALL
- INTERSECT
- EXCEPT
- Date functions
- Running totals
- Moving averages
- Percentage changes
- Period-over-period analysis

============================================================
READ-ONLY REQUIREMENT
============================================================

The uploaded dataset must NEVER be modified.

The corrected query must only READ data.

DO NOT use:

INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
CREATE
REPLACE
MERGE
COPY
ATTACH
DETACH
GRANT
REVOKE

Do not create permanent or temporary tables.

Do not modify the `sales` table.

============================================================
COLUMN RULES
============================================================

1. Use ONLY columns present in the schema.

2. Do not invent columns.

3. The table name is exactly:

   sales

4. Use valid DuckDB SQL.

5. Preserve the analytical objective.

6. Fix the specific error reported by DuckDB.

============================================================
OUTPUT
============================================================

Return ONLY the corrected executable SQL query.

Do not return:

- Markdown
- ```sql
- explanations
- comments
- bullet points

Return ONLY SQL.
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        store=False
    )

    sql = interaction.output_text

    sql = clean_sql(sql)

    if not sql:
        raise ValueError(
            "Gemini returned an empty corrected SQL query."
        )

    return sql