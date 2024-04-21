from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        metadata_obj = sqlalchemy.MetaData()
        potion_inventory = sqlalchemy.Table("potion_inventory", metadata_obj, autoload_with= db.engine) 
        in_stock = connection.execute(sqlalchemy.select(potion_inventory).where(potion_inventory.c.quantity > 0))
        json_str = []
    for row in in_stock:
        json_str.append({
                    "sku": row.sku,
                    "name": row.potion_name,
                    "quantity": row.quantity,
                    "price": row.price,
                    "potion_type": [row.red,
                                    row.green,
                                    row.blue,
                                    row.dark]
                })   
    print(json_str)
    return json_str
