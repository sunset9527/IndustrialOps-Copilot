# 第三方声明

## 依赖许可证

下表列出应用及开发工具的直接依赖。各依赖及传递依赖的版权与完整许可文本随对应发行包提供。

| 用途 | 依赖 | 许可证 |
| --- | --- | --- |
| Python 应用 | FastAPI、SQLAlchemy、PyMySQL、python-docx | MIT |
| Python 应用 | Uvicorn、pypdf | BSD-3-Clause |
| 密码散列 | Passlib | BSD |
| 密码散列 | bcrypt | Apache-2.0 |
| Python 构建与测试 | setuptools、pytest、PyYAML | MIT |
| Python HTTP 测试 | HTTPX | BSD-3-Clause |
| 前端及构建 | Vue、Vite、`@vitejs/plugin-vue` | MIT |

## 直接迁移的外部代码

v0.1 的选择性迁移来自同一作者维护的 HeritageMind，基线、参考范围和排除项见[迁移台账](docs/migration/heritagemind-v01-migration-inventory.json)。本版本未从外部工业项目直接迁入代码。

后续如直接引入外部代码，在此登记上游仓库、固定版本或提交、源文件与目标文件、许可证、修改和归属，并保留原许可证及版权声明。安装依赖与参考设计分别记录。
