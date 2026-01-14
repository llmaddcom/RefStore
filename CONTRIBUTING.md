# 贡献指南

感谢你有兴趣为 RefStore 做出贡献！我们欢迎任何形式的贡献，包括但不限于：

- 报告 Bug
- 提出新功能建议
- 提交代码改进
- 改进文档
- 提供使用示例

## 开发环境设置

### 前置要求

- Python 3.8 或更高版本
- Git
- pip

### 克隆仓库

```bash
git clone https://github.com/yourusername/refstore.git
cd refstore
```

### 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

这会安装所有开发依赖，包括：
- 测试框架（pytest）
- 代码格式化工具（black, isort）
- 代码检查工具（flake8, mypy）
- 覆盖率工具（pytest-cov）

## 代码风格

我们遵循以下代码风格指南：

### PEP 8

RefStore 遵循 PEP 8 编码规范。我们使用工具自动检查和格式化代码。

### Black

使用 Black 进行代码格式化：

```bash
black refstore tests examples
```

配置文件：`pyproject.toml` 中的 `[tool.black]` 部分。

### isort

使用 isort 对导入进行排序：

```bash
isort refstore tests examples
```

配置文件：`pyproject.toml` 中的 `[tool.isort]` 部分。

### Flake8

使用 Flake8 进行代码检查：

```bash
flake8 refstore tests examples
```

### mypy

使用 mypy 进行类型检查：

```bash
mypy refstore
```

配置文件：`pyproject.toml` 中的 `[tool.mypy]` 部分。

## 提交代码前检查

在提交代码前，请确保：

1. 所有测试通过：`pytest`
2. 代码格式正确：`black refstore tests examples`
3. 导入已排序：`isort refstore tests examples`
4. 通过代码检查：`flake8 refstore tests examples`
5. 类型检查通过：`mypy refstore`

### Pre-commit Hooks

我们推荐使用 pre-commit 钩子自动在提交前执行这些检查：

```bash
pip install pre-commit
pre-commit install
```

现在每次提交代码时，pre-commit 会自动运行检查。

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_config.py

# 运行特定测试
pytest tests/test_config.py::TestConfigValidator::test_valid_config

# 显示详细输出
pytest -v

# 只运行失败的测试
pytest --lf
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=refstore --cov-report=html

# 在浏览器中查看覆盖率报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### 编写测试

我们使用 pytest 作为测试框架。测试文件位于 `tests/` 目录。

测试文件命名：`test_*.py`

测试类命名：`Test*`

测试函数命名：`test_*`

示例：

```python
import pytest
from refstore import RefStore


class TestRefStore:
    """RefStore 测试类"""

    def test_upload_file(self):
        """测试上传文件"""
        config = {...}
        store = RefStore(config)

        data = b"test content"
        uri = store.upload_file(data, "test.txt", logic_bucket="user")

        assert uri is not None
        assert uri.startswith("s3://")

    @pytest.mark.asyncio
    async def test_async_upload(self):
        """测试异步上传"""
        from refstore import AsyncRefStore

        config = {...}
        async with AsyncRefStore(config) as store:
            uri = await store.upload_file(b"test", "test.txt")
            assert uri is not None
```

### Mock 和 Fixture

使用 unittest.mock 进行测试时的模拟：

```python
from unittest.mock import Mock, patch

def test_with_mock():
    with patch('refstore.sync.file_service.Minio') as mock_minio:
        mock_client = Mock()
        mock_minio.return_value = mock_client

        store = RefStore(config)
        # ... 测试代码
```

使用 pytest fixtures：

```python
@pytest.fixture
def config():
    """测试配置 fixture"""
    return {
        "minio": {
            "endpoint": "localhost:9000",
            "access_key": "test",
            "secret_key": "test",
        },
    }

def test_with_fixture(config):
    """使用 fixture 的测试"""
    store = RefStore(config)
    # ... 测试代码
```

## 提交 Pull Request

### 分支策略

1. Fork 仓库
2. 从 `main` 分支创建功能分支：

```bash
git checkout -b feature/your-feature-name
```

3. 进行开发和测试
4. 提交更改
5. 推送到你的 fork
6. 创建 Pull Request

### Commit 消息格式

我们使用约定式提交（Conventional Commits）格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）：
- `feat`: 新功能
- `fix`: 修复 Bug
- `docs`: 文档更改
- `style`: 代码格式（不影响代码含义）
- `refactor`: 重构
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动

示例：

```
feat(file_service): add support for multipart upload

Implement multipart upload for files larger than 5MB.

Closes #123
```

```
fix(config): validate endpoint format correctly

Fix validation to reject endpoints without port numbers.

Fixes #456
```

### Pull Request 检查清单

在提交 PR 前，请确保：

- [ ] 代码通过所有测试
- [ ] 代码覆盖率没有显著降低
- [ ] 代码已通过 Black 格式化
- [ ] 导入已通过 isort 排序
- [ ] 代码通过 Flake8 检查
- [ ] 代码通过 mypy 类型检查
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] PR 描述清晰说明了更改内容

## 报告 Bug

在报告 Bug 时，请提供：

1. Bug 的详细描述
2. 重现步骤
3. 期望行为
4. 实际行为
5. 环境信息：
   - Python 版本
   - RefStore 版本
   - 操作系统
6. 错误堆栈跟踪（如果有）
7. 最小可重现示例（如果可能）

## 功能请求

在提出新功能时，请：

1. 清晰描述功能需求
2. 说明为什么需要这个功能
3. 描述期望的使用方式
4. 考虑是否会影响现有功能
5. 如果可能，提供伪代码或示例

## 文档

我们欢迎改进文档的贡献：

- 修正错误和拼写
- 添加使用示例
- 改进解释
- 翻译文档
- 添加图表和图片

## 代码审查

所有代码在合并前都需要经过代码审查。请：

- 保持开放的心态接受反馈
- 及时响应审查意见
- 解释你的设计决策
- 愿意根据反馈进行修改

## 行为准则

- 尊重所有贡献者
- 保持专业和友好的沟通
- 关注问题而不是个人
- 接受并尊重不同的观点
- 做出建设性的反馈

## 获取帮助

如果你在贡献过程中遇到问题：

- 查看现有的 Issue 和 Pull Request
- 在 Issue 中提问
- 加入社区讨论

## 许可证

通过贡献代码，你同意你的贡献将采用项目的 MIT 许可证。

感谢你的贡献！
