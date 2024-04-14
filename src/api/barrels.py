from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    with db.engine.begin() as connection:
        for barrel in barrels_delivered: 
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = (SELECT gold FROM global_inventory) - {}".format(barrel.price)))
            match barrel.sku:
                case "SMALL_GREEN_BARREL":
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = {}".format(barrel.quantity)))
                case "SMALL_RED_BARREL":
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = {}".format(barrel.quantity)))
                case "SMALL_BLUE_BARREL":
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = {}".format(barrel.quantity)))

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
# Used to set purchase logic 
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print(wholesale_catalog)

    json_str = []
    """ """
    with db.engine.begin() as connection:
        grn_count = connection.execute(sqlalchemy.text("SELECT num_green_potions from global_inventory")).scalar_one()
        red_count = connection.execute(sqlalchemy.text("SELECT num_red_potions from global_inventory")).scalar_one()
        blue_count = connection.execute(sqlalchemy.text("SELECT num_blue_potions from global_inventory")).scalar_one()
        gold_count = connection.execute(sqlalchemy.text("SELECT gold from global_inventory")).scalar_one()

    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_GREEN_BARREL" and grn_count < 5 and gold_count >= barrel.price:
            json_str.append({"sku": "SMALL_GREEN_BARREL","quantity": 1,}) 
            gold_count -= barrel.price
        if barrel.sku == "SMALL_RED_BARREL" and red_count < 10 and gold_count >= barrel.price:
            json_str.append({"sku": "SMALL_RED_BARREL","quantity": 1,}) 
            gold_count -= barrel.price
        if barrel.sku == "SMALL_BLUE_BARREL" and blue_count < 10 and gold_count >= barrel.price:
            json_str.append({"sku": "SMALL_BLUE_BARREL","quantity": 1,}) 
            gold_count -= barrel.price

    
    return json_str

        
    


