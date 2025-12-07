import requests, sys

GATEWAY = 'http://localhost:8000'
CUST = ('khangdepzai','123456')

expected_restaurant_ids = [2,3]

def get_token(u,p):
    r = requests.post(f"{GATEWAY}/token", data={'username':u,'password':p})
    r.raise_for_status()
    return r.json()['access_token']

if __name__ == '__main__':
    try:
        token = get_token(*CUST)
    except Exception as e:
        print('Failed to get token', e); sys.exit(2)

    cart_items = [
        {'restaurant_id':2,'product_id':1,'product_name':'Combo Gà Rán Cơ Bản','quantity':1,'price':89000,'weight':0.8},
        {'restaurant_id':3,'product_id':5,'product_name':'Trà Sữa Phúc Long','quantity':1,'price':55000,'weight':0.5}
    ]

    payload = {
        'items': cart_items,
        'delivery_address': '123 Test St',
        'notes': 'Testing split checkout',
        'payment_method': 'cod'
    }

    r = requests.post(f"{GATEWAY}/api/orders/orders/checkout", json=payload, headers={'Authorization': f'Bearer {token}'})
    print('status', r.status_code)
    if r.status_code != 201:
        print(r.text); sys.exit(3)

    data = r.json()
    orders = data.get('orders', [])
    payments = data.get('payments', [])

    print('orders count', len(orders))
    if len(orders) != len(expected_restaurant_ids):
        print('Expected', len(expected_restaurant_ids), 'orders, got', len(orders))
        sys.exit(4)

    # Ensure each created order has the right restaurant id
    got_ids = sorted([o['restaurant_id'] for o in orders])
    if got_ids != sorted(expected_restaurant_ids):
        print('Mismatch restaurants', got_ids)
        sys.exit(5)

    print('Split checkout test passed')
    sys.exit(0)
