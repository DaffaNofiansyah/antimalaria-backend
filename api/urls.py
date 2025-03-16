from django.urls import path
from django.contrib import admin
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    path("predict/", views.PredictIC50View.as_view(), name="predict"),
    # path("google-login/", views.ExchangeGoogleToken.as_view(), name="exchange-google-token"),
    path("compounds/", views.CompoundBaseView.as_view(), name="compound-list"),
    path("predictions/", views.PredictionListView.as_view(), name="prediction-list"),
    path("predictions/<int:prediction_id>/", views.CompoundListView.as_view(), name="prediction-detail"),
    path("compounds/<int:compound_id>/", views.CompoundDetailView.as_view(), name="compound-detail"),
    path("statistics/", views.StatisticsView.as_view(), name="statistics"),
]