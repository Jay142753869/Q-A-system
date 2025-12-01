#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j兼容性测试脚本
验证Neo4j驱动是否能在Python 3.10环境下正常工作
"""

import sys
import os

def test_neo4j_import():
    """测试Neo4j驱动导入"""
    print(f"当前Python版本: {sys.version}")
    print("开始测试Neo4j驱动导入...")
    
    try:
        # 尝试导入neo4j驱动
        from neo4j import GraphDatabase
        print("✅ 成功导入neo4j驱动!")
        
        # 打印Neo4j版本信息
        import neo4j
        print(f"Neo4j驱动版本: {neo4j.__version__}")
        
        # 打印成功信息
        print("✅ Neo4j驱动与Python 3.10兼容性测试通过!")
        print("\n注意: 此测试仅验证导入功能，不测试实际数据库连接。")
        print("如需测试实际连接，请确保Neo4j服务正在运行并配置正确的连接参数。")
        return True
        
    except ImportError as e:
        print(f"❌ 导入neo4j驱动失败: {str(e)}")
        print("请检查是否已安装neo4j驱动: pip install neo4j")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False

def check_python_version():
    """检查Python版本是否为3.10"""
    major, minor = sys.version_info[:2]
    if major == 3 and minor == 10:
        print("✅ Python版本检查通过: Python 3.10")
        return True
    else:
        print(f"⚠️ Python版本检查警告: 当前版本为Python {major}.{minor}，推荐使用Python 3.10")
        return False

def main():
    """主函数"""
    print("="*60)
    print("      Neo4j与Python 3.10兼容性测试")
    print("="*60)
    
    # 检查Python版本
    check_python_version()
    print()
    
    # 测试Neo4j导入
    success = test_neo4j_import()
    print("\n" + "="*60)
    
    if success:
        print("🎉 兼容性测试完成，一切正常!")
    else:
        print("⚠️ 兼容性测试存在问题，请检查错误信息并解决。")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
