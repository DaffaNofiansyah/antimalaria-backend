from rest_framework import serializers
from api.models import Compound, Prediction, PredictionCompound, MLModel

class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = '__all__'

class CompoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compound
        exclude = ['ic50', 'lelp', 'created_at']

class PredictionSerializer(serializers.ModelSerializer):
    ml_model = MLModelSerializer(read_only=True)
    class Meta:
        model = Prediction
        fields = [
            "id",
            "user",
            "ml_model",
            "status",
            "input_source_type",
            "created_at"
        ]

class PredictionCompoundSerializer(serializers.ModelSerializer):
    compound = CompoundSerializer(read_only=True)
    prediction = PredictionSerializer(read_only=True)
    class Meta:
        model = PredictionCompound
        fields = [
            'id', 'ic50', 'lelp', 'compound', 'prediction'
        ]