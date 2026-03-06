"""
Web API 模块 - 基于 FastAPI 的 RESTful 接口
"""

from typing import Optional
from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form, status
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager
import io

from ..sync.file_service import MinioFileService
from ..core.config import ConfigValidator
from ..core.exceptions import RefStoreError
from .models import (
    ConfigModel,
    UploadResponse,
    DownloadRequest,
    PresignedURLRequest,
    PresignedURLResponse,
    FileInfoResponse,
    DeleteRequest,
    DeleteResponse,
    ListRequest,
    ListResponse,
    HealthResponse,
    GatewayStatusResponse,
    GatewayConfigResponse,
    CreateBucketRequest,
    CreateBucketResponse,
    BucketDetailResponse,
    BucketListResponse,
    DeleteBucketResponse,
    BucketMappingResponse,
    UpdateBucketMappingRequest,
)


# 全局存储服务实例
_refstore_service: Optional[MinioFileService] = None


def get_refstore() -> MinioFileService:
    """获取 RefStore 服务实例"""
    if _refstore_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RefStore service not initialized"
        )
    return _refstore_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _refstore_service
    # 启动时初始化
    print("[RefStore Web API] Starting up...")
    yield
    # 关闭时清理
    print("[RefStore Web API] Shutting down...")
    if _refstore_service is not None:
        _refstore_service = None


# 创建 FastAPI 应用
app = FastAPI(
    title="RefStore API",
    description="MinIO 对象存储服务 RESTful API",
    version="0.1.0",
    lifespan=lifespan,
)


def init_service(config: dict):
    """初始化 RefStore 服务"""
    global _refstore_service
    try:
        ConfigValidator.test_connection(config)
        _refstore_service = MinioFileService(config)
        _refstore_service.init_buckets()
        print("[RefStore Web API] Service initialized successfully")
    except Exception as e:
        print(f"[RefStore Web API] Failed to initialize service: {e}")
        raise


# ==========================================
# 健康检查
# ==========================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    try:
        service = get_refstore()
        buckets = service.bucket_manager.list_buckets()
        return HealthResponse(
            status="ok",
            message="RefStore is running",
            buckets_ok=True
        )
    except HTTPException:
        return HealthResponse(
            status="error",
            message="RefStore service not initialized",
            buckets_ok=False
        )


# ==========================================
# 文件上传
# ==========================================

@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    logic_bucket: Optional[str] = Form(None),
    path: Optional[str] = Form(None),
    use_logical_uri: bool = Form(False),
):
    """
    上传文件

    - **file**: 要上传的文件
    - **logic_bucket**: 逻辑桶名（可选）
    - **path**: 存储路径（可选）
    - **use_logical_uri**: 为 True 时返回逻辑桶 URI（仅在 enable_bucket_mapping 开启时有效）
    """
    try:
        service = get_refstore()

        content = await file.read()

        uri = service.upload_file(
            file_data=content,
            original_filename=file.filename or "file",
            content_type=file.content_type or "application/octet-stream",
            logic_bucket=logic_bucket,
            path=path,
            use_logical_uri=use_logical_uri,
        )

        if uri is None:
            return UploadResponse(
                uri="",
                success=False,
                message="Upload failed"
            )

        return UploadResponse(
            uri=uri,
            success=True,
            message="File uploaded successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


# ==========================================
# 文件下载
# ==========================================

@app.get("/download")
async def download_file(uri: str):
    """
    下载文件

    - **uri**: S3 URI (s3://bucket/path/to/file)
    """
    try:
        service = get_refstore()

        data = service.download_file(uri)

        if data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        # 获取文件信息
        info = service.get_file_info(uri)
        content_type = info.get("content_type", "application/octet-stream") if info else "application/octet-stream"

        # 返回文件流
        return StreamingResponse(
            io.BytesIO(data),
            media_type=content_type
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


# ==========================================
# 预签名 URL
# ==========================================

@app.get("/presigned-url", response_model=PresignedURLResponse)
async def get_presigned_url(uri: str, expiry_seconds: Optional[int] = None, method: str = "GET"):
    """
    生成预签名 URL

    - **uri**: S3 URI (s3://bucket/path/to/file)
    - **expiry_seconds**: 过期时间（秒），默认为配置值
    - **method**: HTTP 方法 (GET, PUT, DELETE)
    """
    try:
        service = get_refstore()

        url = service.get_presigned_url(uri, expiry_seconds, method)

        if url is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate presigned URL"
            )

        return PresignedURLResponse(
            url=url,
            uri=uri,
            expiry=expiry_seconds or service.presigned_expiry
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate presigned URL: {str(e)}"
        )


# ==========================================
# 文件信息
# ==========================================

@app.get("/info", response_model=FileInfoResponse)
async def get_file_info(uri: str):
    """
    获取文件信息

    - **uri**: S3 URI (s3://bucket/path/to/file)
    """
    try:
        service = get_refstore()

        info = service.get_file_info(uri)
        exists = service.file_exists(uri)

        return FileInfoResponse(
            uri=uri,
            info=info,
            exists=exists
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file info: {str(e)}"
        )


# ==========================================
# 删除文件
# ==========================================

@app.delete("/delete", response_model=DeleteResponse)
async def delete_files(request: DeleteRequest):
    """
    批量删除文件

    - **uris**: S3 URI 列表
    """
    try:
        service = get_refstore()

        result = service.delete_files(request.uris)

        return DeleteResponse(
            deleted=result.get("deleted", []),
            failed=result.get("failed", [])
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )


# ==========================================
# 列出文件
# ==========================================

@app.get("/list", response_model=ListResponse)
async def list_files(
    logic_bucket: Optional[str] = None,
    prefix: str = "",
    recursive: bool = True,
    use_logical_uri: bool = False,
):
    """
    列出桶中的文件

    - **logic_bucket**: 逻辑桶名
    - **prefix**: 文件前缀
    - **recursive**: 是否递归列出
    - **use_logical_uri**: 为 True 时返回逻辑桶 URI
    """
    try:
        service = get_refstore()

        if logic_bucket is None:
            logic_bucket = service.default_bucket

        files = service.list_files(logic_bucket, prefix, recursive, use_logical_uri)

        return ListResponse(
            logic_bucket=logic_bucket,
            files=files
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"List failed: {str(e)}"
        )


# ==========================================
# 根路径
# ==========================================

@app.get("/")
async def root():
    """根路径 - API 信息"""
    return {
        "name": "RefStore API",
        "version": "0.3.0",
        "description": "MinIO object storage service RESTful API",
        "docs": "/docs",
        "health": "/health",
        "gateway": "/gateway/status",
    }


# ==========================================
# Gateway 管理路由
# ==========================================

gateway_router = APIRouter(prefix="/gateway", tags=["Gateway 管理"])


@gateway_router.get("/status", response_model=GatewayStatusResponse)
async def gateway_status():
    """获取 MinIO 网关连接状态和服务信息"""
    try:
        service = get_refstore()
        buckets = service.bucket_manager.list_buckets()
        return GatewayStatusResponse(
            status="connected",
            endpoint=service.endpoint,
            secure=service.secure,
            enable_bucket_mapping=service.enable_bucket_mapping,
            default_bucket=service.default_bucket,
            bucket_count=len(buckets),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取网关状态失败: {str(e)}",
        )


@gateway_router.get("/config", response_model=GatewayConfigResponse)
async def gateway_config():
    """查看当前 MinIO 服务配置（access_key/secret_key 脱敏）"""
    try:
        service = get_refstore()
        return GatewayConfigResponse(
            endpoint=service.endpoint,
            secure=service.secure,
            enable_bucket_mapping=service.enable_bucket_mapping,
            bucket_map=service.bucket_map,
            default_bucket=service.default_bucket,
            presigned_expiry=service.presigned_expiry,
            public_url=service.public_url,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}",
        )


@gateway_router.get("/buckets", response_model=BucketListResponse)
async def gateway_list_buckets():
    """列出 MinIO 服务上的所有桶"""
    try:
        service = get_refstore()
        buckets = service.bucket_manager.list_buckets()
        return BucketListResponse(buckets=buckets, total=len(buckets))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出桶失败: {str(e)}",
        )


@gateway_router.post("/buckets", response_model=CreateBucketResponse)
async def gateway_create_bucket(request: CreateBucketRequest):
    """创建一个新桶"""
    try:
        service = get_refstore()
        success = service.bucket_manager.create_bucket(request.name, request.location)
        msg = "桶创建成功" if success else "桶创建失败"
        return CreateBucketResponse(success=success, name=request.name, message=msg)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建桶失败: {str(e)}",
        )


@gateway_router.get("/buckets/{name}", response_model=BucketDetailResponse)
async def gateway_get_bucket(name: str):
    """获取指定桶的详细信息"""
    try:
        service = get_refstore()
        info = service.bucket_manager.get_bucket_info(name)
        if info is None:
            return BucketDetailResponse(name=name, exists=False)
        return BucketDetailResponse(
            name=info["name"],
            exists=info["exists"],
            object_count=info.get("object_count"),
            total_size=info.get("total_size"),
            total_size_human=info.get("total_size_human"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取桶信息失败: {str(e)}",
        )


@gateway_router.delete("/buckets/{name}", response_model=DeleteBucketResponse)
async def gateway_delete_bucket(name: str, force: bool = False):
    """
    删除指定桶

    - **force**: 为 True 时强制删除（先清空桶内所有对象）
    """
    try:
        service = get_refstore()
        success = service.bucket_manager.delete_bucket(name, force=force)
        msg = "桶删除成功" if success else "桶删除失败"
        return DeleteBucketResponse(success=success, name=name, message=msg)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除桶失败: {str(e)}",
        )


@gateway_router.get("/bucket-mapping", response_model=BucketMappingResponse)
async def gateway_get_bucket_mapping():
    """查看当前桶映射配置"""
    try:
        service = get_refstore()
        return BucketMappingResponse(
            enable_bucket_mapping=service.enable_bucket_mapping,
            bucket_map=service.bucket_map,
            reverse_bucket_map=service.reverse_bucket_map,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取桶映射配置失败: {str(e)}",
        )


@gateway_router.put("/bucket-mapping", response_model=BucketMappingResponse)
async def gateway_update_bucket_mapping(request: UpdateBucketMappingRequest):
    """
    热更新桶映射配置

    可以单独更新 enable_bucket_mapping 或 bucket_map，也可以同时更新。
    """
    try:
        service = get_refstore()

        if request.enable_bucket_mapping is not None:
            service.enable_bucket_mapping = request.enable_bucket_mapping

        if request.bucket_map is not None:
            service.bucket_map = request.bucket_map

        # 重建反向映射表
        if service.enable_bucket_mapping and service.bucket_map:
            service.reverse_bucket_map = {v: k for k, v in service.bucket_map.items()}
        else:
            service.reverse_bucket_map = {}

        return BucketMappingResponse(
            enable_bucket_mapping=service.enable_bucket_mapping,
            bucket_map=service.bucket_map,
            reverse_bucket_map=service.reverse_bucket_map,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新桶映射配置失败: {str(e)}",
        )


app.include_router(gateway_router)
