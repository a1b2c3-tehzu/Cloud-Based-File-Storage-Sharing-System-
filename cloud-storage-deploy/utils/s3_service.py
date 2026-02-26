import boto3
import os
from botocore.exceptions import NoCredentialsError, ClientError
from config import Config
import uuid

class S3Service:
    def __init__(self):
        self.config = Config()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY,
            region_name=self.config.AWS_REGION
        )
        self.bucket_name = self.config.S3_BUCKET_NAME
    
    def upload_file(self, file_path, file_name, user_id):
        try:
            # Generate unique S3 key
            file_extension = os.path.splitext(file_name)[1]
            unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_extension}"
            s3_key = f"uploads/{user_id}/{unique_filename}"
            
            # Upload file to S3
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': 'application/octet-stream'}
            )
            
            # Generate the URL
            s3_url = f"https://{self.bucket_name}.s3.{self.config.AWS_REGION}.amazonaws.com/{s3_key}"
            
            return {
                'success': True,
                's3_key': s3_key,
                's3_url': s3_url
            }
            
        except NoCredentialsError:
            return {'success': False, 'error': 'AWS credentials not found'}
        except ClientError as e:
            return {'success': False, 'error': f'AWS Client Error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Upload failed: {str(e)}'}
    
    def delete_file(self, s3_key):
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return {'success': True}
        except ClientError as e:
            return {'success': False, 'error': f'Delete failed: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Delete failed: {str(e)}'}
    
    def generate_presigned_url(self, s3_key, expiration=3600):
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return {'success': True, 'url': url}
        except ClientError as e:
            return {'success': False, 'error': f'URL generation failed: {str(e)}'}
    
    def check_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            else:
                raise
    
    def create_bucket(self):
        try:
            if self.config.AWS_REGION == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.config.AWS_REGION}
                )
            return True
        except ClientError as e:
            print(f"Error creating bucket: {e}")
            return False
    
    def list_files(self, prefix=''):
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
            return files
        except ClientError as e:
            print(f"Error listing files: {e}")
            return []

# S3 service instance
s3_service = S3Service()
