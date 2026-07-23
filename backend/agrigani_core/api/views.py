"""
API Views for AgriGani Core.
"""

import logging
from datetime import datetime, timedelta, timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.dateparse import parse_date
import jwt

from agrigani_core.core.models import (
    Farmer, Disease, Treatment, Vendor, Diagnosis, DiagnosisVendor
)
from .serializers import (
    FarmerSerializer, DiseaseSerializer, DiseaseListSerializer,
    TreatmentSerializer, VendorSerializer, DiagnosisSerializer,
    DiagnosisListSerializer, DiagnosisCreateSerializer,
    LoginSerializer, PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer, RegisterSerializer, UserSerializer
)
from .authentication import JWTAuthentication
from .crop_catalog import get_canonical_crop_class_name, get_crop_catalog_entry
from .storage_service import ObjectStorageService
from .ml_service import MLServiceClient, MockMLServiceClient


logger = logging.getLogger(__name__)
User = get_user_model()


def _build_token(user):
    now = datetime.now(timezone.utc)
    return jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'iat': now,
        'exp': now + timedelta(hours=12),
    }, settings.SECRET_KEY, algorithm='HS256')


@api_view(['GET'])
def health_check(request):
    """Simple API health endpoint for deployment and frontend checks."""
    ml_client = MLServiceClient()

    return Response({
        'status': 'ok',
        'api': 'agrigani-core',
        'ml_service_available': ml_client.health_check(),
    })


@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response({
        'token': _build_token(user),
        'user': UserSerializer(user).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    return Response({
        'token': _build_token(user),
        'user': UserSerializer(user).data,
    })


@api_view(['POST'])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data.get('user')

    response = {
        'detail': 'If an account matches that username or email, a reset link has been generated.'
    }

    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = request.build_absolute_uri(
            f"/reset-password.html?uid={uid}&token={token}"
        )
        logger.info("Password reset token generated for user %s: %s", user.username, reset_url)

        if settings.DEBUG:
            response.update({
                'uid': uid,
                'token': token,
                'reset_url': reset_url,
            })

    return Response(response)


@api_view(['POST'])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response({
        'detail': 'Password has been reset successfully.',
        'token': _build_token(user),
        'user': UserSerializer(user).data,
    })


@api_view(['GET'])
def me(request):
    auth = JWTAuthentication().authenticate(request)
    if not auth:
        return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

    user, _ = auth
    return Response(UserSerializer(user).data)


class FarmerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing farmers.
    
    Endpoints:
    - GET /api/v1/farmers/ - List all farmers
    - POST /api/v1/farmers/ - Create a new farmer
    - GET /api/v1/farmers/{id}/ - Retrieve a farmer
    - PUT/PATCH /api/v1/farmers/{id}/ - Update a farmer
    - DELETE /api/v1/farmers/{id}/ - Delete a farmer
    """
    queryset = Farmer.objects.all()
    serializer_class = FarmerSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter farmers by region_code if provided."""
        queryset = super().get_queryset().filter(user=self.request.user)
        region_code = self.request.query_params.get('region_code')
        
        if region_code:
            queryset = queryset.filter(region_code=region_code)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DiseaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing diseases.
    
    Endpoints:
    - GET /api/v1/diseases/ - List all diseases
    - POST /api/v1/diseases/ - Create a new disease
    - GET /api/v1/diseases/{id}/ - Retrieve a disease with treatments
    - PUT/PATCH /api/v1/diseases/{id}/ - Update a disease
    - DELETE /api/v1/diseases/{id}/ - Delete a disease
    """
    queryset = Disease.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Use lightweight serializer for list view."""
        if self.action == 'list':
            return DiseaseListSerializer
        return DiseaseSerializer
    
    def get_queryset(self):
        """Filter diseases by category if provided."""
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        
        if category:
            queryset = queryset.filter(category=category.upper())
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def treatments(self, request, pk=None):
        """Get all treatments for a specific disease."""
        disease = self.get_object()
        treatments = Treatment.objects.filter(disease=disease)
        serializer = TreatmentSerializer(treatments, many=True)
        return Response(serializer.data)


class VendorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing vendors.
    
    Endpoints:
    - GET /api/v1/vendors/ - List all vendors
    - POST /api/v1/vendors/ - Create a new vendor
    - GET /api/v1/vendors/{id}/ - Retrieve a vendor
    - PUT/PATCH /api/v1/vendors/{id}/ - Update a vendor
    - DELETE /api/v1/vendors/{id}/ - Delete a vendor
    """
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """
        Filter vendors by:
        - region_code
        - vendor_type
        - is_verified
        """
        queryset = super().get_queryset()
        
        region_code = self.request.query_params.get('region_code')
        vendor_type = self.request.query_params.get('vendor_type')
        is_verified = self.request.query_params.get('is_verified')
        
        if region_code:
            queryset = queryset.filter(region_code=region_code)
        
        if vendor_type:
            queryset = queryset.filter(vendor_type=vendor_type.upper())
        
        if is_verified is not None:
            is_verified_bool = is_verified.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_verified=is_verified_bool)
        
        return queryset


class DiagnosisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing diagnoses.
    
    Main endpoint for disease diagnosis workflow:
    POST /api/v1/diagnoses/ - Submit image for diagnosis
    
    Other endpoints:
    - GET /api/v1/diagnoses/ - List all diagnoses
    - GET /api/v1/diagnoses/{id}/ - Retrieve a diagnosis
    """
    queryset = Diagnosis.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == 'create':
            return DiagnosisCreateSerializer
        elif self.action == 'list':
            return DiagnosisListSerializer
        return DiagnosisSerializer

    def get_permissions(self):
        if self.action == 'statistics':
            return [AllowAny()]
        return super().get_permissions()
    
    def get_queryset(self):
        """
        Filter diagnoses by:
        - farmer_id
        - disease_id
        - disease_name
        - region_code
        - date range
        """
        queryset = super().get_queryset().filter(farmer__user=self.request.user)
        
        farmer_id = self.request.query_params.get('farmer_id')
        disease_id = self.request.query_params.get('disease_id')
        disease_name = self.request.query_params.get('disease_name')
        region_code = self.request.query_params.get('region_code')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if farmer_id:
            queryset = queryset.filter(farmer_id=farmer_id)
        
        if disease_id:
            queryset = queryset.filter(disease_id=disease_id)

        if disease_name:
            queryset = queryset.filter(disease__name__icontains=disease_name)
        
        if region_code:
            queryset = queryset.filter(region_code=region_code)

        if date_from:
            parsed_from = parse_date(date_from)
            if parsed_from:
                queryset = queryset.filter(created_at__date__gte=parsed_from)

        if date_to:
            parsed_to = parse_date(date_to)
            if parsed_to:
                queryset = queryset.filter(created_at__date__lte=parsed_to)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        Main diagnosis endpoint.
        
        Workflow:
        1. Validate request data
        2. Upload image to object storage
        3. Send image URL to ML service
        4. Save diagnosis to database
        5. Recommend nearby vendors
        6. Return full diagnosis result
        """
        # Validate request
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        try:
            # Step 1: Get farmer
            farmer = get_object_or_404(Farmer, id=validated_data['farmer_id'], user=request.user)
            
            # Step 2: Upload image to object storage
            storage_service = ObjectStorageService()
            image_url = storage_service.upload_image(validated_data['image'])
            
            # Step 3: Call ML service for prediction
            ml_client = self._get_ml_client()
            ml_response = ml_client.predict_disease(
                image_url=image_url,
                farmer_location=validated_data.get('location', farmer.location),
                region_code=validated_data.get('region_code', farmer.region_code)
            )
            
            # Step 4: Find or create disease
            disease = self._get_or_create_disease(ml_response)
            
            # Step 5: Create diagnosis record
            diagnosis = Diagnosis.objects.create(
                farmer=farmer,
                disease=disease,
                image_url=image_url,
                confidence_score=ml_response.get('disease_confidence', 0) * 100,
                location=validated_data.get('location', farmer.location),
                region_code=validated_data.get('region_code', farmer.region_code),
                latitude=validated_data.get('latitude'),
                longitude=validated_data.get('longitude'),
                ml_model_version=ml_response.get('ml_model_version', 'v1.0'),
                raw_ml_response=ml_response,
                notes=validated_data.get('notes', '')
            )
            
            # Step 6: Recommend vendors
            self._recommend_vendors(diagnosis, validated_data.get('region_code', farmer.region_code))
            
            # Step 7: Return response
            response_serializer = DiagnosisSerializer(diagnosis)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception("Diagnosis creation failed")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_ml_client(self):
        """Get ML service client, with optional mock fallback for local demos."""
        client = MLServiceClient()
        
        if not client.health_check():
            if getattr(settings, 'ENABLE_MOCK_ML_FALLBACK', False):
                return MockMLServiceClient()
            raise ValueError(
                "FastAPI ML service is not available. Start it on "
                f"{settings.FASTAPI_ML_SERVICE_URL} or set ENABLE_MOCK_ML_FALLBACK=True."
            )
        
        return client
    
    def _get_or_create_disease(self, ml_response):
        """Get existing disease or create a new one from ML response."""
        disease_name = ml_response.get('disease_name')
        
        if not disease_name:
            raise ValueError("ML service did not return a disease name")
        
        canonical_name = get_canonical_crop_class_name(disease_name) or disease_name
        catalog_entry = get_crop_catalog_entry(canonical_name)

        if catalog_entry:
            disease, _ = Disease.objects.update_or_create(
                name=canonical_name,
                defaults={
                    'scientific_name': catalog_entry.get('scientific_name', ''),
                    'category': 'CROP',
                    'description': catalog_entry['description'],
                    'symptoms': catalog_entry['symptoms'],
                    'causes': catalog_entry.get('causes', ''),
                    'prevention_tips': catalog_entry.get('prevention_tips', ''),
                    'severity_level': catalog_entry.get('severity_level', 3),
                }
            )

            for treatment_data in catalog_entry.get('treatments', []):
                Treatment.objects.update_or_create(
                    disease=disease,
                    medicine_name=treatment_data['medicine_name'],
                    defaults=treatment_data
                )
            return disease

        treatment_data = ml_response.get('treatment_recommendation', {})
        disease, _ = Disease.objects.get_or_create(
            name=disease_name,
            defaults={
                'category': 'CROP',
                'description': f"Auto-created from ML prediction: {disease_name}",
                'symptoms': "To be updated",
                'severity_level': 3
            }
        )

        if treatment_data:
            Treatment.objects.update_or_create(
                disease=disease,
                medicine_name=treatment_data.get('medicine', 'To be updated'),
                defaults={
                    'active_ingredient': treatment_data.get('active_ingredient', ''),
                    'dosage': treatment_data.get('dosage', 'Consult specialist'),
                    'application_method': treatment_data.get('application_method', 'As directed'),
                    'frequency': treatment_data.get('frequency', 'As needed'),
                    'duration': treatment_data.get('duration', 'As needed'),
                    'precautions': treatment_data.get('precautions', ''),
                    'effectiveness_rating': treatment_data.get('effectiveness_rating', 3),
                }
            )

        return disease
    
    def _recommend_vendors(self, diagnosis, region_code):
        """Find and link nearby vendors to the diagnosis."""
        # Get vendors in the same region
        vendors = Vendor.objects.filter(
            region_code=region_code,
            is_verified=True
        )[:5]  # Top 5 vendors
        
        # Link vendors to diagnosis
        for vendor in vendors:
            DiagnosisVendor.objects.create(
                diagnosis=diagnosis,
                vendor=vendor
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get diagnosis statistics."""
        total_diagnoses = Diagnosis.objects.count()
        
        # Group by disease
        diseases = Disease.objects.all()
        disease_stats = []
        
        for disease in diseases:
            count = Diagnosis.objects.filter(disease=disease).count()
            if count > 0:
                disease_stats.append({
                    'disease': disease.name,
                    'count': count
                })
        
        # Sort by count
        disease_stats = sorted(disease_stats, key=lambda x: x['count'], reverse=True)
        
        recent_diagnoses = DiagnosisListSerializer(
            Diagnosis.objects.select_related('farmer', 'disease')[:5],
            many=True
        ).data

        return Response({
            'total_diagnoses': total_diagnoses,
            'disease_breakdown': disease_stats,
            'recent_diagnoses': recent_diagnoses
        })
