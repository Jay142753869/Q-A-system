# 知识推理问答系统部署与维护指南

## 1. 系统环境要求

### 1.1 硬件要求
- **CPU**: 4核或更高
- **内存**: 8GB或更高
- **硬盘**: 100GB可用空间
- **网络**: 稳定的网络连接

### 1.2 软件要求
- **操作系统**: 
  - Linux (推荐Ubuntu 20.04 LTS或CentOS 7)
  - Windows 10/11
  - macOS
- **Python**: 3.8, 3.9, 3.10或3.11
- **Neo4j**: 4.4或更高版本
- **Redis** (可选): 用于缓存

## 2. 安装指南

### 2.1 克隆项目代码

```bash
git clone https://your-repository-url/q-and-a-system.git
cd q-and-a-system
```

### 2.2 创建虚拟环境

#### Linux/macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows
```cmd
python -m venv venv
venv\Scripts\activate
```

### 2.3 安装依赖

```bash
# 升级pip
pip install --upgrade pip

# 安装基础依赖
pip install -r requirements.txt

# 安装pyahocorasick
pip install pyahocorasick

# 安装可选的开发依赖
pip install -r requirements-dev.txt
```

### 2.4 配置Neo4j数据库

#### 2.4.1 安装Neo4j

**使用Docker（推荐）：**
```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -v neo4j_data:/data -v neo4j_logs:/logs --env NEO4J_AUTH=neo4j/password neo4j:latest
```

**直接安装：**
- 从[Neo4j官网](https://neo4j.com/download/)下载并安装适合您操作系统的版本
- 启动Neo4j服务

#### 2.4.2 初始化数据库

1. 访问Neo4j浏览器: http://localhost:7474
2. 使用默认凭据登录 (用户名: neo4j, 密码: neo4j)
3. 修改默认密码
4. 导入示例数据（可选）:

```cypher
// 创建示例实体
CREATE (n1:Concept {name: '深度学习', description: '机器学习的一个分支'})
CREATE (n2:Concept {name: '神经网络', description: '模拟人脑神经元的计算模型'})
CREATE (n3:Concept {name: '机器学习', description: '人工智能的一个分支'})

// 创建关系
CREATE (n1)-[:IS_A]->(n3)
CREATE (n1)-[:USES]->(n2)
```

### 2.5 配置系统环境变量

创建`.env`文件在项目根目录下：

```dotenv
# 数据库连接信息
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Flask配置
FLASK_APP=web_interface/app.py
FLASK_ENV=development  # 生产环境使用 production
SECRET_KEY=your_secret_key_here

# 应用配置
APP_NAME=知识推理问答系统
DEBUG=True  # 生产环境使用 False

# 缓存配置（可选）
REDIS_URL=redis://localhost:6379/0
```

## 3. 开发环境部署

### 3.1 启动开发服务器

```bash
# 确保虚拟环境已激活
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 启动Flask开发服务器
flask run
```

默认情况下，服务将在 http://localhost:5000 启动。

### 3.2 运行测试

```bash
# 运行单元测试
python -m unittest discover tests/unit

# 运行集成测试
python -m unittest discover tests/integration

# 或使用pytest（如果已安装）
pytest
```

### 3.3 代码风格检查

```bash
# 使用flake8检查代码风格
flake8 .

# 使用black格式化代码
black .

# 使用isort排序导入
isort .
```

## 4. 生产环境部署

### 4.1 使用Gunicorn（推荐）

```bash
# 安装Gunicorn
pip install gunicorn

# 启动应用
# 假设有4个worker，绑定到0.0.0.0:8000
gunicorn -w 4 -b 0.0.0.0:8000 "web_interface.app:create_app()"
```

### 4.2 使用Docker部署

#### 4.2.1 创建Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 设置环境变量
ENV FLASK_ENV=production
ENV NEO4J_URI=bolt://neo4j:7687

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "web_interface.app:create_app()"]
```

#### 4.2.2 创建docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:5000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
      - SECRET_KEY=your_secret_key
    depends_on:
      - neo4j
    restart: always

  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    environment:
      - NEO4J_AUTH=neo4j/password
    restart: always

volumes:
  neo4j_data:
  neo4j_logs:
```

#### 4.2.3 启动Docker服务

```bash
docker-compose up -d
```

### 4.3 使用Nginx作为反向代理

#### 4.3.1 安装Nginx

```bash
# Ubuntu/Debian
apt-get update
apt-get install nginx

# CentOS/RHEL
yum install nginx
```

#### 4.3.2 配置Nginx

创建配置文件 `/etc/nginx/sites-available/qanda-system`：

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件处理（如果需要）
    location /static/ {
        alias /path/to/your/app/static/;
        expires 30d;
    }
}
```

启用配置：

```bash
ln -s /etc/nginx/sites-available/qanda-system /etc/nginx/sites-enabled/
nginx -t  # 测试配置
nginx -s reload  # 重新加载Nginx
```

## 5. 监控与维护

### 5.1 日志管理

#### 5.1.1 应用日志

应用日志默认存储在 `logs/` 目录下。配置日志级别：

```dotenv
# 在.env文件中设置
LOG_LEVEL=INFO  # 可选：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/app.log
```

#### 5.1.2 系统日志

监控系统日志：

```bash
# 查看系统日志
tail -f /var/log/syslog

# Docker日志
docker logs -f app_container_name
```

### 5.2 性能监控

#### 5.2.1 使用Prometheus和Grafana（推荐）

1. 安装Prometheus和Grafana
2. 在Flask应用中添加Prometheus指标：

```bash
pip install prometheus-flask-exporter
```

修改应用初始化代码：

```python
from prometheus_flask_exporter import PrometheusMetrics

# 在app初始化后添加
metrics = PrometheusMetrics(app)

# 添加自定义指标
metrics.info('app_info', '应用信息', version='1.0.0')
```

3. 配置Prometheus抓取应用指标
4. 在Grafana中创建监控面板

#### 5.2.2 基本性能检查

```bash
# 检查CPU和内存使用情况
top

# 或使用htop（需要安装）
htop

# 检查磁盘使用情况
df -h

# 检查网络连接
netstat -tuln
```

### 5.3 定期维护任务

#### 5.3.1 数据库维护

```cypher
// Neo4j数据库清理
CALL dbms.indexes()
CALL dbms.stats.retrieve('GRAPH COUNTS')
CALL dbms.functions()

// 数据库备份
CALL dbms.util.checkpoint()
```

#### 5.3.2 系统清理

```bash
# 清理Python缓存
find . -name "__pycache__" -type d -exec rm -rf {} \;

# 清理日志文件（保留最近30天）
find logs/ -name "*.log" -mtime +30 -delete
```

## 6. 常见问题排查

### 6.1 数据库连接问题

**症状：** 应用无法连接到Neo4j数据库

**排查步骤：**
1. 检查Neo4j服务是否运行
   ```bash
   # Docker部署
   docker ps | grep neo4j
   
   # 直接部署
   systemctl status neo4j
   ```

2. 验证数据库凭据是否正确
   - 检查`.env`文件中的数据库配置
   - 尝试使用Neo4j浏览器连接

3. 检查防火墙设置
   ```bash
   # 检查7687端口是否开放
   netstat -tuln | grep 7687
   ```

### 6.2 性能问题

**症状：** 系统响应缓慢

**排查步骤：**
1. 检查数据库查询性能
   - 在Neo4j浏览器中运行EXPLAIN分析查询
   - 为频繁查询添加索引

2. 检查应用日志中的慢请求
   - 查看日志中的执行时间
   - 识别性能瓶颈

3. 增加应用资源
   - 增加Gunicorn worker数量
   - 增加服务器内存

### 6.3 应用崩溃

**症状：** 应用服务停止运行

**排查步骤：**
1. 检查应用日志
   ```bash
   tail -n 200 logs/app.log
   ```

2. 检查依赖问题
   - 验证所有依赖是否正确安装
   - 检查Python版本兼容性

3. 检查资源使用情况
   - 检查内存使用是否过高
   - 检查磁盘空间是否充足

## 7. 安全加固

### 7.1 配置HTTPS

在Nginx中配置SSL证书：

```nginx
server {
    listen 443 ssl;
    server_name your_domain.com;

    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';

    # 其余配置与之前相同
    location / {
        proxy_pass http://127.0.0.1:8000;
        # ...
    }
}

# 重定向HTTP到HTTPS
server {
    listen 80;
    server_name your_domain.com;
    return 301 https://$host$request_uri;
}
```

### 7.2 密码策略

1. 使用强密码
2. 定期更新密码
3. 考虑使用密码管理工具

### 7.3 访问控制

1. 限制管理接口访问
2. 配置防火墙规则
3. 考虑使用VPN进行远程访问

## 8. 数据备份与恢复

### 8.1 数据库备份

**Neo4j备份：**

```bash
# 使用neo4j-admin备份（离线备份）
neo4j-admin dump --database=neo4j --to=/path/to/backup/neo4j-$(date +%Y%m%d).dump

# Docker环境下备份
docker exec -i neo4j_container_name neo4j-admin dump --database=neo4j > /path/to/backup/neo4j-$(date +%Y%m%d).dump
```

### 8.2 数据恢复

**Neo4j恢复：**

```bash
# 使用neo4j-admin恢复
neo4j-admin load --from=/path/to/backup/neo4j-20231201.dump --database=neo4j --force

# Docker环境下恢复
docker exec -i neo4j_container_name neo4j-admin load --from=/backup/neo4j-20231201.dump --database=neo4j --force
```

### 8.3 自动化备份脚本

创建备份脚本 `backup.sh`：

```bash
#!/bin/bash

# 备份目录
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 确保备份目录存在
mkdir -p "$BACKUP_DIR"

# 备份Neo4j数据库（Docker版本）
docker exec -i neo4j neo4j-admin dump --database=neo4j > "$BACKUP_DIR/neo4j_$DATE.dump"

# 备份应用配置
cp -r config "$BACKUP_DIR/config_$DATE"

# 备份日志（可选）
cp -r logs "$BACKUP_DIR/logs_$DATE"

# 清理7天前的备份
find "$BACKUP_DIR" -name "*.dump" -mtime +7 -delete
find "$BACKUP_DIR" -name "config_*" -type d -mtime +7 -exec rm -rf {} \;
find "$BACKUP_DIR" -name "logs_*" -type d -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $DATE"
```

设置定时任务：

```bash
# 编辑crontab
crontab -e

# 添加每天凌晨2点执行备份
0 2 * * * /path/to/backup.sh >> /path/to/backup.log 2>&1
```

## 9. 扩展系统

### 9.1 水平扩展

1. 增加应用服务器实例
2. 使用负载均衡器分发请求
3. 配置共享会话存储

### 9.2 垂直扩展

1. 增加服务器CPU和内存
2. 优化数据库配置
3. 调整JVM参数（对于Neo4j）

### 9.3 添加新功能模块

1. 在项目中创建新模块目录
2. 实现核心功能
3. 注册到主应用
4. 编写测试
5. 更新文档

## 10. 升级系统

### 10.1 版本升级流程

1. 备份当前系统
2. 拉取最新代码
3. 更新依赖
4. 执行数据库迁移（如果需要）
5. 重启应用服务
6. 验证系统功能

### 10.2 数据库升级

```bash
# Neo4j升级前备份
neo4j-admin dump --database=neo4j --to=/path/to/backup/before_upgrade.dump

# 停止Neo4j服务
systemctl stop neo4j

# 更新Neo4j
# ...

# 启动Neo4j服务
systemctl start neo4j

# 验证升级
neo4j-admin report
```

## 11. 常见操作命令

### 11.1 服务管理

```bash
# 启动服务
systemctl start qanda-system

# 停止服务
systemctl stop qanda-system

# 重启服务
systemctl restart qanda-system

# 查看服务状态
systemctl status qanda-system
```

### 11.2 Docker操作

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 11.3 数据库操作

```bash
# 连接到Neo4j（使用cypher-shell）
docker exec -it neo4j_container_name cypher-shell -u neo4j -p your_password

# 列出所有节点
MATCH (n) RETURN n LIMIT 25;

# 列出所有关系
MATCH ()-[r]->() RETURN r LIMIT 25;
```

## 12. 故障恢复

### 12.1 应用故障

1. 检查应用日志
2. 重启应用服务
3. 必要时回滚到上一个稳定版本

### 12.2 数据库故障

1. 检查数据库日志
2. 重启数据库服务
3. 从备份恢复（如果必要）

### 12.3 服务器故障

1. 故障转移到备用服务器
2. 恢复应用和数据库
3. 验证系统功能

## 13. 文档与培训

1. 定期更新技术文档
2. 为团队成员提供系统培训
3. 建立知识库记录常见问题和解决方案