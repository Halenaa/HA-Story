import streamlit as st
import os
import json
import tempfile
from typing import List, Dict, Any
import sys
import time
import datetime
import logging
import copy

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 必须导入真实后端功能，如果失败则报错
print("🔄 开始导入真实后端模块...")

# 基础模块导入
try:
    print("  📁 导入基础配置模块...")
    from src.constant import output_dir
    print("    ✅ src.constant.output_dir 导入成功")
    
    print("  🛠️ 导入工具函数...")
    from src.utils.utils import save_json, load_json
    print("    ✅ src.utils.utils.save_json 导入成功")
    print("    ✅ src.utils.utils.load_json 导入成功")
    
    print("  📝 导入版本命名模块...")
    from src.version_namer import build_version_name
    print("    ✅ src.version_namer.build_version_name 导入成功")
    
    print("  📊 导入日志模块...")
    from src.utils.logger import init_log_path, append_log, build_simple_log
    print("    ✅ src.utils.logger.init_log_path 导入成功")
    print("    ✅ src.utils.logger.append_log 导入成功")
    print("    ✅ src.utils.logger.build_simple_log 导入成功")
    
except ImportError as e:
    st.error(f"❌ 基础模块导入失败: {e}")
    st.stop()

# 大纲生成相关模块导入
try:
    print("  📚 导入大纲生成模块...")
    from src.generation.outline_generator import generate_outline
    print("    ✅ src.generation.outline_generator.generate_outline 导入成功")
    
    print("  🔄 导入章节重排模块...")
    from src.generation.chapter_reorder import reorder_chapters
    print("    ✅ src.generation.chapter_reorder.reorder_chapters 导入成功")
    
    print("  🎭 导入叙述分析模块...")
    from src.generation.narrative_analyzer import analyze_narrative_structure
    print("    ✅ src.generation.narrative_analyzer.analyze_narrative_structure 导入成功")
    
except ImportError as e:
    st.error(f"❌ 大纲相关模块导入失败: {e}")
    st.stop()

# 角色生成相关模块导入 (可选功能)
try:
    print("  👥 导入角色生成模块...")
    from src.generation.generate_characters import generate_characters_v1
    print("    ✅ src.generation.generate_characters.generate_characters_v1 导入成功")
    
    print("  📖 导入故事扩展模块...")
    from src.generation.expand_story import expand_story_v1
    print("    ✅ src.generation.expand_story.expand_story_v1 导入成功")
    
    character_generation_available = True
    
except ImportError as e:
    print(f"⚠️ 角色生成相关模块导入失败: {e}")
    print("⚠️ 角色生成功能将不可用，但不影响大纲生成功能")
    character_generation_available = False

# 对话生成相关模块导入 (可选功能)
try:
    print("  💬 导入对话生成模块...")
    from src.generation.dialogue_inserter import analyze_dialogue_insertions_v2, run_dialogue_insertion
    print("    ✅ src.generation.dialogue_inserter.analyze_dialogue_insertions_v2 导入成功")
    print("    ✅ src.generation.dialogue_inserter.run_dialogue_insertion 导入成功")
    
    print("  🔄 导入对话同步模块...")
    from src.sync.plot_sync_manager import sync_plot_and_dialogue_from_behavior
    print("    ✅ src.sync.plot_sync_manager.sync_plot_and_dialogue_from_behavior 导入成功")
    
    print("  📝 导入故事编译模块...")
    from src.compile_story import compile_full_story_by_sentence
    print("    ✅ src.compile_story.compile_full_story_by_sentence 导入成功")
    
    dialogue_generation_available = True
    
except ImportError as e:
    print(f"⚠️ 对话生成相关模块导入失败: {e}")
    print("⚠️ 对话生成功能将不可用，但不影响其他功能")
    dialogue_generation_available = False

# 故事增强相关模块导入 (可选功能)
try:
    print("  ✨ 导入故事增强模块...")
    from src.enhance_story import enhance_story_with_transitions, polish_dialogues_in_story
    print("    ✅ src.enhance_story.enhance_story_with_transitions 导入成功")
    print("    ✅ src.enhance_story.polish_dialogues_in_story 导入成功")
    
    print("  📝 导入故事编译模块...")
    # compile_story 已经在对话生成中导入过了，这里不需要重复导入
    print("    ✅ src.compile_story 已在对话生成模块中导入")
    
    story_enhancement_available = True
    
except ImportError as e:
    print(f"⚠️ 故事增强相关模块导入失败: {e}")
    print("⚠️ 故事增强功能将不可用，但不影响其他功能")
    story_enhancement_available = False



print("🎉 所有真实后端模块导入完成！")

# 设置日志记录
@st.cache_resource
def setup_logger():
    """设置应用日志记录器"""
    logger = logging.getLogger('outline_app')
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # 创建日志目录
    log_dir = "streamlit_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 文件处理器
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"outline_app_{datetime.datetime.now().strftime('%Y%m%d')}.log"),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# 初始化日志器
app_logger = setup_logger()

# 页面配置
st.set_page_config(
    page_title="故事大纲生成器",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 日志显示组件
def show_execution_log(log_entries):
    """显示执行日志"""
    if log_entries:
        with st.expander("📋 执行日志", expanded=True):
            for entry in log_entries:
                timestamp = entry.get('timestamp', 'Unknown')
                level = entry.get('level', 'INFO')
                message = entry.get('message', '')
                
                if level == 'ERROR':
                    st.error(f"[{timestamp}] {message}")
                elif level == 'WARNING':
                    st.warning(f"[{timestamp}] {message}")
                elif level == 'SUCCESS':
                    st.success(f"[{timestamp}] {message}")
                else:
                    st.info(f"[{timestamp}] {message}")

def log_backend_operation(operation_name, params, start_time, end_time, result, error=None):
    """记录后端操作日志"""
    duration = end_time - start_time
    
    log_entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'operation': operation_name,
        'parameters': params,
        'duration_seconds': round(duration, 3),
        'success': error is None,
        'result_summary': get_result_summary(result) if result else None,
        'error': str(error) if error else None
    }
    
    # 记录到应用日志
    app_logger.info(f"Backend operation: {operation_name} | Duration: {duration:.3f}s | Success: {error is None}")
    
    # 添加到会话状态的日志列表
    if 'execution_logs' not in st.session_state:
        st.session_state.execution_logs = []
    
    st.session_state.execution_logs.append({
        'timestamp': datetime.datetime.now().strftime('%H:%M:%S'),
        'level': 'ERROR' if error else 'SUCCESS',
        'message': f"{operation_name} {'失败' if error else '成功'} (耗时: {duration:.3f}s)"
    })
    
    return log_entry

def get_result_summary(result):
    """获取结果摘要"""
    if isinstance(result, list):
        return f"返回列表，{len(result)}个项目"
    elif isinstance(result, dict):
        return f"返回字典，{len(result)}个字段"
    elif isinstance(result, str):
        return f"返回字符串，长度{len(result)}"
    else:
        return f"返回{type(result).__name__}类型"

def get_current_version():
    """获取当前项目版本名称"""
    try:
        # 尝试从session state获取当前版本
        if hasattr(st.session_state, 'current_version') and st.session_state.current_version:
            return st.session_state.current_version
        
        # 尝试从outline数据推断版本
        if st.session_state.get('outline_data'):
            # 生成一个基于当前时间的版本名
            import time
            timestamp = int(time.time())
            return f"story_enhance_{timestamp}"
        
        # 默认版本名
        return "default_version"
        
    except Exception as e:
        print(f"⚠️ [版本获取] 获取当前版本失败: {e}")
        return "default_version"

# 历史记录管理功能
def save_to_history(action_name, old_data=None):
    """保存当前状态到历史记录"""
    if st.session_state.outline_data is None:
        return
    
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    
    history_entry = {
        'timestamp': timestamp,
        'action': action_name,
        'data': copy.deepcopy(st.session_state.outline_data),
        'version': st.session_state.current_version,
        'old_data': copy.deepcopy(old_data) if old_data else None
    }
    
    # 如果当前不在历史记录的末尾，删除后面的记录
    if st.session_state.history_index < len(st.session_state.outline_history) - 1:
        st.session_state.outline_history = st.session_state.outline_history[:st.session_state.history_index + 1]
    
    # 添加新记录
    st.session_state.outline_history.append(history_entry)
    st.session_state.history_index = len(st.session_state.outline_history) - 1
    
    # 限制历史记录数量（最多保存20个状态）
    if len(st.session_state.outline_history) > 20:
        st.session_state.outline_history = st.session_state.outline_history[-20:]
        st.session_state.history_index = len(st.session_state.outline_history) - 1
    
    app_logger.info(f"Saved to history: {action_name} at {timestamp}")

def save_characters_to_history(action_name, old_characters_data=None):
    """保存角色状态到历史记录"""
    if st.session_state.characters_data is None:
        return
    
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    
    history_entry = {
        'timestamp': timestamp,
        'action': action_name,
        'characters_data': copy.deepcopy(st.session_state.characters_data),
        'character_chapter_mapping': copy.deepcopy(st.session_state.character_chapter_mapping),
        'old_characters_data': copy.deepcopy(old_characters_data) if old_characters_data else None
    }
    
    # 如果当前不在历史记录的末尾，删除后面的记录
    if st.session_state.characters_history_index < len(st.session_state.characters_history) - 1:
        st.session_state.characters_history = st.session_state.characters_history[:st.session_state.characters_history_index + 1]
    
    # 添加新记录
    st.session_state.characters_history.append(history_entry)
    st.session_state.characters_history_index = len(st.session_state.characters_history) - 1
    
    # 限制历史记录数量（最多保存20个状态）
    if len(st.session_state.characters_history) > 20:
        st.session_state.characters_history = st.session_state.characters_history[-20:]
        st.session_state.characters_history_index = len(st.session_state.characters_history) - 1
    
    app_logger.info(f"Saved characters to history: {action_name} at {timestamp}")

def undo_characters_action():
    """撤销上一个角色操作"""
    if st.session_state.characters_history_index > 0:
        st.session_state.characters_history_index -= 1
        previous_state = st.session_state.characters_history[st.session_state.characters_history_index]
        st.session_state.characters_data = copy.deepcopy(previous_state['characters_data'])
        st.session_state.character_chapter_mapping = copy.deepcopy(previous_state['character_chapter_mapping'])
        st.success(f"✅ 已撤销角色操作: {previous_state['action']}")
        return True
    else:
        st.warning("⚠️ 没有可撤销的角色操作")
        return False

def redo_characters_action():
    """重做下一个角色操作"""
    if st.session_state.characters_history_index < len(st.session_state.characters_history) - 1:
        st.session_state.characters_history_index += 1
        next_state = st.session_state.characters_history[st.session_state.characters_history_index]
        st.session_state.characters_data = copy.deepcopy(next_state['characters_data'])
        st.session_state.character_chapter_mapping = copy.deepcopy(next_state['character_chapter_mapping'])
        st.success(f"✅ 已重做角色操作: {next_state['action']}")
        return True
    else:
        st.warning("⚠️ 没有可重做的角色操作")
        return False

def save_story_to_history(action_name, old_story_data=None):
    """保存故事状态到历史记录"""
    if st.session_state.story_data is None:
        return
    
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    
    history_entry = {
        'timestamp': timestamp,
        'action': action_name,
        'story_data': copy.deepcopy(st.session_state.story_data),
        'old_story_data': copy.deepcopy(old_story_data) if old_story_data else None
    }
    
    # 如果当前不在历史记录的末尾，删除后面的记录
    if st.session_state.story_history_index < len(st.session_state.story_history) - 1:
        st.session_state.story_history = st.session_state.story_history[:st.session_state.story_history_index + 1]
    
    # 添加新记录
    st.session_state.story_history.append(history_entry)
    st.session_state.story_history_index = len(st.session_state.story_history) - 1
    
    # 限制历史记录数量（最多保存20个状态）
    if len(st.session_state.story_history) > 20:
        st.session_state.story_history = st.session_state.story_history[-20:]
        st.session_state.story_history_index = len(st.session_state.story_history) - 1
    
    app_logger.info(f"Saved story to history: {action_name} at {timestamp}")

def undo_story_action():
    """撤销上一个故事操作"""
    if st.session_state.story_history_index > 0:
        st.session_state.story_history_index -= 1
        previous_state = st.session_state.story_history[st.session_state.story_history_index]
        st.session_state.story_data = copy.deepcopy(previous_state['story_data'])
        st.success(f"✅ 已撤销故事操作: {previous_state['action']}")
        return True
    else:
        st.warning("⚠️ 没有可撤销的故事操作")
        return False

def redo_story_action():
    """重做下一个故事操作"""
    if st.session_state.story_history_index < len(st.session_state.story_history) - 1:
        st.session_state.story_history_index += 1
        next_state = st.session_state.story_history[st.session_state.story_history_index]
        st.session_state.story_data = copy.deepcopy(next_state['story_data'])
        st.success(f"✅ 已重做故事操作: {next_state['action']}")
        return True
    else:
        st.warning("⚠️ 没有可重做的故事操作")
        return False

def undo_last_action():
    """撤销上一个操作"""
    if st.session_state.history_index > 0:
        st.session_state.history_index -= 1
        previous_state = st.session_state.outline_history[st.session_state.history_index]
        st.session_state.outline_data = copy.deepcopy(previous_state['data'])
        st.session_state.current_version = previous_state['version']
        st.success(f"✅ 已撤销操作: {previous_state['action']}")
        return True
    else:
        st.warning("⚠️ 没有可撤销的操作")
        return False

def redo_last_action():
    """重做下一个操作"""
    if st.session_state.history_index < len(st.session_state.outline_history) - 1:
        st.session_state.history_index += 1
        next_state = st.session_state.outline_history[st.session_state.history_index]
        st.session_state.outline_data = copy.deepcopy(next_state['data'])
        st.session_state.current_version = next_state['version']
        st.success(f"✅ 已重做操作: {next_state['action']}")
        return True
    else:
        st.warning("⚠️ 没有可重做的操作")
        return False

def show_history_panel():
    """显示历史记录面板"""
    if not st.session_state.outline_history:
        st.info("📝 暂无历史记录")
        return
    
    st.subheader("📋 操作历史")
    
    # 撤销/重做按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("↶ 撤销", use_container_width=True, disabled=st.session_state.history_index <= 0):
            if undo_last_action():
                st.rerun()
    
    with col2:
        if st.button("↷ 重做", use_container_width=True, disabled=st.session_state.history_index >= len(st.session_state.outline_history) - 1):
            if redo_last_action():
                st.rerun()
    
    with col3:
        if st.button("🗑️ 清空历史", use_container_width=True):
            st.session_state.outline_history = []
            st.session_state.history_index = -1
            st.success("✅ 历史记录已清空")
            st.rerun()
    
    st.markdown("---")
    
    # 显示历史记录列表
    st.markdown("**历史记录:**")
    
    for i, entry in enumerate(reversed(st.session_state.outline_history)):
        real_index = len(st.session_state.outline_history) - 1 - i
        is_current = real_index == st.session_state.history_index
        
        # 创建历史记录条目
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                status = "🔵" if is_current else "⚪"
                st.markdown(f"{status} `{entry['timestamp']}`")
            
            with col2:
                st.markdown(f"**{entry['action']}**")
                chapter_count = len(entry['data']) if entry['data'] else 0
                st.caption(f"共 {chapter_count} 章节")
            
            with col3:
                if st.button("📍", key=f"goto_{real_index}", help="跳转到此状态"):
                    st.session_state.history_index = real_index
                    st.session_state.outline_data = copy.deepcopy(entry['data'])
                    st.session_state.current_version = entry['version']
                    st.success(f"✅ 已跳转到: {entry['action']}")
                    st.rerun()
        
        if i < len(st.session_state.outline_history) - 1:
            st.markdown("---")

# 全局状态管理
if 'outline_data' not in st.session_state:
    st.session_state.outline_data = None
if 'current_version' not in st.session_state:
    st.session_state.current_version = "test"
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = "preview"
# 历史记录系统
if 'outline_history' not in st.session_state:
    st.session_state.outline_history = []
if 'history_index' not in st.session_state:
    st.session_state.history_index = -1

# 角色生成系统 (集成在大纲生成器中)
if 'characters_data' not in st.session_state:
    st.session_state.characters_data = []

# 角色历史记录系统
if 'characters_history' not in st.session_state:
    st.session_state.characters_history = []
if 'characters_history_index' not in st.session_state:
    st.session_state.characters_history_index = -1

# 角色-章节关联数据
if 'character_chapter_mapping' not in st.session_state:
    st.session_state.character_chapter_mapping = {}  # {chapter_id: [character_names]}

# 故事生成系统
if 'story_data' not in st.session_state:
    st.session_state.story_data = []

# 故事历史记录系统
if 'story_history' not in st.session_state:
    st.session_state.story_history = []
if 'story_history_index' not in st.session_state:
    st.session_state.story_history_index = -1

# 对话生成系统
if 'dialogue_data' not in st.session_state:
    st.session_state.dialogue_data = []

# 对话历史记录系统
if 'dialogue_history' not in st.session_state:
    st.session_state.dialogue_history = []
if 'dialogue_history_index' not in st.session_state:
    st.session_state.dialogue_history_index = -1

# 故事增强系统
if 'enhanced_story_data' not in st.session_state:
    st.session_state.enhanced_story_data = {}

# 故事增强历史记录系统
if 'enhancement_history' not in st.session_state:
    st.session_state.enhancement_history = []
if 'enhancement_history_index' not in st.session_state:
    st.session_state.enhancement_history_index = -1



def main():
    st.title("📚 故事创作系统")
    
    # 显示创作流程步骤
    show_creation_progress()
    
    st.markdown("---")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置参数")
        
        topic = st.text_input("故事题材", value="小红帽", help="故事的主要题材")
        style = st.text_input("故事风格", value="科幻改写", help="故事的风格类型")
        temperature = st.slider("创造性", min_value=0.1, max_value=1.0, value=0.7, step=0.1)
        seed = st.number_input("随机种子", min_value=1, value=42, step=1)
        reorder_mode = st.selectbox("章节顺序", ["linear", "nonlinear"], help="linear=线性顺序, nonlinear=非线性重排")
        
        st.markdown("---")
        
        if st.button("🔄 生成新大纲", type="primary", use_container_width=True):
            generate_new_outline(topic, style, temperature, seed, reorder_mode)
        
        if st.button("📁 加载已有大纲", use_container_width=True):
            st.session_state.show_outline_loader = True
            st.rerun()
        
        st.markdown("---")
        st.markdown("**当前状态:**")
        if st.session_state.outline_data:
            st.success(f"✅ 已加载大纲 ({len(st.session_state.outline_data)} 章)")
        else:
            st.info("📝 未加载大纲")
        
        if st.session_state.characters_data:
            st.success(f"✅ 已生成角色 ({len(st.session_state.characters_data)} 个)")
        else:
            st.info("👥 未生成角色")
        
        # 建议管理
        st.markdown("---")
        st.markdown("### 💡 智能建议")
        
        if st.button("📂 管理保存的建议", use_container_width=True):
            st.session_state.show_suggestions_manager = True
            st.rerun()
        
        # 显示建议统计
        try:
            import os
            suggestions_dir = "data/saved_suggestions"
            if os.path.exists(suggestions_dir):
                suggestion_files = [f for f in os.listdir(suggestions_dir) if f.endswith('.json')]
                st.info(f"📊 已保存 {len(suggestion_files)} 个建议")
            else:
                st.info("📊 暂无已保存建议")
        except:
            pass
    
    # 显示执行日志
    if 'execution_logs' in st.session_state and st.session_state.execution_logs:
        show_execution_log(st.session_state.execution_logs)
    
    # 检查特殊界面显示
    if st.session_state.get('show_suggestions_manager', False):
        show_suggestions_manager()
        return
    
    # 主界面 - 根据当前步骤显示相应界面
    current_step = determine_current_step()
    
    if current_step == "welcome":
        show_welcome_screen()
    elif current_step == "outline":
        show_outline_editor()
    elif current_step == "characters":
        show_character_generation_interface()
    elif current_step == "story":
        show_story_generation_interface()
    elif current_step == "dialogue":
        show_dialogue_generation_interface()
    elif current_step == "enhance":
        show_story_enhancement_interface()

def show_creation_progress():
    """显示创作流程进度"""
    st.markdown("### 🎯 创作流程")
    
    # 确定当前步骤状态
    outline_status = "✅" if st.session_state.outline_data else "⏳"
    character_status = "✅" if st.session_state.characters_data else ("⏳" if st.session_state.outline_data else "⏸️")
    story_status = "⏸️"  # 未来扩展
    
    # 创建流程指示器 - 扩展为5步
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 0.3, 1.5, 0.3, 1.5, 0.3, 1.5, 0.3, 1.5])
    
    with col1:
        outline_color = "success" if outline_status == "✅" else ("warning" if outline_status == "⏳" else "secondary")
        if st.button(f"{outline_status} **步骤1: 大纲生成**", type="secondary" if outline_status != "⏳" else "primary", use_container_width=True):
            st.session_state.current_interface = "outline"
            st.rerun()
    
    with col2:
        st.markdown("<div style='text-align: center; padding-top: 8px;'>→</div>", unsafe_allow_html=True)
    
    with col3:
        character_disabled = not st.session_state.outline_data
        character_type = "secondary" if character_status == "✅" else ("primary" if character_status == "⏳" else "secondary")
        if st.button(f"{character_status} **步骤2: 角色生成**", type=character_type, disabled=character_disabled, use_container_width=True):
            st.session_state.current_interface = "characters"
            st.rerun()
    
    with col4:
        st.markdown("<div style='text-align: center; padding-top: 8px;'>→</div>", unsafe_allow_html=True)
    
    with col5:
        story_disabled = not (st.session_state.outline_data and st.session_state.characters_data)
        story_status = "✅" if st.session_state.get('story_data') else ("⏳" if (st.session_state.outline_data and st.session_state.characters_data) else "⏸️")
        story_type = "secondary" if story_status == "✅" else ("primary" if story_status == "⏳" else "secondary")
        if st.button(f"{story_status} **步骤3: 故事生成**", type=story_type, disabled=story_disabled, use_container_width=True):
            st.session_state.current_interface = "story"
            st.rerun()
    
    with col6:
        st.markdown("<div style='text-align: center; padding-top: 8px;'>→</div>", unsafe_allow_html=True)
    
    with col7:
        dialogue_disabled = not (st.session_state.outline_data and st.session_state.characters_data and st.session_state.get('story_data'))
        dialogue_status = "✅" if st.session_state.get('dialogue_data') else ("⏳" if (st.session_state.outline_data and st.session_state.characters_data and st.session_state.get('story_data')) else "⏸️")
        dialogue_type = "secondary" if dialogue_status == "✅" else ("primary" if dialogue_status == "⏳" else "secondary")
        if st.button(f"{dialogue_status} **步骤4: 对话生成**", type=dialogue_type, disabled=dialogue_disabled, use_container_width=True):
            st.session_state.current_interface = "dialogue"
            st.rerun()
    
    with col8:
        st.markdown("<div style='text-align: center; padding-top: 8px;'>→</div>", unsafe_allow_html=True)
    
    with col9:
        enhance_disabled = not (st.session_state.outline_data and st.session_state.characters_data and st.session_state.get('story_data') and st.session_state.get('dialogue_data'))
        enhance_status = "✅" if st.session_state.get('enhanced_story_data') else ("⏳" if (st.session_state.outline_data and st.session_state.characters_data and st.session_state.get('story_data') and st.session_state.get('dialogue_data')) else "⏸️")
        enhance_type = "secondary" if enhance_status == "✅" else ("primary" if enhance_status == "⏳" else "secondary")
        if st.button(f"{enhance_status} **步骤5: 故事增强**", type=enhance_type, disabled=enhance_disabled, use_container_width=True):
            st.session_state.current_interface = "enhance"
            st.rerun()
    
    # 显示当前步骤说明
    current_step = determine_current_step()
    if current_step == "welcome":
        st.info("🚀 **开始创作**：请先配置参数并生成故事大纲")
    elif current_step == "outline":
        st.info("📝 **大纲阶段**：编辑和完善你的故事大纲")
    elif current_step == "characters":
        st.info("👥 **角色阶段**：基于大纲生成和管理角色")
    elif current_step == "story":
        st.info("📖 **故事阶段**：基于大纲和角色生成详细故事内容")
    elif current_step == "dialogue":
        st.info("💬 **对话阶段**：基于故事内容生成角色对话")
    elif current_step == "enhance":
        st.info("✨ **增强阶段**：添加章节过渡和润色对话，生成完整小说")

def determine_current_step():
    """确定当前应该显示的步骤"""
    # 检查用户是否手动选择了界面
    if 'current_interface' in st.session_state:
        if st.session_state.current_interface == "outline" and st.session_state.outline_data:
            return "outline"
        elif st.session_state.current_interface == "characters" and st.session_state.outline_data:
            return "characters"
        elif st.session_state.current_interface == "story" and st.session_state.outline_data and st.session_state.characters_data:
            return "story"
        elif st.session_state.current_interface == "dialogue" and st.session_state.outline_data and st.session_state.characters_data and st.session_state.get('story_data'):
            return "dialogue"
        elif st.session_state.current_interface == "enhance" and st.session_state.outline_data and st.session_state.characters_data and st.session_state.get('story_data') and st.session_state.get('dialogue_data'):
            return "enhance"
    
    # 自动判断当前步骤
    if not st.session_state.outline_data:
        return "welcome"
    elif not st.session_state.characters_data:
        return "characters"  # 大纲完成后，自动进入角色生成阶段
    elif not st.session_state.get('story_data'):
        return "story"  # 角色完成后，自动进入故事生成阶段
    elif not st.session_state.get('dialogue_data'):
        return "dialogue"  # 故事完成后，自动进入对话生成阶段
    elif not st.session_state.get('enhanced_story_data'):
        return "enhance"  # 对话完成后，自动进入故事增强阶段
    else:
        return "enhance"  # 默认显示故事增强界面

def show_character_generation_interface():
    """显示角色生成界面 - 作为主流程步骤"""
    st.header("👥 步骤2: 角色生成")
    
    # 检查前置条件
    if not st.session_state.outline_data:
        st.error("❌ 请先完成步骤1: 生成故事大纲")
        return
    
    # 检查角色生成功能是否可用
    if not character_generation_available:
        st.error("❌ 角色生成功能不可用，请检查后端模块导入")
        return
    
    # 显示基于大纲的角色生成界面
    show_character_generation_mode()

def show_welcome_screen():
    """欢迎界面"""
    # 检查是否需要显示文件加载器
    if st.session_state.get('show_outline_loader', False):
        load_existing_outline()
        return
    
    st.markdown("""
    ## 🎯 欢迎使用故事创作系统！
    
    这是一个完整的故事创作工具，按照后端流程设计，包含以下主要步骤：
    """)
    
    # 显示完整的创作流程
    st.markdown("### 📋 完整创作流程")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📚 步骤1: 大纲生成**
        - 🚀 快速生成故事大纲
        - ✏️ 交互式编辑章节内容
        - 🔄 重新排列章节顺序
        - 📊 分析叙述结构
        - 💾 保存和导出结果
        """)
    
    with col2:
        st.markdown("""
        **👥 步骤2: 角色生成**
        - 🎭 基于大纲生成角色
        - 📝 管理角色设定
        - 🔗 分析角色与章节关联
        - 💾 保存角色数据
        - ✏️ 编辑角色信息
        """)
    
    with col3:
        st.markdown("""
        **📖 步骤3: 故事生成**
        - 📄 基于大纲扩展详细故事内容
        - 📋 章节摘要和逻辑连贯性检查
        - ✏️ 选择关键章节进行重写
        - 🎨 风格统一性确认和调整
        - 💾 保存和导出完整故事
        """)
    
    st.markdown("---")
    
    st.markdown("""
    **🚀 开始使用：**
    1. 在左侧配置故事参数（题材、风格等）
    2. 点击"生成新大纲"按钮开始创作
    3. 或者点击"加载已有大纲"按钮上传现有文件
    4. 完成大纲后，系统会自动引导你进入角色生成步骤
    """)
    
    # 快速开始按钮
    st.markdown("### 🚀 快速开始")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 加载已有大纲文件", type="secondary", use_container_width=True):
            st.session_state.show_outline_loader = True
            st.rerun()
    
    with col2:
        if st.button("🎭 查看示例格式", use_container_width=True):
            st.session_state.show_example_formats = True
            st.rerun()
    
    # 显示示例格式
    if st.session_state.get('show_example_formats', False):
        st.markdown("---")
        show_example_formats()
    
    # 示例大纲预览
    with st.expander("📖 查看示例大纲"):
        example_outline = [
            {"chapter_id": "Chapter 1", "title": "小红帽的科幻开端", "summary": "在一个充满科幻色彩的世界里，小红帽开始了她的奇异冒险。"},
            {"chapter_id": "Chapter 2", "title": "小红帽的科幻挑战", "summary": "小红帽面临着前所未有的科幻挑战，需要运用智慧和勇气。"},
            {"chapter_id": "Chapter 3", "title": "小红帽的科幻转折", "summary": "故事出现了意想不到的科幻转折，小红帽必须做出重要选择。"}
        ]
        
        for i, ch in enumerate(example_outline):
            st.markdown(f"**{ch['chapter_id']}: {ch['title']}**")
            st.markdown(f"*{ch['summary']}*")
            if i < len(example_outline) - 1:
                st.markdown("---")
    
    # 功能特色
    with st.expander("✨ 系统特色"):
        st.markdown("""
        **🎯 完整的创作流程：**
        - 📚 **智能大纲生成**：基于主题和风格自动生成结构化大纲
        - 🔄 **章节重排优化**：支持线性和非线性章节顺序
        - 👥 **角色智能生成**：基于大纲自动生成符合故事的角色设定
        - ✏️ **全面编辑功能**：支持大纲和角色的手动编辑、重新生成
        - 📊 **历史记录管理**：完整的撤销/重做/回滚功能
        - 💾 **数据持久化**：自动保存到项目目录，支持多格式导出
        """)
        
        st.info("💡 所有功能都基于真实的后端模块，确保生成质量和数据一致性")

def show_example_formats():
    """显示示例文件格式"""
    st.markdown("### 📄 文件格式示例")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📚 大纲文件格式 (JSON):**")
        outline_example = [
            {
                "chapter_id": "Chapter 1",
                "title": "章节标题",
                "summary": "章节摘要内容"
            },
            {
                "chapter_id": "Chapter 2", 
                "title": "第二章标题",
                "summary": "第二章摘要内容"
            }
        ]
        st.code(json.dumps(outline_example, ensure_ascii=False, indent=2), language="json")
    
    with col2:
        st.markdown("**👥 角色文件格式 (JSON):**")
        character_example = [
            {
                "name": "角色姓名",
                "role": "角色定位",
                "traits": "角色特征描述",
                "background": "角色背景故事",
                "motivation": "角色动机"
            }
        ]
        st.code(json.dumps(character_example, ensure_ascii=False, indent=2), language="json")
    
    if st.button("❌ 关闭示例", key="close_examples"):
        st.session_state.show_example_formats = False
        st.rerun()

def generate_new_outline(topic, style, temperature, seed, reorder_mode):
    """生成新大纲 - 完全按照main_pipeline_glm.py的逻辑"""
    
    # 清空之前的日志
    if 'execution_logs' not in st.session_state:
        st.session_state.execution_logs = []
    else:
        st.session_state.execution_logs.clear()
    
    with st.spinner("🔄 正在生成故事大纲..."):
        try:
            # Step 1: 构建版本名称 (按照main_pipeline_glm.py的逻辑)
            start_time = time.time()
            version = build_version_name(
                topic=topic,
                style=style,
                temperature=temperature,
                seed=seed,
                order_mode=reorder_mode
            )
            end_time = time.time()
            
            log_backend_operation(
                "构建版本名称", 
                {"topic": topic, "style": style, "temperature": temperature, "seed": seed, "order_mode": reorder_mode},
                start_time, end_time, version
            )
            
            st.info(f"📝 生成版本名称: {version}")
            
            # Step 2: Outline Generation (按照main_pipeline_glm.py第58-70行的逻辑)
            outline_base_path = os.path.join(output_dir, "reference_outline", f"{topic}_{style}_T{temperature}_s{seed}outline.json")
            os.makedirs(os.path.dirname(outline_base_path), exist_ok=True)
            
            start_time = time.time()
            if os.path.exists(outline_base_path):
                outline = load_json(outline_base_path)
                end_time = time.time()
                log_backend_operation(
                    "加载共享outline", 
                    {"path": outline_base_path},
                    start_time, end_time, outline
                )
                st.info(f"📖 已加载共享outline: {outline_base_path}")
            else:
                outline = generate_outline(topic=topic, style=style, custom_instruction="")
                end_time = time.time()
                log_backend_operation(
                    "生成新outline", 
                    {"topic": topic, "style": style, "custom_instruction": ""},
                    start_time, end_time, outline
                )
                
                # 保存outline
                save_start = time.time()
                save_json(outline, "reference_outline", f"{topic}_{style}_T{temperature}_s{seed}_outline.json")
                save_end = time.time()
                log_backend_operation(
                    "保存outline到共享目录", 
                    {"path": outline_base_path},
                    save_start, save_end, True
                )
                st.success(f"💾 生成并保存共享outline: {outline_base_path}")
            
            st.info(f"✅ Outline生成完成，共 {len(outline)} 章节")
            
            # Step 3: 章节重排处理 (按照main_pipeline_glm.py第92-185行的逻辑)
            reorder_outline_raw = None
            
            if reorder_mode == "linear":
                reorder_outline_raw = outline
                st.info("✅ 使用linear顺序（直接来自outline）")
                
            elif reorder_mode == "nonlinear":
                st.info("🔄 开始非线性重排处理...")
                
                # 保存线性版本
                save_start = time.time()
                save_json(outline, version, "test_outline_linear.json")
                save_end = time.time()
                log_backend_operation(
                    "保存线性outline", 
                    {"version": version},
                    save_start, save_end, True
                )
                
                # 检查缓存的非线性版本
                reorder_path = os.path.join(output_dir, "reference_reorder", f"{topic}_{style}_T{temperature}_s{seed}_nonlinear.json")
                os.makedirs(os.path.dirname(reorder_path), exist_ok=True)
                
                start_time = time.time()
                if os.path.exists(reorder_path):
                    reorder_outline_raw = load_json(reorder_path)
                    end_time = time.time()
                    log_backend_operation(
                        "加载cached非线性顺序", 
                        {"path": reorder_path},
                        start_time, end_time, reorder_outline_raw
                    )
                    st.success(f"✅ 已加载cached非线性顺序: {reorder_path}")
                else:
                    # Step 3.1: 章节重排
                    st.info("🔄 执行章节重排...")
                    reorder_outline_raw = reorder_chapters(outline, mode="nonlinear")
                    end_time = time.time()
                    log_backend_operation(
                        "执行章节重排", 
                        {"mode": "nonlinear", "original_chapters": len(outline)},
                        start_time, end_time, reorder_outline_raw
                    )
                    
                    # 检查重排是否成功 (按照main_pipeline_glm.py第122-141行)
                    if not any("new_order" in ch for ch in reorder_outline_raw):
                        st.warning("⚠️ LLM重排失败：未检测到任何new_order字段，回退为原始顺序")
                        reorder_mode = "linear"
                        reorder_outline_raw = outline
                        log_backend_operation(
                            "重排失败回退", 
                            {"reason": "无new_order字段"},
                            time.time(), time.time(), reorder_outline_raw
                        )
                    else:
                        st.success("✅ reorder_chapters成功生成非线性顺序")
                        
                        # Step 3.2: 叙述结构分析
                        st.info("🔍 开始叙述结构分析...")
                        analysis_start = time.time()
                        reorder_outline_raw = analyze_narrative_structure(
                            reorder_outline_raw, outline, topic=topic, style=style
                        )
                        analysis_end = time.time()
                        log_backend_operation(
                            "叙述结构分析", 
                            {"topic": topic, "style": style},
                            analysis_start, analysis_end, reorder_outline_raw
                        )
                        
                        # 显示分析结果
                        st.info("📖 叙述结构分析结果:")
                        for ch in reorder_outline_raw:
                            role = ch.get('narrative_role', '未分析')
                            st.text(f"  {ch['chapter_id']}: {role}")
                    
                    # 保存非线性版本
                    save_start = time.time()
                    save_json(reorder_outline_raw, "reference_reorder", f"{topic}_{style}_T{temperature}_s{seed}_nonlinear.json")
                    save_end = time.time()
                    log_backend_operation(
                        "保存非线性顺序到缓存", 
                        {"path": reorder_path},
                        save_start, save_end, True
                    )
                    st.success(f"✅ 生成nonlinear顺序并缓存: {reorder_path}")
            
            # Step 4: 统一结构处理 (按照main_pipeline_glm.py第155-185行)
            st.info("🔧 统一结构：补全summary字段，保留叙述分析字段...")
            merge_start = time.time()
            
            final_outline = []
            for reordered_ch in reorder_outline_raw:
                match = next((x for x in outline if x["chapter_id"] == reordered_ch["chapter_id"]), None)
                if match:
                    merged = {
                        "chapter_id": reordered_ch["chapter_id"],
                        "title": reordered_ch["title"],
                        "summary": match.get("summary", "")
                    }
                    
                    # 保留重排和叙述分析相关字段
                    narrative_fields = ["new_order", "narrative_role", "narrative_instruction", "transition_hint"]
                    for field in narrative_fields:
                        if field in reordered_ch:
                            merged[field] = reordered_ch[field]
                    
                    # 添加原始位置信息
                    merged["original_position"] = outline.index(match) + 1
                    
                    final_outline.append(merged)
            
            merge_end = time.time()
            log_backend_operation(
                "合并结构数据", 
                {"original_chapters": len(outline), "final_chapters": len(final_outline)},
                merge_start, merge_end, final_outline
            )
            
            # 保存最终结果
            save_start = time.time()
            save_json(final_outline, version, "test_reorder_outline.json")
            save_end = time.time()
            log_backend_operation(
                "保存最终大纲", 
                {"version": version, "filename": "test_reorder_outline.json"},
                save_start, save_end, True
            )
            
            # 显示最终结构
            if reorder_mode == "nonlinear":
                st.success("✅ 章节顺序处理完成（已保留summary和叙述指导）")
                st.info("🎭 最终章节结构:")
                for idx, ch in enumerate(final_outline):
                    role = ch.get('narrative_role', '线性叙述')
                    orig_pos = ch.get('original_position', '?')
                    st.text(f"  {idx+1}. {ch['chapter_id']} (原第{orig_pos}章) - {role}")
            else:
                st.success("✅ 章节顺序处理完成（已保留summary）")
            
            # 更新会话状态
            st.session_state.outline_data = final_outline
            st.session_state.current_version = version
            # 保存当前参数，用于后续的章节重新生成
            st.session_state.current_topic = topic
            st.session_state.current_style = style
            st.session_state.current_temperature = temperature
            st.session_state.current_seed = seed
            st.session_state.current_reorder_mode = reorder_mode
            
            # 保存初始状态到历史记录
            save_to_history("生成大纲")
            
            st.success(f"🎉 大纲生成完成！共 {len(final_outline)} 章")
            st.rerun()
            
        except Exception as e:
            error_time = time.time()
            log_backend_operation(
                "大纲生成失败", 
                {"topic": topic, "style": style, "reorder_mode": reorder_mode},
                error_time, error_time, None, e
            )
            st.error(f"❌ 大纲生成失败: {str(e)}")
            app_logger.error(f"Outline generation failed: {str(e)}")

def load_existing_outline():
    """加载已有大纲"""
    st.markdown("### 📁 加载已有大纲")
    uploaded_file = st.file_uploader("选择大纲文件", type=['json'], key="outline_upload")
    
    if uploaded_file is not None:
        try:
            # 显示文件信息
            st.info(f"📄 文件名: {uploaded_file.name}")
            st.info(f"📊 文件大小: {uploaded_file.size} bytes")
            
            # 重置文件指针到开始位置
            uploaded_file.seek(0)
            
            # 读取文件内容
            file_content = uploaded_file.read()
            
            # 如果是字节类型，转换为字符串
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # 解析JSON
            outline_data = json.loads(file_content)
            
            # 详细验证数据格式
            if not isinstance(outline_data, list):
                st.error("❌ 文件格式不正确：应为JSON数组格式")
                return
            
            if len(outline_data) == 0:
                st.error("❌ 文件内容为空：没有找到章节数据")
                return
            
            # 验证章节数据格式
            required_fields = ['chapter_id', 'title']
            for i, chapter in enumerate(outline_data):
                if not isinstance(chapter, dict):
                    st.error(f"❌ 第{i+1}个章节格式不正确：应为对象格式")
                    return
                
                missing_fields = [field for field in required_fields if field not in chapter]
                if missing_fields:
                    st.error(f"❌ 第{i+1}个章节缺少必要字段: {', '.join(missing_fields)}")
                    return
            
            # 保存加载前的状态到历史记录（如果有的话）
            if st.session_state.outline_data:
                save_to_history("加载新大纲前的状态", st.session_state.outline_data.copy())
            
            # 加载数据
            st.session_state.outline_data = outline_data
            st.session_state.current_version = f"loaded_{uploaded_file.name.replace('.json', '')}"
            
            # 保存加载后的状态到历史记录
            save_to_history("加载大纲")
            
            st.success(f"✅ 大纲加载成功！共 {len(outline_data)} 章")
            st.info("🔄 页面将自动刷新...")
            
            # 显示加载的章节预览
            with st.expander("📖 加载的章节预览", expanded=True):
                for i, chapter in enumerate(outline_data[:3]):  # 只显示前3章
                    st.text(f"{i+1}. {chapter.get('chapter_id', 'Unknown')}: {chapter.get('title', 'No Title')}")
                if len(outline_data) > 3:
                    st.text(f"... 还有 {len(outline_data) - 3} 章")
            
            # 清除加载器状态
            st.session_state.show_outline_loader = False
            
            st.rerun()
            
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON格式错误: {str(e)}")
            st.error("💡 请确保文件是有效的JSON格式")
        except UnicodeDecodeError as e:
            st.error(f"❌ 文件编码错误: {str(e)}")
            st.error("💡 请确保文件是UTF-8编码")
        except Exception as e:
            st.error(f"❌ 文件加载失败: {str(e)}")
            print(f"❌ [大纲加载] 加载失败: {str(e)}")
    else:
        st.info("💡 请选择一个JSON格式的大纲文件")

def show_outline_editor():
    """大纲编辑器界面"""
    st.header(f"📝 步骤1: 大纲编辑 - {st.session_state.current_version}")
    
    # 编辑模式选择
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("👀 预览模式", use_container_width=True):
            st.session_state.edit_mode = "preview"
            st.rerun()
    
    with col2:
        if st.button("✏️ 编辑模式", use_container_width=True):
            st.session_state.edit_mode = "edit"
            st.rerun()
    
    with col3:
        if st.button("🔄 重排模式", use_container_width=True):
            st.session_state.edit_mode = "reorder"
            st.rerun()
    
    with col4:
        if st.button("📋 历史记录", use_container_width=True):
            st.session_state.edit_mode = "history"
            st.rerun()
    
    with col5:
        if st.button("💾 保存导出", use_container_width=True):
            st.session_state.edit_mode = "export"
            st.rerun()
    
    st.markdown("---")
    
    # 根据模式显示不同界面
    if st.session_state.edit_mode == "preview":
        show_preview_mode()
    elif st.session_state.edit_mode == "edit":
        show_edit_mode()
    elif st.session_state.edit_mode == "reorder":
        show_reorder_mode()
    elif st.session_state.edit_mode == "history":
        show_history_panel()
    elif st.session_state.edit_mode == "export":
        show_export_mode()
    
    # 在大纲编辑器底部显示进入下一步的提示
    st.markdown("---")
    st.markdown("### ✅ 大纲编辑完成")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("💡 大纲编辑完成后，可以进入下一步：角色生成")
    
    with col2:
        if st.button("👥 进入角色生成", type="primary", use_container_width=True):
            st.session_state.current_interface = "characters"
            st.rerun()

def show_preview_mode():
    """预览模式"""
    st.subheader("👀 大纲预览")
    
    # 显示章节信息
    for i, chapter in enumerate(st.session_state.outline_data):
        with st.expander(f"**{chapter['chapter_id']}: {chapter['title']}**", expanded=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**摘要:** {chapter.get('summary', '无摘要')}")
                
                # 显示额外信息
                if 'original_position' in chapter:
                    st.info(f"📍 原位置: 第{chapter['original_position']}章")
                
                if 'narrative_role' in chapter:
                    st.success(f"🎭 叙述角色: {chapter['narrative_role']}")
                
                if 'narrative_instruction' in chapter:
                    st.warning(f"💡 叙述指导: {chapter['narrative_instruction']}")
                
                if 'transition_hint' in chapter:
                    st.info(f"🔗 过渡提示: {chapter['transition_hint']}")
            
            with col2:
                st.markdown(f"**位置:** {i+1}")
                if 'new_order' in chapter:
                    st.markdown(f"**新顺序:** {chapter['new_order']}")

def show_edit_mode():
    """编辑模式"""
    st.subheader("✏️ 章节编辑")
    
    # 批量选择
    st.markdown("**选择要编辑的章节:**")
    selected_chapters = st.multiselect(
        "选择章节",
        options=[f"{i+1}. {ch['title']}" for i, ch in enumerate(st.session_state.outline_data)],
        default=[]
    )
    
    if selected_chapters:
        st.markdown("---")
        
        # 编辑选中的章节
        for selection in selected_chapters:
            chapter_idx = int(selection.split('.')[0]) - 1
            chapter = st.session_state.outline_data[chapter_idx]
            
            st.markdown(f"### 📝 编辑第 {chapter_idx + 1} 章")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_title = st.text_input(
                    "章节标题",
                    value=chapter['title'],
                    key=f"title_{chapter_idx}"
                )
            
            with col2:
                new_chapter_id = st.text_input(
                    "章节ID",
                    value=chapter['chapter_id'],
                    key=f"id_{chapter_idx}"
                )
            
            new_summary = st.text_area(
                "章节摘要",
                value=chapter.get('summary', ''),
                height=100,
                key=f"summary_{chapter_idx}"
            )
            
            # 操作按钮
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 重新生成", key=f"regenerate_{chapter_idx}"):
                    regenerate_chapter(chapter_idx, chapter)
            
            with col2:
                if st.button("🗑️ 删除章节", key=f"delete_{chapter_idx}"):
                    # 保存删除前的状态到历史记录
                    save_to_history(f"删除第{chapter_idx + 1}章", st.session_state.outline_data.copy())
                    # 执行删除
                    deleted_chapter = st.session_state.outline_data.pop(chapter_idx)
                    st.success(f"✅ 已删除第 {chapter_idx + 1} 章: {deleted_chapter.get('title', '未知标题')}")
                    st.rerun()
            
            with col3:
                if st.button("✅ 保存修改", key=f"save_{chapter_idx}"):
                    save_chapter_edit(chapter_idx, new_title, new_chapter_id, new_summary)
            
            st.markdown("---")
    
    # 添加新章节
    st.markdown("### ➕ 添加新章节")
    with st.form("add_chapter_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            new_ch_title = st.text_input("新章节标题")
        
        with col2:
            # 插入位置选择
            insert_positions = ["末尾"] + [f"第{i+1}章前" for i in range(len(st.session_state.outline_data))]
            insert_position = st.selectbox("插入位置", insert_positions)
        
        new_ch_summary = st.text_area("新章节摘要", height=100)
        
        # 冲突检测选项
        enable_conflict_check = st.checkbox("🔍 启用内容冲突检测", value=True, help="检测新章节是否与现有大纲存在逻辑冲突")
        
        if st.form_submit_button("➕ 添加章节"):
            if new_ch_title and new_ch_summary:
                # 确定插入位置
                if insert_position == "末尾":
                    insert_idx = len(st.session_state.outline_data)
                else:
                    insert_idx = int(insert_position.split("第")[1].split("章前")[0]) - 1
                
                add_new_chapter(new_ch_title, new_ch_summary, insert_idx, enable_conflict_check)
            else:
                st.warning("请填写章节标题和摘要")

def show_reorder_mode():
    """重排模式"""
    st.subheader("🔄 章节重排")
    
    # 显示详细的顺序对比
    show_chapter_order_comparison()
    
    st.markdown("---")
    
    # 重排选项
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**自动重排:**")
        if st.button("🔄 非线性重排", use_container_width=True):
            perform_automatic_reorder()
        
        if st.button("📊 叙述结构分析", use_container_width=True):
            perform_narrative_analysis()
    
    with col2:
        st.markdown("**手动重排:**")
        st.markdown("输入新的章节顺序（用逗号分隔）:")
        new_order_input = st.text_input(
            "新顺序",
            value=",".join(str(i+1) for i in range(len(st.session_state.outline_data))),
            help="例如: 1,3,2,4,5"
        )
        
        if st.button("✅ 应用新顺序", use_container_width=True):
            apply_manual_reorder(new_order_input)

def show_character_generation_mode():
    """角色生成模式 - 作为独立步骤"""
    st.subheader("👥 角色生成与管理")
    
    # 检查是否需要显示角色文件加载器
    if st.session_state.get('show_character_loader', False):
        load_existing_characters()
        return
    
    # 检查是否有大纲数据
    if not st.session_state.outline_data:
        st.warning("⚠️ 请先生成故事大纲，然后再生成角色")
        return
    
    # 检查角色生成功能是否可用
    if not character_generation_available:
        st.error("❌ 角色生成功能不可用，请检查后端模块导入")
        return
    
    # 角色生成配置
    st.markdown("### ⚙️ 角色生成配置")
    col1, col2 = st.columns(2)
    
    with col1:
        max_characters = st.slider("最大角色数量", min_value=3, max_value=20, value=8, help="生成的角色数量上限")
        use_cache = st.checkbox("使用缓存", value=True, help="如果已有角色数据，是否直接加载", key="char_use_cache_checkbox")
    
    with col2:
        show_details = st.checkbox("显示详细信息", value=True, help="显示角色的完整信息", key="char_show_details_checkbox")
        auto_save = st.checkbox("自动保存", value=True, help="生成后自动保存到历史记录", key="char_auto_save_checkbox")
    
    st.markdown("---")
    
    # 角色生成按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎭 生成角色", type="primary", use_container_width=True):
            generate_characters_from_outline(max_characters, use_cache, auto_save)
    
    with col2:
        if st.button("🔄 重新生成", use_container_width=True):
            generate_characters_from_outline(max_characters, use_cache=False, auto_save=auto_save)
    
    with col3:
        if st.button("📁 加载角色", use_container_width=True):
            st.session_state.show_character_loader = True
            st.rerun()
    
    st.markdown("---")
    
    # 显示角色数据
    if st.session_state.characters_data:
        show_characters_display(show_details)
    else:
        st.info("📝 暂无角色数据，请点击'生成角色'按钮开始生成")
        
        # 调试信息
        st.info(f"🔍 调试: 当前角色数据状态 - {type(st.session_state.get('characters_data', None))}, 长度: {len(st.session_state.get('characters_data', []))}")
        
        # 提示用户开始生成角色
        st.info("💡 点击上方'生成角色'按钮开始基于大纲生成角色")

def generate_characters_from_outline(max_characters=8, use_cache=True, auto_save=True):
    """从大纲生成角色 - 集成版本"""
    try:
        # 检查缓存
        if use_cache and st.session_state.characters_data:
            st.success("✅ 使用缓存的角色数据")
            return
        
        with st.spinner("🎭 正在生成角色..."):
            # 记录开始时间
            start_time = time.time()
            
            # 在终端显示后端调用信息
            print(f"📊 [大纲生成器集成] 调用后端模块: src.generation.generate_characters.generate_characters_v1")
            print(f"📝 [大纲生成器集成] 输入参数: 大纲章节数={len(st.session_state.outline_data)}, 最大角色数={max_characters}")
            
            # 调用真实后端函数
            characters = generate_characters_v1(st.session_state.outline_data, max_characters=max_characters)
            
            # 记录结束时间
            end_time = time.time()
            
            # 在终端显示结果
            print(f"⏱️ [大纲生成器集成] 生成耗时: {end_time - start_time:.3f}秒")
            print(f"🎉 [大纲生成器集成] 角色生成完成！共生成 {len(characters) if characters else 0} 个角色")
            
            # 验证生成结果
            if not characters or not isinstance(characters, list):
                st.error("❌ 角色生成失败：后端返回数据格式不正确")
                print(f"❌ [大纲生成器集成] 后端返回数据格式错误: {type(characters)} - {str(characters)[:200]}...")
                return
            
            # 保存到会话状态
            st.session_state.characters_data = characters
            
            # 在终端显示角色名单
            character_names = [char.get('name', '未知角色') for char in characters]
            print(f"👥 [大纲生成器集成] 生成的角色: {', '.join(character_names)}")
            
            # 自动保存到历史记录
            if auto_save:
                save_characters_to_history("生成角色")
            
            # 自动关联角色到大纲章节
            print("🔗 [角色管理] 角色生成完成，开始自动关联到大纲章节")
            auto_relink_characters_to_outline()
            
            # 显示成功信息
            st.success(f"🎉 角色生成完成！共生成 {len(characters)} 个角色")
            st.info(f"⏱️ 生成耗时: {end_time - start_time:.3f}秒")
            
            # 显示角色名单
            st.info(f"👥 生成的角色: {', '.join(character_names)}")
            
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 角色生成失败: {str(e)}")
        print(f"❌ [大纲生成器集成] 角色生成失败: {str(e)}")

def load_existing_characters():
    """加载已有角色文件 - 集成版本"""
    st.markdown("### 📁 加载已有角色")
    
    # 添加返回按钮
    if st.button("← 返回角色管理"):
        st.session_state.show_character_loader = False
        st.rerun()
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader("选择角色文件", type=['json'], key="character_upload")
    
    if uploaded_file is not None:
        try:
            # 显示文件信息
            st.info(f"📄 文件名: {uploaded_file.name}")
            st.info(f"📊 文件大小: {uploaded_file.size} bytes")
            
            # 重置文件指针到开始位置
            uploaded_file.seek(0)
            
            # 读取文件内容
            file_content = uploaded_file.read()
            
            # 如果是字节类型，转换为字符串
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # 解析JSON
            characters_data = json.loads(file_content)
            
            # 详细验证数据格式
            if not isinstance(characters_data, list):
                st.error("❌ 文件格式不正确：应为JSON数组格式")
                return
            
            if len(characters_data) == 0:
                st.error("❌ 文件内容为空：没有找到角色数据")
                return
            
            # 验证角色数据格式
            required_fields = ['name', 'role', 'traits', 'background', 'motivation']
            for i, character in enumerate(characters_data):
                if not isinstance(character, dict):
                    st.error(f"❌ 第{i+1}个角色格式不正确：应为对象格式")
                    return
                
                missing_fields = [field for field in required_fields if field not in character]
                if missing_fields:
                    st.error(f"❌ 第{i+1}个角色缺少必要字段: {', '.join(missing_fields)}")
                    return
            
            # 保存加载前的状态到历史记录（如果有的话）
            if st.session_state.characters_data:
                save_characters_to_history("加载新角色前的状态", st.session_state.characters_data.copy())
            
            # 加载数据
            st.session_state.characters_data = characters_data
            
            # 保存加载后的状态到历史记录
            save_characters_to_history("加载角色")
            
            st.success(f"✅ 角色数据加载成功！共 {len(characters_data)} 个角色")
            st.info("🔄 页面将自动刷新...")
            
            # 显示加载的角色预览
            with st.expander("👥 加载的角色预览", expanded=True):
                for i, character in enumerate(characters_data[:3]):  # 只显示前3个角色
                    name = character.get('name', '未知角色')
                    role = character.get('role', '未知角色')
                    st.text(f"{i+1}. {name} - {role}")
                if len(characters_data) > 3:
                    st.text(f"... 还有 {len(characters_data) - 3} 个角色")
            
            # 自动重新关联大纲
            if st.session_state.outline_data:
                auto_relink_characters_to_outline()
                st.info("🔗 已自动重新关联角色到大纲章节")
            
            print(f"📁 [角色管理] 加载角色文件: {len(characters_data)} 个角色")
            
            # 清除加载器状态
            st.session_state.show_character_loader = False
            
            st.rerun()
            
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON格式错误: {str(e)}")
            st.error("💡 请确保文件是有效的JSON格式")
        except UnicodeDecodeError as e:
            st.error(f"❌ 文件编码错误: {str(e)}")
            st.error("💡 请确保文件是UTF-8编码")
        except Exception as e:
            st.error(f"❌ 文件加载失败: {str(e)}")
            print(f"❌ [角色管理] 加载失败: {str(e)}")
    else:
        st.info("💡 请选择一个JSON格式的角色文件")

def show_characters_display(show_details=True):
    """显示角色信息 - 集成版本"""
    # 检查是否进入编辑模式
    if st.session_state.get('character_edit_mode', False):
        show_character_edit_mode()
        return
    
    # 检查是否显示一致性检查界面
    if st.session_state.get('show_consistency_check', False):
        show_character_consistency_check()
        return
    
    # 检查是否显示关系网络界面
    if st.session_state.get('show_character_relationships', False):
        show_character_relationships()
        return
    
    st.markdown("### 👥 角色列表")
    
    characters = st.session_state.characters_data
    
    # 角色统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("角色总数", len(characters))
    with col2:
        roles = [char.get('role', '未知') for char in characters]
        unique_roles = len(set(roles))
        st.metric("角色类型", unique_roles)
    with col3:
        avg_traits_length = sum(len(char.get('traits', '')) for char in characters) // len(characters) if characters else 0
        st.metric("平均特征长度", f"{avg_traits_length}字")
    
    st.markdown("---")
    
    # 角色详细信息
    for i, character in enumerate(characters):
        with st.expander(f"**{character.get('name', f'角色{i+1}')}** - {character.get('role', '未知角色')}", expanded=False):
            
            if show_details:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**👤 姓名:** {character.get('name', '未知')}")
                    st.markdown(f"**🎭 角色:** {character.get('role', '未知')}")
                    st.markdown(f"**💡 动机:** {character.get('motivation', '未知')}")
                
                with col2:
                    st.markdown(f"**✨ 特征:**")
                    st.markdown(f"*{character.get('traits', '无描述')}*")
                    
                    st.markdown(f"**📚 背景:**")
                    st.markdown(f"*{character.get('background', '无背景')}*")
            else:
                # 简化显示
                st.markdown(f"**角色:** {character.get('role', '未知')} | **特征:** {character.get('traits', '无')[:50]}...")
    
    # 角色管理操作
    st.markdown("---")
    st.markdown("### 🛠️ 角色管理")
    
    # 第一行按钮
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("💾 保存角色", use_container_width=True):
            save_characters_to_project()
    
    with col2:
        if st.button("📝 编辑角色", use_container_width=True):
            st.session_state.character_edit_mode = True
            st.rerun()
    
    with col3:
        if st.button("🔗 关联大纲", use_container_width=True):
            link_characters_to_outline()
    
    with col4:
        if st.button("📋 角色历史", use_container_width=True):
            st.session_state.show_character_history = True
            st.rerun()
    
    with col5:
        if st.button("🗑️ 清空角色", use_container_width=True):
            if st.button("⚠️ 确认清空", key="confirm_clear_characters"):
                save_characters_to_history("清空角色", st.session_state.characters_data.copy())
                st.session_state.characters_data = []
                st.session_state.character_chapter_mapping = {}
                st.success("✅ 角色数据已清空")
                print("🗑️ [角色管理] 清空角色数据")
                st.rerun()
    
    # 第二行按钮 - 新增功能
    st.markdown("### 🔍 角色分析")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🎯 一致性检查", use_container_width=True, help="检查角色设定与故事大纲的一致性"):
            st.session_state.show_consistency_check = True
            st.rerun()
    
    with col2:
        if st.button("🕸️ 关系网络", use_container_width=True, help="分析和展示角色间的关系"):
            st.session_state.show_character_relationships = True
            st.rerun()
    
    with col3:
        # 预留空间用于未来扩展
        st.empty()
    
    # 显示角色历史记录面板
    if st.session_state.get('show_character_history', False):
        show_character_history_panel()

def save_characters_to_project():
    """保存角色到项目目录 - 集成版本"""
    try:
        if not st.session_state.characters_data:
            st.warning("⚠️ 没有角色数据可保存")
            return
        
        start_time = time.time()
        # 使用真实后端的保存功能
        save_json(st.session_state.characters_data, st.session_state.current_version, "characters.json")
        end_time = time.time()
        
        st.success(f"✅ 角色已保存到项目目录: {st.session_state.current_version}/characters.json")
        print(f"💾 [大纲生成器集成] 保存角色到项目: {st.session_state.current_version}/characters.json ({len(st.session_state.characters_data)} 个角色)")
        
    except Exception as e:
        st.error(f"❌ 保存失败: {str(e)}")
        print(f"❌ [大纲生成器集成] 保存角色失败: {str(e)}")

def auto_relink_characters_to_outline():
    """自动重新关联角色到大纲章节 - 使用后端智能分析"""
    if not st.session_state.characters_data or not st.session_state.outline_data:
        print("⚠️ [角色关联] 缺少角色或大纲数据，跳过自动关联")
        return False
    
    print("🔗 [角色管理] 开始智能分析角色-章节关联")
    
    # 首先尝试智能分析
    try:
        # 使用后端的智能分析能力
        from src.utils.utils import generate_response, convert_json
        
        # 构建分析请求
        characters_info = []
        for char in st.session_state.characters_data:
            char_info = f"角色：{char.get('name', '未知')} - {char.get('role', '未知角色')}"
            if char.get('traits'):
                char_info += f"，特征：{char.get('traits')}"
            characters_info.append(char_info)
        
        chapters_info = []
        for chapter in st.session_state.outline_data:
            chapter_info = f"{chapter['chapter_id']}: {chapter['title']}"
            if chapter.get('summary'):
                chapter_info += f" - {chapter['summary']}"
            chapters_info.append(chapter_info)
        
        # 构建智能分析提示
        analysis_prompt = f"""
你是一位故事分析专家。请分析以下角色在各个章节中的出现情况。

角色列表：
{chr(10).join(characters_info)}

章节列表：
{chr(10).join(chapters_info)}

请分析每个角色最可能在哪些章节中出现，基于：
1. 角色的定位和特征
2. 章节的内容和情节发展
3. 故事的逻辑结构

返回JSON格式，格式如下：
{{
    "Chapter 1": ["角色名1", "角色名2"],
    "Chapter 2": ["角色名1"],
    ...
}}

只返回JSON，不要其他解释。
"""
        
        # 调用后端分析
        start_time = time.time()
        print(f"📊 [角色关联] 调用后端智能分析...")
        
        msg = [{"role": "user", "content": analysis_prompt}]
        response = generate_response(msg)
        analysis_result = convert_json(response)
        
        end_time = time.time()
        print(f"⏱️ [角色关联] 智能分析耗时: {end_time - start_time:.3f}秒")
        
        if not analysis_result or not isinstance(analysis_result, dict):
            print("⚠️ [角色关联] 智能分析结果格式不正确，使用简单匹配")
            return simple_character_matching()
        
        # 更新关联映射
        st.session_state.character_chapter_mapping = {}
        total_links = 0
        
        for chapter_id, character_names in analysis_result.items():
            if isinstance(character_names, list):
                # 验证角色名称是否存在
                valid_characters = []
                all_char_names = [char.get('name', '') for char in st.session_state.characters_data]
                
                for char_name in character_names:
                    if char_name in all_char_names:
                        valid_characters.append(char_name)
                
                st.session_state.character_chapter_mapping[chapter_id] = valid_characters
                total_links += len(valid_characters)
        
        print(f"🎉 [角色关联] 智能分析完成: {total_links} 个关联")
        return True
        
    except Exception as e:
        print(f"❌ [角色关联] 智能分析失败: {str(e)}")
        print("🔄 [角色关联] 回退到简单匹配方案")
        return simple_character_matching()

def simple_character_matching():
    """简单的字符串匹配作为备选方案"""
    print("🔄 [角色关联] 使用简单匹配备选方案")
    
    # 重置关联映射
    st.session_state.character_chapter_mapping = {}
    
    # 获取所有角色名称
    character_names = [char.get('name', '') for char in st.session_state.characters_data]
    total_links = 0
    
    # 为每个章节分析相关角色
    for chapter in st.session_state.outline_data:
        chapter_id = chapter['chapter_id']
        chapter_text = f"{chapter['title']} {chapter.get('summary', '')}".lower()
        
        related_characters = []
        for char_name in character_names:
            if char_name.lower() in chapter_text:
                related_characters.append(char_name)
        
        st.session_state.character_chapter_mapping[chapter_id] = related_characters
        total_links += len(related_characters)
    
    print(f"✅ [角色关联] 简单匹配完成: {total_links} 个关联")
    return True

def link_characters_to_outline():
    """关联角色到大纲章节 - 手动管理版本"""
    st.markdown("### 🔗 角色-章节关联管理")
    
    if not st.session_state.characters_data:
        st.warning("⚠️ 请先生成角色")
        return
    
    if not st.session_state.outline_data:
        st.warning("⚠️ 请先生成大纲")
        return
    
    # 调试信息
    current_mapping = st.session_state.get('character_chapter_mapping', {})
    total_current_links = sum(len(chars) for chars in current_mapping.values())
    st.info(f"🔍 调试信息: 当前有 {len(st.session_state.characters_data)} 个角色, {len(st.session_state.outline_data)} 个章节, {total_current_links} 个关联")
    
    # 自动分析按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 智能分析关联", use_container_width=True):
            with st.spinner("🔍 正在进行智能分析..."):
                try:
                    success = auto_relink_characters_to_outline()
                    
                    # 统计关联结果
                    total_links = sum(len(chars) for chars in st.session_state.character_chapter_mapping.values())
                    
                    if success and total_links > 0:
                        st.success(f"✅ 智能分析完成！共建立 {total_links} 个角色-章节关联")
                        
                        # 显示分析结果预览
                        with st.expander("📊 查看分析结果", expanded=True):
                            for chapter_id, characters in st.session_state.character_chapter_mapping.items():
                                if characters:
                                    chapter_title = next((ch['title'] for ch in st.session_state.outline_data if ch['chapter_id'] == chapter_id), chapter_id)
                                    st.info(f"**{chapter_title}**: {', '.join(characters)}")
                    elif success and total_links == 0:
                        st.warning("⚠️ 智能分析完成，但未找到明显的角色-章节关联，建议手动设置")
                    else:
                        st.error("❌ 智能分析失败，请检查角色和大纲数据")
                        
                except Exception as e:
                    st.error(f"❌ 分析过程出错: {str(e)}")
                    print(f"❌ [角色关联] 按钮处理出错: {str(e)}")
            
            st.rerun()
    
    with col2:
        if st.button("🗑️ 清空所有关联", use_container_width=True):
            # 统计当前关联数量
            current_links = sum(len(chars) for chars in st.session_state.character_chapter_mapping.values())
            
            st.session_state.character_chapter_mapping = {}
            
            if current_links > 0:
                st.success(f"✅ 已清空 {current_links} 个角色-章节关联")
                print(f"🗑️ [角色管理] 清空所有关联: {current_links} 个")
            else:
                st.info("ℹ️ 当前没有角色-章节关联需要清空")
            
            st.rerun()
    
    st.markdown("---")
    
    # 获取角色名称列表
    character_names = [char.get('name', '') for char in st.session_state.characters_data]
    
    # 为每个章节手动管理角色关联
    st.markdown("### 📝 手动管理章节角色")
    
    for i, chapter in enumerate(st.session_state.outline_data):
        chapter_id = chapter['chapter_id']
        
        with st.expander(f"**第{i+1}章: {chapter['title']}**", expanded=False):
            st.markdown(f"**摘要:** {chapter.get('summary', '无摘要')}")
            
            # 当前关联的角色
            current_characters = st.session_state.character_chapter_mapping.get(chapter_id, [])
            
            # 多选框让用户选择该章节的角色
            selected_characters = st.multiselect(
                f"选择第{i+1}章中出现的角色:",
                options=character_names,
                default=current_characters,
                key=f"chapter_{chapter_id}_characters"
            )
            
            # 更新关联
            if selected_characters != current_characters:
                st.session_state.character_chapter_mapping[chapter_id] = selected_characters
                st.info(f"✅ 第{i+1}章角色关联已更新")
            
            # 显示当前关联状态
            if selected_characters:
                st.success(f"📋 关联角色: {', '.join(selected_characters)}")
            else:
                st.info("📋 暂无关联角色")
    
    # 显示关联统计
    st.markdown("---")
    st.markdown("### 📊 关联统计")
    
    # 统计每个角色出现在多少章节中
    character_chapter_count = {}
    for char_name in character_names:
        count = sum(1 for characters in st.session_state.character_chapter_mapping.values() if char_name in characters)
        character_chapter_count[char_name] = count
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**角色出现频率:**")
        for char_name, count in character_chapter_count.items():
            if count > 0:
                st.text(f"👤 {char_name}: {count} 章节")
            else:
                st.text(f"👻 {char_name}: 未出现")
    
    with col2:
        st.markdown("**章节角色数量:**")
        for i, chapter in enumerate(st.session_state.outline_data):
            chapter_id = chapter['chapter_id']
            char_count = len(st.session_state.character_chapter_mapping.get(chapter_id, []))
            st.text(f"📖 第{i+1}章: {char_count} 个角色")

def show_character_history_panel():
    """显示角色历史记录面板"""
    st.markdown("---")
    st.markdown("### 📋 角色操作历史")
    
    # 关闭历史面板按钮
    if st.button("❌ 关闭历史面板"):
        st.session_state.show_character_history = False
        st.rerun()
    
    if not st.session_state.characters_history:
        st.info("📝 暂无角色历史记录")
        return
    
    # 撤销/重做按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("↶ 撤销角色操作", use_container_width=True, disabled=st.session_state.characters_history_index <= 0):
            if undo_characters_action():
                st.rerun()
    
    with col2:
        if st.button("↷ 重做角色操作", use_container_width=True, disabled=st.session_state.characters_history_index >= len(st.session_state.characters_history) - 1):
            if redo_characters_action():
                st.rerun()
    
    with col3:
        if st.button("🗑️ 清空角色历史", use_container_width=True):
            st.session_state.characters_history = []
            st.session_state.characters_history_index = -1
            st.success("✅ 角色历史记录已清空")
            st.rerun()
    
    st.markdown("---")
    
    # 显示历史记录列表
    st.markdown("**角色操作历史:**")
    
    for i, entry in enumerate(reversed(st.session_state.characters_history)):
        real_index = len(st.session_state.characters_history) - 1 - i
        is_current = real_index == st.session_state.characters_history_index
        
        # 创建历史记录条目
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                status = "🔵" if is_current else "⚪"
                st.markdown(f"{status} `{entry['timestamp']}`")
            
            with col2:
                st.markdown(f"**{entry['action']}**")
                character_count = len(entry['characters_data']) if entry['characters_data'] else 0
                st.caption(f"共 {character_count} 个角色")
            
            with col3:
                if st.button("📍", key=f"goto_char_{real_index}", help="跳转到此状态"):
                    st.session_state.characters_history_index = real_index
                    st.session_state.characters_data = copy.deepcopy(entry['characters_data'])
                    st.session_state.character_chapter_mapping = copy.deepcopy(entry['character_chapter_mapping'])
                    st.success(f"✅ 已跳转到: {entry['action']}")
                    st.rerun()
        
        if i < len(st.session_state.characters_history) - 1:
            st.markdown("---")

def show_story_history_panel():
    """显示故事历史记录面板"""
    st.markdown("---")
    st.markdown("### 📋 故事操作历史")
    
    # 关闭历史面板按钮
    if st.button("❌ 关闭历史面板"):
        st.session_state.show_story_history = False
        st.rerun()
    
    if not st.session_state.story_history:
        st.info("📝 暂无故事历史记录")
        return
    
    # 撤销/重做按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("↶ 撤销故事操作", use_container_width=True, disabled=st.session_state.story_history_index <= 0):
            if undo_story_action():
                st.rerun()
    
    with col2:
        if st.button("↷ 重做故事操作", use_container_width=True, disabled=st.session_state.story_history_index >= len(st.session_state.story_history) - 1):
            if redo_story_action():
                st.rerun()
    
    with col3:
        if st.button("🗑️ 清空故事历史", use_container_width=True):
            st.session_state.story_history = []
            st.session_state.story_history_index = -1
            st.success("✅ 故事历史记录已清空")
            st.rerun()
    
    st.markdown("---")
    
    # 显示历史记录列表
    st.markdown("**故事操作历史:**")
    
    for i, entry in enumerate(reversed(st.session_state.story_history)):
        real_index = len(st.session_state.story_history) - 1 - i
        is_current = real_index == st.session_state.story_history_index
        
        # 创建历史记录条目
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                status = "🔵" if is_current else "⚪"
                st.markdown(f"{status} `{entry['timestamp']}`")
            
            with col2:
                st.markdown(f"**{entry['action']}**")
                story_count = len(entry['story_data']) if entry['story_data'] else 0
                total_words = sum(len(ch.get('plot', '')) for ch in entry['story_data']) if entry['story_data'] else 0
                st.caption(f"共 {story_count} 个章节, {total_words} 字")
            
            with col3:
                if st.button("📍", key=f"goto_story_{real_index}", help="跳转到此状态"):
                    st.session_state.story_history_index = real_index
                    st.session_state.story_data = copy.deepcopy(entry['story_data'])
                    st.success(f"✅ 已跳转到: {entry['action']}")
                    st.rerun()
        
        if i < len(st.session_state.story_history) - 1:
            st.markdown("---")

def show_character_edit_mode():
    """角色编辑模式 - 参考大纲编辑的方式"""
    st.markdown("### ✏️ 角色编辑模式")
    
    # 退出编辑模式按钮
    if st.button("← 返回角色列表"):
        st.session_state.character_edit_mode = False
        st.rerun()
    
    st.markdown("---")
    
    # 批量选择要编辑的角色
    st.markdown("**选择要编辑的角色:**")
    selected_characters = st.multiselect(
        "选择角色",
        options=[f"{i+1}. {char.get('name', f'角色{i+1}')}" for i, char in enumerate(st.session_state.characters_data)],
        default=[]
    )
    
    if selected_characters:
        st.markdown("---")
        
        # 编辑选中的角色
        for selection in selected_characters:
            character_idx = int(selection.split('.')[0]) - 1
            character = st.session_state.characters_data[character_idx]
            
            st.markdown(f"### 📝 编辑角色 {character_idx + 1}: {character.get('name', '未知角色')}")
            
            # 角色基本信息编辑
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input(
                    "角色姓名",
                    value=character.get('name', ''),
                    key=f"char_name_{character_idx}"
                )
                
                new_role = st.text_input(
                    "角色定位",
                    value=character.get('role', ''),
                    key=f"char_role_{character_idx}"
                )
            
            with col2:
                new_traits = st.text_area(
                    "角色特征",
                    value=character.get('traits', ''),
                    height=80,
                    key=f"char_traits_{character_idx}"
                )
            
            # 角色详细信息编辑
            col1, col2 = st.columns(2)
            
            with col1:
                new_background = st.text_area(
                    "角色背景",
                    value=character.get('background', ''),
                    height=100,
                    key=f"char_background_{character_idx}"
                )
            
            with col2:
                new_motivation = st.text_area(
                    "角色动机",
                    value=character.get('motivation', ''),
                    height=100,
                    key=f"char_motivation_{character_idx}"
                )
            
            # 操作按钮
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 重新生成此角色", key=f"regenerate_char_{character_idx}"):
                    regenerate_single_character(character_idx)
            
            with col2:
                if st.button("🗑️ 删除角色", key=f"delete_char_{character_idx}"):
                    # 保存删除前的状态到历史记录
                    save_characters_to_history(f"删除角色: {character.get('name', f'角色{character_idx+1}')}", st.session_state.characters_data.copy())
                    # 执行删除
                    deleted_character = st.session_state.characters_data.pop(character_idx)
                    st.success(f"✅ 已删除角色: {deleted_character.get('name', '未知角色')}")
                    
                    # 删除后自动重新关联大纲
                    auto_relink_characters_to_outline()
                    
                    st.rerun()
            
            with col3:
                if st.button("✅ 保存修改", key=f"save_char_{character_idx}"):
                    save_character_edit(character_idx, new_name, new_role, new_traits, new_background, new_motivation)
            
            st.markdown("---")
    
    # 添加新角色
    st.markdown("### ➕ 添加新角色")
    with st.form("add_character_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_char_name = st.text_input("角色姓名")
            new_char_role = st.text_input("角色定位")
            new_char_traits = st.text_area("角色特征", height=80)
        
        with col2:
            new_char_background = st.text_area("角色背景", height=80)
            new_char_motivation = st.text_area("角色动机", height=80)
        
        if st.form_submit_button("➕ 添加角色"):
            if new_char_name and new_char_role:
                add_new_character(new_char_name, new_char_role, new_char_traits, new_char_background, new_char_motivation)
            else:
                st.warning("请至少填写角色姓名和角色定位")

def regenerate_single_character(character_idx):
    """重新生成单个角色 - 基于当前角色特征重新生成"""
    try:
        character = st.session_state.characters_data[character_idx]
        
        with st.spinner(f"🔄 正在重新生成角色: {character.get('name', f'角色{character_idx+1}')}..."):
            # 记录开始时间
            start_time = time.time()
            
            # 在终端显示后端调用信息
            print(f"📊 [角色编辑] 调用后端模块: src.generation.generate_characters.generate_characters_v1")
            print(f"📝 [角色编辑] 重新生成单个角色: {character.get('name', '未知角色')}")
            
            # 构建针对当前角色的重新生成指令
            current_name = character.get('name', '未知角色')
            current_role = character.get('role', '未知角色')
            
            # 创建一个临时大纲，包含对当前角色的特殊指令
            temp_outline = copy.deepcopy(st.session_state.outline_data)
            
            # 为大纲添加角色重新生成的特殊指令
            character_regeneration_instruction = f"""
请重新生成角色"{current_name}"（{current_role}）。
要求：
1. 保持角色在故事中的基本作用和定位
2. 可以改变具体的特征、背景和动机
3. 名字可以变化，但角色类型要保持一致
4. 确保与故事大纲的整体风格一致
"""
            
            # 调用后端重新生成所有角色，但我们只使用对应位置的角色
            new_characters = generate_characters_v1(temp_outline, max_characters=len(st.session_state.characters_data))
            
            # 记录结束时间
            end_time = time.time()
            
            # 验证生成结果
            if not new_characters or not isinstance(new_characters, list) or len(new_characters) <= character_idx:
                st.error("❌ 角色重新生成失败：后端返回数据不足")
                return
            
            # 保存重新生成前的状态到历史记录
            old_characters_data = st.session_state.characters_data.copy()
            save_characters_to_history(f"重新生成角色: {character.get('name', f'角色{character_idx+1}')}", old_characters_data)
            
            # 替换角色数据
            st.session_state.characters_data[character_idx] = new_characters[character_idx]
            
            # 在终端显示结果
            new_name = new_characters[character_idx].get('name', '未知角色')
            print(f"⏱️ [角色编辑] 生成耗时: {end_time - start_time:.3f}秒")
            print(f"🎉 [角色编辑] 角色重新生成完成: {current_name} → {new_name}")
            
            st.success(f"✅ 角色重新生成完成: {current_name} → {new_name}")
            st.info(f"⏱️ 生成耗时: {end_time - start_time:.3f}秒")
            
            # 重新生成后自动关联大纲
            auto_relink_characters_to_outline()
            
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 角色重新生成失败: {str(e)}")
        print(f"❌ [角色编辑] 角色重新生成失败: {str(e)}")

def save_character_edit(character_idx, new_name, new_role, new_traits, new_background, new_motivation):
    """保存角色编辑"""
    # 保存编辑前的状态到历史记录
    old_characters_data = st.session_state.characters_data.copy()
    save_characters_to_history(f"编辑角色: {st.session_state.characters_data[character_idx].get('name', f'角色{character_idx+1}')}", old_characters_data)
    
    # 执行编辑
    st.session_state.characters_data[character_idx]['name'] = new_name
    st.session_state.characters_data[character_idx]['role'] = new_role
    st.session_state.characters_data[character_idx]['traits'] = new_traits
    st.session_state.characters_data[character_idx]['background'] = new_background
    st.session_state.characters_data[character_idx]['motivation'] = new_motivation
    
    st.success(f"✅ 角色 {new_name} 修改已保存")
    print(f"💾 [角色编辑] 保存角色修改: {new_name}")
    
    # 自动重新关联大纲
    auto_relink_characters_to_outline()

def add_new_character(name, role, traits, background, motivation):
    """添加新角色"""
    try:
        # 保存添加前的状态到历史记录
        old_characters_data = st.session_state.characters_data.copy()
        save_characters_to_history(f"添加新角色: {name}", old_characters_data)
        
        # 创建新角色
        new_character = {
            "name": name,
            "role": role,
            "traits": traits,
            "background": background,
            "motivation": motivation
        }
        
        # 添加到角色列表
        st.session_state.characters_data.append(new_character)
        
        st.success(f"✅ 新角色已添加: {name}")
        print(f"➕ [角色编辑] 添加新角色: {name}")
        
        # 显示角色列表预览
        st.info("📋 当前角色列表:")
        for i, char in enumerate(st.session_state.characters_data):
            marker = "🆕" if i == len(st.session_state.characters_data) - 1 else "👤"
            st.text(f"  {marker} {i+1}. {char.get('name', '未知角色')}")
        
        # 自动重新关联大纲
        auto_relink_characters_to_outline()
        
    except Exception as e:
        st.error(f"❌ 添加角色失败: {str(e)}")
        print(f"❌ [角色编辑] 添加角色失败: {str(e)}")

def show_character_consistency_check():
    """显示角色一致性检查界面"""
    st.markdown("### 🎯 角色一致性检查")
    
    # 返回按钮
    if st.button("← 返回角色列表"):
        st.session_state.show_consistency_check = False
        st.rerun()
    
    st.markdown("---")
    
    if not st.session_state.characters_data or not st.session_state.outline_data:
        st.warning("⚠️ 需要同时有角色数据和大纲数据才能进行一致性检查")
        return
    
    # 一致性检查配置
    st.markdown("### ⚙️ 检查配置")
    col1, col2 = st.columns(2)
    
    with col1:
        check_scope = st.selectbox("检查范围", [
            "全面检查", 
            "基础信息检查", 
            "角色动机检查", 
            "背景设定检查"
        ], help="选择检查的详细程度")
        
        show_suggestions = st.checkbox("显示修改建议", value=True, help="是否显示AI建议的修改方案")
    
    with col2:
        check_level = st.selectbox("检查级别", [
            "严格模式",
            "标准模式", 
            "宽松模式"
        ], index=1, help="检查的严格程度")
        
        auto_fix = st.checkbox("自动修复明显错误", value=False, help="是否自动修复检测到的明显错误")
    
    st.markdown("---")
    
    # 执行一致性检查按钮
    if st.button("🔍 开始一致性检查", type="primary", use_container_width=True):
        perform_consistency_check(check_scope, check_level, show_suggestions, auto_fix)

def perform_consistency_check(check_scope, check_level, show_suggestions, auto_fix):
    """执行一致性检查"""
    try:
        with st.spinner("🔍 正在进行角色一致性分析..."):
            # 记录开始时间
            start_time = time.time()
            
            print(f"🎯 [一致性检查] 开始执行 - 范围: {check_scope}, 级别: {check_level}")
            
            # 构建检查提示
            characters_info = []
            for char in st.session_state.characters_data:
                char_info = {
                    "name": char.get('name', ''),
                    "role": char.get('role', ''),
                    "traits": char.get('traits', ''),
                    "background": char.get('background', ''),
                    "motivation": char.get('motivation', '')
                }
                characters_info.append(char_info)
            
            chapters_info = []
            for chapter in st.session_state.outline_data:
                chapter_info = {
                    "chapter_id": chapter['chapter_id'],
                    "title": chapter['title'],
                    "summary": chapter.get('summary', '')
                }
                chapters_info.append(chapter_info)
            
            # 构建检查级别配置
            strictness_config = {
                "严格模式": "严格检查所有细节，发现任何可能的不一致",
                "标准模式": "检查主要矛盾和明显冲突",
                "宽松模式": "只检查严重的逻辑冲突"
            }
            
            scope_config = {
                "全面检查": "检查角色的所有属性与故事的一致性",
                "基础信息检查": "检查角色姓名、角色定位的一致性",
                "角色动机检查": "检查角色动机与故事情节的匹配度",
                "背景设定检查": "检查角色背景与故事世界观的一致性"
            }
            
            # 调用后端智能分析
            from src.utils.utils import generate_response, convert_json
            
            analysis_prompt = f"""
你是一位专业的故事编辑和角色设定专家。请对以下角色设定与故事大纲进行一致性检查。

检查级别：{strictness_config[check_level]}
检查范围：{scope_config[check_scope]}

角色设定：
{json.dumps(characters_info, ensure_ascii=False, indent=2)}

故事大纲：
{json.dumps(chapters_info, ensure_ascii=False, indent=2)}

请分析每个角色的设定是否与故事大纲保持一致，包括：

1. **角色定位一致性**：角色的作用和定位是否符合故事需要
2. **背景设定一致性**：角色背景是否与故事世界观匹配
3. **动机合理性**：角色动机是否与故事情节发展逻辑一致
4. **特征协调性**：角色特征是否支持其在故事中的行为
5. **名称合适性**：角色名称是否符合故事风格和世界观

请返回JSON格式的检查报告：
{{
    "overall_consistency": "整体一致性评分(1-10)",
    "consistency_summary": "整体一致性总结",
    "character_reports": [
        {{
            "character_name": "角色名称",
            "consistency_score": "一致性评分(1-10)",
            "issues": [
                {{
                    "type": "问题类型",
                    "severity": "严重程度(高/中/低)",
                    "description": "问题描述",
                    "suggestion": "修改建议"
                }}
            ],
            "strengths": ["优点列表"]
        }}
    ],
    "cross_character_issues": [
        {{
            "characters": ["涉及的角色"],
            "issue": "角色间冲突问题",
            "suggestion": "解决建议"
        }}
    ],
    "recommendations": [
        "总体优化建议"
    ]
}}

只返回JSON格式，不要其他解释。
"""
            
            # 调用后端分析
            msg = [{"role": "user", "content": analysis_prompt}]
            response = generate_response(msg)
            analysis_result = convert_json(response)
            
            end_time = time.time()
            print(f"⏱️ [一致性检查] 分析耗时: {end_time - start_time:.3f}秒")
            
            if not analysis_result or not isinstance(analysis_result, dict):
                st.error("❌ 一致性检查失败：后端返回数据格式不正确")
                return
            
            # 显示检查结果
            display_consistency_results(analysis_result, show_suggestions, auto_fix)
            
    except Exception as e:
        st.error(f"❌ 一致性检查失败: {str(e)}")
        print(f"❌ [一致性检查] 检查失败: {str(e)}")

def display_consistency_results(analysis_result, show_suggestions, auto_fix):
    """显示一致性检查结果"""
    st.markdown("---")
    st.markdown("## 📊 一致性检查报告")
    
    # 整体评分
    overall_score = analysis_result.get('overall_consistency', 'N/A')
    consistency_summary = analysis_result.get('consistency_summary', '无总结')
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 创建评分显示
        try:
            score_value = float(overall_score)
            if score_value >= 8:
                score_color = "🟢"
                score_level = "优秀"
            elif score_value >= 6:
                score_color = "🟡"
                score_level = "良好"
            else:
                score_color = "🔴"
                score_level = "需改进"
        except:
            score_color = "⚪"
            score_level = "未知"
        
        st.metric("整体一致性评分", f"{score_color} {overall_score}/10", delta=score_level)
    
    with col2:
        st.markdown("**🔍 总体评价:**")
        st.info(consistency_summary)
    
    st.markdown("---")
    
    # 角色详细报告
    character_reports = analysis_result.get('character_reports', [])
    
    if character_reports:
        st.markdown("### 👥 角色详细分析")
        
        for report in character_reports:
            character_name = report.get('character_name', '未知角色')
            consistency_score = report.get('consistency_score', 'N/A')
            issues = report.get('issues', [])
            strengths = report.get('strengths', [])
            
            with st.expander(f"**{character_name}** - 得分: {consistency_score}/10", expanded=len(issues) > 0):
                
                # 显示优点
                if strengths:
                    st.markdown("**✅ 优点:**")
                    for strength in strengths:
                        st.success(f"• {strength}")
                
                # 显示问题
                if issues:
                    st.markdown("**⚠️ 发现的问题:**")
                    
                    for issue in issues:
                        issue_type = issue.get('type', '未知问题')
                        severity = issue.get('severity', '中')
                        description = issue.get('description', '无描述')
                        suggestion = issue.get('suggestion', '无建议')
                        
                        # 根据严重程度选择颜色
                        if severity == '高':
                            st.error(f"🔴 **{issue_type}** (严重)")
                        elif severity == '中':
                            st.warning(f"🟡 **{issue_type}** (中等)")
                        else:
                            st.info(f"🔵 **{issue_type}** (轻微)")
                        
                        st.markdown(f"   描述: {description}")
                        
                        if show_suggestions and suggestion:
                            st.markdown(f"   💡 建议: {suggestion}")
                        
                        st.markdown("---")
                else:
                    st.success("✅ 未发现明显问题")
    
    # 角色间冲突分析
    cross_character_issues = analysis_result.get('cross_character_issues', [])
    
    if cross_character_issues:
        st.markdown("### 🤝 角色间关系分析")
        
        for issue in cross_character_issues:
            characters = issue.get('characters', [])
            issue_desc = issue.get('issue', '无描述')
            suggestion = issue.get('suggestion', '无建议')
            
            st.warning(f"**涉及角色:** {', '.join(characters)}")
            st.markdown(f"**问题:** {issue_desc}")
            
            if show_suggestions and suggestion:
                st.markdown(f"**建议:** {suggestion}")
            
            st.markdown("---")
    
    # 总体建议
    recommendations = analysis_result.get('recommendations', [])
    
    if recommendations and show_suggestions:
        st.markdown("### 💡 优化建议")
        
        for i, rec in enumerate(recommendations):
            st.info(f"{i+1}. {rec}")
    
    # 保存报告
    st.markdown("---")
    if st.button("💾 保存检查报告", use_container_width=True):
        save_consistency_report(analysis_result)

def save_consistency_report(analysis_result):
    """保存一致性检查报告"""
    try:
        # 使用真实后端的保存功能
        report_filename = f"consistency_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(analysis_result, st.session_state.current_version, report_filename)
        
        st.success(f"✅ 检查报告已保存: {st.session_state.current_version}/{report_filename}")
        print(f"💾 [一致性检查] 保存报告: {report_filename}")
        
    except Exception as e:
        st.error(f"❌ 保存报告失败: {str(e)}")
        print(f"❌ [一致性检查] 保存报告失败: {str(e)}")

def show_character_relationships():
    """显示角色关系网络界面"""
    st.markdown("### 🕸️ 角色关系网络")
    
    # 返回按钮
    if st.button("← 返回角色列表"):
        st.session_state.show_character_relationships = False
        st.rerun()
    
    st.markdown("---")
    
    if not st.session_state.characters_data:
        st.warning("⚠️ 需要有角色数据才能分析关系网络")
        return
    
    # 关系分析配置
    st.markdown("### ⚙️ 分析配置")
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_depth = st.selectbox("分析深度", [
            "基础关系",
            "详细关系", 
            "复杂网络"
        ], index=1, help="选择关系分析的详细程度")
        
        include_outline = st.checkbox("结合大纲分析", value=True, help="是否基于故事大纲分析角色关系")
    
    with col2:
        relationship_types = st.multiselect("关系类型", [
            "家庭关系",
            "朋友关系", 
            "敌对关系",
            "合作关系",
            "师生关系",
            "上下级关系",
            "竞争关系",
            "其他关系"
        ], default=["家庭关系", "朋友关系", "敌对关系", "合作关系"])
        
        show_network_graph = st.checkbox("显示关系图", value=True, help="是否显示可视化关系网络图")
    
    st.markdown("---")
    
    # 执行关系分析按钮
    if st.button("🔍 开始关系分析", type="primary", use_container_width=True):
        perform_relationship_analysis(analysis_depth, include_outline, relationship_types, show_network_graph)

def perform_relationship_analysis(analysis_depth, include_outline, relationship_types, show_network_graph):
    """执行角色关系分析"""
    try:
        with st.spinner("🕸️ 正在分析角色关系网络..."):
            # 记录开始时间
            start_time = time.time()
            
            print(f"🕸️ [关系分析] 开始执行 - 深度: {analysis_depth}, 类型: {relationship_types}")
            
            # 构建分析数据
            characters_info = []
            for char in st.session_state.characters_data:
                char_info = {
                    "name": char.get('name', ''),
                    "role": char.get('role', ''),
                    "traits": char.get('traits', ''),
                    "background": char.get('background', ''),
                    "motivation": char.get('motivation', '')
                }
                characters_info.append(char_info)
            
            # 如果包含大纲分析
            outline_context = ""
            if include_outline and st.session_state.outline_data:
                chapters_info = []
                for chapter in st.session_state.outline_data:
                    chapters_info.append({
                        "chapter_id": chapter['chapter_id'],
                        "title": chapter['title'],
                        "summary": chapter.get('summary', '')
                    })
                outline_context = f"\n\n故事大纲：\n{json.dumps(chapters_info, ensure_ascii=False, indent=2)}"
            
            # 调用后端智能分析
            from src.utils.utils import generate_response, convert_json
            
            analysis_prompt = f"""
你是一位专业的故事分析师和角色关系专家。请分析以下角色之间的关系网络。

分析深度：{analysis_depth}
关系类型：{', '.join(relationship_types)}

角色信息：
{json.dumps(characters_info, ensure_ascii=False, indent=2)}
{outline_context}

请分析角色之间的关系，包括：

1. **直接关系**：角色之间的直接联系和互动
2. **间接关系**：通过其他角色或事件建立的联系
3. **关系强度**：关系的重要程度和影响力
4. **关系性质**：关系的类型（友好、敌对、中性等）
5. **关系发展**：关系在故事中的变化趋势

请返回JSON格式的关系分析：
{{
    "relationship_summary": "关系网络总体描述",
    "character_relationships": [
        {{
            "character_a": "角色A名称",
            "character_b": "角色B名称",
            "relationship_type": "关系类型",
            "relationship_strength": "关系强度(1-10)",
            "relationship_nature": "关系性质(正面/负面/中性)",
            "description": "关系详细描述",
            "story_context": "在故事中的体现",
            "development_trend": "关系发展趋势"
        }}
    ],
    "character_centrality": [
        {{
            "character": "角色名称",
            "centrality_score": "中心度评分(1-10)",
            "role_in_network": "在关系网络中的作用",
            "key_connections": ["重要关联角色列表"]
        }}
    ],
    "relationship_clusters": [
        {{
            "cluster_name": "关系群组名称",
            "members": ["群组成员"],
            "cluster_type": "群组类型",
            "description": "群组描述"
        }}
    ],
    "network_insights": [
        "关系网络洞察"
    ]
}}

只返回JSON格式，不要其他解释。
"""
            
            # 调用后端分析
            msg = [{"role": "user", "content": analysis_prompt}]
            response = generate_response(msg)
            analysis_result = convert_json(response)
            
            end_time = time.time()
            print(f"⏱️ [关系分析] 分析耗时: {end_time - start_time:.3f}秒")
            
            if not analysis_result or not isinstance(analysis_result, dict):
                st.error("❌ 关系分析失败：后端返回数据格式不正确")
                return
            
            # 显示分析结果
            display_relationship_results(analysis_result, show_network_graph)
            
    except Exception as e:
        st.error(f"❌ 关系分析失败: {str(e)}")
        print(f"❌ [关系分析] 分析失败: {str(e)}")

def display_relationship_results(analysis_result, show_network_graph):
    """显示角色关系分析结果"""
    st.markdown("---")
    st.markdown("## 🕸️ 角色关系网络分析")
    
    # 网络总览
    relationship_summary = analysis_result.get('relationship_summary', '无总结')
    st.markdown("### 📊 网络总览")
    st.info(relationship_summary)
    
    st.markdown("---")
    
    # 角色关系列表
    relationships = analysis_result.get('character_relationships', [])
    
    if relationships:
        st.markdown("### 🤝 角色关系详情")
        
        # 创建关系统计
        total_relationships = len(relationships)
        positive_relationships = len([r for r in relationships if r.get('relationship_nature') == '正面'])
        negative_relationships = len([r for r in relationships if r.get('relationship_nature') == '负面'])
        neutral_relationships = len([r for r in relationships if r.get('relationship_nature') == '中性'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总关系数", total_relationships)
        with col2:
            st.metric("正面关系", positive_relationships, delta="🟢")
        with col3:
            st.metric("负面关系", negative_relationships, delta="🔴")
        with col4:
            st.metric("中性关系", neutral_relationships, delta="⚪")
        
        st.markdown("---")
        
        # 详细关系列表
        for i, rel in enumerate(relationships):
            char_a = rel.get('character_a', '角色A')
            char_b = rel.get('character_b', '角色B')
            rel_type = rel.get('relationship_type', '未知关系')
            rel_strength = rel.get('relationship_strength', 'N/A')
            rel_nature = rel.get('relationship_nature', '中性')
            description = rel.get('description', '无描述')
            story_context = rel.get('story_context', '无情境')
            development_trend = rel.get('development_trend', '无趋势')
            
            # 根据关系性质选择颜色
            if rel_nature == '正面':
                nature_color = "🟢"
            elif rel_nature == '负面':
                nature_color = "🔴"
            else:
                nature_color = "⚪"
            
            with st.expander(f"{nature_color} **{char_a} ↔ {char_b}** ({rel_type}) - 强度: {rel_strength}/10"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**关系性质:** {rel_nature}")
                    st.markdown(f"**关系强度:** {rel_strength}/10")
                    st.markdown(f"**关系类型:** {rel_type}")
                
                with col2:
                    st.markdown(f"**发展趋势:** {development_trend}")
                
                st.markdown(f"**关系描述:** {description}")
                
                if story_context != '无情境':
                    st.markdown(f"**故事情境:** {story_context}")
    
    # 角色中心度分析
    centrality_data = analysis_result.get('character_centrality', [])
    
    if centrality_data:
        st.markdown("---")
        st.markdown("### 🎯 角色中心度分析")
        
        # 按中心度排序
        centrality_data.sort(key=lambda x: float(x.get('centrality_score', 0)), reverse=True)
        
        for cent in centrality_data:
            character = cent.get('character', '未知角色')
            centrality_score = cent.get('centrality_score', 'N/A')
            role_in_network = cent.get('role_in_network', '无描述')
            key_connections = cent.get('key_connections', [])
            
            # 根据中心度评分选择颜色
            try:
                score_value = float(centrality_score)
                if score_value >= 8:
                    score_color = "🟢"
                elif score_value >= 6:
                    score_color = "🟡"
                else:
                    score_color = "🔵"
            except:
                score_color = "⚪"
            
            with st.expander(f"{score_color} **{character}** - 中心度: {centrality_score}/10"):
                st.markdown(f"**网络作用:** {role_in_network}")
                
                if key_connections:
                    st.markdown(f"**重要关联:** {', '.join(key_connections)}")
    
    # 关系群组分析
    clusters = analysis_result.get('relationship_clusters', [])
    
    if clusters:
        st.markdown("---")
        st.markdown("### 👥 关系群组分析")
        
        for cluster in clusters:
            cluster_name = cluster.get('cluster_name', '未知群组')
            members = cluster.get('members', [])
            cluster_type = cluster.get('cluster_type', '未知类型')
            description = cluster.get('description', '无描述')
            
            with st.expander(f"**{cluster_name}** ({cluster_type}) - {len(members)} 成员"):
                st.markdown(f"**成员:** {', '.join(members)}")
                st.markdown(f"**群组类型:** {cluster_type}")
                st.markdown(f"**描述:** {description}")
    
    # 网络洞察
    insights = analysis_result.get('network_insights', [])
    
    if insights:
        st.markdown("---")
        st.markdown("### 💡 网络洞察")
        
        for i, insight in enumerate(insights):
            st.info(f"{i+1}. {insight}")
    
    # 网络图可视化
    if show_network_graph and relationships:
        st.markdown("---")
        st.markdown("### 📈 关系网络图")
        
        try:
            # 创建网络图
            create_relationship_network_graph(relationships, centrality_data)
        except Exception as e:
            st.warning(f"⚠️ 网络图生成失败: {str(e)}")
            st.info("💡 可以尝试安装 networkx 和 matplotlib 库以支持网络图可视化")
    
    # 保存分析结果
    st.markdown("---")
    if st.button("💾 保存关系分析", use_container_width=True):
        save_relationship_analysis(analysis_result)

def create_relationship_network_graph(relationships, centrality_data):
    """创建关系网络图 - 使用Mermaid图表"""
    try:
        # 提取所有角色
        characters = set()
        for rel in relationships:
            characters.add(rel.get('character_a', ''))
            characters.add(rel.get('character_b', ''))
        
        characters = list(characters)
        
        # 创建Mermaid图表代码
        mermaid_code = "graph TD\n"
        
        # 添加节点（角色）
        for i, char in enumerate(characters):
            # 根据中心度确定节点样式
            centrality_score = 5  # 默认值
            for cent in centrality_data:
                if cent.get('character') == char:
                    try:
                        centrality_score = float(cent.get('centrality_score', 5))
                    except:
                        centrality_score = 5
                    break
            
            # 根据中心度选择节点样式
            if centrality_score >= 8:
                node_style = f"A{i}[\"{char}<br/>⭐高中心度\"]"
            elif centrality_score >= 6:
                node_style = f"A{i}[\"{char}<br/>🔸中中心度\"]"
            else:
                node_style = f"A{i}[\"{char}\"]"
            
            mermaid_code += f"    {node_style}\n"
        
        # 添加关系边
        for rel in relationships:
            char_a = rel.get('character_a', '')
            char_b = rel.get('character_b', '')
            rel_type = rel.get('relationship_type', '关系')
            rel_nature = rel.get('relationship_nature', '中性')
            
            if char_a in characters and char_b in characters:
                a_idx = characters.index(char_a)
                b_idx = characters.index(char_b)
                
                # 根据关系性质选择边的样式
                if rel_nature == '正面':
                    edge_style = f"A{a_idx} -.->|\"✅ {rel_type}\"| A{b_idx}"
                elif rel_nature == '负面':
                    edge_style = f"A{a_idx} -.->|\"❌ {rel_type}\"| A{b_idx}"
                else:
                    edge_style = f"A{a_idx} -.->|\"⚪ {rel_type}\"| A{b_idx}"
                
                mermaid_code += f"    {edge_style}\n"
        
        # 显示Mermaid图表
        st.markdown("#### 🕸️ 关系网络可视化")
        
        # 创建简化的网络关系表格
        create_relationship_table(relationships, centrality_data)
        
        # 显示Mermaid代码供用户使用
        with st.expander("📊 查看Mermaid图表代码", expanded=False):
            st.code(mermaid_code, language="text")
            st.info("💡 可以复制上面的代码到 [Mermaid在线编辑器](https://mermaid.live/) 中查看可视化图表")
            
            # 提供直接链接
            import urllib.parse
            encoded_mermaid = urllib.parse.quote(mermaid_code)
            mermaid_url = f"https://mermaid.live/edit#pako:eNpdjjEOwjAMRa8S-QduwAKCA3RhYQGxuHFoLdJ4OHa7VL17C2JBYrL1_vfekx_obUYLHShpOmgb5-2Ise6eLvJ5Y_7Eb7Ud10_Kzg=="
            st.markdown(f"🔗 [在新窗口中打开Mermaid编辑器]({mermaid_url})")
            
        # 使用HTML简单显示关系网络
        create_simple_network_html(characters, relationships)
        
    except Exception as e:
        st.error(f"❌ 生成网络图失败: {str(e)}")
        print(f"❌ [关系网络] 图表生成失败: {str(e)}")

def create_relationship_table(relationships, centrality_data):
    """创建关系网络表格显示"""
    st.markdown("#### 📊 关系网络表格")
    
    # 创建关系数据表格
    if relationships:
        import pandas as pd
        
        table_data = []
        for rel in relationships:
            table_data.append({
                "角色A": rel.get('character_a', ''),
                "关系": rel.get('relationship_type', ''),
                "角色B": rel.get('character_b', ''),
                "性质": rel.get('relationship_nature', ''),
                "强度": rel.get('relationship_strength', ''),
                "描述": rel.get('description', '')[:50] + "..." if len(rel.get('description', '')) > 50 else rel.get('description', '')
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 显示中心度排名
    if centrality_data:
        st.markdown("#### 🎯 角色重要性排名")
        
        # 按中心度排序
        sorted_centrality = sorted(centrality_data, key=lambda x: float(x.get('centrality_score', 0)), reverse=True)
        
        col1, col2, col3 = st.columns(3)
        for i, cent in enumerate(sorted_centrality[:9]):  # 显示前9个
            character = cent.get('character', '未知角色')
            score = cent.get('centrality_score', 'N/A')
            
            col_idx = i % 3
            if col_idx == 0:
                with col1:
                    st.metric(f"🥇 {character}" if i == 0 else f"#{i+1} {character}", f"{score}/10")
            elif col_idx == 1:
                with col2:
                    st.metric(f"🥈 {character}" if i == 1 else f"#{i+1} {character}", f"{score}/10")
            else:
                with col3:
                    st.metric(f"🥉 {character}" if i == 2 else f"#{i+1} {character}", f"{score}/10")

def create_simple_network_html(characters, relationships):
    """创建简单的HTML网络图"""
    st.markdown("#### 🕸️ 简化关系网络图")
    
    if not characters or not relationships:
        st.info("📝 暂无关系数据可以显示")
        return
    
    # 限制显示数量，避免页面过载
    max_characters = 10
    max_relationships = 15
    
    display_characters = characters[:max_characters]
    display_relationships = relationships[:max_relationships]
    
    # 角色节点显示
    st.markdown("**👥 角色节点:**")
    
    # 使用columns来布局角色
    cols = st.columns(min(len(display_characters), 4))
    for i, char in enumerate(display_characters):
        with cols[i % len(cols)]:
            st.markdown(f"""
            <div style="
                text-align: center; 
                padding: 10px; 
                margin: 5px;
                background: linear-gradient(135deg, #e3f2fd, #bbdefb); 
                border-radius: 15px; 
                border: 2px solid #1976d2;
                color: #0d47a1;
                font-weight: bold;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                {char}
            </div>
            """, unsafe_allow_html=True)
    
    if len(characters) > max_characters:
        st.info(f"... 还有 {len(characters) - max_characters} 个角色未显示")
    
    st.markdown("---")
    
    # 关系连接显示
    st.markdown("**🔗 关系连接:**")
    
    if not display_relationships:
        st.info("📝 暂无关系数据")
        return
    
    for i, rel in enumerate(display_relationships):
        char_a = rel.get('character_a', '')
        char_b = rel.get('character_b', '')
        rel_type = rel.get('relationship_type', '')
        rel_nature = rel.get('relationship_nature', '')
        rel_strength = rel.get('relationship_strength', 'N/A')
        
        # 根据关系性质选择颜色和图标
        if rel_nature == '正面':
            color = "#4caf50"  # 绿色
            emoji = "💚"
            bg_color = "#e8f5e8"
        elif rel_nature == '负面':
            color = "#f44336"  # 红色
            emoji = "💔"
            bg_color = "#ffebee"
        else:
            color = "#ff9800"  # 橙色
            emoji = "🤝"
            bg_color = "#fff3e0"
        
        # 使用Streamlit的内置组件而不是HTML
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col1:
                st.markdown(f"**{char_a}**")
            
            with col2:
                st.markdown(f"<div style='text-align: center; color: {color};'>{emoji}<br>{rel_type}</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"**{char_b}**")
            
            # 显示关系详情
            if rel_strength != 'N/A':
                st.caption(f"关系强度: {rel_strength}/10 | 性质: {rel_nature}")
            else:
                st.caption(f"性质: {rel_nature}")
        
        if i < len(display_relationships) - 1:
            st.markdown("---")
    
    if len(relationships) > max_relationships:
        st.info(f"... 还有 {len(relationships) - max_relationships} 个关系未显示")

def save_relationship_analysis(analysis_result):
    """保存关系分析结果"""
    try:
        # 使用真实后端的保存功能
        report_filename = f"relationship_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(analysis_result, st.session_state.current_version, report_filename)
        
        st.success(f"✅ 关系分析已保存: {st.session_state.current_version}/{report_filename}")
        print(f"💾 [关系分析] 保存分析: {report_filename}")
        
    except Exception as e:
        st.error(f"❌ 保存分析失败: {str(e)}")
        print(f"❌ [关系分析] 保存分析失败: {str(e)}")

def show_story_generation_interface():
    """显示故事生成界面 - 作为主流程步骤"""
    st.header("📖 步骤3: 故事生成")
    
    # 检查前置条件
    if not st.session_state.outline_data:
        st.error("❌ 请先完成步骤1: 生成故事大纲")
        return
    
    if not st.session_state.characters_data:
        st.error("❌ 请先完成步骤2: 生成角色设定")
        return
    
    # 显示基于大纲和角色的故事生成界面
    show_story_generation_mode()

def show_story_generation_mode():
    """故事生成模式"""
    st.subheader("📖 故事内容生成与管理")
    
    # 故事生成配置
    st.markdown("### ⚙️ 故事生成配置")
    col1, col2 = st.columns(2)
    
    with col1:
        use_narrative_guidance = st.checkbox("使用叙述指导", value=True, help="使用大纲中的叙述分析指导")
        use_cache = st.checkbox("使用缓存", value=True, help="如果已有故事数据，是否直接加载", key="story_use_cache_checkbox")
    
    with col2:
        custom_instruction = st.text_area("自定义指导", placeholder="可选：添加特殊的写作要求或风格指导", height=80)
        auto_save = st.checkbox("自动保存", value=True, help="生成后自动保存", key="story_auto_save_checkbox")
    
    st.markdown("---")
    
    # 故事生成按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📖 生成故事", type="primary", use_container_width=True):
            expand_story_from_outline(use_narrative_guidance, custom_instruction, use_cache, auto_save)
    
    with col2:
        if st.button("🔄 重新生成", use_container_width=True):
            expand_story_from_outline(use_narrative_guidance, custom_instruction, use_cache=False, auto_save=auto_save)
    
    with col3:
        if st.button("📁 加载故事", use_container_width=True):
            st.session_state.show_story_loader = True
            st.rerun()
    
    st.markdown("---")
    
    # 检查是否需要显示故事文件加载器
    if st.session_state.get('show_story_loader', False):
        load_existing_story()
        return
    
    # 显示故事数据
    if st.session_state.story_data:
        show_story_display()
    else:
        st.info("📝 暂无故事数据，请点击'生成故事'按钮开始生成")
        
        # 调试信息
        st.info(f"🔍 调试: 当前故事数据状态 - {type(st.session_state.get('story_data', None))}, 长度: {len(st.session_state.get('story_data', []))}")
        
        # 提示用户开始生成故事
        st.info("💡 点击上方'生成故事'按钮开始基于大纲和角色生成详细故事")

def expand_story_from_outline(use_narrative_guidance=True, custom_instruction="", use_cache=True, auto_save=True):
    """从大纲和角色扩展故事 - 集成版本"""
    try:
        # 检查缓存
        if use_cache and st.session_state.story_data:
            st.success("✅ 使用缓存的故事数据")
            return
        
        with st.spinner("📖 正在生成详细故事内容..."):
            # 记录开始时间
            start_time = time.time()
            
            # 在终端显示后端调用信息
            print(f"📊 [故事生成器集成] 调用后端模块: src.generation.expand_story.expand_story_v1")
            print(f"📝 [故事生成器集成] 输入参数: 大纲章节数={len(st.session_state.outline_data)}, 角色数={len(st.session_state.characters_data)}")
            
            # 准备自定义指导
            final_instruction = ""
            if use_narrative_guidance:
                final_instruction += "请严格按照每章节的叙述指导来组织内容。"
            if custom_instruction:
                final_instruction += f" {custom_instruction}"
            
            # 调用真实后端函数
            from src.generation.expand_story import expand_story_v1
            story = expand_story_v1(
                st.session_state.outline_data, 
                st.session_state.characters_data, 
                custom_instruction=final_instruction if final_instruction else None
            )
            
            # 记录结束时间
            end_time = time.time()
            
            # 在终端显示结果
            print(f"⏱️ [故事生成器集成] 生成耗时: {end_time - start_time:.3f}秒")
            print(f"🎉 [故事生成器集成] 故事生成完成！共生成 {len(story) if story else 0} 个章节")
            
            # 验证生成结果
            if not story or not isinstance(story, list):
                st.error("❌ 故事生成失败：后端返回数据格式不正确")
                print(f"❌ [故事生成器集成] 后端返回数据格式错误: {type(story)} - {str(story)[:200]}...")
                return
            
            # 补充章节ID和标题
            for idx, chapter in enumerate(story):
                if idx < len(st.session_state.outline_data):
                    chapter.setdefault("chapter_id", st.session_state.outline_data[idx]["chapter_id"])
                    chapter.setdefault("title", st.session_state.outline_data[idx]["title"])
            
            # 保存到会话状态
            st.session_state.story_data = story
            
            # 保存到历史记录
            save_story_to_history("生成故事")
            
            # 在终端显示章节列表
            chapter_titles = [ch.get('title', f"第{i+1}章") for i, ch in enumerate(story)]
            print(f"📖 [故事生成器集成] 生成的章节: {', '.join(chapter_titles[:3])}{'...' if len(chapter_titles) > 3 else ''}")
            
            # 自动保存
            if auto_save:
                save_story_to_project()
            
            # 显示成功信息
            st.success(f"🎉 故事生成完成！共生成 {len(story)} 个章节")
            st.info(f"⏱️ 生成耗时: {end_time - start_time:.3f}秒")
            
            # 显示章节简要信息
            st.info(f"📖 生成的章节: {', '.join(chapter_titles)}")
            
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 故事生成失败: {str(e)}")
        print(f"❌ [故事生成器集成] 故事生成失败: {str(e)}")

def save_story_to_project():
    """保存故事到项目目录"""
    try:
        if not st.session_state.story_data:
            st.warning("⚠️ 没有故事数据可保存")
            return
        
        start_time = time.time()
        # 使用真实后端的保存功能
        save_json(st.session_state.story_data, st.session_state.current_version, "story.json")
        end_time = time.time()
        
        st.success(f"✅ 故事已保存到项目目录: {st.session_state.current_version}/story.json")
        print(f"💾 [故事生成器集成] 保存故事到项目: {st.session_state.current_version}/story.json ({len(st.session_state.story_data)} 个章节)")
        
    except Exception as e:
        st.error(f"❌ 保存失败: {str(e)}")
        print(f"❌ [故事生成器集成] 保存故事失败: {str(e)}")

def load_existing_story():
    """加载已有故事文件"""
    st.markdown("### 📁 加载已有故事")
    
    # 添加返回按钮
    if st.button("← 返回故事管理"):
        st.session_state.show_story_loader = False
        st.rerun()
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader("选择故事文件", type=['json'], key="story_upload")
    
    if uploaded_file is not None:
        try:
            # 显示文件信息
            st.info(f"📄 文件名: {uploaded_file.name}")
            st.info(f"📊 文件大小: {uploaded_file.size} bytes")
            
            # 重置文件指针到开始位置
            uploaded_file.seek(0)
            
            # 读取文件内容
            file_content = uploaded_file.read()
            
            # 如果是字节类型，转换为字符串
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # 解析JSON
            story_data = json.loads(file_content)
            
            # 详细验证数据格式
            if not isinstance(story_data, list):
                st.error("❌ 文件格式不正确：应为JSON数组格式")
                return
            
            if len(story_data) == 0:
                st.error("❌ 文件内容为空：没有找到故事数据")
                return
            
            # 验证故事数据格式
            required_fields = ['plot']
            for i, chapter in enumerate(story_data):
                if not isinstance(chapter, dict):
                    st.error(f"❌ 第{i+1}个章节格式不正确：应为对象格式")
                    return
                
                missing_fields = [field for field in required_fields if field not in chapter]
                if missing_fields:
                    st.error(f"❌ 第{i+1}个章节缺少必要字段: {', '.join(missing_fields)}")
                    return
            
            # 加载数据
            st.session_state.story_data = story_data
            
            # 保存到历史记录
            save_story_to_history("加载故事")
            
            st.success(f"✅ 故事数据加载成功！共 {len(story_data)} 个章节")
            st.info("🔄 页面将自动刷新...")
            
            # 显示加载的故事预览
            with st.expander("📖 加载的故事预览", expanded=True):
                for i, chapter in enumerate(story_data[:3]):  # 只显示前3个章节
                    title = chapter.get('title', f'第{i+1}章')
                    plot_preview = chapter.get('plot', '无内容')[:100] + "..." if len(chapter.get('plot', '')) > 100 else chapter.get('plot', '无内容')
                    st.text(f"{i+1}. {title}")
                    st.text(f"   {plot_preview}")
                if len(story_data) > 3:
                    st.text(f"... 还有 {len(story_data) - 3} 个章节")
            
            print(f"📁 [故事管理] 加载故事文件: {len(story_data)} 个章节")
            
            # 清除加载器状态
            st.session_state.show_story_loader = False
            
            st.rerun()
            
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON格式错误: {str(e)}")
            st.error("💡 请确保文件是有效的JSON格式")
        except UnicodeDecodeError as e:
            st.error(f"❌ 文件编码错误: {str(e)}")
            st.error("💡 请确保文件是UTF-8编码")
        except Exception as e:
            st.error(f"❌ 文件加载失败: {str(e)}")
            print(f"❌ [故事管理] 加载失败: {str(e)}")
    else:
        st.info("💡 请选择一个JSON格式的故事文件")

def show_story_display():
    """显示故事信息和管理界面"""
    st.markdown("### 📖 故事内容管理")
    
    story = st.session_state.story_data
    
    # 故事统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("章节总数", len(story))
    with col2:
        total_plot_length = sum(len(ch.get('plot', '')) for ch in story)
        st.metric("总字数", f"{total_plot_length}字")
    with col3:
        avg_length = total_plot_length // len(story) if story else 0
        st.metric("平均章节长度", f"{avg_length}字")
    
    st.markdown("---")
    
    # 故事管理操作
    st.markdown("### 🛠️ 故事管理")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 保存故事", use_container_width=True):
            save_story_to_project()
    
    with col2:
        if st.button("📋 故事历史", use_container_width=True):
            st.session_state.show_story_history = True
            st.rerun()
    
    with col3:
        if st.button("🔄 重新生成全部", use_container_width=True):
            old_story_data = st.session_state.story_data.copy()
            expand_story_from_outline(use_cache=False, auto_save=True)
    
    with col4:
        if st.button("🗑️ 清空故事", use_container_width=True):
            if st.button("⚠️ 确认清空", key="confirm_clear_story"):
                save_story_to_history("清空故事", st.session_state.story_data.copy())
                st.session_state.story_data = []
                st.success("✅ 故事数据已清空")
                print("🗑️ [故事管理] 清空故事数据")
                st.rerun()
    
    # 显示故事历史记录面板
    if st.session_state.get('show_story_history', False):
        show_story_history_panel()
    
    st.markdown("---")
    
    # 功能选项卡
    tab1, tab2, tab3, tab4 = st.tabs(["📋 章节摘要", "🔗 连贯性检查", "✏️ 重点调整", "🎨 风格统一性"])
    
    with tab1:
        show_story_summary()
    
    with tab2:
        show_coherence_check()
    
    with tab3:
        show_story_editing()
    
    with tab4:
        show_style_consistency()

def show_story_summary():
    """显示章节摘要概览"""
    st.markdown("#### 📋 所有章节概览")
    
    story = st.session_state.story_data
    
    # 创建摘要数据
    summary_data = []
    for i, chapter in enumerate(story):
        title = chapter.get('title', f'第{i+1}章')
        plot = chapter.get('plot', '')
        word_count = len(plot)
        
        # 生成摘要（前200字）
        summary = plot[:200] + "..." if len(plot) > 200 else plot
        
        summary_data.append({
            "章节": f"{i+1}. {title}",
            "字数": word_count,
            "内容摘要": summary,
            "场景": chapter.get('scene', '未指定'),
            "人物": ', '.join(chapter.get('characters', [])) if chapter.get('characters') else '未指定'
        })
    
    # 显示摘要表格
    if summary_data:
        import pandas as pd
        df = pd.DataFrame(summary_data)
        
        # 使用更好的显示方式，确保内容摘要可以完全显示
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "内容摘要": st.column_config.TextColumn(
                    "内容摘要",
                    width="large",
                    help="章节详细内容摘要"
                ),
                "章节": st.column_config.TextColumn(
                    "章节",
                    width="medium"
                ),
                "字数": st.column_config.NumberColumn(
                    "字数",
                    width="small"
                ),
                "场景": st.column_config.TextColumn(
                    "场景", 
                    width="medium"
                ),
                "人物": st.column_config.TextColumn(
                    "人物",
                    width="medium"
                )
            }
        )
        
        # 详细内容查看
        st.markdown("---")
        st.markdown("#### 📖 详细内容查看")
        
        # 选择章节查看详细内容
        selected_chapter_for_detail = st.selectbox(
            "选择章节查看完整内容",
            options=[f"{i+1}. {ch.get('title', f'第{i+1}章')}" for i, ch in enumerate(story)],
            index=0,
            key="detail_chapter_selector"
        )
        
        if selected_chapter_for_detail:
            detail_idx = int(selected_chapter_for_detail.split('.')[0]) - 1
            detail_chapter = story[detail_idx]
            
            with st.expander(f"📖 {detail_chapter.get('title', f'第{detail_idx+1}章')} - 完整内容", expanded=True):
                st.markdown(f"**字数：** {len(detail_chapter.get('plot', ''))} 字")
                st.markdown(f"**场景：** {detail_chapter.get('scene', '未指定')}")
                st.markdown(f"**人物：** {', '.join(detail_chapter.get('characters', [])) if detail_chapter.get('characters') else '未指定'}")
                st.markdown("---")
                st.markdown("**完整内容：**")
                st.text_area(
                    "章节完整内容",
                    value=detail_chapter.get('plot', ''),
                    height=400,
                    key=f"detail_content_{detail_idx}",
                    disabled=True,
                    label_visibility="collapsed"
                )
        
        st.markdown("---")
        
        # 导出摘要
        if st.button("📥 导出章节摘要", use_container_width=True):
            summary_text = generate_story_summary_text()
            st.download_button(
                label="📄 下载摘要文本",
                data=summary_text,
                file_name=f"{st.session_state.current_version}_story_summary.txt",
                mime="text/plain"
            )

def show_coherence_check():
    """显示连贯性检查"""
    st.markdown("#### 🔗 章节间连贯性分析")
    
    if st.button("🔍 开始连贯性检查", type="primary", use_container_width=True):
        perform_coherence_analysis()

def show_story_editing():
    """显示故事编辑界面"""
    st.markdown("#### ✏️ 章节重点调整")
    
    story = st.session_state.story_data
    
    # 选择要编辑的章节
    chapter_options = [f"{i+1}. {ch.get('title', f'第{i+1}章')}" for i, ch in enumerate(story)]
    selected_chapters = st.multiselect("选择要重写的章节", chapter_options)
    
    if selected_chapters:
        st.markdown("---")
        
        for selection in selected_chapters:
            chapter_idx = int(selection.split('.')[0]) - 1
            chapter = story[chapter_idx]
            
            with st.expander(f"📝 编辑: {chapter.get('title', f'第{chapter_idx+1}章')}", expanded=True):
                
                # 显示当前内容
                st.markdown("**当前内容:**")
                st.text_area("当前章节内容", value=chapter.get('plot', ''), height=200, key=f"current_plot_{chapter_idx}", disabled=True, label_visibility="collapsed")
                
                # 编辑选项
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"🔄 重新生成第{chapter_idx+1}章", key=f"regen_{chapter_idx}"):
                        regenerate_single_story_chapter(chapter_idx)
                
                with col2:
                    if st.button(f"✏️ 手动编辑第{chapter_idx+1}章", key=f"edit_{chapter_idx}"):
                        st.session_state[f'edit_story_{chapter_idx}'] = True
                        st.rerun()
                
                # 如果进入编辑模式
                if st.session_state.get(f'edit_story_{chapter_idx}', False):
                    st.markdown("**编辑内容:**")
                    new_plot = st.text_area(
                        "新的故事内容", 
                        value=chapter.get('plot', ''), 
                        height=300, 
                        key=f"new_plot_{chapter_idx}"
                    )
                    
                    # 建议文件上传功能
                    st.markdown("---")
                    st.markdown("#### 📁 智能建议文件")
                    
                    uploaded_suggestions = st.file_uploader(
                        "上传建议文件 (.json)",
                        type=['json'],
                        key=f"upload_suggestions_{chapter_idx}",
                        help="上传之前导出的智能建议文件，直接执行级联更新"
                    )
                    
                    if uploaded_suggestions is not None:
                        if st.button(f"🚀 根据建议文件执行更新", key=f"execute_uploaded_{chapter_idx}", type="primary"):
                            execute_uploaded_suggestions(chapter_idx, uploaded_suggestions, new_plot)
                            return
                    
                    st.markdown("---")
                    
                    # 智能冲突检测选项
                    st.markdown("**🔍 智能检测选项:**")
                    col_detect1, col_detect2 = st.columns(2)
                    
                    with col_detect1:
                        enable_conflict_detection = st.checkbox(
                            "启用冲突检测", 
                            value=True, 
                            key=f"conflict_detect_{chapter_idx}",
                            help="检测修改是否与其他章节、角色设定或大纲产生冲突"
                        )
                    
                    with col_detect2:
                        auto_suggest_updates = st.checkbox(
                            "自动建议更新", 
                            value=True, 
                            key=f"auto_suggest_{chapter_idx}",
                            help="如果检测到冲突，自动建议需要更新的其他部分"
                        )
                    
                    # 自定义更新指令
                    custom_update_instruction = st.text_area(
                        "自定义更新指令 (可选)",
                        placeholder="例如：确保所有章节都反映小红帽是幕后黑手这一设定变更...",
                        height=80,
                        key=f"custom_instruction_{chapter_idx}"
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"✅ 智能保存", key=f"smart_save_{chapter_idx}", type="primary"):
                            smart_save_story_chapter_edit(
                                chapter_idx, 
                                new_plot, 
                                enable_conflict_detection, 
                                auto_suggest_updates,
                                custom_update_instruction
                            )
                    
                    with col2:
                        if st.button(f"💾 直接保存", key=f"direct_save_{chapter_idx}"):
                            save_story_chapter_edit(chapter_idx, new_plot)
                    
                    with col3:
                        if st.button(f"❌ 取消编辑", key=f"cancel_{chapter_idx}"):
                            st.session_state[f'edit_story_{chapter_idx}'] = False
                            st.rerun()

def show_style_consistency():
    """显示风格统一性检查"""
    st.markdown("#### 🎨 风格统一性确认")
    
    # 风格检查配置
    col1, col2 = st.columns(2)
    
    with col1:
        check_aspects = st.multiselect("检查方面", [
            "叙述风格",
            "人称一致性", 
            "时态一致性",
            "语言风格",
            "情节风格"
        ], default=["叙述风格", "人称一致性"])
    
    with col2:
        target_style = st.text_input("目标风格", value=st.session_state.get('current_style', '科幻改写'))
    
    if st.button("🎨 开始风格检查", type="primary", use_container_width=True):
        perform_style_consistency_check(check_aspects, target_style)

def perform_coherence_analysis():
    """执行连贯性分析"""
    try:
        with st.spinner("🔍 正在分析章节间连贯性..."):
            # 使用后端LLM进行连贯性分析
            from src.utils.utils import generate_response, convert_json
            
            # 构建分析数据
            chapters_info = []
            for i, chapter in enumerate(st.session_state.story_data):
                chapter_info = {
                    "chapter_id": chapter.get('chapter_id', f'第{i+1}章'),
                    "title": chapter.get('title', f'第{i+1}章'),
                    "plot_summary": chapter.get('plot', '')[:500] + "..." if len(chapter.get('plot', '')) > 500 else chapter.get('plot', ''),
                    "scene": chapter.get('scene', ''),
                    "characters": chapter.get('characters', [])
                }
                chapters_info.append(chapter_info)
            
            analysis_prompt = f"""
你是一位专业的故事编辑。请分析以下故事章节间的连贯性。

故事章节：
{json.dumps(chapters_info, ensure_ascii=False, indent=2)}

请分析：
1. 情节连贯性：章节间的情节发展是否自然流畅
2. 时间连贯性：时间线是否合理
3. 人物连贯性：人物行为和状态变化是否合理
4. 场景连贯性：场景转换是否自然
5. 逻辑连贯性：故事逻辑是否一致

返回JSON格式：
{{
    "overall_coherence": "整体连贯性评分(1-10)",
    "coherence_summary": "连贯性总结",
    "chapter_analysis": [
        {{
            "chapter": "章节标识",
            "coherence_score": "连贯性评分(1-10)",
            "issues": ["发现的问题"],
            "suggestions": ["改进建议"]
        }}
    ],
    "transition_analysis": [
        {{
            "from_chapter": "起始章节",
            "to_chapter": "目标章节", 
            "transition_quality": "过渡质量评分(1-10)",
            "issues": "过渡问题",
            "suggestions": "改进建议"
        }}
    ],
    "recommendations": ["整体改进建议"]
}}

只返回JSON，不要其他解释。
"""
            
            start_time = time.time()
            msg = [{"role": "user", "content": analysis_prompt}]
            response = generate_response(msg)
            analysis_result = convert_json(response)
            end_time = time.time()
            
            print(f"⏱️ [连贯性检查] 分析耗时: {end_time - start_time:.3f}秒")
            
            if analysis_result and isinstance(analysis_result, dict):
                display_coherence_results(analysis_result)
            else:
                st.error("❌ 连贯性分析失败：后端返回数据格式不正确")
                
    except Exception as e:
        st.error(f"❌ 连贯性分析失败: {str(e)}")
        print(f"❌ [连贯性检查] 分析失败: {str(e)}")

def display_coherence_results(analysis_result):
    """显示连贯性分析结果"""
    st.markdown("---")
    st.markdown("## 📊 连贯性分析报告")
    
    # 整体评分
    overall_score = analysis_result.get('overall_coherence', 'N/A')
    coherence_summary = analysis_result.get('coherence_summary', '无总结')
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        try:
            score_value = float(overall_score)
            if score_value >= 8:
                score_color = "🟢"
                score_level = "优秀"
            elif score_value >= 6:
                score_color = "🟡"
                score_level = "良好"
            else:
                score_color = "🔴"
                score_level = "需改进"
        except:
            score_color = "⚪"
            score_level = "未知"
        
        st.metric("整体连贯性评分", f"{score_color} {overall_score}/10", delta=score_level)
    
    with col2:
        st.markdown("**🔍 总体评价:**")
        st.info(coherence_summary)
    
    # 章节分析
    chapter_analysis = analysis_result.get('chapter_analysis', [])
    if chapter_analysis:
        st.markdown("### 📖 章节详细分析")
        
        for analysis in chapter_analysis:
            chapter = analysis.get('chapter', '未知章节')
            score = analysis.get('coherence_score', 'N/A')
            issues = analysis.get('issues', [])
            suggestions = analysis.get('suggestions', [])
            
            with st.expander(f"**{chapter}** - 连贯性: {score}/10"):
                if issues:
                    st.markdown("**⚠️ 发现的问题:**")
                    for issue in issues:
                        st.warning(f"• {issue}")
                
                if suggestions:
                    st.markdown("**💡 改进建议:**")
                    for suggestion in suggestions:
                        st.info(f"• {suggestion}")
    
    # 过渡分析
    transition_analysis = analysis_result.get('transition_analysis', [])
    if transition_analysis:
        st.markdown("### 🔗 章节过渡分析")
        
        for transition in transition_analysis:
            from_chapter = transition.get('from_chapter', '')
            to_chapter = transition.get('to_chapter', '')
            quality = transition.get('transition_quality', 'N/A')
            issues = transition.get('issues', '')
            suggestions = transition.get('suggestions', '')
            
            with st.expander(f"**{from_chapter} → {to_chapter}** - 过渡质量: {quality}/10"):
                if issues:
                    st.warning(f"**问题:** {issues}")
                if suggestions:
                    st.info(f"**建议:** {suggestions}")
    
    # 整体建议
    recommendations = analysis_result.get('recommendations', [])
    if recommendations:
        st.markdown("### 💡 整体改进建议")
        for rec in recommendations:
            st.info(f"• {rec}")

def perform_style_consistency_check(check_aspects, target_style):
    """执行风格一致性检查"""
    try:
        with st.spinner("🎨 正在检查风格一致性..."):
            from src.utils.utils import generate_response, convert_json
            
            # 构建检查数据
            story_content = []
            for i, chapter in enumerate(st.session_state.story_data):
                content = {
                    "chapter": chapter.get('title', f'第{i+1}章'),
                    "plot": chapter.get('plot', '')[:800] + "..." if len(chapter.get('plot', '')) > 800 else chapter.get('plot', '')
                }
                story_content.append(content)
            
            style_prompt = f"""
你是一位专业的文学编辑。请检查以下故事的风格一致性。

目标风格：{target_style}
检查方面：{', '.join(check_aspects)}

故事内容：
{json.dumps(story_content, ensure_ascii=False, indent=2)}

请分析风格一致性，返回JSON格式：
{{
    "overall_consistency": "整体一致性评分(1-10)",
    "consistency_summary": "一致性总结",
    "aspect_analysis": {{
        "叙述风格": {{"score": "评分", "issues": ["问题"], "suggestions": ["建议"]}},
        "人称一致性": {{"score": "评分", "issues": ["问题"], "suggestions": ["建议"]}},
        "时态一致性": {{"score": "评分", "issues": ["问题"], "suggestions": ["建议"]}},
        "语言风格": {{"score": "评分", "issues": ["问题"], "suggestions": ["建议"]}},
        "情节风格": {{"score": "评分", "issues": ["问题"], "suggestions": ["建议"]}}
    }},
    "chapter_consistency": [
        {{
            "chapter": "章节名",
            "consistency_score": "一致性评分(1-10)",
            "style_issues": ["风格问题"],
            "suggestions": ["改进建议"]
        }}
    ],
    "recommendations": ["整体建议"]
}}

只返回JSON，不要其他解释。
"""
            
            start_time = time.time()
            msg = [{"role": "user", "content": style_prompt}]
            response = generate_response(msg)
            analysis_result = convert_json(response)
            end_time = time.time()
            
            print(f"⏱️ [风格检查] 分析耗时: {end_time - start_time:.3f}秒")
            
            if analysis_result and isinstance(analysis_result, dict):
                display_style_consistency_results(analysis_result)
            else:
                st.error("❌ 风格检查失败：后端返回数据格式不正确")
                
    except Exception as e:
        st.error(f"❌ 风格检查失败: {str(e)}")
        print(f"❌ [风格检查] 检查失败: {str(e)}")

def display_style_consistency_results(analysis_result):
    """显示风格一致性检查结果"""
    st.markdown("---")
    st.markdown("## 🎨 风格一致性检查报告")
    
    # 整体评分
    overall_score = analysis_result.get('overall_consistency', 'N/A')
    consistency_summary = analysis_result.get('consistency_summary', '无总结')
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        try:
            score_value = float(overall_score)
            if score_value >= 8:
                score_color = "🟢"
                score_level = "优秀"
            elif score_value >= 6:
                score_color = "🟡"
                score_level = "良好"
            else:
                score_color = "🔴"
                score_level = "需改进"
        except:
            score_color = "⚪"
            score_level = "未知"
        
        st.metric("整体一致性评分", f"{score_color} {overall_score}/10", delta=score_level)
    
    with col2:
        st.markdown("**🎨 风格评价:**")
        st.info(consistency_summary)
    
    # 各方面分析
    aspect_analysis = analysis_result.get('aspect_analysis', {})
    if aspect_analysis:
        st.markdown("### 📋 各方面分析")
        
        for aspect, data in aspect_analysis.items():
            score = data.get('score', 'N/A')
            issues = data.get('issues', [])
            suggestions = data.get('suggestions', [])
            
            with st.expander(f"**{aspect}** - 评分: {score}/10"):
                if issues:
                    st.markdown("**⚠️ 发现的问题:**")
                    for issue in issues:
                        st.warning(f"• {issue}")
                
                if suggestions:
                    st.markdown("**💡 改进建议:**")
                    for suggestion in suggestions:
                        st.info(f"• {suggestion}")
    
    # 章节一致性
    chapter_consistency = analysis_result.get('chapter_consistency', [])
    if chapter_consistency:
        st.markdown("### 📖 章节风格分析")
        
        for analysis in chapter_consistency:
            chapter = analysis.get('chapter', '未知章节')
            score = analysis.get('consistency_score', 'N/A')
            issues = analysis.get('style_issues', [])
            suggestions = analysis.get('suggestions', [])
            
            with st.expander(f"**{chapter}** - 风格一致性: {score}/10"):
                if issues:
                    st.markdown("**🎨 风格问题:**")
                    for issue in issues:
                        st.warning(f"• {issue}")
                
                if suggestions:
                    st.markdown("**💡 改进建议:**")
                    for suggestion in suggestions:
                        st.info(f"• {suggestion}")

def regenerate_single_story_chapter(chapter_idx):
    """重新生成单个故事章节"""
    try:
        chapter = st.session_state.story_data[chapter_idx]
        outline_chapter = st.session_state.outline_data[chapter_idx] if chapter_idx < len(st.session_state.outline_data) else None
        
        if not outline_chapter:
            st.error("❌ 找不到对应的大纲章节")
            return
        
        with st.spinner(f"🔄 正在重新生成第{chapter_idx+1}章..."):
            start_time = time.time()
            
            print(f"📊 [故事编辑] 重新生成第{chapter_idx+1}章: {outline_chapter.get('title', '未知标题')}")
            
            # 保存重新生成前的状态到历史记录
            old_story_data = st.session_state.story_data.copy()
            save_story_to_history(f"重新生成第{chapter_idx+1}章", old_story_data)
            
            # 调用后端重新生成单个章节
            from src.generation.expand_story import expand_story_v1
            
            # 只传入当前章节的大纲和角色
            single_chapter_result = expand_story_v1(
                [outline_chapter], 
                st.session_state.characters_data,
                custom_instruction="请重新创作这个章节，确保内容新颖且符合整体故事风格。"
            )
            
            end_time = time.time()
            
            if single_chapter_result and len(single_chapter_result) > 0:
                # 更新章节数据
                new_chapter = single_chapter_result[0]
                new_chapter.setdefault("chapter_id", outline_chapter["chapter_id"])
                new_chapter.setdefault("title", outline_chapter["title"])
                
                st.session_state.story_data[chapter_idx] = new_chapter
                
                st.success(f"✅ 第{chapter_idx+1}章重新生成完成")
                st.info(f"⏱️ 生成耗时: {end_time - start_time:.3f}秒")
                
                print(f"🎉 [故事编辑] 第{chapter_idx+1}章重新生成完成")
                st.rerun()
            else:
                st.error("❌ 重新生成失败：后端返回数据无效")
                
    except Exception as e:
        st.error(f"❌ 重新生成第{chapter_idx+1}章失败: {str(e)}")
        print(f"❌ [故事编辑] 重新生成失败: {str(e)}")

def save_story_chapter_edit(chapter_idx, new_plot):
    """保存章节编辑"""
    try:
        # 保存编辑前的状态到历史记录
        old_story_data = st.session_state.story_data.copy()
        save_story_to_history(f"编辑第{chapter_idx+1}章", old_story_data)
        
        # 更新章节内容
        st.session_state.story_data[chapter_idx]['plot'] = new_plot
        
        # 清除编辑状态
        st.session_state[f'edit_story_{chapter_idx}'] = False
        
        st.success(f"✅ 第{chapter_idx+1}章修改已保存")
        print(f"💾 [故事编辑] 保存第{chapter_idx+1}章修改: {len(new_plot)} 字")
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 保存修改失败: {str(e)}")
        print(f"❌ [故事编辑] 保存修改失败: {str(e)}")

def smart_save_story_chapter_edit(chapter_idx, new_plot, enable_conflict_detection, auto_suggest_updates, custom_instruction=""):
    """智能保存章节编辑 - 包含冲突检测和级联更新建议"""
    try:
        with st.spinner("🔍 正在进行智能分析..."):
            # 保存编辑前的状态到历史记录
            old_story_data = st.session_state.story_data.copy()
            old_plot = st.session_state.story_data[chapter_idx]['plot']
            
            # 先进行冲突检测
            conflicts_detected = False
            update_suggestions = {}
            
            if enable_conflict_detection:
                conflicts_detected, update_suggestions = detect_plot_conflicts_and_suggest_updates(
                    chapter_idx, old_plot, new_plot, custom_instruction
                )
            
            print(f"🔍 [智能保存] 冲突检测结果: conflicts_detected={conflicts_detected}, auto_suggest_updates={auto_suggest_updates}")
            print(f"🔍 [智能保存] 更新建议: {update_suggestions}")
            
            # 将冲突检测结果保存到session state，确保按钮点击后状态不丢失
            smart_state_key = f'smart_conflict_state_{chapter_idx}'
            if conflicts_detected and auto_suggest_updates:
                st.session_state[smart_state_key] = {
                    'conflicts_detected': True,
                    'update_suggestions': update_suggestions,
                    'new_plot': new_plot,
                    'custom_instruction': custom_instruction,
                    'old_story_data': old_story_data
                }
            
            # 检查是否有保存的冲突状态（用于按钮点击后的重新运行）
            has_smart_state = smart_state_key in st.session_state
            smart_state = st.session_state.get(smart_state_key, {})
            
            print(f"🔍 [智能保存] 状态检查: has_smart_state={has_smart_state}")
            
            # 显示冲突处理界面
            if (conflicts_detected and auto_suggest_updates) or has_smart_state:
                print(f"✅ [智能保存] 进入冲突处理分支")
                
                # 使用保存的状态数据或当前数据
                display_suggestions = smart_state.get('update_suggestions', update_suggestions)
                display_new_plot = smart_state.get('new_plot', new_plot)
                display_custom_instruction = smart_state.get('custom_instruction', custom_instruction)
                display_old_story_data = smart_state.get('old_story_data', old_story_data)
                
                print(f"🔍 [智能保存] 使用的建议数据: {type(display_suggestions)}")
                
                # 显示冲突检测结果和更新建议
                st.markdown("---")
                st.markdown("## 🚨 智能冲突检测结果")
                
                # 显示检测到的冲突
                if display_suggestions.get('conflicts'):
                    st.markdown("### ⚠️ 检测到的冲突:")
                    for conflict in display_suggestions['conflicts']:
                        st.warning(f"• {conflict}")
                
                # 显示更新建议
                if display_suggestions.get('suggestions'):
                    st.markdown("### 💡 建议的更新:")
                    
                    # 大纲更新建议
                    if display_suggestions['suggestions'].get('outline_updates'):
                        st.markdown("**📚 大纲更新建议:**")
                        for update in display_suggestions['suggestions']['outline_updates']:
                            st.info(f"• {update}")
                    
                    # 角色更新建议
                    if display_suggestions['suggestions'].get('character_updates'):
                        st.markdown("**👥 角色更新建议:**")
                        for update in display_suggestions['suggestions']['character_updates']:
                            st.info(f"• {update}")
                    
                    # 其他章节更新建议
                    if display_suggestions['suggestions'].get('other_chapters'):
                        st.markdown("**📖 其他章节更新建议:**")
                        for chapter_update in display_suggestions['suggestions']['other_chapters']:
                            chapter_num = chapter_update.get('chapter', '未知')
                            suggestion = chapter_update.get('suggestion', '')
                            st.info(f"• 第{chapter_num}章: {suggestion}")
                

                
                # 提供用户选择
                st.markdown("---")
                st.markdown("### 🤔 您希望如何处理？")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🚀 执行智能更新", type="primary", key=f"execute_smart_update_{chapter_idx}"):
                        print(f"🔴🔴🔴 [按钮点击] 执行智能更新按钮被点击！章节: {chapter_idx}")
                        print(f"🔴 [按钮点击] 更新建议类型: {type(display_suggestions)}")
                        print(f"🔴 [按钮点击] 更新建议内容: {display_suggestions}")
                        print(f"🔴 [按钮点击] 自定义指令: {display_custom_instruction}")
                        
                        # 执行级联更新
                        execute_cascade_updates(chapter_idx, display_new_plot, display_suggestions, display_custom_instruction)
                        
                        # 清除智能状态
                        if smart_state_key in st.session_state:
                            del st.session_state[smart_state_key]
                            print(f"🗑️ [按钮点击] 已清除智能状态: {smart_state_key}")
                        
                        return
                
                with col2:
                    if st.button("💾 仅保存当前章节", key=f"save_current_only_{chapter_idx}"):
                        save_story_to_history(f"编辑第{chapter_idx+1}章(忽略冲突)", display_old_story_data)
                        st.session_state.story_data[chapter_idx]['plot'] = display_new_plot
                        st.session_state[f'edit_story_{chapter_idx}'] = False
                        
                        # 清除智能状态
                        if smart_state_key in st.session_state:
                            del st.session_state[smart_state_key]
                        
                        st.success(f"✅ 第{chapter_idx+1}章已保存（未处理冲突）")
                        st.rerun()
                
                with col3:
                    if st.button("❌ 取消修改", key=f"cancel_smart_save_{chapter_idx}"):
                        st.session_state[f'edit_story_{chapter_idx}'] = False
                        
                        # 清除智能状态
                        if smart_state_key in st.session_state:
                            del st.session_state[smart_state_key]
                        
                        st.info("已取消修改")
                        st.rerun()
                
            
            # 建议管理功能（始终显示）
            st.markdown("---")
            st.markdown("### 💾 建议管理")
            
            col_save1, col_save2, col_save3, col_save4 = st.columns(4)
            
            # with col_save1:
            #     if st.button("💾 保存分析建议", key=f"save_suggestions_{chapter_idx}"):
            #         print(f"🔘 [UI] 用户点击保存建议按钮，章节{chapter_idx+1}")
            #         save_conflict_suggestions(chapter_idx, update_suggestions, new_plot, custom_instruction)
            with col_save1:
                if st.button("💾 保存分析建议", key=f"save_suggestions_{chapter_idx}"):
                    print(f"🔘 [UI] 用户点击保存建议按钮，章节{chapter_idx+1}")
                    
                    # 显示保存过程
                    with st.spinner("💾 正在保存建议..."):
                        success = save_conflict_suggestions(chapter_idx, update_suggestions, new_plot, custom_instruction)
                    
                    if success:
                        # 保存成功后的处理
                        st.success("🎉 建议保存完成！")
                        st.balloons()  # 添加一个庆祝效果
                        
                        # 可选：短暂延迟后刷新页面让用户看到结果
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 建议保存失败，请查看错误信息")
                        st.info("💡 提示：请检查文件权限和存储空间")            
            with col_save2:
                if st.button("📥 导出建议文件", key=f"export_suggestions_{chapter_idx}"):
                    print(f"🔘 [UI] 用户点击导出建议按钮，章节{chapter_idx+1}")
                    export_suggestions_file(chapter_idx, update_suggestions, new_plot, custom_instruction)
            
            with col_save3:
                if st.button("📁 加载已保存建议", key=f"load_suggestions_{chapter_idx}"):
                    st.session_state[f'show_suggestions_loader_{chapter_idx}'] = True
                    st.rerun()
            
            with col_save4:
                if st.button("📋 查看建议历史", key=f"show_suggestions_history_{chapter_idx}"):
                    st.session_state[f'show_suggestions_history_{chapter_idx}'] = True
                    st.rerun()
            
            # 建议加载器
            if st.session_state.get(f'show_suggestions_loader_{chapter_idx}', False):
                show_suggestions_loader(chapter_idx, new_plot, custom_instruction)
                return
            
            # 建议历史查看器
            if st.session_state.get(f'show_suggestions_history_{chapter_idx}', False):
                show_suggestions_history_for_chapter(chapter_idx, new_plot, custom_instruction)
                return
            
            if not (conflicts_detected and auto_suggest_updates):
                # 没有冲突或不需要自动建议，提供保存选项
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("💾 保存当前章节", type="primary", key=f"save_final_{chapter_idx}"):
                        save_story_to_history(f"智能编辑第{chapter_idx+1}章", old_story_data)
                        st.session_state.story_data[chapter_idx]['plot'] = new_plot
                        st.session_state[f'edit_story_{chapter_idx}'] = False
                        
                        if not conflicts_detected:
                            st.success(f"✅ 第{chapter_idx+1}章修改已保存（未检测到冲突）")
                        else:
                            st.success(f"✅ 第{chapter_idx+1}章修改已保存")
                        
                        print(f"💾 [智能故事编辑] 保存第{chapter_idx+1}章修改: {len(new_plot)} 字")
                        st.rerun()
                
                with col2:
                    if st.button("❌ 取消修改", key=f"cancel_final_{chapter_idx}"):
                        st.session_state[f'edit_story_{chapter_idx}'] = False
                        st.info("已取消修改")
                        st.rerun()
                
    except Exception as e:
        st.error(f"❌ 智能保存失败: {str(e)}")
        print(f"❌ [智能故事编辑] 智能保存失败: {str(e)}")

def detect_plot_conflicts_and_suggest_updates(chapter_idx, old_plot, new_plot, custom_instruction=""):
    """增强版冲突检测 - 整合专业分析工具"""
    try:
        print(f"🔍 [增强冲突检测] 开始多维度分析第{chapter_idx+1}章的修改")
        
        # 1. 基础语义冲突检测（原有方法）
        basic_conflicts = detect_basic_semantic_conflicts(chapter_idx, old_plot, new_plot, custom_instruction)
        
        # 2. 事件一致性检测（使用story_evaluator）
        event_conflicts = detect_event_consistency_conflicts(chapter_idx, old_plot, new_plot)
        
        # 3. 连贯性检测（使用hred_coherence_evaluator）
        coherence_conflicts = detect_coherence_conflicts(chapter_idx, old_plot, new_plot)
        
        # 4. 情感弧线检测（使用emotional_arc_analyzer）
        emotional_conflicts = detect_emotional_arc_conflicts(chapter_idx, old_plot, new_plot)
        
        # 5. 角色状态一致性检测（使用character_state_tracker）
        character_state_conflicts = detect_character_state_conflicts(chapter_idx, old_plot, new_plot)
        
        # 整合所有检测结果
        integrated_result = integrate_conflict_analysis_results(
            basic_conflicts, event_conflicts, coherence_conflicts, 
            emotional_conflicts, character_state_conflicts
        )
        
        print(f"✅ [增强冲突检测] 多维度分析完成")
        
        has_conflicts = integrated_result.get('has_conflicts', False)
        print(f"🔍 [增强冲突检测] 最终结果: has_conflicts={has_conflicts}")
        print(f"🔍 [增强冲突检测] 返回数据: {integrated_result}")
        return has_conflicts, integrated_result
            
    except Exception as e:
        print(f"❌ [增强冲突检测] 检测失败: {str(e)}")
        # 回退到基础检测
        return detect_basic_semantic_conflicts(chapter_idx, old_plot, new_plot, custom_instruction)

def detect_basic_semantic_conflicts(chapter_idx, old_plot, new_plot, custom_instruction=""):
    """基础语义冲突检测（原有方法）"""
    try:
        from src.utils.utils import generate_response, convert_json
        
        print(f"  📝 [基础检测] 语义冲突分析")
        
        # 构建分析数据
        current_outline = st.session_state.outline_data
        current_characters = st.session_state.characters_data
        current_story = st.session_state.story_data
        
        # 构建冲突检测提示
        analysis_prompt = f"""
你是一位专业的故事编辑。用户修改了故事的第{chapter_idx+1}章内容，请分析这个修改是否会与其他部分产生冲突，并提供更新建议。

**原始章节内容:**
{old_plot}

**修改后章节内容:**
{new_plot}

**当前大纲:**
{json.dumps(current_outline, ensure_ascii=False, indent=2)}

**当前角色设定:**
{json.dumps(current_characters, ensure_ascii=False, indent=2)}

**其他章节摘要:**
{json.dumps([{"chapter": i+1, "title": ch.get('title', ''), "plot_summary": ch.get('plot', '')[:200]} for i, ch in enumerate(current_story) if i != chapter_idx], ensure_ascii=False, indent=2)}

**用户自定义指令:**
{custom_instruction if custom_instruction else "无"}

请分析以下方面的潜在冲突：
1. **角色设定冲突**: 修改是否改变了角色的基本属性、动机或关系
2. **情节逻辑冲突**: 修改是否与其他章节的情节发展产生矛盾
3. **大纲一致性**: 修改是否偏离了原始大纲的设定
4. **时间线冲突**: 修改是否影响了故事的时间顺序或因果关系
5. **世界观冲突**: 修改是否改变了故事的基本设定或规则

返回JSON格式：
{{
    "has_conflicts": true/false,
    "conflicts": [
        "具体的冲突描述"
    ],
    "suggestions": {{
        "outline_updates": [
            "大纲需要的具体修改建议"
        ],
        "character_updates": [
            "角色设定需要的具体修改建议"
        ],
        "other_chapters": [
            {{
                "chapter": "章节编号",
                "suggestion": "该章节需要的具体修改建议"
            }}
        ]
    }},
    "severity": "low/medium/high",
    "summary": "冲突检测总结",
    "analysis_type": "basic_semantic"
}}

只返回JSON，不要其他解释。
"""
        
        # 调用后端分析
        msg = [{"role": "user", "content": analysis_prompt}]
        response = generate_response(msg)
        analysis_result = convert_json(response)
        
        if analysis_result and isinstance(analysis_result, dict):
            has_conflicts = analysis_result.get('has_conflicts', False)
            return has_conflicts, analysis_result
        else:
            return False, {}
            
    except Exception as e:
        print(f"❌ [基础检测] 语义分析失败: {str(e)}")
        return False, {}

def detect_event_consistency_conflicts(chapter_idx, old_plot, new_plot):
    """事件一致性冲突检测 - 使用story_evaluator"""
    try:
        print(f"  📊 [事件检测] 事件一致性分析")
        
        # 创建临时故事数据进行事件提取
        temp_story_old = st.session_state.story_data.copy()
        temp_story_new = st.session_state.story_data.copy()
        temp_story_new[chapter_idx]['plot'] = new_plot
        
        # 使用story_evaluator提取事件
        from src.analysis.story_evaluator import extract_events_no_hallucination
        
        # 提取修改前后的事件
        events_old = extract_events_no_hallucination(temp_story_old)
        events_new = extract_events_no_hallucination(temp_story_new)
        
        # 分析事件变化
        event_conflicts = analyze_event_changes(events_old, events_new, chapter_idx)
        
        return event_conflicts
        
    except Exception as e:
        print(f"❌ [事件检测] 事件分析失败: {str(e)}")
        return {"has_conflicts": False, "analysis_type": "event_consistency", "error": str(e)}

def detect_coherence_conflicts(chapter_idx, old_plot, new_plot):
    """连贯性冲突检测 - 使用hred_coherence_evaluator"""
    try:
        print(f"  🔗 [连贯性检测] 语义连贯性分析")
        
        # 创建临时故事数据
        temp_story_old = st.session_state.story_data.copy()
        temp_story_new = st.session_state.story_data.copy()
        temp_story_new[chapter_idx]['plot'] = new_plot
        
        # 使用HRED连贯性评估器
        from src.analysis.hred_coherence_evaluator import HREDCoherenceEvaluator
        
        evaluator = HREDCoherenceEvaluator()
        
        # 计算修改前后的连贯性分数
        coherence_old = evaluator.evaluate_story_coherence(temp_story_old)
        coherence_new = evaluator.evaluate_story_coherence(temp_story_new)
        
        # 分析连贯性变化
        coherence_conflicts = analyze_coherence_changes(coherence_old, coherence_new, chapter_idx)
        
        return coherence_conflicts
        
    except Exception as e:
        print(f"❌ [连贯性检测] 连贯性分析失败: {str(e)}")
        return {"has_conflicts": False, "analysis_type": "coherence", "error": str(e)}

def detect_emotional_arc_conflicts(chapter_idx, old_plot, new_plot):
    """情感弧线冲突检测 - 使用emotional_arc_analyzer"""
    try:
        print(f"  💝 [情感检测] 情感弧线分析")
        
        # 创建临时故事数据
        temp_story_old = st.session_state.story_data.copy()
        temp_story_new = st.session_state.story_data.copy()
        temp_story_new[chapter_idx]['plot'] = new_plot
        
        # 使用情感弧线分析器
        from src.analysis.emotional_arc_analyzer import DualMethodEmotionalAnalyzer
        
        analyzer = DualMethodEmotionalAnalyzer()
        
        # 转换数据格式以适配情感分析器
        def convert_story_format(story_data):
            converted = []
            for i, chapter in enumerate(story_data):
                converted.append({
                    'chapter_num': i + 1,
                    'title': chapter.get('title', f'第{i+1}章'),
                    'content': chapter.get('plot', '')
                })
            return converted
        
        # 分析修改前后的情感弧线
        emotions_old = analyzer.analyze_story_dual_method(convert_story_format(temp_story_old))
        emotions_new = analyzer.analyze_story_dual_method(convert_story_format(temp_story_new))
        
        # 分析情感变化
        emotional_conflicts = analyze_emotional_changes(emotions_old, emotions_new, chapter_idx)
        
        return emotional_conflicts
        
    except Exception as e:
        print(f"❌ [情感检测] 情感分析失败: {str(e)}")
        return {"has_conflicts": False, "analysis_type": "emotional_arc", "error": str(e)}

def detect_character_state_conflicts(chapter_idx, old_plot, new_plot):
    """角色状态一致性检测 - 使用character_state_tracker"""
    try:
        print(f"  👥 [角色状态检测] 角色状态一致性分析")
        
        # 这里需要对话数据，如果没有则跳过
        if not hasattr(st.session_state, 'dialogue_data') or not st.session_state.get('dialogue_data'):
            return {"has_conflicts": False, "analysis_type": "character_state", "skipped": "无对话数据"}
        
        # 使用角色状态追踪器
        from src.analysis.character_state_tracker import extract_character_state_timeline
        
        # 分析角色状态变化
        character_conflicts = analyze_character_state_changes(chapter_idx, old_plot, new_plot)
        
        return character_conflicts
        
    except Exception as e:
        print(f"❌ [角色状态检测] 角色状态分析失败: {str(e)}")
        return {"has_conflicts": False, "analysis_type": "character_state", "error": str(e)}

def analyze_event_changes(events_old, events_new, chapter_idx):
    """分析事件变化"""
    try:
        # 提取事件描述进行比较
        events_old_desc = [e.get('event', '') for e in events_old if isinstance(e, dict)]
        events_new_desc = [e.get('event', '') for e in events_new if isinstance(e, dict)]
        
        # 找出新增、删除、修改的事件
        added_events = [e for e in events_new_desc if e not in events_old_desc]
        removed_events = [e for e in events_old_desc if e not in events_new_desc]
        
        has_conflicts = len(added_events) > 0 or len(removed_events) > 0
        
        conflicts = []
        if added_events:
            conflicts.append(f"新增事件: {', '.join(added_events[:3])}{'...' if len(added_events) > 3 else ''}")
        if removed_events:
            conflicts.append(f"删除事件: {', '.join(removed_events[:3])}{'...' if len(removed_events) > 3 else ''}")
        
        return {
            "has_conflicts": has_conflicts,
            "analysis_type": "event_consistency",
            "conflicts": conflicts,
            "added_events": added_events,
            "removed_events": removed_events,
            "severity": "high" if len(removed_events) > 2 else ("medium" if has_conflicts else "low")
        }
        
    except Exception as e:
        return {"has_conflicts": False, "analysis_type": "event_consistency", "error": str(e)}

def analyze_coherence_changes(coherence_old, coherence_new, chapter_idx):
    """分析连贯性变化"""
    try:
        # 比较连贯性分数
        old_score = coherence_old.get('overall_coherence_score', 0)
        new_score = coherence_new.get('overall_coherence_score', 0)
        
        score_change = new_score - old_score
        threshold = 0.1  # 连贯性变化阈值
        
        has_conflicts = score_change < -threshold
        
        conflicts = []
        if has_conflicts:
            conflicts.append(f"连贯性下降: {old_score:.3f} → {new_score:.3f} (下降 {abs(score_change):.3f})")
        
        return {
            "has_conflicts": has_conflicts,
            "analysis_type": "coherence",
            "conflicts": conflicts,
            "old_score": old_score,
            "new_score": new_score,
            "score_change": score_change,
            "severity": "high" if score_change < -0.2 else ("medium" if has_conflicts else "low")
        }
        
    except Exception as e:
        return {"has_conflicts": False, "analysis_type": "coherence", "error": str(e)}

def analyze_emotional_changes(emotions_old, emotions_new, chapter_idx):
    """分析情感弧线变化"""
    try:
        # 检查分析结果是否包含错误
        if isinstance(emotions_old, dict) and "error" in emotions_old:
            return {"has_conflicts": False, "analysis_type": "emotional_arc", "error": emotions_old["error"]}
        
        if isinstance(emotions_new, dict) and "error" in emotions_new:
            return {"has_conflicts": False, "analysis_type": "emotional_arc", "error": emotions_new["error"]}
        
        # 获取RoBERTa分数（主要方法）
        old_scores = []
        new_scores = []
        
        # 从chapter_analysis中提取分数
        if isinstance(emotions_old, dict) and "chapter_analysis" in emotions_old:
            old_scores = [ch.get('roberta_score', 0) for ch in emotions_old['chapter_analysis']]
        
        if isinstance(emotions_new, dict) and "chapter_analysis" in emotions_new:
            new_scores = [ch.get('roberta_score', 0) for ch in emotions_new['chapter_analysis']]
        
        if len(old_scores) != len(new_scores):
            return {"has_conflicts": True, "analysis_type": "emotional_arc", 
                   "conflicts": ["情感弧线长度发生变化"], "severity": "medium"}
        
        # 计算指定章节的情感变化幅度
        if len(old_scores) > chapter_idx and len(new_scores) > chapter_idx:
            old_emotion = old_scores[chapter_idx]
            new_emotion = new_scores[chapter_idx]
            
            emotion_change = abs(new_emotion - old_emotion)
            threshold = 0.3  # 情感变化阈值
            
            has_conflicts = emotion_change > threshold
            
            conflicts = []
            if has_conflicts:
                conflicts.append(f"第{chapter_idx+1}章情感剧烈变化: {old_emotion:.3f} → {new_emotion:.3f}")
            
            return {
                "has_conflicts": has_conflicts,
                "analysis_type": "emotional_arc",
                "conflicts": conflicts,
                "emotion_change": emotion_change,
                "old_emotion": old_emotion,
                "new_emotion": new_emotion,
                "severity": "high" if emotion_change > 0.5 else ("medium" if has_conflicts else "low")
            }
        
        return {"has_conflicts": False, "analysis_type": "emotional_arc"}
        
    except Exception as e:
        print(f"❌ [情感分析] 分析情感变化失败: {str(e)}")
        return {"has_conflicts": False, "analysis_type": "emotional_arc", "error": str(e)}

def analyze_character_state_changes(chapter_idx, old_plot, new_plot):
    """分析角色状态变化"""
    try:
        # 简单的角色状态变化检测
        # 这里可以进一步集成character_state_tracker的功能
        
        # 提取角色名称
        character_names = [char.get('name', '') for char in st.session_state.characters_data]
        
        conflicts = []
        for char_name in character_names:
            if char_name in old_plot and char_name in new_plot:
                # 检查角色在修改前后的上下文变化
                old_context = extract_character_context(old_plot, char_name)
                new_context = extract_character_context(new_plot, char_name)
                
                if old_context != new_context:
                    conflicts.append(f"角色 {char_name} 的行为状态发生变化")
        
        has_conflicts = len(conflicts) > 0
        
        return {
            "has_conflicts": has_conflicts,
            "analysis_type": "character_state",
            "conflicts": conflicts,
            "severity": "medium" if has_conflicts else "low"
        }
        
    except Exception as e:
        return {"has_conflicts": False, "analysis_type": "character_state", "error": str(e)}

def extract_character_context(text, character_name):
    """提取角色在文本中的上下文"""
    # 简单实现：查找角色名称前后的文本
    import re
    pattern = f".{{0,50}}{re.escape(character_name)}.{{0,50}}"
    matches = re.findall(pattern, text, re.IGNORECASE)
    return ' '.join(matches)

def integrate_conflict_analysis_results(basic_conflicts, event_conflicts, coherence_conflicts, 
                                      emotional_conflicts, character_state_conflicts):
    """整合所有冲突分析结果"""
    try:
        # 收集所有冲突
        all_conflicts = []
        all_suggestions = {"outline_updates": [], "character_updates": [], "other_chapters": []}
        
        # 计算综合严重程度
        severity_scores = {"low": 1, "medium": 2, "high": 3}
        max_severity = 0
        
        # 处理各种分析结果
        analysis_results = [
            ("基础语义", basic_conflicts[1] if isinstance(basic_conflicts, tuple) else basic_conflicts),
            ("事件一致性", event_conflicts),
            ("连贯性", coherence_conflicts), 
            ("情感弧线", emotional_conflicts),
            ("角色状态", character_state_conflicts)
        ]
        
        for analysis_name, result in analysis_results:
            if isinstance(result, dict) and result.get('has_conflicts', False):
                # 添加冲突描述
                conflicts = result.get('conflicts', [])
                for conflict in conflicts:
                    all_conflicts.append(f"[{analysis_name}] {conflict}")
                
                # 更新严重程度
                severity = result.get('severity', 'low')
                max_severity = max(max_severity, severity_scores.get(severity, 1))
                
                # 合并建议
                if 'suggestions' in result:
                    suggestions = result['suggestions']
                    if isinstance(suggestions, dict):
                        for key in all_suggestions:
                            if key in suggestions:
                                all_suggestions[key].extend(suggestions[key])
        
        # 确定最终严重程度
        severity_map = {1: "low", 2: "medium", 3: "high"}
        final_severity = severity_map[max_severity]
        
        # 生成综合报告
        has_conflicts = len(all_conflicts) > 0
        
        summary = f"多维度分析完成，检测到 {len(all_conflicts)} 个潜在冲突"
        if has_conflicts:
            summary += f"，严重程度: {final_severity}"
        
        return {
            "has_conflicts": has_conflicts,
            "conflicts": all_conflicts,
            "suggestions": all_suggestions,
            "severity": final_severity,
            "summary": summary,
            "analysis_type": "integrated_multi_dimensional",
            "detailed_results": {
                "basic_semantic": basic_conflicts[1] if isinstance(basic_conflicts, tuple) else basic_conflicts,
                "event_consistency": event_conflicts,
                "coherence": coherence_conflicts,
                "emotional_arc": emotional_conflicts,
                "character_state": character_state_conflicts
            }
        }
        
    except Exception as e:
        print(f"❌ [结果整合] 整合分析结果失败: {str(e)}")
        # 回退到基础结果
        if isinstance(basic_conflicts, tuple):
            return basic_conflicts[1]
        else:
            return {"has_conflicts": False, "error": f"整合失败: {str(e)}"}

def execute_cascade_updates(chapter_idx, new_plot, update_suggestions, custom_instruction=""):
    """执行级联更新"""
    print(f"🚀🚀🚀 [级联更新] 函数被调用！章节: {chapter_idx}, 指令: {custom_instruction[:50] if custom_instruction else 'None'}")
    print(f"📊 [级联更新] 接收到的更新建议: {type(update_suggestions)} - {update_suggestions}")
    
    try:
        with st.spinner("🚀 正在执行智能更新..."):
            print(f"🚀 [级联更新] 开始执行智能更新")
            print(f"📊 [级联更新] 更新建议数据结构: {update_suggestions}")
            
            # 保存更新前的完整状态
            old_story_data = st.session_state.story_data.copy()
            old_outline_data = st.session_state.outline_data.copy()
            old_characters_data = st.session_state.characters_data.copy()
            
            save_story_to_history(f"智能更新前状态(第{chapter_idx+1}章)", old_story_data)
            
            update_results = {
                'story_updated': False,
                'outline_updated': False,
                'characters_updated': False,
                'other_chapters_updated': []
            }
            
            # 1. 首先更新当前章节
            st.session_state.story_data[chapter_idx]['plot'] = new_plot
            update_results['story_updated'] = True
            
            # 2. 更新其他章节（如果有建议）
            other_chapter_updates = update_suggestions.get('other_chapters', [])
            if not other_chapter_updates and 'suggestions' in update_suggestions:
                other_chapter_updates = update_suggestions['suggestions'].get('other_chapters', [])
            
            if other_chapter_updates:
                st.info(f"🔄 正在更新相关章节...（共{len(other_chapter_updates)}个章节）")
                print(f"📋 [级联更新] 需要更新的章节: {other_chapter_updates}")
                
                for i, chapter_update in enumerate(other_chapter_updates):
                    try:
                        print(f"🔄 [级联更新] 处理第{i+1}个章节更新: {chapter_update}")
                        
                        # 解析章节编号
                        chapter_str = str(chapter_update.get('chapter', '0'))
                        # 提取数字（可能是"第1章"或"Chapter 1"格式）
                        import re
                        chapter_match = re.search(r'\d+', chapter_str)
                        if chapter_match:
                            target_chapter = int(chapter_match.group()) - 1
                        else:
                            print(f"⚠️ [级联更新] 无法解析章节编号: {chapter_str}")
                            continue
                        
                        print(f"📍 [级联更新] 目标章节: {target_chapter+1} (索引{target_chapter})")
                        
                        if 0 <= target_chapter < len(st.session_state.story_data) and target_chapter != chapter_idx:
                            suggestion = chapter_update.get('suggestion', '')
                            print(f"💡 [级联更新] 更新建议: {suggestion[:100]}...")
                            
                            # 显示更新进度
                            with st.spinner(f"🔄 正在重新生成第{target_chapter+1}章..."):
                                # 使用LLM重新生成该章节
                                updated_chapter = update_single_chapter_with_context(
                                    target_chapter, suggestion, new_plot, custom_instruction
                                )
                                
                                if updated_chapter:
                                    st.session_state.story_data[target_chapter] = updated_chapter
                                    update_results['other_chapters_updated'].append(target_chapter + 1)
                                    print(f"✅ [级联更新] 第{target_chapter+1}章更新成功")
                                    st.success(f"✅ 第{target_chapter+1}章已重新生成")
                                else:
                                    print(f"❌ [级联更新] 第{target_chapter+1}章更新失败：未返回有效内容")
                                    st.warning(f"⚠️ 第{target_chapter+1}章更新失败")
                        else:
                            print(f"⚠️ [级联更新] 跳过无效章节: {target_chapter+1}")
                                
                    except Exception as e:
                        print(f"❌ [级联更新] 更新章节失败: {str(e)}")
                        st.error(f"❌ 更新章节时出错: {str(e)}")
                
                print(f"📊 [级联更新] 章节更新完成，成功更新: {update_results['other_chapters_updated']}")
            
            # 3. 更新角色设定（如果有建议）
            character_updates = update_suggestions.get('character_updates', [])
            if not character_updates and 'suggestions' in update_suggestions:
                character_updates = update_suggestions['suggestions'].get('character_updates', [])
            
            if character_updates:
                st.info("👥 正在更新角色设定...")
                
                updated_characters = update_characters_with_context(character_updates, new_plot, custom_instruction)
                if updated_characters:
                    save_characters_to_history(f"智能更新角色(第{chapter_idx+1}章修改)", st.session_state.characters_data.copy())
                    st.session_state.characters_data = updated_characters
                    update_results['characters_updated'] = True
            
            # 4. 更新大纲（如果有建议）
            outline_updates = update_suggestions.get('outline_updates', [])
            if not outline_updates and 'suggestions' in update_suggestions:
                outline_updates = update_suggestions['suggestions'].get('outline_updates', [])
            
            if outline_updates:
                st.info("📚 正在更新大纲...")
                
                updated_outline = update_outline_with_context(outline_updates, new_plot, custom_instruction)
                if updated_outline:
                    save_to_history(f"智能更新大纲(第{chapter_idx+1}章修改)", st.session_state.outline_data.copy())
                    st.session_state.outline_data = updated_outline
                    update_results['outline_updated'] = True
            
            # 清除编辑状态
            st.session_state[f'edit_story_{chapter_idx}'] = False
            
            # 显示更新结果
            st.markdown("---")
            st.markdown("## ✅ 智能更新完成")
            
            st.success(f"✅ 第{chapter_idx+1}章已更新")
            
            if update_results['other_chapters_updated']:
                updated_chapters_str = ', '.join([f"第{ch}章" for ch in update_results['other_chapters_updated']])
                st.success(f"✅ 相关章节已更新: {updated_chapters_str}")
            
            if update_results['characters_updated']:
                st.success("✅ 角色设定已更新")
            
            if update_results['outline_updated']:
                st.success("✅ 大纲已更新")
            
            print(f"🎉 [级联更新] 智能更新完成: {update_results}")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 执行智能更新失败: {str(e)}")
        print(f"❌ [级联更新] 执行失败: {str(e)}")

def update_single_chapter_with_context(chapter_idx, suggestion, reference_plot, custom_instruction=""):
    """基于上下文更新单个章节"""
    try:
        from src.generation.expand_story import expand_story_v1
        
        # 获取对应的大纲章节
        if chapter_idx >= len(st.session_state.outline_data):
            return None
            
        outline_chapter = st.session_state.outline_data[chapter_idx]
        
        # 构建智能更新指令 - 针对plot修改的级联更新
        update_instruction = f"""
重要：基于故事情节的关键修改，请重新生成这个章节的详细内容。

**故事修改背景**：
{suggestion}

**修改后的相关章节内容（作为上下文）**：
{reference_plot[:800] if reference_plot else "无"}

**当前章节原始设定**：
- 章节标题: {outline_chapter.get('title', '')}
- 章节摘要: {outline_chapter.get('summary', '')}

**整体故事角色**：
{'; '.join([f"{char.get('name', '')}: {char.get('role', '')}" for char in st.session_state.characters_data[:5]])}

**重新生成要求**：
1. 必须体现上述故事修改的影响
2. 保持与新的故事逻辑完全一致
3. 维持章节在整体故事中的作用
4. 确保角色行为符合修改后的设定
5. 生成详细完整的故事内容（至少500字）

**用户补充指令**：
{custom_instruction if custom_instruction else "无特殊要求"}

请基于以上要求，重新创作这个章节的完整故事内容。
"""
        
        # 调用后端重新生成
        print(f"🚀 [章节更新] 开始调用expand_story_v1")
        print(f"📝 [章节更新] 更新指令长度: {len(update_instruction)} 字符")
        
        result = expand_story_v1(
            [outline_chapter], 
            st.session_state.characters_data,
            custom_instruction=update_instruction
        )
        
        print(f"📊 [章节更新] expand_story_v1返回: {type(result)}")
        
        if result and len(result) > 0:
            updated_chapter = result[0]
            updated_chapter.setdefault("chapter_id", outline_chapter["chapter_id"])
            updated_chapter.setdefault("title", outline_chapter["title"])
            
            # 验证生成的内容
            new_plot = updated_chapter.get('plot', '')
            print(f"✅ [章节更新] 章节{chapter_idx+1}重新生成成功")
            print(f"📝 [章节更新] 新plot长度: {len(new_plot)} 字符")
            print(f"📖 [章节更新] 新plot预览: {new_plot[:200]}...")
            
            return updated_chapter
        
        print(f"❌ [章节更新] expand_story_v1未返回有效结果")
        return None
        
    except Exception as e:
        print(f"❌ [章节更新] 更新第{chapter_idx+1}章失败: {str(e)}")
        return None

def update_characters_with_context(character_updates, reference_plot, custom_instruction=""):
    """基于上下文更新角色设定"""
    try:
        from src.utils.utils import generate_response, convert_json
        
        # 构建角色更新提示
        update_prompt = f"""
基于以下变更更新角色设定：

变更说明：
{chr(10).join(character_updates)}

参考修改：{reference_plot[:300]}...
用户指令：{custom_instruction}

当前角色设定：
{json.dumps(st.session_state.characters_data, ensure_ascii=False, indent=2)}

请更新相关角色的设定，确保与故事变更保持一致。

返回完整的更新后角色列表，格式与原始相同：
[
    {{
        "name": "角色名",
        "role": "角色定位", 
        "traits": "角色特征",
        "background": "角色背景",
        "motivation": "角色动机"
    }}
]

只返回JSON，不要其他解释。
"""
        
        msg = [{"role": "user", "content": update_prompt}]
        response = generate_response(msg)
        updated_characters = convert_json(response)
        
        if updated_characters and isinstance(updated_characters, list):
            return updated_characters
        
        return None
        
    except Exception as e:
        print(f"❌ [角色更新] 更新失败: {str(e)}")
        return None

def update_outline_with_context(outline_updates, reference_plot, custom_instruction=""):
    """基于上下文更新大纲"""
    try:
        from src.utils.utils import generate_response, convert_json
        
        # 构建大纲更新提示
        update_prompt = f"""
基于以下变更更新故事大纲：

变更说明：
{chr(10).join(outline_updates)}

参考修改：{reference_plot[:300]}...
用户指令：{custom_instruction}

当前大纲：
{json.dumps(st.session_state.outline_data, ensure_ascii=False, indent=2)}

请更新相关章节的大纲，确保与故事变更保持一致。

返回完整的更新后大纲，格式与原始相同：
[
    {{
        "chapter_id": "Chapter X",
        "title": "章节标题",
        "summary": "章节摘要"
    }}
]

保留所有现有字段（如narrative_role等）。

只返回JSON，不要其他解释。
"""
        
        msg = [{"role": "user", "content": update_prompt}]
        response = generate_response(msg)
        updated_outline = convert_json(response)
        
        if updated_outline and isinstance(updated_outline, list):
            return updated_outline
        
        return None
        
    except Exception as e:
        print(f"❌ [大纲更新] 更新失败: {str(e)}")
        return None

def save_conflict_suggestions(chapter_idx, update_suggestions, new_plot, custom_instruction=""):
    """保存冲突分析建议"""
    try:
        import json
        import os
        from datetime import datetime
        
        print(f"💾💾💾 [建议保存] ===== 开始保存第{chapter_idx+1}章的建议 =====")
        print(f"💾 [建议保存] 建议数据类型: {type(update_suggestions)}")
        print(f"💾 [建议保存] 建议数据内容: {str(update_suggestions)[:200]}...")
        print(f"💾 [建议保存] 新plot长度: {len(new_plot)}")
        print(f"💾 [建议保存] 自定义指令: {custom_instruction}")
        
        # 获取当前工作目录的绝对路径
        current_dir = os.getcwd()
        print(f"💾 [建议保存] 当前工作目录: {current_dir}")
        
        # 使用当前故事版本目录 - 改为绝对路径
        current_version = st.session_state.get('current_version', 'unknown')
        if current_version and current_version != 'unknown':
            suggestions_dir = os.path.join(current_dir, "data", "output", current_version)
        else:
            suggestions_dir = os.path.join(current_dir, "data", "saved_suggestions")
        
        # 创建目录并显示详细信息
        print(f"💾 [建议保存] 目标目录: {suggestions_dir}")
        os.makedirs(suggestions_dir, exist_ok=True)
        print(f"💾 [建议保存] 目录创建成功")
        
        # 确保update_suggestions不为空
        if not update_suggestions:
            print("⚠️ [建议保存] update_suggestions为空，使用默认数据")
            update_suggestions = {
                "message": "无冲突检测数据", 
                "conflicts": [], 
                "suggestions": {},
                "has_conflicts": False,
                "analysis_type": "empty_fallback"
            }
        
        # 构建保存数据
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "chapter_idx": chapter_idx,
            "chapter_title": st.session_state.story_data[chapter_idx].get('title', f'第{chapter_idx+1}章') if len(st.session_state.story_data) > chapter_idx else f'第{chapter_idx+1}章',
            "new_plot": new_plot,
            "custom_instruction": custom_instruction,
            "update_suggestions": update_suggestions,
            "story_version": current_version,
            "total_chapters": len(st.session_state.get('story_data', [])),
            "conflicts_count": len(update_suggestions.get('conflicts', [])),
            "suggestions_summary": {
                "outline_updates": len(update_suggestions.get('suggestions', {}).get('outline_updates', [])),
                "character_updates": len(update_suggestions.get('suggestions', {}).get('character_updates', [])),
                "other_chapters": len(update_suggestions.get('suggestions', {}).get('other_chapters', []))
            },
            "save_info": {
                "save_directory": suggestions_dir,
                "working_directory": current_dir,
                "version": current_version
            }
        }
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"suggestions_ch{chapter_idx+1}_{timestamp}.json"
        filepath = os.path.join(suggestions_dir, filename)
        
        print(f"💾 [建议保存] 完整文件路径: {filepath}")
        
        # 检查目录权限
        if not os.access(suggestions_dir, os.W_OK):
            error_msg = f"无法写入目录: {suggestions_dir}"
            print(f"❌ [建议保存] {error_msg}")
            st.error(f"❌ 保存失败: {error_msg}")
            return False
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        # 验证文件是否成功创建
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"💾 [建议保存] 文件已成功写入: {filepath}")
            print(f"💾 [建议保存] 文件大小: {file_size} 字节")
            
            st.success(f"✅ 分析建议已保存成功!")
            st.info(f"📁 保存位置: {filepath}")
            st.info(f"📊 文件大小: {file_size} 字节")
            
            # 显示保存详情
            with st.expander("📄 保存详情", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.json({
                        "保存文件": filename,
                        "章节": f"第{chapter_idx+1}章",
                        "保存时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                with col2:
                    st.json({
                        "冲突数量": len(update_suggestions.get('conflicts', [])),
                        "更新建议": save_data['suggestions_summary'],
                        "文件路径": filepath
                    })
            
            print(f"💾💾💾 [建议保存] ===== 保存成功 ===== : {filepath}")
            return True
        else:
            error_msg = f"文件创建失败: {filepath}"
            print(f"❌ [建议保存] {error_msg}")
            st.error(f"❌ 保存失败: {error_msg}")
            return False
        
    except Exception as e:
        error_msg = f"保存建议失败: {str(e)}"
        print(f"❌ [建议保存] {error_msg}")
        st.error(f"❌ {error_msg}")
        
        # 显示详细错误信息
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ [建议保存] 详细错误: {error_details}")
        
        with st.expander("🔍 错误详情", expanded=False):
            st.code(error_details, language="python")
        
        return False
    
def export_suggestions_file(chapter_idx, update_suggestions, new_plot, custom_instruction=""):
    """导出建议为下载文件"""
    try:
        import json
        from datetime import datetime
        
        print(f"📥📥📥 [建议导出] ===== 开始导出第{chapter_idx+1}章的建议文件 =====")
        print(f"📥 [建议导出] 建议数据类型: {type(update_suggestions)}")
        print(f"📥 [建议导出] 建议数据内容: {str(update_suggestions)[:200]}...")
        print(f"📥 [建议导出] 新plot长度: {len(new_plot)}")
        
        # 确保update_suggestions不为空
        if not update_suggestions:
            update_suggestions = {"message": "无冲突检测数据", "conflicts": [], "suggestions": {}}
        
        # 构建导出数据
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "description": f"第{chapter_idx+1}章智能建议文件",
                "chapter_idx": chapter_idx,
                "story_version": st.session_state.get('current_version', 'unknown')
            },
            "chapter_data": {
                "chapter_idx": chapter_idx,
                "chapter_title": st.session_state.story_data[chapter_idx].get('title', f'第{chapter_idx+1}章'),
                "new_plot": new_plot,
                "custom_instruction": custom_instruction
            },
            "analysis_results": update_suggestions,
            "context_info": {
                "total_chapters": len(st.session_state.story_data),
                "characters_count": len(st.session_state.characters_data),
                "outline_chapters": len(st.session_state.outline_data)
            }
        }
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"智能建议_第{chapter_idx+1}章_{timestamp}.json"
        
        # 转换为JSON字符串
        json_string = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        # 提供下载
        st.download_button(
            label="📥 下载建议文件",
            data=json_string,
            file_name=filename,
            mime="application/json",
            help="下载包含完整分析结果的建议文件",
            key=f"download_suggestions_{chapter_idx}"
        )
        
        st.success(f"✅ 建议文件已准备下载: {filename}")
        
        # 显示导出信息
        with st.expander("📄 导出详情", expanded=False):
            st.json({
                "文件名": filename,
                "章节": f"第{chapter_idx+1}章",
                "冲突数量": len(update_suggestions.get('conflicts', [])),
                "建议类型": list(update_suggestions.get('suggestions', {}).keys()),
                "文件大小": f"{len(json_string)} 字符"
            })
        
    except Exception as e:
        st.error(f"❌ 导出建议文件失败: {str(e)}")
        print(f"❌ [建议导出] 导出失败: {str(e)}")

def execute_uploaded_suggestions(chapter_idx, uploaded_file, current_plot):
    """执行上传的建议文件"""
    try:
        import json
        
        # 重置文件指针
        uploaded_file.seek(0)
        
        # 读取文件内容
        file_content = uploaded_file.read()
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8')
        
        # 解析JSON
        suggestions_data = json.loads(file_content)
        
        # 验证文件格式
        if not validate_suggestions_file(suggestions_data):
            st.error("❌ 无效的建议文件格式")
            return
        
        # 显示建议文件信息
        st.markdown("---")
        st.markdown("### 📋 建议文件信息")
        
        export_info = suggestions_data.get('export_info', {})
        chapter_data = suggestions_data.get('chapter_data', {})
        analysis_results = suggestions_data.get('analysis_results', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("导出时间", export_info.get('timestamp', '未知')[:19])
            st.metric("目标章节", f"第{chapter_data.get('chapter_idx', 0)+1}章")
        
        with col2:
            st.metric("冲突数量", len(analysis_results.get('conflicts', [])))
            st.metric("严重程度", analysis_results.get('severity', '未知'))
        
        with col3:
            suggestions = analysis_results.get('suggestions', {})
            st.metric("其他章节", len(suggestions.get('other_chapters', [])))
            st.metric("角色更新", len(suggestions.get('character_updates', [])))
        
        # 显示主要冲突
        if analysis_results.get('conflicts'):
            st.markdown("**⚠️ 主要冲突:**")
            for conflict in analysis_results['conflicts'][:3]:
                st.warning(f"• {conflict}")
        
        # 显示更新建议
        if suggestions.get('other_chapters'):
            st.markdown("**📖 其他章节更新建议:**")
            for chapter_update in suggestions['other_chapters'][:3]:
                chapter_num = chapter_update.get('chapter', '未知')
                suggestion = chapter_update.get('suggestion', '')
                st.info(f"• 第{chapter_num}章: {suggestion[:100]}{'...' if len(suggestion) > 100 else ''}")
        
        # 执行选项
        st.markdown("---")
        st.markdown("### 🚀 执行选项")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 使用文件中的内容", type="primary", key=f"execute_file_content_{chapter_idx}"):
                # 使用文件中保存的plot和指令
                file_plot = chapter_data.get('new_plot', current_plot)
                file_instruction = chapter_data.get('custom_instruction', '')
                
                st.session_state[f'edit_story_{chapter_idx}'] = False
                execute_cascade_updates(chapter_idx, file_plot, analysis_results, file_instruction)
                st.rerun()
        
        with col2:
            if st.button("🔄 使用当前编辑内容", key=f"execute_current_content_{chapter_idx}"):
                # 使用当前编辑的plot但文件中的建议
                st.session_state[f'edit_story_{chapter_idx}'] = False
                execute_cascade_updates(chapter_idx, current_plot, analysis_results, "")
                st.rerun()
        
        with col3:
            if st.button("📋 查看详细建议", key=f"view_details_{chapter_idx}"):
                st.json(analysis_results)
        
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON文件格式错误: {str(e)}")
    except UnicodeDecodeError as e:
        st.error(f"❌ 文件编码错误: {str(e)}")
    except Exception as e:
        st.error(f"❌ 处理建议文件失败: {str(e)}")
        print(f"❌ [建议文件处理] 失败: {str(e)}")

def validate_suggestions_file(data):
    """验证建议文件格式"""
    try:
        # 检查必要字段
        required_fields = ['export_info', 'chapter_data', 'analysis_results']
        for field in required_fields:
            if field not in data:
                return False
        
        # 检查analysis_results结构
        analysis = data['analysis_results']
        if not isinstance(analysis.get('conflicts', []), list):
            return False
        
        if not isinstance(analysis.get('suggestions', {}), dict):
            return False
        
        return True
    except:
        return False

def show_suggestions_loader(chapter_idx, current_new_plot, current_custom_instruction=""):
    """显示建议加载器"""
    st.markdown("---")
    st.markdown("### 📁 加载已保存的分析建议")
    
    # 返回按钮
    if st.button("← 返回冲突分析", key=f"return_from_loader_{chapter_idx}"):
        st.session_state[f'show_suggestions_loader_{chapter_idx}'] = False
        st.rerun()
    
    try:
        import os
        import json
        
        # 使用当前故事版本目录
        current_version = st.session_state.get('current_version', 'unknown')
        if current_version and current_version != 'unknown':
            suggestions_dir = f"data/output/{current_version}"
        else:
            suggestions_dir = "data/saved_suggestions"
        
        if not os.path.exists(suggestions_dir):
            st.info("📂 还没有保存过任何建议")
            return
        
        # 获取所有建议文件
        suggestion_files = [f for f in os.listdir(suggestions_dir) if f.endswith('.json')]
        
        if not suggestion_files:
            st.info("📂 还没有保存过任何建议")
            return
        
        # 按时间排序（最新的在前）
        suggestion_files.sort(reverse=True)
        
        st.markdown(f"**找到 {len(suggestion_files)} 个已保存的建议**")
        
        # 文件选择器
        selected_file = st.selectbox(
            "选择要加载的建议文件",
            suggestion_files,
            key=f"suggestions_file_selector_{chapter_idx}",
            format_func=lambda x: x.replace('.json', '').replace('_', ' ')
        )
        
        if selected_file:
            filepath = os.path.join(suggestions_dir, selected_file)
            
            # 读取文件
            with open(filepath, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            # 显示建议预览
            st.markdown("#### 📋 建议预览")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("保存时间", saved_data.get('timestamp', '未知')[:19])
                st.metric("目标章节", f"第{saved_data.get('chapter_idx', 0)+1}章")
                st.metric("故事版本", saved_data.get('story_version', '未知'))
            
            with col2:
                st.metric("冲突数量", saved_data.get('conflicts_count', 0))
                suggestions_summary = saved_data.get('suggestions_summary', {})
                st.metric("大纲更新", suggestions_summary.get('outline_updates', 0))
                st.metric("其他章节", suggestions_summary.get('other_chapters', 0))
            
            # 显示冲突和建议详情
            update_suggestions = saved_data.get('update_suggestions', {})
            
            if update_suggestions.get('conflicts'):
                st.markdown("**⚠️ 检测到的冲突:**")
                for conflict in update_suggestions['conflicts'][:3]:  # 显示前3个
                    st.warning(f"• {conflict}")
                if len(update_suggestions['conflicts']) > 3:
                    st.info(f"... 还有 {len(update_suggestions['conflicts']) - 3} 个冲突")
            
            if update_suggestions.get('suggestions', {}).get('other_chapters'):
                st.markdown("**📖 其他章节更新建议:**")
                for chapter_update in update_suggestions['suggestions']['other_chapters'][:3]:
                    chapter_num = chapter_update.get('chapter', '未知')
                    suggestion = chapter_update.get('suggestion', '')
                    st.info(f"• 第{chapter_num}章: {suggestion[:100]}{'...' if len(suggestion) > 100 else ''}")
            
            # 执行选项
            st.markdown("---")
            st.markdown("#### 🚀 执行选项")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🚀 使用原始内容执行", type="primary", key=f"execute_original_{chapter_idx}"):
                    # 使用保存的原始内容执行
                    saved_plot = saved_data.get('new_plot', current_new_plot)
                    saved_instruction = saved_data.get('custom_instruction', current_custom_instruction)
                    
                    st.session_state[f'show_suggestions_loader_{chapter_idx}'] = False
                    
                    # 执行级联更新
                    execute_cascade_updates(chapter_idx, saved_plot, update_suggestions, saved_instruction)
                    st.rerun()
            
            with col2:
                if st.button("🔄 使用当前内容执行", key=f"execute_current_{chapter_idx}"):
                    # 使用当前的内容但保存的建议执行
                    st.session_state[f'show_suggestions_loader_{chapter_idx}'] = False
                    
                    # 执行级联更新
                    execute_cascade_updates(chapter_idx, current_new_plot, update_suggestions, current_custom_instruction)
                    st.rerun()
            
            with col3:
                if st.button("🗑️ 删除此建议", key=f"delete_suggestion_{chapter_idx}"):
                    try:
                        os.remove(filepath)
                        st.success(f"✅ 已删除建议文件: {selected_file}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 删除失败: {str(e)}")
        
    except Exception as e:
        st.error(f"❌ 加载建议失败: {str(e)}")
        print(f"❌ [建议加载] 加载失败: {str(e)}")

def show_suggestions_history_for_chapter(chapter_idx, current_new_plot, current_custom_instruction=""):
    """显示特定章节的建议历史"""
    st.markdown("---")
    st.markdown(f"## 📋 第{chapter_idx+1}章建议历史")
    
    # 返回按钮
    if st.button("← 返回编辑", key=f"back_from_history_{chapter_idx}"):
        st.session_state[f'show_suggestions_history_{chapter_idx}'] = False
        st.rerun()
    
    try:
        import os
        import json
        from datetime import datetime
        
        # 使用当前故事版本目录
        current_version = st.session_state.get('current_version', 'unknown')
        if current_version and current_version != 'unknown':
            suggestions_dir = f"data/output/{current_version}"
        else:
            suggestions_dir = "data/saved_suggestions"
        
        if not os.path.exists(suggestions_dir):
            st.info("📂 还没有保存过任何建议")
            return
        
        # 获取与当前章节相关的建议文件
        suggestion_files = []
        for filename in os.listdir(suggestions_dir):
            if filename.endswith('.json'):
                try:
                    filepath = os.path.join(suggestions_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 检查是否是当前章节的建议
                    if data.get('chapter_idx') == chapter_idx:
                        suggestion_files.append((filename, data))
                except Exception as e:
                    continue
        
        if not suggestion_files:
            st.info(f"📂 第{chapter_idx+1}章还没有保存过建议")
            return
        
        # 按时间排序（最新的在前）
        suggestion_files.sort(key=lambda x: x[1].get('timestamp', ''), reverse=True)
        
        st.markdown(f"**找到 {len(suggestion_files)} 个第{chapter_idx+1}章的建议记录**")
        
        # 显示建议历史
        for i, (filename, saved_data) in enumerate(suggestion_files):
            timestamp = saved_data.get('timestamp', '未知时间')
            try:
                # 格式化时间戳
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = timestamp
            
            with st.expander(f"📅 {formatted_time} - 建议记录 #{i+1}", expanded=(i==0)):
                
                # 显示保存时的章节信息
                if 'new_plot' in saved_data:
                    st.markdown("**📝 当时的章节内容修改:**")
                    with st.container():
                        plot_preview = saved_data['new_plot'][:300] + "..." if len(saved_data['new_plot']) > 300 else saved_data['new_plot']
                        st.text_area(
                            "章节内容预览", 
                            value=plot_preview, 
                            height=100, 
                            disabled=True,
                            key=f"plot_preview_{chapter_idx}_{i}"
                        )
                
                # 显示自定义指令
                if saved_data.get('custom_instruction'):
                    st.markdown("**🎯 自定义指令:**")
                    st.info(saved_data['custom_instruction'])
                
                # 显示分析结果
                update_suggestions = saved_data.get('update_suggestions', {})
                
                if update_suggestions.get('conflicts'):
                    st.markdown("**⚠️ 检测到的冲突:**")
                    for conflict in update_suggestions['conflicts'][:3]:  # 只显示前3个
                        st.warning(f"• {conflict}")
                    if len(update_suggestions['conflicts']) > 3:
                        st.info(f"... 还有 {len(update_suggestions['conflicts']) - 3} 个冲突")
                
                if update_suggestions.get('suggestions', {}).get('other_chapters'):
                    st.markdown("**📖 其他章节更新建议:**")
                    for chapter_update in update_suggestions['suggestions']['other_chapters'][:3]:
                        chapter_num = chapter_update.get('chapter', '未知')
                        suggestion = chapter_update.get('suggestion', '')
                        st.info(f"• 第{chapter_num}章: {suggestion[:100]}{'...' if len(suggestion) > 100 else ''}")
                
                # 操作按钮
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🚀 重新执行", key=f"rerun_suggestion_{chapter_idx}_{i}"):
                        # 使用历史建议重新执行
                        st.session_state[f'show_suggestions_history_{chapter_idx}'] = False
                        execute_cascade_updates(chapter_idx, current_new_plot, update_suggestions, saved_data.get('custom_instruction', ''))
                        st.rerun()
                
                with col2:
                    if st.button("📥 导出此建议", key=f"export_history_{chapter_idx}_{i}"):
                        # 导出这个历史建议
                        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename_export = f"历史建议_第{chapter_idx+1}章_{timestamp_str}.json"
                        
                        json_string = json.dumps(saved_data, ensure_ascii=False, indent=2)
                        
                        st.download_button(
                            label="📥 下载历史建议",
                            data=json_string,
                            file_name=filename_export,
                            mime="application/json",
                            key=f"download_history_{chapter_idx}_{i}"
                        )
                
                with col3:
                    if st.button("🗑️ 删除记录", key=f"delete_history_{chapter_idx}_{i}"):
                        try:
                            filepath = os.path.join(suggestions_dir, filename)
                            os.remove(filepath)
                            st.success("✅ 记录已删除")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 删除失败: {str(e)}")
        
    except Exception as e:
        st.error(f"❌ 加载建议历史失败: {str(e)}")
        print(f"❌ [建议历史] 加载失败: {str(e)}")

def show_suggestions_manager():
    """显示建议管理器"""
    st.markdown("---")
    st.markdown("## 💡 智能建议管理器")
    
    # 返回按钮
    if st.button("← 返回"):
        st.session_state.show_suggestions_manager = False
        st.rerun()
    
    try:
        import os
        import json
        from datetime import datetime
        
        # 使用当前故事版本目录
        current_version = st.session_state.get('current_version', 'unknown')
        if current_version and current_version != 'unknown':
            suggestions_dir = f"data/output/{current_version}"
        else:
            suggestions_dir = "data/saved_suggestions"
        
        if not os.path.exists(suggestions_dir):
            st.info("📂 还没有保存过任何建议")
            return
        
        # 获取所有建议文件
        suggestion_files = [f for f in os.listdir(suggestions_dir) if f.endswith('.json')]
        
        if not suggestion_files:
            st.info("📂 还没有保存过任何建议")
            return
        
        # 按时间排序（最新的在前）
        suggestion_files.sort(reverse=True)
        
        st.markdown(f"**找到 {len(suggestion_files)} 个已保存的建议**")
        
        # 批量操作
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ 清空所有建议", type="secondary"):
                try:
                    for file in suggestion_files:
                        os.remove(os.path.join(suggestions_dir, file))
                    st.success("✅ 已清空所有建议")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 清空失败: {str(e)}")
        
        # 显示建议列表
        for i, filename in enumerate(suggestion_files):
            filepath = os.path.join(suggestions_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                
                # 创建建议卡片
                with st.expander(f"📄 {filename.replace('.json', '')}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("保存时间", saved_data.get('timestamp', '未知')[:19])
                        st.metric("目标章节", f"第{saved_data.get('chapter_idx', 0)+1}章")
                    
                    with col2:
                        st.metric("故事版本", saved_data.get('story_version', '未知'))
                        st.metric("冲突数量", saved_data.get('conflicts_count', 0))
                    
                    with col3:
                        suggestions_summary = saved_data.get('suggestions_summary', {})
                        st.metric("其他章节", suggestions_summary.get('other_chapters', 0))
                        st.metric("角色更新", suggestions_summary.get('character_updates', 0))
                    
                    # 显示部分建议内容
                    update_suggestions = saved_data.get('update_suggestions', {})
                    if update_suggestions.get('conflicts'):
                        st.markdown("**⚠️ 主要冲突:**")
                        for conflict in update_suggestions['conflicts'][:2]:
                            st.warning(f"• {conflict}")
                    
                    # 操作按钮
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🚀 立即执行", key=f"execute_suggestion_{i}"):
                            # 加载并执行建议
                            chapter_idx = saved_data.get('chapter_idx', 0)
                            new_plot = saved_data.get('new_plot', '')
                            custom_instruction = saved_data.get('custom_instruction', '')
                            
                            # 检查当前是否有对应的故事数据
                            if len(st.session_state.story_data) > chapter_idx:
                                st.session_state.show_suggestions_manager = False
                                execute_cascade_updates(chapter_idx, new_plot, update_suggestions, custom_instruction)
                                st.rerun()
                            else:
                                st.error("❌ 当前故事数据与建议不匹配")
                    
                    with col2:
                        if st.button("📋 复制到剪贴板", key=f"copy_suggestion_{i}"):
                            # 这里可以显示JSON内容供复制
                            st.json(saved_data)
                    
                    with col3:
                        if st.button("🗑️ 删除", key=f"delete_suggestion_{i}"):
                            try:
                                os.remove(filepath)
                                st.success(f"✅ 已删除: {filename}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 删除失败: {str(e)}")
            
            except Exception as e:
                st.error(f"❌ 读取文件失败 {filename}: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ 管理器加载失败: {str(e)}")
        print(f"❌ [建议管理器] 加载失败: {str(e)}")

def generate_story_summary_text():
    """生成故事摘要文本"""
    lines = [f"{st.session_state.current_version} 故事摘要\n"]
    lines.append("=" * 50 + "\n")
    
    for i, chapter in enumerate(st.session_state.story_data):
        title = chapter.get('title', f'第{i+1}章')
        plot = chapter.get('plot', '')
        word_count = len(plot)
        
        lines.append(f"{i+1}. {title} ({word_count}字)")
        lines.append(f"场景: {chapter.get('scene', '未指定')}")
        lines.append(f"人物: {', '.join(chapter.get('characters', [])) if chapter.get('characters') else '未指定'}")
        lines.append(f"摘要: {plot[:200]}{'...' if len(plot) > 200 else ''}")
        lines.append("-" * 30)
    
    return "\n".join(lines)

def show_chapter_order_comparison():
    """显示章节顺序对比"""
    if not st.session_state.outline_data:
        return
    
    # 检查是否有重排信息
    has_reorder_info = any('original_position' in ch for ch in st.session_state.outline_data)
    
    if has_reorder_info:
        # 显示重排对比
        st.markdown("### 📋 章节顺序对比")
        
        # 构建原始顺序映射
        original_chapters = {}
        for ch in st.session_state.outline_data:
            if 'original_position' in ch:
                original_chapters[ch['original_position']] = ch
        
        # 显示原始顺序
        st.markdown("**🔸 原始顺序:**")
        original_order_display = []
        for pos in sorted(original_chapters.keys()):
            ch = original_chapters[pos]
            original_order_display.append(f"{pos}. {ch['title']}")
        st.markdown(" → ".join(original_order_display))
        
        # 显示当前顺序
        st.markdown("**🔹 当前顺序:**")
        current_order_display = []
        for i, chapter in enumerate(st.session_state.outline_data):
            orig_pos = chapter.get('original_position', '?')
            current_order_display.append(f"{i+1}. {chapter['title']} (原第{orig_pos}章)")
        st.markdown(" → ".join(current_order_display))
        
        # 显示详细对比表格
        st.markdown("**📊 详细对比:**")
        
        # 创建对比表格数据
        comparison_data = []
        for i, chapter in enumerate(st.session_state.outline_data):
            orig_pos = chapter.get('original_position', '未知')
            narrative_role = chapter.get('narrative_role', '线性叙述')
            
            # 判断位置变化
            if isinstance(orig_pos, int):
                position_change = i + 1 - orig_pos
                if position_change > 0:
                    change_indicator = f"↓ +{position_change}"
                elif position_change < 0:
                    change_indicator = f"↑ {position_change}"
                else:
                    change_indicator = "→ 不变"
            else:
                change_indicator = "?"
            
            comparison_data.append({
                "当前位置": f"第{i+1}章",
                "章节标题": chapter['title'],
                "原始位置": f"第{orig_pos}章" if isinstance(orig_pos, int) else str(orig_pos),
                "位置变化": change_indicator,
                "叙述角色": narrative_role
            })
        
        # 显示表格
        import pandas as pd
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 显示重排统计
        moved_chapters = sum(1 for ch in st.session_state.outline_data 
                           if isinstance(ch.get('original_position'), int) and 
                           st.session_state.outline_data.index(ch) + 1 != ch['original_position'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总章节数", len(st.session_state.outline_data))
        with col2:
            st.metric("重排章节数", moved_chapters)
        with col3:
            st.metric("保持原位", len(st.session_state.outline_data) - moved_chapters)
    
    else:
        # 显示线性顺序
        st.markdown("### 📋 当前章节顺序 (线性)")
        
        current_order = []
        for i, chapter in enumerate(st.session_state.outline_data):
            current_order.append(f"{i+1}. {chapter['title']}")
        
        st.markdown(" → ".join(current_order))
        
        # 显示简单统计
        st.info(f"📊 当前共有 {len(st.session_state.outline_data)} 个章节，按线性顺序排列")

def show_export_mode():
    """导出模式"""
    st.subheader("💾 保存和导出")
    
    # 保存到文件
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**保存大纲:**")
        
        # 构建文件名
        filename = f"{st.session_state.current_version}_outline.json"
        
        # 创建下载按钮
        outline_json = json.dumps(st.session_state.outline_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 下载JSON文件",
            data=outline_json,
            file_name=filename,
            mime="application/json"
        )
        
        # 保存到输出目录
        if st.button("💾 保存到项目目录", use_container_width=True):
            save_to_project_directory()
    
    with col2:
        st.markdown("**导出格式:**")
        
        # 导出为Markdown
        markdown_content = generate_markdown_outline()
        st.download_button(
            label="📝 下载Markdown",
            data=markdown_content,
            file_name=f"{st.session_state.current_version}_outline.md",
            mime="text/markdown"
        )
        
        # 导出为文本
        text_content = generate_text_outline()
        st.download_button(
            label="📄 下载纯文本",
            data=text_content,
            file_name=f"{st.session_state.current_version}_outline.txt",
            mime="text/plain"
        )
    
    st.markdown("---")
    
    # 最终确认
    st.markdown("### ✅ 最终确认")
    
    # 显示最终结构
    st.markdown("**最终章节结构:**")
    for i, chapter in enumerate(st.session_state.outline_data):
        st.markdown(f"{i+1}. **{chapter['chapter_id']}**: {chapter['title']}")
        if chapter.get('summary'):
            st.markdown(f"   *{chapter['summary']}*")
    
    # 统计信息
    total_chapters = len(st.session_state.outline_data)
    st.success(f"✅ 大纲编辑完成！共 {total_chapters} 章")
    
    if st.button("🚀 继续下一步", type="primary", use_container_width=True):
        st.info("🎉 大纲已准备就绪！可以继续生成角色设定和故事内容。")

# 辅助函数
def regenerate_chapter(chapter_idx, chapter):
    """重新生成单个章节"""
    try:
        # 获取当前的故事参数（从侧边栏或会话状态）
        current_topic = st.session_state.get('current_topic', '小红帽')
        current_style = st.session_state.get('current_style', '科幻改写')
        
        # 构建针对特定章节的指令
        chapter_id = chapter.get('chapter_id', f'Chapter {chapter_idx + 1}')
        current_title = chapter.get('title', f'第{chapter_idx + 1}章')
        
        custom_instruction = f"""
请重新生成第{chapter_idx + 1}章的内容。
原章节ID: {chapter_id}
原标题: {current_title}
要求: 保持与整体故事风格一致，但重新创作该章节的标题和摘要。
"""
        
        start_time = time.time()
        st.info(f"🔄 正在重新生成第 {chapter_idx + 1} 章...")
        
        # 重新生成整个大纲，然后提取对应章节
        new_outline = generate_outline(
            topic=current_topic, 
            style=current_style, 
            custom_instruction=custom_instruction
        )
        end_time = time.time()
        
        log_backend_operation(
            f"重新生成第{chapter_idx + 1}章", 
            {
                "chapter_idx": chapter_idx, 
                "chapter_id": chapter_id,
                "topic": current_topic,
                "style": current_style,
                "custom_instruction": custom_instruction[:100] + "..."
            },
            start_time, end_time, new_outline
        )
        
        # 检查生成结果
        if not new_outline or not isinstance(new_outline, list):
            st.error("❌ 后端返回的数据格式不正确")
            st.error(f"实际返回: {type(new_outline)} - {str(new_outline)[:200]}...")
            return
            
        if len(new_outline) <= chapter_idx:
            st.warning(f"⚠️ 生成的章节数({len(new_outline)})不够，无法替换第 {chapter_idx + 1} 章")
            return
        
        # 获取新生成的章节
        new_chapter = new_outline[chapter_idx]
        
        # 验证新章节的格式
        if not isinstance(new_chapter, dict):
            st.error("❌ 新生成的章节格式不正确")
            st.error(f"章节类型: {type(new_chapter)}, 内容: {str(new_chapter)}")
            return
        
        # 处理不同的字段名格式（兼容LLM可能返回的不同格式）
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
        
        # 提取章节信息（兼容多种字段名格式）
        new_title = extract_field(new_chapter, 'title', ['章节标题', '标题', 'chapter_title'], f'重新生成的第{chapter_idx + 1}章')
        new_summary = extract_field(new_chapter, 'summary', ['章节内容', '内容', '摘要', 'chapter_content', 'content'], f'这是重新生成的第{chapter_idx + 1}章内容')
        new_chapter_id = extract_field(new_chapter, 'chapter_id', ['章节编号', '编号'], f'Chapter {chapter_idx + 1}')
        
        # 保留一些原有信息，更新核心内容
        updated_chapter = {
            "chapter_id": chapter.get('chapter_id', new_chapter_id),
            "title": new_title,
            "summary": new_summary
        }
        
        # 显示提取的信息用于调试
        st.info(f"🔍 提取的章节信息:")
        st.info(f"  - 原始数据: {str(new_chapter)[:200]}...")
        st.info(f"  - 提取标题: {new_title}")
        st.info(f"  - 提取摘要: {new_summary[:100]}...")
        
        # 保留原有的叙述分析字段
        narrative_fields = ["new_order", "narrative_role", "narrative_instruction", "transition_hint", "original_position"]
        for field in narrative_fields:
            if field in chapter:
                updated_chapter[field] = chapter[field]
        
        # 保存重新生成前的状态到历史记录
        old_data = st.session_state.outline_data.copy()
        save_to_history(f"重新生成第{chapter_idx + 1}章", old_data)
        
        # 更新章节数据
        st.session_state.outline_data[chapter_idx] = updated_chapter
        
        st.success(f"✅ 第 {chapter_idx + 1} 章重新生成完成")
        st.info(f"📝 新标题: {updated_chapter['title']}")
        st.info(f"📄 新摘要: {updated_chapter['summary'][:100]}...")
        
        st.rerun()
        
    except Exception as e:
        log_backend_operation(
            f"重新生成第{chapter_idx + 1}章失败", 
            {"chapter_idx": chapter_idx, "error": str(e)},
            time.time(), time.time(), None, e
        )
        st.error(f"❌ 重新生成失败: {str(e)}")
        app_logger.error(f"Chapter regeneration failed for chapter {chapter_idx + 1}: {str(e)}")

# delete_chapter 函数已移除，删除逻辑直接在编辑界面中处理

def save_chapter_edit(chapter_idx, new_title, new_chapter_id, new_summary):
    """保存章节编辑"""
    # 保存编辑前的状态到历史记录
    old_data = st.session_state.outline_data.copy()
    save_to_history(f"编辑第{chapter_idx + 1}章", old_data)
    
    # 执行编辑
    st.session_state.outline_data[chapter_idx]['title'] = new_title
    st.session_state.outline_data[chapter_idx]['chapter_id'] = new_chapter_id
    st.session_state.outline_data[chapter_idx]['summary'] = new_summary
    st.success(f"✅ 第 {chapter_idx + 1} 章修改已保存")

def add_new_chapter(title, summary, insert_idx=None, enable_conflict_check=True):
    """添加新章节到指定位置"""
    try:
        # 如果没有指定位置，默认添加到末尾
        if insert_idx is None:
            insert_idx = len(st.session_state.outline_data)
        
        # 保存添加前的状态到历史记录
        old_data = st.session_state.outline_data.copy()
        save_to_history(f"在第{insert_idx + 1}位置添加新章节", old_data)
        
        # 冲突检测
        if enable_conflict_check:
            conflicts = detect_content_conflicts(title, summary, st.session_state.outline_data)
            if conflicts:
                st.warning("⚠️ 检测到潜在的内容冲突:")
                for conflict in conflicts:
                    st.warning(f"  • {conflict}")
                
                # 提供选择
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚨 仍然添加", key="confirm_add_with_conflicts"):
                        pass  # 继续执行添加逻辑
                    else:
                        with col2:
                            if st.button("❌ 取消添加", key="cancel_add"):
                                st.info("已取消添加章节")
                                return
                        
                        # 如果用户没有选择继续，则返回
                        if not st.session_state.get('confirm_add_with_conflicts', False):
                            return
        
        # 生成新的章节ID
        if insert_idx == len(st.session_state.outline_data):
            # 添加到末尾
            new_chapter_id = f"Chapter {len(st.session_state.outline_data) + 1}"
        else:
            # 插入到中间，需要重新编号
            new_chapter_id = f"Chapter {insert_idx + 1}"
        
        # 创建新章节
        new_chapter = {
            "chapter_id": new_chapter_id,
            "title": title,
            "summary": summary
        }
        
        # 如果有原始位置信息，设置新章节的原始位置
        if any('original_position' in ch for ch in st.session_state.outline_data):
            new_chapter['original_position'] = insert_idx + 1
        
        # 插入新章节
        st.session_state.outline_data.insert(insert_idx, new_chapter)
        
        # 更新后续章节的ID
        update_chapter_ids_after_insert(insert_idx)
        
        # 显示成功信息
        position_text = "末尾" if insert_idx == len(st.session_state.outline_data) - 1 else f"第{insert_idx + 1}位置"
        st.success(f"✅ 新章节已添加到{position_text}: {title}")
        
        # 显示章节列表预览
        st.info("📋 当前章节顺序:")
        for i, ch in enumerate(st.session_state.outline_data):
            marker = "🆕" if i == insert_idx else "📄"
            st.text(f"  {marker} {i+1}. {ch['title']}")
        
    except Exception as e:
        st.error(f"❌ 添加章节失败: {str(e)}")
        app_logger.error(f"Add chapter failed: {str(e)}")

def update_chapter_ids_after_insert(insert_idx):
    """插入章节后更新后续章节的ID"""
    for i in range(insert_idx + 1, len(st.session_state.outline_data)):
        # 更新chapter_id
        st.session_state.outline_data[i]['chapter_id'] = f"Chapter {i + 1}"

def detect_content_conflicts(new_title, new_summary, existing_chapters):
    """检测新章节与现有章节的内容冲突"""
    conflicts = []
    
    # 提取关键信息进行冲突检测
    new_content = f"{new_title} {new_summary}".lower()
    
    # 定义一些常见的冲突关键词对
    conflict_patterns = [
        # 角色状态冲突
        (["死", "死亡", "牺牲", "去世"], ["活", "生存", "救", "复活"]),
        (["好人", "善良", "正义"], ["坏人", "邪恶", "反派", "敌人"]),
        (["朋友", "盟友", "帮助"], ["敌人", "背叛", "对抗"]),
        
        # 地点冲突
        (["地球", "家乡", "故乡"], ["外星", "异世界", "太空"]),
        (["城市", "都市"], ["乡村", "农村", "森林"]),
        
        # 时间冲突
        (["过去", "回忆", "历史"], ["未来", "预言", "明天"]),
        (["白天", "早晨", "中午"], ["夜晚", "深夜", "黄昏"]),
        
        # 情节状态冲突
        (["成功", "胜利", "完成"], ["失败", "失败", "放弃"]),
        (["开始", "启程", "出发"], ["结束", "完成", "到达"]),
    ]
    
    # 检查与现有章节的冲突
    for i, chapter in enumerate(existing_chapters):
        existing_content = f"{chapter['title']} {chapter.get('summary', '')}".lower()
        
        # 检查标题相似性
        if similar_titles(new_title, chapter['title']):
            conflicts.append(f"与第{i+1}章标题过于相似: '{chapter['title']}'")
        
        # 检查内容冲突模式
        for positive_words, negative_words in conflict_patterns:
            has_positive_new = any(word in new_content for word in positive_words)
            has_negative_new = any(word in new_content for word in negative_words)
            has_positive_existing = any(word in existing_content for word in positive_words)
            has_negative_existing = any(word in existing_content for word in negative_words)
            
            # 检测矛盾
            if (has_positive_new and has_negative_existing) or (has_negative_new and has_positive_existing):
                conflicts.append(f"与第{i+1}章 '{chapter['title']}' 存在逻辑矛盾")
                break
    
    return conflicts

def similar_titles(title1, title2):
    """检查两个标题是否过于相似"""
    # 简单的相似性检测
    title1_words = set(title1.replace(" ", "").lower())
    title2_words = set(title2.replace(" ", "").lower())
    
    if len(title1_words) == 0 or len(title2_words) == 0:
        return False
    
    # 计算相似度
    intersection = len(title1_words & title2_words)
    union = len(title1_words | title2_words)
    similarity = intersection / union if union > 0 else 0
    
    return similarity > 0.6  # 60%以上相似度认为是相似标题

def perform_automatic_reorder():
    """执行自动重排"""
    try:
        # 保存重排前的状态到历史记录
        old_data = st.session_state.outline_data.copy()
        save_to_history("自动重排", old_data)
        
        # Step 1: 章节重排
        start_time = time.time()
        reordered = reorder_chapters(st.session_state.outline_data, mode="nonlinear")
        reorder_end = time.time()
        
        log_backend_operation(
            "自动重排章节", 
            {"mode": "nonlinear", "chapters": len(st.session_state.outline_data)},
            start_time, reorder_end, reordered
        )
        
        # Step 2: 叙述结构分析
        analysis_start = time.time()
        reordered = analyze_narrative_structure(reordered, st.session_state.outline_data, "小红帽", "科幻改写")
        analysis_end = time.time()
        
        log_backend_operation(
            "自动重排-叙述结构分析", 
            {"topic": "小红帽", "style": "科幻改写"},
            analysis_start, analysis_end, reordered
        )
        
        # 更新大纲数据
        st.session_state.outline_data = reordered
        st.success("✅ 非线性重排完成！")
        st.rerun()
    except Exception as e:
        log_backend_operation(
            "自动重排失败", 
            {"chapters": len(st.session_state.outline_data) if st.session_state.outline_data else 0},
            time.time(), time.time(), None, e
        )
        st.error(f"❌ 自动重排失败: {str(e)}")

def perform_narrative_analysis():
    """执行叙述结构分析"""
    try:
        start_time = time.time()
        analyzed = analyze_narrative_structure(
            st.session_state.outline_data, 
            st.session_state.outline_data, 
            "小红帽", 
            "科幻改写"
        )
        end_time = time.time()
        
        log_backend_operation(
            "叙述结构分析", 
            {"topic": "小红帽", "style": "科幻改写", "chapters": len(st.session_state.outline_data)},
            start_time, end_time, analyzed
        )
        
        st.session_state.outline_data = analyzed
        st.success("✅ 叙述结构分析完成！")
        st.rerun()
    except Exception as e:
        log_backend_operation(
            "叙述结构分析失败", 
            {"chapters": len(st.session_state.outline_data) if st.session_state.outline_data else 0},
            time.time(), time.time(), None, e
        )
        st.error(f"❌ 叙述结构分析失败: {str(e)}")

def apply_manual_reorder(order_input):
    """应用手动重排"""
    try:
        new_order = [int(x.strip()) - 1 for x in order_input.split(',')]
        if len(new_order) != len(st.session_state.outline_data):
            st.error("❌ 顺序数量与章节数量不匹配")
            return
        
        # 检查输入是否有效
        if not all(0 <= idx < len(st.session_state.outline_data) for idx in new_order):
            st.error("❌ 顺序索引超出范围")
            return
        
        if len(set(new_order)) != len(new_order):
            st.error("❌ 顺序中有重复的章节")
            return
        
        # 保存重排前的状态到历史记录
        old_data = st.session_state.outline_data.copy()
        save_to_history("手动重排", old_data)
        
        # 重新排列章节并添加原始位置信息
        reordered_outline = []
        for new_pos, old_idx in enumerate(new_order):
            chapter = st.session_state.outline_data[old_idx].copy()
            
            # 如果章节还没有original_position，则设置为当前位置+1
            if 'original_position' not in chapter:
                chapter['original_position'] = old_idx + 1
            
            # 设置新的顺序信息
            chapter['new_order'] = new_pos + 1
            
            reordered_outline.append(chapter)
        
        st.session_state.outline_data = reordered_outline
        
        st.success("✅ 手动重排完成！")
        
        # 显示重排结果预览
        st.info("📋 重排结果预览:")
        for i, ch in enumerate(reordered_outline):
            orig_pos = ch.get('original_position', '?')
            st.text(f"  {i+1}. {ch['title']} (原第{orig_pos}章)")
        
        st.rerun()
        
    except ValueError:
        st.error("❌ 请输入有效的数字序列，用逗号分隔")
    except Exception as e:
        st.error(f"❌ 手动重排失败: {str(e)}")

def save_to_project_directory():
    """保存到项目目录"""
    try:
        start_time = time.time()
        # 使用真实后端的保存功能
        save_json(st.session_state.outline_data, st.session_state.current_version, "outline.json")
        end_time = time.time()
        
        log_backend_operation(
            "保存到项目目录", 
            {"version": st.session_state.current_version, "filename": "outline.json"},
            start_time, end_time, True
        )
        
        st.success(f"✅ 大纲已保存到项目目录: {st.session_state.current_version}/outline.json")
    except Exception as e:
        log_backend_operation(
            "保存到项目目录失败", 
            {"version": st.session_state.current_version},
            time.time(), time.time(), None, e
        )
        st.error(f"❌ 保存失败: {str(e)}")

def generate_markdown_outline():
    """生成Markdown格式的大纲"""
    markdown_lines = [f"# {st.session_state.current_version} 故事大纲\n"]
    
    for i, chapter in enumerate(st.session_state.outline_data):
        markdown_lines.append(f"## {chapter['chapter_id']}: {chapter['title']}")
        if chapter.get('summary'):
            markdown_lines.append(f"\n{chapter['summary']}\n")
        
        # 添加叙述分析信息
        if 'narrative_role' in chapter:
            markdown_lines.append(f"**叙述角色:** {chapter['narrative_role']}")
        if 'narrative_instruction' in chapter:
            markdown_lines.append(f"**叙述指导:** {chapter['narrative_instruction']}")
        if 'transition_hint' in chapter:
            markdown_lines.append(f"**过渡提示:** {chapter['transition_hint']}")
        
        markdown_lines.append("---\n")
    
    return "\n".join(markdown_lines)

def generate_text_outline():
    """生成纯文本格式的大纲"""
    text_lines = [f"{st.session_state.current_version} 故事大纲\n"]
    text_lines.append("=" * 50 + "\n")
    
    for i, chapter in enumerate(st.session_state.outline_data):
        text_lines.append(f"{chapter['chapter_id']}: {chapter['title']}")
        if chapter.get('summary'):
            text_lines.append(f"摘要: {chapter['summary']}")
        
        # 添加叙述分析信息
        if 'narrative_role' in chapter:
            text_lines.append(f"叙述角色: {chapter['narrative_role']}")
        if 'narrative_instruction' in chapter:
            text_lines.append(f"叙述指导: {chapter['narrative_instruction']}")
        if 'transition_hint' in chapter:
            text_lines.append(f"过渡提示: {chapter['transition_hint']}")
        
        text_lines.append("-" * 30)
    
    return "\n".join(text_lines)

# ==================== 对话生成功能 ====================

def save_dialogue_to_history(action_name, old_dialogue_data=None):
    """保存对话数据到历史记录"""
    try:
        if old_dialogue_data is None:
            old_dialogue_data = copy.deepcopy(st.session_state.dialogue_data) if st.session_state.dialogue_data else []
        
        # 创建历史记录条目
        history_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action_name,
            "dialogue_data": old_dialogue_data,
            "data_length": len(old_dialogue_data) if old_dialogue_data else 0
        }
        
        # 如果当前不在历史记录的末尾，删除后续记录
        if st.session_state.dialogue_history_index < len(st.session_state.dialogue_history) - 1:
            st.session_state.dialogue_history = st.session_state.dialogue_history[:st.session_state.dialogue_history_index + 1]
        
        # 添加新记录
        st.session_state.dialogue_history.append(history_entry)
        st.session_state.dialogue_history_index = len(st.session_state.dialogue_history) - 1
        
        # 限制历史记录数量
        max_history = 20
        if len(st.session_state.dialogue_history) > max_history:
            st.session_state.dialogue_history = st.session_state.dialogue_history[-max_history:]
            st.session_state.dialogue_history_index = len(st.session_state.dialogue_history) - 1
        
        print(f"💾 [对话历史] 保存操作: {action_name}, 当前索引: {st.session_state.dialogue_history_index}")
        
    except Exception as e:
        print(f"❌ [对话历史] 保存失败: {str(e)}")

def undo_dialogue_action():
    """撤销对话操作"""
    if st.session_state.dialogue_history_index > 0:
        st.session_state.dialogue_history_index -= 1
        history_entry = st.session_state.dialogue_history[st.session_state.dialogue_history_index]
        st.session_state.dialogue_data = copy.deepcopy(history_entry["dialogue_data"])
        st.success(f"↩️ 已撤销操作: {history_entry['action']}")
        st.rerun()
    else:
        st.warning("⚠️ 没有可撤销的操作")

def redo_dialogue_action():
    """重做对话操作"""
    if st.session_state.dialogue_history_index < len(st.session_state.dialogue_history) - 1:
        st.session_state.dialogue_history_index += 1
        history_entry = st.session_state.dialogue_history[st.session_state.dialogue_history_index]
        st.session_state.dialogue_data = copy.deepcopy(history_entry["dialogue_data"])
        st.success(f"↪️ 已重做操作: {history_entry['action']}")
        st.rerun()
    else:
        st.warning("⚠️ 没有可重做的操作")

def show_dialogue_generation_interface():
    """显示对话生成界面 - 作为主流程步骤"""
    st.header("💬 步骤4: 对话生成")
    
    # 检查前置条件
    if not st.session_state.outline_data:
        st.error("❌ 请先完成步骤1: 生成故事大纲")
        return
    
    if not st.session_state.characters_data:
        st.error("❌ 请先完成步骤2: 生成角色")
        return
    
    if not st.session_state.get('story_data'):
        st.error("❌ 请先完成步骤3: 生成故事内容")
        return
    
    # 检查对话生成功能是否可用
    if not dialogue_generation_available:
        st.error("❌ 对话生成功能不可用，请检查后端模块导入")
        return
    
    # 显示基于故事的对话生成界面
    show_dialogue_generation_mode()

def show_dialogue_generation_mode():
    """对话生成模式选择"""
    st.markdown("### 💬 对话生成选项")
    
    # 创建选项卡
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 生成对话", "📋 对话预览", "✏️ 编辑对话", "📁 文件管理"])
    
    with tab1:
        show_dialogue_generation_options()
    
    with tab2:
        show_dialogue_display()
    
    with tab3:
        show_dialogue_edit_mode()
    
    with tab4:
        show_dialogue_file_management()

def show_dialogue_generation_options():
    """对话生成选项"""
    st.markdown("#### 🎯 生成新对话")
    
    # 生成参数配置
    col1, col2 = st.columns(2)
    
    with col1:
        use_cache = st.checkbox("使用缓存", value=True, help="如果已有对话数据，是否使用缓存", key="dialogue_use_cache_checkbox")
        auto_save = st.checkbox("自动保存", value=True, help="生成完成后自动保存到项目目录", key="dialogue_auto_save_checkbox")
    
    with col2:
        behavior_model = st.selectbox(
            "行为识别模型", 
            ["gpt-4.1", "gpt-3.5-turbo", "claude-3"], 
            index=0,
            help="用于角色行为分析的模型"
        )
    
    st.markdown("---")
    
    # 生成按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎭 生成章节对话", type="primary", use_container_width=True):
            generate_dialogues_from_story(use_cache=use_cache, auto_save=auto_save, behavior_model=behavior_model)
    
    with col2:
        if st.button("🔄 重新生成全部", use_container_width=True):
            regenerate_all_dialogues(behavior_model=behavior_model)
    
    with col3:
        if st.button("📁 加载已有对话", use_container_width=True):
            st.session_state.show_dialogue_loader_gen = True
            st.rerun()
    
    # 显示对话加载器
    if st.session_state.get('show_dialogue_loader_gen', False):
        load_existing_dialogue("generation_options")

def generate_dialogues_from_story(use_cache=True, auto_save=True, behavior_model="gpt-4.1"):
    """基于故事内容生成对话"""
    try:
        print(f"🎭🎭🎭 [对话生成] ===== 开始生成对话 =====")
        print(f"🎭 [对话生成] 故事章节数: {len(st.session_state.story_data)}")
        print(f"🎭 [对话生成] 角色数量: {len(st.session_state.characters_data)}")
        print(f"🎭 [对话生成] 使用缓存: {use_cache}")
        print(f"🎭 [对话生成] 自动保存: {auto_save}")
        print(f"🎭 [对话生成] 行为模型: {behavior_model}")
        
        # 保存当前状态到历史
        save_dialogue_to_history("生成对话前")
        
        with st.spinner("🎭 正在分析故事并生成对话..."):
            start_time = time.time()
            
            # 调用后端对话生成功能
            chapter_results, sentence_results, behavior_timeline = analyze_dialogue_insertions_v2(
                st.session_state.story_data, 
                st.session_state.characters_data
            )
            
            # 如果需要同步，使用章节级数据
            if len(st.session_state.story_data) == len(chapter_results):
                story_updated, chapter_results_updated, revision_log = sync_plot_and_dialogue_from_behavior(
                    st.session_state.story_data, 
                    chapter_results, 
                    st.session_state.characters_data, 
                    model=behavior_model
                )
            else:
                chapter_results_updated = chapter_results
                revision_log = []
            
            end_time = time.time()
            
            # 保存生成的对话数据
            st.session_state.dialogue_data = {
                "chapter_dialogues": chapter_results_updated,
                "sentence_dialogues": sentence_results,
                "behavior_timeline": behavior_timeline,
                "revision_log": revision_log,
                "generation_params": {
                    "behavior_model": behavior_model,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "story_chapters": len(st.session_state.story_data),
                    "characters_count": len(st.session_state.characters_data)
                }
            }
            
            # 记录操作日志
            log_backend_operation(
                "对话生成", 
                {
                    "story_chapters": len(st.session_state.story_data),
                    "characters": len(st.session_state.characters_data),
                    "behavior_model": behavior_model
                },
                start_time, end_time, 
                {
                    "chapter_dialogues": len(chapter_results_updated),
                    "sentence_dialogues": len(sentence_results),
                    "behavior_timeline": len(behavior_timeline)
                }
            )
            
            print(f"🎭 [对话生成] 章节对话数: {len(chapter_results_updated)}")
            print(f"🎭 [对话生成] 句子对话数: {len(sentence_results)}")
            print(f"🎭 [对话生成] 行为时间线: {len(behavior_timeline)}")
            print(f"🎭🎭🎭 [对话生成] ===== 生成完成 =====")
            
            st.success(f"✅ 对话生成完成！生成了 {len(chapter_results_updated)} 个章节的对话内容")
            
            # 显示生成统计
            with st.expander("📊 生成统计", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("章节对话", len(chapter_results_updated))
                with col2:
                    st.metric("句子对话", len(sentence_results))
                with col3:
                    st.metric("行为事件", len(behavior_timeline))
            
            # 自动保存
            if auto_save:
                save_dialogue_to_project()
            
            # 保存操作到历史
            save_dialogue_to_history("生成对话完成")
            
    except Exception as e:
        error_msg = f"对话生成失败: {str(e)}"
        print(f"❌ [对话生成] {error_msg}")
        st.error(f"❌ {error_msg}")
        
        # 记录错误日志
        log_backend_operation(
            "对话生成失败", 
            {"error": str(e)},
            time.time(), time.time(), None, e
        )

def show_dialogue_display():
    """显示对话内容"""
    if not st.session_state.get('dialogue_data'):
        st.info("📝 暂无对话数据，请先生成对话")
        return
    
    st.markdown("#### 💬 对话内容预览")
    
    dialogue_data = st.session_state.dialogue_data
    
    # 创建子选项卡
    subtab1, subtab2, subtab3 = st.tabs(["📖 章节对话", "📝 句子对话", "🎭 行为时间线"])
    
    with subtab1:
        show_chapter_dialogues(dialogue_data.get("chapter_dialogues", []))
    
    with subtab2:
        show_sentence_dialogues(dialogue_data.get("sentence_dialogues", []))
    
    with subtab3:
        show_behavior_timeline(dialogue_data.get("behavior_timeline", []))

def show_chapter_dialogues(chapter_dialogues):
    """显示章节级对话"""
    if not chapter_dialogues:
        st.info("📝 暂无章节对话数据")
        return
    
    st.markdown("##### 📖 章节对话概览")
    
    # 显示模式选择
    display_mode = st.radio(
        "显示模式",
        ["章节汇总对话", "句子级详细对话"],
        key="chapter_dialogue_display_mode",
        help="章节汇总：将所有句子的对话合并显示；句子级详细：显示每个句子的对话"
    )
    
    if display_mode == "章节汇总对话":
        show_chapter_summary_dialogues(chapter_dialogues)
    else:
        show_chapter_sentence_dialogues(chapter_dialogues)

def show_chapter_summary_dialogues(chapter_dialogues):
    """显示章节汇总对话"""
    st.markdown("#### 📖 章节汇总对话")
    
    # 按章节组织对话数据
    chapter_summary = organize_dialogues_by_chapter(chapter_dialogues)
    
    # 创建章节选择器
    chapter_options = [f"第{i+1}章" for i in range(len(chapter_summary))]
    selected_chapter = st.selectbox("选择章节", chapter_options, key="chapter_summary_selector")
    
    if selected_chapter:
        chapter_idx = int(selected_chapter.replace("第", "").replace("章", "")) - 1
        
        if 0 <= chapter_idx < len(chapter_summary):
            chapter_data = chapter_summary[chapter_idx]
            
            # 显示章节信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📖 **章节**: {selected_chapter}")
                if chapter_idx < len(st.session_state.story_data):
                    story_chapter = st.session_state.story_data[chapter_idx]
                    st.info(f"📝 **标题**: {story_chapter.get('title', '未知')}")
            
            with col2:
                st.metric("对话轮数", len(chapter_data['dialogues']))
                st.metric("参与角色", len(chapter_data['characters']))
            
            with col3:
                st.metric("总句子数", chapter_data['sentence_count'])
                st.metric("有对话句子", chapter_data['dialogue_sentence_count'])
            
            # 显示角色列表
            if chapter_data['characters']:
                st.markdown("**👥 参与角色：**")
                character_cols = st.columns(min(len(chapter_data['characters']), 4))
                for i, char in enumerate(chapter_data['characters']):
                    with character_cols[i % len(character_cols)]:
                        st.markdown(f"🎭 **{char}**")
            
            st.markdown("---")
            
            # 显示完整章节对话
            if chapter_data['dialogues']:
                st.markdown("##### 💬 完整章节对话")
                
                for i, dialogue in enumerate(chapter_data['dialogues']):
                    dialogue_text = dialogue.get('dialogue', dialogue.get('line', ''))
                    speaker = dialogue.get('speaker', '未知角色')
                    action = dialogue.get('action', '')
                    sentence_context = dialogue.get('sentence_context', '')
                    
                    # 创建对话卡片
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        
                        with col1:
                            st.markdown(f"**🎭 {speaker}**")
                        
                        with col2:
                            st.markdown(f"💬 {dialogue_text}")
                            if action:
                                st.markdown(f"*🎭 {action}*")
                            if sentence_context:
                                with st.expander("📋 场景上下文", expanded=False):
                                    st.caption(sentence_context)
                        
                        # 添加分隔线（除了最后一个对话）
                        if i < len(chapter_data['dialogues']) - 1:
                            st.markdown("---")
            else:
                st.info("📝 该章节暂无对话内容")

def organize_dialogues_by_chapter(chapter_dialogues):
    """将句子级对话按章节组织"""
    # 假设每6个句子为一章（根据您的数据调整）
    sentences_per_chapter = 6
    chapter_summary = []
    
    current_chapter = []
    current_chapter_dialogues = []
    current_chapter_characters = set()
    sentence_count = 0
    dialogue_sentence_count = 0
    
    for i, sentence_data in enumerate(chapter_dialogues):
        current_chapter.append(sentence_data)
        sentence_count += 1
        
        # 收集该句子的对话
        dialogues = sentence_data.get("dialogue", [])
        if dialogues:
            dialogue_sentence_count += 1
            for dialogue in dialogues:
                # 添加句子上下文
                dialogue_with_context = dialogue.copy()
                dialogue_with_context['sentence_context'] = sentence_data.get('sentence', '')
                current_chapter_dialogues.append(dialogue_with_context)
                current_chapter_characters.add(dialogue.get('speaker', '未知'))
        
        # 每6个句子或到达末尾时创建一个章节
        if (i + 1) % sentences_per_chapter == 0 or i == len(chapter_dialogues) - 1:
            chapter_summary.append({
                'sentences': current_chapter,
                'dialogues': current_chapter_dialogues,
                'characters': list(current_chapter_characters),
                'sentence_count': sentence_count,
                'dialogue_sentence_count': dialogue_sentence_count
            })
            
            # 重置计数器
            current_chapter = []
            current_chapter_dialogues = []
            current_chapter_characters = set()
            sentence_count = 0
            dialogue_sentence_count = 0
    
    return chapter_summary

def show_chapter_sentence_dialogues(chapter_dialogues):
    """显示章节句子级对话（原来的显示方式）"""
    st.markdown("#### 📝 句子级详细对话")
    
    # 创建章节选择器（每6个句子为一章）
    sentences_per_chapter = 6
    total_chapters = (len(chapter_dialogues) + sentences_per_chapter - 1) // sentences_per_chapter
    chapter_options = [f"第{i+1}章" for i in range(total_chapters)]
    selected_chapter = st.selectbox("选择章节", chapter_options, key="chapter_sentence_selector")
    
    if selected_chapter:
        chapter_idx = int(selected_chapter.replace("第", "").replace("章", "")) - 1
        
        # 计算该章节的句子范围
        start_idx = chapter_idx * sentences_per_chapter
        end_idx = min(start_idx + sentences_per_chapter, len(chapter_dialogues))
        
        st.info(f"显示第 {start_idx + 1}-{end_idx} 个句子，共 {end_idx - start_idx} 个句子")
        
        # 显示该章节的句子对话
        for i in range(start_idx, end_idx):
            if i < len(chapter_dialogues):
                sentence_data = chapter_dialogues[i]
                
                with st.expander(f"句子 {i+1}: {sentence_data.get('sentence', '')[:50]}...", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**📝 原句**: {sentence_data.get('sentence', '')}")
                        
                        dialogues = sentence_data.get('dialogue', [])
                        if dialogues:
                            st.markdown("**💬 生成对话**:")
                            for j, dialogue in enumerate(dialogues):
                                # 兼容不同的字段名
                                dialogue_text = dialogue.get('dialogue', dialogue.get('line', ''))
                                speaker = dialogue.get('speaker', '')
                                action = dialogue.get('action', '')
                                
                                st.markdown(f"  {j+1}. **{speaker}**: {dialogue_text}")
                                if action:
                                    st.markdown(f"     *{action}*")
                    
                    with col2:
                        st.markdown(f"**🎭 需要对话**: {'是' if sentence_data.get('need_to_action') else '否'}")
                        actors = sentence_data.get('actor_list', [])
                        if actors:
                            st.markdown(f"**👥 参与角色**: {', '.join(actors)}")

def show_sentence_dialogues(sentence_dialogues):
    """显示句子级对话"""
    if not sentence_dialogues:
        st.info("📝 暂无句子对话数据")
        return
    
    st.markdown("##### 📝 句子级对话详情")
    
    # 分页显示
    items_per_page = 10
    total_pages = (len(sentence_dialogues) + items_per_page - 1) // items_per_page
    
    if total_pages > 1:
        page = st.selectbox("选择页面", range(1, total_pages + 1), key="sentence_dialogue_page") - 1
    else:
        page = 0
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(sentence_dialogues))
    
    st.info(f"显示第 {start_idx + 1}-{end_idx} 项，共 {len(sentence_dialogues)} 项")
    
    for i in range(start_idx, end_idx):
        sentence_dialogue = sentence_dialogues[i]
        
        with st.expander(f"句子 {i+1}: {sentence_dialogue.get('sentence', '')[:50]}...", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**📝 原句**: {sentence_dialogue.get('sentence', '')}")
                
                dialogues = sentence_dialogue.get('dialogue', [])
                if dialogues:
                    st.markdown("**💬 生成对话**:")
                    for j, dialogue in enumerate(dialogues):
                        # 兼容不同的字段名
                        dialogue_text = dialogue.get('dialogue', dialogue.get('line', ''))
                        speaker = dialogue.get('speaker', '')
                        action = dialogue.get('action', '')
                        
                        st.markdown(f"  {j+1}. **{speaker}**: {dialogue_text}")
                        if action:
                            st.markdown(f"     *{action}*")
            
            with col2:
                st.markdown(f"**🎭 需要对话**: {'是' if sentence_dialogue.get('need_to_action') else '否'}")
                actors = sentence_dialogue.get('actor_list', [])
                if actors:
                    st.markdown(f"**👥 参与角色**: {', '.join(actors)}")

def show_behavior_timeline(behavior_timeline):
    """显示行为时间线"""
    if not behavior_timeline:
        st.info("📝 暂无行为时间线数据")
        return
    
    st.markdown("##### 🎭 角色行为时间线")
    
    # 统计信息
    characters = set(item.get("character", "") for item in behavior_timeline)
    chapters = set(item.get("chapter_id", "") for item in behavior_timeline)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总行为数", len(behavior_timeline))
    with col2:
        st.metric("涉及角色", len(characters))
    with col3:
        st.metric("涉及章节", len(chapters))
    
    # 显示模式选择
    display_mode = st.radio(
        "显示模式",
        ["角色发展轨迹", "时间线列表", "章节分组"],
        key="behavior_display_mode",
        help="角色发展轨迹：按角色显示完整发展过程；时间线列表：按时间顺序显示；章节分组：按章节分组显示"
    )
    
    if display_mode == "角色发展轨迹":
        show_character_development_arcs(behavior_timeline, characters)
    elif display_mode == "时间线列表":
        show_timeline_list(behavior_timeline, characters, chapters)
    else:  # 章节分组
        show_chapter_grouped_behavior(behavior_timeline, chapters)

def show_character_development_arcs(behavior_timeline, characters):
    """显示角色发展轨迹"""
    st.markdown("#### 🎭 角色发展轨迹")
    
    # 按角色组织数据
    character_arcs = {}
    for item in behavior_timeline:
        char = item.get("character", "未知")
        if char not in character_arcs:
            character_arcs[char] = []
        character_arcs[char].append(item)
    
    # 按章节和句子排序
    for char in character_arcs:
        character_arcs[char].sort(key=lambda x: (x.get("chapter_id", ""), x.get("sentence_index", 0)))
    
    # 选择要查看的角色
    if len(characters) > 1:
        selected_chars = st.multiselect(
            "选择要查看的角色",
            list(characters),
            default=list(characters)[:3] if len(characters) > 3 else list(characters),
            key="selected_chars_arc"
        )
    else:
        selected_chars = list(characters)
    
    for char in selected_chars:
        if char in character_arcs:
            with st.expander(f"🎭 {char} 的发展轨迹", expanded=True):
                arc_data = character_arcs[char]
                
                # 显示角色统计
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("行为事件数", len(arc_data))
                with col2:
                    chapters_involved = set(item.get("chapter_id", "") for item in arc_data)
                    st.metric("涉及章节", len(chapters_involved))
                with col3:
                    unique_behaviors = set(item.get("behavior", "") for item in arc_data)
                    st.metric("行为类型", len(unique_behaviors))
                
                # 显示发展时间线
                st.markdown("**📈 发展时间线：**")
                
                for i, item in enumerate(arc_data):
                    chapter_id = item.get("chapter_id", "")
                    sentence_idx = item.get("sentence_index", 0)
                    behavior = item.get("behavior", "")
                    scene_context = item.get("scene_context", "")
                    
                    # 创建时间线条目
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        st.markdown(f"**{i+1}.** `{chapter_id}`")
                        st.caption(f"句子 {sentence_idx}")
                    
                    with col2:
                        st.markdown(f"**💭 {behavior}**")
                        if scene_context:
                            st.caption(f"📋 {scene_context[:100]}{'...' if len(scene_context) > 100 else ''}")
                    
                    # 添加连接线（除了最后一个）
                    if i < len(arc_data) - 1:
                        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;↓")
                
                # 显示行为总结
                st.markdown("**📊 行为总结：**")
                behavior_summary = {}
                for item in arc_data:
                    behavior = item.get("behavior", "")
                    if behavior in behavior_summary:
                        behavior_summary[behavior] += 1
                    else:
                        behavior_summary[behavior] = 1
                
                for behavior, count in sorted(behavior_summary.items(), key=lambda x: x[1], reverse=True):
                    st.markdown(f"- **{behavior}** (出现 {count} 次)")

def show_timeline_list(behavior_timeline, characters, chapters):
    """显示时间线列表"""
    st.markdown("#### ⏰ 时间线列表")
    
    # 筛选选项
    col1, col2 = st.columns(2)
    with col1:
        selected_character = st.selectbox("筛选角色", ["全部"] + list(characters), key="behavior_character_filter")
    with col2:
        selected_chapter = st.selectbox("筛选章节", ["全部"] + list(chapters), key="behavior_chapter_filter")
    
    # 筛选数据
    filtered_timeline = behavior_timeline
    if selected_character != "全部":
        filtered_timeline = [item for item in filtered_timeline if item.get("character") == selected_character]
    if selected_chapter != "全部":
        filtered_timeline = [item for item in filtered_timeline if item.get("chapter_id") == selected_chapter]
    
    # 按时间排序
    filtered_timeline.sort(key=lambda x: (x.get("chapter_id", ""), x.get("sentence_index", 0)))
    
    # 分页显示
    items_per_page = 15
    total_pages = (len(filtered_timeline) + items_per_page - 1) // items_per_page
    
    if total_pages > 1:
        page = st.selectbox("选择页面", range(1, total_pages + 1), key="behavior_timeline_page") - 1
    else:
        page = 0
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(filtered_timeline))
    
    st.info(f"显示第 {start_idx + 1}-{end_idx} 项，共 {len(filtered_timeline)} 项")
    
    # 显示时间线
    for i in range(start_idx, end_idx):
        item = filtered_timeline[i]
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 3])
        
        with col1:
            st.markdown(f"**🎭 {item.get('character', '未知')}**")
        
        with col2:
            st.markdown(f"📖 {item.get('chapter_id', '')}")
        
        with col3:
            st.markdown(f"📝 句子 {item.get('sentence_index', 0)}")
        
        with col4:
            st.markdown(f"💭 {item.get('behavior', '')}")
        
        # 显示场景上下文
        if item.get('scene_context'):
            with st.expander(f"📋 场景上下文 {i+1}", expanded=False):
                st.text(item.get('scene_context', ''))
        
        if i < end_idx - 1:
            st.markdown("---")

def show_chapter_grouped_behavior(behavior_timeline, chapters):
    """显示按章节分组的行为"""
    st.markdown("#### 📖 按章节分组的行为")
    
    # 按章节组织数据
    chapter_behaviors = {}
    for item in behavior_timeline:
        chapter = item.get("chapter_id", "未知章节")
        if chapter not in chapter_behaviors:
            chapter_behaviors[chapter] = []
        chapter_behaviors[chapter].append(item)
    
    # 按章节排序
    sorted_chapters = sorted(chapter_behaviors.keys())
    
    for chapter in sorted_chapters:
        behaviors = chapter_behaviors[chapter]
        
        with st.expander(f"📖 {chapter} ({len(behaviors)} 个行为事件)", expanded=False):
            # 按句子索引排序
            behaviors.sort(key=lambda x: x.get("sentence_index", 0))
            
            # 统计该章节的角色
            chapter_characters = set(item.get("character", "") for item in behaviors)
            st.info(f"涉及角色: {', '.join(chapter_characters)}")
            
            # 显示行为列表
            for i, item in enumerate(behaviors):
                col1, col2, col3 = st.columns([2, 1, 3])
                
                with col1:
                    st.markdown(f"**🎭 {item.get('character', '未知')}**")
                
                with col2:
                    st.markdown(f"📝 句子 {item.get('sentence_index', 0)}")
                
                with col3:
                    st.markdown(f"💭 {item.get('behavior', '')}")
                
                if i < len(behaviors) - 1:
                    st.markdown("---")

def show_dialogue_edit_mode():
    """对话编辑模式"""
    if not st.session_state.get('dialogue_data'):
        st.info("📝 暂无对话数据，请先生成对话")
        return
    
    st.markdown("#### ✏️ 编辑对话内容")
    
    # 历史操作面板
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("↩️ 撤销", use_container_width=True):
            undo_dialogue_action()
    with col2:
        if st.button("↪️ 重做", use_container_width=True):
            redo_dialogue_action()
    with col3:
        if st.button("📋 历史记录", use_container_width=True):
            st.session_state.show_dialogue_history = not st.session_state.get('show_dialogue_history', False)
    
    # 显示历史记录面板
    if st.session_state.get('show_dialogue_history', False):
        show_dialogue_history_panel()
    
    st.markdown("---")
    
    # 编辑选项
    edit_tab1, edit_tab2 = st.tabs(["🔄 重新生成", "✏️ 手动编辑"])
    
    with edit_tab1:
        show_dialogue_regeneration_options()
    
    with edit_tab2:
        show_dialogue_manual_edit()

def show_dialogue_history_panel():
    """显示对话历史记录面板"""
    st.markdown("##### 📋 对话操作历史")
    
    if not st.session_state.dialogue_history:
        st.info("📝 暂无历史记录")
        return
    
    # 显示当前位置
    current_idx = st.session_state.dialogue_history_index
    total_count = len(st.session_state.dialogue_history)
    st.info(f"📍 当前位置: {current_idx + 1}/{total_count}")
    
    # 显示历史记录
    for i, entry in enumerate(reversed(st.session_state.dialogue_history)):
        actual_idx = total_count - 1 - i
        is_current = actual_idx == current_idx
        
        with st.expander(
            f"{'🔵' if is_current else '⚪'} {entry['action']} - {entry['timestamp'][:19]}",
            expanded=is_current
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**操作**: {entry['action']}")
            with col2:
                st.markdown(f"**时间**: {entry['timestamp'][:19]}")
            with col3:
                st.markdown(f"**数据量**: {entry.get('data_length', 0)} 项")
            
            if not is_current:
                if st.button(f"🔄 恢复到此状态", key=f"restore_dialogue_{actual_idx}"):
                    st.session_state.dialogue_history_index = actual_idx
                    st.session_state.dialogue_data = copy.deepcopy(entry["dialogue_data"])
                    st.success(f"✅ 已恢复到: {entry['action']}")
                    st.rerun()
        
        if i < len(st.session_state.dialogue_history) - 1:
            st.markdown("---")

def show_dialogue_regeneration_options():
    """对话重新生成选项"""
    st.markdown("##### 🔄 重新生成对话")
    
    # 选择重新生成的范围
    regen_scope = st.radio(
        "重新生成范围",
        ["单个章节", "全部章节", "特定角色"],
        key="dialogue_regen_scope"
    )
    
    if regen_scope == "单个章节":
        chapter_options = [f"第{i+1}章" for i in range(len(st.session_state.story_data))]
        selected_chapter = st.selectbox("选择章节", chapter_options, key="regen_chapter_selector")
        
        if st.button("🔄 重新生成该章节对话", type="primary"):
            chapter_idx = int(selected_chapter.replace("第", "").replace("章", "")) - 1
            regenerate_single_chapter_dialogue(chapter_idx)
    
    elif regen_scope == "全部章节":
        st.warning("⚠️ 这将重新生成所有章节的对话，可能需要较长时间")
        
        if st.button("🔄 重新生成全部对话", type="primary"):
            regenerate_all_dialogues()
    
    elif regen_scope == "特定角色":
        characters = [char.get("name", f"角色{i+1}") for i, char in enumerate(st.session_state.characters_data)]
        selected_character = st.selectbox("选择角色", characters, key="regen_character_selector")
        
        if st.button("🔄 重新生成该角色对话", type="primary"):
            regenerate_character_dialogues(selected_character)

def regenerate_single_chapter_dialogue(chapter_idx):
    """重新生成单个章节的对话"""
    try:
        print(f"🔄🔄🔄 [对话重生成] ===== 开始重新生成第{chapter_idx+1}章对话 =====")
        
        # 保存当前状态
        save_dialogue_to_history(f"重新生成第{chapter_idx+1}章对话前")
        
        with st.spinner(f"🔄 正在重新生成第{chapter_idx+1}章对话..."):
            # 获取该章节的故事内容
            if chapter_idx >= len(st.session_state.story_data):
                st.error(f"❌ 章节索引超出范围: {chapter_idx}")
                return
            
            chapter_story = [st.session_state.story_data[chapter_idx]]
            
            # 调用后端重新生成
            chapter_results, sentence_results, behavior_timeline = analyze_dialogue_insertions_v2(
                chapter_story, 
                st.session_state.characters_data
            )
            
            # 更新对话数据
            if st.session_state.dialogue_data and "chapter_dialogues" in st.session_state.dialogue_data:
                # 更新指定章节的对话
                st.session_state.dialogue_data["chapter_dialogues"][chapter_idx] = chapter_results[0] if chapter_results else {}
                
                # 更新句子级对话（需要找到对应的句子）
                # 这里简化处理，实际可能需要更复杂的匹配逻辑
                if sentence_results:
                    # 找到属于该章节的句子对话并替换
                    chapter_id = st.session_state.story_data[chapter_idx].get("chapter_id", f"chapter_{chapter_idx+1}")
                    
                    # 移除旧的该章节句子对话
                    old_sentence_dialogues = st.session_state.dialogue_data.get("sentence_dialogues", [])
                    new_sentence_dialogues = [s for s in old_sentence_dialogues if not s.get("sentence", "").startswith(chapter_id)]
                    
                    # 添加新的句子对话
                    new_sentence_dialogues.extend(sentence_results)
                    st.session_state.dialogue_data["sentence_dialogues"] = new_sentence_dialogues
                
                # 更新行为时间线
                if behavior_timeline:
                    old_timeline = st.session_state.dialogue_data.get("behavior_timeline", [])
                    chapter_id = st.session_state.story_data[chapter_idx].get("chapter_id", f"chapter_{chapter_idx+1}")
                    
                    # 移除旧的该章节行为
                    new_timeline = [b for b in old_timeline if b.get("chapter_id") != chapter_id]
                    
                    # 添加新的行为
                    new_timeline.extend(behavior_timeline)
                    st.session_state.dialogue_data["behavior_timeline"] = new_timeline
            
            print(f"🔄 [对话重生成] 第{chapter_idx+1}章对话重新生成完成")
            st.success(f"✅ 第{chapter_idx+1}章对话重新生成完成！")
            
            # 保存操作到历史
            save_dialogue_to_history(f"重新生成第{chapter_idx+1}章对话完成")
            
    except Exception as e:
        error_msg = f"重新生成第{chapter_idx+1}章对话失败: {str(e)}"
        print(f"❌ [对话重生成] {error_msg}")
        st.error(f"❌ {error_msg}")

def regenerate_all_dialogues(behavior_model="gpt-4.1"):
    """重新生成全部对话"""
    try:
        print(f"🔄🔄🔄 [对话重生成] ===== 开始重新生成全部对话 =====")
        
        # 保存当前状态
        save_dialogue_to_history("重新生成全部对话前")
        
        # 直接调用生成函数
        generate_dialogues_from_story(use_cache=False, auto_save=True, behavior_model=behavior_model)
        
        print(f"🔄🔄🔄 [对话重生成] ===== 全部对话重新生成完成 =====")
        
    except Exception as e:
        error_msg = f"重新生成全部对话失败: {str(e)}"
        print(f"❌ [对话重生成] {error_msg}")
        st.error(f"❌ {error_msg}")

def regenerate_character_dialogues(character_name):
    """重新生成特定角色的对话"""
    try:
        print(f"🔄🔄🔄 [对话重生成] ===== 开始重新生成角色 {character_name} 的对话 =====")
        
        # 保存当前状态
        save_dialogue_to_history(f"重新生成角色{character_name}对话前")
        
        with st.spinner(f"🔄 正在重新生成角色 {character_name} 的对话..."):
            # 这里需要实现角色特定的对话重新生成逻辑
            # 由于后端API限制，这里暂时使用全量重新生成
            st.warning("⚠️ 当前版本暂不支持单独重新生成特定角色对话，将重新生成全部对话")
            regenerate_all_dialogues()
        
        print(f"🔄 [对话重生成] 角色 {character_name} 对话重新生成完成")
        
    except Exception as e:
        error_msg = f"重新生成角色 {character_name} 对话失败: {str(e)}"
        print(f"❌ [对话重生成] {error_msg}")
        st.error(f"❌ {error_msg}")

def show_dialogue_manual_edit():
    """手动编辑对话"""
    st.markdown("##### ✏️ 手动编辑对话内容")
    
    if not st.session_state.get('dialogue_data', {}).get('chapter_dialogues'):
        st.info("📝 暂无章节对话数据可编辑")
        return
    
    # 选择要编辑的章节
    chapter_options = [f"第{i+1}章" for i in range(len(st.session_state.dialogue_data["chapter_dialogues"]))]
    selected_chapter = st.selectbox("选择要编辑的章节", chapter_options, key="edit_chapter_selector")
    
    if selected_chapter:
        chapter_idx = int(selected_chapter.replace("第", "").replace("章", "")) - 1
        
        if 0 <= chapter_idx < len(st.session_state.dialogue_data["chapter_dialogues"]):
            edit_chapter_dialogue(chapter_idx)

def edit_chapter_dialogue(chapter_idx):
    """编辑指定章节的对话"""
    chapter_dialogue = st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]
    dialogues = chapter_dialogue.get("dialogue", [])
    
    st.markdown(f"##### 编辑第{chapter_idx+1}章对话")
    
    if not dialogues:
        st.info("📝 该章节暂无对话内容")
        
        # 添加新对话
        if st.button("➕ 添加对话", key=f"add_dialogue_{chapter_idx}"):
            add_new_dialogue_to_chapter(chapter_idx)
        return
    
    # 显示现有对话并提供编辑功能
    for i, dialogue in enumerate(dialogues):
        # 兼容不同的字段名
        dialogue_text = dialogue.get('dialogue', dialogue.get('line', ''))
        speaker = dialogue.get('speaker', '未知')
        
        with st.expander(f"对话 {i+1}: {speaker} - {dialogue_text[:30]}...", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # 编辑对话内容
                new_speaker = st.text_input(
                    "角色名称", 
                    value=speaker, 
                    key=f"edit_speaker_{chapter_idx}_{i}"
                )
                
                new_dialogue = st.text_area(
                    "对话内容", 
                    value=dialogue_text, 
                    key=f"edit_dialogue_{chapter_idx}_{i}",
                    height=100
                )
                
                new_action = st.text_area(
                    "动作描述", 
                    value=dialogue.get('action', ''), 
                    key=f"edit_action_{chapter_idx}_{i}",
                    height=60
                )
            
            with col2:
                # 操作按钮
                if st.button("💾 保存修改", key=f"save_dialogue_{chapter_idx}_{i}"):
                    save_dialogue_edit(chapter_idx, i, new_speaker, new_dialogue, new_action)
                
                if st.button("🗑️ 删除对话", key=f"delete_dialogue_{chapter_idx}_{i}"):
                    delete_dialogue_from_chapter(chapter_idx, i)
    
    # 添加新对话
    st.markdown("---")
    if st.button("➕ 添加新对话", key=f"add_new_dialogue_{chapter_idx}"):
        add_new_dialogue_to_chapter(chapter_idx)

def save_dialogue_edit(chapter_idx, dialogue_idx, new_speaker, new_dialogue, new_action):
    """保存对话编辑"""
    try:
        print(f"💾 [对话编辑] 保存第{chapter_idx+1}章第{dialogue_idx+1}个对话的修改")
        
        # 保存当前状态
        save_dialogue_to_history(f"编辑第{chapter_idx+1}章对话{dialogue_idx+1}前")
        
        # 更新对话内容 - 使用 "line" 字段以保持与后端数据格式一致
        st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]["dialogue"][dialogue_idx] = {
            "speaker": new_speaker,
            "line": new_dialogue,  # 使用 "line" 字段
            "action": new_action
        }
        
        # 保存操作到历史
        save_dialogue_to_history(f"编辑第{chapter_idx+1}章对话{dialogue_idx+1}完成")
        
        st.success(f"✅ 第{chapter_idx+1}章对话 {dialogue_idx+1} 修改已保存")
        st.rerun()
        
    except Exception as e:
        error_msg = f"保存对话编辑失败: {str(e)}"
        print(f"❌ [对话编辑] {error_msg}")
        st.error(f"❌ {error_msg}")

def delete_dialogue_from_chapter(chapter_idx, dialogue_idx):
    """从章节中删除对话"""
    try:
        print(f"🗑️ [对话删除] 删除第{chapter_idx+1}章第{dialogue_idx+1}个对话")
        
        # 保存当前状态
        save_dialogue_to_history(f"删除第{chapter_idx+1}章对话{dialogue_idx+1}前")
        
        # 删除对话
        dialogues = st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]["dialogue"]
        if 0 <= dialogue_idx < len(dialogues):
            dialogues.pop(dialogue_idx)
        
        # 保存操作到历史
        save_dialogue_to_history(f"删除第{chapter_idx+1}章对话{dialogue_idx+1}完成")
        
        st.success(f"✅ 第{chapter_idx+1}章对话 {dialogue_idx+1} 已删除")
        st.rerun()
        
    except Exception as e:
        error_msg = f"删除对话失败: {str(e)}"
        print(f"❌ [对话删除] {error_msg}")
        st.error(f"❌ {error_msg}")

def add_new_dialogue_to_chapter(chapter_idx):
    """向章节添加新对话"""
    st.markdown(f"##### ➕ 向第{chapter_idx+1}章添加新对话")
    
    # 获取可用角色
    characters = [char.get("name", f"角色{i+1}") for i, char in enumerate(st.session_state.characters_data)]
    
    with st.form(f"add_dialogue_form_{chapter_idx}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_speaker = st.selectbox("选择角色", characters + ["其他"], key=f"new_speaker_{chapter_idx}")
            if new_speaker == "其他":
                new_speaker = st.text_input("自定义角色名", key=f"custom_speaker_{chapter_idx}")
        
        with col2:
            st.write("")  # 占位
        
        new_dialogue = st.text_area("对话内容", key=f"new_dialogue_content_{chapter_idx}", height=100)
        new_action = st.text_area("动作描述（可选）", key=f"new_action_{chapter_idx}", height=60)
        
        if st.form_submit_button("➕ 添加对话"):
            if new_speaker and new_dialogue:
                try:
                    # 保存当前状态
                    save_dialogue_to_history(f"添加第{chapter_idx+1}章新对话前")
                    
                    # 添加新对话 - 使用 "line" 字段以保持与后端数据格式一致
                    new_dialogue_item = {
                        "speaker": new_speaker,
                        "line": new_dialogue,  # 使用 "line" 字段
                        "action": new_action
                    }
                    
                    if "dialogue" not in st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]:
                        st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]["dialogue"] = []
                    
                    st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]["dialogue"].append(new_dialogue_item)
                    
                    # 保存操作到历史
                    save_dialogue_to_history(f"添加第{chapter_idx+1}章新对话完成")
                    
                    st.success(f"✅ 新对话已添加到第{chapter_idx+1}章")
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"添加新对话失败: {str(e)}"
                    print(f"❌ [对话添加] {error_msg}")
                    st.error(f"❌ {error_msg}")
            else:
                st.error("❌ 请填写角色名称和对话内容")

def show_dialogue_file_management():
    """对话文件管理"""
    st.markdown("#### 📁 对话文件管理")
    
    # 文件操作选项
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 保存到项目", type="primary", use_container_width=True):
            save_dialogue_to_project()
    
    with col2:
        if st.button("📁 加载对话文件", use_container_width=True):
            st.session_state.show_dialogue_loader_file = True
            st.rerun()
    
    with col3:
        if st.button("📤 导出对话", use_container_width=True):
            export_dialogue_files()
    
    # 显示对话加载器
    if st.session_state.get('show_dialogue_loader_file', False):
        load_existing_dialogue("file_management")
    
    # 显示当前对话文件信息
    if st.session_state.get('dialogue_data'):
        st.markdown("---")
        st.markdown("##### 📊 当前对话数据信息")
        
        dialogue_data = st.session_state.dialogue_data
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            chapter_count = len(dialogue_data.get("chapter_dialogues", []))
            st.metric("章节对话", chapter_count)
        
        with col2:
            sentence_count = len(dialogue_data.get("sentence_dialogues", []))
            st.metric("句子对话", sentence_count)
        
        with col3:
            behavior_count = len(dialogue_data.get("behavior_timeline", []))
            st.metric("行为事件", behavior_count)
        
        with col4:
            generation_params = dialogue_data.get("generation_params", {})
            timestamp = generation_params.get("timestamp", "未知")
            st.metric("生成时间", timestamp[:10] if timestamp != "未知" else "未知")

def save_dialogue_to_project():
    """保存对话到项目目录"""
    try:
        if not st.session_state.get('dialogue_data'):
            st.warning("⚠️ 暂无对话数据可保存")
            return
        
        print(f"💾💾💾 [对话保存] ===== 开始保存对话到项目 =====")
        
        start_time = time.time()
        
        # 保存章节对话
        chapter_dialogues = st.session_state.dialogue_data.get("chapter_dialogues", [])
        save_json(chapter_dialogues, st.session_state.current_version, "dialogue_marks.json")
        
        # 保存句子对话
        sentence_dialogues = st.session_state.dialogue_data.get("sentence_dialogues", [])
        save_json(sentence_dialogues, st.session_state.current_version, "sentence_dialogues.json")
        
        # 保存行为时间线
        behavior_timeline = st.session_state.dialogue_data.get("behavior_timeline", [])
        save_json(behavior_timeline, st.session_state.current_version, "behavior_timeline_raw.json")
        
        # 保存完整对话数据
        save_json(st.session_state.dialogue_data, st.session_state.current_version, "dialogue_complete.json")
        
        end_time = time.time()
        
        # 记录操作日志
        log_backend_operation(
            "保存对话到项目", 
            {"version": st.session_state.current_version},
            start_time, end_time, 
            {
                "chapter_dialogues": len(chapter_dialogues),
                "sentence_dialogues": len(sentence_dialogues),
                "behavior_timeline": len(behavior_timeline)
            }
        )
        
        print(f"💾 [对话保存] 章节对话: {len(chapter_dialogues)} 项")
        print(f"💾 [对话保存] 句子对话: {len(sentence_dialogues)} 项")
        print(f"💾 [对话保存] 行为时间线: {len(behavior_timeline)} 项")
        print(f"💾💾💾 [对话保存] ===== 保存完成 =====")
        
        st.success(f"✅ 对话数据已保存到项目目录: {st.session_state.current_version}/")
        
        # 显示保存详情
        with st.expander("📄 保存详情", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.json({
                    "版本目录": st.session_state.current_version,
                    "章节对话文件": "dialogue_marks.json",
                    "句子对话文件": "sentence_dialogues.json"
                })
            with col2:
                st.json({
                    "行为时间线文件": "behavior_timeline_raw.json",
                    "完整数据文件": "dialogue_complete.json",
                    "保存时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
    except Exception as e:
        error_msg = f"保存对话到项目失败: {str(e)}"
        print(f"❌ [对话保存] {error_msg}")
        st.error(f"❌ {error_msg}")

def load_existing_dialogue(context="default"):
    """加载已有对话文件"""
    st.markdown("##### 📁 加载对话文件")
    
    # 提供两种加载方式
    load_method = st.radio(
        "选择加载方式",
        ["单文件加载（推荐）", "多文件加载"],
        key=f"load_method_{context}",
        help="单文件：加载完整对话数据文件；多文件：分别加载章节对话、句子对话、行为时间线文件"
    )
    
    if load_method == "单文件加载（推荐）":
        # 单文件上传器
        uploaded_file = st.file_uploader(
            "选择完整对话文件",
            type=['json'],
            help="推荐上传 dialogue_complete.json 文件，包含所有对话数据",
            key=f"dialogue_file_uploader_{context}"
        )
        
        if uploaded_file is not None:
            process_single_dialogue_file(uploaded_file, context)
    
    else:
        # 多文件上传器
        st.markdown("##### 📁 分别上传对话文件")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            chapter_file = st.file_uploader(
                "章节对话文件",
                type=['json'],
                help="dialogue_marks.json",
                key=f"chapter_dialogue_uploader_{context}"
            )
        
        with col2:
            sentence_file = st.file_uploader(
                "句子对话文件",
                type=['json'],
                help="sentence_dialogues.json",
                key=f"sentence_dialogue_uploader_{context}"
            )
        
        with col3:
            behavior_file = st.file_uploader(
                "行为时间线文件",
                type=['json'],
                help="behavior_timeline_raw.json",
                key=f"behavior_timeline_uploader_{context}"
            )
        
        if any([chapter_file, sentence_file, behavior_file]):
            process_multiple_dialogue_files(chapter_file, sentence_file, behavior_file, context)

def process_single_dialogue_file(uploaded_file, context):
    """处理单个对话文件"""
    try:
        # 读取文件内容
        uploaded_file.seek(0)
        file_content = uploaded_file.read().decode('utf-8')
        dialogue_data = json.loads(file_content)
        
        print(f"📁 [对话加载] 文件名: {uploaded_file.name}")
        print(f"📁 [对话加载] 文件大小: {len(file_content)} 字符")
        print(f"📁 [对话加载] 数据类型: {type(dialogue_data)}")
        
        # 验证文件格式
        if validate_dialogue_file(dialogue_data, uploaded_file.name):
            # 显示预览
            with st.expander("📋 文件预览", expanded=True):
                if isinstance(dialogue_data, dict):
                    # 完整对话数据格式
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        chapter_count = len(dialogue_data.get("chapter_dialogues", []))
                        st.metric("章节对话", chapter_count)
                    with col2:
                        sentence_count = len(dialogue_data.get("sentence_dialogues", []))
                        st.metric("句子对话", sentence_count)
                    with col3:
                        behavior_count = len(dialogue_data.get("behavior_timeline", []))
                        st.metric("行为事件", behavior_count)
                elif isinstance(dialogue_data, list):
                    # 单一数据格式
                    st.metric("数据项数", len(dialogue_data))
            
            # 加载确认
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 确认加载", type="primary", use_container_width=True, key=f"confirm_load_{context}"):
                    load_dialogue_data(dialogue_data, uploaded_file.name, context)
            
            with col2:
                if st.button("❌ 取消", use_container_width=True, key=f"cancel_load_{context}"):
                    close_dialogue_loader(context)
        
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON 解析失败: {str(e)}")
    except Exception as e:
        st.error(f"❌ 文件加载失败: {str(e)}")

def process_multiple_dialogue_files(chapter_file, sentence_file, behavior_file, context):
    """处理多个对话文件"""
    try:
        dialogue_data = {
            "chapter_dialogues": [],
            "sentence_dialogues": [],
            "behavior_timeline": [],
            "generation_params": {
                "loaded_from_multiple_files": True,
                "timestamp": datetime.datetime.now().isoformat()
            }
        }
        
        files_loaded = []
        
        # 加载章节对话文件
        if chapter_file is not None:
            try:
                chapter_file.seek(0)
                chapter_content = chapter_file.read().decode('utf-8')
                chapter_data = json.loads(chapter_content)
                dialogue_data["chapter_dialogues"] = chapter_data if isinstance(chapter_data, list) else []
                files_loaded.append(f"章节对话: {chapter_file.name}")
                print(f"📁 [多文件加载] 章节对话文件加载成功: {len(dialogue_data['chapter_dialogues'])} 项")
            except Exception as e:
                st.error(f"❌ 章节对话文件加载失败: {str(e)}")
        
        # 加载句子对话文件
        if sentence_file is not None:
            try:
                sentence_file.seek(0)
                sentence_content = sentence_file.read().decode('utf-8')
                sentence_data = json.loads(sentence_content)
                dialogue_data["sentence_dialogues"] = sentence_data if isinstance(sentence_data, list) else []
                files_loaded.append(f"句子对话: {sentence_file.name}")
                print(f"📁 [多文件加载] 句子对话文件加载成功: {len(dialogue_data['sentence_dialogues'])} 项")
            except Exception as e:
                st.error(f"❌ 句子对话文件加载失败: {str(e)}")
        
        # 加载行为时间线文件
        if behavior_file is not None:
            try:
                behavior_file.seek(0)
                behavior_content = behavior_file.read().decode('utf-8')
                behavior_data = json.loads(behavior_content)
                dialogue_data["behavior_timeline"] = behavior_data if isinstance(behavior_data, list) else []
                files_loaded.append(f"行为时间线: {behavior_file.name}")
                print(f"📁 [多文件加载] 行为时间线文件加载成功: {len(dialogue_data['behavior_timeline'])} 项")
            except Exception as e:
                st.error(f"❌ 行为时间线文件加载失败: {str(e)}")
        
        if files_loaded:
            # 显示加载的文件信息
            with st.expander("📋 已加载文件", expanded=True):
                for file_info in files_loaded:
                    st.success(f"✅ {file_info}")
                
                # 显示统计信息
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("章节对话", len(dialogue_data["chapter_dialogues"]))
                with col2:
                    st.metric("句子对话", len(dialogue_data["sentence_dialogues"]))
                with col3:
                    st.metric("行为事件", len(dialogue_data["behavior_timeline"]))
            
            # 加载确认
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 确认加载", type="primary", use_container_width=True, key=f"confirm_multi_load_{context}"):
                    load_dialogue_data(dialogue_data, "多文件组合", context)
            
            with col2:
                if st.button("❌ 取消", use_container_width=True, key=f"cancel_multi_load_{context}"):
                    close_dialogue_loader(context)
        else:
            st.warning("⚠️ 请至少上传一个对话文件")
    
    except Exception as e:
        st.error(f"❌ 多文件加载失败: {str(e)}")

def load_dialogue_data(dialogue_data, source_name, context):
    """加载对话数据到session state"""
    try:
        # 保存当前状态
        save_dialogue_to_history("加载对话文件前")
        
        # 加载数据
        if isinstance(dialogue_data, dict):
            st.session_state.dialogue_data = dialogue_data
        else:
            # 如果是单一格式，尝试构建完整格式
            st.session_state.dialogue_data = {
                "chapter_dialogues": dialogue_data if "dialogue" in str(dialogue_data) else [],
                "sentence_dialogues": dialogue_data if "sentence" in str(dialogue_data) else [],
                "behavior_timeline": dialogue_data if "behavior" in str(dialogue_data) else [],
                "generation_params": {
                    "loaded_from_file": source_name,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            }
        
        # 保存操作到历史
        save_dialogue_to_history(f"加载对话文件: {source_name}")
        
        st.success(f"✅ 对话数据 {source_name} 加载成功！")
        close_dialogue_loader(context)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 加载对话数据失败: {str(e)}")

def close_dialogue_loader(context):
    """关闭对话加载器"""
    if context == "generation_options":
        st.session_state.show_dialogue_loader_gen = False
    elif context == "file_management":
        st.session_state.show_dialogue_loader_file = False

def validate_dialogue_file(data, filename):
    """验证对话文件格式"""
    try:
        if isinstance(data, dict):
            # 完整对话数据格式验证
            required_keys = ["chapter_dialogues", "sentence_dialogues", "behavior_timeline"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                st.warning(f"⚠️ 文件缺少字段: {', '.join(missing_keys)}，将尝试兼容加载")
            
            return True
            
        elif isinstance(data, list):
            # 单一数据格式验证
            if not data:
                st.warning("⚠️ 文件为空列表")
                return True
            
            # 检查是否为章节对话格式
            if all(isinstance(item, dict) and "dialogue" in item for item in data):
                st.info("📋 检测到章节对话格式")
                return True
            
            # 检查是否为句子对话格式
            if all(isinstance(item, dict) and "sentence" in item for item in data):
                st.info("📋 检测到句子对话格式")
                return True
            
            # 检查是否为行为时间线格式
            if all(isinstance(item, dict) and "behavior" in item for item in data):
                st.info("📋 检测到行为时间线格式")
                return True
            
            st.warning("⚠️ 无法识别的数据格式，将尝试通用加载")
            return True
        
        else:
            st.error("❌ 不支持的数据格式，请上传 JSON 格式的对话文件")
            return False
    
    except Exception as e:
        st.error(f"❌ 文件验证失败: {str(e)}")
        return False

def export_dialogue_files():
    """导出对话文件"""
    if not st.session_state.get('dialogue_data'):
        st.warning("⚠️ 暂无对话数据可导出")
        return
    
    st.markdown("##### 📤 导出对话文件")
    
    # 导出选项
    export_format = st.radio(
        "选择导出格式",
        ["完整数据 (JSON)", "章节对话 (JSON)", "句子对话 (JSON)", "行为时间线 (JSON)", "可读文本 (TXT)"],
        key="dialogue_export_format"
    )
    
    try:
        dialogue_data = st.session_state.dialogue_data
        
        if export_format == "完整数据 (JSON)":
            export_data = dialogue_data
            filename = f"dialogue_complete_{st.session_state.current_version}.json"
            
        elif export_format == "章节对话 (JSON)":
            export_data = dialogue_data.get("chapter_dialogues", [])
            filename = f"chapter_dialogues_{st.session_state.current_version}.json"
            
        elif export_format == "句子对话 (JSON)":
            export_data = dialogue_data.get("sentence_dialogues", [])
            filename = f"sentence_dialogues_{st.session_state.current_version}.json"
            
        elif export_format == "行为时间线 (JSON)":
            export_data = dialogue_data.get("behavior_timeline", [])
            filename = f"behavior_timeline_{st.session_state.current_version}.json"
            
        elif export_format == "可读文本 (TXT)":
            export_data = generate_dialogue_text_format(dialogue_data)
            filename = f"dialogue_readable_{st.session_state.current_version}.txt"
        
        # 生成下载内容
        if export_format.endswith("(JSON)"):
            download_content = json.dumps(export_data, ensure_ascii=False, indent=2)
        else:
            download_content = export_data
        
        # 下载按钮
        st.download_button(
            label=f"📥 下载 {filename}",
            data=download_content,
            file_name=filename,
            mime="application/json" if export_format.endswith("(JSON)") else "text/plain",
            use_container_width=True
        )
        
        # 显示预览
        with st.expander("📋 导出预览", expanded=False):
            if export_format.endswith("(JSON)"):
                st.json(export_data)
            else:
                st.text(download_content[:1000] + "..." if len(download_content) > 1000 else download_content)
        
    except Exception as e:
        st.error(f"❌ 导出失败: {str(e)}")

def generate_dialogue_text_format(dialogue_data):
    """生成可读的文本格式对话"""
    lines = []
    lines.append(f"故事对话内容 - {st.session_state.current_version}")
    lines.append("=" * 50)
    lines.append("")
    
    # 章节对话
    chapter_dialogues = dialogue_data.get("chapter_dialogues", [])
    for i, chapter in enumerate(chapter_dialogues):
        lines.append(f"第{i+1}章对话")
        lines.append("-" * 20)
        
        dialogues = chapter.get("dialogue", [])
        if dialogues:
            for j, dialogue in enumerate(dialogues):
                speaker = dialogue.get("speaker", "未知")
                content = dialogue.get("dialogue", "")
                action = dialogue.get("action", "")
                
                lines.append(f"{j+1}. {speaker}: {content}")
                if action:
                    lines.append(f"   [{action}]")
                lines.append("")
        else:
            lines.append("   (无对话内容)")
            lines.append("")
        
        lines.append("")
    
    # 行为统计
    behavior_timeline = dialogue_data.get("behavior_timeline", [])
    if behavior_timeline:
        lines.append("角色行为统计")
        lines.append("-" * 20)
        
        # 按角色分组统计
        character_behaviors = {}
        for item in behavior_timeline:
            char = item.get("character", "未知")
            behavior = item.get("behavior", "")
            if char not in character_behaviors:
                character_behaviors[char] = []
            if behavior not in character_behaviors[char]:
                character_behaviors[char].append(behavior)
        
        for char, behaviors in character_behaviors.items():
            lines.append(f"{char}: {', '.join(behaviors)}")
        
        lines.append("")
    
    return "\n".join(lines)

# ==================== 故事增强功能 ====================

def save_enhancement_to_history(action_name, old_enhancement_data=None):
    """保存故事增强数据到历史记录"""
    try:
        if old_enhancement_data is None:
            old_enhancement_data = copy.deepcopy(st.session_state.enhanced_story_data) if st.session_state.enhanced_story_data else {}
        
        # 创建历史记录条目
        history_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action_name,
            "enhancement_data": old_enhancement_data,
            "data_size": len(str(old_enhancement_data)) if old_enhancement_data else 0
        }
        
        # 如果当前不在历史记录的末尾，删除后续记录
        if st.session_state.enhancement_history_index < len(st.session_state.enhancement_history) - 1:
            st.session_state.enhancement_history = st.session_state.enhancement_history[:st.session_state.enhancement_history_index + 1]
        
        # 添加新记录
        st.session_state.enhancement_history.append(history_entry)
        st.session_state.enhancement_history_index = len(st.session_state.enhancement_history) - 1
        
        # 限制历史记录数量
        max_history = 20
        if len(st.session_state.enhancement_history) > max_history:
            st.session_state.enhancement_history = st.session_state.enhancement_history[-max_history:]
            st.session_state.enhancement_history_index = len(st.session_state.enhancement_history) - 1
        
        print(f"💾 [增强历史] 保存操作: {action_name}, 当前索引: {st.session_state.enhancement_history_index}")
        
    except Exception as e:
        print(f"❌ [增强历史] 保存失败: {str(e)}")

def undo_enhancement_action():
    """撤销故事增强操作"""
    if st.session_state.enhancement_history_index > 0:
        st.session_state.enhancement_history_index -= 1
        history_entry = st.session_state.enhancement_history[st.session_state.enhancement_history_index]
        st.session_state.enhanced_story_data = copy.deepcopy(history_entry["enhancement_data"])
        st.success(f"↩️ 已撤销操作: {history_entry['action']}")
        st.rerun()
    else:
        st.warning("⚠️ 没有可撤销的操作")

def redo_enhancement_action():
    """重做故事增强操作"""
    if st.session_state.enhancement_history_index < len(st.session_state.enhancement_history) - 1:
        st.session_state.enhancement_history_index += 1
        history_entry = st.session_state.enhancement_history[st.session_state.enhancement_history_index]
        st.session_state.enhanced_story_data = copy.deepcopy(history_entry["enhancement_data"])
        st.success(f"↪️ 已重做操作: {history_entry['action']}")
        st.rerun()
    else:
        st.warning("⚠️ 没有可重做的操作")

def show_story_enhancement_interface():
    """显示故事增强界面 - 作为主流程步骤"""
    st.header("✨ 步骤5: 故事增强")
    
    # 检查前置条件
    if not st.session_state.outline_data:
        st.error("❌ 请先完成步骤1: 生成故事大纲")
        return
    
    if not st.session_state.characters_data:
        st.error("❌ 请先完成步骤2: 生成角色")
        return
    
    if not st.session_state.get('story_data'):
        st.error("❌ 请先完成步骤3: 生成故事内容")
        return
    
    if not st.session_state.get('dialogue_data'):
        st.error("❌ 请先完成步骤4: 生成对话内容")
        return
    
    # 检查故事增强功能是否可用
    if not story_enhancement_available:
        st.error("❌ 故事增强功能不可用，请检查后端模块导入")
        return
    
    # 显示基于对话的故事增强界面
    show_story_enhancement_mode()

def show_story_enhancement_mode():
    """故事增强模式选择"""
    st.markdown("### ✨ 故事增强选项")
    
    # 创建选项卡
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 生成增强版", "📋 增强预览", "✏️ 编辑增强", "📁 文件管理"])
    
    with tab1:
        show_enhancement_generation_options()
    
    with tab2:
        show_enhancement_display()
    
    with tab3:
        show_enhancement_edit_mode()
    
    with tab4:
        show_enhancement_file_management()

def show_enhancement_generation_options():
    """故事增强生成选项"""
    st.markdown("#### 🎯 生成增强版故事")
    
    # 增强参数配置
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📝 增强选项")
        enable_transitions = st.checkbox("添加章节过渡", value=True, help="在章节间添加自然的过渡句", key="gen_transitions_checkbox")
        enable_polish = st.checkbox("润色对话", value=True, help="将对话自然融入叙述中", key="gen_polish_checkbox")
        auto_save = st.checkbox("自动保存", value=True, help="生成完成后自动保存到项目目录", key="gen_auto_save_checkbox")
    
    with col2:
        st.markdown("##### ⚙️ 生成参数")
        use_cache = st.checkbox("使用缓存", value=True, help="如果已有增强数据，是否使用缓存", key="gen_use_cache_checkbox")
        
        # 显示当前状态
        if st.session_state.get('enhanced_story_data'):
            st.info("📄 已有增强版本")
        else:
            st.info("📄 尚未生成增强版本")
    
    st.markdown("---")
    
    # 生成按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✨ 生成增强版故事", type="primary", use_container_width=True):
            generate_enhanced_story(
                enable_transitions=enable_transitions,
                enable_polish=enable_polish,
                use_cache=use_cache,
                auto_save=auto_save
            )
    
    with col2:
        if st.button("🔄 重新生成", use_container_width=True):
            regenerate_enhanced_story(
                enable_transitions=enable_transitions,
                enable_polish=enable_polish
            )
    
    with col3:
        if st.button("📁 加载已有增强", use_container_width=True):
            st.session_state.show_enhancement_loader = True
            st.rerun()
    
    # 显示增强加载器
    if st.session_state.get('show_enhancement_loader', False):
        load_existing_enhancement()

def generate_enhanced_story(enable_transitions=True, enable_polish=True, use_cache=True, auto_save=True):
    """生成增强版故事"""
    try:
        print(f"✨✨✨ [故事增强] ===== 开始生成增强版故事 =====")
        print(f"✨ [故事增强] 添加过渡: {enable_transitions}")
        print(f"✨ [故事增强] 润色对话: {enable_polish}")
        print(f"✨ [故事增强] 使用缓存: {use_cache}")
        print(f"✨ [故事增强] 自动保存: {auto_save}")
        
        # 保存当前状态到历史
        save_enhancement_to_history("生成增强版故事前")
        
        with st.spinner("✨ 正在生成增强版故事..."):
            start_time = time.time()
            
            # 准备临时文件来模拟后端调用
            temp_version = f"temp_enhance_{int(time.time())}"
            
            # 创建临时目录和文件
            temp_dir = f"data/output/{temp_version}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # 保存必要的数据到临时目录
            save_json(st.session_state.outline_data, temp_version, "test_reorder_outline.json")
            save_json(st.session_state.story_data, temp_version, "story_updated.json")
            save_json(st.session_state.characters_data, temp_version, "characters.json")
            
            # 保存对话数据
            dialogue_data = st.session_state.dialogue_data
            if isinstance(dialogue_data, dict):
                sentence_dialogues = dialogue_data.get("sentence_dialogues", [])
            else:
                sentence_dialogues = dialogue_data
            
            save_json(sentence_dialogues, temp_version, "dialogue_updated.json")
            
            enhanced_content = ""
            polished_content = ""
            
            # 第一步：添加章节过渡
            if enable_transitions:
                print("✨ [故事增强] 开始添加章节过渡...")
                enhance_story_with_transitions(task_name=temp_version, input_story_file="story_updated.json")
                
                # 读取增强结果
                enhanced_path = f"data/output/{temp_version}/enhanced_story_updated.md"
                if os.path.exists(enhanced_path):
                    with open(enhanced_path, 'r', encoding='utf-8') as f:
                        enhanced_content = f.read()
                    print("✅ [故事增强] 章节过渡添加完成")
                else:
                    st.warning("⚠️ 章节过渡生成失败，将使用原始内容")
                    enhanced_content = compile_enhanced_story_manually()
            else:
                enhanced_content = compile_enhanced_story_manually()
            
            # 第二步：润色对话
            if enable_polish and enhanced_content:
                print("✨ [故事增强] 开始润色对话...")
                
                # 将增强内容写入临时文件供润色使用
                with open(f"data/output/{temp_version}/enhanced_story_updated.md", 'w', encoding='utf-8') as f:
                    f.write(enhanced_content)
                
                polish_dialogues_in_story(task_name=temp_version, input_dialogue_file="dialogue_updated.json")
                
                # 读取润色结果
                polished_path = f"data/output/{temp_version}/enhanced_story_dialogue_updated.md"
                if os.path.exists(polished_path):
                    with open(polished_path, 'r', encoding='utf-8') as f:
                        polished_content = f.read()
                    print("✅ [故事增强] 对话润色完成")
                else:
                    st.warning("⚠️ 对话润色失败，将使用过渡版本")
                    polished_content = enhanced_content
            else:
                polished_content = enhanced_content
            
            end_time = time.time()
            
            # 保存增强结果
            st.session_state.enhanced_story_data = {
                "enhanced_content": enhanced_content,
                "polished_content": polished_content,
                "final_content": polished_content or enhanced_content,
                "generation_params": {
                    "enable_transitions": enable_transitions,
                    "enable_polish": enable_polish,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "processing_time": end_time - start_time
                },
                "temp_version": temp_version
            }
            
            # 清理临时文件
            try:
                import shutil
                shutil.rmtree(temp_dir)
                print(f"🗑️ [故事增强] 清理临时目录: {temp_dir}")
            except Exception as e:
                print(f"⚠️ [故事增强] 临时目录清理失败: {e}")
            
            # 记录操作日志
            log_backend_operation(
                "故事增强", 
                {
                    "enable_transitions": enable_transitions,
                    "enable_polish": enable_polish,
                    "story_chapters": len(st.session_state.story_data),
                    "dialogue_sentences": len(sentence_dialogues)
                },
                start_time, end_time, 
                {
                    "enhanced_content_length": len(enhanced_content),
                    "polished_content_length": len(polished_content),
                    "final_content_length": len(polished_content or enhanced_content)
                }
            )
            
            print(f"✨ [故事增强] 增强内容长度: {len(enhanced_content)}")
            print(f"✨ [故事增强] 润色内容长度: {len(polished_content)}")
            print(f"✨✨✨ [故事增强] ===== 增强完成 =====")
            
            st.success(f"✅ 故事增强完成！生成了 {len(polished_content or enhanced_content)} 字符的增强版故事")
            
            # 显示增强统计
            with st.expander("📊 增强统计", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("处理时间", f"{end_time - start_time:.1f}秒")
                with col2:
                    st.metric("最终内容长度", f"{len(polished_content or enhanced_content):,}字符")
                with col3:
                    enhancement_features = []
                    if enable_transitions:
                        enhancement_features.append("章节过渡")
                    if enable_polish:
                        enhancement_features.append("对话润色")
                    st.metric("增强功能", " + ".join(enhancement_features) if enhancement_features else "无")
            
            # 自动保存
            if auto_save:
                save_enhancement_to_project("auto_save")
            
            # 保存操作到历史
            save_enhancement_to_history("生成增强版故事完成")
            
    except Exception as e:
        error_msg = f"故事增强失败: {str(e)}"
        print(f"❌ [故事增强] {error_msg}")
        st.error(f"❌ {error_msg}")
        
        # 记录错误日志
        log_backend_operation(
            "故事增强失败", 
            {"error": str(e)},
            time.time(), time.time(), None, e
        )

def compile_enhanced_story_manually():
    """手动编译增强故事（作为后备方案）"""
    try:
        print("📝 [故事增强] 使用手动编译方式...")
        
        # 使用现有的编译功能
        dialogue_data = st.session_state.dialogue_data
        if isinstance(dialogue_data, dict):
            sentence_dialogues = dialogue_data.get("sentence_dialogues", [])
        else:
            sentence_dialogues = dialogue_data
        
        compiled_content = compile_full_story_by_sentence(st.session_state.story_data, sentence_dialogues)
        return compiled_content
        
    except Exception as e:
        print(f"❌ [故事增强] 手动编译失败: {e}")
        return "手动编译失败，请检查数据格式"

def regenerate_enhanced_story(enable_transitions=True, enable_polish=True):
    """重新生成增强版故事"""
    # 清除现有增强数据，强制重新生成
    if st.session_state.get('enhanced_story_data'):
        save_enhancement_to_history("重新生成前")
        st.session_state.enhanced_story_data = {}
    
    generate_enhanced_story(
        enable_transitions=enable_transitions,
        enable_polish=enable_polish,
        use_cache=False,
        auto_save=True
    )

def show_enhancement_display():
    """显示增强版故事内容"""
    if not st.session_state.get('enhanced_story_data'):
        st.info("📝 暂无增强版故事，请先生成")
        return
    
    st.markdown("#### 📋 增强版故事预览")
    
    enhanced_data = st.session_state.enhanced_story_data
    
    # 显示增强信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        params = enhanced_data.get('generation_params', {})
        st.info(f"📅 生成时间: {params.get('timestamp', '未知')[:19].replace('T', ' ')}")
    
    with col2:
        processing_time = enhanced_data.get('generation_params', {}).get('processing_time', 0)
        st.info(f"⏱️ 处理时间: {processing_time:.1f}秒")
    
    with col3:
        final_content = enhanced_data.get('final_content', '')
        st.info(f"📄 内容长度: {len(final_content):,}字符")
    
    # 显示增强功能
    params = enhanced_data.get('generation_params', {})
    enhancement_features = []
    if params.get('enable_transitions'):
        enhancement_features.append("✨ 章节过渡")
    if params.get('enable_polish'):
        enhancement_features.append("🎨 对话润色")
    
    if enhancement_features:
        st.success(f"🎯 已启用功能: {' + '.join(enhancement_features)}")
    
    st.markdown("---")
    
    # 创建显示选项卡
    tab1, tab2, tab3 = st.tabs(["📖 最终版本", "✨ 章节过渡版", "🎨 对话润色版"])
    
    with tab1:
        st.markdown("##### 📖 最终增强版本")
        final_content = enhanced_data.get('final_content', '')
        if final_content:
            st.text_area("最终增强内容", final_content, height=600, key="final_enhanced_content")
            
            # 下载按钮
            if st.download_button(
                "📥 下载最终版本",
                final_content,
                file_name=f"enhanced_story_final_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            ):
                st.success("✅ 文件下载开始")
        else:
            st.info("📝 暂无最终版本内容")
    
    with tab2:
        st.markdown("##### ✨ 章节过渡版本")
        enhanced_content = enhanced_data.get('enhanced_content', '')
        if enhanced_content:
            st.text_area("章节过渡内容", enhanced_content, height=600, key="transition_enhanced_content")
            
            if st.download_button(
                "📥 下载过渡版本",
                enhanced_content,
                file_name=f"enhanced_story_transitions_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            ):
                st.success("✅ 文件下载开始")
        else:
            st.info("📝 暂无章节过渡版本内容")
    
    with tab3:
        st.markdown("##### 🎨 对话润色版本")
        polished_content = enhanced_data.get('polished_content', '')
        if polished_content:
            st.text_area("对话润色内容", polished_content, height=600, key="polished_enhanced_content")
            
            if st.download_button(
                "📥 下载润色版本",
                polished_content,
                file_name=f"enhanced_story_polished_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            ):
                st.success("✅ 文件下载开始")
        else:
            st.info("📝 暂无对话润色版本内容")

def show_enhancement_edit_mode():
    """增强版故事编辑模式"""
    if not st.session_state.get('enhanced_story_data'):
        st.info("📝 暂无增强版故事，请先生成")
        return
    
    st.markdown("#### ✏️ 编辑增强版故事")
    
    # 创建编辑选项卡
    tab1, tab2, tab3 = st.tabs(["🔄 重新生成", "✏️ 手动编辑", "📊 历史记录"])
    
    with tab1:
        show_enhancement_regeneration_options()
    
    with tab2:
        show_enhancement_manual_edit()
    
    with tab3:
        show_enhancement_history_panel()

def show_enhancement_regeneration_options():
    """增强版重新生成选项"""
    st.markdown("##### 🔄 重新生成增强版")
    
    # 重新生成选项
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 重新生成范围**")
        regen_scope = st.radio(
            "选择重新生成范围",
            ["完整重新生成", "仅章节过渡", "仅对话润色"],
            key="enhancement_regen_scope"
        )
    
    with col2:
        st.markdown("**⚙️ 生成参数**")
        enable_transitions = st.checkbox("添加章节过渡", value=True, key="regen_transitions")
        enable_polish = st.checkbox("润色对话", value=True, key="regen_polish")
    
    st.markdown("---")
    
    # 重新生成按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 完整重新生成", type="primary", use_container_width=True):
            regenerate_enhanced_story(enable_transitions, enable_polish)
    
    with col2:
        if st.button("✨ 仅重新生成过渡", use_container_width=True):
            regenerate_enhanced_story(True, False)
    
    with col3:
        if st.button("🎨 仅重新润色对话", use_container_width=True):
            regenerate_enhanced_story(False, True)

def show_enhancement_manual_edit():
    """手动编辑增强版内容"""
    st.markdown("##### ✏️ 手动编辑增强内容")
    
    enhanced_data = st.session_state.enhanced_story_data
    current_content = enhanced_data.get('final_content', '')
    
    # 编辑区域
    edited_content = st.text_area(
        "编辑增强版内容",
        current_content,
        height=500,
        key="manual_edit_enhancement",
        help="在此处手动编辑增强版故事内容"
    )
    
    # 编辑操作按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 保存编辑", type="primary", use_container_width=True):
            save_manual_enhancement_edit(edited_content)
    
    with col2:
        if st.button("🔄 重置内容", use_container_width=True):
            st.session_state['manual_edit_enhancement'] = current_content
            st.rerun()
    
    with col3:
        if st.button("📋 预览变化", use_container_width=True):
            show_enhancement_edit_preview(current_content, edited_content)

def save_manual_enhancement_edit(edited_content):
    """保存手动编辑的增强内容"""
    try:
        # 保存编辑前的状态到历史
        save_enhancement_to_history("手动编辑前")
        
        # 更新增强数据
        st.session_state.enhanced_story_data['final_content'] = edited_content
        st.session_state.enhanced_story_data['manual_edited'] = True
        st.session_state.enhanced_story_data['edit_timestamp'] = datetime.datetime.now().isoformat()
        
        # 保存编辑后的状态到历史
        save_enhancement_to_history("手动编辑完成")
        
        st.success("✅ 增强版内容已保存")
        
        # 记录操作日志
        print(f"✏️ [故事增强] 手动编辑保存完成，内容长度: {len(edited_content)}")
        
    except Exception as e:
        error_msg = f"保存编辑失败: {str(e)}"
        print(f"❌ [故事增强] {error_msg}")
        st.error(f"❌ {error_msg}")

def show_enhancement_edit_preview(original_content, edited_content):
    """显示编辑预览对比"""
    st.markdown("##### 📋 编辑变化预览")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**原始内容**")
        st.text_area("原始", original_content[:1000] + "..." if len(original_content) > 1000 else original_content, height=300, disabled=True)
        st.info(f"原始长度: {len(original_content):,} 字符")
    
    with col2:
        st.markdown("**编辑后内容**")
        st.text_area("编辑后", edited_content[:1000] + "..." if len(edited_content) > 1000 else edited_content, height=300, disabled=True)
        st.info(f"编辑后长度: {len(edited_content):,} 字符")
    
    # 变化统计
    length_change = len(edited_content) - len(original_content)
    if length_change > 0:
        st.success(f"📈 内容增加了 {length_change:,} 字符")
    elif length_change < 0:
        st.warning(f"📉 内容减少了 {abs(length_change):,} 字符")
    else:
        st.info("📊 内容长度未变化")

def show_enhancement_history_panel():
    """显示增强版历史记录面板"""
    st.markdown("##### 📊 增强版历史记录")
    
    if not st.session_state.enhancement_history:
        st.info("📝 暂无历史记录")
        return
    
    # 历史操作控制
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("↩️ 撤销", use_container_width=True):
            undo_enhancement_action()
    
    with col2:
        if st.button("↪️ 重做", use_container_width=True):
            redo_enhancement_action()
    
    with col3:
        current_index = st.session_state.enhancement_history_index
        total_history = len(st.session_state.enhancement_history)
        st.info(f"📍 位置: {current_index + 1}/{total_history}")
    
    st.markdown("---")
    
    # 历史记录列表
    st.markdown("**📋 历史操作记录**")
    
    for i, entry in enumerate(reversed(st.session_state.enhancement_history)):
        actual_index = len(st.session_state.enhancement_history) - 1 - i
        is_current = actual_index == st.session_state.enhancement_history_index
        
        with st.expander(
            f"{'🔸' if is_current else '⚪'} {entry['action']} - {entry['timestamp'][:19].replace('T', ' ')}",
            expanded=is_current
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**操作**: {entry['action']}")
                st.markdown(f"**时间**: {entry['timestamp'][:19].replace('T', ' ')}")
            
            with col2:
                st.markdown(f"**数据大小**: {entry['data_size']:,} 字符")
                if st.button(f"📍 跳转到此版本", key=f"jump_to_{actual_index}"):
                    st.session_state.enhancement_history_index = actual_index
                    if actual_index < len(st.session_state.enhancement_history):
                        history_entry = st.session_state.enhancement_history[actual_index]
                        st.session_state.enhanced_story_data = copy.deepcopy(history_entry["enhancement_data"])
                        st.success(f"✅ 已跳转到: {history_entry['action']}")
                        st.rerun()

def show_enhancement_file_management():
    """增强版文件管理"""
    st.markdown("#### 📁 增强版文件管理")
    
    # 文件操作选项卡
    tab1, tab2, tab3 = st.tabs(["💾 保存文件", "📁 加载文件", "📤 导出文件"])
    
    with tab1:
        save_enhancement_to_project("file_management")
    
    with tab2:
        load_existing_enhancement()
    
    with tab3:
        export_enhancement_files()

def save_enhancement_to_project(context="default"):
    """保存增强版到项目目录"""
    if not st.session_state.get('enhanced_story_data'):
        st.info("📝 暂无增强版数据可保存")
        return
    
    st.markdown("##### 💾 保存增强版到项目")
    
    try:
        # 获取当前版本信息
        current_version = get_current_version()
        if not current_version:
            st.error("❌ 无法确定当前项目版本")
            return
        
        enhanced_data = st.session_state.enhanced_story_data
        
        # 保存选项
        col1, col2 = st.columns(2)
        
        with col1:
            save_final = st.checkbox("保存最终版本", value=True, key=f"save_final_checkbox_{context}")
            save_transitions = st.checkbox("保存章节过渡版", value=False, key=f"save_transitions_checkbox_{context}")
        
        with col2:
            save_polished = st.checkbox("保存对话润色版", value=False, key=f"save_polished_checkbox_{context}")
            save_metadata = st.checkbox("保存元数据", value=True, key=f"save_metadata_checkbox_{context}")
        
        if st.button("💾 执行保存", type="primary", use_container_width=True, key=f"save_execute_btn_{context}"):
            saved_files = []
            
            # 保存最终版本
            if save_final and enhanced_data.get('final_content'):
                final_path = f"data/output/{current_version}/enhanced_story_final.md"
                with open(final_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_data['final_content'])
                saved_files.append("enhanced_story_final.md")
            
            # 保存章节过渡版
            if save_transitions and enhanced_data.get('enhanced_content'):
                transitions_path = f"data/output/{current_version}/enhanced_story_transitions.md"
                with open(transitions_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_data['enhanced_content'])
                saved_files.append("enhanced_story_transitions.md")
            
            # 保存对话润色版
            if save_polished and enhanced_data.get('polished_content'):
                polished_path = f"data/output/{current_version}/enhanced_story_polished.md"
                with open(polished_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_data['polished_content'])
                saved_files.append("enhanced_story_polished.md")
            
            # 保存元数据
            if save_metadata:
                metadata = {
                    "generation_params": enhanced_data.get('generation_params', {}),
                    "manual_edited": enhanced_data.get('manual_edited', False),
                    "edit_timestamp": enhanced_data.get('edit_timestamp'),
                    "save_timestamp": datetime.datetime.now().isoformat(),
                    "content_lengths": {
                        "final": len(enhanced_data.get('final_content', '')),
                        "enhanced": len(enhanced_data.get('enhanced_content', '')),
                        "polished": len(enhanced_data.get('polished_content', ''))
                    }
                }
                metadata_path = f"data/output/{current_version}/enhanced_story_metadata.json"
                save_json(metadata, current_version, "enhanced_story_metadata.json")
                saved_files.append("enhanced_story_metadata.json")
            
            st.success(f"✅ 已保存 {len(saved_files)} 个文件到 data/output/{current_version}/")
            for file in saved_files:
                st.info(f"📄 {file}")
            
            print(f"💾 [故事增强] 保存文件到项目: {saved_files}")
    
    except Exception as e:
        error_msg = f"保存文件失败: {str(e)}"
        print(f"❌ [故事增强] {error_msg}")
        st.error(f"❌ {error_msg}")

def load_existing_enhancement():
    """加载已有的增强版文件"""
    st.markdown("##### 📁 加载已有增强版")
    
    uploaded_file = st.file_uploader(
        "选择增强版文件",
        type=['md', 'json'],
        help="支持 .md 文件（故事内容）或 .json 文件（包含元数据）",
        key="enhancement_file_uploader"
    )
    
    if uploaded_file is not None:
        try:
            # 读取文件内容
            uploaded_file.seek(0)
            
            if uploaded_file.name.endswith('.md'):
                # Markdown 文件
                content = uploaded_file.read().decode('utf-8')
                
                # 保存加载前状态
                save_enhancement_to_history("加载文件前")
                
                # 创建增强数据
                st.session_state.enhanced_story_data = {
                    "final_content": content,
                    "enhanced_content": content,
                    "polished_content": content,
                    "generation_params": {
                        "loaded_from_file": True,
                        "filename": uploaded_file.name,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                }
                
                st.success(f"✅ 已加载增强版文件: {uploaded_file.name}")
                st.info(f"📄 内容长度: {len(content):,} 字符")
                
            elif uploaded_file.name.endswith('.json'):
                # JSON 元数据文件
                import json
                data = json.loads(uploaded_file.read().decode('utf-8'))
                
                if 'final_content' in data or 'enhanced_content' in data:
                    save_enhancement_to_history("加载JSON文件前")
                    st.session_state.enhanced_story_data = data
                    st.success(f"✅ 已加载增强版数据: {uploaded_file.name}")
                else:
                    st.error("❌ JSON 文件格式不正确，缺少必要的内容字段")
            
            # 保存加载后状态
            save_enhancement_to_history("文件加载完成")
            
            print(f"📁 [故事增强] 加载文件成功: {uploaded_file.name}")
            st.rerun()
            
        except Exception as e:
            error_msg = f"加载文件失败: {str(e)}"
            print(f"❌ [故事增强] {error_msg}")
            st.error(f"❌ {error_msg}")

def export_enhancement_files():
    """导出增强版文件"""
    if not st.session_state.get('enhanced_story_data'):
        st.info("📝 暂无增强版数据可导出")
        return
    
    st.markdown("##### 📤 导出增强版文件")
    
    enhanced_data = st.session_state.enhanced_story_data
    
    # 导出选项
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📄 内容导出**")
        
        # 最终版本下载
        if enhanced_data.get('final_content'):
            st.download_button(
                "📥 下载最终版本 (.md)",
                enhanced_data['final_content'],
                file_name=f"enhanced_story_final_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        # 章节过渡版本下载
        if enhanced_data.get('enhanced_content'):
            st.download_button(
                "📥 下载过渡版本 (.md)",
                enhanced_data['enhanced_content'],
                file_name=f"enhanced_story_transitions_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    with col2:
        st.markdown("**📊 数据导出**")
        
        # 完整数据导出
        import json
        complete_data = json.dumps(enhanced_data, ensure_ascii=False, indent=2)
        st.download_button(
            "📥 下载完整数据 (.json)",
            complete_data,
            file_name=f"enhanced_story_complete_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
        
        # 元数据导出
        metadata = {
            "generation_params": enhanced_data.get('generation_params', {}),
            "content_lengths": {
                "final": len(enhanced_data.get('final_content', '')),
                "enhanced": len(enhanced_data.get('enhanced_content', '')),
                "polished": len(enhanced_data.get('polished_content', ''))
            },
            "export_timestamp": datetime.datetime.now().isoformat()
        }
        metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
        st.download_button(
            "📥 下载元数据 (.json)",
            metadata_json,
            file_name=f"enhanced_story_metadata_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
