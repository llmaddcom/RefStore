"""
Web API 模块 - 基于 FastAPI 的 RESTful 接口
"""

from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, status
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
    path: Optional[str] = Form(None)
):
    """
    上传文件

    - **file**: 要上传的文件
    - **logic_bucket**: 逻辑桶名（可选）
    - **path**: 存储路径（可选）
    """
    try:
        service = get_refstore()

        # 读取文件内容
        content = await file.read()

        # 上传文件
        uri = service.upload_file(
            file_data=content,
            original_filename=file.filename or "file",
            content_type=file.content_type or "application/octet-stream",
            logic_bucket=logic_bucket,
            path=path
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
    recursive: bool = True
):
    """
    列出桶中的文件

    - **logic_bucket**: 逻辑桶名
    - **prefix**: 文件前缀
    - **recursive**: 是否递归列出
    """
    try:
        service = get_refstore()

        if logic_bucket is None:
            logic_bucket = service.default_bucket

        files = service.list_files(logic_bucket, prefix, recursive)

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
        "version": "0.1.0",
        "description": "MinIO object storage service RESTful API",
        "docs": "/docs",
        "health": "/health"
    }
