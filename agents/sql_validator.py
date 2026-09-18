# ============================================================
# READ-ONLY SQL VALIDATOR
# ============================================================

def validate_sql(con, sql):
    """
    Validate SQL before execution.

    Allows advanced analytical SQL such as:
    - SELECT
    - CTEs
    - Window functions
    - Subqueries
    - JOINs
    - UNION
    - CASE
    - Aggregations

    Blocks SQL that modifies the dataset/database.
    """

    if not sql:
        return False, "SQL query is empty."

    sql = sql.strip()

    # --------------------------------------------------------
    # Remove one trailing semicolon
    # --------------------------------------------------------

    if sql.endswith(";"):
        sql = sql[:-1].strip()

    if not sql:
        return False, "SQL query is empty."

    sql_lower = sql.lower()

    # --------------------------------------------------------
    # Prevent multiple SQL statements
    # --------------------------------------------------------

    if ";" in sql:
        return (
            False,
            "Multiple SQL statements are not allowed."
        )

    # --------------------------------------------------------
    # Block database/data modification operations
    # --------------------------------------------------------

    forbidden_keywords = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "truncate ",
        "create ",
        "replace ",
        "merge ",
        "copy ",
        "attach ",
        "detach ",
        "grant ",
        "revoke "
    ]

    for keyword in forbidden_keywords:

        if keyword in sql_lower:

            return (
                False,
                f"Read-only analysis only. "
                f"'{keyword.strip().upper()}' "
                f"operations are not allowed."
            )

    # --------------------------------------------------------
    # Analytical query must begin with SELECT or WITH
    # --------------------------------------------------------

    if not (
        sql_lower.startswith("select")
        or sql_lower.startswith("with")
    ):

        return (
            False,
            "Only read-only analytical SQL is allowed."
        )

    # --------------------------------------------------------
    # Ask DuckDB to validate the actual query
    # --------------------------------------------------------

    try:

        con.execute(
            f"EXPLAIN {sql}"
        )

        return True, None

    except Exception as e:

        return False, str(e)