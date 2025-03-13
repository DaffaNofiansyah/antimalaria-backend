from django.db import models
from django.contrib.auth.models import User  # Import User model

class MLModel(models.Model):
    name = models.CharField(max_length=255)  # Nama model ML
    version = models.CharField(max_length=50)  # Versi model
    file_path = models.CharField(max_length=255, null=True, blank=True)
    training_date = models.DateTimeField()  # Tanggal pelatihan model
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp otomatis saat dibuat

    def __str__(self):
        return f"{self.name} v{self.version}"

class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Relasi ke User
    model_id = models.CharField(max_length=255)  # ID model yang digunakan
    jenis_malaria = models.CharField(max_length=255)  # Jenis malaria (Plasmodium, Vivax, dll.)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp otomatis saat dibuat

    def __str__(self):
        return f"{self.user.username} - {self.jenis_malaria} ({self.model_id})"

class Compound(models.Model):
    prediction_id = models.ForeignKey(Prediction, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)  # Nullable and optional
    cid = models.CharField(max_length=50, null=True, blank=True)  # Nullable and optional
    smiles = models.TextField(null=True, blank=True)  # Unique identifier
    ic50 = models.FloatField(null=True, blank=True)  # Nullable and optional
    lelp = models.FloatField(null=True, blank=True)  # Nullable and optional
    category = models.CharField(max_length=255, null=True, blank=True)  
    description = models.TextField(null=True, blank=True)  # Store actual description text  
    molecular_formula = models.CharField(max_length=255, null=True, blank=True)  
    molecular_weight = models.FloatField(null=True, blank=True)  # Store as a number  
    iupac_name = models.CharField(max_length=255, null=True, blank=True)  
    synonyms = models.TextField(null=True, blank=True)  # Can store multiple synonyms  
    inchi = models.TextField(null=True, blank=True)  # Usually a long string  
    inchikey = models.CharField(max_length=255, null=True, blank=True)  
    structure_image = models.URLField(null=True, blank=True)  # Keep as URL  
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return self.name
