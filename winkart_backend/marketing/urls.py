from django.urls import path
from marketing.views import ConfigureRecommendationsView, FetchRecommendationsView

urlpatterns = [
    path('recommendations/configure/', ConfigureRecommendationsView.as_view(), name='configure-recommendations'),
    path('recommendations/<str:product_id>/', FetchRecommendationsView.as_view(), name='fetch-recommendations'),
]
