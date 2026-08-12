from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)


@contextmanager
def get_connection():
    connection = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )

    try:
        yield connection
    finally:
        connection.close()


def execute_query(query: str):
    with get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)

            if cursor.description is None:
                return []

            return cursor.fetchall()