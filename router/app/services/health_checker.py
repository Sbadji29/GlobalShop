
from app.database.connections import get_node_role


def check_node(node_name: str) -> dict:
    return get_node_role(node_name)
