import os
import io
import uuid
import mimetypes
import requests
from typing import Optional, BinaryIO, Union, List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse
from minio import Minio
from minio.error import S3Error
from .buckets import BucketManager
from ..core.config import ConfigValidator
from ..utils.uri import URIUtils



# ============================================================
# 文件服务类
# ============================================================
class MinioFileService:
    """
    MinIO 文件服务类
    
    提供文件的上传、下载、删除、URL生成等功能
    支持逻辑桶名到物理桶名的映射
    
    Args:
        config: 配置字典，格式如下：
            {
                "minio": {
                    "endpoint": "10.31.31.41:9000",
                    "access_key": "your_key",
                    "secret_key": "your_secret",
                    "secure": False,
                },
                "bucket_map": {
                    "user": "physical-user-bucket",
                    "public": "physical-public-bucket",
                },
                "default_bucket": "user",  # 可选，默认逻辑桶名
                "presigned_expiry": 3600,  # 可选，预签名URL过期时间（秒）
            }
    """
    
    def __init__(self, config: Dict[str, Any]):
        # 验证并规范化配置
        self.config = ConfigValidator.normalize_config(config)

        minio_config = self.config.get("minio", {})

        # 解析 endpoint
        endpoint = minio_config.get("endpoint", "localhost:9000")
        secure = minio_config.get("secure", False)

        # 处理协议前缀
        if endpoint.startswith("https://"):
            endpoint = endpoint[8:]
            secure = True
        elif endpoint.startswith("http://"):
            endpoint = endpoint[7:]

        self.endpoint = endpoint
        self.secure = secure
        self.bucket_map = self.config.get("bucket_map", {})
        self.default_bucket = self.config.get("default_bucket", "user")
        self.presigned_expiry = self.config.get("presigned_expiry", 3600)
        
        # 创建 MinIO 客户端
        self.client = Minio(
            self.endpoint,
            access_key=minio_config.get("access_key", ""),
            secret_key=minio_config.get("secret_key", ""),
            secure=self.secure
        )
        
        # 初始化桶管理器
        self.bucket_manager = BucketManager(self.client)
    
    def init_buckets(self) -> None:
        """初始化所有配置的物理桶"""
        for logic_name, physical_name in self.bucket_map.items():
            self.bucket_manager.create_bucket(physical_name)
    
    def get_physical_bucket(self, logic_bucket: str) -> str:
        """逻辑桶名 -> 物理桶名"""
        return self.bucket_map.get(logic_bucket, logic_bucket)
    
    # ==========================================
    # 内部辅助方法
    # ==========================================
    
    def _generate_object_path(self, original_filename: str) -> str:
        """生成默认存储路径: 年/月/日/UUID.ext"""
        ext = os.path.splitext(original_filename)[1] if original_filename else ""
        date_path = datetime.now().strftime("%Y/%m/%d")
        unique_name = f"{uuid.uuid4().hex}{ext}"
        return f"{date_path}/{unique_name}"
    
    def _build_object_name(self, original_filename: str, path: Optional[str] = None) -> str:
        """构建对象名称"""
        if path:
            path = path.strip('/')
            return f"{path}/{original_filename}"
        return self._generate_object_path(original_filename)
    
    def _prepare_stream(self, file_data: Union[bytes, BinaryIO]) -> tuple:
        """准备数据流"""
        if isinstance(file_data, bytes):
            data_stream = io.BytesIO(file_data)
            length = len(file_data)
        else:
            data_stream = file_data
            file_data.seek(0, os.SEEK_END)
            length = file_data.tell()
            file_data.seek(0)
        return data_stream, length
    
    def _build_s3_uri(self, logic_bucket: str, object_name: str) -> str:
        """构建 S3 URI（使用逻辑桶名）"""
        return URIUtils.encode_uri(logic_bucket, object_name)
    
    def _parse_s3_uri(self, s3_uri: str) -> tuple:
        """解析 S3 URI -> (logic_bucket, object_name)"""
        return URIUtils.decode_uri(s3_uri)
    
    @staticmethod
    def _guess_content_type(file_path: str) -> str:
        """根据文件扩展名猜测内容类型"""
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or "application/octet-stream"
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"
    
    # ==========================================
    # 上传方法
    # ==========================================
    
    def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        original_filename: str = "file",
        content_type: str = "application/octet-stream",
        logic_bucket: Optional[str] = None,
        path: Optional[str] = None
    ) -> Optional[str]:
        """
        上传文件
        
        :param file_data: 文件数据（bytes 或 BinaryIO）
        :param original_filename: 原始文件名
        :param content_type: 内容类型
        :param logic_bucket: 逻辑桶名（会映射到物理桶）
        :param path: 指定的相对路径（可选）
        :return: S3 URI (如 s3://user/path/file.ext) 或 None
        """
        try:
            logic_bucket = logic_bucket or self.default_bucket
            physical_bucket = self.get_physical_bucket(logic_bucket)
            
            object_name = self._build_object_name(original_filename, path)
            data_stream, length = self._prepare_stream(file_data)
            
            # 确保物理桶存在
            self.bucket_manager.create_bucket(physical_bucket)
            
            self.client.put_object(
                physical_bucket,
                object_name,
                data_stream,
                length,
                content_type=content_type
            )
            
            return self._build_s3_uri(logic_bucket, object_name)
        except Exception as e:
            print(f"[MinioFileService] 上传失败: {e}")
            return None
    
    def upload_from_local(
        self,
        local_path: str,
        logic_bucket: Optional[str] = None,
        path: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """从本地路径上传文件"""
        try:
            if not os.path.exists(local_path):
                print(f"[MinioFileService] 本地文件不存在: {local_path}")
                return None
            
            original_filename = os.path.basename(local_path)
            if not content_type:
                content_type = self._guess_content_type(local_path)
            
            with open(local_path, 'rb') as f:
                return self.upload_file(
                    file_data=f,
                    original_filename=original_filename,
                    content_type=content_type,
                    logic_bucket=logic_bucket,
                    path=path
                )
        except Exception as e:
            print(f"[MinioFileService] 从本地上传失败: {e}")
            return None
    
    def upload_from_url(
        self,
        url: str,
        logic_bucket: Optional[str] = None,
        path: Optional[str] = None,
        timeout: int = 30
    ) -> Optional[str]:
        """从 URL 下载并上传文件"""
        try:
            resp = requests.get(url, stream=True, timeout=timeout)
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', 'application/octet-stream')
                filename = os.path.basename(urlparse(url).path) or "downloaded_file"
                file_stream = io.BytesIO(resp.content)
                
                return self.upload_file(
                    file_data=file_stream,
                    original_filename=filename,
                    content_type=content_type,
                    logic_bucket=logic_bucket,
                    path=path
                )
            print(f"[MinioFileService] URL 请求失败，状态码: {resp.status_code}")
            return None
        except Exception as e:
            print(f"[MinioFileService] 从 URL 上传失败: {e}")
            return None
    
    # ==========================================
    # 下载方法
    # ==========================================
    
    def download_file(self, s3_uri: str) -> Optional[bytes]:
        """下载文件到内存"""
        try:
            logic_bucket, object_name = self._parse_s3_uri(s3_uri)
            physical_bucket = self.get_physical_bucket(logic_bucket)
            
            response = self.client.get_object(physical_bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            print(f"[MinioFileService] 下载失败: {e}")
            return None
    
    def download_to_local(
        self,
        s3_uri: str,
        local_path: str,
        create_dirs: bool = True
    ) -> bool:
        """下载文件到本地路径"""
        try:
            if create_dirs:
                dir_path = os.path.dirname(local_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
            
            data = self.download_file(s3_uri)
            if data is None:
                return False
            
            with open(local_path, 'wb') as f:
                f.write(data)
            return True
        except Exception as e:
            print(f"[MinioFileService] 下载到本地失败: {e}")
            return False
    
    # ==========================================
    # URL 生成方法
    # ==========================================
    
    def get_presigned_url(
        self,
        s3_uri: str,
        expiry_seconds: int = None,
        method: str = "GET"
    ) -> Optional[str]:
        """生成预签名 URL"""
        try:
            logic_bucket, object_name = self._parse_s3_uri(s3_uri)
            physical_bucket = self.get_physical_bucket(logic_bucket)
            expiry = expiry_seconds or self.presigned_expiry
            
            url = self.client.get_presigned_url(
                method,
                physical_bucket,
                object_name,
                expires=timedelta(seconds=expiry)
            )
            return url
        except Exception as e:
            print(f"[MinioFileService] 生成预签名 URL 失败: {e}")
            return None
    
    def get_download_url(self, s3_uri: str, expiry_seconds: int = None) -> Optional[str]:
        """生成下载 URL"""
        return self.get_presigned_url(s3_uri, expiry_seconds, "GET")
    
    # ==========================================
    # 文件信息方法
    # ==========================================
    
    def get_file_info(self, s3_uri: str) -> Optional[Dict[str, Any]]:
        """根据 URI 获取文件信息"""
        try:
            logic_bucket, object_name = self._parse_s3_uri(s3_uri)
            physical_bucket = self.get_physical_bucket(logic_bucket)
            stat = self.client.stat_object(physical_bucket, object_name)
            
            return {
                "logic_bucket": logic_bucket,
                "physical_bucket": physical_bucket,
                "object_name": object_name,
                "size": stat.size,
                "size_human": self._format_size(stat.size),
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "metadata": stat.metadata
            }
        except Exception as e:
            print(f"[MinioFileService] 获取文件信息失败: {e}")
            return None
    
    def file_exists(self, s3_uri: str) -> bool:
        """检查文件是否存在"""
        try:
            logic_bucket, object_name = self._parse_s3_uri(s3_uri)
            physical_bucket = self.get_physical_bucket(logic_bucket)
            self.client.stat_object(physical_bucket, object_name)
            return True
        except:
            return False
    
    # ==========================================
    # 删除方法
    # ==========================================
    
    def delete_file(self, s3_uri: str) -> bool:
        """删除文件"""
        try:
            logic_bucket, object_name = self._parse_s3_uri(s3_uri)
            physical_bucket = self.get_physical_bucket(logic_bucket)
            self.client.remove_object(physical_bucket, object_name)
            return True
        except Exception as e:
            print(f"[MinioFileService] 删除文件失败: {e}")
            return False
    
    def delete_files(self, s3_uris: List[str]) -> Dict[str, Any]:
        """批量删除文件"""
        deleted = []
        failed = []
        
        for uri in s3_uris:
            if self.delete_file(uri):
                deleted.append(uri)
            else:
                failed.append(uri)
        
        return {"deleted": deleted, "failed": failed}
    
    # ==========================================
    # 列表方法
    # ==========================================
    
    def list_files(
        self,
        logic_bucket: Optional[str] = None,
        prefix: str = "",
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """列出桶中的文件"""
        try:
            logic_bucket = logic_bucket or self.default_bucket
            physical_bucket = self.get_physical_bucket(logic_bucket)
            objects = self.client.list_objects(physical_bucket, prefix=prefix, recursive=recursive)
            
            return [
                {
                    "object_name": obj.object_name,
                    "size": obj.size,
                    "size_human": self._format_size(obj.size) if obj.size else "0 B",
                    "last_modified": obj.last_modified,
                    "is_dir": obj.is_dir,
                    "s3_uri": self._build_s3_uri(logic_bucket, obj.object_name)
                }
                for obj in objects
            ]
        except Exception as e:
            print(f"[MinioFileService] 列出文件失败: {e}")
            return []