from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from .models import Compound, Prediction, MLModel
from .serializers import CompoundSerializer, RegisterSerializer, PredictionSerializer, CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
# from .utils import predict_ic50
import requests
import pubchempy as pcp
from django.http import Http404
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
import csv
import io
import environ
from pathlib import Path
# from .utils import predict_ic50
import time # Import time
import logging # Import logging
LOGGER = logging.getLogger(__name__)

env = environ.Env()
environ.Env.read_env(Path(__file__).resolve().parent.parent / '.env')

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
    
from .utils import predict_batch_ic50 # Import the new batch function

class PredictIC50View(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        view_start_time = time.perf_counter()

        user = request.user
        csv_file = request.FILES.get("file", None)
        smiles_input = request.data.get("smiles", None)
        model_descriptor = request.data.get("model_descriptor", None)
        model_method = request.data.get("model_method", None)

        # Validate required parameters
        if not all([model_descriptor, model_method]):
            return Response(
                {"error": "model_descriptor and model_method are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch MLModel in one query
        ml_model = get_object_or_404(MLModel, method=model_method, descriptor=model_descriptor)

        parse_start_time = time.perf_counter()
        smiles_list = []
        if csv_file:
            if not csv_file.name.endswith(".csv"):
                return Response({"error": "Only CSV files are supported."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                decoded_file = csv_file.read().decode("utf-8-sig")
                io_string = io.StringIO(decoded_file)
                reader = csv.reader(io_string)
                # Assumes SMILES is in the first column
                smiles_list = [row[0].strip() for row in reader if row and row[0].strip()]
            except Exception as e:
                return Response({"error": f"Failed to parse CSV: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        elif smiles_input:
            if isinstance(smiles_input, str):
                smiles_list = [s.strip() for s in smiles_input.split(",") if s.strip()]
            elif isinstance(smiles_input, list):
                smiles_list = [s.strip() for s in smiles_input if isinstance(s, str) and s.strip()]
            else:
                return Response({"error": "SMILES input must be a comma-separated string or a list of strings."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Provide either a 'smiles' field or a 'file' (CSV)."}, status=status.HTTP_400_BAD_REQUEST)
        parse_end_time = time.perf_counter()
        LOGGER.info(f"[TIMING] Input parsing and validation: {(parse_end_time - parse_start_time) * 1000:.4f} ms")

        if not smiles_list:
            return Response({"error": "No valid SMILES strings provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the single, powerful batch prediction function
            prediction_call_start_time = time.perf_counter()
            predictions = predict_batch_ic50(
                smiles_list=smiles_list,
                model_name=ml_model.name,
                model_method=model_method,
                model_descriptor=model_descriptor
            )
            prediction_call_end_time = time.perf_counter()
            LOGGER.info(f"[TIMING] 'predict_batch_ic50' call from view: {(prediction_call_end_time - prediction_call_start_time) * 1000:.4f} ms")
            # Format the results

            response_format_start_time = time.perf_counter()
            results = [{"smiles": smiles, "ic50": ic50} for smiles, ic50 in zip(smiles_list, predictions)]
            response_format_end_time = time.perf_counter()
            LOGGER.info(f"[TIMING] Final response formatting: {(response_format_end_time - response_format_start_time) * 1000:.4f} ms")

            view_end_time = time.perf_counter()
            LOGGER.info(f"[TIMING] Total view processing time (end-to-end): {(view_end_time - view_start_time) * 1000:.4f} ms")

            return Response({
                "message": f"Prediction complete for {len(results)} SMILES.",
                "results": results
            }, status=status.HTTP_200_OK) # Use 200 OK for successful processing
        

        except ValueError as e:
            # Catches errors from utils like 'Model not found'
            LOGGER.error(f"Prediction failed with ValueError: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


            
        
        # try:
        #     response = requests.post(env('ML_SERVICE_URL'), json={
        #         "smiles": smiles_list,
        #         "model_name": ml_model.name,
        #         "model_descriptor": model_descriptor,
        #         "model_method": model_method
        #     })
        #     response.raise_for_status()  # Raise an error for bad responses
        #     prediction_result = response.json()
        # except requests.RequestException as e:
        #     raise APIException(f"Failed to connect to prediction service: {e}")
        # except ValueError:
        #     raise APIException("Invalid JSON response from prediction service")

        # try:
        #     prediction_instance = Prediction.objects.create(
        #         user=user,
        #         model=ml_model,
        #         jenis_malaria="default",
        #     )
        # except IntegrityError as e:
        #     raise APIException(f"Failed to create prediction instance: {e}")

        # compounds_to_create = []
        # results = []

        # for prediction in prediction_result:
        #     compounds_to_create.append(
        #         Compound(
        #             prediction=prediction_instance,
        #             **prediction,  # Unpack the prediction dictionary directly
        #             # name=prediction.get("name", ""),
        #             # smiles=prediction.get("smiles", ""),
        #             # cid=prediction.get("cid", None),
        #             # ic50=prediction.get("ic50", None),
        #             # category=prediction.get("category", "Unknown"),
        #             # molecular_formula=prediction.get("molecular_formula", ""),
        #             # molecular_weight=prediction.get("molecular_weight", ""),
        #             # iupac_name=prediction.get("iupac_name", ""),
        #             # synonyms=prediction.get("synonyms", ""),
        #             # inchi=prediction.get("inchi", ""),
        #             # inchikey=prediction.get("inchikey", ""),
        #             # structure_image=prediction.get("structure_image", ""),
        #             # description=prediction.get("description", ""),
        #         )
        #     )
            
        # try:
        #     with transaction.atomic():
        #         Compound.objects.bulk_create(compounds_to_create)
        # except IntegrityError as e:
        #     raise APIException(f"Failed to save compound data: {e}")

        return Response({
            "message": "Prediction created successfully",
            "prediction_id": prediction_instance.id,
            "compounds": CompoundSerializer(compounds_to_create, many=True).data
        }, status=status.HTTP_201_CREATED)
    
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
    
# dummy view to check ttfb
class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

# db query health check
class DBHealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # Perform a simple query to check database connectivity
            Compound.objects.count()
            return Response({"status": "ok"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


class PubChemHealthCheckView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Placeholder compound names for testing
        compound_cid = ["2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244", "2244"]
        if not compound_cid:
            return Response({"error": "No compound cid provided."}, status=status.HTTP_400_BAD_REQUEST)

        compound_str = ','.join(compound_cid)
        try:
            result = fetch_pubchem_batch(compound_str)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

import pprint
def fetch_pubchem_batch(compound_str):
    print(f"Fetching PubChem data for compounds: {compound_str}")
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/property/MolecularWeight,InChIKey/JSON"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"cid": compound_str}
    response = requests.post(url, headers=headers, data=data, timeout=15)
    pprint.pprint(f"PubChem response: {response.json()}")
    if response.status_code == 200:
        parsed = response.json()
        properties = parsed.get("PropertyTable", {}).get("Properties", [])
        # Map results by compound name
        result_map = {}
        for item in properties:
            name = item.get("IUPACName") or "Unknown"
            result_map[name] = {
                "MolecularWeight": item.get("MolecularWeight"),
                "InChIKey": item.get("InChIKey")
            }
        return result_map
    else:
        raise Exception(f"PubChem API error: {response.status_code} - {response.text}")

#
