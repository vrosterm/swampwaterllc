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
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
# Used to set purchase logic 
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    quantity = 0
    with db.engine.begin() as connection:
        inv_count = connection.execute(sqlalchemy.text("SELECT num_green_potions from global_inventory")).scalar_one()
    if inv_count < 10:
        quantity = 1
    
    print(wholesale_catalog)

    return [
        {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": quantity,
        }
    ]

