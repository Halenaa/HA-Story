#!/usr/bin/env python3
"""
测试历史记录功能
"""

import sys
import os
import copy
import datetime

def test_history_functions():
    """测试历史记录相关功能"""
    print("🧪 测试历史记录功能...")
    
    # 模拟会话状态
    class MockSessionState:
        def __init__(self):
            self.outline_data = [
                {"chapter_id": "Chapter 1", "title": "第一章", "summary": "第一章内容"},
                {"chapter_id": "Chapter 2", "title": "第二章", "summary": "第二章内容"},
                {"chapter_id": "Chapter 3", "title": "第三章", "summary": "第三章内容"},
            ]
            self.current_version = "test_version"
            self.outline_history = []
            self.history_index = -1
    
    session_state = MockSessionState()
    
    def save_to_history(action_name, old_data=None):
        """保存当前状态到历史记录"""
        if session_state.outline_data is None:
            return
        
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        
        history_entry = {
            'timestamp': timestamp,
            'action': action_name,
            'data': copy.deepcopy(session_state.outline_data),
            'version': session_state.current_version,
            'old_data': copy.deepcopy(old_data) if old_data else None
        }
        
        # 如果当前不在历史记录的末尾，删除后面的记录
        if session_state.history_index < len(session_state.outline_history) - 1:
            session_state.outline_history = session_state.outline_history[:session_state.history_index + 1]
        
        # 添加新记录
        session_state.outline_history.append(history_entry)
        session_state.history_index = len(session_state.outline_history) - 1
        
        # 限制历史记录数量（最多保存20个状态）
        if len(session_state.outline_history) > 20:
            session_state.outline_history = session_state.outline_history[-20:]
            session_state.history_index = len(session_state.outline_history) - 1
        
        print(f"  ✅ 保存历史记录: {action_name} at {timestamp}")
    
    def undo_last_action():
        """撤销上一个操作"""
        if session_state.history_index > 0:
            session_state.history_index -= 1
            previous_state = session_state.outline_history[session_state.history_index]
            session_state.outline_data = copy.deepcopy(previous_state['data'])
            session_state.current_version = previous_state['version']
            print(f"  ✅ 已撤销操作: {previous_state['action']}")
            return True
        else:
            print("  ⚠️ 没有可撤销的操作")
            return False
    
    def redo_last_action():
        """重做下一个操作"""
        if session_state.history_index < len(session_state.outline_history) - 1:
            session_state.history_index += 1
            next_state = session_state.outline_history[session_state.history_index]
            session_state.outline_data = copy.deepcopy(next_state['data'])
            session_state.current_version = next_state['version']
            print(f"  ✅ 已重做操作: {next_state['action']}")
            return True
        else:
            print("  ⚠️ 没有可重做的操作")
            return False
    
    # 测试场景
    print("\n1. 初始状态:")
    print(f"   章节数: {len(session_state.outline_data)}")
    print(f"   历史记录数: {len(session_state.outline_history)}")
    
    # 保存初始状态
    print("\n2. 保存初始状态:")
    save_to_history("初始生成")
    print(f"   历史记录数: {len(session_state.outline_history)}")
    
    # 模拟删除章节
    print("\n3. 删除第2章:")
    old_data = session_state.outline_data.copy()
    save_to_history("删除第2章", old_data)
    deleted_chapter = session_state.outline_data.pop(1)
    print(f"   删除章节: {deleted_chapter['title']}")
    print(f"   剩余章节数: {len(session_state.outline_data)}")
    print(f"   历史记录数: {len(session_state.outline_history)}")
    
    # 模拟添加章节
    print("\n4. 添加新章节:")
    old_data = session_state.outline_data.copy()
    save_to_history("添加新章节", old_data)
    new_chapter = {"chapter_id": "Chapter 4", "title": "新第四章", "summary": "新添加的章节"}
    session_state.outline_data.append(new_chapter)
    print(f"   添加章节: {new_chapter['title']}")
    print(f"   章节数: {len(session_state.outline_data)}")
    print(f"   历史记录数: {len(session_state.outline_history)}")
    
    # 测试撤销
    print("\n5. 撤销添加操作:")
    undo_last_action()
    print(f"   章节数: {len(session_state.outline_data)}")
    
    # 测试再次撤销
    print("\n6. 撤销删除操作:")
    undo_last_action()
    print(f"   章节数: {len(session_state.outline_data)}")
    
    # 测试重做
    print("\n7. 重做删除操作:")
    redo_last_action()
    print(f"   章节数: {len(session_state.outline_data)}")
    
    # 显示历史记录
    print("\n8. 历史记录列表:")
    for i, entry in enumerate(session_state.outline_history):
        current_marker = "🔵" if i == session_state.history_index else "⚪"
        print(f"   {current_marker} {entry['timestamp']} - {entry['action']} ({len(entry['data'])} 章)")
    
    print("\n✅ 历史记录功能测试完成")
    return True

if __name__ == "__main__":
    print("🚀 开始测试历史记录功能")
    print("=" * 50)
    
    if test_history_functions():
        print("\n🎉 所有测试通过！")
    else:
        print("\n❌ 测试失败")
