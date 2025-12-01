// 这是从extrapolation_result.html中提取的JavaScript代码
// 用于独立验证JavaScript语法

// 将Jinja2模板变量替换为测试数据
const relationshipStatsLabels = ['类型1', '类型2', '类型3'];
const relationshipStatsData = [10, 20, 30];

// 模拟Chart对象
const Chart = function(ctx, config) {
    console.log('图表初始化成功！');
    console.log('图表配置:', config);
    return { chart: '模拟图表对象' };
};

// 模拟DOM环境
global.document = {
    getElementById: function(id) {
        if (id === 'relationshipChart') {
            return { 
                getContext: function() {
                    return { canvas: '模拟canvas上下文' };
                }
            };
        }
        return null;
    },
    querySelectorAll: function() {
        return [];
    },
    addEventListener: function(event, callback) {
        console.log(`事件监听器添加成功: ${event}`);
        // 立即执行回调函数以测试代码
        callback();
        return true;
    }
};

// 为querySelectorAll结果添加forEach方法
Array.prototype.forEach = Array.prototype.forEach || function(callback) {
    for (let i = 0; i < this.length; i++) {
        callback(this[i], i, this);
    }
};

try {
    // 这是修复后的JavaScript代码
    document.addEventListener('DOMContentLoaded', function() {
        // 关系类型分布图表
        // {% if relationship_stats %} 已在服务端处理
        const ctx = document.getElementById('relationshipChart');
        if (ctx) {
            const chartCtx = ctx.getContext('2d');
            
            // 图表配置
            const chartConfig = {
                type: 'bar',
                data: {
                    labels: relationshipStatsLabels,
                    datasets: [{
                        label: '预测次数',
                        data: relationshipStatsData,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.6)',
                            'rgba(54, 162, 235, 0.6)',
                            'rgba(255, 206, 86, 0.6)',
                            'rgba(75, 192, 192, 0.6)',
                            'rgba(153, 102, 255, 0.6)',
                            'rgba(255, 159, 64, 0.6)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)',
                            'rgba(255, 159, 64, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            };
            
            // 初始化图表
            try {
                const relationshipChart = new Chart(chartCtx, chartConfig);
            } catch (error) {
                console.error('图表初始化失败:', error);
            }
        }
        // {% endif %} 已在服务端处理
        
        // 为预测卡片添加置信度相关样式
        const predictionCards = document.querySelectorAll('.prediction-card');
        predictionCards.forEach(function(card) {
            const confidenceData = card.dataset.confidence;
            if (confidenceData) {
                const confidence = parseFloat(confidenceData);
                let confidenceClass = 'confidence-low';
                
                if (confidence >= 0.7) {
                    confidenceClass = 'confidence-high';
                } else if (confidence >= 0.4) {
                    confidenceClass = 'confidence-medium';
                }
                
                card.classList.add(confidenceClass);
            }
        });
    });
    
    console.log('✅ JavaScript语法验证通过！代码可以正常解析。');
    
} catch (error) {
    console.error('❌ JavaScript语法验证失败:', error.message);
    console.error(error.stack);
}