#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网络设备巡检工具
使用Netmiko库连接网络设备并执行巡检命令
"""

import json
import argparse
from netmiko import ConnectHandler
from netmiko import NetMikoTimeoutException, NetMikoAuthenticationException


class NetworkInspector:
    def __init__(self, devices_file='devices.json', commands_file=None):
        """
        初始化巡检工具
        
        Args:
            devices_file (str): 包含设备信息的JSON文件路径
            commands_file (str): 包含巡检命令的JSON文件路径（可选）
        """
        self.devices_file = devices_file
        self.commands_file = commands_file
        self.commands = self._load_commands() if commands_file else {}
        self.devices = self._load_devices()
    
    def _load_commands(self):
        """
        从JSON文件加载巡检命令

        Returns:
            dict: 巡检命令字典，以设备类型为键，命令列表为值
        """
        try:
            with open(self.commands_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"命令文件 {self.commands_file} 未找到，请检查文件路径。")
            return {}
        except json.JSONDecodeError:
            print(f"命令文件 {self.commands_file} 格式错误，请检查JSON格式。")
            return {}
    
    def _load_devices(self):
        """
        从JSON文件加载设备信息

        Returns:
            list: 设备信息列表
        """
        try:
            with open(self.devices_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 如果是混合JSON格式（包含devices和commands键）
                if isinstance(data, dict) and 'devices' in data:
                    # 加载设备信息
                    devices = data['devices']
                    
                    # 如果有commands键且未单独指定commands_file，则加载命令
                    if 'commands' in data and not self.commands_file:
                        self.commands = data['commands']
                        
                    return devices
                else:
                    # 传统格式，直接返回数据
                    return data
        except FileNotFoundError:
            print(f"设备文件 {self.devices_file} 未找到，请创建该文件。")
            return []
        except json.JSONDecodeError:
            print(f"设备文件 {self.devices_file} 格式错误，请检查JSON格式。")
            return []
    
    def inspect_device(self, device):
        """
        对单个设备执行巡检
        
        Args:
            device (dict): 设备信息字典
            
        Returns:
            dict: 巡检结果
        """
        result = {
            'hostname': device.get('host'),
            'ip_address': device.get('host'),  # 添加IP地址
            'device_type': device.get('device_type'),
            'status': 'failed',
            'output': '',
            'password_used': None  # 记录使用的密码
        }
        
        # 尝试使用主密码连接
        device_config = device.copy()
        passwords = [device.get('password')]
        
        # 如果配置了备用密码，也加入尝试列表
        if 'backup_password' in device and device['backup_password']:
            passwords.append(device['backup_password'])
        
        # 从设备配置中移除backup_password和commands，避免传递给Netmiko
        device_config.pop('backup_password', None)
        device_config.pop('commands', None)
        
        connection = None
        password_used = None  # 记录实际使用的密码
        
        for i, password in enumerate(passwords):
            try:
                # 更新设备配置中的密码
                device_config['password'] = password
                password_type = "主密码" if i == 0 else "备用密码"
                print(f"正在尝试使用{password_type}连接设备 {device.get('host')}...")
                
                # 建立连接
                connection = ConnectHandler(**device_config)
                password_used = password_type
                
                # 如果连接成功，跳出循环
                print(f"成功使用{password_type}连接到设备 {device.get('host')}")
                break
                
            except NetMikoAuthenticationException:
                print(f"使用{password_type}连接设备 {device.get('host')} 失败，尝试下一个密码...")
                continue
            except NetMikoTimeoutException:
                result['output'] = '连接超时'
                result['password_used'] = password_used
                return result
            except Exception as e:
                result['output'] = f'发生错误: {str(e)}'
                result['password_used'] = password_used
                return result
        
        # 如果所有密码都尝试失败
        if connection is None:
            result['output'] = '认证失败：所有密码尝试均失败'
            result['password_used'] = password_used
            return result
        
        try:
            # 获取设备提示符以确定主机名
            prompt = connection.find_prompt()
            hostname = prompt.rstrip('#>$ ')
            result['hostname'] = hostname
            result['password_used'] = password_used
            
            # 执行巡检命令（从设备配置或默认命令中获取）
            commands = self._get_inspection_commands(device)
            output = ''
            
            for cmd in commands:
                output += f'\n--- Command: {cmd} ---\n'
                # 使用send_command_timing作为更可靠的方法
                try:
                    cmd_output = connection.send_command_timing(
                        cmd,
                        read_timeout=30,       # 设置30秒超时
                        strip_prompt=False,    # 保留提示符
                        strip_command=True     # 移除命令本身
                    )
                    output += cmd_output or ''
                except Exception as e:
                    # 记录错误但继续执行下一个命令
                    output += f"命令 '{cmd}' 执行失败: {str(e)}\n"
                
            result['status'] = 'success'
            result['output'] = output
            
        except Exception as e:
            result['output'] = f'执行命令时发生错误: {str(e)}'
            result['password_used'] = password_used
        finally:
            # 关闭连接
            try:
                connection.disconnect()
            except:
                pass
                
        return result
    
    def _get_inspection_commands(self, device):
        """
        从设备配置中获取巡检命令，如果没有配置则使用默认命令
        
        Args:
            device (dict): 设备信息字典
            
        Returns:
            list: 命令列表
        """
        # 如果设备配置中包含commands字段，则使用配置的命令
        if 'commands' in device and device['commands']:
            return device['commands']
        
        # 如果有单独的命令文件或混合JSON中的命令配置
        device_type = device.get('device_type')
        if self.commands and device_type in self.commands:
            return self.commands[device_type]
        
        # 否则根据设备类型使用默认命令
        commands_map = {
            'cisco_ios': [
                'show version',
                'show ip interface brief',
                'show vlan brief',
                'show spanning-tree summary',
                'show arp',
                'show processes cpu',
                'show memory statistics'
            ],
            'cisco_xe': [
                'show version',
                'show ip interface brief',
                'show vlan brief',
                'show spanning-tree summary',
                'show arp',
                'show processes cpu',
                'show memory statistics'
            ],
            'cisco_nxos': [
                'show version',
                'show interface brief',
                'show vlan brief',
                'show spanning-tree detail',
                'show ip arp',
                'show processes cpu',
                'show processes memory'
            ],
            'huawei': [
                'display version',
                'display ip interface brief',
                'display vlan',
                'display stp brief',
                'display arp',
                'display cpu-usage',
                'display memory-usage'
            ],
            'h3c': [
                'display version',
                'display ip interface brief',
                'display vlan',
                'display stp brief',
                'display arp',
                'display cpu-usage',
                'display memory'
            ],
            'juniper': [
                'show version',
                'show interfaces terse',
                'show vlans',
                'show spanning-tree bridge',
                'show arp',
                'show chassis alarms',
                'show system processes summary'
            ]
        }
        
        return commands_map.get(device_type, ['show version'])
    
    def run_inspection(self):
        """
        对所有设备执行巡检
        
        Returns:
            list: 所有设备的巡检结果
        """
        results = []
        
        for device in self.devices:
            print(f"正在巡检设备: {device.get('host')}...")
            result = self.inspect_device(device)
            results.append(result)
            print(f"设备 {result['hostname']} 巡检完成，状态: {result['status']}")
            
        return results
    
    def save_results(self, results, output_file='inspection_results.txt'):
        """
        保存巡检结果到文件
        
        Args:
            results (list): 巡检结果列表
            output_file (str): 输出文件路径
        """
        import datetime
        
        # 获取当前时间作为时间戳
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入时间戳
            f.write(f"巡检时间: {timestamp}\n")
            f.write("=" * 50 + "\n\n")
            
            for result in results:
                f.write(f"设备: {result['hostname']} ({result['device_type']})\n")
                # 输出IP地址
                if result.get('ip_address'):
                    f.write(f"IP地址: {result['ip_address']}\n")
                f.write(f"状态: {result['status']}\n")
                # 输出使用的密码信息
                if result['password_used']:
                    f.write(f"登录密码: {result['password_used']}\n")
                elif result['status'] != 'success':
                    f.write(f"登录密码: 未成功登录\n")
                f.write(f"输出:\n{result['output']}\n")
                f.write("=" * 50 + "\n\n")
        
        print(f"巡检结果已保存到 {output_file}")


def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='网络设备巡检工具')
    parser.add_argument('config', nargs='?', 
                        help='配置文件路径（可以是设备配置文件、命令配置文件或混合配置文件）')
    parser.add_argument('-d', '--devices', 
                        help='设备配置文件路径')
    parser.add_argument('-c', '--commands', 
                        help='巡检命令配置文件路径')
    parser.add_argument('-m', '--mixed', 
                        help='混合配置文件路径（同时包含设备和命令信息）')
    parser.add_argument('-o', '--output', 
                        help='巡检报告输出文件路径')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 处理混合配置文件选项
    if args.mixed:
        # 如果指定了混合配置文件，则使用它作为设备文件，不使用单独的命令文件
        inspector = NetworkInspector(devices_file=args.mixed)
    elif args.devices:
        # 如果指定了设备配置文件，则使用它
        inspector = NetworkInspector(devices_file=args.devices, commands_file=args.commands)
    elif args.config:
        # 如果直接指定了配置文件，则尝试作为混合配置文件处理
        inspector = NetworkInspector(devices_file=args.config)
    else:
        # 使用默认设备配置文件
        inspector = NetworkInspector()
    
    if not inspector.devices:
        print("没有找到有效的设备配置，请检查设备配置文件。")
        return
    
    # 执行巡检
    results = inspector.run_inspection()
    
    # 保存结果（只保存TXT文本，不生成HTML报告）
    if args.output:
        inspector.save_results(results, args.output)
    else:
        inspector.save_results(results)


if __name__ == '__main__':
    main()
