# glm_llm = ChatOpenAI(
#     api_key=os.getenv("b6bb9bc3aaa74730aac46fe21e7505ae.uuZ1vg8y5oO2g6Ap"),
#     model="glm-4-air",
#     base_url="	https://open.bigmodel.cn/api/paas/v4/chat/completions",
#     temperature=0.7,
# )


# response = glm_llm.invoke()
# print(response.content)


from openai import OpenAI 

client = OpenAI(
    api_key="b6bb9bc3aaa74730aac46fe21e7505ae.uuZ1vg8y5oO2g6Ap",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
) 

completion = client.chat.completions.create(
    model="glm-4-air",  
    messages=[    
        {"role": "system", "content": "你是一个聪明且富有创造力的小说作家"},    
        {"role": "user", "content": "请你作为童话故事大王，写一篇短篇童话故事，故事的主题是要永远保持一颗善良的心，要能够激发儿童的学习兴趣和想象力，同时也能够帮助儿童更好地理解和接受故事中所蕴含的道理和价值观。"} 
    ],
    top_p=0.7,
    temperature=0.9
 ) 
 
print(completion.choices[0].message)