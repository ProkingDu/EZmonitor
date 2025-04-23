import time
import os
import sys
import subprocess
def monitor_nginx_log(log_file):
    print(f"Monitoring Nginx log file: {log_file}")
    with open(log_file, 'r') as f:
        # 移动到文件末尾
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)  # 等待新数据
                continue
            try:
                parts = line.split()
                ip = parts[0]
                timestamp = parts[3][1:] + " " + parts[4][:-1]
                request = " ".join(parts[5:8]).strip('"')
                method, path, _ = request.split()
                protocol = "https" if "443" in line else "http"
                full_url = f"{protocol}://{ip}{path}"
                print(f"URL: {full_url}")
                print(f"Method: {method}")
                print(f"Time: {timestamp}")
                print("-" * 50)
            except IndexError:
                continue

# # 实时监控
# log_file = "/www/wwwlogs/demo.xiaodu0.com.log"
# monitor_nginx_log(log_file)

# 验证Nginx是否安装
def verify_nginx():
    py_version = sys.version_info[0]*10+sys.version_info[1]
    print(py_version)
    if(py_version <= 36):
        # 如果是3.6以下
        try:
            res = subprocess.run(['nginx','-v'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
            return True
        except Exception as e:
            print(e)
            return False
    elif py_version > 37:
        res = subprocess.run(['nginx','-v'],capture_output=True,text=True,check=True)
        print(res)
        return False

a="2025-04-09 11:27:56+08:00"
b="2025-04-09 11:28:26.848068+08:00"
print(a < b)