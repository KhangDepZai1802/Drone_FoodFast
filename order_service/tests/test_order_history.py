import requests
import sys

GATEWAY = 'http://localhost:8000'

# Credentials
CUSTOMER = ('khangdepzai', '123456')
RESTAURANT = ('kfc_vietnam', '123456')

def get_token(username, password):
    r = requests.post(f"{GATEWAY}/token", data={'username': username, 'password': password})
    r.raise_for_status()
    return r.json()['access_token']


def create_order(token):
    payload = {
        'restaurant_id': 2,
        'delivery_address': 'Automated test address',
        'items': [{'product_id': 1, 'product_name': 'Combo', 'quantity': 1, 'price': 89000, 'weight': 0.5}]
    }
    r = requests.post(f"{GATEWAY}/api/orders/orders", json=payload, headers={'Authorization': f'Bearer {token}'})
    r.raise_for_status()
    return r.json()


def update_status(token, order_id, status):
    r = requests.put(f"{GATEWAY}/api/orders/orders/{order_id}/status", json={'status': status}, headers={'Authorization': f'Bearer {token}'})
    r.raise_for_status()
    return r.json()


def get_order(order_id):
    r = requests.get(f"{GATEWAY}/api/orders/orders/{order_id}")
    r.raise_for_status()
    return r.json()


if __name__ == '__main__':
    try:
        cust_token = get_token(*CUSTOMER)
        rest_token = get_token(*RESTAURANT)
    except Exception as e:
        print('Failed to get tokens:', e)
        sys.exit(2)

    order = create_order(cust_token)
    order_id = order['id']
    print('Created order', order_id)

    # Verify initial history
    fetched = get_order(order_id)
    if not any(h['status'] == 'waiting_confirmation' for h in fetched.get('history', [])):
        print('Initial history missing waiting_confirmation')
        sys.exit(3)

    # Update to READY
    updated = update_status(rest_token, order_id, 'ready')
    print('Updated status to ready, got:', updated['status'])

    fetched = get_order(order_id)
    statuses = [h['status'] for h in fetched.get('history', [])]
    if 'ready' not in statuses:
        print('Ready history entry missing', statuses)
        sys.exit(4)

    print('READY history present')

    # If a drone was assigned, verify in_delivery is present
    if fetched.get('drone_id'):
        if 'in_delivery' not in statuses:
            print('Drone assigned but in_delivery history missing', statuses)
            sys.exit(5)
        else:
            print('IN_DELIVERY history present as expected')

    print('Order history test passed')
    sys.exit(0)
