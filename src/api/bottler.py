from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            match potion.potion_type:
                case [0, 100, 0, 0]:
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = {}".format(potion.quantity)))
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = (SELECT num_green_ml from global_inventory) - {}".format(potion.quantity * potion.potion_type[1])))
                case [100, 0, 0, 0]:
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = {}".format(potion.quantity)))
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = (SELECT num_red_ml from global_inventory) - {}".format(potion.quantity * potion.potion_type[0])))            
                case [0, 0, 100, 0]:
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = {}".format(potion.quantity)))
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = (SELECT num_blue_ml from global_inventory) - {}".format(potion.quantity * potion.potion_type[2])))     
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        grn_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml from global_inventory")).scalar_one()
        grn_bottle_ct = grn_ml//100
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml from global_inventory")).scalar_one()
        red_bottle_ct = red_ml//100
        blu_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml from global_inventory")).scalar_one()
        blu_bottle_ct = blu_ml//100                                           

    json_str = []
    if grn_bottle_ct != 0:
        json_str.append({"potion_type": [0, 100, 0, 0],"quantity": grn_bottle_ct,})
    if red_bottle_ct != 0:
        json_str.append({"potion_type": [100, 0, 0, 0],"quantity": red_bottle_ct,})
    if blu_bottle_ct != 0:
        json_str.append({"potion_type": [0, 0, 100, 0],"quantity": blu_bottle_ct,})
                
    return json_str

if __name__ == "__main__":
    print(get_bottle_plan())