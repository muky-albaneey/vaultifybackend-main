# api/storage_backends.py
import mimetypes
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from storages.utils import clean_name, safe_join

class LinodeMediaStorage(S3Boto3Storage):
    """
    Single-request PUT to Linode Object Storage.
    Avoids multipart + private helpers for maximum compatibility.
    """
    location = ""            # use your model's upload_to paths
    file_overwrite = False
    default_acl = getattr(settings, "AWS_DEFAULT_OBJECT_ACL", None)
    use_threads = False

    def _save(self, name, content):
        rel_name = clean_name(name)
        key = safe_join(self.location, rel_name) if self.location else rel_name
        try:
            content.seek(0)
        except Exception:
            pass
        body = content.read()
        content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        extra = {"ContentType": content_type}
        if self.default_acl:
            extra["ACL"] = self.default_acl
        self.bucket.Object(key).put(Body=body, **extra)  # one-shot PUT
        return rel_name
