REGION_TO_NODE = {
    "AFRICA": "node1",
    "EUROPE": "node2",
    "AMERICA": "node3",
    "ASIA": "node4",
}


def get_node_by_region(region: str) -> str:
    region = region.upper()

    if region not in REGION_TO_NODE:
        raise ValueError(f"Région inconnue : {region}")

    return REGION_TO_NODE[region]


def get_node_by_product_id(product_id: int) -> str:
    node_number = ((product_id - 1) % 4) + 1

    return f"node{node_number}"