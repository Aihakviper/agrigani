"""
Admin configuration for AgriGani Core models.
"""

from django.contrib import admin
from .models import Farmer, Disease, Treatment, Vendor, Diagnosis, DiagnosisVendor


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone_number', 'location', 'region_code', 'created_at']
    list_filter = ['region_code', 'gender', 'created_at']
    search_fields = ['full_name', 'phone_number', 'email', 'location']
    ordering = ['-created_at']


@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'severity_level', 'created_at']
    list_filter = ['category', 'severity_level']
    search_fields = ['name', 'scientific_name', 'description']
    ordering = ['name']


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ['medicine_name', 'disease', 'effectiveness_rating', 'frequency']
    list_filter = ['effectiveness_rating', 'disease']
    search_fields = ['medicine_name', 'active_ingredient']
    ordering = ['-effectiveness_rating']


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor_type', 'location', 'region_code', 'is_verified', 'rating']
    list_filter = ['vendor_type', 'region_code', 'is_verified']
    search_fields = ['name', 'phone_number', 'address', 'location']
    ordering = ['-is_verified', '-rating']


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ['id', 'farmer', 'disease', 'confidence_score', 'location', 'created_at']
    list_filter = ['disease', 'region_code', 'created_at']
    search_fields = ['farmer__full_name', 'location']
    ordering = ['-created_at']
    readonly_fields = ['raw_ml_response', 'created_at']


@admin.register(DiagnosisVendor)
class DiagnosisVendorAdmin(admin.ModelAdmin):
    list_display = ['diagnosis', 'vendor', 'distance_km', 'created_at']
    list_filter = ['created_at']
    search_fields = ['diagnosis__id', 'vendor__name']
    ordering = ['diagnosis', 'distance_km']
