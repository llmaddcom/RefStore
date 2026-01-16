"""
URI 工具模块测试
"""

import pytest
from refstore.utils.uri import (
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
)
from refstore.core.exceptions import URIParseError


class TestURIUtils:
    """URI 工具类测试"""

    def test_encode_uri(self):
        """测试 URI 编码"""
        uri = URIUtils.encode_uri("user", "path/to/file.txt")
        assert uri == "s3://user/path/to/file.txt"

    def test_encode_uri_with_leading_slash(self):
        """测试带前导斜杠的 URI 编码"""
        uri = URIUtils.encode_uri("user", "/path/to/file.txt")
        assert uri == "s3://user/path/to/file.txt"

    def test_encode_uri_with_trailing_slash(self):
        """测试带尾随斜杠的 URI 编码"""
        uri = URIUtils.encode_uri("user", "path/to/file.txt/")
        # 应该移除尾部斜杠
        assert "s3://user/path/to/file.txt" == uri

    def test_encode_uri_empty_bucket(self):
        """测试空桶名"""
        with pytest.raises(ValueError):
            URIUtils.encode_uri("", "path/to/file.txt")

    def test_encode_uri_empty_object_name(self):
        """测试空对象名称"""
        with pytest.raises(ValueError):
            URIUtils.encode_uri("user", "")

    def test_decode_uri(self):
        """测试 URI 解码"""
        logic_bucket, object_name = URIUtils.decode_uri("s3://user/path/to/file.txt")
        assert logic_bucket == "user"
        assert object_name == "path/to/file.txt"

    def test_decode_uri_without_s3_prefix(self):
        """测试不带 s3:// 前缀的 URI"""
        with pytest.raises(URIParseError):
            URIUtils.decode_uri("user/path/to/file.txt")

    def test_decode_uri_empty_uri(self):
        """测试空 URI"""
        with pytest.raises(URIParseError):
            URIUtils.decode_uri("")

    def test_decode_uri_invalid_format(self):
        """测试无效格式的 URI"""
        with pytest.raises(URIParseError):
            URIUtils.decode_uri("s3://")

    def test_validate_uri(self):
        """测试 URI 验证"""
        assert URIUtils.validate_uri("s3://user/path/to/file.txt") == True
        assert URIUtils.validate_uri("user/path/to/file.txt") == False
        assert URIUtils.validate_uri("") == False

    def test_get_bucket_from_uri(self):
        """测试从 URI 提取桶名"""
        bucket = URIUtils.get_bucket_from_uri("s3://user/path/to/file.txt")
        assert bucket == "user"

    def test_get_bucket_from_uri_invalid(self):
        """测试从无效 URI 提取桶名"""
        bucket = URIUtils.get_bucket_from_uri("user/path/to/file.txt")
        assert bucket is None

    def test_get_object_name_from_uri(self):
        """测试从 URI 提取对象名称"""
        object_name = URIUtils.get_object_name_from_uri("s3://user/path/to/file.txt")
        assert object_name == "path/to/file.txt"

    def test_get_object_name_from_uri_invalid(self):
        """测试从无效 URI 提取对象名称"""
        object_name = URIUtils.get_object_name_from_uri("user/path/to/file.txt")
        assert object_name is None

    def test_get_file_extension(self):
        """测试获取文件扩展名"""
        ext = URIUtils.get_file_extension("s3://user/path/to/file.txt")
        assert ext == ".txt"

    def test_get_file_extension_no_extension(self):
        """测试没有扩展名的文件"""
        ext = URIUtils.get_file_extension("s3://user/path/to/file")
        assert ext == ""

    def test_get_file_extension_multiple_dots(self):
        """测试多个点的文件名"""
        ext = URIUtils.get_file_extension("s3://user/path/to/file.tar.gz")
        assert ext == ".gz"

    def test_normalize_uri(self):
        """测试 URI 规范化"""
        uri = URIUtils.normalize_uri("s3://user//path//to//file.txt")
        # 移除多余的斜杠
        assert uri == "s3://user/path/to/file.txt"

    def test_join_uri(self):
        """测试 URI 连接"""
        base_uri = "s3://user/path"
        relative_path = "to/file.txt"
        combined = URIUtils.join_uri(base_uri, relative_path)
        assert combined == "s3://user/path/to/file.txt"

    def test_join_uri_with_slashes(self):
        """测试带斜杠的 URI 连接"""
        base_uri = "s3://user/path"
        relative_path = "/to/file.txt"
        combined = URIUtils.join_uri(base_uri, relative_path)
        assert combined == "s3://user/path/to/file.txt"

    def test_join_uri_bucket_only(self):
        """测试只有桶名的 URI 连接"""
        base_uri = "s3://user"
        relative_path = "to/file.txt"
        combined = URIUtils.join_uri(base_uri, relative_path)
        assert combined == "s3://user/to/file.txt"

    def test_get_parent_uri(self):
        """测试获取父级 URI"""
        uri = "s3://user/path/to/file.txt"
        parent = URIUtils.get_parent_uri(uri)
        assert parent == "s3://user/path/to"

    def test_get_parent_uri_no_parent(self):
        """测试没有父级的 URI"""
        uri = "s3://user/file.txt"
        parent = URIUtils.get_parent_uri(uri)
        assert parent == "s3://user"

    def test_function_level_api(self):
        """测试函数级别的 API"""
        uri = encode_uri("user", "path/to/file.txt")
        assert uri == "s3://user/path/to/file.txt"

        logic_bucket, object_name = decode_uri(uri)
        assert logic_bucket == "user"
        assert object_name == "path/to/file.txt"

        assert validate_uri(uri) == True
        assert get_bucket_from_uri(uri) == "user"
        assert get_object_name_from_uri(uri) == "path/to/file.txt"
        assert get_file_extension(uri) == ".txt"
