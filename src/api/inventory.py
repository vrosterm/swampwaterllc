from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        grn_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml from global_inventory")).scalar_one()
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml from global_inventory")).scalar_one()
        blu_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml from global_inventory")).scalar_one()
        grn_count = connection.execute(sqlalchemy.text("SELECT num_green_potions from global_inventory")).scalar_one()
        red_count = connection.execute(sqlalchemy.text("SELECT num_red_potions from global_inventory")).scalar_one()
        blu_count = connection.execute(sqlalchemy.text("SELECT num_blue_potions from global_inventory")).scalar_one()
        gold_count = connection.execute(sqlalchemy.text("SELECT gold from global_inventory")).scalar_one()
    
    return {"number_of_potions": grn_count + red_count + blu_count, "ml_in_barrels": red_ml + grn_ml + blu_ml, "gold": gold_count}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
