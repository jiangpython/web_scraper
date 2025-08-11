#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发爬虫配置管理
根据不同场景提供优化的并发参数
"""

from typing import Dict, Any
import psutil
import os


class ParallelConfig:
    """并发配置管理器"""
    
    # 预设配置方案
    PRESETS = {
        'conservative': {
            'name': '保守模式',
            'description': '稳定性优先适合网络不稳定环境',
            'max_workers': 2,
            'pool_size': 3,
            'batch_size': 30,
            'delay_config': {
                'success_delay': (2, 4),
                'error_delay': (5, 8),
                'retry_delay': (8, 12),
            },
            'max_retries': 3,
            'timeout': 60
        },
        
        'balanced': {
            'name': '平衡模式',
            'description': '性能与稳定性平衡推荐日常使用',
            'max_workers': 4,
            'pool_size': 6,
            'batch_size': 50,
            'delay_config': {
                'success_delay': (1, 3),
                'error_delay': (3, 6),
                'retry_delay': (5, 8),
            },
            'max_retries': 2,
            'timeout': 45
        },
        
        'aggressive': {
            'name': '激进模式',
            'description': '高性能优先适合稳定网络环境',
            'max_workers': 6,
            'pool_size': 10,
            'batch_size': 80,
            'delay_config': {
                'success_delay': (0.5, 2),
                'error_delay': (2, 4),
                'retry_delay': (3, 5),
            },
            'max_retries': 1,
            'timeout': 30
        },
        
        'extreme': {
            'name': '极限模式',
            'description': '最高性能仅适合本地测试或极优网络',
            'max_workers': 10,
            'pool_size': 15,
            'batch_size': 100,
            'delay_config': {
                'success_delay': (0.2, 1),
                'error_delay': (1, 3),
                'retry_delay': (2, 4),
            },
            'max_retries': 1,
            'timeout': 20
        }
    }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> Dict[str, Any]:
        """获取预设配置"""
        if preset_name not in cls.PRESETS:
            raise ValueError(f"未知预设: {preset_name}")
        
        return cls.PRESETS[preset_name].copy()
    
    @classmethod
    def get_auto_config(cls) -> Dict[str, Any]:
        """根据系统资源自动推荐配置"""
        # 获取系统信息
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        print(f" 检测系统资源:")
        print(f"   CPU核心数: {cpu_count}")
        print(f"   内存大小: {memory_gb:.1f}GB")
        
        # 根据资源推荐配置
        if cpu_count <= 2 or memory_gb < 4:
            preset = 'conservative'
            reason = "系统资源有限"
        elif cpu_count <= 4 or memory_gb < 8:
            preset = 'balanced'
            reason = "系统资源中等"
        elif cpu_count <= 8 or memory_gb < 16:
            preset = 'aggressive'
            reason = "系统资源良好"
        else:
            preset = 'extreme'
            reason = "系统资源充足"
        
        config = cls.get_preset(preset)
        config['auto_reason'] = reason
        
        print(f" 推荐配置: {config['name']} ({reason})")
        
        return config
    
    @classmethod
    def customize_config(cls, base_preset: str = 'balanced', **overrides) -> Dict[str, Any]:
        """基于预设自定义配置"""
        config = cls.get_preset(base_preset)
        
        # 应用覆盖参数
        for key, value in overrides.items():
            if key in config:
                config[key] = value
            else:
                print(f"  未知配置参数: {key}")
        
        return config
    
    @classmethod
    def print_all_presets(cls):
        """打印所有预设配置"""
        print(" 可用的并发配置预设:")
        print()
        
        for preset_name, config in cls.PRESETS.items():
            print(f" {preset_name.upper()}: {config['name']}")
            print(f"   描述: {config['description']}")
            print(f"   线程数: {config['max_workers']}")
            print(f"   驱动池: {config['pool_size']}")
            print(f"   批次大小: {config['batch_size']}")
            print(f"   预计性能: {cls._estimate_performance(config)}")
            print()
    
    @classmethod
    def _estimate_performance(cls, config: Dict) -> str:
        """估算配置性能"""
        workers = config['max_workers']
        avg_time_per_project = 8  # 秒
        
        projects_per_minute = (60 / avg_time_per_project) * workers
        hours_for_7000 = 7000 / (projects_per_minute * 60)
        
        return f"约{projects_per_minute:.0f}个/分钟7000个项目需{hours_for_7000:.1f}小时"
    
    @classmethod
    def validate_config(cls, config: Dict) -> Dict[str, Any]:
        """验证配置合理性"""
        issues = []
        warnings = []
        
        # 检查必需字段
        required_fields = ['max_workers', 'pool_size', 'batch_size']
        for field in required_fields:
            if field not in config:
                issues.append(f"缺少必需字段: {field}")
        
        if issues:
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        # 合理性检查
        if config['max_workers'] > config['pool_size']:
            warnings.append("线程数超过驱动池大小可能导致线程等待")
        
        if config['max_workers'] > psutil.cpu_count() * 2:
            warnings.append(f"线程数({config['max_workers']})超过CPU核心数({psutil.cpu_count()})的2倍")
        
        if config['batch_size'] < config['max_workers'] * 5:
            warnings.append("批次大小过小可能无法充分利用并发能力")
        
        # 资源检查
        estimated_memory = config['pool_size'] * 150  # 每个WebDriver约150MB
        available_memory = psutil.virtual_memory().available / (1024**2)
        
        if estimated_memory > available_memory * 0.8:
            issues.append(f"内存不足预计需要{estimated_memory:.0f}MB可用{available_memory:.0f}MB")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'estimated_memory_mb': estimated_memory,
            'available_memory_mb': available_memory
        }


def main():
    """测试配置管理器"""
    print(" 并发爬虫配置管理器测试\n")
    
    # 显示所有预设
    ParallelConfig.print_all_presets()
    
    # 自动推荐配置
    auto_config = ParallelConfig.get_auto_config()
    print(f"   推荐原因: {auto_config['auto_reason']}")
    
    # 验证配置
    validation = ParallelConfig.validate_config(auto_config)
    print(f"\n 配置验证:")
    print(f"   有效性: {' 通过' if validation['valid'] else ' 失败'}")
    
    if validation['issues']:
        print(f"   问题: {', '.join(validation['issues'])}")
    
    if validation['warnings']:
        print(f"   警告: {', '.join(validation['warnings'])}")
    
    print(f"   预计内存占用: {validation['estimated_memory_mb']:.0f}MB")
    
    # 自定义配置示例
    custom = ParallelConfig.customize_config(
        'balanced',
        max_workers=8,
        batch_size=60
    )
    print(f"\n  自定义配置示例:")
    print(f"   线程数: {custom['max_workers']}")
    print(f"   批次大小: {custom['batch_size']}")


if __name__ == "__main__":
    main()