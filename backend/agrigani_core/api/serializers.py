"""
Serializers for AgriGani Core API.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from agrigani_core.core.models import Farmer, Disease, Treatment, Vendor, Diagnosis, DiagnosisVendor


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Public account shape returned to the frontend."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username is already taken")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError("Invalid username or password")
        attrs['user'] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        help_text="Username or email for the account that needs password reset"
    )

    def validate(self, attrs):
        identifier = attrs['identifier'].strip()
        user = User.objects.filter(username__iexact=identifier).first()
        if not user:
            user = User.objects.filter(email__iexact=identifier).first()
        attrs['user'] = user
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise serializers.ValidationError("Invalid password reset link") from exc

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError("Invalid or expired password reset token")

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class FarmerSerializer(serializers.ModelSerializer):
    """Serializer for Farmer model."""
    
    class Meta:
        model = Farmer
        fields = [
            'id', 'full_name', 'phone_number', 'email', 'location',
            'region_code', 'gender', 'farm_size_hectares', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TreatmentSerializer(serializers.ModelSerializer):
    """Serializer for Treatment model."""
    
    class Meta:
        model = Treatment
        fields = [
            'id', 'medicine_name', 'active_ingredient', 'dosage',
            'application_method', 'frequency', 'duration', 
            'precautions', 'effectiveness_rating'
        ]


class DiseaseSerializer(serializers.ModelSerializer):
    """Serializer for Disease model."""
    treatments = TreatmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Disease
        fields = [
            'id', 'name', 'scientific_name', 'category', 'description',
            'symptoms', 'causes', 'prevention_tips', 'severity_level',
            'treatments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DiseaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for disease listings."""
    treatments = TreatmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Disease
        fields = [
            'id', 'name', 'category', 'description', 'symptoms',
            'prevention_tips', 'severity_level', 'treatments'
        ]


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for Vendor model."""
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'name', 'vendor_type', 'phone_number', 'email',
            'address', 'location', 'region_code', 
            'latitude', 'longitude', 'is_verified', 'rating',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DiagnosisVendorSerializer(serializers.ModelSerializer):
    """Serializer for recommended vendors in diagnosis."""
    vendor = VendorSerializer(read_only=True)
    
    class Meta:
        model = DiagnosisVendor
        fields = ['vendor', 'distance_km']


class DiagnosisSerializer(serializers.ModelSerializer):
    """Serializer for Diagnosis model."""
    farmer_name = serializers.CharField(source='farmer.full_name', read_only=True)
    disease_name = serializers.CharField(source='disease.name', read_only=True)
    disease_details = DiseaseSerializer(source='disease', read_only=True)
    recommended_vendors = DiagnosisVendorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Diagnosis
        fields = [
            'id', 'farmer', 'farmer_name', 'disease', 'disease_name',
            'disease_details', 'image_url', 'confidence_score',
            'location', 'region_code', 'latitude', 'longitude',
            'ml_model_version', 'raw_ml_response', 'notes',
            'recommended_vendors', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'raw_ml_response']


class DiagnosisListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for diagnosis listings."""
    farmer_name = serializers.CharField(source='farmer.full_name', read_only=True)
    disease_name = serializers.CharField(source='disease.name', read_only=True)
    
    class Meta:
        model = Diagnosis
        fields = [
            'id', 'farmer', 'farmer_name', 'disease', 'disease_name',
            'image_url', 'confidence_score', 'location', 'region_code',
            'ml_model_version', 'created_at'
        ]


class DiagnosisCreateSerializer(serializers.Serializer):
    """Serializer for creating a new diagnosis."""
    farmer_id = serializers.IntegerField(required=True)
    image = serializers.ImageField(required=True)
    location = serializers.CharField(required=False, allow_blank=True)
    region_code = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        required=False, 
        allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        required=False, 
        allow_null=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_image(self, value):
        """Validate uploaded image."""
        # Check file size (5MB max)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image file size cannot exceed 5MB")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Only JPEG and PNG images are allowed. Got: {value.content_type}"
            )
        
        return value
    
    def validate_farmer_id(self, value):
        """Validate farmer exists."""
        if not Farmer.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Farmer with ID {value} does not exist")
        return value
