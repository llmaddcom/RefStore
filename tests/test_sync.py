"""
同步 API 测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from refstore.sync.file_service import MinioFileService
from refstore.sync.buckets import BucketManager
from refstore.core.config import ConfigValidator


class TestMinioFileService:
    """同步文件服务测试"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            "minio": {
                "endpoint": "localhost:9000",
                "access_key": "test_key",
                "secret_key": "test_secret",
                "secure": False,
            },
            "bucket_map": {
                "user": "physical-user-bucket",
                "public": "physical-public-bucket",
            },
            "default_bucket": "user",
            "presigned_expiry": 3600,
        }

    def test_init(self, config):
        """测试初始化"""
        with patch('refstore.sync.file_service.Minio'):
            service = MinioFileService(config)
            assert service.endpoint == "localhost:9000"
            assert service.secure == False
            assert service.default_bucket == "user"
            assert service.presigned_expiry == 3600
            assert service.bucket_map == {
                "user": "physical-user-bucket",
                "public": "physical-public-bucket",
            }

    def test_get_physical_bucket(self, config):
        """测试获取物理桶名"""
        with patch('refstore.sync.file_service.Minio'):
            service = MinioFileService(config)
            assert service.get_physical_bucket("user") == "physical-user-bucket"
            assert service.get_physical_bucket("public") == "physical-public-bucket"
            assert service.get_physical_bucket("unknown") == "unknown"

    def test_build_s3_uri(self, config):
        """测试构建 S3 URI"""
        with patch('refstore.sync.file_service.Minio'):
            service = MinioFileService(config)
            uri = service._build_s3_uri("user", "path/to/file.txt")
            assert uri == "s3://user/path/to/file.txt"

    def test_parse_s3_uri(self, config):
        """测试解析 S3 URI"""
        with patch('refstore.sync.file_service.Minio'):
            service = MinioFileService(config)
            logic_bucket, object_name = service._parse_s3_uri("s3://user/path/to/file.txt")
            assert logic_bucket == "user"
            assert object_name == "path/to/file.txt"

    def test_parse_s3_uri_invalid(self, config):
        """测试解析无效的 S3 URI"""
        with patch('refstore.sync.file_service.Minio'):
            service = MinioFileService(config)
            with pytest.raises(Exception):
                service._parse_s3_uri("invalid-uri")

    def test_generate_object_path(self, config):
        """测试生成对象路径"""
        with patch('refstore.sync.file_service.Minio'):
            service = MinioFileService(config)
            path = service._generate_object_path("test.txt")
            # 应该是 年/月/日/UUID.ext 格式
            assert path.count('/') == 3
            assert path.endswith(".txt")

    def test_format_size(self, config):
        """测试格式化文件大小"""
        with patch('refstore.sync.file_service.Minio'):
            service = MinioFileService(config)
            assert service._format_size(100) == "100.00 B"
            assert "KB" in service._format_size(1500)
            assert "MB" in service._format_size(2000000)


class TestBucketManager:
    """桶管理器测试"""

    @pytest.fixture
    def mock_client(self):
        """模拟 MinIO 客户端"""
        return Mock()

    def test_init(self, mock_client):
        """测试初始化"""
        manager = BucketManager(mock_client)
        assert manager.client == mock_client

    def test_create_bucket(self, mock_client):
        """测试创建桶"""
        mock_client.bucket_exists.return_value = False
        mock_client.make_bucket.return_value = None

        manager = BucketManager(mock_client)
        result = manager.create_bucket("test-bucket")
        assert result == True

    def test_create_bucket_already_exists(self, mock_client):
        """测试创建已存在的桶"""
        mock_client.bucket_exists.return_value = True

        manager = BucketManager(mock_client)
        result = manager.create_bucket("test-bucket")
        assert result == True

    def test_delete_bucket(self, mock_client):
        """测试删除桶"""
        mock_client.bucket_exists.return_value = True
        mock_client.remove_bucket.return_value = None

        manager = BucketManager(mock_client)
        result = manager.delete_bucket("test-bucket")
        assert result == True

    def test_bucket_exists(self, mock_client):
        """测试检查桶是否存在"""
        mock_client.bucket_exists.return_value = True

        manager = BucketManager(mock_client)
        result = manager.bucket_exists("test-bucket")
        assert result == True
