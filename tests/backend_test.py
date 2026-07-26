"""
WIBAZA Marketplace - Backend API Tests
Covers: auth, categories, products, cart, orders, admin, chatbot
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://global-trading-hub-21.preview.emergentagent.com').rstrip('/')

ADMIN_EMAIL = 'admin@wibaza.com'
ADMIN_PASSWORD = 'Admin@2026Wibaza'

# Unique run-scoped identifiers to avoid conflicts across re-runs
RUN_ID = uuid.uuid4().hex[:8]
CLIENT_EMAIL = f'test_client_{RUN_ID}@wibaza.com'
SELLER_EMAIL = f'test_seller_{RUN_ID}@wibaza.com'
COMMON_PW = 'TestPass@123'


# ---------- Fixtures ----------
@pytest.fixture(scope='session')
def admin_session():
    s = requests.Session()
    r = s.post(f'{BASE_URL}/api/auth/login', json={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD})
    assert r.status_code == 200, f'Admin login failed: {r.status_code} {r.text}'
    return s


@pytest.fixture(scope='session')
def client_session():
    s = requests.Session()
    # Register client
    r = s.post(f'{BASE_URL}/api/auth/register', json={
        'email': CLIENT_EMAIL,
        'password': COMMON_PW,
        'name': 'Test Client',
        'role': 'client'
    })
    if r.status_code == 400:
        # Already registered, login instead
        r = s.post(f'{BASE_URL}/api/auth/login', json={'email': CLIENT_EMAIL, 'password': COMMON_PW})
    assert r.status_code == 200, f'Client register/login failed: {r.status_code} {r.text}'
    return s


@pytest.fixture(scope='session')
def seller_data(admin_session):
    """Register a seller and approve them via admin; return session + user_id."""
    s = requests.Session()
    r = s.post(f'{BASE_URL}/api/auth/register', json={
        'email': SELLER_EMAIL,
        'password': COMMON_PW,
        'name': 'Test Seller',
        'role': 'seller'
    })
    # Seller register returns 200 but is_approved=false. Cookies may be set but login later 403.
    assert r.status_code in (200, 400), f'Seller register: {r.status_code} {r.text}'
    seller_user = r.json() if r.status_code == 200 else None

    # Fetch user id via admin listing if not returned
    if not seller_user or 'id' not in seller_user:
        users = admin_session.get(f'{BASE_URL}/api/admin/users').json()
        seller_user = next((u for u in users if u.get('email') == SELLER_EMAIL), None)
        assert seller_user, 'Seller user not found via admin listing'

    return {'user_id': seller_user['id'], 'email': SELLER_EMAIL}


@pytest.fixture(scope='session')
def approved_seller_session(admin_session, seller_data):
    """Approve seller and return a logged-in session."""
    user_id = seller_data['user_id']
    r = admin_session.post(f'{BASE_URL}/api/admin/sellers/{user_id}/approve?approved=true')
    assert r.status_code == 200, f'Seller approval failed: {r.status_code} {r.text}'

    s = requests.Session()
    r = s.post(f'{BASE_URL}/api/auth/login', json={'email': SELLER_EMAIL, 'password': COMMON_PW})
    assert r.status_code == 200, f'Approved seller login failed: {r.status_code} {r.text}'
    return s


# ---------- Health ----------
class TestHealth:
    def test_root_online(self):
        r = requests.get(f'{BASE_URL}/api/')
        assert r.status_code == 200
        data = r.json()
        assert data['status'] == 'online'
        assert data['message'] == 'WIBAZA Marketplace API'

    def test_health_check(self):
        r = requests.get(f'{BASE_URL}/api/health')
        assert r.status_code == 200
        assert r.json()['status'] == 'healthy'


# ---------- Auth ----------
class TestAuth:
    def test_admin_login(self):
        s = requests.Session()
        r = s.post(f'{BASE_URL}/api/auth/login', json={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD})
        assert r.status_code == 200
        data = r.json()
        assert data.get('role') == 'admin'
        assert data.get('email') == ADMIN_EMAIL
        # Cookies must be set
        assert s.cookies.get('access_token'), 'access_token cookie not set'
        assert s.cookies.get('refresh_token'), 'refresh_token cookie not set'

    def test_admin_me(self, admin_session):
        r = admin_session.get(f'{BASE_URL}/api/auth/me')
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get('role') == 'admin'
        assert data.get('email') == ADMIN_EMAIL

    def test_register_client(self, client_session):
        r = client_session.get(f'{BASE_URL}/api/auth/me')
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get('role') == 'client'
        assert data.get('email') == CLIENT_EMAIL

    def test_register_seller_pending(self, seller_data):
        # Login should be blocked with 403 for unapproved seller.
        # But this fixture already ran; the seller may have been approved by later tests.
        # We test this only if seller_data indicates unapproved. So we do a fresh register.
        s = requests.Session()
        email = f'test_pending_{RUN_ID}@wibaza.com'
        r = s.post(f'{BASE_URL}/api/auth/register', json={
            'email': email, 'password': COMMON_PW, 'name': 'Pending Seller', 'role': 'seller'
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get('role') == 'seller'
        assert data.get('is_approved') is False

        # Logout / clear cookies and try login -> should fail with 403
        s2 = requests.Session()
        r2 = s2.post(f'{BASE_URL}/api/auth/login', json={'email': email, 'password': COMMON_PW})
        assert r2.status_code == 403, f'Expected 403, got {r2.status_code}: {r2.text}'
        assert 'pending approval' in r2.text.lower() or 'pending' in r2.text.lower()

    def test_login_invalid_credentials(self):
        r = requests.post(f'{BASE_URL}/api/auth/login', json={
            'email': ADMIN_EMAIL, 'password': 'wrongpassword'
        })
        assert r.status_code == 401


# ---------- Categories ----------
class TestCategories:
    def test_list_categories(self):
        r = requests.get(f'{BASE_URL}/api/categories')
        assert r.status_code == 200
        cats = r.json()
        assert isinstance(cats, list)
        assert len(cats) >= 6, f'Expected at least 6 seeded categories, got {len(cats)}'
        expected = {'Eletronicos', 'Moda', 'Casa e Decoracao', 'Livros', 'Esportes', 'Beleza e Saude'}
        got = {c['name'] for c in cats}
        assert expected.issubset(got), f'Missing categories: {expected - got}'

    def test_categories_expose_id(self):
        """Categories response should contain an 'id' field for FE consumption."""
        r = requests.get(f'{BASE_URL}/api/categories')
        assert r.status_code == 200
        cats = r.json()
        # Bug detection: categories won't have id since backend excludes _id AND doesn't rename
        missing_id = [c['name'] for c in cats if 'id' not in c]
        assert not missing_id, f'Categories missing id field: {missing_id}'

    def test_admin_create_category(self, admin_session):
        name = f'TEST_CAT_{RUN_ID}'
        r = admin_session.post(f'{BASE_URL}/api/categories/', json={
            'name': name, 'description': 'Test category', 'image_url': 'https://example.com/img.png'
        })
        assert r.status_code == 200, f'Create category failed: {r.status_code} {r.text}'
        data = r.json()
        assert data['name'] == name
        assert 'id' in data
        assert data['slug'] == name.lower().replace(' ', '-').replace('_', '')
        pytest.category_id = data['id']  # store for later


# ---------- Admin ----------
class TestAdmin:
    def test_admin_stats(self, admin_session):
        r = admin_session.get(f'{BASE_URL}/api/admin/stats')
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ('total_users', 'total_sellers', 'total_products', 'total_orders',
                  'pending_products', 'pending_sellers', 'total_revenue'):
            assert k in data, f'Missing stat key: {k}'
        assert isinstance(data['total_users'], int)

    def test_admin_users_list(self, admin_session):
        r = admin_session.get(f'{BASE_URL}/api/admin/users')
        assert r.status_code == 200, r.text
        users = r.json()
        assert isinstance(users, list)
        # Admin should be present, all users must have id
        no_id = [u.get('email') for u in users if 'id' not in u]
        assert not no_id, f'Users missing id field: {no_id}'

    def test_client_cannot_access_admin_stats(self, client_session):
        r = client_session.get(f'{BASE_URL}/api/admin/stats')
        assert r.status_code == 403


# ---------- Products (Seller/Admin) ----------
class TestProducts:
    def test_seller_create_product_pending(self, approved_seller_session):
        # Get a category id (need one). Use admin flow to fetch a category id via DB shortcut:
        # There is no public category with 'id', so we use the one created earlier or via admin.
        cat_id = getattr(pytest, 'category_id', None)
        if not cat_id:
            pytest.skip('No category id available (create-category test likely failed)')

        product_payload = {
            'name': f'TEST_PROD_{RUN_ID}',
            'description': 'Test product description',
            'category_id': cat_id,
            'price': 99.99,
            'stock': 10,
            'product_type': 'physical',
            'tags': ['test']
        }
        r = approved_seller_session.post(f'{BASE_URL}/api/products', json=product_payload)
        assert r.status_code == 200, f'Create product failed: {r.status_code} {r.text}'
        data = r.json()
        assert data['name'] == product_payload['name']
        assert data['approval_status'] == 'pending'
        assert 'id' in data
        pytest.product_id = data['id']

    def test_products_list_excludes_pending(self):
        # The just-created product is pending -> should NOT appear in public listing
        r = requests.get(f'{BASE_URL}/api/products')
        assert r.status_code == 200
        data = r.json()
        assert 'products' in data
        names = [p.get('name') for p in data['products']]
        assert f'TEST_PROD_{RUN_ID}' not in names, 'Pending product should not appear in public listing'

    def test_admin_approve_product(self, admin_session):
        pid = getattr(pytest, 'product_id', None)
        if not pid:
            pytest.skip('No product id available')
        r = admin_session.post(f'{BASE_URL}/api/products/{pid}/approve?approved=true')
        assert r.status_code == 200, r.text
        assert 'approved' in r.json()['message'].lower()

    def test_products_list_includes_approved(self):
        pid = getattr(pytest, 'product_id', None)
        if not pid:
            pytest.skip('No product id available')
        # small delay for consistency
        time.sleep(0.5)
        r = requests.get(f'{BASE_URL}/api/products')
        assert r.status_code == 200
        data = r.json()
        names = [p.get('name') for p in data['products']]
        assert f'TEST_PROD_{RUN_ID}' in names, f'Approved product missing from public listing. Got: {names}'


# ---------- Cart ----------
class TestCart:
    def test_client_add_to_cart(self, client_session):
        pid = getattr(pytest, 'product_id', None)
        if not pid:
            pytest.skip('No product id available')
        r = client_session.post(f'{BASE_URL}/api/cart/items', json={
            'product_id': pid, 'quantity': 2
        })
        assert r.status_code == 200, f'Add to cart failed: {r.status_code} {r.text}'

    def test_client_get_cart(self, client_session):
        r = client_session.get(f'{BASE_URL}/api/cart')
        assert r.status_code == 200, r.text
        cart = r.json()
        assert 'items' in cart
        assert len(cart['items']) >= 1
        item = cart['items'][0]
        assert 'product' in item, 'Cart item should be enriched with product data'
        assert 'name' in item['product']
        assert item['quantity'] == 2


# ---------- Orders ----------
class TestOrders:
    def test_client_create_order(self, client_session, approved_seller_session):
        pid = getattr(pytest, 'product_id', None)
        if not pid:
            pytest.skip('No product id available')

        # Need seller_id for the order item; grab it via /auth/me on seller session
        me = approved_seller_session.get(f'{BASE_URL}/api/auth/me').json()
        seller_id = me.get('id') or me.get('_id')
        assert seller_id, f'Seller /me returned no id: {me}'

        payload = {
            'items': [{
                'product_id': pid,
                'product_name': f'TEST_PROD_{RUN_ID}',
                'seller_id': seller_id,
                'quantity': 1,
                'unit_price': 99.99,
                'total_price': 99.99
            }],
            'shipping_address': {'street': '123 St', 'city': 'SP', 'country': 'BR', 'zip': '00000-000'},
            'billing_address': {'street': '123 St', 'city': 'SP', 'country': 'BR', 'zip': '00000-000'}
        }
        r = client_session.post(f'{BASE_URL}/api/orders', json=payload)
        assert r.status_code == 200, f'Order create failed: {r.status_code} {r.text}'
        data = r.json()
        assert 'order_number' in data
        assert data['total'] == 99.99
        assert data['status'] == 'pending'
        pytest.order_id = data['id']

    def test_client_list_orders(self, client_session):
        r = client_session.get(f'{BASE_URL}/api/orders')
        assert r.status_code == 200, r.text
        orders = r.json()
        assert isinstance(orders, list)
        assert len(orders) >= 1


# ---------- Products - New Fields (colors, sizes, dimensions, images, tags) ----------
class TestProductNewFields:
    def test_seller_create_product_with_new_fields(self, approved_seller_session, admin_session):
        cat_id = getattr(pytest, 'category_id', None)
        if not cat_id:
            pytest.skip('No category id available')
        
        payload = {
            'name': f'TEST_PROD_FULL_{RUN_ID}',
            'description': 'Product with colors, sizes, dimensions',
            'category_id': cat_id,
            'price': 199.99,
            'stock': 5,
            'weight': 1.5,
            'dimensions': {'length': 20.0, 'width': 10.0, 'height': 5.0, 'unit': 'cm'},
            'images': ['https://example.com/a.jpg', 'https://example.com/b.jpg'],
            'colors': ['Preto', 'Branco', 'Vermelho'],
            'sizes': ['P', 'M', 'G'],
            'tags': ['novo', 'oferta', 'iphone'],
            'attributes': [{'name': 'Origem', 'value': 'Brasil'}],
            'brand': 'TestBrand',
            'sku': f'SKU-{RUN_ID}',
            'product_type': 'physical'
        }
        r = approved_seller_session.post(f'{BASE_URL}/api/products', json=payload)
        assert r.status_code == 200, f'{r.status_code}: {r.text}'
        data = r.json()
        pytest.product_full_id = data['id']
        # Verify create endpoint accepts and persists these fields (BUG: images/attributes overwritten in code)
        assert data['colors'] == ['Preto', 'Branco', 'Vermelho'], f'colors not preserved: {data.get("colors")}'
        assert data['sizes'] == ['P', 'M', 'G'], f'sizes not preserved: {data.get("sizes")}'
        assert data['tags'] == ['novo', 'oferta', 'iphone'], f'tags not preserved: {data.get("tags")}'
        assert data['weight'] == 1.5
        assert data['dimensions']['length'] == 20.0
        assert data['dimensions']['unit'] == 'cm'
        # These are known bug sites - the create endpoint overwrites images/attributes to []
        assert data['images'] == ['https://example.com/a.jpg', 'https://example.com/b.jpg'], f'images overwritten! got: {data.get("images")}'
        assert data['attributes'] == [{'name': 'Origem', 'value': 'Brasil'}], f'attributes overwritten! got: {data.get("attributes")}'

    def test_get_product_returns_new_fields(self):
        pid = getattr(pytest, 'product_full_id', None)
        if not pid:
            pytest.skip('No full product id')
        # Approve first for public listing
        admin_s = requests.Session()
        admin_s.post(f'{BASE_URL}/api/auth/login', json={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD})
        admin_s.post(f'{BASE_URL}/api/products/{pid}/approve?approved=true')
        
        r = requests.get(f'{BASE_URL}/api/products/{pid}')
        assert r.status_code == 200, r.text
        data = r.json()
        assert 'colors' in data
        assert 'sizes' in data
        assert 'dimensions' in data
        assert 'weight' in data
        assert 'images' in data

    def test_search_products_by_name(self):
        # Should return the full product created above (approved)
        r = requests.get(f'{BASE_URL}/api/products', params={'search': f'TEST_PROD_FULL_{RUN_ID}'})
        assert r.status_code == 200, r.text
        data = r.json()
        names = [p.get('name') for p in data['products']]
        assert f'TEST_PROD_FULL_{RUN_ID}' in names, f'Search did not return product. Got: {names}'

    def test_search_products_by_tag(self):
        # 'iphone' tag was added to the product
        r = requests.get(f'{BASE_URL}/api/products', params={'search': 'iphone'})
        assert r.status_code == 200
        data = r.json()
        # Should find our product tagged with iphone or the seeded iPhone 15 Pro
        assert data['total'] >= 1

    def test_seller_update_product_new_fields(self, approved_seller_session):
        pid = getattr(pytest, 'product_full_id', None)
        if not pid:
            pytest.skip('No full product id')
        update_payload = {
            'colors': ['Azul', 'Verde'],
            'sizes': ['GG', 'XG'],
            'dimensions': {'length': 30.0, 'width': 15.0, 'height': 8.0, 'unit': 'cm'},
            'images': ['https://example.com/updated.jpg']
        }
        r = approved_seller_session.put(f'{BASE_URL}/api/products/{pid}', json=update_payload)
        assert r.status_code == 200, r.text
        # Verify via GET
        r2 = requests.get(f'{BASE_URL}/api/products/{pid}')
        assert r2.status_code == 200
        data = r2.json()
        assert data['colors'] == ['Azul', 'Verde']
        assert data['sizes'] == ['GG', 'XG']
        assert data['images'] == ['https://example.com/updated.jpg']
        assert data['dimensions']['length'] == 30.0


# ---------- Chatbot ----------
class TestChatbot:
    def test_chatbot_message_no_500(self):
        r = requests.post(f'{BASE_URL}/api/chatbot/message', json={
            'message': 'Olá, o que você vende?', 'conversation_history': []
        })
        # Given placeholder key, either 200 with fallback or gracefully failing (not 500)
        assert r.status_code == 200, f'Chatbot returned {r.status_code}: {r.text}'
        data = r.json()
        assert 'response' in data
        assert isinstance(data['response'], str) and len(data['response']) > 0
