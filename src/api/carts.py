from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    if sort_col is search_sort_options.customer_name:
        order_by = db.search_view.c.customer_name
    elif sort_col is search_sort_options.item_sku:
        order_by = db.search_view.c.item_sku
    elif sort_col is search_sort_options.line_item_total:
        order_by = db.search_view.c.quantity
    elif sort_col is search_sort_options.timestamp:
        order_by = db.search_view.c.created_at
    else: 
        assert False

    if sort_order is search_sort_order.asc:
        order_by = order_by.asc()
    else:
        order_by = order_by.desc() 

    if search_page == "":
        offset = 0
    else: 
        offset = int(search_page)

    stmt = (sqlalchemy.select(db.search_view)
    .limit(5)
    .offset(5*offset)
    .order_by(order_by)
    )

    if customer_name != "":
        stmt = stmt.where(db.search_view.c.customer_name.ilike(f"%{customer_name}%"))

    if potion_sku != "":
        stmt = stmt.where(db.search_view.c.item_sku.ilike(f"%{potion_sku}%"))

    json = []
    with db.engine.begin() as connection:
        result = connection.execute(stmt)
        offset_max = connection.execute(sqlalchemy.text("SELECT COUNT(customer_id) FROM search_view")).scalar_one()//5
        print(offset_max)
        for row in result:
            json.append(
                {
                "line_item_id": row.customer_id,
                "item_sku": row.item_sku,
                "customer_name": row.customer_name,
                "line_item_total": row.gold,
                "timestamp": row.created_at,
                }
            )
    if offset-1 < 0:
        previous = ""
    else:
        previous = str(offset-1)
    if offset+1 > offset_max:
        next = ""
    else:
        next = str(offset+1)

    return {
        "previous": previous,
        "next": next,
        "results": json,
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO carts (customer_name, customer_class, level) VALUES (:customer_name, :customer_class, :level)"),[
            {"customer_name": new_cart.customer_name,
             "customer_class": new_cart.character_class,
             "level": new_cart.level}
        ])
        return {"cart_id": connection.execute(sqlalchemy.text("SELECT MAX(ID) from carts")).scalar_one()}


class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text('''
                                           INSERT INTO cart_items (customer_id, quantity, item_id)
                                           SELECT :cart_id, :quantity,
                                           id FROM potion_inventory WHERE sku = :item_sku 
                                           '''),[{"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity}])

    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    revenue = 0
    potion_total = 0
    potion_str = ''
    with db.engine.begin() as connection:
        potions_bought = connection.execute(sqlalchemy.text("""SELECT COALESCE(SUM(cart_items.quantity),0) AS total, item_id, price, potion_name 
                                                            FROM cart_items 
                                                            JOIN potion_inventory ON potion_inventory.id = item_id
                                                            WHERE customer_id = :cart_id
                                                            GROUP BY item_id, price, potion_name"""),[{"cart_id": cart_id}]).fetchall()
        for potion in potions_bought:
            potion_total += potion.total
            revenue += potion.total * potion.price
            potion_str += f'{potion.potion_name}, '
            connection.execute(sqlalchemy.text("""INSERT INTO potion_ledger (potion_id, change, description) VALUES (:item_id, :total, :descriptor)"""),[{"item_id": potion.item_id, "total": potion.total*-1, "descriptor": f'Sold to {cart_id}'}])
        connection.execute(sqlalchemy.text("""INSERT INTO gold_ledger (change, description) VALUES (:revenue, :description)"""),[{"revenue": revenue, "description": f'Sold {potion_total} of {potion_str}'}])





        
    return {"total_potions_bought": potion_total, "total_gold_paid": revenue}
