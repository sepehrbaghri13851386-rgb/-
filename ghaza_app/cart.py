"""
Session-based shopping cart.

Cart structure inside request.session:
    cart = {
        "<food_id>": {"qty": 2},
        ...
    }
"""

CART_SESSION_KEY = 'cart'


def get_cart(session):
    """Return the raw cart dict stored in the session (never None)."""
    return session.get(CART_SESSION_KEY, {})


def add_to_cart(session, food_id, qty=1):
    """Add qty of food_id to the cart (or increase its quantity)."""
    cart = get_cart(session)
    key = str(food_id)
    cart[key] = cart.get(key, 0) + max(1, int(qty))
    cart[key] = min(cart[key], 99)
    session[CART_SESSION_KEY] = cart
    return cart[key]


def set_qty(session, food_id, qty):
    """Set an exact quantity; qty <= 0 removes the item."""
    cart = get_cart(session)
    key = str(food_id)
    if qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = min(int(qty), 99)
    session[CART_SESSION_KEY] = cart
    return cart


def remove_from_cart(session, food_id):
    """Remove food_id from the cart."""
    cart = get_cart(session)
    cart.pop(str(food_id), None)
    session[CART_SESSION_KEY] = cart
    return cart


def clear_cart(session):
    """Empty the cart (called after an order is placed)."""
    session[CART_SESSION_KEY] = {}
    return {}


def cart_details(session):
    """Build a list of dicts (food object, qty, unit price, line total)
    plus the cart totals. Returns (items, totals_dict)."""
    from ghaza_app.models import Food

    cart = get_cart(session)
    items = []
    subtotal = 0
    count = 0

    if cart:
        ids = [int(k) for k in cart.keys() if str(k).isdigit()]
        foods = Food.objects.filter(id__in=ids, is_available=True)
        food_map = {f.id: f for f in foods}
        for key, qty in cart.items():
            food = food_map.get(int(key))
            if food is None:
                continue
            line_total = food.final_price * qty
            subtotal += line_total
            count += qty
            items.append({
                'food': food,
                'qty': qty,
                'line_total': line_total,
            })

    delivery_fee = 25000 if items else 0
    totals = {
        'count': count,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'grand_total': subtotal + delivery_fee,
    }
    return items, totals
