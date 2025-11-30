from .interpolation_model import InterpolationModel
from .extrapolation_model import ExtrapolationModel

class QAEngine:
    """
    问答引擎，整合内推和外推模型
    负责处理用户查询并返回相应的回答
    """
    def __init__(self, graph_manager):
        """初始化问答引擎"""
        self.graph_manager = graph_manager
        
        # 初始化内推模型
        self.interpolation_model = InterpolationModel(graph_manager)
        
        # 初始化外推模型
        self.extrapolation_model = ExtrapolationModel(graph_manager)
    
    def answer_interpolation_query(self, entity1, relationship=None, entity2=None, top_k=5):
        """
        处理内推查询：已知部分信息，补全缺失信息
        
        支持三种查询模式：
        1. 已知两个实体，预测它们之间的关系 (entity1, ?, entity2)
        2. 已知一个实体和关系，预测另一个实体 (entity1, relationship, ?)
        3. 已知关系和目标实体，预测源实体 (?, relationship, entity2)
        """
        results = []
        
        # 检查参数有效性
        if entity1 and entity2 and not relationship:
            # 预测两个实体之间的关系
            results = self.interpolation_model.predict_relationships_between_entities(
                entity1, entity2, top_k=top_k
            )
        elif entity1 and relationship and not entity2:
            # 预测实体关系的目标实体
            results = self.interpolation_model.predict_target_entities(
                entity1, relationship, top_k=top_k
            )
        elif not entity1 and relationship and entity2:
            # 预测关系的源实体
            results = self.interpolation_model.predict_source_entities(
                entity2, relationship, top_k=top_k
            )
        else:
            # 参数不完整，返回错误信息
            results.append({
                'error': '参数不完整，请提供足够的信息进行内推查询',
                'suggestion': '请提供以下组合之一：\n' \
                           '1. 两个实体（预测它们之间的关系）\n' \
                           '2. 一个实体和一种关系（预测另一个实体）\n' \
                           '3. 一种关系和一个目标实体（预测源实体）'
            })
        
        return results
    
    def answer_extrapolation_query(self, entity, future_years=5, top_k=5):
        """
        处理外推查询：预测未来可能发生的关系
        
        Args:
            entity: 要预测的实体
            future_years: 预测未来的年数
            top_k: 返回前k个预测结果
            
        Returns:
            预测的未来关系列表
        """
        results = []
        
        if not entity:
            results.append({
                'error': '参数不完整，请提供实体名称',
                'suggestion': '请提供一个实体名称以预测其未来可能的关系'
            })
        else:
            # 使用外推模型预测未来关系
            results = self.extrapolation_model.predict_future_relationships(
                entity, future_years=future_years, top_k=top_k
            )
        
        return results
    
    def predict_industry_trend(self, industry, future_years=5, top_k=5):
        """
        预测行业趋势
        
        Args:
            industry: 行业名称
            future_years: 预测未来的年数
            top_k: 返回前k个预测结果
            
        Returns:
            行业趋势预测列表
        """
        results = []
        
        if not industry:
            results.append({
                'error': '参数不完整，请提供行业名称',
                'suggestion': '请提供一个行业名称以预测其未来趋势'
            })
        else:
            # 使用外推模型预测行业趋势
            results = self.extrapolation_model.predict_market_trend(
                industry, future_years=future_years, top_k=top_k
            )
        
        return results
    
    def train_models(self, interpolation_epochs=10, extrapolation_epochs=5, learning_rate=0.01):
        """
        训练所有模型
        
        Args:
            interpolation_epochs: 内推模型训练轮数
            extrapolation_epochs: 外推模型训练轮数
            learning_rate: 学习率
            
        Returns:
            训练结果字典
        """
        import time
        results = {}
        
        # 训练内推模型
        print("训练内推模型...")
        start_time = time.time()
        self.interpolation_model.train(epochs=interpolation_epochs, learning_rate=learning_rate)
        results['interpolation'] = {
            'epochs': interpolation_epochs,
            'time_seconds': time.time() - start_time
        }
        
        # 训练外推模型
        print("训练外推模型...")
        start_time = time.time()
        self.extrapolation_model.train(epochs=extrapolation_epochs, learning_rate=learning_rate)
        results['extrapolation'] = {
            'epochs': extrapolation_epochs,
            'time_seconds': time.time() - start_time
        }
        
        return results
    
    def save_models(self, interpolation_path, extrapolation_path):
        """
        保存模型
        
        Args:
            interpolation_path: 内推模型保存路径
            extrapolation_path: 外推模型保存路径
            
        Returns:
            保存结果字典
        """
        results = {
            'interpolation': self.interpolation_model.save_model(interpolation_path),
            'extrapolation': self.extrapolation_model.save_model(extrapolation_path)
        }
        return results
    
    def load_models(self, interpolation_path, extrapolation_path):
        """
        加载模型
        
        Args:
            interpolation_path: 内推模型加载路径
            extrapolation_path: 外推模型加载路径
            
        Returns:
            加载结果字典
        """
        results = {
            'interpolation': self.interpolation_model.load_model(interpolation_path),
            'extrapolation': self.extrapolation_model.load_model(extrapolation_path)
        }
        return results

# 导出类和函数
__all__ = ['QAEngine', 'InterpolationModel', 'ExtrapolationModel']

# 示例用法
if __name__ == "__main__":
    print("问答引擎示例")
    print("请在导入知识图谱管理器后使用此引擎")