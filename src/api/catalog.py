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
        in_stock = connection.execute(sqlalchemy.text("""SELECT sku, potion_name, price, red, green, blue, dark, COALESCE(SUM(change),0) AS total
                                                      FROM potion_inventory
                                                      JOIN potion_ledger ON potion_inventory.id = potion_id
                                                      GROUP BY sku, potion_name, price, red, green, blue, dark
                                                      """))

        json_str = []
    for row in in_stock:
        json_str.append({
                    "sku": row.sku,
                    "name": row.potion_name,
                    "quantity": row.total,
                    "price": row.price,
                    "potion_type": [row.red,
                                    row.green,
                                    row.blue,
                                    row.dark]
                })   
    print(json_str)
    return json_str
