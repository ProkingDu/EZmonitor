import os
import yaml

class Config:
    _instance = None

    def __new__(cls, config_path=None):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize(config_path)
        return cls._instance

    def _initialize(self, config_path):
        if config_path is None:
            config_path = 'config.yaml'
        
        if not os.path.exists(config_path):
            self._create_default_config(config_path)
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def _create_default_config(self, config_path):
        default_config = {
            'log_dir': '/path/to/log/directory',
            'ports': [80, 443],
            'interface': -1,  # -1 表示监控所有网卡
            'interval': 5  # 保存记录的时间间隔（秒）
        }
        with open(config_path, 'w') as f:
            yaml.safe_dump(default_config, f)
        print(f"创建默认配置文件: {config_path}")

    def __getitem__(self, key):
        return self.config.get(key)