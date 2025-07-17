from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import LoginSerializer


# api/v1/auth/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

@extend_schema(
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="User registered successfully.",
            response={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "user": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "username": {"type": "string"},
                            "email": {"type": "string"},
                            "role": {"type": "string"},
                        }
                    }
                }
            }
        ),
        400: OpenApiResponse(description="Validation failed")
    },
    examples=[
        OpenApiExample(
            "Register Example",
            value={
                "username": "daffa123",
                "email": "daffa@example.com",
                "password": "password123",
                "password2": "password123"
            },
            request_only=True,
        )
    ]
)
class RegisterView(APIView):
    permission_classes = [AllowAny]  # Allow any user to register

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "User registered successfully.",
                    "user": {
                        "id": str(user.id),
                        "username": user.username,
                        "email": user.email,
                        "role": user.role
                    }
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="Login successful, JWT token returned",
            response={
                "type": "object",
                "properties": {
                    "refresh": {"type": "string"},
                    "access": {"type": "string"},
                    "username": {"type": "string"},
                    "email": {"type": "string"},
                    "id": {"type": "string"},
                    "role": {"type": "string"}
                }
            }
        ),
        401: OpenApiResponse(description="Invalid credentials"),
    },
    examples=[
        OpenApiExample(
            "Login Example",
            value={
                "email": "daffa@example.com",
                "password": "password123"
            },
            request_only=True
        )
    ]
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer