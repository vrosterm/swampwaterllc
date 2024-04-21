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
    metadata_obj = sqlalchemy.MetaData()
    potion_inventory = sqlalchemy.Table("potion_inventory", metadata_obj, autoload_with= db.engine) 
    material_inventory = sqlalchemy.Table("material_inventory", metadata_obj, autoload_with= db.engine) 
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            connection.execute(sqlalchemy.update(potion_inventory).where(
                potion_inventory.c.red == potion.potion_type[0] and 
                potion_inventory.c.green == potion.potion_type[1] and 
                potion_inventory.c.blue == potion.potion_type[2] and 
                potion_inventory.c.dark == potion.potion_type[3] 
                ).values(quantity = potion.quantity))
            connection.execute(sqlalchemy.update(material_inventory).values(
                red_ml = material_inventory.c.red_ml - potion.potion_type[0]*potion.quantity,
                green_ml = material_inventory.c.green_ml - potion.potion_type[1]*potion.quantity,
                blue_ml = material_inventory.c.blue_ml - potion.potion_type[2]*potion.quantity,
                dark_ml = material_inventory.c.dark_ml - potion.potion_type[3]*potion.quantity))
            print(connection.execute(sqlalchemy.select(material_inventory)).fetchall())
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    metadata_obj = sqlalchemy.MetaData()
    potion_inventory = sqlalchemy.Table("potion_inventory", metadata_obj, autoload_with= db.engine) 

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        ml = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM material_inventory")).all()[0]
        quantity_dict = {}
        json = []
        potions = connection.execute(sqlalchemy.select(potion_inventory))
        for row in potions:
            quantity_dict[row.sku] = ([row.red, row.green, row.blue, row.dark], row.quantity) 
        if ml[0] >= 150 and ml[1] >= 150 and quantity_dict["SWAMP_WATER_0"][1] < 3: 
            json.append({
                "potion_type": quantity_dict["SWAMP_WATER_0"][0],
                "quantity": 3
            })
            ml = [m - p*3 for m, p in zip(ml, quantity_dict["SWAMP_WATER_0"][0])]
            print(ml)

        if ml[0] >= 150 and ml[2] >= 150 and quantity_dict["VIOLET_POTION_0"][1] < 3: 
            json.append({
                "potion_type": quantity_dict["VIOLET_POTION_0"][0],
                "quantity": 3
            })
            ml = [m - p*3 for m, p in zip(ml, quantity_dict["VIOLET_POTION_0"][0])]
            print(ml)

        if ml[0] >= 100 and quantity_dict["RED_POTION_0"][1] < 5:
            q = ml[0]//200
            if q > 0:
                json.append({
                    "potion_type": quantity_dict["RED_POTION_0"][0],
                    "quantity": q
                })
            ml = [m - p*q for m, p in zip(ml, quantity_dict["RED_POTION_0"][0])]
            print(ml)

        if ml[1] >= 100 and quantity_dict["GREEN_POTION_0"][1] < 5:
            q = ml[1]//200
            if q > 0: 
                json.append({
                    "potion_type": quantity_dict["GREEN_POTION_0"][0],
                    "quantity": q
                })
            ml = [m - p*q for m, p in zip(ml, quantity_dict["GREEN_POTION_0"][0])]
            print(ml)

        if ml[2] >= 100 and quantity_dict["BLUE_POTION_0"][1] < 5:
            q = ml[2]//200
            if q > 0:
                json.append({
                    "potion_type": quantity_dict["BLUE_POTION_0"][0],
                    "quantity": q
                })
            ml = [m - p*q for m, p in zip(ml, quantity_dict["BLUE_POTION_0"][0])]
            print(ml)  
    return json

if __name__ == "__main__":
    print(get_bottle_plan())