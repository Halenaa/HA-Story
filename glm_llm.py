from openai import OpenAI 

class LLMCall:
    """智谱AI大模型调用类"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key="b6bb9bc3aaa74730aac46fe21e7505ae.uuZ1vg8y5oO2g6Ap",
            base_url="https://open.bigmodel.cn/api/paas/v4/"
        )
    
    def generate_response(self, prompt, temperature=0.7, model="glm-4-air"):
        """生成回复"""
        try:
            completion = self.client.chat.completions.create(
                model=model,  
                messages=[    
                    {"role": "system", "content": "你是一个聪明且富有创造力的小说作家"},    
                    {"role": "user", "content": prompt} 
                ],
                top_p=0.7,
                temperature=temperature
            ) 
            
            return completion.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"生成失败: {str(e)}")