"""
API成本计算器
用于估算不同LLM模型的API调用成本
"""

from typing import Dict, Optional
import re

class APICostCalculator:
    """API成本计算器"""
    
    # 主要模型的价格表（每1000 tokens的价格，美元）
    MODEL_PRICING = {
        # OpenAI GPT 系列
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-32k': {'input': 0.06, 'output': 0.12},
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
        'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
        'gpt-4.1': {'input': 0.01, 'output': 0.03},  # 假设价格
        'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
        'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004},
        
        # Anthropic Claude 系列
        'claude-3-opus': {'input': 0.015, 'output': 0.075},
        'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
        'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
        'claude-2': {'input': 0.008, 'output': 0.024},
        'claude-instant': {'input': 0.0008, 'output': 0.0024},
        
        # Google 系列
        'gemini-pro': {'input': 0.001, 'output': 0.002},
        'gemini-ultra': {'input': 0.01, 'output': 0.03},
        
        # 其他模型
        'llama-2-70b': {'input': 0.0007, 'output': 0.0009},
        'mixtral-8x7b': {'input': 0.0007, 'output': 0.0007},
        
        # 默认估算价格
        'default': {'input': 0.001, 'output': 0.002}
    }
    
    @classmethod
    def calculate_cost(cls, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        计算API调用成本
        
        Args:
            model_name: 模型名称
            input_tokens: 输入token数量
            output_tokens: 输出token数量
            
        Returns:
            成本（美元）
        """
        # 规范化模型名称
        normalized_model = cls._normalize_model_name(model_name)
        
        # 获取定价信息
        pricing = cls.MODEL_PRICING.get(normalized_model, cls.MODEL_PRICING['default'])
        
        # 计算成本
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        total_cost = input_cost + output_cost
        
        return total_cost
    
    @classmethod
    def _normalize_model_name(cls, model_name: str) -> str:
        """规范化模型名称以匹配定价表"""
        if not model_name:
            return 'default'
            
        model_name = model_name.lower().strip()
        
        # 直接匹配
        if model_name in cls.MODEL_PRICING:
            return model_name
        
        # 模糊匹配
        for key in cls.MODEL_PRICING.keys():
            if key in model_name or model_name in key:
                return key
        
        # 基于关键词匹配
        if 'gpt-4' in model_name:
            if '32k' in model_name:
                return 'gpt-4-32k'
            elif 'turbo' in model_name:
                return 'gpt-4-turbo'
            else:
                return 'gpt-4'
        elif 'gpt-3.5' in model_name or 'gpt3.5' in model_name:
            if '16k' in model_name:
                return 'gpt-3.5-turbo-16k'
            else:
                return 'gpt-3.5-turbo'
        elif 'claude' in model_name:
            if '3' in model_name:
                if 'opus' in model_name:
                    return 'claude-3-opus'
                elif 'sonnet' in model_name:
                    return 'claude-3-sonnet'
                elif 'haiku' in model_name:
                    return 'claude-3-haiku'
                else:
                    return 'claude-3-sonnet'  # 默认
            elif 'instant' in model_name:
                return 'claude-instant'
            else:
                return 'claude-2'
        elif 'gemini' in model_name:
            if 'ultra' in model_name:
                return 'gemini-ultra'
            else:
                return 'gemini-pro'
        
        return 'default'
    
    @classmethod
    def estimate_tokens_from_text(cls, text: str) -> int:
        """
        从文本估算token数量
        这是一个粗略的估算，实际token数量可能有差异
        """
        if not text:
            return 0
        
        # 简单的token估算：
        # 英文大约 4 字符 = 1 token
        # 中文大约 1.5-2 字符 = 1 token
        
        # 计算中英文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(text) - chinese_chars
        
        # 估算token数量
        chinese_tokens = chinese_chars / 1.5  # 中文token估算
        english_tokens = english_chars / 4    # 英文token估算
        
        total_tokens = int(chinese_tokens + english_tokens)
        
        # 最小token数量
        return max(total_tokens, 1)
    
    @classmethod
    def get_model_pricing_info(cls, model_name: str) -> Dict:
        """获取模型定价信息"""
        normalized_model = cls._normalize_model_name(model_name)
        pricing = cls.MODEL_PRICING.get(normalized_model, cls.MODEL_PRICING['default'])
        
        return {
            'model': normalized_model,
            'input_price_per_1k': pricing['input'],
            'output_price_per_1k': pricing['output'],
            'total_price_per_1k': pricing['input'] + pricing['output']
        }
    
    @classmethod
    def calculate_cost_with_estimation(cls, model_name: str, input_text: str, 
                                     output_text: str, input_tokens: int = None, 
                                     output_tokens: int = None) -> Dict:
        """
        计算成本，支持从文本估算token数量
        
        Args:
            model_name: 模型名称
            input_text: 输入文本
            output_text: 输出文本  
            input_tokens: 实际输入token数量（可选）
            output_tokens: 实际输出token数量（可选）
            
        Returns:
            包含成本和token信息的字典
        """
        # 使用实际token数量或估算
        if input_tokens is None:
            input_tokens = cls.estimate_tokens_from_text(input_text)
        if output_tokens is None:
            output_tokens = cls.estimate_tokens_from_text(output_text)
        
        # 计算成本
        cost = cls.calculate_cost(model_name, input_tokens, output_tokens)
        
        # 获取定价信息
        pricing_info = cls.get_model_pricing_info(model_name)
        
        return {
            'model': pricing_info['model'],
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'cost': cost,
            'input_cost': (input_tokens / 1000) * pricing_info['input_price_per_1k'],
            'output_cost': (output_tokens / 1000) * pricing_info['output_price_per_1k'],
            'pricing_info': pricing_info
        }


def main():
    """测试API成本计算器"""
    calculator = APICostCalculator()
    
    # 测试用例
    test_cases = [
        {
            'model': 'gpt-4',
            'input_text': '请生成一个关于科幻的故事大纲',
            'output_text': '这是一个关于时间旅行的科幻故事。主角是一个物理学家...'
        },
        {
            'model': 'claude-3-sonnet', 
            'input_text': 'Generate a character for a science fiction story',
            'output_text': 'Dr. Elena Vasquez is a brilliant quantum physicist who discovers...'
        }
    ]
    
    print("🧮 API成本计算器测试")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {case['model']}")
        result = calculator.calculate_cost_with_estimation(
            case['model'], case['input_text'], case['output_text']
        )
        
        print(f"输入Tokens: {result['input_tokens']}")
        print(f"输出Tokens: {result['output_tokens']}")
        print(f"总Tokens: {result['total_tokens']}")
        print(f"总成本: ${result['cost']:.6f}")
        print(f"输入成本: ${result['input_cost']:.6f}")
        print(f"输出成本: ${result['output_cost']:.6f}")


if __name__ == "__main__":
    main()
