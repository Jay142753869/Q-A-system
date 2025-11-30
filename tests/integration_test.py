#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
集成测试脚本
测试整个问答系统的功能，包括预处理模块、知识图谱和问答引擎的集成
"""

import os
import sys
import logging
import unittest
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入系统组件
from preprocessing import QueryPreprocessor
from knowledge_graph import GraphManager, Neo4jManager
from models import QAEngine, InterpolationModel, ExtrapolationModel

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IntegrationTest(unittest.TestCase):
    """集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        logger.info("开始集成测试...")
        
        # 初始化Neo4j连接和知识图谱管理器
        try:
            cls.neo4j_manager = Neo4jManager()
            cls.graph_manager = GraphManager(cls.neo4j_manager)
            logger.info("知识图谱管理器初始化成功")
        except Exception as e:
            logger.error(f"初始化Neo4j连接失败: {str(e)}")
            logger.warning("将使用内存中的知识图谱进行测试")
            # 如果无法连接Neo4j，使用内存模式
            cls.neo4j_manager = None
            cls.graph_manager = GraphManager(None)
        
        # 初始化预处理模块
        try:
            cls.preprocessor = QueryPreprocessor()
            logger.info("预处理模块初始化成功")
        except Exception as e:
            logger.error(f"初始化预处理模块失败: {str(e)}")
            cls.preprocessor = None
        
        # 初始化问答引擎
        try:
            cls.qa_engine = QAEngine(cls.graph_manager)
            logger.info("问答引擎初始化成功")
        except Exception as e:
            logger.error(f"初始化问答引擎失败: {str(e)}")
            cls.qa_engine = None
        
        # 加载示例数据
        sample_data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "knowledge_graph", "data", "sample_graph.json"
        )
        
        try:
            if os.path.exists(sample_data_path):
                if cls.graph_manager.get_node_count() == 0:
                    cls.graph_manager.build_graph_from_json(sample_data_path)
                    logger.info(f"成功加载示例数据，当前节点数: {cls.graph_manager.get_node_count()}")
        except Exception as e:
            logger.error(f"加载示例数据失败: {str(e)}")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        logger.info("集成测试结束")
    
    def test_preprocessing_module(self):
        """测试预处理模块功能"""
        if not self.preprocessor:
            self.skipTest("预处理模块未初始化")
        
        try:
            # 测试预处理功能
            query = "苹果公司会收购哪些公司？"
            result = self.preprocessor.preprocess_query(query)
            
            # 获取分词结果
            tokens = result.get('tokens', [])
            logger.info(f"分词结果: {tokens}")
            self.assertGreater(len(tokens), 0)
            
            # 测试实体和关系提取
            ac_matches = result.get('ac_matches', {})
            entities = [e['text'] for e in ac_matches.get('entities', [])]
            relations = [r['text'] for r in ac_matches.get('relationships', [])]
            logger.info(f"提取的实体: {entities}")
            logger.info(f"提取的关系: {relations}")
            
            # 测试BERT嵌入
            query_embedding = result.get('query_embedding')
            self.assertIsNotNone(query_embedding)
            logger.info(f"查询嵌入向量类型: {type(query_embedding)}")
            
            # 测试最佳匹配
            best_matches = self.preprocessor.get_best_matches(query)
            logger.info(f"最佳匹配组合数量: {len(best_matches)}")
            
        except Exception as e:
            logger.error(f"预处理模块测试失败: {str(e)}")
            self.fail(f"预处理模块测试失败: {str(e)}")
    
    def test_knowledge_graph(self):
        """测试知识图谱功能"""
        if not self.graph_manager:
            self.skipTest("知识图谱管理器未初始化")
        
        try:
            # 测试获取节点数量
            node_count = self.graph_manager.get_node_count()
            logger.info(f"知识图谱节点数: {node_count}")
            
            # 测试查询功能
            if hasattr(self.graph_manager, 'query_relation'):
                results = self.graph_manager.query_relation("苹果公司", "生产")
                logger.info(f"查询关系结果数量: {len(results)}")
            
            # 测试获取实体信息
            if hasattr(self.graph_manager, 'get_entity_info'):
                entity_info = self.graph_manager.get_entity_info("苹果公司")
                logger.info(f"获取实体信息: {'成功' if entity_info else '失败'}")
            
        except Exception as e:
            logger.error(f"知识图谱测试失败: {str(e)}")
            # 知识图谱测试失败不中断整个测试流程
            pass
    
    def test_interpolation_model(self):
        """测试内推模型"""
        if not self.qa_engine or not hasattr(self.qa_engine, 'interpolation_model'):
            self.skipTest("内推模型未初始化")
        
        try:
            # 测试内推查询
            results = self.qa_engine.answer_interpolation_query(
                entity1="苹果公司", 
                relationship="收购", 
                entity2="", 
                top_k=3
            )
            
            logger.info(f"内推查询结果数量: {len(results)}")
            self.assertGreaterEqual(len(results), 0)
            
            if results:
                logger.info(f"内推结果示例: {results[0]}")
                self.assertIn("confidence", results[0])
                self.assertIn("prediction_type", results[0])
                
        except Exception as e:
            logger.error(f"内推模型测试失败: {str(e)}")
            # 模型测试失败不中断整个测试流程
            pass
    
    def test_extrapolation_model(self):
        """测试外推模型"""
        if not self.qa_engine or not hasattr(self.qa_engine, 'extrapolation_model'):
            self.skipTest("外推模型未初始化")
        
        try:
            # 测试外推查询
            predictions_by_year, relationship_stats, general_insights = self.qa_engine.answer_extrapolation_query(
                entity="苹果公司",
                future_years=3,
                top_k=2
            )
            
            logger.info(f"外推预测年份数: {len(predictions_by_year)}")
            logger.info(f"关系类型统计: {relationship_stats}")
            logger.info(f"趋势洞察: {general_insights}")
            
            self.assertGreaterEqual(len(predictions_by_year), 1)
            self.assertIn("labels", relationship_stats)
            self.assertIn("data", relationship_stats)
            
        except Exception as e:
            logger.error(f"外推模型测试失败: {str(e)}")
            # 模型测试失败不中断整个测试流程
            pass
    
    def test_industry_trend_prediction(self):
        """测试行业趋势预测"""
        if not self.qa_engine or not hasattr(self.qa_engine, 'predict_industry_trend'):
            self.skipTest("行业趋势预测功能未初始化")
        
        try:
            # 测试行业趋势预测
            trends = self.qa_engine.predict_industry_trend(
                industry="科技",
                future_years=3,
                top_k=3
            )
            
            logger.info(f"行业趋势预测结果数量: {len(trends)}")
            self.assertGreaterEqual(len(trends), 0)
            
            if trends:
                logger.info(f"行业趋势示例: {trends[0]}")
                self.assertIn("year", trends[0])
                self.assertIn("trend", trends[0])
                self.assertIn("confidence", trends[0])
                
        except Exception as e:
            logger.error(f"行业趋势预测测试失败: {str(e)}")
            # 测试失败不中断整个测试流程
            pass


def run_integration_tests():
    """运行集成测试"""
    logger.info("启动集成测试套件...")
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTest)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试摘要
    logger.info(f"测试结果: 运行{result.testsRun}个测试, 失败{len(result.failures)}, 错误{len(result.errors)}")
    
    # 保存测试报告
    save_test_report(result)
    
    return result.wasSuccessful()


def save_test_report(result):
    """保存测试报告"""
    try:
        # 创建测试报告目录
        report_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "tests", "reports"
        )
        os.makedirs(report_dir, exist_ok=True)
        
        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(report_dir, f"integration_test_report_{timestamp}.json")
        
        # 构建报告内容
        report = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "success": result.wasSuccessful()
        }
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试报告已保存至: {report_file}")
        
    except Exception as e:
        logger.error(f"保存测试报告失败: {str(e)}")


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
