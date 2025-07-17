from rest_framework import status, viewsets
from .serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        description="Get a list of users (admin only). Regular users only see their own data.",
        responses={
            200: OpenApiResponse(
                description="List of users.",
                response=UserSerializer(many=True)
            ),
            403: OpenApiResponse(description="Forbidden: Not allowed."),
        }
    ),
    retrieve=extend_schema(
        description="Retrieve a user's details. Regular users can only access their own data.",
        responses={
            200: OpenApiResponse(
                description="User details.",
                response=UserSerializer
            ),
            403: OpenApiResponse(description="Forbidden: Not allowed."),
            404: OpenApiResponse(description="User not found."),
        }
    ),
    destroy=extend_schema(
        description="Delete a user (admin only).",
        responses={
            204: OpenApiResponse(description="User deleted successfully."),
            403: OpenApiResponse(description="Forbidden: Not allowed."),
            404: OpenApiResponse(description="User not found.")
        }
    ),
    partial_update=extend_schema(
        description="Update the password for the current user. Requires both `password` and `password2` fields.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "password": {"type": "string"},
                    "password2": {"type": "string"},
                },
                "required": ["password", "password2"]
            }
        },
        responses={
            200: OpenApiResponse(description="Password has been changed."),
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Forbidden: Not allowed."),
        }
    )
)
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        if self.request.user.role != 'admin':
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user.role != 'admin' and obj.id != self.request.user.id:
            raise PermissionDenied("You do not have permission to access this user.")
        return obj
    
    def destroy(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            raise PermissionDenied("Only admin can delete users.")
        return super().destroy(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        password = request.data.get("password")
        password2 = request.data.get("password2")

        if not password or not password2:
            return Response(
                {"detail": "Both password and password2 are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if password != password2:
            return Response(
                {"detail": "Passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(password, user)
        except ValidationError as e:
            return Response(
                {"detail": e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(password)
        user.save()

        return Response(
            {"message": "Password has been changed."},
            status=status.HTTP_200_OK
        )


    