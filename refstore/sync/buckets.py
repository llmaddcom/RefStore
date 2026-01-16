from minio import Minio
from minio.error import S3Error
from typing import List, Dict, Any, Optional

# ============================================================
# 桶管理类
# ============================================================
class BucketManager:
    """
    MinIO 桶管理类
    
    提供桶的创建、删除、查询等管理功能
    """
    
    def __init__(self, client: Minio):
        self.client = client
    
    def create_bucket(self, bucket_name: str, location: str = None) -> bool:
        """创建桶"""
        try:
            if not self.bucket_exists(bucket_name):
                if location:
                    self.client.make_bucket(bucket_name, location=location)
                else:
                    self.client.make_bucket(bucket_name)
                print(f"[BucketManager] 桶 '{bucket_name}' 创建成功")
                return True
            return True
        except S3Error as e:
            print(f"[BucketManager] 创建桶失败: {e}")
            return False
    
    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """删除桶"""
        try:
            if not self.bucket_exists(bucket_name):
                return True
            
            if force:
                self._clear_bucket(bucket_name)
            
            self.client.remove_bucket(bucket_name)
            print(f"[BucketManager] 桶 '{bucket_name}' 删除成功")
            return True
        except S3Error as e:
            print(f"[BucketManager] 删除桶失败: {e}")
            return False
    
    def _clear_bucket(self, bucket_name: str) -> None:
        """清空桶内所有对象"""
        try:
            objects = self.client.list_objects(bucket_name, recursive=True)
            for obj in objects:
                self.client.remove_object(bucket_name, obj.object_name)
        except S3Error as e:
            print(f"[BucketManager] 清空桶失败: {e}")
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """检查桶是否存在"""
        try:
            return self.client.bucket_exists(bucket_name)
        except S3Error:
            return False
    
    def list_buckets(self) -> List[Dict[str, Any]]:
        """列出所有桶"""
        try:
            buckets = self.client.list_buckets()
            return [
                {"name": b.name, "creation_date": b.creation_date}
                for b in buckets
            ]
        except S3Error as e:
            print(f"[BucketManager] 列出桶失败: {e}")
            return []
    
    def get_bucket_info(self, bucket_name: str) -> Optional[Dict[str, Any]]:
        """获取桶信息"""
        try:
            if not self.bucket_exists(bucket_name):
                return None
            
            objects = list(self.client.list_objects(bucket_name, recursive=True))
            total_size = sum(obj.size for obj in objects)
            
            return {
                "name": bucket_name,
                "exists": True,
                "object_count": len(objects),
                "total_size": total_size,
                "total_size_human": self._format_size(total_size)
            }
        except S3Error as e:
            print(f"[BucketManager] 获取桶信息失败: {e}")
            return None
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"