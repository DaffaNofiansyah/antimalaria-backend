from rest_framework import serializers
from django.contrib.auth import get_user_model
from api.models import Compound, Prediction, PredictionCompound  # Adjust the import based on your actual model location

User = get_user_model()

class CompoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compound
        fields = ['__all__']

class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = ['__all__'] 


class PredictionCompoundSerializer(serializers.ModelSerializer):
    compound = CompoundSerializer(read_only=True)
    prediction = PredictionSerializer(read_only=True)

    class Meta:
        model = PredictionCompound
        fields = '__all__'