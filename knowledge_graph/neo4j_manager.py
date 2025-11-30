from neo4j import GraphDatabase
import logging

class Neo4jManager:
    def __init__(self, uri="neo4j://localhost:7687", user="neo4j", password="password"):
        """初始化Neo4j连接管理器"""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._connect()
    
    def _connect(self):
        """建立与Neo4j数据库的连接"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # 测试连接
            self.test_connection()
            logging.info("成功连接到Neo4j数据库")
        except Exception as e:
            logging.error(f"连接Neo4j数据库失败: {str(e)}")
            self.driver = None
    
    def test_connection(self):
        """测试数据库连接"""
        if self.driver:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS count")
                return result.single()[0] == 1
        return False
    
    def execute_query(self, query, parameters=None):
        """执行Cypher查询"""
        if not self.driver:
            logging.error("数据库连接未初始化")
            return None
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logging.error(f"执行查询失败: {str(e)}")
            return None
    
    def execute_write(self, query, parameters=None):
        """执行写操作的Cypher查询"""
        if not self.driver:
            logging.error("数据库连接未初始化")
            return None
        
        try:
            with self.driver.session() as session:
                result = session.write_transaction(lambda tx: tx.run(query, parameters or {}).data())
                return result
        except Exception as e:
            logging.error(f"执行写操作失败: {str(e)}")
            return None
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logging.info("已关闭Neo4j数据库连接")
    
    def create_node(self, label, properties):
        """创建节点"""
        # 构建属性字符串
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE (n:{label} {{ {props_str} }}) RETURN n"
        return self.execute_write(query, properties)
    
    def create_relationship(self, start_node_label, start_node_prop, 
                          relationship_type, end_node_label, end_node_prop, 
                          rel_properties=None):
        """创建关系"""
        # 查找开始节点
        start_query = f"MATCH (a:{start_node_label}) WHERE a.{list(start_node_prop.keys())[0]} = ${list(start_node_prop.keys())[0]} RETURN a LIMIT 1"
        # 查找结束节点
        end_query = f"MATCH (b:{end_node_label}) WHERE b.{list(end_node_prop.keys())[0]} = ${list(end_node_prop.keys())[0]} RETURN b LIMIT 1"
        
        # 组合查询参数
        params = {**start_node_prop, **end_node_prop}
        
        # 添加关系属性
        rel_props_str = ""
        if rel_properties:
            rel_props_str = ", " + ", ".join([f"{k}: ${k}_rel" for k in rel_properties.keys()])
            # 添加关系属性到参数
            for k, v in rel_properties.items():
                params[f"{k}_rel"] = v
        
        # 创建关系
        query = f"""
        {start_query}
        {end_query}
        CREATE (a)-[r:{relationship_type} {{created_at: datetime() {rel_props_str}}}]->(b)
        RETURN a, r, b
        """
        
        return self.execute_write(query, params)
    
    def get_node_by_property(self, label, property_name, property_value):
        """根据属性查找节点"""
        query = f"MATCH (n:{label}) WHERE n.{property_name} = $value RETURN n"
        return self.execute_query(query, {"value": property_value})
    
    def get_relationships(self, node_label, property_name, property_value, 
                         relationship_type=None):
        """获取节点的关系"""
        rel_filter = f"[:{relationship_type}]" if relationship_type else ""
        query = f"""
        MATCH (n:{node_label})-[r{rel_filter}]-(m)
        WHERE n.{property_name} = $value
        RETURN n, r, m
        """
        return self.execute_query(query, {"value": property_value})
    
    def clear_database(self):
        """清空数据库（谨慎使用）"""
        query = "MATCH (n) DETACH DELETE n"
        return self.execute_write(query)

# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # 初始化Neo4j管理器
        neo4j_manager = Neo4jManager()
        
        if neo4j_manager.driver:
            print("Neo4j连接测试成功!")
            
            # 示例：创建一些测试数据
            print("\n创建测试数据...")
            
            # 创建公司节点
            neo4j_manager.create_node("Company", {"name": "苹果公司", "industry": "科技", "founded": 1976})
            neo4j_manager.create_node("Company", {"name": "微软公司", "industry": "科技", "founded": 1975})
            neo4j_manager.create_node("Company", {"name": "特斯拉公司", "industry": "汽车", "founded": 2003})
            
            # 创建产品节点
            neo4j_manager.create_node("Product", {"name": "iPhone", "category": "智能手机", "price": 999})
            neo4j_manager.create_node("Product", {"name": "Windows", "category": "操作系统", "price": 199})
            
            # 创建关系
            neo4j_manager.create_relationship(
                "Company", {"name": "苹果公司"}, 
                "PRODUCES", 
                "Product", {"name": "iPhone"}, 
                {"since": 2007}
            )
            
            neo4j_manager.create_relationship(
                "Company", {"name": "微软公司"}, 
                "PRODUCES", 
                "Product", {"name": "Windows"}, 
                {"since": 1985}
            )
            
            neo4j_manager.create_relationship(
                "Company", {"name": "苹果公司"}, 
                "COMPETES_WITH", 
                "Company", {"name": "微软公司"}
            )
            
            # 查询数据
            print("\n查询公司信息:")
            companies = neo4j_manager.execute_query("MATCH (c:Company) RETURN c.name AS name, c.industry AS industry")
            for company in companies:
                print(f"- {company['name']} ({company['industry']})")
            
            print("\n查询产品信息:")
            products = neo4j_manager.execute_query("MATCH (p:Product) RETURN p.name AS name, p.category AS category")
            for product in products:
                print(f"- {product['name']} ({product['category']})")
            
            print("\n查询公司与产品的关系:")
            relationships = neo4j_manager.execute_query(
                "MATCH (c:Company)-[r:PRODUCES]->(p:Product) RETURN c.name AS company, p.name AS product, r.since AS since"
            )
            for rel in relationships:
                print(f"- {rel['company']} 生产 {rel['product']} (自{rel['since']}年)")
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        if 'neo4j_manager' in locals():
            neo4j_manager.close()