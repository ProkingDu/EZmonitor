# EZMonitor

## 项目概述

**EZMonitor** 是一个基于 Python 的网络流量监控工具，旨在捕获指定网卡的流量数据并记录到文件中，同时提供定时清理功能。该工具通过 YAML 配置文件灵活指定监控、记录和清理行为，适用于网络管理员或开发人员监控和分析网络流量。

### 主要功能
- **多网卡监控**：支持同时监控多个网络接口的流量。
- **端口过滤**：可选指定需要监控的端口，默认监控所有端口。
- **灵活记录**：支持将流量数据保存为 CSV、TXT 或 LOG 格式，并按周、天或小时分割文件。
- **定时清理**：提供观察器模块，可自动清理指定天数前的日志文件。
- **配置文件驱动**：通过 YAML 文件配置所有参数，易于修改和扩展。

### 项目目标
捕获网络流量并记录到文件中，字段包括：时间戳、源 IP、目的 IP、源端口、目的端口、源 MAC、目的 MAC。

---

## 安装

### 环境要求
- **操作系统**：Linux（推荐，需支持 Scapy 的原始数据包捕获），Windows（部分功能可能受限）
- **Python 版本**：3.6+
- **权限**：运行程序需要管理员权限（捕获网络数据包）

### 依赖安装
1. 安装 Python 依赖：
   ```bash
   pip install scapy pyyaml
   ```

2. 确保系统支持 Scapy 的原始数据包捕获：
   - Linux：需要 `libpcap`（通常默认安装）。
   - Windows：需要安装 Npcap（推荐）。

---

## 使用方法
### 初始化Nginx

項目依賴Nginx整合網站日誌，需要执行初始化命令来进行Nginx的依赖注入。
```bash
python3 nginx_initializaiton.py --config config.yaml
```

如果此程序不起作用，则可以手动编辑NGINX的配置文件，在http块中添加（或修改）:
```nginx
'log_format custom \'$remote_addr|$remote_port|[$time_local]|$scheme://$http_host$request_uri|$status $body_bytes_sent|"$http_referer"|[UA]$http_user_agent[UA]|$server_addr|$server_port\''
```

同时修改需要监控的站点的网站*access_log*为：
```bash
access_log 你的日志文件地址 custom
```

完成配置之后即可运行程序。

### 运行程序
1. 准备配置文件（例如 `config.yaml`），具体格式见下文。
2. 使用命令行启动程序并指定配置文件路径：
   ```bash
   python main.py --config config.yaml
   ```

3. 按 `Ctrl+C` 停止程序，程序会自动清理资源。

### 示例输出
日志文件会保存在指定路径下的子目录中，例如：
```
./2025-03/traffic_20250318.csv
```

---

## 配置文件说明

配置文件使用 YAML 格式，包含三个主要部分：`monitors`（监视器）、`writers`（记录器）和 `observers`（观察器）。

### 示例配置文件 (`config.yaml`)
```yaml
monitors:
  - interface: "eth0"
    interval: 5
    ports: [80, 443]
  - interface: "eth1"
    interval: 10
    ports: []

writers:
  path: "./"
  format: "csv"
  interval_type: "day"

observers:
  enabled: true
  cleanup_days: 30
```

### 配置项详解

#### 1. `monitors`
- **interface**（必填）：要监控的网卡名称（例如 `eth0`、`wlan0`）。
- **interval**（必填）：监控周期（秒），每次捕获数据的间隔。
- **ports**（可选）：要监控的端口列表（例如 `[80, 443]`），为空或不填表示监控所有端口。

#### 2. `writers`
- **path**（必填）：日志文件保存路径（例如 `./` 表示项目根目录）。
- **format**（必填）：文件格式，可选 `csv`、`txt` 或 `log`。
- **interval_type**（必填）：文件分割间隔，可选 `week`（按周）、`day`（按天）或 `hour`（按小时）。

#### 3. `observers`
- **enabled**（必填）：是否启用自动清理（`true` 或 `false`）。
- **cleanup_days**（必填）：清理多少天前的文件（整数，例如 `30`）。

---

## 项目结构

```
├── 2025-03/                   # 示例日志文件子目录
│   └── traffic_20250318.csv   # 示例日志文件
├── config_manager.py          # 配置解析模块
├── config.yaml                # 默认配置文件
├── documents/
│   └── requirement.md         # 需求文档
├── main.py                    # 主程序入口
├── monitors/                  # 监视器模块
│   ├── monitor_factory.py     # 监视器工厂
│   ├── network_monitor.py     # 网络监控核心类
│   ├── __pycache__/           # Python 缓存文件
│   └── unit_test.py           # 单元测试
├── observers/                 # 观察器模块
│   ├── observer.py            # 文件清理观察器
│   └── __init__.py
├── writers/                   # 记录器模块
│   ├── writer.py              # 流量数据记录器
│   └── __init__.py
```

### 文件说明
- **`config_manager.py`**：解析 YAML 配置文件并验证其有效性。
- **`main.py`**：程序入口，协调监视器、记录器和观察器的运行。
- **`monitors/`**：包含网络流量捕获的逻辑。
- **`writers/`**：负责将捕获的数据写入文件。
- **`observers/`**：实现定时清理过期日志文件。

---

## 功能性需求实现

1. **多网卡监控**：通过配置文件指定多个 `interface`，支持独立监控。
2. **自定义监控时间间隔**：通过 `interval` 参数设置。
3. **自定义监控网卡和端口**：通过 `interface` 和 `ports` 参数实现。
4. **选择记录文件类型**：支持 `csv`、`txt` 和 `log` 格式。
5. **定时清理模块**：通过 `observers` 配置启用并指定清理条件。
6. **不同网卡记录不同目录**：当前按月分目录，可扩展为按网卡分目录。

---

## 非功能性需求实现

1. **性能**：使用线程异步处理监控和清理，确保高流量下稳定运行。
2. **可扩展性**：模块化设计，支持添加新文件格式或清理条件。
3. **用户界面**：命令行界面，通过配置文件管理所有参数。
4. **安全性**：日志文件权限依赖操作系统，建议设置适当权限。
5. **可维护性**：代码模块化，注释清晰，便于维护。
6. **日志记录**：使用 Python 的 `logging` 模块记录关键操作和错误。

---

## 开发与调试

### 测试
运行 `monitors/unit_test.py` 进行单元测试：
```bash
python monitors/unit_test.py
```

### 注意事项
- 运行需要管理员权限（Linux 使用 `sudo`，Windows 以管理员身份运行）。
- 确保网卡名称正确，可通过 `scapy.get_if_list()` 查看可用接口。
- 高流量环境下可能需要调整 `interval` 参数以优化性能。

---

## 贡献指南

欢迎贡献代码或提出建议：
1. Fork 本仓库。
2. 创建新分支（例如 `feature/new-format`）。
3. 提交 Pull Request，描述你的更改。

### 待改进
- 支持按网卡分目录存储日志。
- 添加更多文件格式（如 JSON）。
- 优化高流量场景下的性能。

---

## 许可证

本项目采用 MIT 许可证，详情见 `LICENSE` 文件（待添加）。

