from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        inv_count = connection.execute(sqlalchemy.text("SELECT num_green_potions from global_inventory")).scalar_one()

    return [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": inv_count,
                "price": 60,
                "potion_type": [0, 100, 0, 0],
            }
        ]
