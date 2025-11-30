import re

# 尝试导入pyahocorasick，如果不可用则使用简单的替代实现
try:
    import pyahocorasick as ahocorasick
    USE_AHOCORASICK = True
except ImportError:
    print("Warning: pyahocorasick module not found, using simple regex implementation")
    USE_AHOCORASICK = False

class ACMatcher:
    def __init__(self):
        if USE_AHOCORASICK:
            # 初始化AC自动机
            self.automaton = ahocorasick.Automaton()
        self.is_built = False
        self.entities = []
        self.relationships = []
    
    def add_entities(self, entities):
        """添加实体到AC自动机"""
        if USE_AHOCORASICK:
            for i, entity in enumerate(entities):
                self.automaton.add_word(entity, (i, entity))
        self.entities.extend(entities)
        self.is_built = False
    
    def add_relationships(self, relationships):
        """添加关系到AC自动机"""
        if USE_AHOCORASICK:
            for i, rel in enumerate(relationships):
                self.automaton.add_word(rel, (i + len(self.entities), rel))
        self.relationships.extend(relationships)
        self.is_built = False
    
    def build(self):
        """构建AC自动机"""
        if USE_AHOCORASICK and not self.is_built:
            self.automaton.make_automaton()
            self.is_built = True
    
    def match(self, text):
        """在文本中匹配实体和关系"""
        if USE_AHOCORASICK:
            if not self.is_built:
                self.build()
            
            matches = []
            for end_idx, (idx, matched_str) in self.automaton.iter(text):
                start_idx = end_idx - len(matched_str) + 1
                # 判断是实体还是关系
                if idx < len(self.entities):
                    match_type = 'entity'
                else:
                    match_type = 'relationship'
                matches.append({
                    'text': matched_str,
                    'type': match_type,
                    'start': start_idx,
                    'end': end_idx
                })
        else:
            # 简单的正则表达式实现
            matches = []
            # 匹配实体
            for i, entity in enumerate(self.entities):
                pattern = re.escape(entity)
                for match in re.finditer(pattern, text):
                    matches.append({
                        'text': entity,
                        'type': 'entity',
                        'start': match.start(),
                        'end': match.end() - 1  # 保持与AC自动机相同的索引格式
                    })
            # 匹配关系
            for i, rel in enumerate(self.relationships):
                pattern = re.escape(rel)
                for match in re.finditer(pattern, text):
                    matches.append({
                        'text': rel,
                        'type': 'relationship',
                        'start': match.start(),
                        'end': match.end() - 1  # 保持与AC自动机相同的索引格式
                    })
        
        # 合并重叠的匹配，选择最长的匹配
        matches = sorted(matches, key=lambda x: (x['start'], -len(x['text'])))
        merged_matches = []
        last_end = -1
        
        for match in matches:
            if match['start'] > last_end:
                merged_matches.append(match)
                last_end = match['end']
        
        # 按位置排序
        merged_matches = sorted(merged_matches, key=lambda x: x['start'])
        return merged_matches
    
    def extract_entities_and_relationships(self, text):
        """提取文本中的实体和关系"""
        matches = self.match(text)
        entities = [m for m in matches if m['type'] == 'entity']
        relationships = [m for m in matches if m['type'] == 'relationship']
        
        return {
            'entities': entities,
            'relationships': relationships,
            'all_matches': matches
        }

# 测试代码
if __name__ == "__main__":
    matcher = ACMatcher()
    
    # 添加一些测试实体和关系
    entities = ['苹果', '微软', '谷歌', '特斯拉', '亚马逊']
    relationships = ['收购', '合作', '投资', '研发', '推出']
    
    matcher.add_entities(entities)
    matcher.add_relationships(relationships)
    matcher.build()
    
    text = "苹果公司收购了一家小公司，同时与微软展开合作，谷歌和特斯拉也在研发新的技术。"
    result = matcher.extract_entities_and_relationships(text)
    
    print("匹配到的实体:")
    for entity in result['entities']:
        print(f"  - {entity['text']} (位置: {entity['start']}-{entity['end']})")
    
    print("匹配到的关系:")
    for rel in result['relationships']:
        print(f"  - {rel['text']} (位置: {rel['start']}-{rel['end']})")