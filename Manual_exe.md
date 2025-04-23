# 可执行文件的操作说明

可执行文件包含两个：
- main 用于启动主程序
- nginx_initializaiton 用于初始化nginx

二者都需要指定参数：
```bash
./main --config config.yaml
```
```bash
./nginx_initializaiton --config config.yaml
```
如果提示权限不足，则：
```bash
sudo chmod +x main
```

配置文件可以放在任意位置，默认的配置文件格式：
```yaml
system:
  filter_internal_ip: true  # 过滤内网IP
  filter_superfluous_ip: true  # 过滤多余IP


middleware:
  type: "nginx"  # 中间件类型，默认nginx
  config: "/www/server/nginx/conf/nginx.conf"  # 主配置文件路径
  sites_dir: "/www/server/panel/vhost/nginx"  # 站点配置文件目录
  logs_dir: "/www/wwwlogs"  # 日志目录

monitors:
  - interface: "eth0"  # 网卡
    interval: 1  # 监控间隔
    ports: [22, 2004]  # 监控端口
  - interface: "lo"
    interval: 5
    ports: []

writers:
  path: "./logs" # 记录文件目录
  format: "csv" # csv txt log
  interval_type: "hour" # hour day week
  fake_img : true

observers:
  enabled: true
  target_directory: "./"
  cleanup_days: 1
```

