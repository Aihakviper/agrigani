"""
Management command to populate database with sample data.
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from agrigani_core.api.crop_catalog import CROP_CLASS_CATALOG
from agrigani_core.core.models import Disease, Treatment, Vendor


class Command(BaseCommand):
    help = 'Populate database with sample diseases, treatments, and vendors'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database with sample data...')
        
        # Create model-aligned diseases and treatments.
        diseases_data = [
            {
                'name': name,
                'scientific_name': entry.get('scientific_name', ''),
                'category': 'CROP',
                'description': entry['description'],
                'symptoms': entry['symptoms'],
                'causes': entry.get('causes', ''),
                'prevention_tips': entry.get('prevention_tips', ''),
                'severity_level': entry.get('severity_level', 3),
                'treatments': entry.get('treatments', []),
            }
            for name, entry in CROP_CLASS_CATALOG.items()
        ]
        
        diseases_created = 0
        treatments_created = 0
        
        for disease_data in diseases_data:
            treatments_list = disease_data.pop('treatments')
            
            disease, created = Disease.objects.update_or_create(
                name=disease_data['name'],
                defaults=disease_data
            )
            
            if created:
                diseases_created += 1
                self.stdout.write(f'  Created disease: {disease.name}')
            else:
                self.stdout.write(f'  Updated disease: {disease.name}')

            for treatment_data in treatments_list:
                _, treatment_created = Treatment.objects.update_or_create(
                    disease=disease,
                    medicine_name=treatment_data['medicine_name'],
                    defaults=treatment_data
                )
                if treatment_created:
                    treatments_created += 1
        
        # Create sample vendors
        vendors_data = [
            {
                'name': 'Kaduna Agro Supplies',
                'vendor_type': 'AGRO_DEALER',
                'phone_number': '08012345671',
                'email': 'kaduna@agrosupplies.com',
                'address': 'Shop 45, Kaduna Central Market',
                'location': 'Kaduna Central, Kaduna',
                'region_code': 'NG-KD',
                'latitude': 10.5231,
                'longitude': 7.4383,
                'is_verified': True,
                'rating': 4.5
            },
            {
                'name': 'Green Valley Veterinary Clinic',
                'vendor_type': 'VET_CLINIC',
                'phone_number': '08012345672',
                'email': 'greenvalley@vet.ng',
                'address': '12 Ahmadu Bello Way, Kaduna',
                'location': 'Kaduna South, Kaduna',
                'region_code': 'NG-KD',
                'latitude': 10.5105,
                'longitude': 7.4165,
                'is_verified': True,
                'rating': 4.8
            },
            {
                'name': 'Kano Agricultural Pharmacy',
                'vendor_type': 'PHARMACY',
                'phone_number': '08012345673',
                'address': 'No. 78, Kofar Mata, Kano',
                'location': 'Kano Municipal, Kano',
                'region_code': 'NG-KN',
                'latitude': 12.0022,
                'longitude': 8.5919,
                'is_verified': True,
                'rating': 4.3
            },
            {
                'name': 'Abuja Farm Inputs',
                'vendor_type': 'AGRO_DEALER',
                'phone_number': '08012345674',
                'email': 'abuja@farminputs.ng',
                'address': 'Plot 234, Wuse Market',
                'location': 'Wuse, Abuja',
                'region_code': 'NG-FC',
                'latitude': 9.0579,
                'longitude': 7.4951,
                'is_verified': True,
                'rating': 4.6
            },
            {
                'name': 'Niger State Agro Services',
                'vendor_type': 'AGRO_DEALER',
                'phone_number': '08012345675',
                'address': 'Minna Main Market',
                'location': 'Minna, Niger',
                'region_code': 'NG-NI',
                'latitude': 9.6140,
                'longitude': 6.5489,
                'is_verified': False,
                'rating': 4.0
            }
        ]
        
        vendors_created = 0
        
        for vendor_data in vendors_data:
            vendor, created = Vendor.objects.get_or_create(
                name=vendor_data['name'],
                defaults=vendor_data
            )
            
            if created:
                vendors_created += 1
                self.stdout.write(f'  Created vendor: {vendor.name}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\nDatabase seeded successfully!\n'
            f'  - {diseases_created} diseases created\n'
            f'  - {treatments_created} treatments created\n'
            f'  - {vendors_created} vendors created'
        ))
