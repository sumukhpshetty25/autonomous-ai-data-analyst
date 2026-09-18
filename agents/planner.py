import os
import json

from google import genai
from dotenv import load_dotenv

from pydantic import BaseModel

from typing import List


load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. "
        "Please add GEMINI_API_KEY to your .env file."
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


class InvestigationStep(BaseModel):

    step: int

    analysis: str

    reason: str


class InvestigationPlan(BaseModel):

    objective: str

    steps: List[InvestigationStep]


def create_plan(
    schema,
    question,
    data_profile=None
):

    if data_profile is None:
        data_profile = {}

    profile_text = json.dumps(
        data_profile,
        indent=2,
        default=str
    )

    prompt = f"""
You are an expert autonomous data analyst.

Your job is to create a step-by-step investigation
plan for a business question.

============================================================
BUSINESS QUESTION
============================================================

{question}

============================================================
DATASET SCHEMA
============================================================

{schema}

============================================================
DATA QUALITY AND DATA PROFILE
============================================================

{profile_text}

This profile describes the PREPROCESSED dataset.

Use this information when designing the investigation.

============================================================
INVESTIGATION PRINCIPLES
============================================================

The investigation should progressively move from:

1. Overall business outcome
2. Trends and changes
3. Driver decomposition
4. Segment-level analysis
5. Deeper drill-down
6. Anomalies or unusual behavior
7. Root-cause evidence

Only include analyses that are relevant to
the business question and supported by the dataset.

============================================================
DATA QUALITY HANDLING
============================================================

Missing values:

Do NOT assume missing values mean zero.

Do NOT automatically remove records.

If missing values are relevant to the question,
investigate their impact.

Outliers:

Do NOT automatically remove outliers.

If potential outliers are relevant,
investigate them as possible signals.

Duplicates:

The dataset has already had exact duplicate rows
removed during preprocessing.

============================================================
ADVANCED SQL
============================================================

The SQL agent can use:

- CTEs
- Multiple CTEs
- Window functions
- LAG
- LEAD
- RANK
- DENSE_RANK
- ROW_NUMBER
- PARTITION BY
- Subqueries
- Nested queries
- CASE WHEN
- JOINs
- UNION
- HAVING
- Date functions
- Running totals
- Moving averages
- Period-over-period analysis

Design investigation steps that can benefit
from these techniques when appropriate.

============================================================
IMPORTANT RULES
============================================================

1. Do NOT invent columns.

2. Do NOT assume columns that do not exist.

3. Every step must be executable using the dataset.

4. Avoid repeating the same analysis.

5. Use the data profile to identify useful
   investigation directions.

6. Prefer approximately 4–7 meaningful steps.

7. Each step should have a clear analytical purpose.

8. Later steps should ideally drill deeper into
   findings discovered earlier.

============================================================
OUTPUT
============================================================

Return the investigation plan in the required
structured JSON format.
"""

    response = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": InvestigationPlan.model_json_schema()
        },
        store=False
    )

    return InvestigationPlan.model_validate_json(
        response.output_text
    )