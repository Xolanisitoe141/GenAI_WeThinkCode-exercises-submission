"""
Exercise 4: Refactored Discount Calculator
==========================================
Refactored for readability: proper naming, helper functions,
guard clauses, and docstrings.
"""


def calculate_cart_total(cart):
    """Return the total price of all items in the cart."""
    return sum(item['price'] * item['quantity'] for item in cart)


def apply_promo_discount(total, promos, user):
    """
    Evaluate each promo and return the best discount amount.
    Also sets free_shipping on the user dict if applicable.
    """
    best_discount = 0

    for promo in promos:
        min_purchase = promo.get('min_purchase')
        meets_minimum = (min_purchase is None) or (total >= min_purchase)

        if not meets_minimum:
            continue

        if promo['type'] == 'percent':
            promo_discount = total * promo['value'] / 100
            best_discount = max(best_discount, promo_discount)

        elif promo['type'] == 'fixed':
            best_discount = max(best_discount, promo['value'])

        elif promo['type'] == 'shipping':
            user['free_shipping'] = True

    return best_discount


def apply_member_discount(total, user):
    """Return loyalty discount based on the user's membership status."""
    if user['status'] == 'vip':
        return total * 0.05
    if user['status'] == 'member' and user['months'] > 6:
        return total * 0.02
    return 0


def discount(cart, promos, user):
    """
    Calculate the final price after applying the best available discount.

    Returns a dict with keys: original, discount, final, free_shipping.
    """
    cart_total = calculate_cart_total(cart)

    promo_discount  = apply_promo_discount(cart_total, promos, user)
    member_discount = apply_member_discount(cart_total, user)
    best_discount   = max(promo_discount, member_discount)

    return {
        'original'     : cart_total,
        'discount'     : best_discount,
        'final'        : cart_total - best_discount,
        'free_shipping': user.get('free_shipping', False),
    }
