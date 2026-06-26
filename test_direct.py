import os
import django
import sys

# Setup django
sys.path.append(os.path.join(os.path.dirname(__file__), 'winkart_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'winkart_backend.settings')
django.setup()

from django.test import RequestFactory
from operations.views import BulkExportDataView
from authentication.auth import MongoUser
from rest_framework.authentication import BaseAuthentication

class MockAuth(BaseAuthentication):
    def authenticate(self, request):
        user = MongoUser({
            '_id': '6a3a31827d3e38e045bf9b1f',
            'role': 'seller',
            'name': 'Test Seller',
            'email': 'test_seller@winkart.com'
        })
        return (user, None)

class MyExportView(BulkExportDataView):
    def dispatch(self, request, *args, **kwargs):
        print("MyExportView dispatch called!")
        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request, *args, **kwargs):
        print("MyExportView get called!")
        try:
            res = super().get(request, *args, **kwargs)
            print("super().get returned:", res)
            return res
        except Exception as e:
            import traceback
            print("super().get raised exception:")
            traceback.print_exc()
            raise e

def test_view():
    rf = RequestFactory()
    req = rf.get('/api/operations/products/export/', {'type': 'bills', 'export_format': 'excel'})
    
    MyExportView.authentication_classes = [MockAuth]
    view = MyExportView.as_view()
    
    try:
        resp = view(req)
        print("STATUS:", resp.status_code)
        print("DATA:", resp.data if hasattr(resp, 'data') else resp.content)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_view()
