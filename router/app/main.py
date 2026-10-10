from fastapi import FastAPI

from app.config import NODES
from app.services.health_checker import check_node
from app.routers.clients import router as clients_router
from app.routers.products import router as products_router
from app.routers.orders import router as orders_router
from app.services.shard_manager import (
    get_node_by_region,
    get_node_by_product_id
)

app = FastAPI(
    title="GlobalShop Distributed Database Router",
    version="1.0.0"
)

app.include_router(clients_router)
app.include_router(products_router)
app.include_router(orders_router)

@app.get("/")
def root():
    return {
        "application": "GlobalShop",
        "status": "running"
    }



@app.get("/health")
def health():
    nodes = {
        node_name: check_node(node_name)
        for node_name in NODES
    }

    return {
        "status": (
            "UP"
            if all(node["status"] == "UP" for node in nodes.values())
            else "DEGRADED"
        ),
        "nodes": nodes,
    }



@app.get("/shard/client/{region}")
def client_shard(region: str):
    node = get_node_by_region(region)

    return {
        "region": region.upper(),
        "node": node
    }


@app.get("/shard/product/{product_id}")
def product_shard(product_id: int):
    node = get_node_by_product_id(product_id)

    return {
        "product_id": product_id,
        "node": node
    }