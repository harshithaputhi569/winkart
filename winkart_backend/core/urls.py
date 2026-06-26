from django.urls import path
from core.views import (
    CategoryListCreateView,
    CategoryDetailView,
    ShopListView,
    ShopDetailView,
    ProductListCreateView,
    ProductDetailView,
    BannerListCreateView,
    BannerDetailView
)

urlpatterns = [
    path('categories/', CategoryListCreateView.as_view(), name='categories-list'),
    path('categories/<str:category_id>/', CategoryDetailView.as_view(), name='categories-detail'),
    path('shops/', ShopListView.as_view(), name='shops-list'),
    path('shops/<str:shop_id>/', ShopDetailView.as_view(), name='shops-detail'),
    path('products/', ProductListCreateView.as_view(), name='products-list'),
    path('products/<str:product_id>/', ProductDetailView.as_view(), name='products-detail'),
    path('banners/', BannerListCreateView.as_view(), name='banners-list'),
    path('banners/<str:banner_id>/', BannerDetailView.as_view(), name='banners-detail'),
]
