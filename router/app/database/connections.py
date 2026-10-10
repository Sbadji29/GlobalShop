
import psycopg2
from app.config import NODES


def get_connection(node_name: str):
    if node_name not in NODES:
        raise ValueError(f"Node inconnu : {node_name}")

    config = NODES[node_name]

    return psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["user"],
        password=config["password"],
        connect_timeout=3,
    )


def get_node_role(node_name: str) -> dict:
    """
    Vérifie la disponibilité du serveur et son rôle PostgreSQL.
    pg_is_in_recovery() = True : réplique en lecture seule.
    pg_is_in_recovery() = False : serveur principal.
    """
    connection = None

    try:
        connection = get_connection(node_name)

        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_is_in_recovery();")
            in_recovery = cursor.fetchone()[0]

        return {
            "node": node_name,
            "status": "UP",
            "role": "REPLICA" if in_recovery else "PRIMARY",
            "read_only": in_recovery,
        }

    except Exception as exc:
        return {
            "node": node_name,
            "status": "DOWN",
            "role": "UNKNOWN",
            "read_only": None,
            "error": str(exc),
        }

    finally:
        if connection is not None:
            connection.close()
