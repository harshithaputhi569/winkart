import os
import sys
import django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'winkart_backend.settings')
django.setup()

from pymongo import MongoClient, GEOSPHERE, TEXT
from django.conf import settings

# MongoDB Connection URI
MONGO_URI = getattr(settings, 'MONGODB_URI', 'mongodb://localhost:27017/')
MONGO_DB_NAME = getattr(settings, 'MONGODB_NAME', 'winkart_db')

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Collections
users_col = db['users']
categories_col = db['categories']
products_col = db['products']
banners_col = db['banners']
bills_col = db['bills']
invoices_col = db['invoices']
import_logs_col = db['import_logs']
product_structures_col = db['product_structures']

def init_db():
    """Initializes the database collections and sets up indexes."""
    try:
        # User indexes
        users_col.create_index("email", unique=True, sparse=True)
        users_col.create_index("phone", unique=True, sparse=True)
        users_col.create_index([("location", GEOSPHERE)])
        
        # Category indexes
        categories_col.create_index("slug", unique=True)
        categories_col.create_index("parent_id")
        
        # Product indexes
        products_col.create_index("shop_id")
        products_col.create_index("category_id")
        products_col.create_index([("name", TEXT), ("description", TEXT)], default_language="english")
        
        # Banner indexes
        banners_col.create_index("shop_id")
        banners_col.create_index([("start_date", 1), ("end_date", 1)])
        
        # Bills indexes
        bills_col.create_index("customer_id")
        bills_col.create_index("shop_id")
        bills_col.create_index("status")
        bills_col.create_index("created_at")
        
        # Invoice indexes
        invoices_col.create_index("bill_id", unique=True)
        
        # Import Logs indexes
        import_logs_col.create_index("seller_id")
        import_logs_col.create_index("created_at")

        # Product Structures indexes
        product_structures_col.create_index("seller_id", unique=True)
        
        print("MongoDB Indexes initialized successfully.")
    except Exception as e:
        print(f"Error initializing MongoDB Indexes: {e}")

if __name__ == "__main__":
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'winkart_backend.settings')
    django.setup()
    init_db()

