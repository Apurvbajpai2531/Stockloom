from .database import execute_query


def get_database_schema():
    query = """
    SELECT
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """

    rows = execute_query(query)

    schema = {}

    for row in rows:
        table = row["table_name"]

        if table not in schema:
            schema[table] = []

        schema[table].append(
            {
                "column": row["column_name"],
                "type": row["data_type"],
            }
        )

    return schema