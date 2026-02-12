"""
Product stocks (write-only model)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from sqlalchemy import text
from stocks.models.stock import Stock
from db import get_redis_conn, get_sqlalchemy_session

# Redis being redis, I need to manually sync it's info and the info of it' smetadata (sku, etc) anytime ANY operation is done, otherwise 
# it will never be up to date. It still wont be up to date when a query has not been made on it.
def _upsert_stock_to_redis(r, session, product_id, quantity):
    p = session.execute(
        text("SELECT name, sku, price FROM products WHERE id = :id"), 
        {"id": product_id}
    ).fetchone()
    
    if p:
        # Mapping to do it all at once
        r.hset(f"stock:{product_id}", mapping={
            "quantity": quantity,
            "name": p.name,
            "sku": p.sku,
            "price": str(p.price)
        })
    else:
        # Fallback if does not exist in product tbale
        r.hset(f"stock:{product_id}", "quantity", quantity)

def set_stock_for_product(product_id, quantity):
    """Set stock quantity for product in MySQL"""
    session = get_sqlalchemy_session()
    try: 
        result = session.execute(
            text(f"""
                UPDATE stocks 
                SET quantity = :qty 
                WHERE product_id = :pid
            """),
            {"pid": product_id, "qty": quantity}
        )
        response_message = f"rows updated: {result.rowcount}"
        if result.rowcount == 0:
            new_stock = Stock(product_id=product_id, quantity=quantity)
            session.add(new_stock)
            response_message = f"rows added, product {new_stock.product_id}"
            session.flush() 
            session.commit()
  
        r = get_redis_conn()
        _upsert_stock_to_redis(r, session, product_id, quantity)
        r.hset(f"stock:{product_id}", "quantity", quantity)
        return response_message
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
    
def update_stock_mysql(session, order_items, operation):
    """ Update stock quantities in MySQL according to a given operation (+/-) """
    try:
        for item in order_items:
            if hasattr(order_items[0], 'product_id'):
                pid = item.product_id
                qty = item.quantity
            else:
                pid = item['product_id']
                qty = item['quantity']
            session.execute(
                text(f"""
                    UPDATE stocks 
                    SET quantity = quantity {operation} :qty 
                    WHERE product_id = :pid
                """),
                {"pid": pid, "qty": qty}
            )
    except Exception as e:
        raise e
    
def check_out_items_from_stock(session, order_items):
    """ Decrease stock quantities in Redis """
    update_stock_mysql(session, order_items, "-")
    
def check_in_items_to_stock(session, order_items):
    """ Increase stock quantities in Redis """
    update_stock_mysql(session, order_items, "+")

def update_stock_redis(order_items, operation):
    """ Update stock quantities in Redis """
    if not order_items:
        return
    r = get_redis_conn()
    stock_keys = list(r.scan_iter("stock:*"))
    if stock_keys:
        session = get_sqlalchemy_session() # Utilisation d'une session alchemy
        pipeline = r.pipeline()
        for item in order_items:
            if hasattr(item, 'product_id'):
                product_id = item.product_id
                quantity = item.quantity
            else:
                product_id = item['product_id']
                quantity = item['quantity']
            current_stock = r.hget(f"stock:{product_id}", "quantity")
            current_stock = int(current_stock) if current_stock else 0
            
            if operation == '+':
                new_quantity = current_stock + quantity
            else:  
                new_quantity = current_stock - quantity
            

            p = session.execute(
                text("SELECT name, sku, price FROM products WHERE id = :id"), 
                {"id": product_id}
            ).fetchone()

            pipeline.hset(f"stock:{product_id}", mapping={
                "quantity": new_quantity,
                "name": p.name,       # Ajouté
                "sku": p.sku,         # Ajouté
                "price": str(p.price) # Ajouté (converti en string pour Redis)
            })

            _upsert_stock_to_redis(r, session, product_id, quantity)
        
        pipeline.execute()
        session.close() # on doit maintenant fermer la session
    else:
        _populate_redis_from_mysql(r)

def _populate_redis_from_mysql(redis_conn):
    """ Helper function to populate Redis from MySQL stocks table """
    session = get_sqlalchemy_session()
    try:
        # Nouveau join pour les nouvelles colonnes
        stocks = session.execute(
            text("""
                SELECT s.product_id, s.quantity, p.name, p.sku, p.price 
                FROM stocks s 
                JOIN products p ON s.product_id = p.id
            """)
        ).fetchall()

        if not len(stocks):
            print("Il n'est pas nécessaire de synchroniser le stock MySQL avec Redis")
            return
        
        pipeline = redis_conn.pipeline()
        for product_id, quantity, name, sku, price in stocks:
            pipeline.hset(
                f"stock:{product_id}", 
                mapping={ 
                    "quantity": quantity,
                    "name": name,
                    "sku": sku,
                    "price": str(price) # Redis doesn't like the decimal type
                }
            )
        
        pipeline.execute()
        print(f"{len(stocks)} enregistrements de stock ont été synchronisés avec Redis")
        
    except Exception as e:
        print(f"Erreur de synchronisation: {e}")
        raise e
    finally:
        session.close()