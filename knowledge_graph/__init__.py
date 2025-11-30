from .neo4j_manager import Neo4jManager
from .graph_manager import GraphManager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

__all__ = ['Neo4jManager', 'GraphManager', 'init_knowledge_graph']

def init_knowledge_graph(uri="neo4j://localhost:7687", user="neo4j", password="password", 
                        sample_data=True, sample_path=None):
    """
    初始化知识图谱
    
    Args:
        uri: Neo4j数据库URI
        user: 用户名
        password: 密码
        sample_data: 是否导入示例数据
        sample_path: 示例数据路径
    
    Returns:
        GraphManager实例
    """
    # 初始化Neo4j连接
    neo4j_manager = Neo4jManager(uri, user, password)
    
    # 检查连接是否成功
    if not neo4j_manager.driver:
        logging.error("无法连接到Neo4j数据库，请检查配置")
        return None
    
    # 初始化图谱管理器
    graph_manager = GraphManager(neo4j_manager)
    
    # 导入示例数据
    if sample_data:
        if sample_path is None:
            import os
            sample_path = os.path.join(
                os.path.dirname(__file__), 
                'data', 
                'sample_graph.json'
            )
        
        if os.path.exists(sample_path):
            logging.info(f"导入示例数据: {sample_path}")
            success = graph_manager.build_graph_from_json(sample_path)
            if success:
                logging.info("示例数据导入成功")
            else:
                logging.warning("示例数据导入失败")
        else:
            logging.warning(f"示例数据文件不存在: {sample_path}")
    
    return graph_manager

# 示例用法
def example_usage():
    """示例用法"""
    try:
        # 初始化知识图谱
        graph_manager = init_knowledge_graph()
        
        if graph_manager:
            # 测试基本查询
            print("\n===== 知识图谱示例查询 =====\n")
            
            # 查询实体信息
            print("1. 查询苹果公司信息:")
            entity_info = graph_manager.get_entity_info("苹果公司")
            if entity_info:
                for info in entity_info:
                    print(f"   类型: {info['type']}")
                    print(f"   属性: {info['properties']}")
            
            # 查询实体关系
            print("\n2. 查询苹果公司的产品:")
            relationships = graph_manager.query_entities_relationships("苹果公司", "PRODUCES")
            if relationships:
                for rel in relationships:
                    print(f"   - {rel['entity']} 生产 {rel['related_entity']} (自{rel.get('rel_properties', {}).get('since', '未知')}年)")
            
            # 查询公司之间的竞争关系
            print("\n3. 查询公司间的竞争关系:")
            competition = graph_manager.execute_query(
                "MATCH (a:Company)-[r:COMPETES_WITH]->(b:Company) RETURN a.name AS company1, r.field AS field, b.name AS company2"
            )
            if competition:
                for comp in competition:
                    print(f"   - {comp['company1']} 与 {comp['company2']} 在 {comp['field']} 领域竞争")
            
            # 查询人物与公司的关系
            print("\n4. 查询人物与公司的关系:")
            person_company = graph_manager.execute_query(
                "MATCH (p:Person)-[r]->(c:Company) RETURN p.name AS person, type(r) AS relationship, c.name AS company"
            )
            if person_company:
                for pc in person_company:
                    print(f"   - {pc['person']} {pc['relationship']} {pc['company']}")
            
            # 查询最短路径
            print("\n5. 查询苹果公司和特斯拉公司之间的路径:")
            path = graph_manager.query_path_between_entities("苹果公司", "特斯拉公司")
            if path:
                print(f"   找到路径: {len(path)} 条")
            else:
                print("   未找到直接路径")
    
    except Exception as e:
        logging.error(f"示例运行出错: {str(e)}")
    finally:
        if 'graph_manager' in locals():
            graph_manager.close()

if __name__ == "__main__":
    example_usage()