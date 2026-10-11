from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.database.connections import get_connection
from app.services.shard_manager import get_node_by_region


router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    region: str


@router.post("/")
def create_client(client: ClientCreate):

    try:
        node_name = get_node_by_region(client.region)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    connection = None

    try:
        connection = get_connection(node_name)

        cursor = connection.cursor()

        query = """
            INSERT INTO clients
                (name, email, phone, region)
            VALUES
                (%s, %s, %s, %s)
            RETURNING id, name, email, phone, region, created_at;
        """

        cursor.execute(
            query,
            (
                client.name,
                client.email,
                client.phone,
                client.region.upper()
            )
        )

        created_client = cursor.fetchone()

        connection.commit()

        cursor.close()

        return {
            "message": "Client créé avec succès",
            "node": node_name,
            "client": {
                "id": created_client[0],
                "name": created_client[1],
                "email": created_client[2],
                "phone": created_client[3],
                "region": created_client[4],
                "created_at": created_client[5]
            }
        }

    except Exception as e:

        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création du client : {str(e)}"
        )

    finally:

        if connection:
            connection.close()