#!/usr/bin/env python3
"""
测试章节重新生成功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_outline_generation():
    """测试大纲生成功能"""
    try:
        from src.generation.outline_generator import generate_outline
        
        print("🧪 测试大纲生成...")
        
        # 测试基本生成
        print("\n1. 测试基本生成:")
        outline1 = generate_outline(topic="小红帽", style="科幻改写")
        print(f"生成结果类型: {type(outline1)}")
        if isinstance(outline1, list) and len(outline1) > 0:
            print(f"章节数量: {len(outline1)}")
            print(f"第一章格式: {outline1[0]}")
            print(f"第一章字段: {list(outline1[0].keys()) if isinstance(outline1[0], dict) else '非字典格式'}")
        
        # 测试带自定义指令的生成
        print("\n2. 测试带自定义指令的生成:")
        custom_instruction = """
请重新生成第6章的内容。
原章节ID: Chapter 6
原标题: 智斗大灰狼
要求: 保持与整体故事风格一致，但重新创作该章节的标题和摘要。
"""
        outline2 = generate_outline(
            topic="小红帽", 
            style="科幻改写", 
            custom_instruction=custom_instruction
        )
        print(f"生成结果类型: {type(outline2)}")
        if isinstance(outline2, list) and len(outline2) > 0:
            print(f"章节数量: {len(outline2)}")
            if len(outline2) > 5:  # 如果有第6章
                print(f"第6章格式: {outline2[5]}")
                print(f"第6章字段: {list(outline2[5].keys()) if isinstance(outline2[5], dict) else '非字典格式'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_field_extraction():
    """测试字段提取功能"""
    print("\n🧪 测试字段提取...")
    
    # 模拟LLM可能返回的不同格式
    test_cases = [
        # 标准格式
        {"chapter_id": "Chapter 1", "title": "测试标题", "summary": "测试摘要"},
        # 中文字段格式
        {"章节标题": "测试标题", "章节内容": "测试摘要"},
        # 混合格式
        {"chapter_id": "Chapter 1", "章节标题": "测试标题", "summary": "测试摘要"},
    ]
    
    def extract_field(chapter_data, field_name, alternatives=None, default=""):
        """从章节数据中提取字段，支持多种可能的字段名"""
        if alternatives is None:
            alternatives = []
        
        # 首先尝试标准字段名
        if field_name in chapter_data:
            return chapter_data[field_name]
        
        # 尝试备选字段名
        for alt_name in alternatives:
            if alt_name in chapter_data:
                return chapter_data[alt_name]
        
        return default
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {test_case}")
        
        title = extract_field(test_case, 'title', ['章节标题', '标题', 'chapter_title'], '默认标题')
        summary = extract_field(test_case, 'summary', ['章节内容', '内容', '摘要', 'chapter_content', 'content'], '默认摘要')
        chapter_id = extract_field(test_case, 'chapter_id', ['章节编号', '编号'], 'Chapter X')
        
        print(f"  提取结果:")
        print(f"    标题: {title}")
        print(f"    摘要: {summary}")
        print(f"    章节ID: {chapter_id}")

if __name__ == "__main__":
    print("🚀 开始测试章节重新生成功能")
    print("=" * 50)
    
    # 测试字段提取
    test_field_extraction()
    
    # 测试大纲生成
    if test_outline_generation():
        print("\n✅ 所有测试通过")
    else:
        print("\n❌ 测试失败")
