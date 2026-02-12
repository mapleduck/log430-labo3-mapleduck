"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import pytest
import uuid
from store_manager import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status':'ok'}

def test_stock_flow(client):
    # Creer un id unique pour eviter des conflits au cas ou l'utilisateur d'un test anterieur n'aurait pas ete supprime
    # Si l'API retournait une liste entiere de users, on aurait pu verifier nous meme
    unique_id = uuid.uuid4().hex[:8]
    user_email = f'test_{unique_id}@example.com'
    user_name = f'User {unique_id}'

    user_data = {'name': user_name, 'email': user_email}
    res = client.post('/users', data=json.dumps(user_data), content_type='application/json')
    assert res.status_code == 201
    user_id = res.get_json()['user_id']

    try:
        # 1. Créer un article
        product_data = {'name': 'Test Item', 'sku': '12345', 'price': 99.90}
        prod_res = client.post('/products', data=json.dumps(product_data), content_type='application/json')
        assert prod_res.status_code == 201
        product_id = prod_res.get_json()['product_id']

        # 2. Ajouter 5 unités au stock
        client.post('/stocks', data=json.dumps({'product_id': product_id, 'quantity': 5}), content_type='application/json')
        
        # 3. Vérifier le stock (doit être 5)
        check_stock = client.get(f'/stocks/{product_id}')
        assert check_stock.get_json()['quantity'] == 5

        # 4. Passer une commande de 2 unités
        order_data = {'user_id': user_id, 'items': [{'product_id': product_id, 'quantity': 2}]}
        order_res = client.post('/orders', data=json.dumps(order_data), content_type='application/json')
        assert order_res.status_code == 201
        order_id = order_res.get_json()['order_id']

        # 5. Vérifier que le stock est descendu à 3
        assert client.get(f'/stocks/{product_id}').get_json()['quantity'] == 3

        # 6. Supprimer la commande et vérifier le retour en stock à 5
        del_order_res = client.delete(f'/orders/{order_id}')
        assert del_order_res.status_code in [200]
        assert client.get(f'/stocks/{product_id}').get_json()['quantity'] == 5

    finally:
        if user_id:
            client.delete(f'/users/{user_id}')