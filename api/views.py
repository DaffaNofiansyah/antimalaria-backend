from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Compound, Prediction, MLModel
from .serializers import CompoundListSerializer, CompoundDetailSerializer, RegisterSerializer, PredictionSerializer, CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from .utils import predict_ic50
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.conf import settings
import requests
import pubchempy as pcp
from django.http import Http404
# from google.oauth2 import id_token
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Avg

# Create your views here.

class CompoundBaseView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CompoundListSerializer

    def get_queryset(self):
        return Compound.objects.all()

class PredictionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PredictionSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Prediction.objects.all()
        return Prediction.objects.filter(user=self.request.user)

class CompoundListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CompoundListSerializer

    def get_queryset(self):
        prediction_param = self.kwargs.get('prediction_id')  # Get from URL query params
        if not self.request.user.is_staff:
            if not Prediction.objects.filter(user=self.request.user, id=prediction_param).exists():
                return Response(status=status.HTTP_403_FORBIDDEN)
        return Compound.objects.filter(prediction_id=prediction_param)

# Detail view: return all compound data
class CompoundDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CompoundDetailSerializer

    def get_object(self):
        queryset = Compound.objects.all()
        prediction_param = self.kwargs.get('prediction_id')
        compound_param = self.kwargs.get('compound_id')

        if not self.request.user.is_staff:
            if not Prediction.objects.filter(user=self.request.user, id=prediction_param).exists():
                raise Http404

        compound = queryset.filter(prediction_id=prediction_param, id=compound_param).first()
        if compound is None:
            raise Http404
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
        smiles_input = request.data.get("smiles", None)
        model_type = request.data.get("model", None)

        if not smiles_input:
            return Response({"error": "SMILES string(s) are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize input to list
        if isinstance(smiles_input, str):
            smiles_list = [smiles.strip() for smiles in smiles_input.split(",") if smiles.strip()]
        elif isinstance(smiles_input, list):
            smiles_list = [smiles.strip() for smiles in smiles_input]
        else:
            return Response({"error": "Invalid input format. Provide a list or a comma-separated string."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Create a Prediction entry
        prediction = Prediction.objects.create(user=user, model_id=1, jenis_malaria="default")

        results = []
        data = {
            "cid": None, "molecular_formula": None, "molecular_weight": None,
            "iupac_name": None, "inchi": None, "inchikey": None, "description": None,
            "synonyms": None, "structure_image": None, "name": None,
            "category": None
        }
        for smiles in smiles_list:
            ic50 = predict_ic50(smiles, model_type)  # Get predicted IC50

            if ic50 is None:
                results.append({"smiles": smiles, "error": "Invalid SMILES string"})
                continue  # Skip to next

            # Step 2: Fetch compound data from PubChem
            compound_data = self.fetch_pubchem_data(smiles, data)
            category = "Highly Active" if ic50 > 8 else "Moderately Active" if 7 < ic50 <= 8 else "Weakly Active" if 6 < ic50 <= 7 else "Inactive"

            # Step 3: Create a new Compound entry
            compound = Compound.objects.create(
                prediction_id=prediction,
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
            )

            results.append({
                "iupac_name": compound.iupac_name,
                "smiles": smiles,
                "cid": compound.cid,
                "pic50": ic50,
                "category": category,
                "molecular_formula": compound.molecular_formula,
                "molecular_weight": compound.molecular_weight,
                "synonyms": compound.synonyms,
                "inchi": compound.inchi,
                "inchikey": compound.inchikey,
                "structure_image": compound.structure_image,
                "description": compound.description,
            })

        return Response(results, status=status.HTTP_201_CREATED)

    def fetch_pubchem_data(self, smiles, data):
        try:
            compound = pcp.get_compounds(smiles, 'smiles')
            if compound:
                compound = compound[0]  # Get the first matching compound
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

                # Fetch description separately using PubChem REST API
                if compound.cid:
                    description_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{compound.cid}/description/JSON"
                    response = requests.get(description_url)
                    if response.status_code == 200:
                        json_data = response.json()
                        descriptions = json_data.get("InformationList", {}).get("Information", [])
                        
                        # Extract the first available description
                        for item in descriptions:
                            if "Description" in item:
                                data["description"] = item["Description"]
                                break  # Stop after getting the first description
        
        except Exception as e:
            print(f"Error fetching data from PubChem: {e}")

        return data


class StatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_predictions = Prediction.objects.filter(user=request.user).count()
        total_compounds = Compound.objects.filter(prediction_id__user=request.user).count()
        highly_active_count = Compound.objects.filter(prediction_id__user=request.user, category="Highly Active").count()
        moderately_active_count = Compound.objects.filter(prediction_id__user=request.user, category="Moderately Active").count()
        weakly_active_count = Compound.objects.filter(prediction_id__user=request.user, category="Weakly Active").count()
        inactive_count = Compound.objects.filter(prediction_id__user=request.user, category="Inactive").count()
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




