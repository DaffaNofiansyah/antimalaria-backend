from rest_framework import serializers
from api.models import Compound, Prediction, PredictionCompound

class CompoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compound
        exclude = ['id', 'created_at']

class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = '__all__'

class PredictionCompoundSerializer(serializers.ModelSerializer):
    compound = CompoundSerializer(read_only=True)
    prediction = PredictionSerializer(read_only=True)
    class Meta:
        model = PredictionCompound
        fields = [
            'id', 'ic50', 'lelp', 'compound', 'prediction'
        ]