import jieba
import re

class TextProcessor:
    def __init__(self):
        # 初始化jieba分词器
        jieba.initialize()
        # 定义常用停用词
        self.stopwords = set([
            '的', '了', '和', '是', '在', '有', '我', '他', '她', '它',
            '这', '那', '你', '们', '就', '都', '而', '及', '与', '或',
            '一个', '我们', '你们', '他们', '她们', '它们', '这个', '那个'
        ])
    
    def clean_text(self, text):
        """清理文本，去除特殊字符和多余空格"""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除特殊字符，保留中文、英文、数字
        text = re.sub(r'[^一-龥a-zA-Z0-9]', ' ', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def tokenize(self, text):
        """中文分词"""
        # 先清理文本
        text = self.clean_text(text)
        # 使用jieba进行分词
        tokens = list(jieba.cut(text))
        # 过滤停用词
        tokens = [token for token in tokens if token not in self.stopwords and token.strip()]
        return tokens
    
    def add_user_dict(self, words):
        """添加用户自定义词典"""
        for word in words:
            jieba.add_word(word)
    
    def extract_keywords(self, text, top_k=5):
        """提取关键词"""
        # 简单的词频统计方法
        from collections import Counter
        tokens = self.tokenize(text)
        word_counts = Counter(tokens)
        return [word for word, _ in word_counts.most_common(top_k)]

# 测试代码
if __name__ == "__main__":
    processor = TextProcessor()
    text = "这是一个测试文本，用于测试分词功能。"
    print(f"原始文本: {text}")
    print(f"清理后的文本: {processor.clean_text(text)}")
    print(f"分词结果: {processor.tokenize(text)}")
    print(f"关键词: {processor.extract_keywords(text)}")