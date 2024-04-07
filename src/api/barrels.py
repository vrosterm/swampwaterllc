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
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = {}".format(barrels_delivered[0].ml_per_barrel)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = {}".format(barrels_delivered[0].price)))

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
# Used to set purchase logic 
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print(wholesale_catalog)
    """ """
    with db.engine.begin() as connection:
        inv_count = connection.execute(sqlalchemy.text("SELECT num_green_potions from global_inventory")).scalar_one()
        gold_count = connection.execute(sqlalchemy.text("SELECT gold from global_inventory")).scalar_one()


    if inv_count < 10 and gold_count > 100:
        return [
        {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": 1, 
        }
    ]
    else:
        return
        
    


