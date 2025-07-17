from rest_framework import viewsets
from .serializers import CompoundSerializer
from rest_framework.permissions import IsAuthenticated
from api.models import Compound  # Adjust the import based on your actual model location

class CompoundViewSet(viewsets.ModelViewSet):
    serializer_class = CompoundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Compound.objects.all()
        return Compound.objects.filter(prediction__user=self.request.user)