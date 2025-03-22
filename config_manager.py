import yaml
import os
from typing import Dict, List, Set

class ConfigManager:
    """解析和管理配置文件"""
    
    def __init__(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self._validate_config()

    def _validate_config(self) -> None:
        required_sections = ['system', 'monitors', 'writers', 'observers']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required section: {section}")
        
        # 验证 system
        system_config = self.config['system']
        if 'filter_internal_ip' not in system_config or 'filter_superfluous_ip' not in system_config:
            raise ValueError("System must specify 'filter_internal_ip' and 'filter_superfluous_ip'")

        # 验证 monitors
        for monitor in self.config['monitors']:
            if 'interface' not in monitor or 'interval' not in monitor:
                raise ValueError("Each monitor must specify 'interface' and 'interval'")

        # 验证 writers
        writer_config = self.config['writers']
        if 'path' not in writer_config or 'format' not in writer_config or 'interval_type' not in writer_config:
            raise ValueError("Writers must specify 'path', 'format', and 'interval_type'")
        if writer_config['format'] not in ['csv', 'txt', 'log']:
            raise ValueError("Unsupported format, must be 'csv', 'txt', or 'log'")
        if writer_config['interval_type'] not in ['week', 'day', 'hour']:
            raise ValueError("Unsupported interval_type, must be 'week', 'day', or 'hour'")

        # 验证 observers
        observer_config = self.config['observers']
        if 'enabled' not in observer_config or 'cleanup_days' not in observer_config:
            raise ValueError("Observers must specify 'enabled' and 'cleanup_days'")

    def get_system_config(self) -> Dict:
        """获取系统配置"""
        return self.config['system']

    def get_monitors_config(self) -> List[Dict]:
        return self.config['monitors']

    def get_writers_config(self) -> Dict:
        return self.config['writers']

    def get_observers_config(self) -> Dict:
        return self.config['observers']