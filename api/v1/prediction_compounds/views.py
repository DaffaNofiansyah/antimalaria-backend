from rest_framework import viewsets
from .serializers import PredictionCompoundSerializer
from rest_framework.permissions import IsAuthenticated
from api.models import PredictionCompound  # Adjust the import based on your actual model location
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

@extend_schema_view(
    list=extend_schema(
        description="Retrieve a list of prediction compound records. Admins see all data; users see only their own.",
        responses={
            200: OpenApiResponse(
                description="List of prediction compounds.",
                response=PredictionCompoundSerializer(many=True)
            ),
            403: OpenApiResponse(description="Permission denied.")
        }
    ),
    retrieve=extend_schema(
        description="Get a specific prediction compound by ID. Access restricted to owners or admin.",
        responses={
            200: OpenApiResponse(
                description="Prediction compound details.",
                response=PredictionCompoundSerializer
            ),
            404: OpenApiResponse(description="Prediction compound not found."),
            403: OpenApiResponse(description="Permission denied.")
        }
    ),
    destroy=extend_schema(
        description="Delete a prediction compound entry. Only accessible to owners or admin.",
        responses={
            204: OpenApiResponse(description="Prediction compound deleted successfully."),
            404: OpenApiResponse(description="Prediction compound not found."),
            403: OpenApiResponse(description="Permission denied.")
        }
    ),
)
class PredictionCompoundViewSet(viewsets.ModelViewSet):
    serializer_class = PredictionCompoundSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'delete', 'head', 'options']

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return PredictionCompound.objects.all()
        return PredictionCompound.objects.filter(prediction__user=self.request.user)