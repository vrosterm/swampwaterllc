from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
metadata_obj = sqlalchemy.MetaData()
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
    color_dict = ['red', 'green', 'blue', 'dark']
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            match = connection.execute(sqlalchemy.text(""" SELECT id FROM potion_inventory
                                                       WHERE red = :red_ml AND green = :green_ml AND blue = :blue_ml AND dark = :dark_ml
                                                    """),[{"red_ml": potion.potion_type[0],
                                                            "green_ml": potion.potion_type[1],
                                                            "blue_ml": potion.potion_type[2],
                                                            "dark_ml": potion.potion_type[3]}]).scalar_one()
            connection.execute(sqlalchemy.text("""
                                               INSERT INTO potion_ledger (potion_id, change, description) 
                                               VALUES(:match , :quantity, 'from mix')"""),[{"quantity": potion.quantity, "match": match}])   
            i = 0
            while i < len(color_dict):
                ml = potion.potion_type[i]
                color = color_dict[i]
                i += 1  
                if ml > 0:
                    print(color)
                    connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (type, change)
                                                    VALUES (:color, :ml_quantity)
                                                        """),[{"color": color, "ml_quantity": ml*potion.quantity*-1}])                                                                    
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
        db_delta = connection.execute(sqlalchemy.text('''
                                (SELECT COALESCE(SUM(change), 0) FROM ml_ledger WHERE type = 'red') UNION ALL
                                (SELECT COALESCE(SUM(change), 0) FROM ml_ledger WHERE type = 'green') UNION ALL
                                (SELECT COALESCE(SUM(change), 0) FROM ml_ledger WHERE type = 'blue') UNION ALL
                                (SELECT COALESCE(SUM(change), 0) FROM ml_ledger WHERE type = 'dark')                                
                                ''')).fetchall()
        ml = []
        for color in db_delta:
            ml.append(color[0])      
        print(ml)  
        quantity_dict = {}
        json = []
        potions = connection.execute(sqlalchemy.text("""
                                    SELECT sku, COALESCE(SUM(change),0) AS quantity, red, green, blue, dark
                                    FROM potion_ledger
                                    RIGHT JOIN potion_inventory ON potion_ledger.potion_id = potion_inventory.id
                                    GROUP BY sku, red, green, blue, dark
                                    """)).fetchall()
        for row in potions:
            quantity_dict[row.sku] = ([row.red, row.green, row.blue, row.dark], row.quantity)
        print(quantity_dict)
        # Swamp Water
        if ml[0] >= 150 and ml[1] >= 150 and quantity_dict["SWAMP_WATER_0"][1] < 3: 
            json.append({
                "potion_type": quantity_dict["SWAMP_WATER_0"][0],
                "quantity": 3
            })
            ml = [m - p*3 for m, p in zip(ml, quantity_dict["SWAMP_WATER_0"][0])]

        # Violet
        if ml[0] >= 150 and ml[2] >= 150 and quantity_dict["VIOLET_POTION_0"][1] < 3: 
            json.append({
                "potion_type": quantity_dict["VIOLET_POTION_0"][0],
                "quantity": 3
            })
            ml = [m - p*3 for m, p in zip(ml, quantity_dict["VIOLET_POTION_0"][0])]
        # Red
        if ml[0] >= 100 and quantity_dict["RED_POTION_0"][1] < 5:
            q = ml[0]//200
            if q > 0:
                json.append({
                    "potion_type": quantity_dict["RED_POTION_0"][0],
                    "quantity": q
                })
            ml = [m - p*q for m, p in zip(ml, quantity_dict["RED_POTION_0"][0])]
        # Green
        if ml[1] >= 100 and quantity_dict["GREEN_POTION_0"][1] < 5:
            q = ml[1]//200
            if q > 0: 
                json.append({
                    "potion_type": quantity_dict["GREEN_POTION_0"][0],
                    "quantity": q
                })
            ml = [m - p*q for m, p in zip(ml, quantity_dict["GREEN_POTION_0"][0])]
        # Blue
        if ml[2] >= 100 and quantity_dict["BLUE_POTION_0"][1] < 5:
            q = ml[2]//200
            if q > 0:
                json.append({
                    "potion_type": quantity_dict["BLUE_POTION_0"][0],
                    "quantity": q
                })
            ml = [m - p*q for m, p in zip(ml, quantity_dict["BLUE_POTION_0"][0])]
        print(json)
    return json
if __name__ == "__main__":
    print(get_bottle_plan())