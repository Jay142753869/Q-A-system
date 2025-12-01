from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # 直接返回测试HTML内容，避免依赖其他模块
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        .confidence-bar {
            width: 100%;
            height: 8px;
            background-color: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .confidence-fill {
            height: 100%;
            transition: width 1s ease;
        }
        
        .high-confidence {
            background-color: #28a745;
        }
        </style>
    </head>
    <body>
        <h1>测试CSS语法</h1>
        <div class="confidence-bar">
            <div class="confidence-fill high-confidence" style="width: 85%;"></div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)
