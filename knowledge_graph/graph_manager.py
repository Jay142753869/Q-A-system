from .neo4j_manager import Neo4jManager
import json
import logging
import pandas as pd

class GraphManager:
    def __init__(self, neo4j_manager=None):
        """初始化知识图谱管理器"""
        self.neo4j_manager = neo4j_manager or Neo4jManager()
        self.logger = logging.getLogger(__name__)
    
    def build_graph_from_json(self, data_path):
        """从JSON文件构建知识图谱"""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 创建节点
            if 'nodes' in data:
                for node in data['nodes']:
                    label = node.pop('label')
                    self.neo4j_manager.create_node(label, node)
                    self.logger.info(f"创建节点: {label} {node}")
            
            # 创建关系
            if 'relationships' in data:
                for rel in data['relationships']:
                    self.neo4j_manager.create_relationship(
                        rel['start_label'],
                        {rel['start_property']: rel['start_value']},
                        rel['type'],
                        rel['end_label'],
                        {rel['end_property']: rel['end_value']},
                        rel.get('properties', {})
                    )
                    self.logger.info(f"创建关系: {rel['type']}")
            
            return True
        except Exception as e:
            self.logger.error(f"从JSON构建图谱失败: {str(e)}")
            return False
    
    def build_graph_from_csv(self, nodes_csv, relationships_csv):
        """从CSV文件构建知识图谱"""
        try:
            # 导入节点
            nodes_df = pd.read_csv(nodes_csv)
            for _, row in nodes_df.iterrows():
                # 假设CSV中有label列，其余列为属性
                row_dict = row.to_dict()
                label = row_dict.pop('label')
                self.neo4j_manager.create_node(label, row_dict)
            
            # 导入关系
            rels_df = pd.read_csv(relationships_csv)
            for _, row in rels_df.iterrows():
                row_dict = row.to_dict()
                # 假设CSV中有必要的关系信息列
                self.neo4j_manager.create_relationship(
                    row_dict['start_label'],
                    {row_dict['start_property']: row_dict['start_value']},
                    row_dict['type'],
                    row_dict['end_label'],
                    {row_dict['end_property']: row_dict['end_value']},
                    {k: v for k, v in row_dict.items() if k not in ['start_label', 'start_property', 'start_value', 'type', 'end_label', 'end_property', 'end_value']}
                )
            
            return True
        except Exception as e:
            self.logger.error(f"从CSV构建图谱失败: {str(e)}")
            return False
    
    def query_entities_relationships(self, entity, relationship=None, top_k=5):
        """查询与实体相关的关系和其他实体"""
        if relationship:
            query = f"""
            MATCH (e)-[r:{relationship}]->(related)
            WHERE e.name CONTAINS $entity OR e.id = $entity
            RETURN e.name AS entity, type(r) AS relationship, labels(related)[0] AS related_type, related.name AS related_entity, properties(r) AS rel_properties
            LIMIT $limit
            """
        else:
            query = f"""
            MATCH (e)-[r]->(related)
            WHERE e.name CONTAINS $entity OR e.id = $entity
            RETURN e.name AS entity, type(r) AS relationship, labels(related)[0] AS related_type, related.name AS related_entity, properties(r) AS rel_properties
            LIMIT $limit
            """
        
        return self.neo4j_manager.execute_query(
            query, 
            {"entity": entity, "limit": top_k}
        )
    
    def query_relationship_between_entities(self, entity1, entity2):
        """查询两个实体之间的关系"""
        query = f"""
        MATCH (e1)-[r]-(e2)
        WHERE (e1.name CONTAINS $entity1 OR e1.id = $entity1) AND 
              (e2.name CONTAINS $entity2 OR e2.id = $entity2)
        RETURN e1.name AS entity1, type(r) AS relationship, e2.name AS entity2, properties(r) AS rel_properties
        """
        
        return self.neo4j_manager.execute_query(
            query, 
            {"entity1": entity1, "entity2": entity2}
        )
    
    def query_path_between_entities(self, entity1, entity2, max_depth=3):
        """查询两个实体之间的路径"""
        query = f"""
        MATCH path = shortestPath((e1)-[*1..{max_depth}]-(e2))
        WHERE (e1.name CONTAINS $entity1 OR e1.id = $entity1) AND 
              (e2.name CONTAINS $entity2 OR e2.id = $entity2)
        RETURN path
        """
        
        return self.neo4j_manager.execute_query(
            query, 
            {"entity1": entity1, "entity2": entity2}
        )
    
    def get_entity_info(self, entity_name):
        """获取实体的详细信息"""
        query = f"""
        MATCH (e) WHERE e.name CONTAINS $entity_name OR e.id = $entity_name
        RETURN labels(e)[0] AS type, properties(e) AS properties
        LIMIT 1
        """
        
        return self.neo4j_manager.execute_query(
            query, 
            {"entity_name": entity_name}
        )
    
    def get_all_entities(self, label=None, limit=100):
        """获取所有实体"""
        if label:
            query = f"MATCH (e:{label}) RETURN properties(e) AS entity LIMIT $limit"
        else:
            query = "MATCH (e) RETURN labels(e)[0] AS type, properties(e) AS entity LIMIT $limit"
        
        return self.neo4j_manager.execute_query(
            query, 
            {"limit": limit}
        )
    
    def get_all_relationships(self, limit=100):
        """获取所有关系类型"""
        query = "MATCH ()-[r]->() RETURN DISTINCT type(r) AS relationship_type LIMIT $limit"
        return self.neo4j_manager.execute_query(
            query, 
            {"limit": limit}
        )
    
    def export_graph_to_json(self, output_path):
        """导出知识图谱为JSON格式"""
        try:
            # 获取所有节点
            nodes_query = "MATCH (n) RETURN labels(n)[0] AS label, properties(n) AS properties"
            nodes = self.neo4j_manager.execute_query(nodes_query)
            
            # 获取所有关系
            relationships_query = """
            MATCH (a)-[r]->(b)
            RETURN labels(a)[0] AS start_label, properties(a) AS start_props,
                   type(r) AS type, properties(r) AS rel_props,
                   labels(b)[0] AS end_label, properties(b) AS end_props
            """
            relationships = self.neo4j_manager.execute_query(relationships_query)
            
            # 构建导出数据结构
            export_data = {
                "nodes": [],
                "relationships": []
            }
            
            # 处理节点
            for node in nodes:
                node_data = node['properties']
                node_data['label'] = node['label']
                export_data['nodes'].append(node_data)
            
            # 处理关系
            for rel in relationships:
                # 使用name属性作为标识，如果没有则使用id
                start_id_prop = 'name' if 'name' in rel['start_props'] else 'id'
                end_id_prop = 'name' if 'name' in rel['end_props'] else 'id'
                
                rel_data = {
                    "start_label": rel['start_label'],
                    "start_property": start_id_prop,
                    "start_value": rel['start_props'].get(start_id_prop, ''),
                    "type": rel['type'],
                    "end_label": rel['end_label'],
                    "end_property": end_id_prop,
                    "end_value": rel['end_props'].get(end_id_prop, ''),
                    "properties": rel['rel_props']
                }
                export_data['relationships'].append(rel_data)
            
            # 保存到JSON文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"导出图谱失败: {str(e)}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.neo4j_manager:
            self.neo4j_manager.close()

# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # 初始化图谱管理器
        graph_manager = GraphManager()
        
        # 示例：查询实体信息
        print("查询苹果公司信息:")
        entity_info = graph_manager.get_entity_info("苹果公司")
        if entity_info:
            for info in entity_info:
                print(f"类型: {info['type']}")
                print(f"属性: {info['properties']}")
        
        # 查询关系
        print("\n查询苹果公司的关系:")
        relationships = graph_manager.query_entities_relationships("苹果公司")
        for rel in relationships:
            print(f"{rel['entity']} -[{rel['relationship']}]-> {rel['related_entity']} ({rel['related_type']})")
        
        # 查询两个实体之间的关系
        print("\n查询苹果公司和微软公司的关系:")
        entity_relations = graph_manager.query_relationship_between_entities("苹果公司", "微软公司")
        for rel in entity_relations:
            print(f"{rel['entity1']} -[{rel['relationship']}]-> {rel['entity2']}")
            if rel['rel_properties']:
                print(f"关系属性: {rel['rel_properties']}")
    
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        if 'graph_manager' in locals():
            graph_manager.close()