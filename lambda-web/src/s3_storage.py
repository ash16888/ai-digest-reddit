"""S3 storage module for fetching static files from AWS S3."""
import json
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class S3Storage:
    """Handle S3 operations for the Reddit digest application."""
    
    def __init__(self, bucket_name: str = None):
        """Initialize S3 client with the specified bucket."""
        # Get bucket name from environment or use default
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")
        
        try:
            # Try to create S3 client with credentials and region
            region = os.getenv("AWS_DEFAULT_REGION", "eu-central-1")
            self.s3_client = boto3.client('s3', region_name=region)
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.available = True
            print(f"S3 connection successful to bucket: {self.bucket_name} in region: {region}")
        except (NoCredentialsError, ClientError) as e:
            print(f"Warning: S3 not available ({e}). Lambda application requires S3 connection.")
            self.s3_client = None
            self.available = False
    
    def download_json(self, key: str) -> Optional[dict]:
        """Download and parse JSON file from S3."""
        if not self.available:
            return None
            
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            print(f"Error downloading {key} from S3: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error downloading {key}: {e}")
            return None
    
    def download_markdown(self, key: str) -> Optional[str]:
        """Download markdown file from S3."""
        if not self.available:
            return None
            
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            return content
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            print(f"Error downloading {key} from S3: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error downloading {key}: {e}")
            return None
    
    def list_files(self, prefix: str) -> list[str]:
        """List all files in S3 with given prefix."""
        if not self.available:
            return []
            
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
                
            return [obj['Key'] for obj in response['Contents']]
        except Exception as e:
            print(f"Error listing files with prefix {prefix}: {e}")
            return []


# Create global instance
s3_storage = S3Storage()