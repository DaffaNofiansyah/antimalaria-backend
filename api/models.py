import uuid
from django.db import models
from django.contrib.auth.models import User  # Import User model

class MLModel(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)  # Nullable and optional
    method = models.CharField(max_length=255, null=True, blank=True)  # Nullable and optional
    descriptor= models.CharField(max_length=255, null=True, blank=True)  # Nullable and optional
    version = models.CharField(max_length=50)  # Versi model
    file_path = models.CharField(max_length=255, null=True, blank=True)
    training_date = models.DateTimeField()  # Tanggal pelatihan model
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp otomatis saat dibuat

    def __str__(self):
        return f"{self.name} v{self.version}"

class Prediction(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ml_model = models.ForeignKey(MLModel, on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    input_source_type = models.CharField(max_length=50, null=True, blank=True) # e.g., 'csv', 'text'
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True) # Will be set by the collector task.

    def __str__(self):
        return f"Prediction Job {self.id} ({self.status})"

class Compound(models.Model):
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

# This model corresponds to the 'prediction_compounds' table in your ERD.
# It's the crucial linking table that stores the result of one compound in one job.
class PredictionCompound(models.Model):
    # ForeignKeys creating the many-to-many relationship.
    prediction = models.ForeignKey(Prediction, related_name='prediction_compounds', on_delete=models.CASCADE)
    compound = models.ForeignKey(Compound, related_name='predictions', on_delete=models.CASCADE)
    
    # The actual predicted values.
    ic50 = models.FloatField(null=True, blank=True)
    lelp = models.FloatField(null=True, blank=True)

    class Meta:
        # This constraint ensures you don't save a result for the same
        # compound twice within the same prediction job.
        unique_together = ('prediction', 'compound')

    def __str__(self):
        return f"Result for {self.compound.name} in Job {self.prediction.id}"