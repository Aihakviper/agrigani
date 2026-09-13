"""
Object Storage Service for handling image uploads.
Supports: Local, Supabase, Azure Blob, Cloudflare R2
"""

import os
import uuid
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


class ObjectStorageService:
    """
    Handles image uploads to various storage backends.
    """
    
    def __init__(self):
        self.storage_type = settings.OBJECT_STORAGE_TYPE
        self.bucket = settings.OBJECT_STORAGE_BUCKET
        
    def upload_image(self, image_file, folder='diagnoses'):
        """
        Upload image to object storage and return URL.
        
        Args:
            image_file: Django UploadedFile object
            folder: Storage folder/prefix
            
        Returns:
            str: Public URL of uploaded image
        """
        # Generate unique filename
        ext = Path(image_file.name).suffix
        filename = f"{folder}/{uuid.uuid4()}{ext}"
        
        if self.storage_type == 'local':
            return self._upload_local(image_file, filename)
        elif self.storage_type == 'supabase':
            return self._upload_supabase(image_file, filename)
        elif self.storage_type == 'azure':
            return self._upload_azure(image_file, filename)
        elif self.storage_type == 'r2':
            return self._upload_r2(image_file, filename)
        else:
            # Default to local storage
            return self._upload_local(image_file, filename)
    
    def _upload_local(self, image_file, filename):
        """Upload to local media storage."""
        path = default_storage.save(filename, ContentFile(image_file.read()))
        url = default_storage.url(path)
        
        # Make absolute URL if needed
        if not url.startswith('http'):
            base_url = os.getenv('BASE_URL', 'http://localhost:8000')
            url = f"{base_url}{url}"
        
        return url
    
    def _upload_supabase(self, image_file, filename):
        """
        Upload to Supabase Storage.
        Requires: supabase-py
        """
        try:
            from supabase import create_client
            
            supabase_url = settings.OBJECT_STORAGE_URL
            supabase_key = settings.OBJECT_STORAGE_KEY
            
            supabase = create_client(supabase_url, supabase_key)
            
            # Upload file
            response = supabase.storage.from_(self.bucket).upload(
                filename,
                image_file.read(),
                file_options={"content-type": image_file.content_type}
            )
            
            # Get public URL
            public_url = supabase.storage.from_(self.bucket).get_public_url(filename)
            
            return public_url
            
        except ImportError:
            raise Exception("supabase-py package is required for Supabase storage")
        except Exception as e:
            raise Exception(f"Supabase upload failed: {str(e)}")
    
    def _upload_azure(self, image_file, filename):
        """
        Upload to Azure Blob Storage.
        Requires: azure-storage-blob
        """
        try:
            from azure.storage.blob import BlobServiceClient
            
            connection_string = settings.OBJECT_STORAGE_URL
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            
            # Get container client
            container_client = blob_service_client.get_container_client(self.bucket)
            
            # Upload blob
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(
                image_file.read(),
                content_settings={'content_type': image_file.content_type}
            )
            
            # Get URL
            url = blob_client.url
            
            return url
            
        except ImportError:
            raise Exception("azure-storage-blob package is required for Azure storage")
        except Exception as e:
            raise Exception(f"Azure upload failed: {str(e)}")
    
    def _upload_r2(self, image_file, filename):
        """
        Upload to Cloudflare R2.
        Requires: boto3 (S3-compatible)
        """
        try:
            import boto3
            from botocore.config import Config
            
            # R2 uses S3-compatible API
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.OBJECT_STORAGE_URL,
                aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
                config=Config(signature_version='s3v4')
            )
            
            # Upload file
            s3_client.upload_fileobj(
                image_file,
                self.bucket,
                filename,
                ExtraArgs={'ContentType': image_file.content_type}
            )
            
            # Construct public URL
            account_id = os.getenv('R2_ACCOUNT_ID')
            url = f"https://{self.bucket}.{account_id}.r2.cloudflarestorage.com/{filename}"
            
            return url
            
        except ImportError:
            raise Exception("boto3 package is required for R2 storage")
        except Exception as e:
            raise Exception(f"R2 upload failed: {str(e)}")
    
    def delete_image(self, image_url):
        """
        Delete image from storage (optional implementation).
        """
        # Extract filename from URL and delete
        # Implementation depends on storage backend
        pass
