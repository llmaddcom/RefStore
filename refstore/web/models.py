"""Web API 的 Pydantic 模型"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ConfigModel(BaseModel):
    """配置模型"""
    minio: Dict[str, Any]
    enable_bucket_mapping: Optional[bool] = False
    bucket_map: Optional[Dict[str, str]] = None
    default_bucket: Optional[str] = "default"
    presigned_expiry: Optional[int] = 3600


class UploadRequest(BaseModel):
    """上传请求模型"""
    filename: Optional[str] = "file"
    content_type: Optional[str] = "application/octet-stream"
    logic_bucket: Optional[str] = None
    path: Optional[str] = None


class UploadResponse(BaseModel):
    """上传响应模型"""
    uri: str
    success: bool
    message: Optional[str] = None


class DownloadRequest(BaseModel):
    """下载请求模型"""
    uri: str


class PresignedURLRequest(BaseModel):
    """预签名 URL 请求模型"""
    uri: str
    expiry_seconds: Optional[int] = None
    method: Optional[str] = "GET"


class PresignedURLResponse(BaseModel):
    """预签名 URL 响应模型"""
    url: str
    uri: str
    expiry: Optional[int] = None


class FileInfo(BaseModel):
    """文件信息模型"""
    logic_bucket: str
    physical_bucket: str
    object_name: str
    size: int
    size_human: str
    content_type: str
    last_modified: datetime
    etag: Optional[str] = None


class FileInfoResponse(BaseModel):
    """文件信息响应模型"""
    uri: str
    info: Optional[FileInfo] = None
    exists: bool


class DeleteRequest(BaseModel):
    """删除请求模型"""
    uris: list[str]


class DeleteResponse(BaseModel):
    """删除响应模型"""
    deleted: list[str]
    failed: list[str]


class ListRequest(BaseModel):
    """列表请求模型"""
    logic_bucket: Optional[str] = None
    prefix: Optional[str] = ""
    recursive: Optional[bool] = True


class FileListItem(BaseModel):
    """文件列表项模型"""
    object_name: str
    size: int
    size_human: str
    last_modified: datetime
    is_dir: bool
    s3_uri: str


class ListResponse(BaseModel):
    """列表响应模型"""
    logic_bucket: str
    files: list[FileListItem]


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    message: str
    buckets_ok: bool


# ==========================================
# Gateway 管理模型
# ==========================================

class GatewayStatusResponse(BaseModel):
    """网关状态响应"""
    status: str
    endpoint: str
    secure: bool
    enable_bucket_mapping: bool
    default_bucket: str
    bucket_count: int


class GatewayConfigResponse(BaseModel):
    """网关配置响应（脱敏）"""
    endpoint: str
    secure: bool
    enable_bucket_mapping: bool
    bucket_map: Dict[str, str]
    default_bucket: str
    presigned_expiry: int
    public_url: Optional[str] = None


class CreateBucketRequest(BaseModel):
    """创建桶请求"""
    name: str
    location: Optional[str] = None


class CreateBucketResponse(BaseModel):
    """创建桶响应"""
    success: bool
    name: str
    message: Optional[str] = None


class BucketDetailResponse(BaseModel):
    """桶详情响应"""
    name: str
    exists: bool
    object_count: Optional[int] = None
    total_size: Optional[int] = None
    total_size_human: Optional[str] = None


class BucketListResponse(BaseModel):
    """桶列表响应"""
    buckets: List[Dict[str, Any]]
    total: int


class DeleteBucketResponse(BaseModel):
    """删除桶响应"""
    success: bool
    name: str
    message: Optional[str] = None


class BucketMappingResponse(BaseModel):
    """桶映射配置响应"""
    enable_bucket_mapping: bool
    bucket_map: Dict[str, str]
    reverse_bucket_map: Dict[str, str]


class UpdateBucketMappingRequest(BaseModel):
    """更新桶映射请求"""
    enable_bucket_mapping: Optional[bool] = None
    bucket_map: Optional[Dict[str, str]] = None
