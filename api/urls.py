from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),

    path("predict/", views.PredictIC50View.as_view(), name="predict"),

    path("compounds/", views.CompoundListView.as_view(), name="compound-list"),
    path("compounds/base/", views.CompoundBaseView.as_view(), name="compound-base"),
    path("compounds/<int:compound_id>/", views.CompoundDetailView.as_view(), name="compound-detail"),
    path("compounds/<int:compound_id>/delete/", views.CompoundDeleteView.as_view(), name="compound-delete"),
    
    path("predictions/", views.PredictionListView.as_view(), name="prediction-list"),
    path("predictions/<int:prediction_id>/", views.PredictionDetailView.as_view(), name="prediction-detail"),
    path("predictions/<int:prediction_id>/delete/", views.PredictionDeleteView.as_view(), name="prediction-delete"),

    path("health-check/", views.HealthCheckView.as_view(), name="health-check"),
    path("db-health-check/", views.DBHealthCheckView.as_view(), name="db-health-check"),
]