"""RefStore 自定义异常类"""


class RefStoreError(Exception):
    """RefStore 基础异常"""
    pass


class ConfigError(RefStoreError):
    """配置错误"""
    pass


class ConnectionError(RefStoreError):
    """连接错误"""
    pass


class BucketNotFoundError(RefStoreError):
    """桶不存在错误"""
    pass


class FileNotFoundError(RefStoreError):
    """文件不存在错误"""
    pass


class URIParseError(RefStoreError):
    """URI 解析错误"""
    pass


class UploadError(RefStoreError):
    """上传错误"""
    pass


class DownloadError(RefStoreError):
    """下载错误"""
    pass
