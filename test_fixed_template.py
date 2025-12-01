from flask import Flask

# 创建Flask应用
app = Flask(__name__)

# 读取模板文件
with open('web_interface/templates/interpolation_result.html', 'r', encoding='utf-8') as f:
    template_content = f.read()

try:
    with app.app_context():
        # 尝试编译模板
        template = app.jinja_env.from_string(template_content)
        print("✅ 模板编译成功！")
        print("CSS语法错误已修复。")
except Exception as e:
    print(f"❌ 编译错误: {e}")
    import traceback
    traceback.print_exc()
