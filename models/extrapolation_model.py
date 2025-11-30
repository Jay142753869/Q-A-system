import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import torch
import torch.nn as nn
import torch.optim as optim
import logging
from sklearn.metrics.pairwise import cosine_similarity

class ExtrapolationModel:
    def __init__(self, graph_manager, embedding_dim=128):
        """初始化外推模型"""
        self.graph_manager = graph_manager
        self.embedding_dim = embedding_dim
        self.logger = logging.getLogger(__name__)
        
        # 初始化实体和关系的时间感知嵌入
        self.entity_embeddings = {}
        self.relationship_embeddings = {}
        self.temporal_data = []  # 存储时间相关的数据
        
        # 构建模型
        self._build_temporal_model()
    
    def _build_temporal_model(self):
        """构建时间感知模型"""
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
        
        # 收集时间相关数据
        self._collect_temporal_data()
        
        self.logger.info(f"构建了时间感知模型，包含 {len(self.entity_embeddings)} 个实体和 {len(self.relationship_embeddings)} 个关系")
    
    def _collect_temporal_data(self):
        """收集时间相关的数据"""
        # 查询所有带时间属性的关系
        query = """
        MATCH (h)-[r]->(t)
        WHERE r.since IS NOT NULL OR r.year IS NOT NULL OR r.created_at IS NOT NULL
        RETURN h.name AS head, type(r) AS relationship, t.name AS tail, properties(r) AS props
        """
        results = self.graph_manager.neo4j_manager.execute_query(query)
        
        for result in results:
            # 提取时间信息
            year = None
            if 'year' in result['props']:
                year = result['props']['year']
            elif 'since' in result['props']:
                year = result['props']['since']
            elif 'created_at' in result['props']:
                # 处理Neo4j的datetime格式
                created_at = result['props']['created_at']
                if isinstance(created_at, str):
                    try:
                        year = int(created_at.split('-')[0])
                    except:
                        pass
            
            if year and result['head'] in self.entity_embeddings and result['tail'] in self.entity_embeddings:
                self.temporal_data.append({
                    'head': result['head'],
                    'relationship': result['relationship'],
                    'tail': result['tail'],
                    'year': int(year)
                })
        
        # 转换为DataFrame便于处理
        if self.temporal_data:
            self.temporal_df = pd.DataFrame(self.temporal_data)
            self.logger.info(f"收集了 {len(self.temporal_data)} 条时间相关数据")
        else:
            self.temporal_df = pd.DataFrame(columns=['head', 'relationship', 'tail', 'year'])
            self.logger.warning("没有收集到时间相关数据")
    
    def predict_future_relationships(self, entity, future_years=5, top_k=5):
        """预测实体未来可能发生的关系"""
        if entity not in self.entity_embeddings:
            self.logger.warning(f"实体 '{entity}' 不在模型中")
            return []
        
        predictions = []
        current_year = datetime.now().year
        future_year = current_year + future_years
        
        # 分析实体的历史行为模式
        entity_history = self.temporal_df[self.temporal_df['head'] == entity]
        
        # 计算实体在不同关系类型上的活跃度
        if not entity_history.empty:
            rel_counts = entity_history['relationship'].value_counts()
            # 对每种关系类型，预测可能的目标实体
            for rel_type, count in rel_counts.items():
                if rel_type not in self.relationship_embeddings:
                    continue
                
                # 基于历史行为和嵌入相似性进行预测
                rel_predictions = self._predict_relationship_target(entity, rel_type, future_year)
                predictions.extend(rel_predictions)
        else:
            # 如果没有历史数据，使用一般的嵌入相似性
            for rel_type, rel_emb in self.relationship_embeddings.items():
                # 简单的基于嵌入的预测
                entity_emb = self.entity_embeddings[entity]
                for target_entity, target_emb in self.entity_embeddings.items():
                    if target_entity == entity:
                        continue
                    
                    # 检查关系是否已存在
                    existing = self.graph_manager.query_relationship_between_entities(entity, target_entity)
                    if not any(r['relationship'] == rel_type for r in existing):
                        # 计算预测分数
                        similarity = cosine_similarity([entity_emb + rel_emb], [target_emb])[0][0]
                        predictions.append({
                            'source': entity,
                            'relationship': rel_type,
                            'target': target_entity,
                            'predicted_year': future_year,
                            'confidence': float(similarity),
                            'reason': '基于语义相似度的预测'
                        })
        
        # 按置信度排序，返回top_k个预测
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return predictions[:top_k]
    
    def _predict_relationship_target(self, entity, relationship_type, future_year):
        """预测特定关系类型的目标实体"""
        predictions = []
        entity_emb = self.entity_embeddings[entity]
        rel_emb = self.relationship_embeddings[relationship_type]
        
        # 分析历史目标实体的特征
        entity_history = self.temporal_df[(self.temporal_df['head'] == entity) & 
                                         (self.temporal_df['relationship'] == relationship_type)]
        
        if not entity_history.empty:
            # 获取历史目标实体的嵌入
            history_targets = entity_history['tail'].tolist()
            if history_targets:
                # 计算历史目标实体的平均嵌入
                history_embs = np.array([self.entity_embeddings[t] for t in history_targets if t in self.entity_embeddings])
                if len(history_embs) > 0:
                    avg_history_emb = np.mean(history_embs, axis=0)
                    
                    # 寻找与历史目标实体相似的其他实体
                    for target_entity, target_emb in self.entity_embeddings.items():
                        if target_entity == entity or target_entity in history_targets:
                            continue
                        
                        # 检查关系是否已存在
                        existing = self.graph_manager.query_relationship_between_entities(entity, target_entity)
                        if not any(r['relationship'] == relationship_type for r in existing):
                            # 综合得分：与历史模式的相似度 + 基于嵌入模型的预测
                            pattern_similarity = cosine_similarity([target_emb], [avg_history_emb])[0][0]
                            embedding_similarity = cosine_similarity([entity_emb + rel_emb], [target_emb])[0][0]
                            combined_score = 0.6 * pattern_similarity + 0.4 * embedding_similarity
                            
                            predictions.append({
                                'source': entity,
                                'relationship': relationship_type,
                                'target': target_entity,
                                'predicted_year': future_year,
                                'confidence': float(combined_score),
                                'reason': f'基于{relationship_type}历史模式的预测'
                            })
        
        return predictions
    
    def predict_market_trend(self, industry, future_years=5, top_k=5):
        """预测特定行业的市场趋势"""
        # 查询该行业的所有公司
        query = f"MATCH (c:Company) WHERE c.industry = $industry RETURN c.name AS company, properties(c) AS props"
        companies = self.graph_manager.neo4j_manager.execute_query(query, {"industry": industry})
        
        if not companies:
            self.logger.warning(f"未找到行业 '{industry}' 的公司")
            return []
        
        company_names = [c['company'] for c in companies]
        trend_predictions = []
        future_year = datetime.now().year + future_years
        
        # 分析行业内的关系模式
        for company in company_names:
            if company in self.entity_embeddings:
                # 预测该公司在行业内的未来行为
                predictions = self.predict_future_relationships(company, future_years, top_k=3)
                for pred in predictions:
                    # 只考虑行业内的关系
                    if pred['target'] in company_names:
                        trend_predictions.append({
                            'industry': industry,
                            'prediction': f"{pred['source']} 可能在 {pred['predicted_year']} 年与 {pred['target']} 建立 {pred['relationship']} 关系",
                            'confidence': pred['confidence'],
                            'reason': pred['reason'],
                            'participants': [pred['source'], pred['target']]
                        })
        
        # 按置信度排序
        trend_predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return trend_predictions[:top_k]
    
    def train(self, epochs=10, learning_rate=0.01):
        """训练时间感知嵌入模型"""
        if not self.temporal_data:
            self.logger.warning("没有时间数据可供训练")
            return
        
        # 将嵌入转换为PyTorch张量
        entity_params = {}
        for entity, emb in self.entity_embeddings.items():
            entity_params[entity] = nn.Parameter(torch.tensor(emb, dtype=torch.float32))
        
        rel_params = {}
        for rel, emb in self.relationship_embeddings.items():
            rel_params[rel] = nn.Parameter(torch.tensor(emb, dtype=torch.float32))
        
        # 创建优化器
        parameters = list(entity_params.values()) + list(rel_params.values())
        optimizer = optim.Adam(parameters, lr=learning_rate)
        
        # 定义带时间权重的损失函数
        def temporal_loss(head, rel, tail, year, max_year):
            # 时间衰减因子：越近期的数据权重越高
            time_weight = 1.0 - (max_year - year) / (max_year - min(self.temporal_df['year'].min(), year - 10))
            time_weight = max(0.1, min(1.0, time_weight))
            
            # 基本的TransE损失
            score = torch.norm(head + rel - tail, dim=1)
            weighted_loss = time_weight * torch.mean(score)
            return weighted_loss
        
        # 获取最大年份
        max_year = self.temporal_df['year'].max() if not self.temporal_df.empty else datetime.now().year
        
        self.logger.info(f"开始训练时间感知模型，共 {len(self.temporal_data)} 个时间样本")
        
        for epoch in range(epochs):
            total_loss = 0
            
            for _, row in self.temporal_df.iterrows():
                head, rel, tail, year = row['head'], row['relationship'], row['tail'], row['year']
                
                if head in entity_params and rel in rel_params and tail in entity_params:
                    # 计算损失
                    loss = temporal_loss(
                        entity_params[head].unsqueeze(0),
                        rel_params[rel].unsqueeze(0),
                        entity_params[tail].unsqueeze(0),
                        year,
                        max_year
                    )
                    
                    # 反向传播和优化
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
            
            # 更新嵌入字典
            for entity, param in entity_params.items():
                self.entity_embeddings[entity] = param.detach().numpy()
            
            for rel, param in rel_params.items():
                self.relationship_embeddings[rel] = param.detach().numpy()
            
            self.logger.info(f"Epoch {epoch+1}/{epochs}, 平均损失: {total_loss/len(self.temporal_data):.6f}")
    
    def save_model(self, filepath):
        """保存模型"""
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump({
                'entity_embeddings': self.entity_embeddings,
                'relationship_embeddings': self.relationship_embeddings,
                'temporal_data': self.temporal_data,
                'embedding_dim': self.embedding_dim
            }, f)
        self.logger.info(f"模型已保存到 {filepath}")
    
    def load_model(self, filepath):
        """加载模型"""
        import pickle
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.entity_embeddings = data['entity_embeddings']
                self.relationship_embeddings = data['relationship_embeddings']
                self.temporal_data = data['temporal_data']
                self.embedding_dim = data['embedding_dim']
                # 重新构建DataFrame
                if self.temporal_data:
                    self.temporal_df = pd.DataFrame(self.temporal_data)
            self.logger.info(f"从 {filepath} 加载模型成功")
            return True
        except Exception as e:
            self.logger.error(f"加载模型失败: {str(e)}")
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
        
        # 初始化外推模型
        model = ExtrapolationModel(graph_manager, embedding_dim=64)
        
        # 训练模型
        print("训练外推模型...")
        model.train(epochs=5, learning_rate=0.01)
        
        # 预测未来关系
        print("\n预测苹果公司未来5年可能的关系:")
        future_predictions = model.predict_future_relationships("苹果公司", future_years=5, top_k=5)
        for i, pred in enumerate(future_predictions, 1):
            print(f"  {i}. {pred['source']} 可能在 {pred['predicted_year']} 年与 {pred['target']} 建立 {pred['relationship']} 关系")
            print(f"     置信度: {pred['confidence']:.4f}, 原因: {pred['reason']}")
        
        # 预测行业趋势
        print("\n预测科技行业未来趋势:")
        trends = model.predict_market_trend("科技", future_years=5, top_k=5)
        for i, trend in enumerate(trends, 1):
            print(f"  {i}. {trend['prediction']}")
            print(f"     置信度: {trend['confidence']:.4f}, 原因: {trend['reason']}")
    
    except Exception as e:
        print(f"发生错误: {str(e)}")