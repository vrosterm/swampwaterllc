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
        grn_count = connection.execute(sqlalchemy.text("SELECT num_green_potions from global_inventory")).scalar_one()
        red_count = connection.execute(sqlalchemy.text("SELECT num_red_potions from global_inventory")).scalar_one()
        blu_count = connection.execute(sqlalchemy.text("SELECT num_blue_potions from global_inventory")).scalar_one()
        json_str = []


    if grn_count != 0:
        json_str.insert({
                    "sku": "GREEN_POTION_0",
                    "name": "green potion",
                    "quantity": grn_count,
                    "price": 40,
                    "potion_type": [0, 100, 0, 0],
                })
    if red_count != 0:
        json_str.insert({
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": red_count,
                    "price": 40,
                    "potion_type": [100, 0, 0, 0],
                }) 
    if blu_count != 0:
        json_str.insert({
                    "sku": "BLUE_POTION_0",
                    "name": "blue potion",
                    "quantity": blu_count,
                    "price": 40,
                    "potion_type": [0, 0, 100, 0],
                })    
    return json_str
