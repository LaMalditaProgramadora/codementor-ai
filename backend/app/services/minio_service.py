from minio import Minio
from minio.error import S3Error
from typing import Optional, BinaryIO
import io
from datetime import timedelta
from app.core.config import get_settings

settings = get_settings()


class MinIOService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        self.bucket_submissions = settings.MINIO_BUCKET_SUBMISSIONS
        self.bucket_videos = settings.MINIO_BUCKET_VIDEOS
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """
        Ensure required buckets exist
        """
        try:
            for bucket in [self.bucket_submissions, self.bucket_videos]:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    print(f"Created bucket: {bucket}")
        except S3Error as e:
            print(f"Error ensuring buckets: {str(e)}")
    
    def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        bucket_name: Optional[str] = None,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload file to MinIO
        
        Args:
            file_data: File object or bytes
            object_name: Name for the object in MinIO
            bucket_name: Bucket to upload to (default: submissions)
            content_type: MIME type of the file
        
        Returns:
            Object path
        """
        if bucket_name is None:
            bucket_name = self.bucket_submissions
        
        try:
            # Get file size
            if isinstance(file_data, bytes):
                file_data = io.BytesIO(file_data)
                file_size = len(file_data.getvalue())
            else:
                file_data.seek(0, 2)  # Seek to end
                file_size = file_data.tell()
                file_data.seek(0)  # Seek back to start
            
            # Upload
            self.client.put_object(
                bucket_name,
                object_name,
                file_data,
                file_size,
                content_type=content_type
            )
            
            return f"{bucket_name}/{object_name}"
        
        except S3Error as e:
            raise Exception(f"Error uploading file: {str(e)}")
    
    def download_file(self, object_name: str, bucket_name: Optional[str] = None) -> bytes:
        """
        Download file from MinIO
        """
        if bucket_name is None:
            bucket_name = self.bucket_submissions
        
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        
        except S3Error as e:
            raise Exception(f"Error downloading file: {str(e)}")
    
    def get_file_url(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Get presigned URL for file access
        """
        if bucket_name is None:
            bucket_name = self.bucket_submissions
        
        try:
            url = self.client.presigned_get_object(
                bucket_name,
                object_name,
                expires=expires
            )
            return url
        
        except S3Error as e:
            raise Exception(f"Error generating URL: {str(e)}")
    
    def delete_file(self, object_name: str, bucket_name: Optional[str] = None) -> bool:
        """
        Delete file from MinIO
        """
        if bucket_name is None:
            bucket_name = self.bucket_submissions
        
        try:
            self.client.remove_object(bucket_name, object_name)
            return True
        
        except S3Error as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    def list_files(self, prefix: str = "", bucket_name: Optional[str] = None) -> list:
        """
        List files in bucket with optional prefix
        """
        if bucket_name is None:
            bucket_name = self.bucket_submissions
        
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        
        except S3Error as e:
            raise Exception(f"Error listing files: {str(e)}")
    
    def file_exists(self, object_name: str, bucket_name: Optional[str] = None) -> bool:
        """
        Check if file exists in MinIO
        """
        if bucket_name is None:
            bucket_name = self.bucket_submissions
        
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_info(self, object_name: str, bucket_name: Optional[str] = None) -> dict:
        """
        Get file metadata
        """
        if bucket_name is None:
            bucket_name = self.bucket_submissions
        
        try:
            stat = self.client.stat_object(bucket_name, object_name)
            return {
                'size': stat.size,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'content_type': stat.content_type
            }
        
        except S3Error as e:
            raise Exception(f"Error getting file info: {str(e)}")
    
    def upload_submission(
        self,
        submission_id: int,
        file_data: BinaryIO,
        filename: str,
        content_type: str = "application/zip"
    ) -> str:
        """
        Upload submission file with structured naming
        """
        object_name = f"submissions/{submission_id}/{filename}"
        return self.upload_file(
            file_data,
            object_name,
            self.bucket_submissions,
            content_type
        )
    
    def upload_video(
        self,
        submission_id: int,
        file_data: BinaryIO,
        filename: str,
        content_type: str = "video/mp4"
    ) -> str:
        """
        Upload video file with structured naming
        """
        object_name = f"videos/{submission_id}/{filename}"
        return self.upload_file(
            file_data,
            object_name,
            self.bucket_videos,
            content_type
        )


# Singleton instance
minio_service = MinIOService()
