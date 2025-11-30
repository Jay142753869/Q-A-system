import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import torch
import torch.nn as nn
import torch.optim as optim
import logging

class InterpolationModel:
    def __init__(self, graph_manager, embedding_dim=128):
        """初始化内推模型"""
        self.graph_manager = graph_manager
        self.embedding_dim = embedding_dim
        self.logger = logging.getLogger(__name__)
        
        # 初始化实体和关系的嵌入
        self.entity_embeddings = {}
        self.relationship_embeddings = {}
        
        # 构建嵌入模型
        self._build_embeddings()
    
    def _build_embeddings(self):
        """构建实体和关系的嵌入"""
        # 获取所有实体
        entities = self.graph_manager.get_all_entities(limit=1000)
        for entity_data in entities:
            if isinstance(entity_data, dict) and 'properties' in entity_data:
                entity_id = entity_data['properties'].get('name', str(entity_data['properties'].get('id', 'unknown')))
                # 为每个实体创建随机嵌入
                self.entity_embeddings[entity_id] = np.random.normal(0, 0.1, self.embedding_dim)
        
        # 获取所有关系类型
        relationships = self.graph_manager.get_all_relationships(limit=100)
        for rel_data in relationships:
            if isinstance(rel_data, dict) and 'relationship_type' in rel_data:
                rel_type = rel_data['relationship_type']
                # 为每个关系类型创建随机嵌入
                self.relationship_embeddings[rel_type] = np.random.normal(0, 0.1, self.embedding_dim)
        
        self.logger.info(f"构建了 {len(self.entity_embeddings)} 个实体嵌入和 {len(self.relationship_embeddings)} 个关系嵌入")
    
    def predict_missing_relationships(self, entity, top_k=5):
        """预测与给定实体可能存在的缺失关系"""
        if entity not in self.entity_embeddings:
            self.logger.warning(f"实体 '{entity}' 不在嵌入模型中")
            return []
        
        entity_emb = self.entity_embeddings[entity]
        predictions = []
        
        # 对每个可能的目标实体和关系类型进行预测
        for target_entity, target_emb in self.entity_embeddings.items():
            if target_entity == entity:  # 跳过自身
                continue
            
            for rel_type, rel_emb in self.relationship_embeddings.items():
                # 使用简单的评分函数：实体嵌入 + 关系嵌入 与 目标实体嵌入的相似度
                # 这是TransE模型的简化版本
                predicted_target = entity_emb + rel_emb
                similarity = cosine_similarity([predicted_target], [target_emb])[0][0]
                
                # 检查这种关系是否已经存在
                existing_rels = self.graph_manager.query_relationship_between_entities(entity, target_entity)
                if not any(r['relationship'] == rel_type for r in existing_rels):
                    predictions.append({
                        'source': entity,
                        'relationship': rel_type,
                        'target': target_entity,
                        'score': float(similarity)
                    })
        
        # 按分数排序，返回top_k个预测
        predictions.sort(key=lambda x: x['score'], reverse=True)
        return predictions[:top_k]
    
    def predict_related_entities(self, entity, relationship_type, top_k=5):
        """预测与给定实体存在特定关系的其他实体"""
        if entity not in self.entity_embeddings:
            self.logger.warning(f"实体 '{entity}' 不在嵌入模型中")
            return []
        
        if relationship_type not in self.relationship_embeddings:
            self.logger.warning(f"关系类型 '{relationship_type}' 不在嵌入模型中")
            return []
        
        entity_emb = self.entity_embeddings[entity]
        rel_emb = self.relationship_embeddings[relationship_type]
        
        # 预测目标实体的嵌入
        predicted_target_emb = entity_emb + rel_emb
        
        # 计算与所有其他实体的相似度
        similarities = []
        for target_entity, target_emb in self.entity_embeddings.items():
            if target_entity == entity:  # 跳过自身
                continue
            
            similarity = cosine_similarity([predicted_target_emb], [target_emb])[0][0]
            
            # 检查这种关系是否已经存在
            existing_rels = self.graph_manager.query_entities_relationships(entity, relationship_type)
            if not any(r['related_entity'] == target_entity for r in existing_rels):
                similarities.append({
                    'entity': entity,
                    'relationship': relationship_type,
                    'predicted_target': target_entity,
                    'score': float(similarity)
                })
        
        # 按相似度排序，返回top_k个预测
        similarities.sort(key=lambda x: x['score'], reverse=True)
        return similarities[:top_k]
    
    def train(self, epochs=10, learning_rate=0.01):
        """训练嵌入模型（简化版）"""
        # 收集训练数据：已知的三元组 (head, relation, tail)
        training_data = []
        
        # 查询所有关系作为训练数据
        for rel_type in self.relationship_embeddings.keys():
            query = f"MATCH (h)-[r:{rel_type}]->(t) RETURN h.name AS head, t.name AS tail"
            results = self.graph_manager.neo4j_manager.execute_query(query)
            
            for result in results:
                if result['head'] in self.entity_embeddings and result['tail'] in self.entity_embeddings:
                    training_data.append((result['head'], rel_type, result['tail']))
        
        if not training_data:
            self.logger.warning("没有找到训练数据")
            return
        
        # 将嵌入转换为PyTorch张量
        entity_emb_tensor = {}
        for entity, emb in self.entity_embeddings.items():
            entity_emb_tensor[entity] = nn.Parameter(torch.tensor(emb, dtype=torch.float32))
        
        rel_emb_tensor = {}
        for rel, emb in self.relationship_embeddings.items():
            rel_emb_tensor[rel] = nn.Parameter(torch.tensor(emb, dtype=torch.float32))
        
        # 创建优化器
        parameters = list(entity_emb_tensor.values()) + list(rel_emb_tensor.values())
        optimizer = optim.Adam(parameters, lr=learning_rate)
        
        # 定义损失函数（TransE损失）
        def transE_loss(head, rel, tail, neg_tail):
            # 正样本：h + r ≈ t
            pos_score = torch.norm(head + rel - tail, dim=1)
            # 负样本：h + r ≉ t'
            neg_score = torch.norm(head + rel - neg_tail, dim=1)
            # 间隔损失
            margin = 1.0
            loss = torch.mean(torch.relu(pos_score - neg_score + margin))
            return loss
        
        # 开始训练
        self.logger.info(f"开始训练，共 {len(training_data)} 个训练样本")
        
        for epoch in range(epochs):
            total_loss = 0
            
            for head, rel, tail in training_data:
                # 准备正样本
                h_emb = entity_emb_tensor[head]
                r_emb = rel_emb_tensor[rel]
                t_emb = entity_emb_tensor[tail]
                
                # 随机选择一个负样本（简化版：随机选择一个其他实体）
                neg_entities = [e for e in self.entity_embeddings.keys() if e != tail]
                if neg_entities:
                    neg_tail = np.random.choice(neg_entities)
                    neg_t_emb = entity_emb_tensor[neg_tail]
                    
                    # 计算损失
                    loss = transE_loss(h_emb.unsqueeze(0), r_emb.unsqueeze(0), t_emb.unsqueeze(0), neg_t_emb.unsqueeze(0))
                    
                    # 反向传播和优化
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
            
            # 更新嵌入字典
            for entity, param in entity_emb_tensor.items():
                self.entity_embeddings[entity] = param.detach().numpy()
            
            for rel, param in rel_emb_tensor.items():
                self.relationship_embeddings[rel] = param.detach().numpy()
            
            self.logger.info(f"Epoch {epoch+1}/{epochs}, 平均损失: {total_loss/len(training_data):.6f}")
    
    def save_embeddings(self, filepath):
        """保存嵌入到文件"""
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump({
                'entity_embeddings': self.entity_embeddings,
                'relationship_embeddings': self.relationship_embeddings,
                'embedding_dim': self.embedding_dim
            }, f)
        self.logger.info(f"嵌入已保存到 {filepath}")
    
    def load_embeddings(self, filepath):
        """从文件加载嵌入"""
        import pickle
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.entity_embeddings = data['entity_embeddings']
                self.relationship_embeddings = data['relationship_embeddings']
                self.embedding_dim = data['embedding_dim']
            self.logger.info(f"从 {filepath} 加载嵌入成功")
            return True
        except Exception as e:
            self.logger.error(f"加载嵌入失败: {str(e)}")
            return False

# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # 导入知识图谱管理器
        from knowledge_graph import GraphManager, Neo4jManager
        
        # 初始化知识图谱
        neo4j_manager = Neo4jManager()
        graph_manager = GraphManager(neo4j_manager)
        
        # 初始化内推模型
        model = InterpolationModel(graph_manager, embedding_dim=64)
        
        # 训练模型
        print("训练内推模型...")
        model.train(epochs=5, learning_rate=0.01)
        
        # 预测缺失的关系
        print("\n预测苹果公司可能的关系:")
        predictions = model.predict_missing_relationships("苹果公司", top_k=5)
        for i, pred in enumerate(predictions, 1):
            print(f"  {i}. {pred['source']} -[{pred['relationship']}]-> {pred['target']} (分数: {pred['score']:.4f})")
        
        # 预测特定关系的目标实体
        print("\n预测苹果公司可能收购的公司:")
        investment_predictions = model.predict_related_entities("苹果公司", "INVESTS_IN", top_k=5)
        for i, pred in enumerate(investment_predictions, 1):
            print(f"  {i}. {pred['entity']} 可能 {pred['relationship']} {pred['predicted_target']} (分数: {pred['score']:.4f})")
    
    except Exception as e:
        print(f"发生错误: {str(e)}")