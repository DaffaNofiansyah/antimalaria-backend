from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PredictionCompoundViewSet

router = DefaultRouter()
router.register(r'', PredictionCompoundViewSet, basename='prediction_compounds')

urlpatterns = [
    path('', include(router.urls)),
]