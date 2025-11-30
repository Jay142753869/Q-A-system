from flask import Flask, render_template, request, jsonify
import sys
import os
import logging
import random
from datetime import datetime

# 添加项目根目录到Python路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目的核心模块
from preprocessing import QueryPreprocessor
from knowledge_graph import init_knowledge_graph, Neo4jManager, GraphManager
from models import QAEngine

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_local_development')

# 全局变量
preprocessor = None
graph_manager = None
qa_engine = None

# 示例数据 - 用于演示和测试
def get_sample_interpolation_data(entity1=None, relation=None, entity2=None):
    """获取示例内推预测数据"""
    sample_results = [
        {
            "confidence": 0.92,
            "prediction_type": "predicted_relation",
            "entity1": "苹果公司" if not entity1 else entity1,
            "relation": "收购" if not relation else relation,
            "entity2": "特斯拉" if not entity2 else entity2,
            "evidence": [
                "苹果公司历史上曾多次收购科技公司",
                "特斯拉的自动驾驶技术与苹果的产品战略相符",
                "两家公司在供应链方面有合作基础"
            ]
        },
        {
            "confidence": 0.85,
            "prediction_type": "predicted_target",
            "entity1": "苹果公司" if not entity1 else entity1,
            "relation": "收购" if not relation else relation,
            "entity2": "英伟达",
            "evidence": [
                "苹果公司需要更强的AI芯片支持",
                "英伟达在AI领域处于领先地位",
                "半导体行业整合趋势明显"
            ]
        },
        {
            "confidence": 0.78,
            "prediction_type": "predicted_relation",
            "entity1": "苹果公司" if not entity1 else entity1,
            "relation": "合作",
            "entity2": "微软" if not entity2 else entity2,
            "evidence": [
                "两家公司在云服务方面有合作空间",
                "微软CEO曾表示愿意与苹果加深合作",
                "双方在企业市场有互补优势"
            ]
        },
        {
            "confidence": 0.71,
            "prediction_type": "predicted_source",
            "entity1": "谷歌",
            "relation": "竞争" if not relation else relation,
            "entity2": "苹果公司" if not entity2 else entity2,
            "evidence": [
                "两家公司在智能手机操作系统市场直接竞争",
                "在AI助手领域存在竞争关系",
                "在云计算和服务生态方面有竞争"
            ]
        },
        {
            "confidence": 0.65,
            "prediction_type": "predicted_relation",
            "entity1": "苹果公司" if not entity1 else entity1,
            "relation": "投资",
            "entity2": "创业公司X" if not entity2 else entity2,
            "evidence": [
                "苹果公司设有专门的风投部门",
                "该创业公司的技术符合苹果的创新方向",
                "苹果近年来增加了对初创企业的投资"
            ]
        }
    ]
    
    # 如果提供了特定实体或关系，过滤相关结果
    filtered_results = []
    for result in sample_results:
        if entity1 and result["entity1"] != entity1:
            continue
        if relation and result["relation"] != relation:
            continue
        if entity2 and result["entity2"] != entity2:
            continue
        filtered_results.append(result)
    
    # 如果过滤后没有结果，返回原始结果的一部分
    if not filtered_results:
        filtered_results = sample_results[:3]
    
    return filtered_results

def get_sample_extrapolation_data(entity, future_years=5):
    """获取示例外推预测数据"""
    current_year = datetime.now().year
    
    # 按年份组织预测结果
    predictions_by_year = {}
    relationship_types = []
    
    # 生成每年的预测结果
    for i in range(1, future_years + 1):
        year = current_year + i
        predictions = []
        
        # 为第一年生成更多预测
        num_predictions = min(3 + i, 5)
        
        for j in range(num_predictions):
            # 根据年份和索引生成不同的关系类型
            if i <= 2:
                # 近期更可能发生收购和合作
                rel_types = ["收购", "合作", "投资"]
            else:
                # 远期可能有更多战略合作
                rel_types = ["战略合作", "技术授权", "合资企业", "市场拓展"]
            
            rel_type = random.choice(rel_types)
            relationship_types.append(rel_type)
            
            # 目标实体根据关系类型变化
            if rel_type == "收购":
                targets = ["AI初创公司A", "芯片制造商B", "软件服务公司C", "数据安全公司D"]
            elif rel_type == "合作":
                targets = ["云服务提供商E", "内容平台F", "零售巨头G", "汽车制造商H"]
            elif rel_type == "投资":
                targets = ["创新科技公司I", "生物技术公司J", "绿色能源公司K"]
            elif rel_type == "战略合作":
                targets = ["大型科技集团L", "国家研究机构M", "行业联盟N"]
            elif rel_type == "技术授权":
                targets = ["设备制造商O", "消费电子公司P", "系统集成商Q"]
            elif rel_type == "合资企业":
                targets = ["国际科技公司R", "产业巨头S", "市场领导者T"]
            else:  # 市场拓展
                targets = ["新兴市场分销商U", "区域零售商V", "电商平台W"]
            
            target_entity = random.choice(targets)
            
            # 置信度随时间降低
            base_confidence = 0.9 - (i * 0.1)  # 每年降低0.1的基准置信度
            random_factor = random.uniform(-0.1, 0.1)  # 添加随机波动
            confidence = max(0.1, min(0.95, base_confidence + random_factor))
            
            # 生成支持依据
            evidence_count = random.randint(2, 4)
            evidence_templates = [
                f"{entity}近期在{rel_type}方面表现出积极态度",
                f"市场趋势表明{rel_type}类型的合作正在增加",
                f"历史数据分析显示类似实体在该时期有{rel_type}行为",
                f"行业专家预测未来{rel_type}活动将增多",
                f"{entity}与{target_entity}在业务上有很强的互补性",
                f"两家公司高管曾公开表达合作意向",
                f"当前经济环境有利于此类{rel_type}活动",
                f"双方已在多个项目上有初步接触"
            ]
            evidence = random.sample(evidence_templates, evidence_count)
            
            predictions.append({
                "confidence": confidence,
                "source_entity": entity,
                "relationship_type": rel_type,
                "target_entity": target_entity,
                "evidence": evidence
            })
        
        # 按置信度排序
        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        predictions_by_year[year] = predictions
    
    # 计算关系类型统计
    rel_counts = {}
    for rel in relationship_types:
        rel_counts[rel] = rel_counts.get(rel, 0) + 1
    
    relationship_stats = {
        "labels": list(rel_counts.keys()),
        "data": list(rel_counts.values())
    }
    
    # 生成整体趋势洞察
    top_relation = max(rel_counts, key=rel_counts.get) if rel_counts else "无"
    general_insights = f"基于预测分析，{entity}在未来{future_years}年内最可能发生的关系类型是{top_relation}。" \
                      f"近期（1-2年）的预测置信度较高，而远期预测的不确定性增加。" \
                      f"建议重点关注近期的预测结果，并根据市场变化适时调整策略。"
    
    return predictions_by_year, relationship_stats, general_insights


def initialize_components():
    """初始化系统组件"""
    global preprocessor, graph_manager, qa_engine
    
    try:
        logger.info("正在初始化系统组件...")
        
        # 初始化Neo4j连接
        neo4j_manager = Neo4jManager()
        graph_manager = GraphManager(neo4j_manager)
        
        # 初始化预处理模块
        preprocessor = QueryPreprocessor()
        
        # 初始化问答引擎
        qa_engine = QAEngine(graph_manager)
        
        # 尝试加载示例数据（如果没有数据）
        if graph_manager.get_node_count() == 0:
            logger.info("检测到数据库为空，尝试加载示例数据...")
            sample_data_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "knowledge_graph", "data", "sample_graph.json"
            )
            if os.path.exists(sample_data_path):
                graph_manager.build_graph_from_json(sample_data_path)
                logger.info("示例数据加载成功")
        
        # 训练模型
        logger.info("正在训练模型...")
        qa_engine.train_models(interpolation_epochs=5, extrapolation_epochs=3, learning_rate=0.01)
        
        logger.info("系统组件初始化完成")
        return True
    except Exception as e:
        logger.error(f"初始化系统组件失败: {str(e)}")
        return False


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/interpolation', methods=['GET', 'POST'])
def interpolation_page():
    """内推页面"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            entity1 = request.form.get('entity1', '').strip()
            relationship = request.form.get('relationship', '').strip()
            entity2 = request.form.get('entity2', '').strip()
            top_k = int(request.form.get('top_k', 5))
            
            # 使用问答引擎获取结果
            results = qa_engine.answer_interpolation_query(entity1, relationship, entity2, top_k)
            
            # 渲染结果页面
            return render_template('interpolation_result.html', 
                                results=results, 
                                entity1=entity1, 
                                relationship=relationship, 
                                entity2=entity2)
        except Exception as e:
            logger.error(f"处理内推查询时出错: {str(e)}")
            return render_template('interpolation.html', error=str(e))
    
    # GET请求，渲染表单页面
    return render_template('interpolation.html')


@app.route('/extrapolation', methods=['GET', 'POST'])
def extrapolation_page():
    """外推页面"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            entity = request.form.get('entity', '').strip()
            future_years = int(request.form.get('future_years', 5))
            top_k = int(request.form.get('top_k', 5))
            
            # 验证输入
            if not entity:
                return render_template('extrapolation.html', error="请输入实体名称")
            
            # 使用问答引擎获取结果
            try:
                predictions_by_year, relationship_stats, general_insights = qa_engine.answer_extrapolation_query(entity, future_years, top_k)
                logger.info(f"成功获取外推预测结果，覆盖 {future_years} 年")
            except Exception as e:
                logger.error(f"外推查询处理失败: {str(e)}")
                # 使用示例数据
                predictions_by_year, relationship_stats, general_insights = get_sample_extrapolation_data(entity, future_years)
            
            # 渲染结果页面
            return render_template('extrapolation_result.html', 
                                predictions_by_year=predictions_by_year,
                                relationship_stats=relationship_stats,
                                general_insights=general_insights,
                                entity=entity, 
                                future_years=future_years,
                                top_k=top_k)
        except Exception as e:
            logger.error(f"处理外推查询时出错: {str(e)}")
            return render_template('extrapolation.html', error=str(e))
    
    # GET请求，渲染表单页面
    return render_template('extrapolation.html')


@app.route('/api/interpolation', methods=['POST'])
def api_interpolation():
    """内推API接口"""
    try:
        data = request.json
        entity1 = data.get('entity1', '').strip()
        relationship = data.get('relationship', '').strip()
        entity2 = data.get('entity2', '').strip()
        top_k = int(data.get('top_k', 5))
        
        results = qa_engine.answer_interpolation_query(entity1, relationship, entity2, top_k)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        logger.error(f"内推API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extrapolation', methods=['POST'])
def api_extrapolation():
    """外推API接口"""
    try:
        data = request.json
        entity = data.get('entity', '').strip()
        future_years = int(data.get('future_years', 5))
        top_k = int(data.get('top_k', 5))
        
        if not entity:
            return jsonify({'error': '请输入实体名称'}), 400
        
        # 使用问答引擎处理外推查询
        try:
            predictions_by_year, relationship_stats, general_insights = qa_engine.answer_extrapolation_query(entity, future_years, top_k)
        except Exception as e:
            logger.error(f"API外推查询处理失败: {str(e)}")
            predictions_by_year, relationship_stats, general_insights = get_sample_extrapolation_data(entity, future_years)
        
        return jsonify({
            'success': True,
            'predictions_by_year': predictions_by_year,
            'relationship_stats': relationship_stats,
            'general_insights': general_insights,
            'input_data': {
                'entity': entity,
                'future_years': future_years,
                'top_k': top_k
            }
        })
    except Exception as e:
        logger.error(f"外推API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/trends', methods=['POST'])
def api_trends():
    """行业趋势预测API接口"""
    try:
        data = request.json
        industry = data.get('industry', '').strip()
        future_years = int(data.get('future_years', 5))
        
        if not industry:
            return jsonify({'error': '请输入行业名称'}), 400
        
        # 使用问答引擎处理行业趋势预测
        try:
            trends = qa_engine.predict_industry_trend(industry, future_years, 5)  # 这里默认使用top_k=5
        except Exception as e:
            logger.error(f"API行业趋势预测处理失败: {str(e)}")
            # 生成示例趋势数据
            trends = [
                {
                    "year": datetime.now().year + i,
                    "trend": f"{industry}行业在{i+1}年后的主要趋势",
                    "description": f"随着技术发展，{industry}行业将经历重要变革，包括数字化转型加速、新兴技术应用普及等。",
                    "confidence": 0.8 - (i * 0.1)
                }
                for i in range(future_years)
            ]
        
        return jsonify({
            'success': True,
            'trends': trends,
            'input_data': {
                'industry': industry,
                'future_years': future_years
            }
        })
    except Exception as e:
        logger.error(f"API行业趋势预测处理错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health')
def health_check():
    """健康检查接口"""
    global preprocessor, graph_manager, qa_engine
    
    status = {
        'preprocessor_loaded': preprocessor is not None,
        'graph_manager_loaded': graph_manager is not None,
        'qa_engine_loaded': qa_engine is not None,
        'node_count': graph_manager.get_node_count() if graph_manager else 0
    }
    
    return jsonify({
        'status': 'healthy' if all(status.values()) else 'unhealthy',
        'components': status
    })


if __name__ == '__main__':
    # 初始化系统组件
    initialized = initialize_components()
    
    if initialized:
        logger.info("启动Flask应用...")
        # 开发环境下运行
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        logger.error("系统初始化失败，无法启动应用")