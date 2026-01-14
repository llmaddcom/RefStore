"""
RefStore - 简单易用的 MinIO 对象存储服务封装库

支持：
- 同步/异步 API
- Web API (FastAPI)
- S3 URI 编码/解码
- 逻辑桶名到物理桶名的映射
- 配置验证和连接测试
- 重试机制
"""

__version__ = "0.1.0"
__author__ = "RefStore Contributors"

# 核心异常
from .core.exceptions import (
    RefStoreError,
    ConfigError,
    ConnectionError,
    BucketNotFoundError,
    FileNotFoundError,
    URIParseError,
)

# 核心工具
from .core.config import ConfigValidator
from .core.retry import retry_with_backoff, RetryHandler
from .utils.uri import (
    URIUtils,
    encode_uri,
    decode_uri,
    validate_uri,
    get_bucket_from_uri,
    get_object_name_from_uri,
    get_file_extension,
    normalize_uri,
    join_uri,
    get_parent_uri,
    parse_filename,
)

# 同步 API
from .sync.file_service import MinioFileService as RefStore
from .sync.buckets import BucketManager

# 异步 API
from ._async.file_service import AsyncMinioFileService as AsyncRefStore
from ._async.buckets import AsyncBucketManager

# Web API
from .web import app as web_app
from .web import init_service as init_web_service


__all__ = [
    # 异常类
    "RefStoreError",
    "ConfigError",
    "ConnectionError",
    "BucketNotFoundError",
    "FileNotFoundError",
    "URIParseError",
    # 核心工具
    "ConfigValidator",
    "retry_with_backoff",
    "RetryHandler",
    # URI 工具
    "URIUtils",
    "encode_uri",
    "decode_uri",
    "validate_uri",
    "get_bucket_from_uri",
    "get_object_name_from_uri",
    "get_file_extension",
    "normalize_uri",
    "join_uri",
    "get_parent_uri",
    "parse_filename",
    # 同步 API
    "RefStore",
    "BucketManager",
    # 异步 API
    "AsyncRefStore",
    "AsyncBucketManager",
    # Web API
    "web_app",
    "init_web_service",
]


def __getattr__(name):
    """懒加载 Web API 相关模块"""
    if name in ["web_app", "init_web_service"]:
        # 确保依赖已安装
        try:
            import fastapi
            import pydantic
        except ImportError as e:
            raise ImportError(
                f"To use Web API features, please install: pip install refstore[web]"
            ) from e

    # 模块已存在，正常返回
    return globals().get(name)
