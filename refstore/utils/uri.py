"""URI 编码/解码工具模块"""

import re
from typing import Tuple, Optional
from urllib.parse import urlparse

from ..core.exceptions import URIParseError


class URIUtils:
    """URI 工具类"""

    # S3 URI 正则表达式
    S3_URI_PATTERN = re.compile(r'^s3://([^/]+)/(.+)$')

    @staticmethod
    def encode_uri(logic_bucket: str, object_name: str) -> str:
        """
        编码 S3 URI

        Args:
            logic_bucket: 逻辑桶名
            object_name: 对象名称（相对路径）

        Returns:
            S3 URI 字符串 (格式: s3://bucket/path/to/file)

        Raises:
            ValueError: 参数无效时
        """
        if not logic_bucket:
            raise ValueError("逻辑桶名不能为空")

        if not object_name:
            raise ValueError("对象名称不能为空")

        # 规范化路径：移除开头的和结尾的斜杠
        object_name = object_name.strip('/')

        # 构建标准化的 URI
        uri = f"s3://{logic_bucket}/{object_name}"
        return uri

    @staticmethod
    def decode_uri(s3_uri: str) -> Tuple[str, str]:
        """
        解码 S3 URI

        Args:
            s3_uri: S3 URI 字符串 (格式: s3://bucket/path/to/file)

        Returns:
            (logic_bucket, object_name) 元组

        Raises:
            URIParseError: URI 格式无效时
        """
        if not s3_uri:
            raise URIParseError("URI 不能为空")

        # 验证 URI 格式
        if not s3_uri.startswith("s3://"):
            raise URIParseError(f"无效的 S3 URI 格式，应以 's3://' 开头: {s3_uri}")

        # 使用正则表达式解析
        match = URIUtils.S3_URI_PATTERN.match(s3_uri)
        if not match:
            raise URIParseError(f"无效的 S3 URI 格式: {s3_uri}")

        logic_bucket = match.group(1)
        object_name = match.group(2)

        if not logic_bucket:
            raise URIParseError(f"URI 中缺少桶名: {s3_uri}")

        if not object_name:
            raise URIParseError(f"URI 中缺少对象名称: {s3_uri}")

        return logic_bucket, object_name

    @staticmethod
    def validate_uri(s3_uri: str) -> bool:
        """
        验证 S3 URI 格式是否有效

        Args:
            s3_uri: S3 URI 字符串

        Returns:
            URI 有效返回 True，否则返回 False
        """
        try:
            URIUtils.decode_uri(s3_uri)
            return True
        except URIParseError:
            return False

    @staticmethod
    def get_bucket_from_uri(s3_uri: str) -> Optional[str]:
        """
        从 URI 中提取桶名

        Args:
            s3_uri: S3 URI 字符串

        Returns:
            桶名，如果 URI 无效则返回 None
        """
        try:
            logic_bucket, _ = URIUtils.decode_uri(s3_uri)
            return logic_bucket
        except URIParseError:
            return None

    @staticmethod
    def get_object_name_from_uri(s3_uri: str) -> Optional[str]:
        """
        从 URI 中提取对象名称

        Args:
            s3_uri: S3 URI 字符串

        Returns:
            对象名称，如果 URI 无效则返回 None
        """
        try:
            _, object_name = URIUtils.decode_uri(s3_uri)
            return object_name
        except URIParseError:
            return None

    @staticmethod
    def get_file_extension(s3_uri: str) -> Optional[str]:
        """
        从 URI 中提取文件扩展名

        Args:
            s3_uri: S3 URI 字符串

        Returns:
            文件扩展名（包含点，如 '.txt'），如果没有扩展名则返回空字符串
        """
        try:
            _, object_name = URIUtils.decode_uri(s3_uri)
            # 获取对象名称的最后部分
            filename = object_name.split('/')[-1]
            # 提取扩展名
            ext = None
            if '.' in filename:
                ext = filename.rsplit('.', 1)[1]
                return f".{ext}" if ext else ""
            return ""
        except URIParseError:
            return None

    @staticmethod
    def normalize_uri(s3_uri: str) -> str:
        """
        规范化 URI（移除多余的斜杠等）

        Args:
            s3_uri: S3 URI 字符串

        Returns:
            规范化后的 URI

        Raises:
            URIParseError: URI 格式无效时
        """
        logic_bucket, object_name = URIUtils.decode_uri(s3_uri)
        return URIUtils.encode_uri(logic_bucket, object_name)

    @staticmethod
    def join_uri(base_uri: str, relative_path: str) -> str:
        """
        将相对路径连接到基础 URI

        Args:
            base_uri: 基础 S3 URI
            relative_path: 相对路径

        Returns:
            组合后的 URI

        Raises:
            URIParseError: URI 格式无效时
        """
        logic_bucket, object_name = URIUtils.decode_uri(base_uri)

        # 规范化路径
        relative_path = relative_path.strip('/')

        if object_name:
            # 基础 URI 有对象名称，作为目录
            combined_object_name = f"{object_name}/{relative_path}"
        else:
            # 基础 URI 只有桶名
            combined_object_name = relative_path

        return URIUtils.encode_uri(logic_bucket, combined_object_name)

    @staticmethod
    def get_parent_uri(s3_uri: str) -> str:
        """
        获取父级 URI

        Args:
            s3_uri: S3 URI 字符串

        Returns:
            父级 URI

        Raises:
            URIParseError: URI 格式无效时
        """
        logic_bucket, object_name = URIUtils.decode_uri(s3_uri)

        # 找到最后一个斜杠的位置
        last_slash = object_name.rfind('/')
        if last_slash == -1:
            # 对象名称没有目录，只返回桶名
            return URIUtils.encode_uri(logic_bucket, "")

        # 获取父级目录
        parent_object_name = object_name[:last_slash]
        return URIUtils.encode_uri(logic_bucket, parent_object_name)

    @staticmethod
    def parse_filename(object_name: str) -> Tuple[str, str]:
        """
        从对象名称中解析目录和文件名

        Args:
            object_name: 对象名称

        Returns:
            (directory, filename) 元组
        """
        if '/' in object_name:
            directory, filename = object_name.rsplit('/', 1)
        else:
            directory = ""
            filename = object_name

        return directory, filename


# 为了向后兼容，提供函数级别的接口
encode_uri = URIUtils.encode_uri
decode_uri = URIUtils.decode_uri
validate_uri = URIUtils.validate_uri
get_bucket_from_uri = URIUtils.get_bucket_from_uri
get_object_name_from_uri = URIUtils.get_object_name_from_uri
get_file_extension = URIUtils.get_file_extension
normalize_uri = URIUtils.normalize_uri
join_uri = URIUtils.join_uri
get_parent_uri = URIUtils.get_parent_uri
parse_filename = URIUtils.parse_filename
