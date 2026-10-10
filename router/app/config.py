import os

NODES = {
    
    "node1": {
        "host": os.getenv("NODE1_HOST", "localhost"),
        "port": int(os.getenv("NODE1_PORT", 5437)),
        "database": os.getenv("NODE1_DB", "globalshop"),
        "user": os.getenv("NODE1_USER", "globalshop"),
        "password": os.getenv("NODE1_PASSWORD", "globalshop123"),
        "region": "AFRICA",
    },

    "node2": {
        "host": os.getenv("NODE2_HOST", "localhost"),
        "port": int(os.getenv("NODE2_PORT", 5434)),
        "database": os.getenv("NODE2_DB", "globalshop"),
        "user": os.getenv("NODE2_USER", "globalshop"),
        "password": os.getenv("NODE2_PASSWORD", "globalshop123"),
        "region": "EUROPE",
    },

    "node3": {
        "host": os.getenv("NODE3_HOST", "localhost"),
        "port": int(os.getenv("NODE3_PORT", 5435)),
        "database": os.getenv("NODE3_DB", "globalshop"),
        "user": os.getenv("NODE3_USER", "globalshop"),
        "password": os.getenv("NODE3_PASSWORD", "globalshop123"),
        "region": "AMERICA",
    },

    "node4": {
        "host": os.getenv("NODE4_HOST", "localhost"),
        "port": int(os.getenv("NODE4_PORT", 5436)),
        "database": os.getenv("NODE4_DB", "globalshop"),
        "user": os.getenv("NODE4_USER", "globalshop"),
        "password": os.getenv("NODE4_PASSWORD", "globalshop123"),
        "region": "ASIA",
    },
}