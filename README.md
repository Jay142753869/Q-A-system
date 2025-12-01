# 知识推理问答系统

## 项目概述

本项目是一个基于知识图谱的智能问答系统，支持内推式问答和外推式预测功能。系统能够理解用户的自然语言问题，从知识图谱中检索相关信息，并生成准确的回答。同时，还能基于已有知识进行趋势预测和关系分析。

### 核心功能
- **内推式问答**：根据已有知识图谱回答用户问题
- **外推式预测**：基于现有数据预测行业趋势和实体关系
- **知识图谱管理**：构建和维护领域知识图谱
- **自然语言处理**：实体识别、关系提取、语义理解
- **可视化界面**：交互式查询和结果展示

## 系统架构

系统采用模块化设计，主要包含以下核心模块：

### 1. 预处理模块 (preprocessing)
负责对用户输入的自然语言文本进行处理，包括分词、实体识别、关系提取和向量编码。
- **文本处理器**：使用jieba进行中文分词
- **AC自动机匹配器**：用于实体和关系的高效匹配
- **BERT编码器**：生成文本的语义向量表示

### 2. 知识图谱模块 (knowledge_graph)
管理知识图谱的构建、存储和查询，支持节点和关系的增删改查操作。
- **图管理器**：与Neo4j数据库交互
- **数据加载器**：导入和初始化知识图谱数据

### 3. 问答引擎模块 (models)
包含内推模型和外推模型，负责回答用户问题和进行趋势预测。
- **内推模型**：在已有知识中查找答案
- **外推模型**：基于现有知识进行预测
- **趋势分析器**：分析行业发展趋势

### 4. Web界面模块 (web_interface)
提供用户友好的交互界面，支持问题输入、结果展示和数据可视化。
- **Flask应用**：处理HTTP请求和响应
- **模板系统**：渲染HTML页面
- **静态资源**：CSS、JavaScript和图片等

### 5. 测试模块 (tests)
包含单元测试和集成测试，确保系统各组件正常工作。

## 技术栈

- **编程语言**：Python 3.8~3.11
- **Web框架**：Flask
- **自然语言处理**：jieba, Transformers (BERT)
- **知识图谱**：Neo4j
- **机器学习**：PyTorch, scikit-learn, NumPy
- **字符串匹配**：pyahocorasick (可选，有回退方案)
- **数据处理**：Pandas
- **可视化**：Chart.js

## 安装指南

### 1. 克隆项目

```bash
git clone <项目仓库地址>
cd Q and A system
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件，配置以下环境变量：

```
# Neo4j数据库连接信息
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Flask配置
FLASK_ENV=development
FLASK_APP=web_interface/app.py
```

### 4. 启动Neo4j数据库

确保Neo4j数据库服务已启动并可访问。

## 使用说明

### 启动Web服务

```bash
# 进入项目根目录
cd Q and A system

# 启动Flask应用
flask run
```

访问 `http://localhost:5000` 即可使用系统。

### API接口

#### 内推问答接口
- **URL**: `/api/interpolate`
- **方法**: POST
- **参数**: `{"query": "问题文本"}`
- **返回**: 包含答案的JSON对象

#### 外推预测接口
- **URL**: `/api/extrapolate`
- **方法**: POST
- **参数**: `{"query": "问题文本", "time_range": "预测时间范围"}`
- **返回**: 包含预测结果的JSON对象

#### 行业趋势预测接口
- **URL**: `/api/trends`
- **方法**: POST
- **参数**: `{"industry": "行业名称", "time_range": "预测时间范围"}`
- **返回**: 包含趋势预测的JSON对象

## 项目结构

```
Q and A system/
├── knowledge_graph/       # 知识图谱模块
│   ├── __init__.py
│   ├── graph_manager.py   # 图谱管理类
│   └── data_loader.py     # 数据加载工具
├── models/                # 模型模块
│   ├── __init__.py
│   ├── interpolation.py   # 内推模型
│   ├── extrapolation.py   # 外推模型
│   └── trend_analyzer.py  # 趋势分析模型
├── preprocessing/         # 预处理模块
│   ├── __init__.py
│   ├── text_processor.py  # 文本处理
│   ├── ac_matcher.py      # AC自动机匹配器
│   ├── bert_encoder.py    # BERT编码器
│   └── utils/             # 工具函数
├── web_interface/         # Web界面模块
│   ├── __init__.py
│   ├── app.py             # Flask应用入口
│   ├── static/            # 静态资源
│   └── templates/         # HTML模板
├── tests/                 # 测试模块
│   ├── __init__.py
│   ├── integration_test.py  # 集成测试
│   └── reports/           # 测试报告
├── requirements.txt       # 依赖列表
└── README.md              # 项目文档
```

## 测试

### 运行集成测试

```bash
python tests/integration_test.py
```

测试报告将生成在 `tests/reports/` 目录下。

## 注意事项

1. 系统依赖Neo4j数据库，请确保数据库服务正常运行
2. BERT模型会在首次使用时自动下载，可能需要一些时间
3. 如果pyahocorasick模块不可用，系统会自动使用基于正则表达式的替代方案
4. 对于大规模知识图谱，建议优化Neo4j数据库配置以提高性能

## 功能特点

- 支持中文自然语言输入和理解
- 使用AC自动机或正则表达式进行高效实体和关系匹配
- 基于BERT模型获取语义嵌入，提高语义理解准确性
- 支持知识图谱内推和外推两种推理模式
- 直观的可视化界面，包含结果图表和趋势分析
- 模块化设计，便于扩展和维护

## 未来改进方向

1. 增强实体识别和关系提取的准确性
2. 支持多模态数据输入和输出
3. 实现分布式部署以提高系统扩展性
4. 添加更多领域的知识图谱数据
5. 优化查询性能和用户体验
6. 实现实时知识更新和图谱维护
7. 增加多轮对话功能，支持上下文理解

## 许可证

[在此添加许可证信息]

## 联系方式

如有问题或建议，请联系项目维护者。