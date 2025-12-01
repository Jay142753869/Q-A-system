from flask import Flask, render_template
import os

# 创建Flask应用实例并配置模板目录
app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_interface', 'templates')

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

@app.route('/interpolation')
def interpolation():
    # 添加插值页面路由
    try:
        return render_template('interpolation.html')
    except Exception as e:
        return f'''<h1>插值页面模板加载失败: {str(e)}</h1>'''

@app.route('/extrapolation')
def extrapolation():
    # 添加外推页面路由
    try:
        return render_template('extrapolation.html')
    except Exception as e:
        return f'''<h1>外推页面模板加载失败: {str(e)}</h1>'''

if __name__ == '__main__':
    # 设置host为0.0.0.0使外部可访问，并启用调试模式
    app.run(host='0.0.0.0', port=5000, debug=True)
