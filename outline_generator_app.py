import streamlit as st
import os
import json
import tempfile
from typing import List, Dict, Any
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入后端功能
try:
    from src.constant import output_dir
    from src.utils.utils import save_json, load_json
    from src.generation.outline_generator import generate_outline
    from src.generation.chapter_reorder import reorder_chapters
    from src.generation.narrative_analyzer import analyze_narrative_structure
    from src.version_namer import build_version_name
    BACKEND_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ 后端模块导入失败: {e}")
    st.info("将使用模拟模式运行")
    BACKEND_AVAILABLE = False

# 页面配置
st.set_page_config(
    page_title="故事大纲生成器",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 模拟后端功能（当真实后端不可用时）
class MockBackend:
    @staticmethod
    def generate_outline(topic="小红帽", style="科幻改写", custom_instruction=""):
        """模拟大纲生成"""
        mock_chapters = [
            {
                "chapter_id": "Chapter 1",
                "title": f"{topic}的{style}开端",
                "summary": f"在一个充满{style}色彩的世界里，{topic}开始了她的奇异冒险。"
            },
            {
                "chapter_id": "Chapter 2", 
                "title": f"{topic}的{style}挑战",
                "summary": f"{topic}面临着前所未有的{style}挑战，需要运用智慧和勇气。"
            },
            {
                "chapter_id": "Chapter 3",
                "title": f"{topic}的{style}转折",
                "summary": f"故事出现了意想不到的{style}转折，{topic}必须做出重要选择。"
            },
            {
                "chapter_id": "Chapter 4",
                "title": f"{topic}的{style}高潮",
                "summary": f"故事达到{style}高潮，{topic}将面临最终的考验。"
            },
            {
                "chapter_id": "Chapter 5",
                "title": f"{topic}的{style}结局",
                "summary": f"故事迎来{style}结局，{topic}的冒险画上圆满句点。"
            }
        ]
        return mock_chapters
    
    @staticmethod
    def reorder_chapters(chapters, mode="nonlinear"):
        """模拟章节重排"""
        if mode == "linear":
            return chapters
        
        # 简单的非线性重排
        reordered = chapters.copy()
        if len(reordered) >= 3:
            # 交换第2和第4章
            reordered[1], reordered[3] = reordered[3], reordered[1]
            for i, ch in enumerate(reordered):
                ch["new_order"] = i + 1
        return reordered
    
    @staticmethod
    def analyze_narrative_structure(reordered, original, topic, style):
        """模拟叙述分析"""
        for ch in reordered:
            if "new_order" in ch:
                ch["narrative_role"] = "非线性叙述"
                ch["narrative_instruction"] = "需要处理时间线跳跃"
                ch["transition_hint"] = "使用过渡技巧连接"
        return reordered

# 全局状态管理
if 'outline_data' not in st.session_state:
    st.session_state.outline_data = None
if 'current_version' not in st.session_state:
    st.session_state.current_version = "test"
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = "preview"

def main():
    st.title("📚 故事大纲生成器")
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
            load_existing_outline()
        
        st.markdown("---")
        st.markdown("**当前状态:**")
        if st.session_state.outline_data:
            st.success(f"✅ 已加载大纲 ({len(st.session_state.outline_data)} 章)")
        else:
            st.info("📝 未加载大纲")
    
    # 主界面
    if st.session_state.outline_data is None:
        show_welcome_screen()
    else:
        show_outline_editor()

def show_welcome_screen():
    """欢迎界面"""
    st.markdown("""
    ## 🎯 欢迎使用故事大纲生成器！
    
    这个工具可以帮助你：
    - 🚀 快速生成故事大纲
    - ✏️ 交互式编辑章节内容
    - 🔄 重新排列章节顺序
    - 📊 分析叙述结构
    - 💾 保存和导出结果
    
    **开始使用：**
    1. 在左侧配置故事参数
    2. 点击"生成新大纲"按钮
    3. 或者加载已有的大纲文件
    """)
    
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

def generate_new_outline(topic, style, temperature, seed, reorder_mode):
    """生成新大纲"""
    with st.spinner("🔄 正在生成故事大纲..."):
        try:
            if BACKEND_AVAILABLE:
                # 使用真实后端
                outline = generate_outline(topic=topic, style=style, custom_instruction="")
                
                # 构建版本名称
                version = build_version_name(
                    topic=topic,
                    style=style,
                    temperature=temperature,
                    seed=seed,
                    order_mode=reorder_mode
                )
            else:
                # 使用模拟后端
                outline = MockBackend.generate_outline(topic=topic, style=style)
                version = f"{topic}_{style}_T{temperature}_s{seed}_{reorder_mode}"
            
            # 处理章节重排
            if reorder_mode == "nonlinear":
                if BACKEND_AVAILABLE:
                    reordered = reorder_chapters(outline, mode="nonlinear")
                    # 叙述结构分析
                    reordered = analyze_narrative_structure(reordered, outline, topic, style)
                else:
                    reordered = MockBackend.reorder_chapters(outline, mode="nonlinear")
                    reordered = MockBackend.analyze_narrative_structure(reordered, outline, topic, style)
                
                # 合并原始信息
                final_outline = []
                for reordered_ch in reordered:
                    match = next((x for x in outline if x["chapter_id"] == reordered_ch["chapter_id"]), None)
                    if match:
                        merged = {
                            "chapter_id": reordered_ch["chapter_id"],
                            "title": reordered_ch["title"],
                            "summary": match.get("summary", ""),
                            "original_position": outline.index(match) + 1
                        }
                        
                        # 保留重排和叙述分析字段
                        narrative_fields = ["new_order", "narrative_role", "narrative_instruction", "transition_hint"]
                        for field in narrative_fields:
                            if field in reordered_ch:
                                merged[field] = reordered_ch[field]
                        
                        final_outline.append(merged)
                
                outline = final_outline
            
            st.session_state.outline_data = outline
            st.session_state.current_version = version
            
            st.success(f"✅ 大纲生成完成！共 {len(outline)} 章")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 大纲生成失败: {str(e)}")

def load_existing_outline():
    """加载已有大纲"""
    uploaded_file = st.file_uploader("选择大纲文件", type=['json'])
    
    if uploaded_file is not None:
        try:
            outline_data = json.load(uploaded_file)
            if isinstance(outline_data, list) and len(outline_data) > 0:
                st.session_state.outline_data = outline_data
                st.session_state.current_version = "loaded_outline"
                st.success(f"✅ 大纲加载成功！共 {len(outline_data)} 章")
                st.rerun()
            else:
                st.error("❌ 文件格式不正确")
        except Exception as e:
            st.error(f"❌ 文件加载失败: {str(e)}")

def show_outline_editor():
    """大纲编辑器界面"""
    st.header(f"📝 大纲编辑器 - {st.session_state.current_version}")
    
    # 编辑模式选择
    col1, col2, col3, col4 = st.columns(4)
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
    elif st.session_state.edit_mode == "export":
        show_export_mode()

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
                    delete_chapter(chapter_idx)
            
            with col3:
                if st.button("✅ 保存修改", key=f"save_{chapter_idx}"):
                    save_chapter_edit(chapter_idx, new_title, new_chapter_id, new_summary)
            
            st.markdown("---")
    
    # 添加新章节
    st.markdown("### ➕ 添加新章节")
    with st.form("add_chapter_form"):
        new_ch_title = st.text_input("新章节标题")
        new_ch_summary = st.text_area("新章节摘要")
        
        if st.form_submit_button("➕ 添加章节"):
            if new_ch_title and new_ch_summary:
                add_new_chapter(new_ch_title, new_ch_summary)
            else:
                st.warning("请填写章节标题和摘要")

def show_reorder_mode():
    """重排模式"""
    st.subheader("🔄 章节重排")
    
    # 显示当前顺序
    st.markdown("**当前章节顺序:**")
    current_order = []
    for i, chapter in enumerate(st.session_state.outline_data):
        current_order.append(f"{i+1}. {chapter['title']}")
    
    st.markdown(" → ".join(current_order))
    
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
    """重新生成章节"""
    try:
        if BACKEND_AVAILABLE:
            # 使用真实后端重新生成
            new_outline = generate_outline(
                topic="小红帽", 
                style="科幻改写", 
                custom_instruction="重新生成单个章节"
            )
            if len(new_outline) > chapter_idx:
                st.session_state.outline_data[chapter_idx] = new_outline[chapter_idx]
                st.success(f"✅ 第 {chapter_idx + 1} 章重新生成完成")
        else:
            # 模拟重新生成
            st.session_state.outline_data[chapter_idx]['title'] = f"重新生成的第{chapter_idx + 1}章"
            st.session_state.outline_data[chapter_idx]['summary'] = f"这是重新生成的第{chapter_idx + 1}章内容"
            st.success(f"✅ 第 {chapter_idx + 1} 章重新生成完成")
        
        st.rerun()
    except Exception as e:
        st.error(f"❌ 重新生成失败: {str(e)}")

def delete_chapter(chapter_idx):
    """删除章节"""
    if st.button(f"🗑️ 确认删除第 {chapter_idx + 1} 章", key=f"confirm_delete_{chapter_idx}"):
        del st.session_state.outline_data[chapter_idx]
        st.success(f"✅ 第 {chapter_idx + 1} 章已删除")
        st.rerun()

def save_chapter_edit(chapter_idx, new_title, new_chapter_id, new_summary):
    """保存章节编辑"""
    st.session_state.outline_data[chapter_idx]['title'] = new_title
    st.session_state.outline_data[chapter_idx]['chapter_id'] = new_chapter_id
    st.session_state.outline_data[chapter_idx]['summary'] = new_summary
    st.success(f"✅ 第 {chapter_idx + 1} 章修改已保存")

def add_new_chapter(title, summary):
    """添加新章节"""
    new_chapter = {
        "chapter_id": f"Chapter {len(st.session_state.outline_data) + 1}",
        "title": title,
        "summary": summary
    }
    st.session_state.outline_data.append(new_chapter)
    st.success(f"✅ 新章节已添加: {title}")

def perform_automatic_reorder():
    """执行自动重排"""
    try:
        if BACKEND_AVAILABLE:
            reordered = reorder_chapters(st.session_state.outline_data, mode="nonlinear")
            reordered = analyze_narrative_structure(reordered, st.session_state.outline_data, "小红帽", "科幻改写")
        else:
            reordered = MockBackend.reorder_chapters(st.session_state.outline_data, mode="nonlinear")
            reordered = MockBackend.analyze_narrative_structure(reordered, st.session_state.outline_data, "小红帽", "科幻改写")
        
        # 更新大纲数据
        st.session_state.outline_data = reordered
        st.success("✅ 非线性重排完成！")
        st.rerun()
    except Exception as e:
        st.error(f"❌ 自动重排失败: {str(e)}")

def perform_narrative_analysis():
    """执行叙述结构分析"""
    try:
        if BACKEND_AVAILABLE:
            analyzed = analyze_narrative_structure(
                st.session_state.outline_data, 
                st.session_state.outline_data, 
                "小红帽", 
                "科幻改写"
            )
        else:
            analyzed = MockBackend.analyze_narrative_structure(
                st.session_state.outline_data, 
                st.session_state.outline_data, 
                "小红帽", 
                "科幻改写"
            )
        
        st.session_state.outline_data = analyzed
        st.success("✅ 叙述结构分析完成！")
        st.rerun()
    except Exception as e:
        st.error(f"❌ 叙述结构分析失败: {str(e)}")

def apply_manual_reorder(order_input):
    """应用手动重排"""
    try:
        new_order = [int(x.strip()) - 1 for x in order_input.split(',')]
        if len(new_order) != len(st.session_state.outline_data):
            st.error("❌ 顺序数量与章节数量不匹配")
            return
        
        # 重新排列章节
        reordered_outline = [st.session_state.outline_data[i] for i in new_order]
        st.session_state.outline_data = reordered_outline
        
        st.success("✅ 手动重排完成！")
        st.rerun()
    except Exception as e:
        st.error(f"❌ 手动重排失败: {str(e)}")

def save_to_project_directory():
    """保存到项目目录"""
    try:
        if BACKEND_AVAILABLE:
            # 使用真实后端的保存功能
            save_json(st.session_state.outline_data, st.session_state.current_version, "outline.json")
            st.success(f"✅ 大纲已保存到项目目录: {st.session_state.current_version}/outline.json")
        else:
            # 模拟保存
            st.info("💡 模拟模式：大纲已准备就绪，可下载使用")
    except Exception as e:
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

if __name__ == "__main__":
    main()
