import yaml
import os
from typing import Dict, List

class ConfigManager:
    """解析和管理配置文件"""

    def __init__(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self._validate_config()

    def _validate_config(self) -> None:
        required_sections = ['system', 'middleware', 'monitors', 'writers', 'observers']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required section: {section}")

        # 验证 system
        system_config = self.config['system']
        if 'filter_internal_ip' not in system_config or 'filter_superfluous_ip' not in system_config:
            raise ValueError("System must specify 'filter_internal_ip' and 'filter_superfluous_ip'")

        # 验证 middleware
        middleware_config = self.config['middleware']
        if 'type' not in middleware_config:
            raise ValueError("Middleware must specify 'type'")
        if middleware_config['type'] != 'nginx':
            raise ValueError("Only 'nginx' middleware is supported")
        if 'config' not in middleware_config or 'sites_dir' not in middleware_config or 'logs_dir' not in middleware_config:
            raise ValueError("Middleware must specify 'config', 'sites_dir', and 'logs_dir'")
        for key in ['config', 'sites_dir', 'logs_dir']:
            if not isinstance(middleware_config[key], str) or not middleware_config[key]:
                raise ValueError(f"Middleware '{key}' must be a non-empty string")

        # 验证 monitors
        if self.config['monitors'] is not None:
            for monitor in self.config['monitors']:
                if 'interface' not in monitor or 'interval' not in monitor:
                    raise ValueError("Each monitor must specify 'interface' and 'interval'")
                if not isinstance(monitor['interval'], int) or monitor['interval'] <= 0:
                    raise ValueError("Monitor 'interval' must be a positive integer")
                if 'ports' in monitor and not isinstance(monitor['ports'], list):
                    raise ValueError("Monitor 'ports' must be a list of integers")

        # 验证 writers
        writer_config = self.config['writers']
        if 'path' not in writer_config or 'format' not in writer_config or 'interval_type' not in writer_config:
            raise ValueError("Writers must specify 'path', 'format', and 'interval_type'")
        if writer_config['format'] not in ['csv', 'txt', 'log']:
            raise ValueError("Unsupported format, must be 'csv', 'txt', or 'log'")
        if writer_config['interval_type'] not in ['week', 'day', 'hour']:
            raise ValueError("Unsupported interval_type, must be 'week', 'day', or 'hour'")
        if 'fake_img' not in writer_config:
            raise ValueError("Writers must specify 'fake_img'")
        if not isinstance(writer_config['fake_img'], bool):
            raise ValueError("Writers 'fake_img' must be a boolean")

        # 验证 observers
        observer_config = self.config['observers']
        if 'enabled' not in observer_config or 'cleanup_days' not in observer_config:
            raise ValueError("Observers must specify 'enabled' and 'cleanup_days'")
        if not isinstance(observer_config['enabled'], bool):
            raise ValueError("Observers 'enabled' must be a boolean")
        if not isinstance(observer_config['cleanup_days'], int) or observer_config['cleanup_days'] <= 0:
            raise ValueError("Observers 'cleanup_days' must be a positive integer")

    def get_system_config(self) -> Dict:
        return self.config['system']

    def get_middleware_config(self) -> Dict:
        return self.config['middleware']

    def get_network_monitors_config(self) -> List[Dict]:
        return self.config['monitors']

    def get_writers_config(self) -> Dict:
        return self.config['writers']

    def get_observers_config(self) -> Dict:
        return self.config['observers']

    def get_config(self) -> Dict:
        return self.config