from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.connections import get_connection
from app.services.shard_manager import get_node_by_product_id


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None
    price: float
    quantity: int


@router.post("/")
def create_product(product: ProductCreate):

    if product.price < 0:
        raise HTTPException(
            status_code=400,
            detail="Le prix ne peut pas être négatif"
        )

    if product.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Le stock ne peut pas être négatif"
        )

    connection = None

    try:
        # Pour obtenir un nouvel ID et connaître son Node,
        # nous allons d'abord générer l'ID.
        #
        # Pour cette première version, on utilise une génération
        # coordonnée par le Router.

        node_name = None

        # Trouver le prochain ID disponible globalement
        max_id = 0

        for candidate_node in ["node1", "node2", "node3", "node4"]:

            conn = get_connection(candidate_node)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COALESCE(MAX(id), 0) FROM products;"
            )

            current_max = cursor.fetchone()[0]

            max_id = max(max_id, current_max)

            cursor.close()
            conn.close()

        product_id = max_id + 1

        node_name = get_node_by_product_id(product_id)

        connection = get_connection(node_name)

        cursor = connection.cursor()

        # Création du produit
        cursor.execute(
            """
            INSERT INTO products
                (id, name, description, category, price)
            VALUES
                (%s, %s, %s, %s, %s)
            RETURNING id, name, description, category, price, created_at;
            """,
            (
                product_id,
                product.name,
                product.description,
                product.category,
                product.price
            )
        )

        created_product = cursor.fetchone()

        # Création du stock sur LE MÊME NODE
        cursor.execute(
            """
            INSERT INTO stock
                (product_id, quantity)
            VALUES
                (%s, %s)
            RETURNING product_id, quantity, updated_at;
            """,
            (
                product_id,
                product.quantity
            )
        )

        created_stock = cursor.fetchone()

        connection.commit()

        cursor.close()

        return {
            "message": "Produit créé avec succès",
            "node": node_name,
            "product": {
                "id": created_product[0],
                "name": created_product[1],
                "description": created_product[2],
                "category": created_product[3],
                "price": float(created_product[4]),
                "created_at": created_product[5]
            },
            "stock": {
                "product_id": created_stock[0],
                "quantity": created_stock[1],
                "updated_at": created_stock[2]
            }
        }

    except Exception as e:

        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création du produit : {str(e)}"
        )

    finally:

        if connection:
            connection.close()


@router.get("/{product_id}")
def get_product(product_id: int):

    node_name = get_node_by_product_id(product_id)

    connection = None

    try:
        connection = get_connection(node_name)
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                p.id,
                p.name,
                p.description,
                p.category,
                p.price,
                p.created_at,
                s.quantity,
                s.updated_at
            FROM products p
            JOIN stock s
                ON p.id = s.product_id
            WHERE p.id = %s;
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        cursor.close()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Produit {product_id} introuvable"
            )

        return {
            "node": node_name,
            "product": {
                "id": product[0],
                "name": product[1],
                "description": product[2],
                "category": product[3],
                "price": float(product[4]),
                "created_at": product[5],
                "stock": product[6],
                "stock_updated_at": product[7]
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération : {str(e)}"
        )

    finally:
        if connection:
            connection.close()