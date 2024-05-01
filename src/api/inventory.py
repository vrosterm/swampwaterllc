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
        potion_count = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM potion_ledger")).scalar_one()
        ml_count = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change),0) FROM ml_ledger")).scalar_one()
        gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change),0) FROM gold_ledger")).scalar_one()
    
    return {"number_of_potions": potion_count, "ml_in_barrels": ml_count, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    potion_cap_purchase = 0
    ml_cap_purchase = 0
    with db.engine.begin() as connection:
        potion_count = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM potion_ledger")).scalar_one()
        ml_count = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change),0) FROM ml_ledger")).scalar_one()
        gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change),0) FROM gold_ledger")).scalar_one()

    if 50 - potion_count%50 <= 10 and gold >= 1500:
        potion_cap_purchase += 1
        gold -= 1000*potion_cap_purchase
    
    if 10000 - ml_count%10000 <= 1000 and gold >= 1500:
        ml_cap_purchase += 1 


    return {
        "potion_capacity": potion_cap_purchase,
        "ml_capacity": ml_cap_purchase
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
