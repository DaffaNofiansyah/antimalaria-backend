from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PredictionViewSet, PredictIC50View

router = DefaultRouter()
router.register(r'', PredictionViewSet, basename='predictions')


urlpatterns = [
  path('predict/', PredictIC50View.as_view(), name='predict'),
  path('', include(router.urls)),
]