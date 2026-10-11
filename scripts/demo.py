
import json
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"


def get_json(path):
    """Effectue une requête GET et retourne le code HTTP et le JSON."""
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Accept": "application/json"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {"detail": body}
        return error.code, data

    except Exception as error:
        return None, {"detail": str(error)}


def show_result(label, status, data):
    if status is None:
        print(f"[ERREUR] {label} : {data.get('detail')}")
        return False

    print(f"[HTTP {status}] {label}")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 200 <= status < 300


def main():
    print("=" * 55)
    print("       DEMONSTRATION AUTOMATISEE GLOBALSHOP")
    print(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("=" * 55)

    checks = []

    # 1. Vérifier que l'API répond
    status, data = get_json("/")
    checks.append(show_result("Accueil API", status, data))

    # 2. Vérifier la santé des nœuds configurés
    status, data = get_json("/health")
    checks.append(show_result("Santé des nœuds", status, data))

    if status == 200 and isinstance(data, dict):
        print("\nRésumé des nœuds :")
        nodes = data.get("nodes", {})

        for name, node in nodes.items():
            print(
                f" - {name}: statut={node.get('status')}, "
                f"rôle={node.get('role')}, "
                f"lecture_seule={node.get('read_only')}"
            )

    # 3. Vérifier des produits sur plusieurs nœuds
    for product_id in (1, 10, 11):
        status, data = get_json(f"/products/{product_id}")
        ok = show_result(f"Lecture produit {product_id}", status, data)
        checks.append(ok)

        if status == 200 and isinstance(data, dict):
            product = data.get("product", {})
            print(
                f"   Produit : {product.get('name')} | "
                f"Nœud : {data.get('node')} | "
                f"Stock : {product.get('stock')}"
            )

    print("\n" + "=" * 55)
    print(f"Vérifications réussies : {sum(checks)}/{len(checks)}")
    print("Aucune commande ni modification de données effectuée.")
    print("=" * 55)


if __name__ == "__main__":
    main()
