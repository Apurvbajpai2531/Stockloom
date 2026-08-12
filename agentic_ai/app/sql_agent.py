import json
import re

from .database import execute_query
from .ollama_client import ask_ollama
from .schema import get_database_schema


def clean_sql(text: str) -> str:
    text = text.strip()

    text = re.sub(
        r"```sql",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.replace("```", "")

    return text.strip().rstrip(";")


def validate_sql(query: str):
    normalized = query.strip().lower()

    allowed = (
        normalized.startswith("select")
        or normalized.startswith("with")
    )

    if not allowed:
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    forbidden = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "truncate ",
        "create ",
        "grant ",
        "revoke ",
    ]

    for keyword in forbidden:
        if keyword in normalized:
            raise ValueError(
                f"Forbidden SQL operation: {keyword.strip()}"
            )


async def generate_sql(question: str):
    schema = get_database_schema()

    prompt = f"""
You are the SQL agent for StockLoom,
an inventory and warehouse management system.

Database schema:

{json.dumps(schema, indent=2, default=str)}

User question:

{question}

Generate ONE PostgreSQL SELECT query that answers
the user's question.

Rules:

1. Only generate SELECT or WITH queries.
2. Never modify database data.
3. Never use INSERT.
4. Never use UPDATE.
5. Never use DELETE.
6. Never use DROP.
7. Never use ALTER.
8. Never use TRUNCATE.
9. Use only tables and columns from the schema.
10. Return only SQL.
"""

    response = await ask_ollama(prompt)

    sql = clean_sql(response)

    validate_sql(sql)

    return sql


async def answer_question(question: str):
    sql = await generate_sql(question)

    results = execute_query(sql)

    prompt = f"""
You are the StockLoom inventory assistant.

User question:
{question}

SQL used:
{sql}

Database result:
{json.dumps(results, indent=2, default=str)}

Answer the user using ONLY the database result.

Rules:

- Do not invent data.
- If there are no results, clearly say no matching data was found.
- Keep the answer concise.
- Use simple business language.
- Mention important numbers.
"""

    answer = await ask_ollama(prompt)

    return {
        "question": question,
        "sql": sql,
        "data": results,
        "answer": answer.strip(),
    }