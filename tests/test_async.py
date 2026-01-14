"""
异步 API 测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from refstore._async.file_service import AsyncMinioFileService
from refstore._async.buckets import AsyncBucketManager


class TestAsyncMinioFileService:
    """异步文件服务测试"""

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
            },
            "default_bucket": "user",
            "presigned_expiry": 3600,
        }

    @pytest.mark.asyncio
    async def test_init(self, config):
        """测试初始化"""
        with patch('refstore.async.file_service.SyncMinioFileService'):
            service = AsyncMinioFileService(config)
            assert service.endpoint == "localhost:9000"
            assert service.default_bucket == "user"
            await service.close()

    @pytest.mark.asyncio
    async def test_get_physical_bucket(self, config):
        """测试获取物理桶名"""
        with patch('refstore.async.file_service.SyncMinioFileService'):
            service = AsyncMinioFileService(config)
            bucket = service.get_physical_bucket("user")
            assert bucket == "physical-user-bucket"
            await service.close()

    @pytest.mark.asyncio
    async def test_properties(self, config):
        """测试属性访问"""
        with patch('refstore.async.file_service.SyncMinioFileService'):
            service = AsyncMinioFileService(config)
            assert service.endpoint == "localhost:9000"
            assert service.secure == False
            assert service.bucket_map == {"user": "physical-user-bucket"}
            assert service.default_bucket == "user"
            assert service.presigned_expiry == 3600
            await service.close()


class TestAsyncBucketManager:
    """异步桶管理器测试"""

    @pytest.fixture
    def mock_client(self):
        """模拟 MinIO 客户端"""
        return Mock()

    @pytest.mark.asyncio
    async def test_init(self, mock_client):
        """测试初始化"""
        manager = AsyncBucketManager(mock_client)
        assert manager.client == mock_client
        await manager.close()

    @pytest.mark.asyncio
    async def test_create_bucket(self, mock_client):
        """测试创建桶"""
        with patch('refstore.async.buckets.SyncBucketManager') as mock_sync:
            mock_sync_manager = Mock()
            mock_sync.return_value = mock_sync_manager
            mock_sync_manager.create_bucket.return_value = True

            manager = AsyncBucketManager(mock_client)
            result = await manager.create_bucket("test-bucket")
            assert result == True
            await manager.close()

    @pytest.mark.asyncio
    async def test_bucket_exists(self, mock_client):
        """测试检查桶是否存在"""
        with patch('refstore.async.buckets.SyncBucketManager') as mock_sync:
            mock_sync_manager = Mock()
            mock_sync.return_value = mock_sync_manager
            mock_sync_manager.bucket_exists.return_value = True

            manager = AsyncBucketManager(mock_client)
            result = await manager.bucket_exists("test-bucket")
            assert result == True
            await manager.close()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_client):
        """测试上下文管理器"""
        async with AsyncBucketManager(mock_client) as manager:
            assert manager is not None
        # 上下文退出后应该关闭资源
