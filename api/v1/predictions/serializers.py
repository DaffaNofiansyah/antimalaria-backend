from rest_framework import serializers
from api.models import Compound, Prediction, PredictionCompound, MLModel
class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = '__all__'  # Include all fields of the MLModel

class CompoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compound
        exclude = ['ic50', 'lelp', 'created_at']  # Exclude fields that are not needed in the serializer

class PredictionCompoundSerializer(serializers.ModelSerializer):
    compound = CompoundSerializer(read_only=True)
    
    class Meta:
        model = PredictionCompound
        fields = ['id', 'ic50', 'lelp', 'compound']

class PredictionSerializer(serializers.ModelSerializer):
    prediction_compounds = PredictionCompoundSerializer(many=True, read_only=True)
    ml_model = MLModelSerializer(read_only=True)

    class Meta:
        model = Prediction  # Replace with your actual prediction model
        fields = [
            "id",
            "user",
            "ml_model",
            "status",
            "input_source_type",
            "created_at",
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