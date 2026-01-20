# 规则编辑器

一个基于 Python + PyQt6 的规则文件编辑器，专门用于编辑特定 YAML 格式的规则文件。

## 关于本项目

本项目由 **GitHub Copilot (Claude Opus 4.5)** 根据用户需求生成。用户提供了功能需求和设计思路，AI 完成了代码实现。

## 功能特性

- ✅ **规则文件管理**：新建、打开、保存、导出 YAML 规则文件
- ✅ **现代化 UI**：简洁美观的界面设计，支持 Windows 深浅色主题自适应
- ✅ **高 DPI 支持**：完美适配高分辨率屏幕
- ✅ **规则编辑**：
  - 规则启用状态和严重程度采用点选方式编辑
  - 名称、编号、规则内容和提示模板采用编辑框编辑
  - 括号等成对符号自动补全
- ✅ **SpEL 代码提示**：规则表达式和消息模板支持类似 IDE 的代码补全
- ✅ **SpringBoot 项目扫描**：扫描 Java 项目获取类、字段、方法信息用于代码提示
- ✅ **配置文件系统**：支持多配置文件切换
- ✅ **自动备份**：定时自动备份，支持手动备份和恢复
- ✅ **版本管理**：支持修改规则文件的版本号
- ✅ **一键启动**：双击批处理文件即可启动，无需命令行

## 系统要求

- Windows 10/11
- Python 3.8 或更高版本（仅源码运行需要）

## 安装与运行

### 方式一：直接下载可执行文件（推荐）

1. 前往 [Releases](../../releases) 页面
2. 下载最新版本的 `RuleEditor_vX.X.exe`
3. 双击运行即可，无需安装 Python 环境

### 方式二：使用安装脚本运行源码

1. 确保已安装 Python 3.8+
2. 双击运行 `install.bat`
3. 等待安装完成
4. 双击 `start.bat` 启动应用

### 方式三：手动安装运行源码

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

## 使用说明

### 规则文件格式

规则文件采用 YAML 格式，示例：

```yaml
version: 1
rules:
  - code: RULE_001
    name: 身份证号为空
    enabled: true
    severity: HIGH
    expression: "baseInfo.idNumber == NULL"
    message: "身份证号为空"
```

### 规则字段说明

| 字段       | 说明                      | 必填 |
| ---------- | ------------------------- | ---- |
| code       | 规则编号，唯一标识        | 是   |
| name       | 规则名称，简短描述        | 是   |
| enabled    | 是否启用                  | 是   |
| severity   | 严重程度：LOW/MEDIUM/HIGH | 是   |
| expression | SpEL 表达式，规则条件     | 是   |
| message    | 提示消息模板              | 是   |

### SpEL 表达式

规则表达式使用 Spring Expression Language (SpEL) 语法。编辑器提供代码补全功能，支持：

- 对象属性访问：`baseInfo.idNumber`
- 方法调用：`#fn.genderFromIdNumber(baseInfo.idNumber)`
- 比较操作：`==`, `!=`, `>`, `<`, `>=`, `<=`
- 逻辑操作：`&&`, `||`, `!`, `and`, `or`, `not`
- 集合操作：`.size()`, `.isEmpty()`, `.?[]` 等

### SpringBoot 项目扫描

1. 点击菜单 "工具" → "SpringBoot项目扫描"
2. 选择 SpringBoot 项目目录
3. 设置函数类后缀（默认为 "Functions"）
4. 点击 "开始扫描"

扫描完成后，代码补全将包含扫描到的类、字段和方法信息。

### 配置文件管理

支持创建多个配置文件，每个配置文件可以保存不同的 SpringBoot 项目扫描结果。

点击菜单 "工具" → "配置文件管理" 进行管理。

### 自动备份

- 默认每 5 分钟自动备份一次
- 备份文件保存在 `config/backups` 目录
- 默认保留最近 10 个备份
- 可在设置中自定义备份间隔和数量

## 快捷键

| 快捷键       | 功能         |
| ------------ | ------------ |
| Ctrl+N       | 新建文件     |
| Ctrl+O       | 打开文件     |
| Ctrl+S       | 保存文件     |
| Ctrl+Shift+S | 另存为       |
| Ctrl+B       | 立即创建备份 |

## 项目结构

```
rule_editor_app/
├── config/                 # 配置文件目录
│   ├── app_config.json    # 应用配置
│   ├── profiles/          # 配置文件存储
│   └── backups/           # 备份文件
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── models.py          # 数据模型
│   ├── config_manager.py  # 配置管理
│   ├── theme_manager.py   # 主题管理
│   ├── spel_completer.py  # SpEL 代码补全
│   ├── springboot_scanner.py  # SpringBoot 扫描
│   ├── backup_manager.py  # 备份管理
│   ├── rule_editor.py     # 规则编辑器组件
│   ├── dialogs.py         # 对话框组件
│   └── main_window.py     # 主窗口
├── main.py                 # 程序入口
├── requirements.txt        # Python 依赖
├── start.bat               # 一键启动脚本
├── install.bat             # 依赖安装脚本
└── README.md              # 说明文档
```

## 依赖库

- PyQt6：GUI 框架
- PyYAML：YAML 文件处理
- darkdetect：系统主题检测
- javalang：Java 源码解析
- watchdog：文件系统监控

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
