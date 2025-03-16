from rest_framework import serializers
from .models import Compound, Prediction
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CompoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compound
        fields = '__all__'


class CompoundListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compound
        fields = ('id', 'iupac_name', 'smiles', 'cid', 'ic50', 'category')


class CompoundDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compound
        fields = '__all__'


class PredictionSerializer(serializers.ModelSerializer):
    # Returns user's full name
    user = serializers.CharField(source='user.username', read_only=True)
    model = serializers.CharField(source='model.name', read_only=True)

    class Meta:
        model = Prediction
        fields = '__all__'


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords must match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom claims
        data.update({
            "username": self.user.username,
            "email": self.user.email
        })
        return data
