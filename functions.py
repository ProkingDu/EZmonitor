import os
import shutil
import subprocess
import yaml
import sys
import re

def get_config(filepath: str) -> dict:
    """读取 YAML 配置文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def verify_nginx():
    py_version = sys.version_info[0]*10+sys.version_info[1]
    if(py_version <= 36):
        try:
            subprocess.run(['nginx','-v'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
            return True
        except Exception as e:
            print(e)
            return False
    elif py_version > 37:
        try:
            subprocess.run(['nginx','-v'],capture_output=True,text=True,check=True)
            return True
        except Exception as e:
            print(e)
            return False

def backup_nginx_config(filepath: str) -> str:
    """备份 Nginx 配置文件"""
    backup_path = filepath + '.bak'
    shutil.copy2(filepath, backup_path)
    print(f"已创建备份: {backup_path}")
    return backup_path

def restore_nginx_config(original_path: str, backup_path: str) -> None:
    """从备份恢复 Nginx 配置文件"""
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, original_path)
        print(f"已从 {backup_path} 恢复到 {original_path}")
    else:
        raise FileNotFoundError(f"备份文件 {backup_path} 不存在")

def update_nginx_log_format(filepath: str, expected_format: str) -> bool:
    """检查并更新 http 块中的 log_format，支持 http 和 { 不在同一行"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Nginx 配置文件 {filepath} 不存在")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    http_start = -1
    http_end = -1
    log_format_line = -1
    brace_count = 0

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if 'http' in line_stripped and http_start == -1:
            http_start = i
            for j in range(i, len(lines)):
                if '{' in lines[j].strip():
                    http_start = j + 1
                    brace_count = 1
                    break
            break

    if http_start != -1:
        for i in range(http_start, len(lines)):
            line_stripped = lines[i].strip()
            if '{' in line_stripped:
                brace_count += 1
            if '}' in line_stripped:
                brace_count -= 1
                if brace_count == 0:
                    http_end = i
                    break
            if 'log_format' in line_stripped:
                log_format_line = i

    modified = False
    if http_start == -1:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(f"\nhttp {{\n    {expected_format};\n}}\n")
        print("未找到 http 块，已添加")
        modified = True
    else:
        if log_format_line != -1:
            current_format = lines[log_format_line].strip().rstrip(';')
            if current_format != expected_format:
                print(f"替换 log_format: {current_format} -> {expected_format}")
                lines[log_format_line] = f"    {expected_format};\n"
                modified = True
            else:
                print(f"log_format 已符合预期: {current_format}")
        else:
            lines.insert(http_start, f"    {expected_format};\n")
            print("http 块中未找到 log_format，已添加")
            modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"已更新配置文件: {filepath}")
    return True

def inspect_nginx_conf(path: str) -> None:
    """简单打印配置文件内容"""
    with open(path, 'r', encoding='utf-8') as f:
        print(f.read())

def get_site_configs(sites_dir: str) -> list:
    """获取站点配置文件列表，过滤目录和非站点文件"""
    site_configs = []
    site_pattern = re.compile(r'^[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\.conf$')

    for filename in os.listdir(sites_dir):
        filepath = os.path.join(sites_dir, filename)
        if os.path.isdir(filepath):
            continue
        if not site_pattern.match(filename):
            continue
        site_configs.append(filepath)
    return site_configs

def update_site_access_log(filepath: str, site_name: str) -> bool:
    """检查并更新站点的 server 块中的 access_log 配置"""
    expected_log_path = f"/www/wwwlogs/{site_name}.log"
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 定位 server 块（直属）
    server_start = -1
    server_end = -1
    access_log_line = -1
    brace_count = 0

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if 'server' in line_stripped and server_start == -1:
            server_start = i
            for j in range(i, len(lines)):
                if '{' in lines[j].strip():
                    server_start = j + 1
                    brace_count = 1
                    break
            break

    if server_start != -1:
        for i in range(server_start, len(lines)):
            line_stripped = lines[i].strip()
            # 只检查直属 server 块，遇到嵌套块（如 location）停止
            if brace_count == 1 and '{' in line_stripped and any(kw in line_stripped for kw in ['location']):
                continue
            if '{' in line_stripped:
                brace_count += 1
            if '}' in line_stripped:
                brace_count -= 1
                if brace_count == 0:
                    server_end = i
                    continue
            if 'access_log' in line_stripped:
                access_log_line = i

    # 检查 access_log
    if server_start == -1:
        print(f"{filepath}: 未找到 server 块，跳过")
        return False

    if access_log_line == -1:
        print(f"{filepath}: server 块中未找到 access_log，跳过")
        return False

    # 检查 access_log 的日志路径
    current_access_log = lines[access_log_line].strip()
    if expected_log_path not in current_access_log:
        print(f"{filepath}: access_log 日志路径不匹配，预期 {expected_log_path}，实际 {current_access_log}")
        return False

    # 检查是否已指定 custom 格式
    if 'custom' in current_access_log:
        print(f"{filepath}: access_log 已使用 custom 格式，跳过")
        return True

    # 修改 access_log 添加 custom 格式
    new_access_log = current_access_log.rstrip(';\n') + ' custom;\n'
    lines[access_log_line] = new_access_log
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"{filepath}: 已更新 access_log 为 {new_access_log.strip()}")
    return True