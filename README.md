# 🤖 Autonomous AI Data Analyst

An AI-powered data analysis platform that allows users to upload a CSV or Excel dataset, ask business questions in natural language, and receive an autonomous, evidence-based investigation.

Instead of simply generating a SQL query, the system performs a multi-step analytical investigation using **Gemini + DuckDB**, interprets the results, decides what to investigate next, generates visualizations, and produces a final business analyst report.

---

## 🚀 Live Demo

🌐 **Live Application:** Coming Soon

📂 **GitHub Repository:** This repository

---

## 🎯 Project Overview

Traditional data analysis often requires a user to:

1. Understand the dataset
2. Clean the data
3. Write SQL queries
4. Analyze the results
5. Identify follow-up questions
6. Create visualizations
7. Prepare a final report

This project attempts to automate that workflow.

The user only needs to provide:

> **A dataset + a business question**

The AI analyst then determines how to investigate the question and progressively drills into the data.

---

## 🧠 How It Works

```text
                    ┌─────────────────────┐
                    │    Upload Dataset   │
                    │     CSV / Excel     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Data Preprocessing  │
                    │ & Quality Checks    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Data Profile    │
                    │ Schema + Statistics │
                    └──────────┬──────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │       Ask AI            │
                  │ Natural Language Query  │
                  └────────────┬────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Gemini Planner    │
                    │ Initial Direction   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    SQL Generator    │
                    │     Gemini + SQL    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    SQL Validator    │
                    │    Read-Only Check  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       DuckDB        │
                    │   Execute Analysis  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Query Result     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Gemini Analyst    │
                    │    Generate Finding │
                    └──────────┬──────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │    Decision Agent       │
                  │                         │
                  │ Continue? → Next Step  │
                  │ Stop? → Final Report   │
                  └────────────┬────────────┘
                               │
                         ┌─────┴─────┐
                         │           │
                      Continue      Stop
                         │           │
                         ▼           ▼
                    Next Query   Final Report
                         │
                         └───────►
```

---

# ✨ Key Features

## 🧹 Automated Data Quality

Before analysis, the dataset goes through a preprocessing and quality-checking stage.

The system detects:

* Missing values
* Exact duplicate rows
* Completely empty rows
* Date columns
* Numeric columns
* Categorical columns
* Potential statistical outliers
* Category distributions
* Numeric statistics

### Data handling philosophy

The system intentionally avoids destructive preprocessing.

* Missing values are **detected, not automatically filled**
* Potential outliers are **detected, not automatically removed**
* Exact duplicate rows are removed
* Completely empty rows are removed
* Leading/trailing whitespace is removed from text values
* Detected date columns are converted to datetime

This allows the AI analyst to reason about data quality rather than silently changing the analytical dataset.

---

# 🧠 Autonomous AI Investigation

The system uses multiple AI components rather than relying on a single prompt.

### 1. Planner Agent

The Planner receives:

* Business question
* Dataset schema
* Data profile
* Data quality information

It generates an initial analytical direction.

---

### 2. SQL Agent

The SQL Agent converts an investigation step into executable DuckDB SQL.

It can use advanced analytical SQL such as:

* CTEs
* Multiple CTEs
* Recursive CTEs when appropriate
* Window functions
* `LAG()`
* `LEAD()`
* `RANK()`
* `DENSE_RANK()`
* `ROW_NUMBER()`
* `NTILE()`
* `PARTITION BY`
* Subqueries
* Nested queries
* Correlated subqueries
* `CASE WHEN`
* Conditional aggregation
* `JOIN`
* `LEFT JOIN`
* `RIGHT JOIN`
* `FULL JOIN`
* `UNION`
* `UNION ALL`
* `INTERSECT`
* `EXCEPT`
* Date functions
* Running totals
* Moving averages
* Percentage changes
* Period-over-period analysis
* Percentiles

---

### 3. SQL Validator

Generated SQL is validated before execution.

The system blocks data/database modification operations such as:

```text
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
```

The analytical dataset is exposed as:

```sql
sales
```

and the AI is instructed to perform read-only analysis.

---

### 4. Analyst Agent

After SQL execution, the actual query result is passed to Gemini.

The Analyst generates a concise finding based on the observed result.

The system is instructed to:

* Use actual results
* Avoid inventing numbers
* Avoid inventing columns
* Distinguish correlation from causation
* Identify meaningful trends and differences
* Explain the relevance to the original business question

---

### 5. Decision Agent

This is what makes the project adaptive.

After each investigation, the Decision Agent receives the investigation history and determines:

```text
Should the investigation continue?
```

If yes:

```text
What should be investigated next?
```

If no:

```text
Is there enough evidence to answer the question?
```

For example:

```text
Question:
Why did profit decline?

        ↓

Step 1:
Analyze monthly profit

        ↓

Finding:
Profit declined sharply beginning in April.

        ↓

Decision Agent:

Next:
Investigate discount trends by month.

        ↓

Finding:
Discount rates increased significantly.

        ↓

Decision Agent:

Next:
Identify products contributing most
to the margin decline.

        ↓

Finding:
Laptop profitability deteriorated significantly.

        ↓

Decision Agent:

STOP
```

This allows the investigation path to depend on **actual evidence**, rather than blindly executing a fixed list of queries.

---

# 📊 Automated Visualization

After each successful analytical query, Gemini determines whether visualization adds value.

Supported visualizations include:

* Line charts
* Bar charts
* Scatter plots
* Pie charts
* No chart when visualization is unnecessary

Charts are rendered using Plotly.

---

# 💻 SQL Playground

The application also includes a separate SQL Playground.

Users can manually write analytical SQL against:

```sql
sales
```

Example:

```sql
WITH monthly_profit AS (
    SELECT
        DATE_TRUNC('month', order_date) AS month,
        SUM(profit) AS profit
    FROM sales
    GROUP BY 1
)

SELECT
    month,
    profit,
    profit - LAG(profit) OVER (
        ORDER BY month
    ) AS profit_change
FROM monthly_profit
ORDER BY month;
```

The SQL Playground:

* Validates the query
* Executes the query
* Displays the result

It does **not** trigger AI analysis, AI findings, or AI chart selection.

---

# 📄 Final Analyst Report

After the autonomous investigation finishes, Gemini synthesizes the collected evidence into a business-focused report containing:

### Executive Summary

A concise answer to the original question.

### Key Findings

The most important observations discovered during the investigation.

### Root Cause Analysis

Likely drivers supported by the collected evidence.

### Supporting Evidence

Relevant numbers and analytical results.

### Business Recommendations

Practical actions connected to the evidence.

### Limitations

Important limitations or missing information affecting the analysis.

---

# 🏗️ Project Architecture

```text
autonomous-ai-data-analyst/
│
├── app.py
│
├── agents/
│   ├── planner.py
│   ├── sql_agent.py
│   ├── sql_validator.py
│   ├── analyst.py
│   └── decision_agent.py
│
├── utils/
│   └── preprocessing.py
│
├── data/
│   └── sales.csv
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 🛠️ Technology Stack

| Technology    | Purpose                                   |
| ------------- | ----------------------------------------- |
| Python        | Core application                          |
| Streamlit     | Web application                           |
| Gemini        | AI planning, SQL generation and reasoning |
| DuckDB        | Analytical SQL execution                  |
| Pandas        | Data processing                           |
| Plotly        | Data visualization                        |
| Pydantic      | Structured AI responses                   |
| python-dotenv | Environment configuration                 |
| OpenPyXL      | Excel file support                        |

---

# 🔄 End-to-End Workflow

```text
CSV / Excel
     ↓
Preprocessing
     ↓
Data Quality Analysis
     ↓
Data Profiling
     ↓
DuckDB
     ↓
Business Question
     ↓
Gemini Planner
     ↓
Investigation Step
     ↓
Gemini SQL Agent
     ↓
SQL Validator
     ↓
DuckDB Execution
     ↓
Actual Result
     ↓
Gemini Finding
     ↓
Gemini Visualization Selection
     ↓
Decision Agent
     ↓
┌───────────────┐
│ Continue?     │
└───────┬───────┘
        │
   Yes  │  No
        │
        ▼
   Next Step
        │
        └───────────────┐
                        ↓
                  Final Report
```

---

# 🚀 Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/autonomous-ai-data-analyst.git
```

Navigate into the project:

```bash
cd autonomous-ai-data-analyst
```

---

## 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Gemini API

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

**Never commit the `.env` file to GitHub.**

The repository includes `.gitignore` rules to prevent accidental commits.

---

## 5. Run the application

```bash
streamlit run app.py
```

The application will be available locally at:

```text
http://localhost:8501
```

---

# 📁 Dataset Format

The application accepts:

```text
.csv
.xlsx
```

The uploaded dataset can contain arbitrary analytical columns.

For example:

```text
order_id
order_date
customer_id
product
category
region
quantity
unit_price
discount
revenue
cost
profit
```

The AI dynamically receives the dataset schema and profile, so the system is not hard-coded specifically for the sample sales dataset.

---

# 🔐 Data & Security

The application is designed around a read-only analytical workflow.

AI-generated SQL is validated before execution.

The AI is instructed not to modify the dataset or database objects.

API credentials should be stored using environment variables locally and deployment secrets in hosted environments.

For production deployment, additional security controls such as parser-based SQL validation, authentication, query timeouts, resource limits, and stronger sandboxing should be considered.

---

# ⚠️ Current Limitations

This is a portfolio/research project and not intended to replace a production enterprise analytics platform.

Current limitations include:

* SQL validation is keyword-based rather than fully AST/parser-based.
* Very large datasets may require additional optimization.
* AI-generated analysis can occasionally require validation by a human analyst.
* The quality of insights depends on the quality and structure of the uploaded data.
* Visualization selection is currently limited to a small set of chart types.
* Complex causal relationships cannot be established from observational data alone.

---

# 🔮 Future Improvements

Potential future versions could include:

* SQL AST-based security validation
* Query execution timeouts
* Large-dataset sampling and optimization
* Automatic anomaly detection
* Statistical hypothesis testing
* Forecasting
* Correlation analysis
* Feature importance analysis
* More visualization types
* Conversational follow-up questions
* Persistent investigation history
* Exportable PDF/Excel reports
* Authentication and user accounts
* Dataset versioning
* Multi-table relational analysis
* Automatic data dictionary generation
* Agent evaluation and benchmarking
* Cost/token monitoring
* Human-in-the-loop approval for important analyses

---

# 🎓 Why This Project?

The goal of this project is to explore how **AI agents can augment the traditional data analyst workflow**.

Instead of using an LLM only as a chatbot or SQL generator, this system combines:

```text
LLM Reasoning
      +
Data Profiling
      +
SQL Generation
      +
SQL Validation
      +
Analytical Execution
      +
Result Interpretation
      +
Adaptive Decision Making
      +
Visualization
      +
Business Reporting
```

The project demonstrates concepts across:

* Data Analytics
* SQL
* Data Engineering
* Generative AI
* Agentic AI
* Machine Learning Engineering
* Data Visualization
* Business Intelligence

---

# 👨‍💻 Author

**Sumukh P. Shetty**

B.E. Artificial Intelligence & Data Science

---

## ⭐ If you find this project interesting

Consider starring the repository and exploring the architecture.

---

## 📜 License

This project is intended for educational, portfolio, and research purposes.


🌐 Live Application: Coming Soon