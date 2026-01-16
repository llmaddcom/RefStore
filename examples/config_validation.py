"""
RefStore 配置验证示例

演示如何验证和测试配置
"""

from refstore import ConfigValidator
from refstore.core.exceptions import ConfigError, ConnectionError


def test_valid_config():
    """测试有效配置"""
    print("\n=== 测试有效配置 ===")

    config = {
        "minio": {
            "endpoint": "localhost:9000",
            "access_key": "your_access_key",
            "secret_key": "your_secret_key",
            "secure": False,
        },
        "bucket_map": {
            "user": "physical-user-bucket",
            "public": "physical-public-bucket",
        },
    }

    try:
        validated = ConfigValidator.validate_config(config)
        print(f"[OK] 配置验证通过")
        print(f"  - Endpoint: {validated['minio']['endpoint']}")
        print(f"  - Default bucket: {validated['default_bucket']}")
        print(f"  - Presigned expiry: {validated['presigned_expiry']}")
    except ConfigError as e:
        print(f"[ERROR] 配置验证失败: {e}")


def test_invalid_config():
    """测试无效配置"""
    print("\n=== 测试无效配置 ===")

    # 缺少必需字段
    invalid_configs = [
        {
            "minio": {
                # 缺少 endpoint
                "access_key": "test",
                "secret_key": "test",
            }
        },
        {
            "minio": {
                "endpoint": "localhost",  # 无效的 endpoint 格式
                "access_key": "test",
                "secret_key": "test",
            }
        },
        {
            "minio": {
                "endpoint": "localhost:9000",
                "access_key": "test",
                "secret_key": "test",
            },
            "presigned_expiry": -1,  # 无效的过期时间
        }
    ]

    for i, config in enumerate(invalid_configs, 1):
        print(f"\n配置 {i}:")
        try:
            ConfigValidator.validate_config(config)
            print(f"  [意外] 配置验证通过（应该失败）")
        except ConfigError as e:
            print(f"  [预期] 验证失败: {e}")


def test_connection():
    """测试连接"""
    print("\n=== 测试 MinIO 连接 ===")

    config = {
        "minio": {
            "endpoint": "localhost:9000",
            "access_key": "test_key",
            "secret_key": "test_secret",
            "secure": False,
        },
    }

    try:
        success = ConfigValidator.test_connection(config)
        if success:
            print(f"[OK] 连接成功")
        else:
            print(f"[ERROR] 连接失败")
    except ConnectionError as e:
        print(f"[ERROR] 连接失败: {e}")


def test_get_schema():
    """获取配置 Schema"""
    print("\n=== 获取配置 Schema ===")

    schema = ConfigValidator.get_config_schema()
    print(f"Schema 类型: {schema['type']}")
    print(f"必需字段: {schema['required']}")

    minio_props = schema['properties']['minio']['properties']
    print(f"MinIO 配置项:")
    for key, value in minio_props.items():
        print(f"  - {key}: {value.get('type', 'unknown')}")


def test_normalize_config():
    """测试配置规范化"""
    print("\n=== 测试配置规范化 ===")

    # 最小配置
    minimal_config = {
        "minio": {
            "endpoint": "localhost:9000",
            "access_key": "test",
            "secret_key": "test",
        }
    }

    normalized = ConfigValidator.normalize_config(minimal_config)
    print(f"最小配置规范化后:")
    print(f"  - Default bucket: {normalized['default_bucket']}")
    print(f"  - Presigned expiry: {normalized['presigned_expiry']}")
    print(f"  - Bucket map: {normalized['bucket_map']}")


def main():
    """主函数"""
    print("RefStore 配置验证示例")
    print("=" * 50)

    # 测试有效配置
    test_valid_config()

    # 测试无效配置
    test_invalid_config()

    # 测试连接
    test_connection()

    # 获取 Schema
    test_get_schema()

    # 测试配置规范化
    test_normalize_config()

    print("\n" + "=" * 50)
    print("示例完成")


if __name__ == "__main__":
    main()
