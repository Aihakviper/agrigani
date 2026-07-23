"""
Database models for AgriGani Core application.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Farmer(models.Model):
    """
    Represents a farmer using the AgriGani platform.
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    full_name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='farmers',
        blank=True,
        null=True,
        help_text="Account that owns this farmer profile"
    )
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    location = models.CharField(max_length=255, help_text="Village, LGA, State")
    region_code = models.CharField(max_length=50, help_text="e.g., NG-KD (Kaduna), NG-KN (Kano)")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    farm_size_hectares = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Farm size in hectares"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farmers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['region_code']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"


class Disease(models.Model):
    """
    Represents a crop or livestock disease.
    """
    CATEGORY_CHOICES = [
        ('CROP', 'Crop Disease'),
        ('LIVESTOCK', 'Livestock Disease'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    scientific_name = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='CROP')
    description = models.TextField()
    symptoms = models.TextField(help_text="Common symptoms of the disease")
    causes = models.TextField(blank=True, help_text="What causes this disease")
    prevention_tips = models.TextField(blank=True)
    severity_level = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Low, 5=Critical"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'diseases'
        ordering = ['name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class Treatment(models.Model):
    """
    Treatment recommendations for a specific disease.
    """
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='treatments')
    medicine_name = models.CharField(max_length=255)
    active_ingredient = models.CharField(max_length=255, blank=True)
    dosage = models.TextField(help_text="Recommended dosage")
    application_method = models.TextField(help_text="How to apply the treatment")
    frequency = models.CharField(max_length=255, help_text="e.g., 'Every 7 days'")
    duration = models.CharField(max_length=255, help_text="e.g., '3 weeks'")
    precautions = models.TextField(blank=True)
    effectiveness_rating = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Low, 5=Highly Effective"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'treatments'
        ordering = ['-effectiveness_rating']
    
    def __str__(self):
        return f"{self.medicine_name} for {self.disease.name}"


class Vendor(models.Model):
    """
    Agro-medicine vendors and veterinary clinics.
    """
    VENDOR_TYPE_CHOICES = [
        ('AGRO_DEALER', 'Agricultural Input Dealer'),
        ('VET_CLINIC', 'Veterinary Clinic'),
        ('PHARMACY', 'Agricultural Pharmacy'),
    ]
    
    name = models.CharField(max_length=255)
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPE_CHOICES)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    location = models.CharField(max_length=255, help_text="Village, LGA, State")
    region_code = models.CharField(max_length=50, help_text="e.g., NG-KD")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendors'
        ordering = ['-is_verified', '-rating']
        indexes = [
            models.Index(fields=['region_code']),
            models.Index(fields=['vendor_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.vendor_type})"


class Diagnosis(models.Model):
    """
    Stores each diagnosis event.
    """
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='diagnoses')
    disease = models.ForeignKey(Disease, on_delete=models.SET_NULL, null=True, related_name='diagnoses')
    image_url = models.URLField(max_length=500)
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="ML model confidence (0-100)"
    )
    location = models.CharField(max_length=255, blank=True)
    region_code = models.CharField(max_length=50, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    ml_model_version = models.CharField(max_length=50, default='v1.0')
    raw_ml_response = models.JSONField(blank=True, null=True, help_text="Full ML service response")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'diagnoses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['farmer', '-created_at']),
            models.Index(fields=['disease']),
            models.Index(fields=['region_code']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Diagnosis #{self.id} - {self.disease.name if self.disease else 'Unknown'} ({self.confidence_score}%)"


class DiagnosisVendor(models.Model):
    """
    Links vendors recommended for a specific diagnosis.
    """
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE, related_name='recommended_vendors')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    distance_km = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Distance from farmer to vendor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'diagnosis_vendors'
        unique_together = ['diagnosis', 'vendor']
        ordering = ['distance_km']
    
    def __str__(self):
        return f"Diagnosis #{self.diagnosis.id} -> {self.vendor.name}"
