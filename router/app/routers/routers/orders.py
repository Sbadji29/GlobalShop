from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.connections import get_connection
from app.services.shard_manager import (
    get_node_by_region,
    get_node_by_product_id
)


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    client_id: int
    client_region: str
    items: list[OrderItemCreate]


def verify_client(client_id: int, client_region: str):

    node_name = get_node_by_region(client_region)

    connection = None

    try:
        connection = get_connection(node_name)
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, name, email, region
            FROM clients
            WHERE id = %s;
            """,
            (client_id,)
        )

        client = cursor.fetchone()

        cursor.close()

        if not client:
            raise HTTPException(
                status_code=404,
                detail=f"Client {client_id} introuvable sur {node_name}"
            )

        return {
            "node": node_name,
            "id": client[0],
            "name": client[1],
            "email": client[2],
            "region": client[3]
        }

    finally:
        if connection:
            connection.close()


def reserve_stock(product_id: int, quantity: int):

    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="La quantité doit être supérieure à 0"
        )

    node_name = get_node_by_product_id(product_id)

    connection = None

    try:
        connection = get_connection(node_name)

        # Début de transaction PostgreSQL
        connection.autocommit = False

        cursor = connection.cursor()

        # Verrouillage de la ligne stock
        cursor.execute(
            """
            SELECT
                s.quantity,
                p.name,
                p.price
            FROM stock s
            JOIN products p
                ON p.id = s.product_id
            WHERE s.product_id = %s
            FOR UPDATE;
            """,
            (product_id,)
        )

        stock = cursor.fetchone()

        if not stock:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail=f"Produit {product_id} introuvable"
            )

        current_quantity = stock[0]
        product_name = stock[1]
        product_price = stock[2]

        # Vérification du stock
        if current_quantity < quantity:

            connection.rollback()

            raise HTTPException(
                status_code=409,
                detail=(
                    f"Stock insuffisant pour {product_name}. "
                    f"Disponible : {current_quantity}, "
                    f"demandé : {quantity}"
                )
            )

        # Réservation
        new_quantity = current_quantity - quantity

        cursor.execute(
            """
            UPDATE stock
            SET
                quantity = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE product_id = %s;
            """,
            (
                new_quantity,
                product_id
            )
        )

        connection.commit()

        cursor.close()

        return {
            "node": node_name,
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "unit_price": float(product_price),
            "remaining_stock": new_quantity
        }

    except HTTPException:
        raise

    except Exception as e:

        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la réservation du stock : {str(e)}"
        )

    finally:

        if connection:
            connection.close()

def release_stock(product_id: int, quantity: int):

    node_name = get_node_by_product_id(product_id)

    connection = None

    try:
        connection = get_connection(node_name)
        connection.autocommit = False

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT quantity
            FROM stock
            WHERE product_id = %s
            FOR UPDATE;
            """,
            (product_id,)
        )

        stock = cursor.fetchone()

        if not stock:
            connection.rollback()
            raise Exception(
                f"Stock introuvable pour le produit {product_id}"
            )

        new_quantity = stock[0] + quantity

        cursor.execute(
            """
            UPDATE stock
            SET
                quantity = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE product_id = %s;
            """,
            (
                new_quantity,
                product_id
            )
        )

        connection.commit()

        cursor.close()

        return {
            "node": node_name,
            "product_id": product_id,
            "released_quantity": quantity,
            "new_stock": new_quantity
        }

    except Exception:

        if connection:
            connection.rollback()

        raise

    finally:

        if connection:
            connection.close()


@router.post("/")
def create_order(order: OrderCreate):

    # ==========================================
    # 1. VALIDATION DE LA REQUÊTE
    # ==========================================

    if not order.items:
        raise HTTPException(
            status_code=400,
            detail="La commande doit contenir au moins un produit"
        )

    # Pour cette première version :
    # une seule ligne produit par commande.
    if len(order.items) != 1:
        raise HTTPException(
            status_code=400,
            detail="Cette première version accepte un seul produit par commande"
        )

    item = order.items[0]

    if item.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="La quantité doit être supérieure à 0"
        )

    # ==========================================
    # 2. VÉRIFIER LE CLIENT
    # ==========================================

    client = verify_client(
        order.client_id,
        order.client_region
    )

    client_node = client["node"]

    # ==========================================
    # 3. RÉSERVER LE STOCK
    # ==========================================

    reservation = None

    try:

        reservation = reserve_stock(
            item.product_id,
            item.quantity
        )

        # ==========================================
        # 4. CALCUL DU TOTAL
        # ==========================================

        unit_price = reservation["unit_price"]

        total_amount = unit_price * item.quantity

        # ==========================================
        # 5. CRÉER LA COMMANDE
        # ==========================================

        connection = None

        try:

            connection = get_connection(client_node)

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO orders
                    (client_id, status, total_amount)
                VALUES
                    (%s, %s, %s)
                RETURNING id, status, total_amount, created_at;
                """,
                (
                    order.client_id,
                    "PENDING",
                    total_amount
                )
            )

            created_order = cursor.fetchone()

            order_id = created_order[0]

            # ==========================================
            # 6. CRÉER ORDER_ITEM
            # ==========================================

            cursor.execute(
                """
                INSERT INTO order_items
                    (order_id, product_id, quantity, unit_price)
                VALUES
                    (%s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    order_id,
                    item.product_id,
                    item.quantity,
                    unit_price
                )
            )

            order_item_id = cursor.fetchone()[0]

            # ==========================================
            # 7. CRÉER LA FACTURE
            # ==========================================

            cursor.execute(
                """
                INSERT INTO invoices
                    (order_id, amount, status)
                VALUES
                    (%s, %s, %s)
                RETURNING id;
                """,
                (
                    order_id,
                    total_amount,
                    "PENDING"
                )
            )

            invoice_id = cursor.fetchone()[0]

            # ==========================================
            # 8. CONFIRMER LA COMMANDE
            # ==========================================

            cursor.execute(
                """
                UPDATE orders
                SET status = 'CONFIRMED'
                WHERE id = %s;
                """,
                (order_id,)
            )

            # On valide toutes les opérations
            connection.commit()

            cursor.close()

            return {
                "message": "Commande créée avec succès",
                "status": "CONFIRMED",

                "order": {
                    "id": order_id,
                    "client_id": order.client_id,
                    "total_amount": float(total_amount)
                },

                "item": {
                    "id": order_item_id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": float(unit_price)
                },

                "invoice": {
                    "id": invoice_id,
                    "amount": float(total_amount),
                    "status": "PENDING"
                },

                "nodes": {
                    "client_order": client_node,
                    "product_stock": reservation["node"]
                },

                "stock": {
                    "remaining": reservation["remaining_stock"]
                }
            }

        except Exception as e:

            # ------------------------------------------
            # ÉCHEC DE CRÉATION DE LA COMMANDE
            # ------------------------------------------

            if connection:
                connection.rollback()

            # Compensation :
            # on rend le stock réservé
            release_stock(
                item.product_id,
                item.quantity
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Erreur lors de la création de la commande. "
                    "Le stock a été restauré. "
                    f"Détail : {str(e)}"
                )
            )

        finally:

            if connection:
                connection.close()

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la commande : {str(e)}"
        )