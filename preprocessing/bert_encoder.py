import torch
from transformers import BertModel, BertTokenizer
import numpy as np

class BertEncoder:
    def __init__(self, model_name='bert-base-chinese'):
        """初始化BERT编码器"""
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name)
        # 设置为评估模式
        self.model.eval()
        # 检查是否有GPU可用
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
    
    def get_word_embedding(self, word):
        """获取单个词的嵌入向量"""
        # 编码词语
        inputs = self.tokenizer(word, return_tensors='pt', padding=True, truncation=True)
        # 将输入移至相应设备
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # 不计算梯度
        with torch.no_grad():
            outputs = self.model(**inputs)
            # 获取[CLS]标记的输出作为句子表示
            cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
        
        return cls_embedding
    
    def get_sentence_embedding(self, sentence):
        """获取句子的嵌入向量"""
        return self.get_word_embedding(sentence)
    
    def get_batch_embeddings(self, texts, batch_size=32):
        """批量获取文本的嵌入向量"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            # 批量编码
            inputs = self.tokenizer(batch_texts, return_tensors='pt', padding=True, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
    
    def compute_similarity(self, embedding1, embedding2):
        """计算两个嵌入向量的余弦相似度"""
        from sklearn.metrics.pairwise import cosine_similarity
        # 确保输入是二维数组
        if len(embedding1.shape) == 1:
            embedding1 = embedding1.reshape(1, -1)
        if len(embedding2.shape) == 1:
            embedding2 = embedding2.reshape(1, -1)
        
        return cosine_similarity(embedding1, embedding2)[0, 0]
    
    def find_most_similar(self, query_embedding, candidate_embeddings, top_k=5):
        """找到与查询嵌入最相似的候选嵌入"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
        # 获取top_k个最相似的索引
        top_indices = np.argsort(similarities)[::-1][:top_k]
        top_similarities = similarities[top_indices]
        
        return top_indices, top_similarities

# 测试代码
if __name__ == "__main__":
    encoder = BertEncoder()
    
    # 测试单个词嵌入
    word = "苹果"
    embedding = encoder.get_word_embedding(word)
    print(f"词语 '{word}' 的嵌入向量维度: {embedding.shape}")
    
    # 测试句子嵌入
    sentence = "苹果公司发布了新产品"
    sentence_embedding = encoder.get_sentence_embedding(sentence)
    print(f"句子的嵌入向量维度: {sentence_embedding.shape}")
    
    # 测试相似度计算
    word1 = "苹果"
    word2 = "公司"
    word3 = "香蕉"
    
    emb1 = encoder.get_word_embedding(word1)
    emb2 = encoder.get_word_embedding(word2)
    emb3 = encoder.get_word_embedding(word3)
    
    sim12 = encoder.compute_similarity(emb1, emb2)
    sim13 = encoder.compute_similarity(emb1, emb3)
    
    print(f"'{word1}' 和 '{word2}' 的相似度: {sim12:.4f}")
    print(f"'{word1}' 和 '{word3}' 的相似度: {sim13:.4f}")
    
    # 测试批量处理
    texts = ["苹果", "香蕉", "橙子", "葡萄", "西瓜"]
    batch_embeddings = encoder.get_batch_embeddings(texts)
    print(f"批量嵌入的形状: {batch_embeddings.shape}")
    
    # 测试最相似查询
    query = "苹果"
    query_emb = encoder.get_word_embedding(query)
    indices, similarities = encoder.find_most_similar(query_emb, batch_embeddings)
    
    print(f"与 '{query}' 最相似的词语:")
    for idx, sim in zip(indices, similarities):
        print(f"  - {texts[idx]}: {sim:.4f}")