from rest_framework import status, viewsets
from rest_framework.views import APIView
import csv
import io
from django.shortcuts import get_object_or_404
from django.utils import timezone
import pubchempy as pcp
import requests

from rest_framework.response import Response
from .serializers import PredictionSerializer, PredictionInputSerializer
from rest_framework.permissions import IsAuthenticated
from api.models import Prediction, Compound, PredictionCompound, MLModel
from .utils import predict_batch_ic50
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiTypes, OpenApiExample

@extend_schema_view(
    list=extend_schema(
        description="Get a list of all predictions (admin) or only your own (user).",
        responses={
            200: OpenApiResponse(
                description="List of predictions.",
                response=PredictionSerializer(many=True)
            ),
            403: OpenApiResponse(description="Forbidden: User not authenticated.")
        }
    ),
    retrieve=extend_schema(
        description="Retrieve a specific prediction by its ID.",
        responses={
            200: OpenApiResponse(
                description="Prediction details.",
                response=PredictionSerializer
            ),
            403: OpenApiResponse(description="Forbidden: You don't have permission."),
            404: OpenApiResponse(description="Prediction not found."),
        }
    ),
    destroy=extend_schema(
        description="Delete a prediction.",
        responses={
            204: OpenApiResponse(description="Deleted successfully."),
            403: OpenApiResponse(description="Forbidden: Not allowed."),
            404: OpenApiResponse(description="Prediction not found.")
        }
    )
)
class PredictionViewSet(viewsets.ModelViewSet):
    """
    API endpoint to retrieve or delete predictions.
    Admins can see all predictions; users can only see their own.
    """
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'delete', 'head', 'options']

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Prediction.objects.all()
        return Prediction.objects.filter(user=self.request.user)






class PredictIC50View(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=PredictionInputSerializer,
        responses={
            200: OpenApiResponse(
                description="Prediction completed successfully.",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="Prediction Success",
                        value={
                            "message": "Prediction complete and saved for 2 SMILES.",
                            "prediction_id": 42,
                            "results": [
                                {
                                    "smiles": "C=C", 
                                    "ic50": 0.00032,
                                    "compound": 
                                    {
                                        "id": "1",
                                        "smiles": "C=C",
                                        "iupac_name": "But-2-ene",
                                        "cid": "1234",
                                        "description": "A simple alkene.",
                                        "molecular_formula": "C4H8",
                                        "molecular_weight": 56.11,
                                        "synonyms": "Butylene, 2-Butene",
                                        "inchi": "InChI=1S/C4H8/c1-3=2/h1-2H,3H2",
                                        "inchikey": "XKQZJYVYQFJZQH-UHFFFAOYSA-N",
                                        "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=1234&t=l"
                                    }
                                },
                                {
                                    "smiles": "CCO",
                                    "ic50": 0.00213,
                                    "compound": 
                                    {
                                        "id": "2",
                                        "smiles": "CCO",
                                        "iupac_name": "Ethanol",
                                        "cid": "5678",
                                        "description": "A simple alcohol.",
                                        "molecular_formula": "C2H6O",
                                        "molecular_weight": 46.07,
                                        "synonyms": "Ethyl alcohol, Ethanol",
                                        "inchi": "InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3",
                                        "inchikey": "LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
                                        "structure_image": "https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid=5678&t=l"
                                    }
                                }
                            ]
                        },
                        status_codes=["200"]
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Bad request.",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="Missing Parameters",
                        value={"error": "model_descriptor and model_method are required."},
                        status_codes=["400"]
                    )
                ]
            )
        },
        description=(
            "Predict IC50 values from SMILES strings or a CSV file using a selected ML model.\n\n"
            "**Supported Models (method + descriptor):**\n"
            "- xgb + ecfp\n"
            "- xgb + pubchem\n"
            "- lgbm + ecfp\n"
            "- lgbm + pubchem\n"
            "- svr + ecfp\n"
            "- svr + pubchem\n"
        )
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        csv_file = request.FILES.get("file", None)
        smiles_input = request.data.get("smiles", None)
        model_descriptor = request.data.get("model_descriptor", None)
        model_method = request.data.get("model_method", None)

        # serializer = PredictionInputSerializer(data={**request.data, **request.FILES})
        # if not serializer.is_valid():
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # validated = serializer.validated_data
        # smiles_input = validated.get("smiles")
        # csv_file = validated.get("file")
        # model_method = validated.get("model_method")
        # model_descriptor = validated.get("model_descriptor")


        errors = {}

        # Validate required fields
        if not model_method:
            errors["model_method"] = ["This field is required."]
        if not model_descriptor:
            errors["model_descriptor"] = ["This field is required."]
        if not smiles_input and not csv_file:
            errors["input"] = ["Either 'smiles' or 'file' must be provided."]

        # If errors, return
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        smiles_list = []

        # Validate required parameters
        if not all([model_descriptor, model_method]):
            return Response(
                {"error": "model_descriptor and model_method are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch MLModel in one query
        ml_model = get_object_or_404(MLModel, file_path="xgb_model_ecfp.json")

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

        seen = set()
        smiles_list = [s for s in smiles_list if not (s in seen or seen.add(s))]

        if not smiles_list:
            return Response({"error": "No valid SMILES strings provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            predictions = predict_batch_ic50(
                smiles_list=smiles_list,
                model_name="xgb_model_ecfp.json",
                model_method="xgb",
                model_descriptor="ecfp"
            )

            # results = [{"smiles": smiles, "ic50": ic50} for smiles, ic50 in zip(smiles_list, predictions)]

            # 1. Create Prediction instance
            prediction = Prediction.objects.create(
                user=user,
                ml_model=ml_model,
                status=Prediction.Status.COMPLETED,
                input_source_type="csv" if csv_file else "text",
                completed_at=timezone.now()  # Set completed_at to now
            )

            results = []
            # 2. Save Compounds and PredictionCompound results
            for smiles, ic50 in zip(smiles_list, predictions):
                compound, _ = Compound.objects.get_or_create(
                    smiles=smiles,
                    defaults={
                        "iupac_name": None,  # optional fields, fill if available
                        "cid": None,
                        "description": None,
                    }
                )

                PredictionCompound.objects.create(
                    prediction=prediction,
                    compound=compound,
                    ic50=ic50,
                    lelp=None  # fill this if you calculate LELP
                )

                results.append({
                    "smiles": smiles,
                    "ic50": ic50,
                    "compound": {
                        "id": compound.id,
                        "smiles": compound.smiles,
                        "iupac_name": compound.iupac_name,
                        "cid": compound.cid,
                        "description": compound.description,
                        "molecular_formula": compound.molecular_formula,
                        "molecular_weight": compound.molecular_weight,
                        "synonyms": compound.synonyms,
                        "inchi": compound.inchi,
                        "inchikey": compound.inchikey,
                        "structure_image": compound.structure_image
                    }
                })

            return Response({
                "message": f"Prediction complete and saved for {len(results)} SMILES.",
                "prediction_id": prediction.id,
                "results": results
            }, status=status.HTTP_200_OK)
        

        except ValueError as e:
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

        # return Response({
        #     "message": "Prediction created successfully",
        #     "prediction_id": prediction_instance.id,
        #     "compounds": CompoundSerializer(compounds_to_create, many=True).data
        # }, status=status.HTTP_201_CREATED)
    
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