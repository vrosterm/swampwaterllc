from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import math
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
            connection.execute(sqlalchemy.text("""INSERT INTO potion_ledger (potion_id, change, description) 
                                               VALUES(:match , :quantity, 'from mix')"""),[{"quantity": potion.quantity, "match": match}])   
            i = 0
            # Add subtractions to ml ledger, with the type provided by color_dict. It's not really a dict, but I don't care...
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
def min_threshold_ml(ml: list[int], threshold: list[int]): 
    required_ml = []
    i = 0
    while i < len(threshold):
        if threshold[i] != 0:
            required_ml.append(ml[i])
        i += 1
    return min(required_ml)

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    json = []

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

        potions = connection.execute(sqlalchemy.text("SELECT red, green, blue, dark, th_red, th_green, th_blue, th_dark FROM potion_inventory"))
        for potion in potions:
            # Compare the minimum ml needed before you start making potions, and the actual ml needed to make at least one.
            threshold = [potion.th_red, potion.th_green, potion.th_blue, potion.th_dark]
            potion_type = [potion.red, potion.green, potion.blue, potion.dark]
            if all([m >= t for m,t in zip(ml, threshold)]):
                # In layman's terms, find the ml color that's needed with the least amount stored, and int divide by the maximum color ml needed to make at least one potion
                # which is inflated by 1.5. That way, no negative ml occurs, and there's always a little left over for the next batch.
                print(min_threshold_ml(ml, threshold), math.floor(1.5*max(potion_type)))
                q = min_threshold_ml(ml, threshold)//math.floor(1.5*max(potion_type))
                if q != 0:
                    json.append({
                        "potion_type": potion_type,
                        "quantity": q
                    })
                    ml = [m - p*q for m, p in zip(ml, potion_type)]
                    print(ml)
    return json
if __name__ == "__main__":
    print(get_bottle_plan())