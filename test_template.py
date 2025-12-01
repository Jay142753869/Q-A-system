from flask import Flask, render_template_string
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'web_interface'))

try:
    # 读取模板文件
    with open('web_interface/templates/interpolation_result.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # 创建Flask应用
    app = Flask(__name__)
    
    # 测试渲染模板
    with app.app_context():
        # 创建一个模拟的result对象
        class MockResult:
            def __init__(self):
                self.confidence = 0.85
                self.reason = "测试理由"
        
        # 尝试编译模板（不需要实际渲染）
        print("尝试编译模板...")
        template = app.jinja_env.from_string(template_content)
        print("模板编译成功！")
        
        # 如果需要，可以尝试渲染
        # result = MockResult()
        # rendered = template.render(result=result)
        # print("模板渲染成功！")
        
except Exception as e:
    print(f"编译错误: {e}")
    import traceback
    traceback.print_exc()
