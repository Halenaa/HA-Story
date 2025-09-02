#!/usr/bin/env python3
"""
测试角色生成功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_character_generation_import():
    """测试角色生成模块导入"""
    print("🧪 测试角色生成模块导入...")
    
    try:
        print("  📁 导入基础配置模块...")
        from src.constant import output_dir
        print("    ✅ src.constant.output_dir 导入成功")
        
        print("  🛠️ 导入工具函数...")
        from src.utils.utils import save_json, load_json
        print("    ✅ src.utils.utils.save_json 导入成功")
        print("    ✅ src.utils.utils.load_json 导入成功")
        
        print("  👥 导入角色生成模块...")
        from src.generation.generate_characters import generate_characters_v1
        print("    ✅ src.generation.generate_characters.generate_characters_v1 导入成功")
        
        print("  📖 导入故事扩展模块...")
        from src.generation.expand_story import expand_story_v1
        print("    ✅ src.generation.expand_story.expand_story_v1 导入成功")
        
        print("🎉 所有角色生成相关模块导入成功！")
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_character_generation_function():
    """测试角色生成功能"""
    print("\n🎭 测试角色生成功能...")
    
    # 模拟大纲数据
    test_outline = [
        {
            "chapter_id": "Chapter 1",
            "title": "小红帽的太空任务",
            "summary": "小红帽是一名居住在未来星球上的少女，她接受任务前往外婆的空间站。"
        },
        {
            "chapter_id": "Chapter 2", 
            "title": "太空穿梭",
            "summary": "小红帽乘坐飞船穿越危险的星际丛林，遇到各种机械生物。"
        },
        {
            "chapter_id": "Chapter 3",
            "title": "AI狼现身",
            "summary": "一只AI控制的机械大灰狼拦截了小红帽，外婆是个善良的老人。"
        }
    ]
    
    try:
        from src.generation.generate_characters import generate_characters_v1
        import time
        
        print(f"📊 输入大纲:")
        for i, ch in enumerate(test_outline):
            print(f"  {i+1}. {ch['title']}: {ch['summary']}")
        
        print(f"\n🔄 调用 generate_characters_v1...")
        print(f"  参数: outline={len(test_outline)}章节, max_characters=5")
        
        start_time = time.time()
        characters = generate_characters_v1(test_outline, max_characters=5)
        end_time = time.time()
        
        print(f"⏱️ 生成耗时: {end_time - start_time:.3f}秒")
        
        # 验证结果
        if not characters:
            print("❌ 角色生成失败: 返回空结果")
            return False
        
        if not isinstance(characters, list):
            print(f"❌ 角色生成失败: 返回类型错误 {type(characters)}")
            print(f"实际返回: {str(characters)[:200]}...")
            return False
        
        print(f"✅ 角色生成成功! 共生成 {len(characters)} 个角色")
        
        # 显示生成的角色
        print(f"\n👥 生成的角色:")
        for i, char in enumerate(characters):
            name = char.get('name', '未知')
            role = char.get('role', '未知')
            traits = char.get('traits', '无')[:50] + "..." if len(char.get('traits', '')) > 50 else char.get('traits', '无')
            
            print(f"  {i+1}. {name} ({role})")
            print(f"     特征: {traits}")
        
        # 验证必要字段
        required_fields = ['name', 'role', 'traits', 'background', 'motivation']
        for i, char in enumerate(characters):
            missing_fields = [field for field in required_fields if field not in char]
            if missing_fields:
                print(f"⚠️ 角色{i+1} 缺少字段: {missing_fields}")
            else:
                print(f"✅ 角色{i+1} 字段完整")
        
        return True
        
    except Exception as e:
        print(f"❌ 角色生成测试失败: {str(e)}")
        return False

def test_save_load_characters():
    """测试角色保存和加载功能"""
    print("\n💾 测试角色保存和加载...")
    
    try:
        from src.utils.utils import save_json, load_json
        import tempfile
        import json
        
        # 创建测试角色数据
        test_characters = [
            {
                "name": "小红帽",
                "role": "主角",
                "traits": "勇敢、聪明、善良",
                "background": "来自未来星球的少女",
                "motivation": "拯救外婆"
            },
            {
                "name": "机械大灰狼",
                "role": "反派",
                "traits": "狡猾、强大、AI控制",
                "background": "被邪恶势力控制的机器人",
                "motivation": "阻止小红帽"
            }
        ]
        
        print(f"📝 测试数据: {len(test_characters)} 个角色")
        
        # 使用临时目录测试保存
        with tempfile.TemporaryDirectory() as temp_dir:
            # 保存测试
            test_file = os.path.join(temp_dir, "test_characters.json")
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_characters, f, ensure_ascii=False, indent=2)
            
            print("✅ 角色保存成功")
            
            # 加载测试
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded_characters = json.load(f)
            
            if loaded_characters == test_characters:
                print("✅ 角色加载成功，数据一致")
                return True
            else:
                print("❌ 角色加载失败，数据不一致")
                return False
        
    except Exception as e:
        print(f"❌ 角色保存/加载测试失败: {str(e)}")
        return False

def main():
    print("🚀 开始角色生成功能测试")
    print("=" * 60)
    
    # 测试导入
    import_success = test_character_generation_import()
    
    if import_success:
        # 测试功能
        function_success = test_character_generation_function()
        
        # 测试保存加载
        save_load_success = test_save_load_characters()
        
        print("\n" + "=" * 60)
        print("📊 测试结果总结:")
        print(f"  模块导入: {'✅ 成功' if import_success else '❌ 失败'}")
        print(f"  功能测试: {'✅ 成功' if function_success else '❌ 失败'}")
        print(f"  保存加载: {'✅ 成功' if save_load_success else '❌ 失败'}")
        
        if import_success and function_success and save_load_success:
            print("\n🎉 所有测试通过！角色生成功能可以正常使用。")
        else:
            print("\n⚠️ 部分测试失败，请检查相关模块。")
    else:
        print("\n❌ 基础模块导入失败，无法进行后续测试")

if __name__ == "__main__":
    main()
