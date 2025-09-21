import os, mimetypes
from pathlib import Path
import boto3

_s3 = None

def s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3

def upload_to_s3(local: Path, bucket: str, key: str, public: bool = True) -> str:
    ct, _ = mimetypes.guess_type(str(local))
    extra = {"ContentType": ct or "application/octet-stream"}
    s3().upload_file(str(local), bucket, key, ExtraArgs=extra)
    if public:
        s3().put_object_acl(Bucket=bucket, Key=key, ACL="public-read")
    return f"s3://{bucket}/{key}"

def public_url(bucket: str, key: str) -> str:
    base = os.getenv("PUBLIC_BASE_URL")
    if base:
        # CDN 베이스가 있으면 사용
        return f"{base}/{key}"
    # 없으면 S3 웹 URL 형태(버킷 퍼블릭 정책 필요)
    region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
