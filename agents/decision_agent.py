import os
import json

from google import genai
from dotenv import load_dotenv

from pydantic import BaseModel


# ============================================================
# ENVIRONMENT
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
# RESPONSE MODEL
# ============================================================

class NextInvestigation(BaseModel):

    continue_investigation: bool

    next_analysis: str | None

    reason: str


# ============================================================
# DECIDE NEXT INVESTIGATION
# ============================================================

def decide_next_investigation(
    question,
    data_profile,
    investigation_history
):
    """
    Decide whether the autonomous investigation
    should continue and what should be investigated next.

    The decision is based on ACTUAL evidence gathered
    so far.
    """

    profile_text = json.dumps(
        data_profile,
        indent=2,
        default=str
    )

    history_text = ""

    for item in investigation_history:

        result = item.get(
            "result"
        )

        if result is not None:

            if hasattr(result, "to_string"):

                result_text = (
                    result
                    .head(20)
                    .to_string(index=False)
                )

            else:

                result_text = str(result)

        else:

            result_text = "No result."

        history_text += f"""
============================================================
STEP {item.get('step')}
============================================================

Analysis:
{item.get('analysis')}

SQL:
{item.get('sql')}

Actual Result:
{result_text}

Finding:
{item.get('finding')}

"""


    prompt = f"""
You are the decision-making component of an
autonomous data analyst.

Your job is to decide whether the investigation
should continue and, if so, determine the most
useful NEXT investigation based on the evidence
already collected.

============================================================
BUSINESS QUESTION
============================================================

{question}

============================================================
DATA PROFILE
============================================================

{profile_text}

============================================================
INVESTIGATION HISTORY
============================================================

{history_text}

============================================================
YOUR OBJECTIVE
============================================================

Think like a senior data analyst.

Do NOT simply follow a predetermined investigation plan.

Instead:

1. Examine the actual results.

2. Identify what has already been established.

3. Identify important unanswered questions.

4. Determine which finding appears most relevant
   to answering the original business question.

5. Choose the next analysis that would provide
   the greatest additional evidence.

6. Avoid repeating analyses that have already
   been performed.

7. Stop when the available evidence is sufficient
   to answer the business question.

============================================================
EXAMPLES
============================================================

If the investigation shows:

"Profit declined sharply beginning in April."

A useful next investigation might be:

"Compare revenue, cost and discount trends before
and after April."

If that shows:

"Discount rates increased significantly."

A useful next investigation might be:

"Determine which products and regions experienced
the largest margin deterioration associated with
the higher discounts."

If the evidence already clearly explains the issue,
stop the investigation.

============================================================
IMPORTANT RULES
============================================================

1. Base the decision ONLY on available evidence.

2. Do not invent data.

3. Do not invent columns.

4. Do not repeat completed analyses.

5. The next analysis must be executable using
   the available dataset.

6. Prefer focused investigations over generic analysis.

7. Do not recommend business actions yet.

8. Do not claim causation without evidence.

9. Stop if additional investigation is unlikely
   to materially improve the answer.

============================================================
OUTPUT
============================================================

Return:

- continue_investigation
- next_analysis
- reason

If investigation should stop:

continue_investigation = false

next_analysis = null

reason = explain why the evidence is sufficient.
"""

    response = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": NextInvestigation.model_json_schema()
        },
        store=False
    )

    return NextInvestigation.model_validate_json(
        response.output_text
    )