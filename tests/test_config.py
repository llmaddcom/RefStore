"""
配置验证模块测试
"""

import pytest
from refstore.core.config import ConfigValidator
from refstore.core.exceptions import ConfigError, ConnectionError


class TestConfigValidator:
    """配置验证器测试"""

    def test_valid_config(self):
        """测试有效配置"""
        config = {
            "minio": {
                "endpoint": "localhost:9000",
                "access_key": "test_key",
                "secret_key": "test_secret",
                "secure": False,
            },
            "bucket_map": {
                "user": "physical-user-bucket",
            },
        }

        validated = ConfigValidator.validate_config(config)
        assert validated is not None
        assert "minio" in validated

    def test_missing_minio_config(self):
        """测试缺少 minio 配置"""
        config = {
            "bucket_map": {},
        }

        with pytest.raises(ConfigError, match="缺少 minio 配置"):
            ConfigValidator.validate_config(config)

    def test_missing_endpoint(self):
        """测试缺少 endpoint"""
        config = {
            "minio": {
                "access_key": "test_key",
                "secret_key": "test_secret",
            },
        }

        with pytest.raises(ConfigError, match="endpoint"):
            ConfigValidator.validate_config(config)

    def test_missing_access_key(self):
        """测试缺少 access_key"""
        config = {
            "minio": {
                "endpoint": "localhost:9000",
                "secret_key": "test_secret",
            },
        }

        with pytest.raises(ConfigError, match="access_key"):
            ConfigValidator.validate_config(config)

    def test_invalid_endpoint_format(self):
        """测试无效的 endpoint 格式"""
        config = {
            "minio": {
                "endpoint": "localhost",
                "access_key": "test_key",
                "secret_key": "test_secret",
            },
        }

        with pytest.raises(ConfigError, match="endpoint 格式无效"):
            ConfigValidator.validate_config(config)

    def test_endpoint_with_protocol(self):
        """测试带协议前缀的 endpoint"""
        config = {
            "minio": {
                "endpoint": "http://localhost:9000",
                "access_key": "test_key",
                "secret_key": "test_secret",
            },
        }

        validated = ConfigValidator.validate_config(config)
        assert validated is not None

    def test_endpoint_with_https_protocol(self):
        """测试带 HTTPS 协议前缀的 endpoint"""
        config = {
            "minio": {
                "endpoint": "https://localhost:9000",
                "access_key": "test_key",
                "secret_key": "test_secret",
            },
        }

        validated = ConfigValidator.validate_config(config)
        assert validated is not None
        assert validated["minio"]["secure"] == True

    def test_default_values(self):
        """测试默认值设置"""
        config = {
            "minio": {
                "endpoint": "localhost:9000",
                "access_key": "test_key",
                "secret_key": "test_secret",
            },
        }

        validated = ConfigValidator.validate_config(config)
        assert "bucket_map" in validated
        assert "default_bucket" in validated
        assert validated["default_bucket"] == "user"
        assert "presigned_expiry" in validated
        assert validated["presigned_expiry"] == 3600

    def test_invalid_presigned_expiry(self):
        """测试无效的 presigned_expiry"""
        config = {
            "minio": {
                "endpoint": "localhost:9000",
                "access_key": "test_key",
                "secret_key": "test_secret",
            },
            "presigned_expiry": -1,
        }

        with pytest.raises(ConfigError, match="presigned_expiry"):
            ConfigValidator.validate_config(config)

    def test_normalize_config(self):
        """测试配置规范化"""
        config = {
            "minio": {
                "endpoint": "localhost:9000",
                "access_key": "test_key",
                "secret_key": "test_secret",
            },
        }

        normalized = ConfigValidator.normalize_config(config)
        assert normalized is not None
        assert "bucket_map" in normalized

    def test_get_config_schema(self):
        """测试获取配置 Schema"""
        schema = ConfigValidator.get_config_schema()
        assert schema is not None
        assert "type" in schema
        assert "required" in schema

    def test_connection_failure(self):
        """测试连接失败（假设没有真实的 MinIO 服务）"""
        config = {
            "minio": {
                "endpoint": "localhost:9000",
                "access_key": "test_key",
                "secret_key": "test_secret",
            },
        }

        with pytest.raises(ConnectionError):
            ConfigValidator.test_connection(config)
