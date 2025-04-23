import argparse
import sys
import subprocess
from functions import *


def main():
    parser = argparse.ArgumentParser(description="Nginx 适配初始化程序")
    parser.add_argument('--config', type=str, required=True, help="Path to the config file")
    args = parser.parse_args()

    # 读取 YAML 配置
    config = get_config(args.config)
    if not config:
        raise Exception("无法加载配置文件")

    nginx_setting = config['middleware']
    nginx_conf_path = nginx_setting['config']
    sites_dir = nginx_setting['sites_dir']
    expected_log_format = 'log_format custom \'$remote_addr|$remote_port|[$time_local]|$scheme://$http_host$request_uri|$status $body_bytes_sent|"$http_referer"|[UA]$http_user_agent[UA]|$server_addr|$server_port\''

    # 验证 Nginx 是否安装
    if not verify_nginx():
        raise Exception("Nginx 未安装")

    # 第一步：更新主配置文件
    print(f"检查 Nginx 配置文件: {nginx_conf_path}")
    inspect_nginx_conf(nginx_conf_path)
    backup_path = backup_nginx_config(nginx_conf_path)
    try:
        update_nginx_log_format(nginx_conf_path, expected_log_format)
        if sys.version_info[0] * 10 + sys.version_info[1] <= 36:
            result = subprocess.run(['nginx', '-t', '-c', nginx_conf_path], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, check=False)
            if result.returncode != 0:
                print(f"Nginx 配置验证失败: {result.stderr.decode('utf-8')}")
                restore_nginx_config(nginx_conf_path, backup_path)
                raise Exception("配置无效，已恢复备份")
        else:
            result = subprocess.run(['nginx', '-t', '-c', nginx_conf_path], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Nginx 配置验证失败: {result.stderr}")
                restore_nginx_config(nginx_conf_path, backup_path)
                raise Exception("配置无效，已恢复备份")
        print("Nginx 主配置文件验证通过")
    except Exception as e:
        print(f"发生错误: {e}")
        restore_nginx_config(nginx_conf_path, backup_path)
        raise

    # 第二步：处理站点配置文件
    print(f"\n处理站点配置文件目录: {sites_dir}")
    site_configs = get_site_configs(sites_dir)
    if not site_configs:
        print("未找到站点配置文件")
        return

    success_sites = []
    failed_sites = []

    for site_config in site_configs:
        site_name = os.path.basename(site_config).replace('.conf', '')
        print(f"\n处理站点: {site_name} ({site_config})")

        # 备份
        site_backup_path = backup_nginx_config(site_config)
        try:
            # 更新 access_log
            if update_site_access_log(site_config, site_name):
                # 验证配置
                if sys.version_info[0] * 10 + sys.version_info[1] <= 36:
                    result = subprocess.run(['nginx', '-t', '-c', nginx_conf_path], stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE, check=False)
                    if result.returncode != 0:
                        print(f"Nginx 配置验证失败: {result.stderr.decode('utf-8')}")
                        restore_nginx_config(site_config, site_backup_path)
                        failed_sites.append(site_name)
                        continue
                else:
                    result = subprocess.run(['nginx', '-t', '-c', nginx_conf_path], capture_output=True, text=True)
                    if result.returncode != 0:
                        print(f"Nginx 配置验证失败: {result.stderr}")
                        restore_nginx_config(site_config, site_backup_path)
                        failed_sites.append(site_name)
                        continue
                success_sites.append(site_name)
            else:
                failed_sites.append(site_name)
        except Exception as e:
            print(f"处理 {site_name} 时发生错误: {e}")
            restore_nginx_config(site_config, site_backup_path)
            failed_sites.append(site_name)

    # 打印结果
    print("\n=== 处理结果 ===")
    print(f"成功修改的站点 ({len(success_sites)}): {', '.join(success_sites) if success_sites else '无'}")
    print(f"失败的站点 ({len(failed_sites)}): {', '.join(failed_sites) if failed_sites else '无'}")


if __name__ == "__main__":
    main()