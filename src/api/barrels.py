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
            connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (change, description) VALUES (:total_cost, :descriptor)"),[{"total_cost": barrel.quantity*barrel.price*-1, "descriptor": f'Bought {barrel.quantity} {barrel.sku}'}])
            match barrel.potion_type: 
                case [0,1,0,0]:
                    connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (type, change) VALUES ('green', :barrel_ml)"),[{"barrel_ml": barrel.ml_per_barrel*barrel.quantity}])
                case [1,0,0,0]:
                    connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (type, change) VALUES ('red', :barrel_ml)"),[{"barrel_ml": barrel.ml_per_barrel*barrel.quantity}])
                case [0,0,1,0]:
                    connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (type, change) VALUES ('blue', :barrel_ml)"),[{"barrel_ml": barrel.ml_per_barrel*barrel.quantity}])
                case [0,0,0,1]:
                    connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (type, change) VALUES ('dark', :barrel_ml)"),[{"barrel_ml": barrel.ml_per_barrel*barrel.quantity}])

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
# Used to set purchase logic 
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print(wholesale_catalog)

    json_str = []
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
        gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM gold_ledger")).scalar_one()
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_GREEN_BARREL" and ml[0] <= 250 and gold >= barrel.price:
                print(ml, barrel.sku, barrel.price)
                json_str.append({"sku": "SMALL_GREEN_BARREL","quantity": max(1, gold//200)})
                gold -= barrel.price 
            if barrel.sku == "SMALL_RED_BARREL" and ml[1] <= 250 and gold >= barrel.price:
                print(ml, barrel.sku, barrel.price)
                json_str.append({"sku": "SMALL_RED_BARREL","quantity": max(1, gold//200)}) 
                gold -= barrel.price 
            if barrel.sku == "SMALL_BLUE_BARREL" and ml[2] <= 250 and gold >= barrel.price:
                print(ml, barrel.sku, barrel.price)
                json_str.append({"sku": "SMALL_BLUE_BARREL","quantity": max(1, gold//200)}) 
                gold -= barrel.price 
            if barrel.sku == "SMALL_DARK_BARREL" and ml[2] <= 250 and gold >= barrel.price:
                print(ml, barrel.sku, barrel.price)
                json_str.append({"sku": "SMALL_DARK_BARREL","quantity": max(1, gold//200)}) 
                gold -= barrel.price 
    
    return json_str

        
    


