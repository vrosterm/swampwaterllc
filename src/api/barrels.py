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
            connection.execute(sqlalchemy.text("UPDATE material_inventory SET gold = material_inventory.gold - :total_cost"),[{"total_cost": barrel.price*barrel.quantity}])
            match barrel.potion_type:
                case [0,1,0,0]:
                    connection.execute(sqlalchemy.text("UPDATE material_inventory SET green_ml = green_ml + :barrel_ml"),[{"barrel_ml": barrel.ml_per_barrel}])
                case [1,0,0,0]:
                    connection.execute(sqlalchemy.text("UPDATE material_inventory SET red_ml = red_ml + :barrel_ml"),[{"barrel_ml": barrel.ml_per_barrel}])
                case [0,0,1,0]:
                    connection.execute(sqlalchemy.text("UPDATE material_inventory SET blue_ml = blue_ml + :barrel_ml"),[{"barrel_ml": barrel.ml_per_barrel}])
                case [0,0,0,1]:
                    connection.execute(sqlalchemy.text("UPDATE material_inventory SET dark_ml = dark_ml + :barrel_ml"),[{"barrel_ml": barrel.ml_per_barrel}])

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
        ml = connection.execute(sqlalchemy.text("SELECT green_ml, red_ml, blue_ml, dark_ml from material_inventory")).fetchall()[0]
        gold = connection.execute(sqlalchemy.text("SELECT gold from material_inventory")).scalar_one()
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_GREEN_BARREL" and ml[0] <= 250 and gold >= barrel.price:
                print(ml, barrel.sku, barrel.price)
                json_str.append({"sku": "SMALL_GREEN_BARREL","quantity": 1,}) 
                connection.execute(sqlalchemy.text("UPDATE material_inventory SET gold = (SELECT gold FROM material_inventory) - :barrel_price"),[{"barrel_price": barrel.price}])
            if barrel.sku == "SMALL_RED_BARREL" and ml[1] <= 250 and gold >= barrel.price:
                print(ml, barrel.sku, barrel.price)
                json_str.append({"sku": "SMALL_RED_BARREL","quantity": 1,}) 
                connection.execute(sqlalchemy.text("UPDATE material_inventory SET gold = (SELECT gold FROM material_inventory) - :barrel_price"),[{"barrel_price": barrel.price}])
            if barrel.sku == "SMALL_BLUE_BARREL" and ml[2] <= 250 and gold >= barrel.price:
                print(ml, barrel.sku, barrel.price)
                json_str.append({"sku": "SMALL_BLUE_BARREL","quantity": 1,}) 
                connection.execute(sqlalchemy.text("UPDATE material_inventory SET gold = (SELECT gold FROM material_inventory) - :barrel_price"),[{"barrel_price": barrel.price}])

    
    return json_str

        
    


