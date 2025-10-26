# 网络设备巡检工具使用说明

## 项目结构
```
network_inspector/
├── network_inspector.py    # 巡检工具主程序
├── devices.json           # 设备配置文件示例
├── commands.json          # 命令配置文件示例
├── mixed_config.json      # 混合配置文件示例
├── requirements.txt       # 依赖库列表
├── devices_example.json   # 设备配置文件示例
├── commands_example.json  # 命令配置文件示例
├── mixed_example.json     # 混合配置文件示例
└── README.md             # 使用说明文件
```

## 安装依赖
```bash
pip install -r requirements.txt
```

## 配置文件格式说明

### 1. 设备配置文件格式
设备配置文件包含网络设备的连接信息和巡检命令：

```json
[
    {
        "device_type": "cisco_ios",
        "host": "192.168.1.1",
        "username": "admin",
        "password": "main_password",
        "backup_password": "backup_password",
        "secret": "enable_password",
        "commands": [
            "show version",
            "show ip interface brief"
        ]
    }
]
```

字段说明：
- `device_type`: 设备类型（必需）
- `host`: 设备IP地址（必需）
- `username`: 登录用户名（必需）
- `password`: 主密码（必需）
- `backup_password`: 备用密码（可选）
- `secret`: 特权模式密码（可选，仅Cisco设备需要）
- `commands`: 设备特定的巡检命令（可选）

### 2. 命令配置文件格式
命令配置文件按设备类型定义巡检命令：

```json
{
    "cisco_ios": [
        "show version",
        "show ip interface brief"
    ],
    "huawei": [
        "display version",
        "display ip interface brief"
    ]
}
```

### 3. 混合配置文件格式
混合配置文件同时包含设备信息和命令配置：

```json
{
    "devices": [
        {
            "device_type": "cisco_ios",
            "host": "192.168.1.1",
            "username": "admin",
            "password": "main_password",
            "backup_password": "backup_password"
        }
    ],
    "commands": {
        "cisco_ios": [
            "show version",
            "show ip interface brief"
        ]
    }
}
```

## 命令行选项说明

```bash
python network_inspector.py [选项]
```

选项：
- `-h, --help`: 显示帮助信息
- `-d, --devices DEVICES`: 设备配置文件路径（默认：devices.json）
- `-c, --commands COMMANDS`: 巡检命令配置文件路径（可选）
- `-m, --mixed MIXED`: 混合配置文件路径（同时包含设备和命令信息）

使用示例：
```bash
# 使用默认设备配置文件
python network_inspector.py

# 指定设备配置文件
python network_inspector.py -d devices_example.json

# 指定设备和命令配置文件
python network_inspector.py -d devices_example.json -c commands_example.json

# 指定混合配置文件
python network_inspector.py -m mixed_example.json
```

## 输出文件格式说明

工具执行完成后，会生成一个名为 `inspection_results.txt` 的文本文件，格式如下：

```
巡检时间: 2023-10-26 14:30:00
==================================================

设备: Router1 (cisco_ios)
状态: success
登录密码: 主密码
输出:
--- Command: show version ---
Cisco IOS Software, C2960 Software (C2960-LANBASEK9-M), Version 12.2(55)SE12

--- Command: show ip interface brief ---
Interface              IP-Address      OK? Method Status                Protocol
Vlan1                  192.168.1.1     YES manual up                    up

==================================================
```

字段说明：
- `巡检时间`: 巡检执行的时间戳
- `设备`: 设备主机名和类型
- `状态`: 巡检结果状态（success/failed）
- `登录密码`: 实际使用的密码类型（主密码/备用密码/未成功登录）
- `输出`: 设备命令执行结果

## 支持的设备类型
- cisco_ios: Cisco IOS 设备
- cisco_xe: Cisco XE 设备
- cisco_nxos: Cisco NX-OS 设备
- huawei: 华为设备
- h3c: H3C 设备
- juniper: Juniper 设备