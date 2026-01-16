"""配置验证和管理模块"""

from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from .exceptions import ConfigError, ConnectionError


class ConfigValidator:
    """配置验证器"""

    # 配置结构 Schema
    CONFIG_SCHEMA = {
        "type": "object",
        "required": ["minio"],
        "properties": {
            "minio": {
                "type": "object",
                "required": ["endpoint", "access_key", "secret_key"],
                "properties": {
                    "endpoint": {"type": "string"},
                    "access_key": {"type": "string"},
                    "secret_key": {"type": "string"},
                    "secure": {"type": "boolean", "default": False},
                },
            },
            "bucket_map": {
                "type": "object",
                "description": "逻辑桶名到物理桶名的映射",
            },
            "default_bucket": {"type": "string", "default": "user"},
            "presigned_expiry": {"type": "integer", "default": 3600},
        },
    }

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置字典

        Args:
            config: 配置字典

        Returns:
            验证后的配置字典

        Raises:
            ConfigError: 配置无效时
        """
        if not isinstance(config, dict):
            raise ConfigError("配置必须是一个字典")

        # 验证 minio 配置
        if "minio" not in config:
            raise ConfigError("缺少 minio 配置")

        minio_config = config["minio"]

        required_minio_fields = ["endpoint", "access_key", "secret_key"]
        for field in required_minio_fields:
            if field not in minio_config:
                raise ConfigError(f"minio 配置缺少必需字段: {field}")
            if not minio_config[field]:
                raise ConfigError(f"minio.{field} 不能为空")

        # 验证 endpoint 格式
        endpoint = minio_config["endpoint"]
        cls._validate_endpoint(endpoint)

        # 验证 bucket_map
        if "bucket_map" in config:
            if not isinstance(config["bucket_map"], dict):
                raise ConfigError("bucket_map 必须是一个字典")

        # 设置默认值
        if "secure" not in minio_config:
            minio_config["secure"] = False

        if "default_bucket" not in config:
            config["default_bucket"] = "user"

        if "presigned_expiry" not in config:
            config["presigned_expiry"] = 3600

        # 验证 presigned_expiry
        if not isinstance(config["presigned_expiry"], int) or config["presigned_expiry"] <= 0:
            raise ConfigError("presigned_expiry 必须是正整数")

        return config

    @staticmethod
    def _validate_endpoint(endpoint: str) -> None:
        """验证 endpoint 格式"""
        if not isinstance(endpoint, str) or not endpoint.strip():
            raise ConfigError("endpoint 不能为空字符串")

        # 移除协议前缀（如果存在）
        if endpoint.startswith("https://"):
            endpoint = endpoint[8:]
        elif endpoint.startswith("http://"):
            endpoint = endpoint[7:]

        # 验证格式: host:port
        if ":" not in endpoint:
            raise ConfigError(f"endpoint 格式无效，应为 'host:port': {endpoint}")

        host, port = endpoint.rsplit(":", 1)

        if not host.strip():
            raise ConfigError(f"endpoint 中的 host 不能为空")

        try:
            port_num = int(port)
            if port_num <= 0 or port_num > 65535:
                raise ConfigError(f"endpoint 中的端口号无效: {port}")
        except ValueError:
            raise ConfigError(f"endpoint 中的端口号必须是整数: {port}")

    @classmethod
    def test_connection(cls, config: Dict[str, Any]) -> bool:
        """
        测试 MinIO 连接

        Args:
            config: 配置字典

        Returns:
            连接成功返回 True，否则返回 False

        Raises:
            ConfigError: 配置无效时
            ConnectionError: 连接失败时
        """
        # 先验证配置
        config = cls.validate_config(config)

        minio_config = config["minio"]

        # 处理 endpoint
        endpoint = minio_config["endpoint"]
        if endpoint.startswith("https://"):
            endpoint = endpoint[8:]
            secure = True
        elif endpoint.startswith("http://"):
            endpoint = endpoint[7:]
            secure = False
        else:
            secure = minio_config.get("secure", False)

        try:
            # 创建 MinIO 客户端
            client = Minio(
                endpoint,
                access_key=minio_config["access_key"],
                secret_key=minio_config["secret_key"],
                secure=secure,
            )

            # 测试连接
            client.list_buckets()
            return True

        except S3Error as e:
            raise ConnectionError(f"MinIO 连接失败 (S3Error): {e}")
        except Exception as e:
            raise ConnectionError(f"MinIO 连接失败: {e}")

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """获取配置结构的 Schema"""
        return cls.CONFIG_SCHEMA

    @classmethod
    def normalize_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        规范化配置字典

        Args:
            config: 原始配置

        Returns:
            规范化后的配置
        """
        config = cls.validate_config(config.copy())

        # 确保 minio 配置包含所有必需字段
        if "bucket_map" not in config:
            config["bucket_map"] = {}

        return config
