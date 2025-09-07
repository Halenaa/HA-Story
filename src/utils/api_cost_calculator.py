"""
API Cost Calculator
Used to estimate API call costs for different LLM models
"""

from typing import Dict, Optional
import re

class APICostCalculator:
    """API Cost Calculator"""
    
    # Price table for major models (price per 1000 tokens, USD)
    MODEL_PRICING = {
        # OpenAI GPT series
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-32k': {'input': 0.06, 'output': 0.12},
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
        'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
        'gpt-4.1': {'input': 0.01, 'output': 0.03},  # Assumed pricing
        'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
        'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004},
        
        # Anthropic Claude series
        'claude-3-opus': {'input': 0.015, 'output': 0.075},
        'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
        'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
        'claude-2': {'input': 0.008, 'output': 0.024},
        'claude-instant': {'input': 0.0008, 'output': 0.0024},
        
        # Google series
        'gemini-pro': {'input': 0.001, 'output': 0.002},
        'gemini-ultra': {'input': 0.01, 'output': 0.03},
        
        # Other models
        'llama-2-70b': {'input': 0.0007, 'output': 0.0009},
        'mixtral-8x7b': {'input': 0.0007, 'output': 0.0007},
        
        # Default estimated pricing
        'default': {'input': 0.001, 'output': 0.002}
    }
    
    @classmethod
    def calculate_cost(cls, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate API call cost
        
        Args:
            model_name: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost (USD)
        """
        # Normalize model name
        normalized_model = cls._normalize_model_name(model_name)
        
        # Get pricing information
        pricing = cls.MODEL_PRICING.get(normalized_model, cls.MODEL_PRICING['default'])
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        total_cost = input_cost + output_cost
        
        return total_cost
    
    @classmethod
    def _normalize_model_name(cls, model_name: str) -> str:
        """Normalize model name to match pricing table"""
        if not model_name:
            return 'default'
            
        model_name = model_name.lower().strip()
        
        # Direct match
        if model_name in cls.MODEL_PRICING:
            return model_name
        
        # Fuzzy match
        for key in cls.MODEL_PRICING.keys():
            if key in model_name or model_name in key:
                return key
        
        # Keyword-based matching
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
                    return 'claude-3-sonnet'  # default
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
        Estimate token count from text
        This is a rough estimation, actual token count may vary
        """
        if not text:
            return 0
        
        # Simple token estimation:
        # English: approximately 4 characters = 1 token
        # Chinese: approximately 1.5-2 characters = 1 token
        
        # Count Chinese and English characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(text) - chinese_chars
        
        # Estimate token count
        chinese_tokens = chinese_chars / 1.5  # Chinese token estimation
        english_tokens = english_chars / 4    # English token estimation
        
        total_tokens = int(chinese_tokens + english_tokens)
        
        # Minimum token count
        return max(total_tokens, 1)
    
    @classmethod
    def get_model_pricing_info(cls, model_name: str) -> Dict:
        """Get model pricing information"""
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
        Calculate cost with support for token estimation from text
        
        Args:
            model_name: Model name
            input_text: Input text
            output_text: Output text  
            input_tokens: Actual input token count (optional)
            output_tokens: Actual output token count (optional)
            
        Returns:
            Dictionary containing cost and token information
        """
        # Use actual token count or estimation
        if input_tokens is None:
            input_tokens = cls.estimate_tokens_from_text(input_text)
        if output_tokens is None:
            output_tokens = cls.estimate_tokens_from_text(output_text)
        
        # Calculate cost
        cost = cls.calculate_cost(model_name, input_tokens, output_tokens)
        
        # Get pricing information
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
    """Test API cost calculator"""
    calculator = APICostCalculator()
    
    # Test cases
    test_cases = [
        {
            'model': 'gpt-4',
            'input_text': 'Please generate a science fiction story outline',
            'output_text': 'This is a science fiction story about time travel. The protagonist is a physicist...'
        },
        {
            'model': 'claude-3-sonnet', 
            'input_text': 'Generate a character for a science fiction story',
            'output_text': 'Dr. Elena Vasquez is a brilliant quantum physicist who discovers...'
        }
    ]
    
    print("API Cost Calculator Test")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {case['model']}")
        result = calculator.calculate_cost_with_estimation(
            case['model'], case['input_text'], case['output_text']
        )
        
        print(f"Input Tokens: {result['input_tokens']}")
        print(f"Output Tokens: {result['output_tokens']}")
        print(f"Total Tokens: {result['total_tokens']}")
        print(f"Total Cost: ${result['cost']:.6f}")
        print(f"Input Cost: ${result['input_cost']:.6f}")
        print(f"Output Cost: ${result['output_cost']:.6f}")


if __name__ == "__main__":
    main()
