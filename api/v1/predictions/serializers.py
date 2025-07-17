from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
#import prediction models if needed
from api.models import Compound, Prediction, PredictionCompound  # Adjust the import based on your actual model location

class CompoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compound
        exclude = ['id', 'created_at']

class PredictionCompoundSerializer(serializers.ModelSerializer):
    compound = CompoundSerializer(read_only=True)
    
    class Meta:
        model = PredictionCompound
        fields = ['id', 'ic50', 'lelp', 'compound']

class PredictionSerializer(serializers.ModelSerializer):
    prediction_compounds = PredictionCompoundSerializer(many=True, read_only=True)

    class Meta:
        model = Prediction  # Replace with your actual prediction model
        fields = [
            "id",
            "user",
            "ml_model",
            "status",
            "input_source_type",
            "created_at",
            "completed_at",
            "prediction_compounds"  # ⬅️ Put this at the bottom
        ]

class PredictionInputSerializer(serializers.Serializer):
    smiles = serializers.CharField(required=False, help_text="Comma-separated SMILES strings")
    file = serializers.FileField(required=False, help_text="CSV file containing SMILES in the first column")
    model_method = serializers.CharField(required=True, help_text="Model method used for prediction")
    model_descriptor = serializers.CharField(required=True, help_text="Model descriptor used for prediction")

    def validate(self, data):
        if not data.get('smiles') and not data.get('file'):
            raise serializers.ValidationError("Either 'smiles' or 'file' must be provided.")
        
        if data.get('file'):
            if not data['file'].name.endswith(('.csv', '.json')):
                raise serializers.ValidationError("File must be a CSV or JSON.")
        
        if not data.get('model_descriptor'):
            raise serializers.ValidationError("Model descriptor is required.")
        
        if not data.get('model_method'):
            raise serializers.ValidationError("Model method is required.")
        
        return data