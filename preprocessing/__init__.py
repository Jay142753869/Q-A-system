from .text_processor import TextProcessor
from .ac_matcher import ACMatcher
from .bert_encoder import BertEncoder
import numpy as np

class QueryPreprocessor:
    def __init__(self, entities=None, relationships=None):
        """初始化查询预处理器"""
        # 初始化各个组件
        self.text_processor = TextProcessor()
        self.ac_matcher = ACMatcher()
        self.bert_encoder = BertEncoder()
        
        # 添加实体和关系到AC自动机
        if entities:
            self.ac_matcher.add_entities(entities)
        if relationships:
            self.ac_matcher.add_relationships(relationships)
        self.ac_matcher.build()
        
        # 预计算实体和关系的嵌入向量
        self.entity_embeddings = None
        self.relationship_embeddings = None
        self._precompute_embeddings()
    
    def _precompute_embeddings(self):
        """预计算实体和关系的嵌入向量"""
        if self.ac_matcher.entities:
            self.entity_embeddings = self.bert_encoder.get_batch_embeddings(self.ac_matcher.entities)
        if self.ac_matcher.relationships:
            self.relationship_embeddings = self.bert_encoder.get_batch_embeddings(self.ac_matcher.relationships)
    
    def update_knowledge_base(self, entities=None, relationships=None):
        """更新知识库中的实体和关系"""
        if entities:
            self.ac_matcher.add_entities(entities)
        if relationships:
            self.ac_matcher.add_relationships(relationships)
        self.ac_matcher.build()
        self._precompute_embeddings()
    
    def preprocess_query(self, query):
        """预处理用户查询"""
        # 1. 清理和分词
        cleaned_text = self.text_processor.clean_text(query)
        tokens = self.text_processor.tokenize(query)
        
        # 2. 使用AC自动机匹配实体和关系
        matches = self.ac_matcher.extract_entities_and_relationships(cleaned_text)
        
        # 3. 获取查询的嵌入向量
        query_embedding = self.bert_encoder.get_sentence_embedding(query)
        
        # 4. 基于相似度进行实体链接
        entity_links = self._link_entities(query_embedding)
        
        # 5. 基于相似度进行关系链接
        relationship_links = self._link_relationships(query_embedding)
        
        return {
            'original_query': query,
            'cleaned_text': cleaned_text,
            'tokens': tokens,
            'ac_matches': matches,
            'query_embedding': query_embedding,
            'entity_links': entity_links,
            'relationship_links': relationship_links
        }
    
    def _link_entities(self, query_embedding, top_k=3):
        """基于相似度进行实体链接"""
        if self.entity_embeddings is None or len(self.ac_matcher.entities) == 0:
            return []
        
        indices, similarities = self.bert_encoder.find_most_similar(
            query_embedding, 
            self.entity_embeddings, 
            top_k=top_k
        )
        
        return [
            {
                'entity': self.ac_matcher.entities[idx],
                'similarity': float(sim)
            }
            for idx, sim in zip(indices, similarities)
        ]
    
    def _link_relationships(self, query_embedding, top_k=3):
        """基于相似度进行关系链接"""
        if self.relationship_embeddings is None or len(self.ac_matcher.relationships) == 0:
            return []
        
        indices, similarities = self.bert_encoder.find_most_similar(
            query_embedding, 
            self.relationship_embeddings, 
            top_k=top_k
        )
        
        return [
            {
                'relationship': self.ac_matcher.relationships[idx],
                'similarity': float(sim)
            }
            for idx, sim in zip(indices, similarities)
        ]
    
    def get_best_matches(self, query, top_k=5):
        """获取最佳匹配的实体和关系组合"""
        preprocessed = self.preprocess_query(query)
        
        # 组合实体和关系
        combinations = []
        for entity in preprocessed['entity_links']:
            for rel in preprocessed['relationship_links']:
                # 计算组合分数
                score = (entity['similarity'] + rel['similarity']) / 2
                combinations.append({
                    'entity': entity['entity'],
                    'relationship': rel['relationship'],
                    'score': score,
                    'entity_similarity': entity['similarity'],
                    'relationship_similarity': rel['similarity']
                })
        
        # 按分数排序，返回top_k个最佳组合
        combinations.sort(key=lambda x: x['score'], reverse=True)
        return combinations[:top_k]

# 示例用法
if __name__ == "__main__":
    # 示例实体和关系
    sample_entities = ['苹果', '微软', '谷歌', '特斯拉', '亚马逊', '阿里巴巴', '腾讯']
    sample_relationships = ['收购', '合作', '投资', '研发', '推出', '竞争', '提供']
    
    # 初始化预处理器
    preprocessor = QueryPreprocessor(sample_entities, sample_relationships)
    
    # 测试查询
    query = "苹果公司最近收购了哪些公司？"
    result = preprocessor.preprocess_query(query)
    
    print("===== 查询预处理结果 =====")
    print(f"原始查询: {result['original_query']}")
    print(f"清理后的文本: {result['cleaned_text']}")
    print(f"分词结果: {result['tokens']}")
    
    print("\nAC自动机匹配结果:")
    print(f"匹配到的实体: {[e['text'] for e in result['ac_matches']['entities']]}")
    print(f"匹配到的关系: {[r['text'] for r in result['ac_matches']['relationships']]}")
    
    print("\n实体链接结果:")
    for entity in result['entity_links']:
        print(f"  - {entity['entity']}: 相似度 {entity['similarity']:.4f}")
    
    print("\n关系链接结果:")
    for rel in result['relationship_links']:
        print(f"  - {rel['relationship']}: 相似度 {rel['similarity']:.4f}")
    
    print("\n最佳匹配组合:")
    best_matches = preprocessor.get_best_matches(query)
    for i, match in enumerate(best_matches, 1):
        print(f"  {i}. 实体: {match['entity']}, 关系: {match['relationship']}, 分数: {match['score']:.4f}")