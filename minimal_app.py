from flask import Flask, render_template, request, jsonify
import os
import re
import jieba
from typing import Dict, List, Tuple, Optional

# 创建Flask应用实例并配置模板目录
app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_interface', 'templates')

# 简单的自然语言处理函数，用于从问题中提取实体和关系
def parse_natural_language_question(question: str) -> Dict[str, str]:
    """
    解析自然语言问题，提取实体和关系信息
    返回格式: {"type": "question_type", "entity1": "实体1", "relationship": "关系", "entity2": "实体2"}
    """
    result = {"type": "unknown", "entity1": "", "relationship": "", "entity2": ""}
    question = question.lower()
    
    # 使用jieba进行中文分词
    seg_list = list(jieba.cut(question))
    
    # 模式1: 询问两个实体之间的关系 (A和B之间有什么关系?)
    relation_pattern = r'(.*?)和(.*?)之间有什么关系'
    relation_match = re.search(relation_pattern, question)
    if relation_match:
        result["type"] = "entity_entity"
        result["entity1"] = relation_match.group(1).strip()
        result["entity2"] = relation_match.group(2).strip()
        return result
    
    # 模式2: 已知实体和关系，询问另一个实体 (A的X有哪些? / A的X是什么?)
    entity_rel_pattern = r'(.*?)的(.*?)[有是](哪些|什么)'
    entity_rel_match = re.search(entity_rel_pattern, question)
    if entity_rel_match:
        result["type"] = "entity_relationship"
        result["entity1"] = entity_rel_match.group(1).strip()
        result["relationship"] = entity_rel_match.group(2).strip()
        return result
    
    # 模式3: 已知关系和目标实体，询问源实体 (谁的X是B? / 什么的X是B?)
    rel_entity_pattern = r'(谁|什么)的(.*?)是(.*?)'
    rel_entity_match = re.search(rel_entity_pattern, question)
    if rel_entity_match:
        result["type"] = "relationship_entity"
        result["relationship"] = rel_entity_match.group(2).strip()
        result["entity2"] = rel_entity_match.group(3).strip()
        return result
    
    # 模式4: 外推问题 (预测A的未来发展 / A未来会如何?)
    extrapolate_pattern = r'(预测|未来|将会|可能|预计|展望).*?([^的，。,.;； ]+?)'
    extrapolate_match = re.search(extrapolate_pattern, question)
    if extrapolate_match:
        entity_candidate = extrapolate_match.group(2).strip()
        # 如果匹配到的内容太短，尝试整个问题中找可能的实体
        if len(entity_candidate) < 2:
            # 使用jieba分词后的结果来寻找可能的实体
            possible_entities = [word for word in seg_list if len(word) > 2 and word not in ['什么', '哪里', '哪个', '如何', '怎样']]
            if possible_entities:
                entity_candidate = possible_entities[0]
        
        result["type"] = "extrapolation"
        result["entity1"] = entity_candidate
        return result
    
    # 模式5: 谁+动词+实体 (谁发明了电话?)
    who_verb_entity_pattern = r'(谁|什么)(发明|创立|创建|发现|开发|制作|生产|设计|撰写)(了|的)?(.*?)'
    who_verb_entity_match = re.search(who_verb_entity_pattern, question)
    if who_verb_entity_match:
        result["type"] = "relationship_entity"
        result["relationship"] = who_verb_entity_match.group(2).strip()
        result["entity2"] = who_verb_entity_match.group(4).strip()
        return result
    
    # 模式6: 实体+动词+什么/谁 (苹果公司收购了什么?)
    entity_verb_what_pattern = r'(.*?)(收购|投资|合作|研发|生产)(了|的)?(什么|谁)'  
    entity_verb_what_match = re.search(entity_verb_what_pattern, question)
    if entity_verb_what_match:
        result["type"] = "entity_relationship"
        result["entity1"] = entity_verb_what_match.group(1).strip()
        result["relationship"] = entity_verb_what_match.group(2).strip()
        return result
    
    # 默认模式：使用jieba分词找出可能的实体
    # 策略：找出分词结果中长度大于2的连续词作为实体
    possible_entities = []
    temp_entity = ""
    
    for word in seg_list:
        # 跳过停用词和标点符号
        if word in ['的', '了', '和', '与', '或', '在', '是', '有', '吗', '呢', '啊', '吧', ',', '，', '.', '。', '?', '？', '!', '！', '：', ':']:
            if temp_entity and len(temp_entity) > 2:
                possible_entities.append(temp_entity)
                temp_entity = ""
            continue
        
        temp_entity += word
        if len(temp_entity) > 2:
            possible_entities.append(temp_entity)
    
    if possible_entities:
        # 选择最长的可能实体
        possible_entities.sort(key=len, reverse=True)
        result["type"] = "extrapolation"
        result["entity1"] = possible_entities[0]
    
    return result

# 模拟知识图谱查询结果的函数
def mock_query_knowledge_graph(query_type: str, **kwargs) -> List[Dict[str, str]]:
    """
    模拟知识图谱查询结果
    在实际应用中，这里应该调用真实的知识图谱查询接口
    """
    if query_type == "entity_entity":
        # 模拟两个实体之间的关系预测
        return [
            {"relationship": "生产", "confidence": "0.95", "explanation": f"{kwargs.get('entity1')}是一家知名企业，主要业务包括{kwargs.get('entity2')}的设计和制造。"},
            {"relationship": "拥有", "confidence": "0.82", "explanation": f"数据显示{kwargs.get('entity1')}对{kwargs.get('entity2')}品牌拥有完全的所有权。"},
            {"relationship": "研发", "confidence": "0.78", "explanation": f"{kwargs.get('entity1')}投入大量资源进行{kwargs.get('entity2')}相关技术的研发。"}
        ]
    elif query_type == "entity_relationship":
        # 模拟已知实体和关系，预测另一个实体
        return [
            {"entity": "iPhone", "confidence": "0.92", "explanation": f"{kwargs.get('entity1')}最著名的产品之一就是{kwargs.get('relationship')}iPhone系列智能手机。"},
            {"entity": "iPad", "confidence": "0.88", "explanation": f"{kwargs.get('entity1')}同时也{kwargs.get('relationship')}平板电脑产品iPad。"},
            {"entity": "MacBook", "confidence": "0.85", "explanation": f"在个人电脑领域，{kwargs.get('entity1')}也{kwargs.get('relationship')}MacBook系列笔记本电脑。"}
        ]
    elif query_type == "relationship_entity":
        # 模拟已知关系和目标实体，预测源实体
        return [
            {"entity": "苹果公司", "confidence": "0.96", "explanation": f"{kwargs.get('entity2')}是由{kwargs.get('relationship')}的知名科技产品。"},
            {"entity": "富士康", "confidence": "0.75", "explanation": f"{kwargs.get('relationship')}是{kwargs.get('entity2')}的主要制造商之一。"},
            {"entity": "iOS生态系统", "confidence": "0.70", "explanation": f"{kwargs.get('relationship')}在{kwargs.get('entity2')}的软件生态系统中扮演重要角色。"}
        ]
    elif query_type == "extrapolation":
        # 模拟外推预测结果
        return [
            {"entity": "人工智能公司", "relationship": "收购", "confidence": "0.88", "explanation": f"根据{kwargs.get('entity1')}的历史收购模式和行业趋势，未来很可能收购一家专注于AI技术的创新企业。"},
            {"entity": "电动汽车制造商", "relationship": "合作", "confidence": "0.82", "explanation": f"考虑到市场发展方向，{kwargs.get('entity1')}有较大可能与电动汽车领域的领先企业建立战略合作。"},
            {"entity": "元宇宙平台", "relationship": "投资", "confidence": "0.76", "explanation": f"随着元宇宙概念的兴起，{kwargs.get('entity1')}预计将在该领域进行战略投资。"}
        ]
    
    # 默认返回
    return [{"text": "抱歉，我无法理解您的问题。请尝试使用更清晰的表达方式。", "confidence": "0.0", "explanation": "无法解析问题类型或缺少必要参数。"}]

@app.route('/')
def index():
    # 尝试渲染web_interface/templates中的index.html模板
    try:
        return render_template('index.html')
    except Exception as e:
        # 如果模板渲染失败，返回错误信息和基本的CSS测试页面
        return f'''
        <h1>模板加载失败: {str(e)}</h1>
        <div style='width: 100%; height: 8px; background-color: #e9ecef; border-radius: 4px; overflow: hidden;'>
            <div style='height: 100%; width: 85%; background-color: #28a745; transition: width 1s ease;'></div>
        </div>
        '''

@app.route('/interpolation', methods=['GET', 'POST'])
def interpolation():
    # 添加插值页面路由，支持GET和POST方法
    if request.method == 'POST':
        # 处理表单提交的数据
        entity1 = request.form.get('entity1', '').strip()
        relationship = request.form.get('relationship', '').strip()
        entity2 = request.form.get('entity2', '').strip()
        top_k = int(request.form.get('top_k', 5))
        
        # 确定查询类型
        query_type = "unknown"
        if entity1 and entity2 and not relationship:
            query_type = "entity_entity"
        elif entity1 and relationship and not entity2:
            query_type = "entity_relationship"
        elif relationship and entity2 and not entity1:
            query_type = "relationship_entity"
        
        # 查询知识图谱（这里使用模拟数据）
        results = mock_query_knowledge_graph(query_type, entity1=entity1, relationship=relationship, entity2=entity2)
        
        # 返回结果页面
        try:
            return render_template('interpolation_result.html', 
                                query_type=query_type,
                                entity1=entity1,
                                relationship=relationship,
                                entity2=entity2,
                                results=results[:top_k])
        except Exception as e:
            # 如果结果页面渲染失败，返回简单的结果展示
            return f'''
            <h1>查询结果</h1>
            <p>查询参数: 实体1={entity1}, 关系={relationship}, 实体2={entity2}</p>
            <h2>预测结果:</h2>
            <ul>
            {''.join([f'<li>{str(result)}</li>' for result in results[:top_k]])}
            </ul>
            <a href="/interpolation">返回查询页面</a>
            '''
    
    # GET请求时渲染表单页面
    try:
        return render_template('interpolation.html')
    except Exception as e:
        return f'''<h1>插值页面模板加载失败: {str(e)}</h1>'''

@app.route('/extrapolation', methods=['GET', 'POST'])
def extrapolation():
    # 添加外推页面路由，支持GET和POST方法
    if request.method == 'POST':
        # 处理表单提交的数据
        entity = request.form.get('entity', '').strip()
        future_years = int(request.form.get('future_years', 5))
        top_k = int(request.form.get('top_k', 5))
        
        # 查询知识图谱（这里使用模拟数据）
        results = mock_query_knowledge_graph("extrapolation", entity1=entity, future_years=future_years)
        
        # 返回结果页面
        try:
            return render_template('extrapolation_result.html', 
                                entity=entity,
                                future_years=future_years,
                                results=results[:top_k])
        except Exception as e:
            # 如果结果页面渲染失败，返回简单的结果展示
            return f'''
            <h1>预测结果</h1>
            <p>查询参数: 实体={entity}, 预测年数={future_years}</p>
            <h2>预测结果:</h2>
            <ul>
            {''.join([f'<li>{str(result)}</li>' for result in results[:top_k]])}
            </ul>
            <a href="/extrapolation">返回预测页面</a>
            '''
    
    # GET请求时渲染表单页面
    try:
        return render_template('extrapolation.html')
    except Exception as e:
        return f'''<h1>外推页面模板加载失败: {str(e)}</h1>'''

@app.route('/natural_language', methods=['GET', 'POST'])
def natural_language_qa():
    """
    自然语言问答路由
    允许用户输入完整的自然语言问题，系统自动解析并返回答案
    """
    if request.method == 'POST':
        # 获取用户输入的自然语言问题
        question = request.form.get('question', '').strip()
        top_k = int(request.form.get('top_k', 5))
        
        if not question:
            # 如果问题为空，显示错误信息
            try:
                return render_template('natural_language.html', error="请输入问题")
            except Exception:
                return "<h1>错误：请输入问题</h1><a href='/natural_language'>返回</a>"
        
        # 解析自然语言问题
        parsed_question = parse_natural_language_question(question)
        
        # 根据问题类型查询知识图谱
        query_type = parsed_question["type"]
        results = mock_query_knowledge_graph(
            query_type,
            entity1=parsed_question["entity1"],
            relationship=parsed_question["relationship"],
            entity2=parsed_question["entity2"]
        )
        
        # 返回结果页面
        try:
            return render_template('natural_language_result.html',
                                question=question,
                                parsed_question=parsed_question,
                                results=results[:top_k])
        except Exception as e:
            # 如果结果页面渲染失败，返回简单的结果展示
            return f'''
            <h1>问答结果</h1>
            <p>您的问题: {question}</p>
            <p>解析结果: {str(parsed_question)}</p>
            <h2>答案:</h2>
            <ul>
            {''.join([f'<li>{str(result)}</li>' for result in results[:top_k]])}
            </ul>
            <a href="/natural_language">返回问答页面</a>
            '''
    
    # GET请求时渲染表单页面
    try:
        return render_template('natural_language.html')
    except Exception:
        # 如果模板不存在，创建一个简单的自然语言问答页面
        return '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>自然语言问答</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
                h1, h2 { color: #333; }
                input[type="text"] { width: 100%; padding: 10px; margin-bottom: 10px; }
                button { padding: 10px 20px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background-color: #45a049; }
                .error { color: red; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>自然语言问答</h1>
                <form method="POST">
                    <label for="question">请输入您的问题：</label><br>
                    <input type="text" id="question" name="question" placeholder="例如：苹果公司和iPhone之间有什么关系？" style="width: 100%; height: 100px;"><br>
                    <label for="top_k">返回结果数量：</label>
                    <select id="top_k" name="top_k">
                        <option value="3">3</option>
                        <option value="5" selected>5</option>
                        <option value="10">10</option>
                    </select><br>
                    <button type="submit">提问</button>
                </form>
                <h3>示例问题：</h3>
                <ul>
                    <li>苹果公司和iPhone之间有什么关系？</li>
                    <li>微软的产品有哪些？</li>
                    <li>谁创立了特斯拉？</li>
                    <li>预测苹果公司未来的发展</li>
                </ul>
            </div>
        </body>
        </html>
        '''

if __name__ == '__main__':
    # 设置host为0.0.0.0使外部可访问，并启用调试模式
    app.run(host='0.0.0.0', port=5000, debug=True)
