from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text('''UPDATE material_inventory SET red_ml = 0, 
                                           green_ml = 0,
                                            blue_ml = 0,
                                            dark_ml = 0'''))
        connection.execute(sqlalchemy.text("UPDATE potion_inventory SET quantity = 0"))
        connection.execute(sqlalchemy.text("UPDATE material_inventory SET gold=100"))
        connection.execute(sqlalchemy.text('''DELETE FROM cart_items; 
                                           DELETE FROM carts'''))
    return "OK"

