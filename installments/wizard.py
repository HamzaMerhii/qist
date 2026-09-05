"""Session-backed cart helpers for the multi-step 'Create New Sale' wizard.
Nothing is written to the DB until the Payment step is confirmed.
"""
from decimal import Decimal


def _cart_key(customer_id):
    return f"sale_cart_{customer_id}"


def get_cart(request, customer_id):
    return request.session.get(_cart_key(customer_id), {"items": [], "discount": "0", "tax": "0"})


def save_cart(request, customer_id, cart):
    request.session[_cart_key(customer_id)] = cart
    request.session.modified = True


def clear_cart(request, customer_id):
    request.session.pop(_cart_key(customer_id), None)


def add_item(request, customer_id, description, sku, unit_price, quantity=1, product_id=None, discount_pct="0"):
    cart = get_cart(request, customer_id)
    cart["items"].append({
        "product_id": product_id,
        "description": description,
        "sku": sku,
        "unit_price": str(unit_price),
        "quantity": int(quantity),
        "discount_pct": str(discount_pct),
    })
    save_cart(request, customer_id, cart)


def remove_item(request, customer_id, index):
    cart = get_cart(request, customer_id)
    if 0 <= index < len(cart["items"]):
        cart["items"].pop(index)
    save_cart(request, customer_id, cart)


def update_item_qty(request, customer_id, index, quantity):
    cart = get_cart(request, customer_id)
    if 0 <= index < len(cart["items"]):
        cart["items"][index]["quantity"] = max(1, int(quantity))
    save_cart(request, customer_id, cart)


def cart_line_total(item):
    gross = Decimal(item["unit_price"]) * int(item["quantity"])
    disc = Decimal(item.get("discount_pct", "0"))
    return (gross - (gross * disc / 100)).quantize(Decimal("0.01"))


def cart_subtotal(cart):
    return sum((cart_line_total(i) for i in cart["items"]), Decimal("0.00"))
