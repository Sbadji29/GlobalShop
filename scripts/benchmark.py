
import json
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "http://127.0.0.1:8000/orders/"
CLIENT_ID = 1
CLIENT_REGION = "AFRICA"
PRODUCT_ID = 10
QUANTITY = 1
TOTAL_REQUESTS = 100
MAX_WORKERS = 100


def purchase(request_number):
    payload = {
        "client_id": CLIENT_ID,
        "client_region": CLIENT_REGION,
        "items": [
            {
                "product_id": PRODUCT_ID,
                "quantity": QUANTITY
            }
        ]
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return {
                "request": request_number,
                "status": response.status,
                "body": body
            }

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        return {
            "request": request_number,
            "status": error.code,
            "body": body
        }

    except Exception as error:
        return {
            "request": request_number,
            "status": "TECHNICAL_ERROR",
            "body": str(error)
        }


def main():
    print("=== BENCHMARK GLOBALSHOP ===")
    print(f"Demandes : {TOTAL_REQUESTS}")
    print(f"Workers simultanés : {MAX_WORKERS}")
    print(f"Produit : {PRODUCT_ID}")
    print("Démarrage du test...\n")

    start = time.perf_counter()
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(purchase, i + 1)
            for i in range(TOTAL_REQUESTS)
        ]

        for future in as_completed(futures):
            results.append(future.result())

    elapsed = time.perf_counter() - start

    success = sum(r["status"] == 200 for r in results)
    insufficient_stock = sum(r["status"] == 409 for r in results)
    not_found = sum(r["status"] == 404 for r in results)
    technical_http_errors = sum(
        isinstance(r["status"], int)
        and r["status"] >= 500
        for r in results
    )
    client_errors = sum(
        isinstance(r["status"], int)
        and 400 <= r["status"] < 500
        and r["status"] != 409
        and r["status"] != 404
        for r in results
    )
    network_errors = sum(
        r["status"] == "TECHNICAL_ERROR"
        for r in results
    )

    print("=== RÉSULTATS ===")
    print(f"Demandes envoyées       : {len(results)}")
    print(f"Achats réussis (200)    : {success}")
    print(f"Stock insuffisant (409) : {insufficient_stock}")
    print(f"Produit/client absent   : {not_found}")
    print(f"Autres erreurs HTTP 4xx : {client_errors}")
    print(f"Erreurs serveur 5xx     : {technical_http_errors}")
    print(f"Erreurs réseau          : {network_errors}")
    print(f"Durée totale            : {elapsed:.2f} secondes")
    print(f"Débit moyen             : {len(results) / elapsed:.2f} req/s")

    print("\n=== PREMIÈRES ERREURS ===")
    errors = [r for r in results if r["status"] != 200]
    for result in errors[:5]:
        print(
            f"Requête {result['request']} | "
            f"HTTP {result['status']} | {result['body'][:250]}"
        )

    print("\nVérifie maintenant le stock dans DBeaver.")


if __name__ == "__main__":
    main()
