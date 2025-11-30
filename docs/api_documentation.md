# 知识推理问答系统API文档

## 1. 概述

本文档详细描述知识推理问答系统提供的所有API接口，包括接口URL、请求方法、请求参数、返回格式和示例。

## 2. 基础URL

所有API接口的基础URL为：`http://localhost:5000/api/v1`

## 3. 核心API接口

### 3.1 内推问答接口

#### 3.1.1 单轮问答

**接口描述**：接收用户问题，返回内推式回答

**请求URL**：`/qa/internal`

**请求方法**：POST

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| question | String | 是 | 用户问题文本 |
| top_k | Integer | 否 | 返回结果数量，默认5 |

**请求示例**：
```json
{
  "question": "什么是深度学习？",
  "top_k": 3
}
```

**返回格式**：
| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| code | Integer | 状态码，0表示成功，非0表示失败 |
| message | String | 状态描述 |
| data | Object | 返回数据 |
| data.answers | Array | 回答列表 |
| data.answers[].text | String | 回答文本 |
| data.answers[].confidence | Float | 置信度，0-1之间 |
| data.answers[].sources | Array | 引用的知识源列表 |
| data.extracted_entities | Array | 提取的实体列表 |
| data.extracted_relationships | Array | 提取的关系列表 |

**返回示例**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "answers": [
      {
        "text": "深度学习是机器学习的一个分支，它通过多层神经网络来模拟人脑的学习过程。",
        "confidence": 0.95,
        "sources": ["entity_1", "entity_2"]
      }
    ],
    "extracted_entities": ["深度学习", "机器学习", "神经网络"],
    "extracted_relationships": ["is_a"]
  }
}
```

#### 3.1.2 多轮对话

**接口描述**：支持上下文理解的多轮对话问答

**请求URL**：`/qa/conversation`

**请求方法**：POST

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| session_id | String | 是 | 会话ID，用于跟踪对话上下文 |
| question | String | 是 | 用户当前问题 |
| history | Array | 否 | 历史对话记录 |

**请求示例**：
```json
{
  "session_id": "session_123",
  "question": "它有哪些应用场景？",
  "history": [
    {"role": "user", "content": "什么是深度学习？"},
    {"role": "assistant", "content": "深度学习是机器学习的一个分支..."}
  ]
}
```

**返回格式**：
| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| code | Integer | 状态码 |
| message | String | 状态描述 |
| data | Object | 返回数据 |
| data.answer | String | 回答文本 |
| data.session_id | String | 会话ID |
| data.context_understood | Boolean | 是否理解上下文 |

### 3.2 外推预测接口

#### 3.2.1 行业趋势预测

**接口描述**：基于历史数据预测行业未来趋势

**请求URL**：`/predict/trend`

**请求方法**：POST

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| industry | String | 是 | 行业名称 |
| time_range | Integer | 否 | 预测时间范围（月），默认12 |
| factors | Array | 否 | 考虑的影响因素列表 |

**请求示例**：
```json
{
  "industry": "人工智能",
  "time_range": 24,
  "factors": ["政策支持", "技术突破", "市场需求"]
}
```

**返回格式**：
| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| code | Integer | 状态码 |
| message | String | 状态描述 |
| data | Object | 返回数据 |
| data.industry | String | 行业名称 |
| data.predictions | Array | 预测数据点列表 |
| data.predictions[].time | String | 时间点 |
| data.predictions[].value | Float | 预测值 |
| data.confidence_level | Float | 预测置信度 |
| data.key_drivers | Array | 关键驱动因素 |

#### 3.2.2 关系预测

**接口描述**：预测两个实体之间可能存在的关系

**请求URL**：`/predict/relationship`

**请求方法**：POST

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| entity1 | String | 是 | 第一个实体 |
| entity2 | String | 是 | 第二个实体 |
| top_n | Integer | 否 | 返回预测的关系数量，默认3 |

**请求示例**：
```json
{
  "entity1": "人工智能",
  "entity2": "医疗健康",
  "top_n": 5
}
```

**返回格式**：
| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| code | Integer | 状态码 |
| message | String | 状态描述 |
| data | Object | 返回数据 |
| data.entity1 | String | 第一个实体 |
| data.entity2 | String | 第二个实体 |
| data.predicted_relationships | Array | 预测的关系列表 |
| data.predicted_relationships[].type | String | 关系类型 |
| data.predicted_relationships[].score | Float | 关系强度分数 |
| data.predicted_relationships[].explanation | String | 关系解释 |

### 3.3 知识图谱管理接口

#### 3.3.1 查询实体

**接口描述**：查询知识图谱中的实体信息

**请求URL**：`/kg/entity`

**请求方法**：GET

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| name | String | 是 | 实体名称 |
| detail_level | String | 否 | 详情级别：basic/full，默认basic |

**请求示例**：
```
GET /kg/entity?name=深度学习&detail_level=full
```

**返回格式**：
| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| code | Integer | 状态码 |
| message | String | 状态描述 |
| data | Object | 返回数据 |
| data.id | String | 实体ID |
| data.name | String | 实体名称 |
| data.type | String | 实体类型 |
| data.attributes | Object | 实体属性 |
| data.relationships | Array | 关联关系列表 |

#### 3.3.2 查询关系

**接口描述**：查询两个实体之间的关系

**请求URL**：`/kg/relationship`

**请求方法**：GET

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| source | String | 是 | 源实体名称 |
| target | String | 是 | 目标实体名称 |

**请求示例**：
```
GET /kg/relationship?source=深度学习&target=神经网络
```

**返回格式**：
| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| code | Integer | 状态码 |
| message | String | 状态描述 |
| data | Object | 返回数据 |
| data.source | String | 源实体 |
| data.target | String | 目标实体 |
| data.relationships | Array | 关系列表 |
| data.relationships[].type | String | 关系类型 |
| data.relationships[].properties | Object | 关系属性 |

#### 3.3.3 添加实体

**接口描述**：向知识图谱中添加新实体

**请求URL**：`/kg/entity`

**请求方法**：POST

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| name | String | 是 | 实体名称 |
| type | String | 是 | 实体类型 |
| attributes | Object | 否 | 实体属性 |

**请求示例**：
```json
{
  "name": "GPT-4",
  "type": "模型",
  "attributes": {
    "发布日期": "2023-03-14",
    "开发机构": "OpenAI",
    "参数规模": "万亿级"
  }
}
```

**返回格式**：
| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| code | Integer | 状态码 |
| message | String | 状态描述 |
| data | Object | 返回数据 |
| data.id | String | 新创建实体的ID |
| data.name | String | 实体名称 |
| data.status | String | 创建状态 |

#### 3.3.4 添加关系

**接口描述**：向知识图谱中添加实体间关系

**请求URL**：`/kg/relationship`

**请求方法**：POST

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| source | String | 是 | 源实体名称 |
| target | String | 是 | 目标实体名称 |
| type | String | 是 | 关系类型 |
| properties | Object | 否 | 关系属性 |

**请求示例**：
```json
{
  "source": "GPT-4",
  "target": "OpenAI",
  "type": "developed_by",
  "properties": {
    "时间": "2023",
    "重要性": "高"
  }
}
```

**返回格式**：
| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| code | Integer | 状态码 |
| message | String | 状态描述 |
| data | Object | 返回数据 |
| data.status | String | 创建状态 |
| data.relationship_id | String | 关系ID |

### 3.4 数据统计接口

#### 3.4.1 图谱统计

**接口描述**：获取知识图谱的统计信息

**请求URL**：`/kg/stats`

**请求方法**：GET

**返回格式**：
| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| code | Integer | 状态码 |
| message | String | 状态描述 |
| data | Object | 返回数据 |
| data.node_count | Integer | 节点数量 |
| data.relationship_count | Integer | 关系数量 |
| data.entity_types | Object | 各类型实体数量 |
| data.relationship_types | Object | 各类型关系数量 |
| data.last_update | String | 最后更新时间 |

#### 3.4.2 问答统计

**接口描述**：获取系统问答性能统计

**请求URL**：`/stats/qa`

**请求方法**：GET

**请求参数**：
| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| time_range | String | 否 | 时间范围：day/week/month/all，默认week |

**请求示例**：
```
GET /stats/qa?time_range=month
```

**返回格式**：
| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| code | Integer | 状态码 |
| message | String | 状态描述 |
| data | Object | 返回数据 |
| data.total_questions | Integer | 问题总数 |
| data.avg_response_time | Float | 平均响应时间（秒） |
| data.success_rate | Float | 成功率 |
| data.top_entities | Array | 最常查询的实体 |
| data.top_topics | Array | 热门话题 |

## 4. 错误码说明

| 错误码 | 描述 |
| :--- | :--- |
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权访问 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 501 | 功能未实现 |
| 503 | 服务暂时不可用 |

## 5. 使用示例

### 5.1 Python调用示例

```python
import requests
import json

# 内推问答调用示例
def ask_question(question):
    url = "http://localhost:5000/api/v1/qa/internal"
    headers = {"Content-Type": "application/json"}
    data = {"question": question, "top_k": 1}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        result = response.json()
        
        if result["code"] == 0:
            return result["data"]["answers"][0]["text"]
        else:
            return f"错误: {result['message']}"
    except Exception as e:
        return f"请求失败: {str(e)}"

# 行业趋势预测示例
def predict_trend(industry, time_range=12):
    url = "http://localhost:5000/api/v1/predict/trend"
    headers = {"Content-Type": "application/json"}
    data = {"industry": industry, "time_range": time_range}
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()
```

### 5.2 JavaScript调用示例

```javascript
// 内推问答调用示例
async function askQuestion(question) {
    try {
        const response = await fetch('http://localhost:5000/api/v1/qa/internal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                top_k: 1
            })
        });
        
        const result = await response.json();
        
        if (result.code === 0) {
            return result.data.answers[0].text;
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('Error asking question:', error);
        return null;
    }
}

// 查询实体信息示例
async function getEntityInfo(entityName) {
    try {
        const response = await fetch(
            `http://localhost:5000/api/v1/kg/entity?name=${encodeURIComponent(entityName)}&detail_level=full`
        );
        return await response.json();
    } catch (error) {
        console.error('Error fetching entity info:', error);
        return null;
    }
}
```

## 6. API使用注意事项

1. **请求频率限制**：默认每分钟最多60次请求，超出限制将返回429错误
2. **参数验证**：所有输入参数都会进行验证，格式错误会返回400错误
3. **编码规范**：所有文本数据使用UTF-8编码
4. **错误处理**：API调用失败时，请检查错误码和错误信息进行相应处理
5. **身份认证**：部分管理接口需要提供访问令牌

## 7. 版本控制

API版本通过URL路径中的`v1`标识，未来版本升级将保持向后兼容。