from rest_framework import generics, status
from rest_framework.response import Response
from .models import Compound, Prediction, MLModel
from .serializers import CompoundSerializer, RegisterSerializer, PredictionSerializer, CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .utils import predict_ic50
import requests
import pubchempy as pcp
from django.http import Http404
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
import csv
import io


# Create your views here.

class CompoundBaseView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CompoundSerializer

    def get_queryset(self):
        return Compound.objects.select_related("prediction").filter(prediction=None)

class PredictionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PredictionSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Prediction.objects.select_related("user", "model").all()
        return Prediction.objects.select_related("user", "model").filter(user=self.request.user)

class PredictionDetailView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CompoundSerializer

    def get_queryset(self):
        prediction_id = self.kwargs.get('prediction_id')  # Get from URL params

        # Fetch prediction instance in one query
        prediction = get_object_or_404(Prediction, id=prediction_id)

        # If user is not staff, ensure they own the prediction
        if not self.request.user.is_staff and prediction.user != self.request.user:
            raise PermissionDenied("You do not have permission to access this resource.")

        # Optimize query by filtering using the prediction instance
        return Compound.objects.filter(prediction=prediction).select_related("prediction")

# Detail view: return all compound data
class CompoundDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CompoundSerializer

    def get_object(self):
        queryset = Compound.objects.all()
        compound_param = self.kwargs.get('compound_id')

        compound = queryset.filter(id=compound_param).first()
        if compound is None:
            raise Http404

        # If the compound is associated with a prediction (not public)
        if compound.prediction:
            if not self.request.user.is_staff and compound.prediction.user != self.request.user:
                raise Http404  # User doesn't have permission

        return compound


class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "User registered successfully"
        }, status=status.HTTP_201_CREATED)
    

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
class PredictIC50View(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        csv_file = request.FILES.get("file", None)
        smiles_input = request.data.get("smiles", None)
        model_descriptor = request.data.get("model_descriptor", None)
        model_method = request.data.get("model_method", None)

        # Fetch MLModel in one query
        ml_model = get_object_or_404(MLModel, method=model_method, descriptor=model_descriptor)

        smiles_list = []

        if csv_file:
            if not csv_file.name.endswith(".csv"):
                return Response({"error": "Only CSV files are supported."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                decoded_file = csv_file.read().decode("utf-8-sig")
                io_string = io.StringIO(decoded_file)
                reader = csv.reader(io_string)
                for row in reader:
                    if row:  # skip empty rows
                        smiles_list.append(row[0].strip())
            except Exception as e:
                return Response({"error": f"Failed to parse CSV: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        elif smiles_input:
            if isinstance(smiles_input, str):
                smiles_list = [smiles.strip() for smiles in smiles_input.split(",") if smiles.strip()]
            elif isinstance(smiles_input, list):
                smiles_list = [smiles.strip() for smiles in smiles_input]
            else:
                return Response({"error": "Invalid input format. Provide a list, string, or a CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"error": "Provide either SMILES or a CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Create a Prediction entry
        prediction = Prediction.objects.create(user=user, model=ml_model, jenis_malaria="default")

        results = []
        compounds_to_create = []

        # Step 2: Process all SMILES
        for smiles in smiles_list:
            ic50 = predict_ic50(smiles, ml_model.name, model_method, model_descriptor)  # Get predicted IC50

            if ic50 is None:
                results.append({"smiles": smiles, "error": "Invalid SMILES string"})
                continue  # Skip to next

            # Fetch compound data from PubChem
            compound_data = self.fetch_pubchem_data(smiles)

            # Determine activity category
            category = (
                "Highly Active" if ic50 > 8 else
                "Moderately Active" if 7 < ic50 <= 8 else
                "Weakly Active" if 6 < ic50 <= 7 else
                "Inactive"
            )

            # Prepare compound for bulk insert
            compounds_to_create.append(Compound(
                prediction=prediction,
                name=compound_data.get("name", ""),
                smiles=smiles,
                cid=compound_data.get("cid", None),
                ic50=ic50,
                category=category,
                molecular_formula=compound_data.get("molecular_formula", ""),
                molecular_weight=compound_data.get("molecular_weight", ""),
                iupac_name=compound_data.get("iupac_name", ""),
                synonyms=compound_data.get("synonyms", ""),
                inchi=compound_data.get("inchi", ""),
                inchikey=compound_data.get("inchikey", ""),
                structure_image=compound_data.get("structure_image", ""),
                description=compound_data.get("description", ""),
            ))

        # Step 3: Bulk insert compounds to minimize DB queries
        with transaction.atomic():
            Compound.objects.bulk_create(compounds_to_create)

        # Convert inserted compounds into response format
        for compound in compounds_to_create:
            results.append({
                "id": compound.id,
                "iupac_name": compound.iupac_name,
                "smiles": compound.smiles,
                "cid": compound.cid,
                "ic50": compound.ic50,
                "category": compound.category,
                "molecular_formula": compound.molecular_formula,
                "molecular_weight": compound.molecular_weight,
                "synonyms": compound.synonyms,
                "inchi": compound.inchi,
                "inchikey": compound.inchikey,
                "structure_image": compound.structure_image,
                "description": compound.description,
            })

        return Response(results, status=status.HTTP_201_CREATED)

    def fetch_pubchem_data(self, smiles):
        """Fetch compound data from PubChem and optimize API calls."""
        data = {
            "cid": None, "molecular_formula": None, "molecular_weight": None,
            "iupac_name": None, "inchi": None, "inchikey": None, "description": None,
            "synonyms": None, "structure_image": None, "name": None,
            "category": None
        }
        
        try:
            compounds = pcp.get_compounds(smiles, 'smiles')
            if compounds:
                compound = compounds[0]  # Get the first matching compound
                data.update({
                    "cid": compound.cid,
                    "molecular_formula": compound.molecular_formula,
                    "molecular_weight": compound.molecular_weight,
                    "iupac_name": compound.iupac_name,
                    "inchi": compound.inchi,
                    "inchikey": compound.inchikey,
                    "synonyms": ", ".join(compound.synonyms) if compound.synonyms else None,
                    "structure_image": f"https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid={compound.cid}&t=l" if compound.cid else None,
                })

                # Fetch description from PubChem REST API
                if compound.cid:
                    description = self.fetch_pubchem_description(compound.cid)
                    if description:
                        data["description"] = description
                        
        except Exception as e:
            print(f"Error fetching data from PubChem: {e}")

        return data

    def fetch_pubchem_description(self, cid):
        """Fetch compound description from PubChem API."""
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/description/JSON"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                json_data = response.json()
                descriptions = json_data.get("InformationList", {}).get("Information", [])
                for item in descriptions:
                    if "Description" in item:
                        return item["Description"]
        except requests.RequestException as e:
            print(f"Error fetching description from PubChem: {e}")
        return None


class StatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_predictions = Prediction.objects.filter(user=request.user).count()
        total_compounds = Compound.objects.filter(prediction__user=request.user).count()
        highly_active_count = Compound.objects.filter(prediction__user=request.user, category="Highly Active").count()
        moderately_active_count = Compound.objects.filter(prediction__user=request.user, category="Moderately Active").count()
        weakly_active_count = Compound.objects.filter(prediction__user=request.user, category="Weakly Active").count()
        inactive_count = Compound.objects.filter(prediction__user=request.user, category="Inactive").count()
        # avg_ic50 = Compound.objects.filter(prediction_id__user=request.user).aggregate(avg_ic50=Avg("ic50"))["avg_ic50"]

        return Response({
            "predictions": {
                "total predictions": total_compounds,
            },
            "compounds": {
                "total compounds": total_predictions,
                "categories": {
                    "active": highly_active_count,
                    "moderately active": moderately_active_count,
                    "weakly active": weakly_active_count,
                    "inactive": inactive_count
                },
            },
            # "average_ic50": avg_ic50,
        }, status=status.HTTP_200_OK)


class CompoundDeleteView(generics.DestroyAPIView):
    """
    API view to delete a Compound instance.
    Requires authentication.
    The 'compound_id' in the URL will be used for lookup.
    """
    permission_classes = [IsAuthenticated] # Or your custom permissions
    lookup_field = 'id'
    lookup_url_kwarg = 'compound_id' # This must match <int:compound_id> in urls.py

    def get_queryset(self):
        """
        This method is called to get the base queryset for the view.
        Ensure your Compound model is imported correctly.
        """
        # Make sure to import your Compound model correctly from your app's models.py
        # from .models import Compound # Example: from myapp.models import Compound
        return Compound.objects.all()

    def perform_destroy(self, instance):
        """
        Called when deleting an instance.
        Default behavior is instance.delete().
        You can add custom logic here if needed.
        """
        # Example: Log the deletion
        # print(f"Deleting Compound: {instance.id} (Name: {instance.name}) by user {self.request.user}")
        super().perform_destroy(instance)
        # No need to manually handle Prediction deletion here, as a Compound is standalone or linked from Prediction.

class PredictionDeleteView(generics.DestroyAPIView):
    """
    API view to delete a Prediction instance.
    Deleting a Prediction will also delete associated Compound objects
    due to on_delete=models.CASCADE in the Compound.prediction ForeignKey.
    Requires authentication.
    The 'prediction_id' in the URL will be used for lookup.
    """
    permission_classes = [IsAuthenticated] # Or your custom permissions
    lookup_field = 'id'
    lookup_url_kwarg = 'prediction_id' # This must match <int:prediction_id> in urls.py

    def get_queryset(self):
        """
        This method is called to get the base queryset for the view.
        Ensure your Prediction model is imported correctly.
        """
        # Make sure to import your Prediction model correctly from your app's models.py
        # from .models import Prediction # Example: from myapp.models import Prediction
        return Prediction.objects.all()

    def perform_destroy(self, instance):
        """
        Called when deleting an instance.
        Default behavior is instance.delete().
        Associated Compound objects are deleted automatically by the database
        due to `on_delete=models.CASCADE` on the `Compound.prediction` ForeignKey.
        """
        # Example: Log the deletion
        # print(f"Deleting Prediction: {instance.id} (Jenis: {instance.jenis_malaria}) by user {self.request.user}")
        # print(f"Associated compounds for prediction {instance.id} will also be deleted due to on_delete=CASCADE.")
        super().perform_destroy(instance)


class CompoundListView(generics.ListAPIView):
    serializer_class = CompoundSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Compound.objects.filter(prediction__user=self.request.user).distinct().order_by('-created_at')
        return Compound.objects.none()