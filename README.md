# RefStore

[![PyPI version](https://img.shields.io/pypi/v/refstore)](https://pypi.org/project/refstore/)
[![Python versions](https://img.shields.io/pypi/pyversions/refstore)](https://pypi.org/project/refstore/)
[![License](https://img.shields.io/pypi/l/refstore)](LICENSE)
[![codecov](https://codecov.io/gh/yourusername/refstore/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/refstore)

简单易用的 MinIO 对象存储服务封装库，支持集中式文件网关。

## 特性

- **同步/异步 API** - 提供完整的同步和异步接口
- **Web API (FastAPI)** - 基于 FastAPI 的 RESTful 接口
- **集中式文件网关** - 多项目共享网关，通过 GatewayClient SDK 连接
- **S3 URI 编码/解码** - 统一的文件标识：`s3://bucket/path/to/file`
- **可选逻辑桶名映射** - 默认关闭，遵循 AWS S3 最佳实践（使用 Prefix 隔离）
- **配置验证** - 内置配置格式验证和连接测试
- **重试机制** - 带指数退避的自动重试
- **完整的文档和示例** - 包含丰富的使用示例和测试用例

## 安装

### 基础安装

```bash
pip install refstore
```

### 完整安装（包含 Web API）

```bash
pip install refstore[web]
```

### 网关客户端安装（包含异步网关 SDK）

```bash
pip install refstore[gateway]
```

### 开发安装

```bash
pip install refstore[dev]
```

### 全部安装

```bash
pip install refstore[all]
```

## 快速开始

### 基础用法（桶映射关闭，推荐）

默认模式下，逻辑桶映射关闭，桶名直接对应 MinIO 物理桶，使用 Prefix 进行项目/租户隔离。

```python
from refstore import RefStore

config = {
    "minio": {
        "endpoint": "localhost:9000",
        "access_key": "your_access_key",
        "secret_key": "your_secret_key",
        "secure": False,
    },
    "default_bucket": "my-project",
}

store = RefStore(config)
store.init_buckets()

# 上传文件，用 path 进行项目/租户隔离
uri = store.upload_file(
    file_data=b"Hello, RefStore!",
    original_filename="test.txt",
    content_type="text/plain",
    path="tenant-a/documents"
)
print(f"文件已上传: {uri}")  # s3://my-project/tenant-a/documents/test.txt

# 生成预签名 URL
url = store.get_presigned_url(uri, expiry_seconds=3600)
print(f"下载 URL: {url}")

# 下载文件
data = store.download_file(uri)
print(f"文件内容: {data.decode('utf-8')}")

# 获取文件信息
info = store.get_file_info(uri)
print(f"文件大小: {info['size_human']}")

# 列出文件
files = store.list_files(prefix="tenant-a/")
print(f"找到 {len(files)} 个文件")
```

### 开启逻辑桶名映射（高级用法）

如果你需要将多个逻辑桶映射到不同的物理桶，可以开启桶映射功能：

```python
from refstore import RefStore

config = {
    "minio": {
        "endpoint": "localhost:9000",
        "access_key": "your_access_key",
        "secret_key": "your_secret_key",
        "secure": False,
    },
    "enable_bucket_mapping": True,
    "bucket_map": {
        "user": "physical-user-bucket",
        "public": "physical-public-bucket",
    },
    "default_bucket": "user",
    "presigned_expiry": 3600,
}

store = RefStore(config)
store.init_buckets()

# 上传文件 - 默认返回物理桶 URI
uri = store.upload_file(
    file_data=b"Hello!",
    original_filename="test.txt",
    logic_bucket="user",
)
print(f"物理桶 URI: {uri}")  # s3://physical-user-bucket/2026/03/06/xxx.txt

# 上传文件 - 返回逻辑桶 URI
uri_logical = store.upload_file(
    file_data=b"Hello!",
    original_filename="test.txt",
    logic_bucket="user",
    use_logical_uri=True,
)
print(f"逻辑桶 URI: {uri_logical}")  # s3://user/2026/03/06/xxx.txt

# 下载时两种 URI 都支持
data = store.download_file(uri)           # 物理桶 URI 可以用
data = store.download_file(uri_logical)   # 逻辑桶 URI 也可以用
```

### 异步 API

```python
import asyncio
from refstore import AsyncRefStore

config = {
    "minio": {
        "endpoint": "localhost:9000",
        "access_key": "your_access_key",
        "secret_key": "your_secret_key",
        "secure": False,
    },
}

async def main():
    async with AsyncRefStore(config) as store:
        uri = await store.upload_file(
            file_data=b"Hello, Async RefStore!",
            original_filename="async_test.txt",
        )

        data = await store.download_file(uri)
        print(data.decode('utf-8'))

        # 并发上传多个文件
        tasks = [
            store.upload_file(b"File 1", "file1.txt")
            for _ in range(10)
        ]
        uris = await asyncio.gather(*tasks)

asyncio.run(main())
```

### Web API

启动 Web 服务：

```python
from refstore import web_app, init_web_service

config = {
    "minio": {
        "endpoint": "localhost:9000",
        "access_key": "your_access_key",
        "secret_key": "your_secret_key",
        "secure": False,
    },
}

init_web_service(config)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(web_app, host="0.0.0.0", port=8000)
```

或使用命令行：

```bash
uvicorn refstore.web:web_app --host 0.0.0.0 --port 8000 --reload
```

访问 API 文档：http://localhost:8000/docs

### 集中式文件网关（GatewayClient）

多项目共享同一个 RefStore 网关服务，各项目无需配置 MinIO 连接信息，只需知道网关地址。

**启动网关服务**（运维侧）：

```python
from refstore import web_app, init_web_service
import uvicorn

config = {
    "minio": {
        "endpoint": "10.31.31.41:9000",
        "access_key": "admin_key",
        "secret_key": "admin_secret",
        "secure": False,
    },
    "default_bucket": "shared-storage",
}

init_web_service(config)
uvicorn.run(web_app, host="0.0.0.0", port=8000)
```

**通过 SDK 连接网关**（各项目侧）：

```python
from refstore.gateway import GatewayClient

# 只需网关地址，无需 MinIO 连接信息
client = GatewayClient(gateway_url="http://gateway-host:8000")

# 查看网关状态
status = client.get_status()
print(f"连接状态: {status['status']}, 桶数量: {status['bucket_count']}")

# 查看配置（脱敏）
config = client.get_config()

# 桶管理
client.create_bucket("my-project-bucket")
buckets = client.list_buckets()
info = client.get_bucket_info("my-project-bucket")
client.delete_bucket("old-bucket", force=True)

# 文件操作
uri_result = client.upload_file(b"Hello Gateway!", filename="test.txt", logic_bucket="default")
uri = uri_result["uri"]

data = client.download_file(uri)
url_result = client.get_presigned_url(uri)

files = client.list_files()
client.delete_file(uri)
```

**异步网关客户端**：

```python
import asyncio
from refstore.gateway import AsyncGatewayClient

async def main():
    async with AsyncGatewayClient(gateway_url="http://gateway-host:8000") as client:
        status = await client.get_status()
        result = await client.upload_file(b"Hello!", filename="test.txt")
        data = await client.download_file(result["uri"])

asyncio.run(main())
```

## 配置

### 完整配置示例

```python
config = {
    # MinIO 连接配置（必需）
    "minio": {
        "endpoint": "localhost:9000",
        "access_key": "your_access_key",
        "secret_key": "your_secret_key",
        "secure": False,
    },

    # 逻辑桶映射开关（可选，默认 False）
    # 遵循 AWS S3 最佳实践：默认关闭，用 Prefix 隔离
    "enable_bucket_mapping": False,

    # 逻辑桶名到物理桶名的映射（仅在 enable_bucket_mapping=True 时生效）
    "bucket_map": {
        "user": "physical-user-bucket",
        "public": "physical-public-bucket",
        "temp": "physical-temp-bucket",
    },

    # 默认桶名（可选，默认为 "default"）
    "default_bucket": "default",

    # 预签名 URL 过期时间（可选，默认为 3600 秒）
    "presigned_expiry": 3600,

    # 公共基础 URL（可选，用于生成预签名URL时替换host部分）
    "public_url": "https://cdn.example.com",
}
```

### 配置验证

```python
from refstore import ConfigValidator

try:
    config = ConfigValidator.normalize_config(your_config)
    print("配置有效")
except ConfigError as e:
    print(f"配置无效: {e}")

try:
    ConfigValidator.test_connection(config)
    print("连接成功")
except ConnectionError as e:
    print(f"连接失败: {e}")
```

### 使用公共URL（反向代理场景）

当你通过nginx等反向代理访问MinIO时，可以使用 `public_url` 配置来生成使用公共域名的预签名URL：

```python
config = {
    "minio": {
        "endpoint": "10.31.31.41:9000",
        "access_key": "your_access_key",
        "secret_key": "your_secret_key",
        "secure": False,
    },
    "public_url": "https://shclzczy.odb.sh.cn/cdip-file-system/",
}

store = RefStore(config)

uri = store.upload_file(b"Hello", "test.txt")
url = store.get_presigned_url(uri)
# url: https://shclzczy.odb.sh.cn/cdip-file-system/default/.../test.txt?X-Amz-Algorithm=...
```

**重要说明**：
- `public_url` 只影响预签名URL的显示，MinIO客户端的实际连接仍然使用 `endpoint` 配置
- 预签名URL的签名是基于内部 `endpoint` 计算的
- 如果 `public_url` 包含路径前缀（如 `/cdip-file-system/`），会自动添加到生成的URL中
- **必须正确配置 nginx 的 Host header**，否则签名验证会失败

#### Nginx 配置示例（关键！）

```nginx
server {
    listen 443 ssl;
    server_name shclzczy.odb.sh.cn;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /cdip-file-system/ {
        proxy_pass http://10.31.31.41:9000/;
        
        # 关键：Host header 必须设置为 MinIO 的内部地址
        proxy_set_header Host 10.31.31.41:9000;
        
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 300;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        chunked_transfer_encoding off;
    }
}
```

## URI 操作

RefStore 使用标准化的 S3 URI 格式：`s3://bucket/path/to/file`

```python
from refstore import encode_uri, decode_uri, validate_uri, get_bucket_from_uri

# 编码 URI
uri = encode_uri("my-bucket", "documents/report.pdf")
# s3://my-bucket/documents/report.pdf

# 解码 URI
bucket, object_name = decode_uri(uri)
# bucket: my-bucket, object_name: documents/report.pdf

# 验证 URI
is_valid = validate_uri(uri)
# True

# 提取桶名
bucket = get_bucket_from_uri(uri)
# my-bucket

# 提取对象名称
object_name = get_object_name_from_uri(uri)
# documents/report.pdf

# 获取文件扩展名
ext = get_file_extension(uri)
# .pdf
```

## 高级功能

### 重试机制

```python
from refstore import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1.0)
def upload_with_retry(store, data, filename):
    return store.upload_file(data, filename)
```

### 桶管理

```python
from refstore import BucketManager

bucket_manager = BucketManager(minio_client)

bucket_manager.create_bucket("my-bucket")
exists = bucket_manager.bucket_exists("my-bucket")
buckets = bucket_manager.list_buckets()
info = bucket_manager.get_bucket_info("my-bucket")
bucket_manager.delete_bucket("my-bucket", force=True)
```

### 批量操作

```python
uris = [
    "s3://default/file1.txt",
    "s3://default/file2.txt",
    "s3://default/file3.txt",
]
result = store.delete_files(uris)
print(f"删除成功: {len(result['deleted'])}")
print(f"删除失败: {len(result['failed'])}")
```

### 网关桶映射热更新

通过网关 API 或 SDK 可以在运行时更新桶映射配置：

```python
from refstore.gateway import GatewayClient

client = GatewayClient(gateway_url="http://gateway-host:8000")

# 查看当前映射
mapping = client.get_bucket_mapping()
print(f"映射开启: {mapping['enable_bucket_mapping']}")
print(f"映射表: {mapping['bucket_map']}")

# 热更新映射
client.update_bucket_mapping(
    enable_bucket_mapping=True,
    bucket_map={
        "user": "prod-user-bucket",
        "logs": "prod-logs-bucket",
    }
)
```

## API 文档

### 同步 API

- `RefStore` - 同步文件服务类
  - `upload_file(file_data, original_filename, content_type, logic_bucket, path, use_logical_uri)` - 上传文件
  - `upload_from_local(local_path, logic_bucket, path, content_type, use_logical_uri)` - 从本地路径上传
  - `upload_from_url(url, logic_bucket, path, timeout, use_logical_uri)` - 从 URL 上传
  - `download_file(s3_uri)` - 下载文件到内存
  - `download_to_local(s3_uri, local_path)` - 下载文件到本地
  - `get_presigned_url(s3_uri, expiry_seconds, method)` - 生成预签名 URL
  - `get_file_info(s3_uri)` - 获取文件信息
  - `file_exists(s3_uri)` - 检查文件是否存在
  - `delete_file(s3_uri)` - 删除文件
  - `delete_files(s3_uris)` - 批量删除文件
  - `list_files(logic_bucket, prefix, recursive, use_logical_uri)` - 列出文件
  - `get_physical_bucket(logic_bucket)` - 逻辑桶名 -> 物理桶名
  - `get_logical_bucket(physical_bucket)` - 物理桶名 -> 逻辑桶名

### 异步 API

- `AsyncRefStore` - 异步文件服务类（方法签名与同步 API 相同）

### Web API 端点

**文件操作：**

- `POST /upload` - 上传文件
- `GET /download` - 下载文件
- `GET /presigned-url` - 生成预签名 URL
- `GET /info` - 获取文件信息
- `DELETE /delete` - 删除文件
- `GET /list` - 列出文件
- `GET /health` - 健康检查

**网关管理：**

- `GET /gateway/status` - MinIO 连接状态和服务信息
- `GET /gateway/config` - 查看当前配置（脱敏）
- `GET /gateway/buckets` - 列出所有桶
- `POST /gateway/buckets` - 创建桶
- `GET /gateway/buckets/{name}` - 获取桶详情
- `DELETE /gateway/buckets/{name}` - 删除桶
- `GET /gateway/bucket-mapping` - 查看桶映射配置
- `PUT /gateway/bucket-mapping` - 热更新桶映射配置

### Gateway SDK

- `GatewayClient` - 同步网关客户端
  - 管理：`get_status()`, `get_config()`, `list_buckets()`, `create_bucket()`, `get_bucket_info()`, `delete_bucket()`, `get_bucket_mapping()`, `update_bucket_mapping()`
  - 文件：`upload_file()`, `upload_from_local()`, `download_file()`, `download_to_local()`, `get_presigned_url()`, `get_file_info()`, `delete_file()`, `delete_files()`, `list_files()`
- `AsyncGatewayClient` - 异步网关客户端（方法签名同上，均为 async）

## 示例

查看 `examples/` 目录获取更多使用示例：

- `basic_usage.py` - 同步 API 基础用法
- `async_usage.py` - 异步 API 用法
- `web_service.py` - Web API 服务启动
- `web_client.py` - Web API 客户端使用
- `config_validation.py` - 配置验证示例

运行示例：

```bash
python examples/basic_usage.py
python examples/async_usage.py
python examples/web_service.py
python examples/config_validation.py
```

## 开发

### 运行测试

```bash
pip install -e ".[dev]"
pytest
pytest --cov=refstore --cov-report=html
```

### 代码格式化

```bash
black refstore tests examples
isort refstore tests examples
```

### 代码检查

```bash
flake8 refstore tests examples
mypy refstore
```

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与贡献。

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 问题反馈

如果你遇到问题或有建议，请在 [GitHub Issues](https://github.com/yourusername/refstore/issues) 中提出。

## 致谢

- [MinIO](https://min.io/) - 高性能的对象存储
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架
