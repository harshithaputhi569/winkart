from django.urls import path
from operations.views import (
    CartView,
    CheckoutView,
    CustomerBillsListView,
    SellerBillsListView,
    BillDetailView,
    DownloadInvoiceView,
    BulkImportProductsView,
    BulkExportDataView,
    ImportHistoryLogView
)

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('bills/customer/', CustomerBillsListView.as_view(), name='customer-bills'),
    path('bills/seller/', SellerBillsListView.as_view(), name='seller-bills'),
    path('bills/<str:bill_id>/', BillDetailView.as_view(), name='bill-detail'),
    path('bills/<str:bill_id>/download/', DownloadInvoiceView.as_view(), name='download-invoice'),
    path('products/import/', BulkImportProductsView.as_view(), name='products-import'),
    path('products/export/', BulkExportDataView.as_view(), name='products-export'),
    path('products/import/history/', ImportHistoryLogView.as_view(), name='import-history'),
]
