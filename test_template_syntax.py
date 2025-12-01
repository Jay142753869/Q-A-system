from flask import Flask, render_template_string

# 创建Flask应用
app = Flask(__name__)

# 测试模板字符串
template_string = '''
{% set result = {"confidence": 0.85} %}
{% set confidence_class = "high-confidence" if result.confidence >= 0.7 else "medium-confidence" if result.confidence >= 0.4 else "low-confidence" %}
<div class="confidence-fill {{ confidence_class }}" style="width: {{ (result.confidence * 100)|round(0) }}%"></div>
'''

# 测试渲染
try:
    with app.app_context():
        # 尝试编译模板
        template = app.jinja_env.from_string(template_string)
        rendered = template.render()
        print("模板编译成功！")
        print(f"渲染结果: {rendered}")
        print("第89行的模板语法是正确的。")
except Exception as e:
    print(f"编译错误: {e}")
    import traceback
    traceback.print_exc()
