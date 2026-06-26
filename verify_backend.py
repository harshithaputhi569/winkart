import requests
import json
import time
import os
import pandas as pd
from bson import ObjectId
from pymongo import MongoClient

# Database Cleanup Helper
def cleanup_mongodb():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['winkart_db']
    db['users'].delete_many({'email': {'$in': ['test_customer@winkart.com', 'test_seller@winkart.com']}})
    db['categories'].delete_many({'slug': {'$in': ['test-electronics', 'test-smartphones']}})
    # Clean products listed by test seller
    # Find test seller first
    seller = db['users'].find_one({'email': 'test_seller@winkart.com'})
    if seller:
        db['products'].delete_many({'shop_id': str(seller['_id'])})
        db['banners'].delete_many({'shop_id': str(seller['_id'])})
        db['bills'].delete_many({'shop_id': str(seller['_id'])})
        db['import_logs'].delete_many({'seller_id': str(seller['_id'])})
    # Remove test carts
    db['carts'].delete_many({})
    print("Database cleaned up successfully.")

def run_tests():
    BASE_URL = 'http://127.0.0.1:8000/api'
    
    # 1. Cleanup database first
    cleanup_mongodb()
    
    # Create session
    sess = requests.Session()
    
    print("\n--- Testing Registration & Authentication ---")
    
    # Register Customer
    cust_reg_payload = {
        "name": "Test Customer",
        "email": "test_customer@winkart.com",
        "phone": "9999988888",
        "password": "securepassword123"
    }
    r = sess.post(f"{BASE_URL}/auth/register/customer/", json=cust_reg_payload)
    print("Customer Register:", r.status_code, r.json().get('message'))
    assert r.status_code == 201
    
    # Register Seller
    seller_reg_payload = {
        "name": "Test Seller",
        "email": "test_seller@winkart.com",
        "phone": "8888899999",
        "password": "securepassword123",
        "shop_name": "Test Supermart",
        "shop_address": "456 Tech Park, Bengaluru, Karnataka"
    }
    r = sess.post(f"{BASE_URL}/auth/register/seller/", json=seller_reg_payload)
    print("Seller Register:", r.status_code, r.json().get('message'))
    assert r.status_code == 201
    
    # Login Seller
    login_payload = {
        "email": "test_seller@winkart.com",
        "password": "securepassword123"
    }
    r = sess.post(f"{BASE_URL}/auth/login/", json=login_payload)
    print("Seller Login:", r.status_code)
    assert r.status_code == 200
    seller_tokens = r.json()['tokens']
    seller_id = r.json()['user']['id']
    
    # Login Customer
    login_payload = {
        "email": "test_customer@winkart.com",
        "password": "securepassword123"
    }
    r = sess.post(f"{BASE_URL}/auth/login/", json=login_payload)
    print("Customer Login:", r.status_code)
    assert r.status_code == 200
    customer_tokens = r.json()['tokens']
    customer_id = r.json()['user']['id']
    
    # Headers
    seller_headers = {'Authorization': f"Bearer {seller_tokens['access']}"}
    customer_headers = {'Authorization': f"Bearer {customer_tokens['access']}"}
    
    print("\n--- Testing Profile & Seller Configuration ---")
    
    # Get profile
    r = sess.get(f"{BASE_URL}/auth/profile/", headers=customer_headers)
    print("Get Profile:", r.status_code, r.json().get('name'))
    assert r.status_code == 200
    
    # Update Seller Settings (Map Coordinates & Hours)
    settings_payload = {
        "shop_description": "All your tech gadgets in one place.",
        "location": {
            "latitude": 12.9716,
            "longitude": 77.5946
        },
        "business_hours": {
            "monday": {"is_open": True, "open_time": "08:00", "close_time": "22:00"}
        }
    }
    r = sess.put(f"{BASE_URL}/auth/seller/settings/", json=settings_payload, headers=seller_headers)
    print("Update Seller Settings:", r.status_code, r.json().get('message'))
    assert r.status_code == 200
    
    print("\n--- Testing Geospatial Shop Listing ---")
    
    # Search nearby shops (within 50km of Bengaluru)
    r = sess.get(f"{BASE_URL}/core/shops/?latitude=12.9700&longitude=77.5900")
    print("Geospatial Shop Search (Found):", r.status_code, len(r.json()))
    assert r.status_code == 200
    assert len(r.json()) > 0
    assert r.json()[0]['shop_name'] == "Test Supermart"
    
    print("\n--- Testing Categories & Catalog Management ---")
    
    # Create L1 Category
    cat_l1_payload = {
        "name": "Electronics",
        "slug": "test-electronics"
    }
    r = sess.post(f"{BASE_URL}/core/categories/", json=cat_l1_payload, headers=seller_headers)
    print("Create L1 Category:", r.status_code, r.json().get('name'))
    assert r.status_code == 201
    l1_id = r.json()['id']
    
    # Create L2 Category (Sub-category)
    cat_l2_payload = {
        "name": "Smartphones",
        "slug": "test-smartphones",
        "parent_id": l1_id
    }
    r = sess.post(f"{BASE_URL}/core/categories/", json=cat_l2_payload, headers=seller_headers)
    print("Create L2 Category:", r.status_code, r.json().get('name'))
    assert r.status_code == 201
    l2_id = r.json()['id']
    
    # List categories
    r = sess.get(f"{BASE_URL}/core/categories/")
    print("List Categories count:", r.status_code, len(r.json()))
    assert r.status_code == 200
    
    # Create Products
    prod1_payload = {
        "name": "Phone Max Pro 14",
        "description": "High end premium phone",
        "price": 79999.00,
        "discount_price": 74999.00,
        "category_id": l2_id,
        "stock_quantity": 50,
        "attributes": {"brand": "Apple", "color": "Deep Purple"}
    }
    r = sess.post(f"{BASE_URL}/core/products/", json=prod1_payload, headers=seller_headers)
    print("Create Product 1:", r.status_code, r.json().get('name'))
    assert r.status_code == 201
    prod1_id = r.json()['id']
    
    prod2_payload = {
        "name": "Phone Charger Fast 30W",
        "description": "30W fast charging adaptor",
        "price": 1999.00,
        "discount_price": 1499.00,
        "category_id": l2_id,
        "stock_quantity": 200,
        "attributes": {"brand": "Apple", "type": "USB-C"}
    }
    r = sess.post(f"{BASE_URL}/core/products/", json=prod2_payload, headers=seller_headers)
    print("Create Product 2:", r.status_code, r.json().get('name'))
    assert r.status_code == 201
    prod2_id = r.json()['id']
    
    # List shop details (checking sub-categories based on listed products)
    r = sess.get(f"{BASE_URL}/core/shops/{seller_id}/")
    print("Get Shop Details with categories:", r.status_code, len(r.json()['categories']))
    assert r.status_code == 200
    assert len(r.json()['categories']) > 0
    
    print("\n--- Testing Marketing & Recommendation Configurations ---")
    
    # Configure Product 2 as a Cross-sell recommendation for Product 1
    rec_payload = {
        "product_id": prod1_id,
        "type": "cross_sell",
        "linked_product_ids": [prod2_id]
    }
    r = sess.post(f"{BASE_URL}/marketing/recommendations/configure/", json=rec_payload, headers=seller_headers)
    print("Configure Cross-sell:", r.status_code, r.json().get('message'))
    assert r.status_code == 200
    
    # Fetch Recommendations for Product 1
    r = sess.get(f"{BASE_URL}/marketing/recommendations/{prod1_id}/")
    print("Fetch Recommendations count:", r.status_code, len(r.json()['cross_sell_recommendations']))
    assert r.status_code == 200
    assert len(r.json()['cross_sell_recommendations']) == 1
    assert r.json()['cross_sell_recommendations'][0]['name'] == "Phone Charger Fast 30W"
    
    print("\n--- Testing Cart & Billing Flow ---")
    
    # Add items to customer cart
    cart_payload = {
        "shop_id": seller_id,
        "items": [
            {"product_id": prod1_id, "quantity": 1},
            {"product_id": prod2_id, "quantity": 2}
        ]
    }
    r = sess.post(f"{BASE_URL}/operations/cart/", json=cart_payload, headers=customer_headers)
    print("Update Customer Cart:", r.status_code, r.json().get('message'))
    assert r.status_code == 200
    
    # View cart details
    r = sess.get(f"{BASE_URL}/operations/cart/", headers=customer_headers)
    print("Get Cart:", r.status_code, "Total items:", r.json()['total_items'])
    assert r.status_code == 200
    assert r.json()['total_items'] == 3
    
    # Checkout and generate a Bill
    checkout_payload = {
        "customer_name": "Test Customer",
        "customer_phone": "9999988888"
    }
    r = sess.post(f"{BASE_URL}/operations/checkout/", json=checkout_payload, headers=customer_headers)
    print("Checkout (Generate Bill):", r.status_code, "Bill Number:", r.json().get('bill_number'))
    assert r.status_code == 201
    bill_id = r.json()['bill_id']
    
    # Customer previous bills history
    r = sess.get(f"{BASE_URL}/operations/bills/customer/", headers=customer_headers)
    print("Customer Bills History:", r.status_code, "Bills count:", len(r.json()))
    assert r.status_code == 200
    assert len(r.json()) > 0
    
    # Seller bills list (Dashboard)
    r = sess.get(f"{BASE_URL}/operations/bills/seller/", headers=seller_headers)
    print("Seller Bills Dashboard:", r.status_code, "Bills count:", len(r.json()))
    assert r.status_code == 200
    assert len(r.json()) > 0
    
    # Seller updates Bill Status to Paid
    r = sess.put(f"{BASE_URL}/operations/bills/{bill_id}/", json={"status": "Paid"}, headers=seller_headers)
    print("Seller Updates Bill Status to Paid:", r.status_code, r.json().get('message'))
    assert r.status_code == 200
    
    # Dynamic Invoice PDF Download
    r = sess.get(f"{BASE_URL}/operations/bills/{bill_id}/download/")
    print("Download Invoice PDF:", r.status_code, "Content length:", len(r.content))
    assert r.status_code == 200
    assert r.headers['Content-Type'] == 'application/pdf'
    
    print("\n--- Testing Excel Exports ---")
    
    # Export Bills
    r = sess.get(f"{BASE_URL}/operations/products/export/?type=bills&export_format=excel", headers=seller_headers)
    print("Export Bills Excel:", r.status_code, "Content length:", len(r.content))
    assert r.status_code == 200
    assert 'spreadsheet' in r.headers['Content-Type'] or 'excel' in r.headers['Content-Type']
    
    print("\n--- Testing Excel Bulk Imports ---")
    # Generate dummy excel for import testing
    import io
    df = pd.DataFrame([
        {
            "name": "Phone Pro Max 15",
            "price": 99999.00,
            "category_slug": "test-smartphones",
            "description": "New model 15 phone",
            "discount_price": 94999.00,
            "stock_quantity": 25,
            "attributes": "brand:Apple,color:Natural Titanium"
        }
    ])
    xlsx_buffer = io.BytesIO()
    with pd.ExcelWriter(xlsx_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    xlsx_buffer.seek(0)
    xlsx_data = xlsx_buffer.getvalue()
    
    # Perform import
    files = {'file': ('import_test.xlsx', xlsx_data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    r = sess.post(f"{BASE_URL}/operations/products/import/", files=files, headers=seller_headers)
    print("Bulk Excel Import Products:", r.status_code, "Success count:", r.json().get('success_count'))
    assert r.status_code == 200
    assert r.json().get('success_count') == 1
    
    # View import history logs
    r = sess.get(f"{BASE_URL}/operations/products/import/history/", headers=seller_headers)
    print("Seller Import History Logs:", r.status_code, "Logs count:", len(r.json()))
    assert r.status_code == 200
    assert len(r.json()) > 0
    
    # 2. Cleanup database after tests
    cleanup_mongodb()
    
    print("\nALL BACKEND API TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
