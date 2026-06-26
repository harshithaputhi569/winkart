from django.urls import path
from authentication.views import (
    CustomerRegisterView,
    SellerRegisterView,
    LoginView,
    TokenRefreshView,
    ProfileView,
    SellerSettingsView,
    MediaUploadView
)

urlpatterns = [
    path('register/customer/', CustomerRegisterView.as_view(), name='customer-register'),
    path('register/seller/', SellerRegisterView.as_view(), name='seller-register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('seller/settings/', SellerSettingsView.as_view(), name='seller-settings'),
    path('upload/', MediaUploadView.as_view(), name='media-upload'),
]
