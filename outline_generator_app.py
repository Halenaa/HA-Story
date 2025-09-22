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

# Add project root directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Must import real backend functionality, error if failed
print("🔄 Starting to import real backend modules...")

# Basic module imports
try:
    print("  📁 Importing basic configuration module...")
    from src.constant import output_dir
    print("    src.constant.output_dir imported successfully")
    
    print("  Importing utility functions...")
    from src.utils.utils import save_json, load_json
    print("    src.utils.utils.save_json imported successfully")
    print("    src.utils.utils.load_json imported successfully")
    
    print("  📝 Importing version naming module...")
    from src.version_namer import build_version_name
    print("    src.version_namer.build_version_name imported successfully")
    
    print("  Importing logger module...")
    from src.utils.logger import init_log_path, append_log, build_simple_log
    print("    src.utils.logger.init_log_path imported successfully")
    print("    src.utils.logger.append_log imported successfully")
    print("    src.utils.logger.build_simple_log imported successfully")
    
except ImportError as e:
    st.error(f"❌ Basic module import failed: {e}")
    st.stop()

# Outline generation related module imports
try:
    print("  📚 Importing outline generation module...")
    from src.generation.outline_generator import generate_outline
    print("     src.generation.outline_generator.generate_outline imported successfully")
    
    print("  🔄 Importing chapter reorder module...")
    from src.generation.chapter_reorder import reorder_chapters
    print("     src.generation.chapter_reorder.reorder_chapters imported successfully")
    
    print("   Importing narrative analysis module...")
    from src.generation.narrative_analyzer import analyze_narrative_structure
    print("     src.generation.narrative_analyzer.analyze_narrative_structure imported successfully")
    
except ImportError as e:
    st.error(f"❌ Outline related module import failed: {e}")
    st.stop()

# Character generation related module imports (optional feature)
try:
    print("  👥 Importing character generation module...")
    from src.generation.generate_characters import generate_characters_v1
    print("     src.generation.generate_characters.generate_characters_v1 imported successfully")
    
    print("  📖 Importing story expansion module...")
    from src.generation.expand_story import expand_story_v1
    print("     src.generation.expand_story.expand_story_v1 imported successfully")
    
    character_generation_available = True
    
except ImportError as e:
    print(f"⚠️ Character generation related module import failed: {e}")
    print("⚠️ Character generation function will be unavailable, but will not affect outline generation function")
    character_generation_available = False

# Dialogue generation related module imports (optional feature)
try:
    print("  💬 Importing dialogue generation module...")
    from src.generation.dialogue_inserter import analyze_dialogue_insertions_v2, run_dialogue_insertion
    print("     src.generation.dialogue_inserter.analyze_dialogue_insertions_v2 imported successfully")
    print("     src.generation.dialogue_inserter.run_dialogue_insertion imported successfully")
    
    print("  🔄 Importing dialogue synchronization module...")
    from src.sync.plot_sync_manager import sync_plot_and_dialogue_from_behavior
    print("     src.sync.plot_sync_manager.sync_plot_and_dialogue_from_behavior imported successfully")
    
    print("  📝 Importing story compilation module...")
    from src.compile_story import compile_full_story_by_sentence
    print("     src.compile_story.compile_full_story_by_sentence imported successfully")
    
    dialogue_generation_available = True
    
except ImportError as e:
    print(f"⚠️ Dialogue generation related module import failed: {e}")
    print("⚠️ Dialogue generation function will be unavailable, but will not affect other functions")
    dialogue_generation_available = False

# Story enhancement related module imports (optional feature)
try:
    print("  ✨ Importing story enhancement module...")
    from src.enhance_story import enhance_story_with_transitions, polish_dialogues_in_story
    print("     src.enhance_story.enhance_story_with_transitions imported successfully")
    print("     src.enhance_story.polish_dialogues_in_story imported successfully")
    
    print("  📝 Importing story compilation module...")
    # compile_story has already been imported in dialogue generation, no need to import again here
    print("     src.compile_story already imported in dialogue generation module")
    
    story_enhancement_available = True
    
except ImportError as e:
    print(f"⚠️ Story enhancement related module import failed: {e}")
    print("⚠️ Story enhancement function will be unavailable, but will not affect other functions")
    story_enhancement_available = False



print("✅ All real backend modules imported successfully!")

# Setup logging
@st.cache_resource
def setup_logger():
    """Setup application logger"""
    logger = logging.getLogger('outline_app')
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create log directory
    log_dir = "streamlit_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # File handler
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"outline_app_{datetime.datetime.now().strftime('%Y%m%d')}.log"),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Initialize logger
app_logger = setup_logger()

# Page configuration
st.set_page_config(
    page_title="HA-Story",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Log display component
def show_execution_log(log_entries):
    """Show execution log"""
    if log_entries:
        with st.expander("📋 Execution Log", expanded=True):
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
    """Log backend operation"""
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
    
    # Log to application log
    app_logger.info(f"Backend operation: {operation_name} | Duration: {duration:.3f}s | Success: {error is None}")
    
    # Add to session state log list
    if 'execution_logs' not in st.session_state:
        st.session_state.execution_logs = []
    
    st.session_state.execution_logs.append({
        'timestamp': datetime.datetime.now().strftime('%H:%M:%S'),
        'level': 'ERROR' if error else 'SUCCESS',
        'message': f"{operation_name} {'failed' if error else 'succeeded'} (duration: {duration:.3f}s)"
    })
    
    return log_entry

def get_result_summary(result):
    """Get result summary"""
    if isinstance(result, list):
        return f"Returned list with {len(result)} items"
    elif isinstance(result, dict):
        return f"Returned dictionary with {len(result)} fields"
    elif isinstance(result, str):
        return f"Returned string with length {len(result)}"
    else:
        return f"Returned {type(result).__name__} type"

def get_current_version():
    """Get current project version name"""
    try:
        # Try to get current version from session state
        if hasattr(st.session_state, 'current_version') and st.session_state.current_version:
            return st.session_state.current_version
        
        # Try to infer version from outline data
        if st.session_state.get('outline_data'):
            # Generate a version name based on current time
            import time
            timestamp = int(time.time())
            return f"story_enhance_{timestamp}"
        
        # Default version name
        return "default_version"
        
    except Exception as e:
        print(f"⚠️ [Version] Failed to get current version: {e}")
        return "default_version"

def get_current_topic_and_style():
    """Dynamically get current topic and style"""
    try:
        # Check if there are saved parameters
        if hasattr(st.session_state, 'current_topic') and hasattr(st.session_state, 'current_style'):
            topic = st.session_state.current_topic
            style = st.session_state.current_style
            
            # If it's custom description mode, need to adjust based on actual situation
            if hasattr(st.session_state, 'current_generation_mode') and st.session_state.current_generation_mode == "description_based":
                # For custom description mode, can infer from user description or use general description
                if hasattr(st.session_state, 'current_user_description') and st.session_state.current_user_description:
                    user_desc = st.session_state.current_user_description
                    # Simple inference: if description contains specific keywords, use more specific description
                    if "sci-fi" in user_desc.lower() or "science fiction" in user_desc.lower() or "sci-fi" in user_desc:
                        style = "Science Fiction Story"
                    elif "romance" in user_desc.lower() or "love" in user_desc.lower() or "romance" in user_desc:
                        style = "Romance Story"  
                    elif "mystery" in user_desc.lower() or "suspense" in user_desc.lower() or "mystery" in user_desc:
                        style = "Mystery Story"
                    elif "history" in user_desc.lower() or "historical" in user_desc.lower() or "history" in user_desc:
                        style = "Historical Story"
                    elif "fantasy" in user_desc.lower() or "magic" in user_desc.lower() or "fantasy" in user_desc:
                        style = "Fantasy Story"
                    elif "workplace" in user_desc.lower() or "office" in user_desc.lower() or "workplace" in user_desc:
                        style = "Workplace Story"
                    else:
                        style = "Custom Story"
                    
                    # Topic can be extracted from description key information
                    topic = "User Custom Topic"
            
            return topic, style
        
        # If no saved parameters, return default values
        return "Unknown Topic", "Unknown Style"
    except Exception as e:
        print(f"⚠️ [Topic/Style] Failed to get: {e}")
        # Return default values on error
        return "Unknown Topic", "Unknown Style"

# History management functionality
def save_to_history(action_name, old_data=None):
    """Save current state to history"""
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
    
    # If not at the end of history, delete records after current position
    if st.session_state.history_index < len(st.session_state.outline_history) - 1:
        st.session_state.outline_history = st.session_state.outline_history[:st.session_state.history_index + 1]
    
    # Add new record
    st.session_state.outline_history.append(history_entry)
    st.session_state.history_index = len(st.session_state.outline_history) - 1
    
    # Limit history records (maximum 20 states)
    if len(st.session_state.outline_history) > 20:
        st.session_state.outline_history = st.session_state.outline_history[-20:]
        st.session_state.history_index = len(st.session_state.outline_history) - 1
    
    app_logger.info(f"Saved to history: {action_name} at {timestamp}")

def save_characters_to_history(action_name, old_characters_data=None):
    """Save character state to history"""
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
    
    # If not at the end of history, delete records after current position
    if st.session_state.characters_history_index < len(st.session_state.characters_history) - 1:
        st.session_state.characters_history = st.session_state.characters_history[:st.session_state.characters_history_index + 1]
    
    # Add new record
    st.session_state.characters_history.append(history_entry)
    st.session_state.characters_history_index = len(st.session_state.characters_history) - 1
    
    # Limit history records (maximum 20 states)
    if len(st.session_state.characters_history) > 20:
        st.session_state.characters_history = st.session_state.characters_history[-20:]
        st.session_state.characters_history_index = len(st.session_state.characters_history) - 1
    
    app_logger.info(f"Saved characters to history: {action_name} at {timestamp}")

def undo_characters_action():
    """Undo previous character action"""
    if st.session_state.characters_history_index > 0:
        st.session_state.characters_history_index -= 1
        previous_state = st.session_state.characters_history[st.session_state.characters_history_index]
        st.session_state.characters_data = copy.deepcopy(previous_state['characters_data'])
        st.session_state.character_chapter_mapping = copy.deepcopy(previous_state['character_chapter_mapping'])
        st.success(f"✓ Character action undone: {previous_state['action']}")
        return True
    else:
        st.warning("⚠️ No character actions to undo")
        return False

def redo_characters_action():
    """Redo next character action"""
    if st.session_state.characters_history_index < len(st.session_state.characters_history) - 1:
        st.session_state.characters_history_index += 1
        next_state = st.session_state.characters_history[st.session_state.characters_history_index]
        st.session_state.characters_data = copy.deepcopy(next_state['characters_data'])
        st.session_state.character_chapter_mapping = copy.deepcopy(next_state['character_chapter_mapping'])
        st.success(f"✓ Character action redone: {next_state['action']}")
        return True
    else:
        st.warning("⚠️ No character actions to redo")
        return False

def save_story_to_history(action_name, old_story_data=None):
    """Save story state to history"""
    if st.session_state.story_data is None:
        return
    
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    
    history_entry = {
        'timestamp': timestamp,
        'action': action_name,
        'story_data': copy.deepcopy(st.session_state.story_data),
        'old_story_data': copy.deepcopy(old_story_data) if old_story_data else None
    }
    
    # If not at the end of history, delete records after current position
    if st.session_state.story_history_index < len(st.session_state.story_history) - 1:
        st.session_state.story_history = st.session_state.story_history[:st.session_state.story_history_index + 1]
    
    # Add new record
    st.session_state.story_history.append(history_entry)
    st.session_state.story_history_index = len(st.session_state.story_history) - 1
    
    # Limit history records (maximum 20 states)
    if len(st.session_state.story_history) > 20:
        st.session_state.story_history = st.session_state.story_history[-20:]
        st.session_state.story_history_index = len(st.session_state.story_history) - 1
    
    app_logger.info(f"Saved story to history: {action_name} at {timestamp}")

def undo_story_action():
    """Undo previous story action"""
    if st.session_state.story_history_index > 0:
        st.session_state.story_history_index -= 1
        previous_state = st.session_state.story_history[st.session_state.story_history_index]
        st.session_state.story_data = copy.deepcopy(previous_state['story_data'])
        st.success(f"✓ Story action undone: {previous_state['action']}")
        return True
    else:
        st.warning("⚠️ No story actions to undo")
        return False

def redo_story_action():
    """Redo next story action"""
    if st.session_state.story_history_index < len(st.session_state.story_history) - 1:
        st.session_state.story_history_index += 1
        next_state = st.session_state.story_history[st.session_state.story_history_index]
        st.session_state.story_data = copy.deepcopy(next_state['story_data'])
        st.success(f"✓ Story action redone: {next_state['action']}")
        return True
    else:
        st.warning("⚠️ No story actions to redo")
        return False

def undo_last_action():
    """Undo previous action"""
    if st.session_state.history_index > 0:
        st.session_state.history_index -= 1
        previous_state = st.session_state.outline_history[st.session_state.history_index]
        st.session_state.outline_data = copy.deepcopy(previous_state['data'])
        st.session_state.current_version = previous_state['version']
        st.success(f"✓ Action undone: {previous_state['action']}")
        return True
    else:
        st.warning("⚠️ No actions to undo")
        return False

def redo_last_action():
    """Redo next action"""
    if st.session_state.history_index < len(st.session_state.outline_history) - 1:
        st.session_state.history_index += 1
        next_state = st.session_state.outline_history[st.session_state.history_index]
        st.session_state.outline_data = copy.deepcopy(next_state['data'])
        st.session_state.current_version = next_state['version']
        st.success(f"✓ Action redone: {next_state['action']}")
        return True
    else:
        st.warning("⚠️ No actions to redo")
        return False

def show_history_panel():
    """Show history panel"""
    if not st.session_state.outline_history:
        st.info("📝 No history records")
        return
    
    st.subheader("📋 Operation History")
    
    # Undo/Redo buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("↶ Undo", use_container_width=True, disabled=st.session_state.history_index <= 0):
            if undo_last_action():
                st.rerun()
    
    with col2:
        if st.button("↷ Redo", use_container_width=True, disabled=st.session_state.history_index >= len(st.session_state.outline_history) - 1):
            if redo_last_action():
                st.rerun()
    
    with col3:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.outline_history = []
            st.session_state.history_index = -1
            st.success("✓ History records cleared")
            st.rerun()
    
    st.markdown("---")
    
    # Show history records list
    st.markdown("**History Records:**")
    
    for i, entry in enumerate(reversed(st.session_state.outline_history)):
        real_index = len(st.session_state.outline_history) - 1 - i
        is_current = real_index == st.session_state.history_index
        
        # Create history record entry
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                status = "" if is_current else ""
                st.markdown(f"{status} `{entry['timestamp']}`")
            
            with col2:
                st.markdown(f"**{entry['action']}**")
                chapter_count = len(entry['data']) if entry['data'] else 0
                st.caption(f"Total {chapter_count} chapters")
            
            with col3:
                if st.button("📍", key=f"goto_{real_index}", help="Jump to this state"):
                    st.session_state.history_index = real_index
                    st.session_state.outline_data = copy.deepcopy(entry['data'])
                    st.session_state.current_version = entry['version']
                    st.success(f"✓ Jumped to: {entry['action']}")
                    st.rerun()
        
        if i < len(st.session_state.outline_history) - 1:
            st.markdown("---")

# Global state management
if 'outline_data' not in st.session_state:
    st.session_state.outline_data = None
if 'current_version' not in st.session_state:
    st.session_state.current_version = "test"
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = "preview"
# History system
if 'outline_history' not in st.session_state:
    st.session_state.outline_history = []
if 'history_index' not in st.session_state:
    st.session_state.history_index = -1

# Character generation system (integrated in outline generator)
if 'characters_data' not in st.session_state:
    st.session_state.characters_data = []

# Character history system
if 'characters_history' not in st.session_state:
    st.session_state.characters_history = []
if 'characters_history_index' not in st.session_state:
    st.session_state.characters_history_index = -1

# Character-chapter association data
if 'character_chapter_mapping' not in st.session_state:
    st.session_state.character_chapter_mapping = {}  # {chapter_id: [character_names]}

# Story generation system
if 'story_data' not in st.session_state:
    st.session_state.story_data = []

# Story history system
if 'story_history' not in st.session_state:
    st.session_state.story_history = []
if 'story_history_index' not in st.session_state:
    st.session_state.story_history_index = -1

# Dialogue generation system
if 'dialogue_data' not in st.session_state:
    st.session_state.dialogue_data = []

# Dialogue history system
if 'dialogue_history' not in st.session_state:
    st.session_state.dialogue_history = []
if 'dialogue_history_index' not in st.session_state:
    st.session_state.dialogue_history_index = -1

# Story enhancement system
if 'enhanced_story_data' not in st.session_state:
    st.session_state.enhanced_story_data = {}

# Story enhancement history system
if 'enhancement_history' not in st.session_state:
    st.session_state.enhancement_history = []
if 'enhancement_history_index' not in st.session_state:
    st.session_state.enhancement_history_index = -1



def main():
    st.title("📚 HA-Story")
    
    # Show creation process steps
    show_creation_progress()
    
    st.markdown("---")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration Parameters")
        
        # Generation mode selection
        generation_mode = st.radio(
            "📝 Generation Mode", 
            ["Traditional Mode", "Custom Description Mode"],
            help="Traditional Mode: Generate based on topic and style; Custom Description Mode: Generate based on user description and optional file"
        )
        
        st.markdown("---")
        
        if generation_mode == "Traditional Mode":
            # Traditional mode parameters
            topic = st.text_input("Story Topic", value="Little Red Riding Hood", help="Main topic of the story")
            style = st.text_input("Story Style", value="Science Fiction Rewrite", help="Style type of the story")
            user_description = None
            file_content = None
            
        else:
            # Custom description mode parameters
            # Usage instructions
            with st.expander("📚 Usage Instructions"):
                st.markdown("""
                **Custom Description Mode supports the following creation methods:**
                
                🆕 **Original Stories**:
                - "I want to write a sci-fi story about time travel..."
                - "Create a modern urban romantic comedy..."
                
                ➡️ **Story Continuation**:
                - "Please continue this story..." + upload original story file
                - "Continue creating subsequent plots based on existing content..."
                
                🔄 **Story Adaptation**:
                - "Rewrite this classic fairy tale as a modern sci-fi story..." + upload original story
                - "Change this story to a mystery style..."
                
                💭 **Inspired Creation**:
                - "Inspired by this story, create a new story..." + upload reference file
                - "Borrow the setting of this story to create different plots..."
                """)
            
            user_description = st.text_area(
                "📖 Story Description", 
                placeholder="Please describe the story you want to create, for example:\n- I want to write a sci-fi story about...\n- Please continue this story...\n- Please rewrite this story as...\n- Inspired by this story, create a new story...",
                height=100,
                help="Detailed description of the story content, style, or creative intent you want"
            )
            
            # File upload
            uploaded_file = st.file_uploader(
                "📎 Upload Reference File (Optional)",
                type=['txt', 'md'],
                help="Upload text file as reference, can be existing story, outline, or other related content"
            )
            
            # Process file content
            file_content = None
            if uploaded_file is not None:
                try:
                    file_content = str(uploaded_file.read(), "utf-8")
                    st.success(f"✓ File uploaded: {uploaded_file.name} ({len(file_content)} characters)")
                    
                    # Show file preview
                    with st.expander("📖 File Preview"):
                        st.text_area(
                            "File Content Preview",
                            value=file_content[:500] + ("..." if len(file_content) > 500 else ""),
                            height=100,
                            disabled=True
                        )
                except Exception as e:
                    st.error(f"❌ File reading failed: {e}")
                    file_content = None
            
            # Traditional parameters keep default values (for version naming, etc.)
            topic = "Custom Story"
            style = "User Description"
        
        # General parameters
        temperature = st.slider("Creativity", min_value=0.1, max_value=1.0, value=0.7, step=0.1)
        seed = st.number_input("Random Seed", min_value=1, value=42, step=1)
        reorder_mode = st.selectbox("Chapter Order", ["linear", "nonlinear"], help="linear=linear order, nonlinear=non-linear reorder")
        
        st.markdown("---")
        
        # Generate button - call different functions based on mode
        if generation_mode == "Traditional Mode":
            if st.button("🔄 Generate New Outline", type="primary", use_container_width=True):
                generate_new_outline(topic, style, temperature, seed, reorder_mode, "traditional")
        else:
            # Validate custom mode input
            can_generate = bool(user_description and user_description.strip())
            if not can_generate:
                st.warning("⚠️ Please fill in story description")
            
            if st.button(
                "✨ Generate Custom Outline", 
                type="primary", 
                use_container_width=True,
                disabled=not can_generate
            ):
                generate_new_outline(topic, style, temperature, seed, reorder_mode, "description_based", user_description, file_content)
        
        if st.button("📁 Load Existing Outline", use_container_width=True):
            st.session_state.show_outline_loader = True
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Current Status:**")
        if st.session_state.outline_data:
            st.success(f"✓ Outline loaded ({len(st.session_state.outline_data)} chapters)")
        else:
            st.info("📝 No outline loaded")
        
        if st.session_state.characters_data:
            st.success(f"✓ Characters generated ({len(st.session_state.characters_data)} characters)")
        else:
            st.info("👥 No characters generated")
        
        # Performance analysis
        st.markdown("---")
        st.markdown("###  📈 Performance Analysis")
        
        if st.button("📈 View Performance Report", use_container_width=True):
            st.session_state.show_performance_analysis = True
            st.rerun()
        
        # Show performance analysis file statistics
        try:
            import os
            # Check performance report files in output directory
            output_dir = "data/output"
            if os.path.exists(output_dir):
                performance_files = []
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if file.startswith("performance_analysis_") and file.endswith(".json"):
                            performance_files.append(file)
                st.info(f"📈 Generated {len(performance_files)} performance reports")
            else:
                st.info("📈 No performance reports")
        except:
            pass

        # Suggestion management
        st.markdown("---")
        st.markdown("###  🧠 Smart Suggestions")
        
        if st.button("📂 Manage Saved Suggestions", use_container_width=True):
            st.session_state.show_suggestions_manager = True
            st.rerun()
        
        # Show suggestion statistics
        try:
            import os
            suggestions_dir = "data/saved_suggestions"
            if os.path.exists(suggestions_dir):
                suggestion_files = [f for f in os.listdir(suggestions_dir) if f.endswith('.json')]
                st.info(f"📁 Saved {len(suggestion_files)} suggestions")
            else:
                st.info("📁 No saved suggestions")
        except:
            pass
    
    # Show execution log
    if 'execution_logs' in st.session_state and st.session_state.execution_logs:
        show_execution_log(st.session_state.execution_logs)
    
    # Check special interface display
    if st.session_state.get('show_performance_analysis', False):
        show_performance_analysis_interface()
        return
    
    if st.session_state.get('show_suggestions_manager', False):
        show_suggestions_manager()
        return
    
    # Main interface - display corresponding interface based on current step
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
    """Show creation process progress"""
    st.markdown("###  🎨 Creation Workflow")
    
    # Determine current step status
    outline_status = "" if st.session_state.outline_data else ""
    character_status = "" if st.session_state.characters_data else ("" if st.session_state.outline_data else "")
    story_status = ""  # Future expansion
    
    # Create workflow indicator - expanded to 5 steps
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 0.3, 1.5, 0.3, 1.5, 0.3, 1.5, 0.3, 1.5])
    
    with col1:
        outline_color = "success" if outline_status == "" else ("warning" if outline_status == "" else "secondary")
        if st.button(f"{outline_status} **Step 1: Outline Generation**", type="secondary" if outline_status != "" else "primary", use_container_width=True):
            st.session_state.current_interface = "outline"
            st.rerun()
    
    with col2:
        st.markdown("<div style='text-align: center; padding-top: 8px;'>→</div>", unsafe_allow_html=True)
    
    with col3:
        character_disabled = not st.session_state.outline_data
        character_type = "secondary" if character_status == "" else ("primary" if character_status == "" else "secondary")
        if st.button(f"{character_status} **Step 2: Character Generation**", type=character_type, disabled=character_disabled, use_container_width=True):
            st.session_state.current_interface = "characters"
            st.rerun()
    
    with col4:
        st.markdown("<div style='text-align: center; padding-top: 8px;'>→</div>", unsafe_allow_html=True)
    
    with col5:
        story_disabled = not (st.session_state.outline_data and st.session_state.characters_data)
        story_status = "" if st.session_state.get('story_data') else ("" if (st.session_state.outline_data and st.session_state.characters_data) else "")
        story_type = "secondary" if story_status == "" else ("primary" if story_status == "" else "secondary")
        if st.button(f"{story_status} **Step 3: Story Generation**", type=story_type, disabled=story_disabled, use_container_width=True):
            st.session_state.current_interface = "story"
            st.rerun()
    
    with col6:
        st.markdown("<div style='text-align: center; padding-top: 8px;'>→</div>", unsafe_allow_html=True)
    
    with col7:
        dialogue_disabled = not (st.session_state.outline_data and st.session_state.characters_data and st.session_state.get('story_data'))
        dialogue_status = "" if st.session_state.get('dialogue_data') else ("" if (st.session_state.outline_data and st.session_state.characters_data and st.session_state.get('story_data')) else "")
        dialogue_type = "secondary" if dialogue_status == "" else ("primary" if dialogue_status == "" else "secondary")
        if st.button(f"{dialogue_status} **Step 4: Dialogue Generation**", type=dialogue_type, disabled=dialogue_disabled, use_container_width=True):
            st.session_state.current_interface = "dialogue"
            st.rerun()
    
    with col8:
        st.markdown("<div style='text-align: center; padding-top: 8px;'>→</div>", unsafe_allow_html=True)
    
    with col9:
        enhance_disabled = not (st.session_state.outline_data and st.session_state.characters_data and st.session_state.get('story_data') and st.session_state.get('dialogue_data'))
        enhance_status = "" if st.session_state.get('enhanced_story_data') else ("" if (st.session_state.outline_data and st.session_state.characters_data and st.session_state.get('story_data') and st.session_state.get('dialogue_data')) else "")
        enhance_type = "secondary" if enhance_status == "" else ("primary" if enhance_status == "" else "secondary")
        if st.button(f"{enhance_status} **Step 5: Story Enhancement**", type=enhance_type, disabled=enhance_disabled, use_container_width=True):
            st.session_state.current_interface = "enhance"
            st.rerun()
    
    # Show current step description
    current_step = determine_current_step()
    if current_step == "welcome":
        st.info("✨ **Start Creating**: Please configure parameters first and generate story outline")
    elif current_step == "outline":
        st.info("📝 **Outline Stage**: Edit and refine your story outline")
    elif current_step == "characters":
        st.info("👥 **Character Stage**: Generate and manage characters based on outline")
    elif current_step == "story":
        st.info("📖 **Story Stage**: Generate detailed story content based on outline and characters")
    elif current_step == "dialogue":
        st.info("💬 **Dialogue Stage**: Generate character dialogue based on story content")
    elif current_step == "enhance":
        st.info("✨ **Enhancement Stage**: Add chapter transitions and polish dialogue to generate complete novel")

def determine_current_step():
    """Determine current step to display"""
    # Check if user manually selected interface
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
    
    # Automatically determine current step
    if not st.session_state.outline_data:
        return "welcome"
    elif not st.session_state.characters_data:
        return "characters"  # After outline completion, automatically enter character generation stage
    elif not st.session_state.get('story_data'):
        return "story"  # After character completion, automatically enter story generation stage
    elif not st.session_state.get('dialogue_data'):
        return "dialogue"  # After story completion, automatically enter dialogue generation stage
    elif not st.session_state.get('enhanced_story_data'):
        return "enhance"  # After dialogue completion, automatically enter story enhancement stage
    else:
        return "enhance"  # Default display story enhancement interface

def show_character_generation_interface():
    """Show character generation interface - as main process step"""
    st.header("👥 Step 2: Character Generation")
    
    # Check prerequisites
    if not st.session_state.outline_data:
        st.error("❌ Please complete Step 1 first: Generate Story Outline")
        return
    
    # Check if character generation functionality is available
    if not character_generation_available:
        st.error("❌ Character generation function unavailable, please check backend module import")
        return
    
    # Show outline-based character generation interface
    show_character_generation_mode()

def show_welcome_screen():
    """Welcome screen"""
    # Check if file loader needs to be displayed
    if st.session_state.get('show_outline_loader', False):
        load_existing_outline()
        return
    
    st.markdown("""
    ##  Welcome to HA-Story Creation System！
    
    This is a complete story creation tool designed according to backend workflow, including the following main steps:
    """)
    
    # Show Complete Creation Workflow
    st.markdown("###  Complete Creation Workflow")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📚 Step 1: Outline Generation**
        -  Quickly generate story outline
        -  Interactive editing of chapter content
        - 🔄 Reorder chapter sequence
        -  Analyze narrative structure
        -  Save and export results
        """)
    
    with col2:
        st.markdown("""
        **👥 Step 2: Character Generation**
        -  Generate characters based on outline
        - 📝 Manage character settings
        - 🔗 Analyze character-chapter associations
        -  Save character data
        -  Edit character information
        """)
    
    with col3:
        st.markdown("""
        **📖 Step 3: Story Generation**
        - 📄 Expand detailed story content based on outline
        -  Chapter summary and logical coherence check
        -  Select key chapters for rewriting
        -  Style consistency confirmation and adjustment
        -  Save and export complete story
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ** Getting Started：**
    1. Configure story parameters on the left (topic, style, etc.)
    2. Click "Generate New Outline" button to start creating
    3. Or click "Load Existing Outline" button to upload existing file
    4. After completing the outline，the system will automatically guide you to the character generation step
    """)
    
    # Quick Start buttons
    st.markdown("###  Quick Start")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 Load Existing Outline File", type="secondary", use_container_width=True):
            st.session_state.show_outline_loader = True
            st.rerun()
    
    with col2:
        if st.button(" View Example Format", use_container_width=True):
            st.session_state.show_example_formats = True
            st.rerun()
    
    # Show example formats
    if st.session_state.get('show_example_formats', False):
        st.markdown("---")
        show_example_formats()
    
    # Example outline preview
    with st.expander("📖 View Example Outline"):
        example_outline = [
            {"chapter_id": "Chapter 1", "title": "Little Red Riding Hood's Sci-Fi Beginning", "summary": "In a world full of sci-fi colors, Little Red Riding Hood begins her extraordinary adventure."},
            {"chapter_id": "Chapter 2", "title": "Little Red Riding Hood's Sci-Fi Challenge", "summary": "Little Red Riding Hood faces unprecedented sci-fi challenges, requiring wisdom and courage."},
            {"chapter_id": "Chapter 3", "title": "Little Red Riding Hood's Sci-Fi Turning Point", "summary": "The story takes an unexpected sci-fi turn, and Little Red Riding Hood must make an important choice."}
        ]
        
        for i, ch in enumerate(example_outline):
            st.markdown(f"**{ch['chapter_id']}: {ch['title']}**")
            st.markdown(f"*{ch['summary']}*")
            if i < len(example_outline) - 1:
                st.markdown("---")
    
    # System features
    with st.expander("✨ System Features"):
        st.markdown("""
        ** Complete Creation Workflow：**
        - 📚 **Intelligent Outline Generation**：Automatically generate structured outlines based on theme and style
        - 🔄 **Chapter Reorder Optimization**：Support linear and non-linear chapter sequences
        - 👥 **Intelligent Character Generation**：Automatically generate character settings that fit the story based on outline
        -  **Comprehensive Editing Features**：Support manual editing and regeneration of outlines and characters
        -  **History Management**：Complete undo/redo/rollback functionality
        -  **Data Persistence**：Automatic save to project directory, support multiple format export
        """)
        
        st.info(" All features are based on real backend modules, ensuring generation quality and data consistency")

def show_example_formats():
    """Show example file formats"""
    st.markdown("### 📄 File Format Examples")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📚 Outline File Format (JSON):**")
        outline_example = [
            {
                "chapter_id": "Chapter 1",
                "title": "Chapter Title",
                "summary": "Chapter summary content"
            },
            {
                "chapter_id": "Chapter 2", 
                "title": "Second Chapter Title",
                "summary": "Second chapter summary content"
            }
        ]
        st.code(json.dumps(outline_example, ensure_ascii=False, indent=2), language="json")
    
    with col2:
        st.markdown("**👥 Character File Format (JSON):**")
        character_example = [
            {
                "name": "Character Name",
                "role": "Character Role",
                "traits": "Character Trait Description",
                "background": "Character Background Story",
                "motivation": "Character Motivation"
            }
        ]
        st.code(json.dumps(character_example, ensure_ascii=False, indent=2), language="json")
    
    if st.button(" Close Examples", key="close_examples"):
        st.session_state.show_example_formats = False
        st.rerun()

def generate_new_outline(topic, style, temperature, seed, reorder_mode, generation_mode="traditional", user_description=None, file_content=None):
    """Generate new outline - supports traditional mode and custom description mode"""
    
    # Clear previous logs
    if 'execution_logs' not in st.session_state:
        st.session_state.execution_logs = []
    else:
        st.session_state.execution_logs.clear()
    
    spinner_text = "🔄 Generating story outline..." if generation_mode == "traditional" else " Generating outline based on your description..."
    
    with st.spinner(spinner_text):
        try:
            # Step 1: Build version name (according to main_pipeline_glm.py logic)
            start_time = time.time()
            
            if generation_mode == "traditional":
                version = build_version_name(
                    topic=topic,
                    style=style,
                    temperature=temperature,
                    seed=seed,
                    order_mode=reorder_mode
                )
            else:  # description_based mode
                import hashlib
                import datetime
                # Generate short identifier based on user description
                desc_hash = hashlib.md5(user_description.encode('utf-8')).hexdigest()[:8] if user_description else "nodesc"
                timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
                version = f"custom_{desc_hash}_{reorder_mode}_T{temperature}_s{seed}_{timestamp}"
            
            end_time = time.time()
            
            log_backend_operation(
                "Build version name", 
                {
                    "generation_mode": generation_mode,
                    "topic": topic, 
                    "style": style, 
                    "temperature": temperature, 
                    "seed": seed, 
                    "order_mode": reorder_mode,
                    "user_description": user_description[:50] + "..." if user_description and len(user_description) > 50 else user_description,
                    "has_file": bool(file_content)
                },
                start_time, end_time, version
            )
            
            st.info(f"📝 Generated version name: {version}")
            
            # Step 2: Outline Generation - call different generation logic based on mode
            start_time = time.time()
            
            if generation_mode == "traditional":
                # Traditional mode: using shared cache
                outline_base_path = os.path.join(output_dir, "reference_outline", f"{topic}_{style}_T{temperature}_s{seed}_outline.json")
                os.makedirs(os.path.dirname(outline_base_path), exist_ok=True)
                
                if os.path.exists(outline_base_path):
                    outline = load_json(outline_base_path)
                    end_time = time.time()
                    log_backend_operation(
                        "Load shared outline", 
                        {"path": outline_base_path},
                        start_time, end_time, outline
                    )
                    st.info(f"📖 Loaded shared outline: {outline_base_path}")
                else:
                    outline = generate_outline(
                        topic=topic, 
                        style=style, 
                        custom_instruction="",
                        generation_mode="traditional"
                    )
                    end_time = time.time()
                    log_backend_operation(
                        "Generate new outline", 
                        {"topic": topic, "style": style, "custom_instruction": "", "generation_mode": "traditional"},
                        start_time, end_time, outline
                    )
                    
                    # Save outline
                    save_start = time.time()
                    save_json(outline, "reference_outline", f"{topic}_{style}_T{temperature}_s{seed}_outline.json")
                    save_end = time.time()
                    log_backend_operation(
                        "Save outline to shared directory", 
                        {"path": outline_base_path},
                        save_start, save_end, True
                    )
                    st.success(f" Generated and saved shared outline: {outline_base_path}")
            
            else:
                # Custom description mode: not using shared cache
                outline = generate_outline(
                    topic=topic,  # This is "Custom Story"
                    style=style,  # This is "User Description"
                    custom_instruction="",
                    generation_mode="description_based",
                    user_description=user_description,
                    file_content=file_content
                )
                end_time = time.time()
                log_backend_operation(
                    "Generate custom outline", 
                    {
                        "generation_mode": "description_based",
                        "user_description": user_description[:100] + "..." if user_description and len(user_description) > 100 else user_description,
                        "file_content_length": len(file_content) if file_content else 0
                    },
                    start_time, end_time, outline
                )
                st.success(f"✓ Custom outline generation based on your description completed")
            
            st.info(f"📝 Outline generation completed, total {len(outline)} chapters")
            
            # Step 3: Chapter reorder processing (according to main_pipeline_glm.py lines 92-185 logic)
            reorder_outline_raw = None
            
            if reorder_mode == "linear":
                reorder_outline_raw = outline
                st.info("📝 Using linear order (directly from outline)")
                
            elif reorder_mode == "nonlinear":
                st.info("🔄 Starting non-linear reorder processing...")
                
                # Save linear version
                save_start = time.time()
                save_json(outline, version, "test_outline_linear.json")
                save_end = time.time()
                log_backend_operation(
                    "Save linear outline", 
                    {"version": version},
                    save_start, save_end, True
                )
                
                # Check cached non-linear version
                reorder_path = os.path.join(output_dir, "reference_reorder", f"{topic}_{style}_T{temperature}_s{seed}_nonlinear.json")
                os.makedirs(os.path.dirname(reorder_path), exist_ok=True)
                
                start_time = time.time()
                if os.path.exists(reorder_path):
                    reorder_outline_raw = load_json(reorder_path)
                    end_time = time.time()
                    log_backend_operation(
                        "Load cached non-linear order", 
                        {"path": reorder_path},
                        start_time, end_time, reorder_outline_raw
                    )
                    st.success(f"✓ Loaded cached non-linear order: {reorder_path}")
                else:
                    # Step 3.1: Chapter reorder
                    st.info("🔄 Execute chapter reorder...")
                    reorder_outline_raw = reorder_chapters(outline, mode="nonlinear")
                    end_time = time.time()
                    log_backend_operation(
                        "Execute chapter reorder", 
                        {"mode": "nonlinear", "original_chapters": len(outline)},
                        start_time, end_time, reorder_outline_raw
                    )
                    
                    # Check if reorder was successful (according to main_pipeline_glm.py lines 122-141)
                    if not any("new_order" in ch for ch in reorder_outline_raw):
                        st.warning("⚠️ LLM reorder failed: No new_order field detected, falling back to original order")
                        reorder_mode = "linear"
                        reorder_outline_raw = outline
                        log_backend_operation(
                            "Reorder failed fallback", 
                            {"reason": "No new_order field"},
                            time.time(), time.time(), reorder_outline_raw
                        )
                    else:
                        st.success(" reorder_chapters successfully generated non-linear order")
                        
                        # Step 3.2: Narrative structure analysis
                        st.info("🔍 Starting narrative structure analysis...")
                        analysis_start = time.time()
                        reorder_outline_raw = analyze_narrative_structure(
                            reorder_outline_raw, outline, topic=topic, style=style
                        )
                        analysis_end = time.time()
                        log_backend_operation(
                            "Narrative structure analysis", 
                            {"topic": topic, "style": style},
                            analysis_start, analysis_end, reorder_outline_raw
                        )
                        
                        # Show analysis results
                        st.info("📖 Narrative structure analysis results:")
                        for ch in reorder_outline_raw:
                            role = ch.get('narrative_role', 'Not analyzed')
                            st.text(f"  {ch['chapter_id']}: {role}")
                    
                    # Save non-linear version
                    save_start = time.time()
                    save_json(reorder_outline_raw, "reference_reorder", f"{topic}_{style}_T{temperature}_s{seed}_nonlinear.json")
                    save_end = time.time()
                    log_backend_operation(
                        "Save non-linear order to cache", 
                        {"path": reorder_path},
                        save_start, save_end, True
                    )
                    st.success(f" Generated non-linear order and cached: {reorder_path}")
            
            # Step 4: Unified structure processing (according to main_pipeline_glm.py lines 155-185)
            st.info("🔧 Unified structure: supplement summary field, retain narrative analysis fields...")
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
                    
                    # Retain reorder and narrative analysis related fields
                    narrative_fields = ["new_order", "narrative_role", "narrative_instruction", "transition_hint"]
                    for field in narrative_fields:
                        if field in reordered_ch:
                            merged[field] = reordered_ch[field]
                    
                    # Add original position information
                    merged["original_position"] = outline.index(match) + 1
                    
                    final_outline.append(merged)
            
            merge_end = time.time()
            log_backend_operation(
                "Merge structure data", 
                {"original_chapters": len(outline), "final_chapters": len(final_outline)},
                merge_start, merge_end, final_outline
            )
            
            # Save final results
            save_start = time.time()
            save_json(final_outline, version, "test_reorder_outline.json")
            save_end = time.time()
            log_backend_operation(
                "Save final outline", 
                {"version": version, "filename": "test_reorder_outline.json"},
                save_start, save_end, True
            )
            
            # Show final structure
            if reorder_mode == "nonlinear":
                st.success(" Chapter order processing completed (retained summary and narrative guidance)")
                st.info(" Final chapter structure:")
                for idx, ch in enumerate(final_outline):
                    role = ch.get('narrative_role', 'Linear narrative')
                    orig_pos = ch.get('original_position', '?')
                    st.text(f"  {idx+1}. {ch['chapter_id']} (Originally chapter {orig_pos}) - {role}")
            else:
                st.success(" Chapter order processing completed (retained summary)")
            
            # Update session state
            st.session_state.outline_data = final_outline
            st.session_state.current_version = version
            # Save current parameters for subsequent chapter regeneration
            st.session_state.current_topic = topic
            st.session_state.current_style = style
            st.session_state.current_temperature = temperature
            st.session_state.current_seed = seed
            st.session_state.current_reorder_mode = reorder_mode
            st.session_state.current_generation_mode = generation_mode
            # Save additional parameters for custom description mode
            if generation_mode == "description_based":
                st.session_state.current_user_description = user_description
                st.session_state.current_file_content = file_content
            
            # Save initial state to history
            save_to_history("Generate outline")
            
            st.success(f"✓ Outline generation completed! Total {len(final_outline)} chapters")
            st.rerun()
            
        except Exception as e:
            error_time = time.time()
            log_backend_operation(
                "Outline generation failed", 
                {"topic": topic, "style": style, "reorder_mode": reorder_mode},
                error_time, error_time, None, e
            )
            st.error(f"❌ Outline generation failed: {str(e)}")
            app_logger.error(f"Outline generation failed: {str(e)}")

def load_existing_outline():
    """Load existing outline"""
    st.markdown("### 📁 Load Existing Outline")
    
    # Add session state to prevent duplicate uploader after successful upload
    if st.session_state.get('outline_file_uploaded', False):
        st.success("✅ Outline file uploaded successfully! The page will refresh automatically.")
        # Reset flag after display
        st.session_state.outline_file_uploaded = False
        return
    
    uploaded_file = st.file_uploader("Select Outline File", type=['json'], key="outline_upload")
    
    if uploaded_file is not None:
        try:
            # Show file information
            st.info(f"📄 File name: {uploaded_file.name}")
            st.info(f" File size: {uploaded_file.size} bytes")
            
            # Reset file pointer to beginning
            uploaded_file.seek(0)
            
            # Read file content
            file_content = uploaded_file.read()
            
            # If bytes type, convert to string
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # Parse JSON
            outline_data = json.loads(file_content)
            
            # Detailed validation of data format
            if not isinstance(outline_data, list):
                st.error("❌ Incorrect file format: should be JSON array format")
                return
            
            if len(outline_data) == 0:
                st.error("❌ File content is empty: no chapter data found")
                return
            
            # Validate chapter data format
            required_fields = ['chapter_id', 'title']
            for i, chapter in enumerate(outline_data):
                if not isinstance(chapter, dict):
                    st.error(f"❌ Chapter {i+1} format incorrect: should be object format")
                    return
                
                missing_fields = [field for field in required_fields if field not in chapter]
                if missing_fields:
                    st.error(f"❌ Chapter {i+1} missing required fields: {', '.join(missing_fields)}")
                    return
            
            # Save state before loading to history (if exists)
            if st.session_state.outline_data:
                save_to_history("State before loading new outline", st.session_state.outline_data.copy())
            
            # Load data
            st.session_state.outline_data = outline_data
            st.session_state.current_version = f"loaded_{uploaded_file.name.replace('.json', '')}"
            
            # Save state after loading to history
            save_to_history("Load outline")
            
            st.success(f"✓ Outline loaded successfully! Total {len(outline_data)} chapters")
            st.info("🔄 Page will refresh automatically...")
            
            # Show Loaded Chapter Preview
            with st.expander("📖 Loaded Chapter Preview", expanded=True):
                for i, chapter in enumerate(outline_data[:3]):  # Only show first 3 chapters
                    st.text(f"{i+1}. {chapter.get('chapter_id', 'Unknown')}: {chapter.get('title', 'No Title')}")
                if len(outline_data) > 3:
                    st.text(f"... More {len(outline_data) - 3} chapters")
            
            # Clear loader state
            st.session_state.show_outline_loader = False
            
            # Set flag to prevent duplicate uploader
            st.session_state.outline_file_uploaded = True
            st.rerun()
            
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON format error: {str(e)}")
            st.error("❌ Please ensure the file is in valid JSON format")
        except UnicodeDecodeError as e:
            st.error(f"❌ File encoding error: {str(e)}")
            st.error("❌ Please ensure the file is UTF-8 encoded")
        except Exception as e:
            st.error(f"❌ File loading failed: {str(e)}")
            print(f"⚠️ [Outline Loading] Loading failed: {str(e)}")
    else:
        st.info(" Please select a JSON format outline file")

def show_outline_editor():
    """Outline editor interface"""
    st.header(f"📝 Step 1: Outline Editing - {st.session_state.current_version}")
    
    # Editing mode selection
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("👀 Preview Mode", use_container_width=True):
            st.session_state.edit_mode = "preview"
            st.rerun()
    
    with col2:
        if st.button("📝 Edit Mode", use_container_width=True):
            st.session_state.edit_mode = "edit"
            st.rerun()
    
    with col3:
        if st.button("🔄 Reorder Mode", use_container_width=True):
            st.session_state.edit_mode = "reorder"
            st.rerun()
    
    with col4:
        if st.button("📜 History", use_container_width=True):
            st.session_state.edit_mode = "history"
            st.rerun()
    
    with col5:
        if st.button("💾 Save & Export", use_container_width=True):
            st.session_state.edit_mode = "export"
            st.rerun()
    
    st.markdown("---")
    
    # Show different interfaces based on mode
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
    
    # Show next step prompt at the bottom of Outline Editor
    st.markdown("---")
    st.markdown("### ✓ Outline Editing Complete")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("📝 After completing outline editing, you can proceed to the next step: Character Generation")
    
    with col2:
        if st.button("👥 Enter Character Generation", type="primary", use_container_width=True):
            st.session_state.current_interface = "characters"
            st.rerun()

def show_preview_mode():
    """Preview mode"""
    st.subheader("👀 Outline Preview")
    
    # Show chapter information
    for i, chapter in enumerate(st.session_state.outline_data):
        with st.expander(f"**{chapter['chapter_id']}: {chapter['title']}**", expanded=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Summary:** {chapter.get('summary', 'No summary')}")
                
                # Show additional information
                if 'original_position' in chapter:
                    st.info(f"📍 Original position: Chapter {chapter['original_position']}")
                
                if 'narrative_role' in chapter:
                    st.success(f"🎭 Narrative role: {chapter['narrative_role']}")
                
                if 'narrative_instruction' in chapter:
                    st.warning(f"⚠️ Narrative guidance: {chapter['narrative_instruction']}")
                
                if 'transition_hint' in chapter:
                    st.info(f"🔗 Transition hint: {chapter['transition_hint']}")
            
            with col2:
                st.markdown(f"**Position:** {i+1}")
                if 'new_order' in chapter:
                    st.markdown(f"**New order:** {chapter['new_order']}")

def show_edit_mode():
    """Edit mode"""
    st.subheader("📝 Chapter Editing")
    
    # Batch selection
    st.markdown("**Select chapters to edit:**")
    selected_chapters = st.multiselect(
        "Select chapters",
        options=[f"{i+1}. {ch['title']}" for i, ch in enumerate(st.session_state.outline_data)],
        default=[]
    )
    
    if selected_chapters:
        st.markdown("---")
        
        # Edit selected chapters
        for selection in selected_chapters:
            chapter_idx = int(selection.split('.')[0]) - 1
            chapter = st.session_state.outline_data[chapter_idx]
            
            st.markdown(f"### 📝 Edit Chapter {chapter_idx + 1}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_title = st.text_input(
                    "Chapter Title",
                    value=chapter['title'],
                    key=f"title_{chapter_idx}"
                )
            
            with col2:
                new_chapter_id = st.text_input(
                    "Chapter ID",
                    value=chapter['chapter_id'],
                    key=f"id_{chapter_idx}"
                )
            
            new_summary = st.text_area(
                "Chapter Summary",
                value=chapter.get('summary', ''),
                height=100,
                key=f"summary_{chapter_idx}"
            )
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Regenerate", key=f"regenerate_{chapter_idx}"):
                    regenerate_chapter(chapter_idx, chapter)
            
            with col2:
                if st.button("🗑️ Delete Chapter", key=f"delete_{chapter_idx}"):
                    # Save state before deletion to history
                    save_to_history(f"Delete chapter {chapter_idx + 1}", st.session_state.outline_data.copy())
                    # Execute deletion
                    deleted_chapter = st.session_state.outline_data.pop(chapter_idx)
                    st.success(f"✓ Deleted chapter {chapter_idx + 1}: {deleted_chapter.get('title', 'Unknown title')}")
                    st.rerun()
            
            with col3:
                if st.button("💾 Save Changes", key=f"save_{chapter_idx}"):
                    save_chapter_edit(chapter_idx, new_title, new_chapter_id, new_summary)
            
            st.markdown("---")
    
    # Add new chapter
    st.markdown("### ➕ Add New Chapter")
    with st.form("add_chapter_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            new_ch_title = st.text_input("New Chapter Title")
        
        with col2:
            # Insert position selection
            insert_positions = ["At End"] + [f"Before Chapter {i+1}" for i in range(len(st.session_state.outline_data))]
            insert_position = st.selectbox("Insert Position", insert_positions)
        
        new_ch_summary = st.text_area("New Chapter Summary", height=100)
        
        # Conflict detection options
        enable_conflict_check = st.checkbox("🔍 Enable Content Conflict Detection", value=True, help="Detect if new chapters have logical conflicts with existing outline")
        
        if st.form_submit_button("➕ Add Chapter"):
            if new_ch_title and new_ch_summary:
                # Determine insert position
                if insert_position == "At End":
                    insert_idx = len(st.session_state.outline_data)
                else:
                    insert_idx = int(insert_position.split("Chapter ")[1].split("")[0]) - 1
                
                add_new_chapter(new_ch_title, new_ch_summary, insert_idx, enable_conflict_check)
            else:
                st.warning("⚠️ Please fill in chapter title and summary")

def show_reorder_mode():
    """Reorder mode"""
    st.subheader("🔄 Chapter Reorder")
    
    # Show detailed order comparison
    show_chapter_order_comparison()
    
    st.markdown("---")
    
    # Reorder options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Automatic Reorder:**")
        if st.button("🔄 Non-linear Reorder", use_container_width=True):
            perform_automatic_reorder()
        
        if st.button(" Narrative structure analysis", use_container_width=True):
            perform_narrative_analysis()
    
    with col2:
        st.markdown("**Manual Reorder:**")
        st.markdown("Enter new chapter order (comma-separated):")
        new_order_input = st.text_input(
            "New Order",
            value=",".join(str(i+1) for i in range(len(st.session_state.outline_data))),
            help="For example: 1,3,2,4,5"
        )
        
        if st.button("✓ Apply New Order", use_container_width=True):
            apply_manual_reorder(new_order_input)

def show_character_generation_mode():
    """Character generation mode - as independent step"""
    st.subheader("👥 Character Generation & Management")
    
    # Check if character file loader needs to be shown
    if st.session_state.get('show_character_loader', False):
        load_existing_characters()
        return
    
    # Check if outline data exists
    if not st.session_state.outline_data:
        st.warning("⚠️ Please generate story outline first, then generate characters")
        return
    
    # Check if character generation functionality is available
    if not character_generation_available:
        st.error("❌ Character generation function unavailable, please check backend module import")
        return
    
    # Character generation configuration
    st.markdown("### Character Generation Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        max_characters = st.slider("Maximum Number of Characters", min_value=3, max_value=20, value=8, help="Upper limit for the number of generated characters")
        use_cache = st.checkbox("Use Cache", value=True, help="If character data already exists, load it directly", key="char_use_cache_checkbox")
    
    with col2:
        show_details = st.checkbox("Show Details", value=True, help="Show complete character information", key="char_show_details_checkbox")
        auto_save = st.checkbox("Auto Save", value=True, help="Automatically save to history after generation", key="char_auto_save_checkbox")
    
    st.markdown("---")
    
    # Character generation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✨ Generate Characters", type="primary", use_container_width=True):
            generate_characters_from_outline(max_characters, use_cache, auto_save)
    
    with col2:
        if st.button("🔄 Regenerate", use_container_width=True):
            generate_characters_from_outline(max_characters, use_cache=False, auto_save=auto_save)
    
    with col3:
        if st.button("📁 Load Characters", use_container_width=True):
            st.session_state.show_character_loader = True
            st.rerun()
    
    st.markdown("---")
    
    # Show character data
    if st.session_state.characters_data:
        show_characters_display(show_details)
    else:
        st.info("📝 No character data available. Please click 'Generate Characters' button to start generation")
        
        # Debug information
        st.info(f"🔍 Debug: Current character data state - {type(st.session_state.get('characters_data', None))}, length: {len(st.session_state.get('characters_data', []))}")
        
        # Prompt user to start character generation
        st.info("🎯 Click 'Generate Characters' button above to start generating characters based on outline")

def generate_characters_from_outline(max_characters=8, use_cache=True, auto_save=True):
    """Generate characters from outline - integrated version"""
    try:
        # Check cache
        if use_cache and st.session_state.characters_data:
            st.success("✓ Using cached character data")
            return
        
        with st.spinner("✨ Generating characters..."):
            # Record start time
            start_time = time.time()
            
            # Display backend call information in terminal
            print(f"📝 [Outline Generator Integration] Calling backend module: src.generation.generate_characters.generate_characters_v1")
            print(f"📝 [Outline Generator Integration] Input parameters: outline_chapters={len(st.session_state.outline_data)}, max_characters={max_characters}")
            
            # Call real backend function
            characters = generate_characters_v1(st.session_state.outline_data, max_characters=max_characters)
            
            # Record end time
            end_time = time.time()
            
            # Display results in terminal
            print(f"⏱️ [Outline Generator Integration] Generation time: {end_time - start_time:.3f}s")
            print(f"✓ [Outline Generator Integration] Character generation completed! Total generated {len(characters) if characters else 0} characters")
            
            # Validate generation results
            if not characters or not isinstance(characters, list):
                st.error("❌ Character generation failed: incorrect backend returned data format")
                print(f"⚠️ [Outline Generator Integration] Backend returned data format error: {type(characters)} - {str(characters)[:200]}...")
                return
            
            # Save to session state
            st.session_state.characters_data = characters
            
            # Display character list in terminal
            character_names = [char.get('name', 'Unknown Character') for char in characters]
            print(f"👥 [Outline Generator Integration] Generated characters: {', '.join(character_names)}")
            
            # Automatically save to history
            if auto_save:
                save_characters_to_history("Generate characters")
            
            # Automatically link characters to outline chapters
            print("🔗 [Character Management] Character generation completed, starting automatic link to outline chapters")
            auto_relink_characters_to_outline()
            
            # Show success message
            st.success(f"✓ Character generation completed! Total generated {len(characters)} characters")
            st.info(f"⏱️ Generation time: {end_time - start_time:.3f}s")
            
            # Show character list
            st.info(f"👥 Generated characters: {', '.join(character_names)}")
            
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Character generation failed: {str(e)}")
        print(f"⚠️ [Outline Generator Integration] Character generation failed: {str(e)}")

def load_existing_characters():
    """Load existing character file - integrated version"""
    st.markdown("### 📁 Load Existing Characters")
    
    # Add session state to prevent duplicate uploader after successful upload
    if st.session_state.get('character_file_uploaded', False):
        st.success("✅ Character file uploaded successfully! The page will refresh automatically.")
        # Reset flag after display
        st.session_state.character_file_uploaded = False
        return
    
    # Add return button
    if st.button("← Return to Character Management"):
        st.session_state.show_character_loader = False
        st.rerun()
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Select Character File", type=['json'], key="character_upload")
    
    if uploaded_file is not None:
        try:
            # Show file information
            st.info(f"📄 File name: {uploaded_file.name}")
            st.info(f" File size: {uploaded_file.size} bytes")
            
            # Reset file pointer to beginning
            uploaded_file.seek(0)
            
            # Read file content
            file_content = uploaded_file.read()
            
            # If bytes type, convert to string
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # Parse JSON
            characters_data = json.loads(file_content)
            
            # Detailed validation of data format
            if not isinstance(characters_data, list):
                st.error("❌ Incorrect file format: should be JSON array format")
                return
            
            if len(characters_data) == 0:
                st.error("⚠️ File content is empty: no character data found")
                return
            
            # Validate character data format
            required_fields = ['name', 'role', 'traits', 'background', 'motivation']
            for i, character in enumerate(characters_data):
                if not isinstance(character, dict):
                    st.error(f"⚠️ Character {i+1} format error: should be object format")
                    return
                
                missing_fields = [field for field in required_fields if field not in character]
                if missing_fields:
                    st.error(f"⚠️ Character {i+1} missing required fields: {', '.join(missing_fields)}")
                    return
            
            # Save state before loading to history (if exists)
            if st.session_state.characters_data:
                save_characters_to_history("State before loading new characters", st.session_state.characters_data.copy())
            
            # Load data
            st.session_state.characters_data = characters_data
            
            # Save state after loading to history
            save_characters_to_history("Load characters")
            
            st.success(f"✓ Character data loaded successfully! Total {len(characters_data)} characters")
            st.info("🔄 Page will refresh automatically...")
            
            # Show loaded character preview
            with st.expander("👥 Loaded Character Preview", expanded=True):
                for i, character in enumerate(characters_data[:3]):  # Only show first 3 characters
                    name = character.get('name', 'Unknown Character')
                    role = character.get('role', 'Unknown Role')
                    st.text(f"{i+1}. {name} - {role}")
                if len(characters_data) > 3:
                    st.text(f"... More {len(characters_data) - 3} characters")
            
            # Automatically re-link to outline
            if st.session_state.outline_data:
                auto_relink_characters_to_outline()
                st.info("🔗 Automatically re-linked characters to outline chapters")
            
            print(f"📁 [Character Management] Load character file: {len(characters_data)} characters")
            
            # Clear loader state
            st.session_state.show_character_loader = False
            
            # Set flag to prevent duplicate uploader
            st.session_state.character_file_uploaded = True
            st.rerun()
            
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON format error: {str(e)}")
            st.error("❌ Please ensure the file is in valid JSON format")
        except UnicodeDecodeError as e:
            st.error(f"❌ File encoding error: {str(e)}")
            st.error("❌ Please ensure the file is UTF-8 encoded")
        except Exception as e:
            st.error(f"❌ File loading failed: {str(e)}")
            print(f"⚠️ [Character Management] Load failed: {str(e)}")
    else:
        st.info("📝 Please select a JSON format character file")

def show_characters_display(show_details=True):
    """Show character information - integrated version"""
    # Check if entering edit mode
    if st.session_state.get('character_edit_mode', False):
        show_character_edit_mode()
        return
    
    # Check if showing consistency check interface
    if st.session_state.get('show_consistency_check', False):
        show_character_consistency_check()
        return
    
    # Check if showing relationship network interface
    if st.session_state.get('show_character_relationships', False):
        show_character_relationships()
        return
    
    st.markdown("### Character List")
    
    characters = st.session_state.characters_data
    
    # Character statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Characters", len(characters))
    with col2:
        roles = [char.get('role', 'Unknown') for char in characters]
        unique_roles = len(set(roles))
        st.metric("Character Types", unique_roles)
    with col3:
        avg_traits_length = sum(len(char.get('traits', '')) for char in characters) // len(characters) if characters else 0
        st.metric("Average Traits Length", f"{avg_traits_length} chars")
    
    st.markdown("---")
    
    # Character detailed information
    for i, character in enumerate(characters):
        with st.expander(f"**{character.get('name', f'Character {i+1}')}** - {character.get('role', 'Unknown Role')}", expanded=False):
            
            if show_details:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**👤 Name:** {character.get('name', 'Unknown')}")
                    st.markdown(f"**🎭 Role:** {character.get('role', 'Unknown')}")
                    st.markdown(f"**🎯 Motivation:** {character.get('motivation', 'Unknown')}")
                
                with col2:
                    st.markdown(f"**✨ Traits:**")
                    st.markdown(f"*{character.get('traits', 'No description')}*")
                    
                    st.markdown(f"**📚 Background:**")
                    st.markdown(f"*{character.get('background', 'No background')}*")
            else:
                # Simplified display
                st.markdown(f"**Role:** {character.get('role', 'Unknown')} | **Traits:** {character.get('traits', 'None')[:50]}...")
    
    # Character management operations
    st.markdown("---")
    st.markdown("### 🛠️ Character Management")
    
    # First row buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("💾 Save Characters", use_container_width=True):
            save_characters_to_project()
    
    with col2:
        if st.button("📝 Edit Characters", use_container_width=True):
            st.session_state.character_edit_mode = True
            st.rerun()
    
    with col3:
        if st.button("🔗 Link Outline", use_container_width=True):
            link_characters_to_outline()
    
    with col4:
        if st.button("📜 Character History", use_container_width=True):
            st.session_state.show_character_history = True
            st.rerun()
    
    with col5:
        if st.button("🗑️ Clear Characters", use_container_width=True):
            if st.button("✓ Confirm Clear", key="confirm_clear_characters"):
                save_characters_to_history("Clear characters", st.session_state.characters_data.copy())
                st.session_state.characters_data = []
                st.session_state.character_chapter_mapping = {}
                st.success("✓ Character data cleared")
                print("✓ [Character Management] Clear character data")
                st.rerun()
    
    # Second row buttons - new features
    st.markdown("### 🔍 Character Analysis")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✓ Consistency Check", use_container_width=True, help="Check consistency between character settings and story outline"):
            st.session_state.show_consistency_check = True
            st.rerun()
    
    with col2:
        if st.button("🕸️ Relationship Network", use_container_width=True, help="Analyze and display relationships between characters"):
            st.session_state.show_character_relationships = True
            st.rerun()
    
    with col3:
        # Reserved space for future expansion
        st.empty()
    
    # Show character history panel
    if st.session_state.get('show_character_history', False):
        show_character_history_panel()

def save_characters_to_project():
    """Save characters to project directory - integrated version"""
    try:
        if not st.session_state.characters_data:
            st.warning("⚠️ No character data to save")
            return
        
        start_time = time.time()
        # Use real backend save function
        save_json(st.session_state.characters_data, st.session_state.current_version, "characters.json")
        end_time = time.time()
        
        st.success(f"✓ Characters saved to project directory: {st.session_state.current_version}/characters.json")
        print(f"💾 [Outline Generator Integration] Save characters to project: {st.session_state.current_version}/characters.json ({len(st.session_state.characters_data)} characters)")
        
    except Exception as e:
        st.error(f"⚠️ Save failed: {str(e)}")
        print(f"⚠️ [Outline Generator Integration] Save characters failed: {str(e)}")

def auto_relink_characters_to_outline():
    """Auto re-link characters to outline chapters - using backend intelligent analysis"""
    if not st.session_state.characters_data or not st.session_state.outline_data:
        print("⚠️ [Character Link] Missing character or outline data, skip auto-link")
        return False
    
    print("🔗 [Character Management] Start intelligent analysis of character-chapter links")
    
    # First try intelligent analysis
    try:
        # Use backend intelligent analysis capability
        from src.utils.utils import generate_response, convert_json
        
        # Build analysis request
        characters_info = []
        for char in st.session_state.characters_data:
            char_info = f"Character: {char.get('name', 'Unknown')} - {char.get('role', 'Unknown Role')}"
            if char.get('traits'):
                char_info += f", Traits: {char.get('traits')}"
            characters_info.append(char_info)
        
        chapters_info = []
        for chapter in st.session_state.outline_data:
            chapter_info = f"{chapter['chapter_id']}: {chapter['title']}"
            if chapter.get('summary'):
                chapter_info += f" - {chapter['summary']}"
            chapters_info.append(chapter_info)
        
        # Build intelligent analysis prompt
        analysis_prompt = f"""
You are a story analysis expert. Please analyze the appearance of the following characters in various chapters.

Character List:
{chr(10).join(characters_info)}

Chapter List:
{chr(10).join(chapters_info)}

Please analyze which chapters each character is most likely to appear in, based on:
1. Character positioning and traits
2. Chapter content and plot development
3. Logical structure of the story

Return in JSON format as follows:
{{
    "Chapter 1": ["Character1", "Character2"],
    "Chapter 2": ["Character1"],
    ...
}}

Return only JSON, no other explanations.
"""
        
        # Call backend analysis
        start_time = time.time()
        print(f"📝 [Character Link] Calling backend intelligent analysis...")
        
        msg = [{"role": "user", "content": analysis_prompt}]
        response = generate_response(msg)
        analysis_result = convert_json(response)
        
        end_time = time.time()
        print(f"⏱️ [Character Link] Intelligent analysis time: {end_time - start_time:.3f}s")
        
        if not analysis_result or not isinstance(analysis_result, dict):
            print("⚠️ [Character Link] Intelligent analysis result format incorrect, using simple matching")
            return simple_character_matching()
        
        # Update association mapping
        st.session_state.character_chapter_mapping = {}
        total_links = 0
        
        for chapter_id, character_names in analysis_result.items():
            if isinstance(character_names, list):
                # Verify if character name exists
                valid_characters = []
                all_char_names = [char.get('name', '') for char in st.session_state.characters_data]
                
                for char_name in character_names:
                    if char_name in all_char_names:
                        valid_characters.append(char_name)
                
                st.session_state.character_chapter_mapping[chapter_id] = valid_characters
                total_links += len(valid_characters)
        
        print(f"✓ [Character Link] Intelligent analysis completed: {total_links} links")
        return True
        
    except Exception as e:
        print(f"⚠️ [Character Link] Intelligent analysis failed: {str(e)}")
        print("🔄 [Character Link] Fallback to simple matching solution")
        return simple_character_matching()

def simple_character_matching():
    """Simple string matching as backup solution"""
    print("🔄 [Character Link] Using simple matching fallback solution")
    
    # Reset association mapping
    st.session_state.character_chapter_mapping = {}
    
    # Get all character names
    character_names = [char.get('name', '') for char in st.session_state.characters_data]
    total_links = 0
    
    # Analyze relevant characters for each chapter
    for chapter in st.session_state.outline_data:
        chapter_id = chapter['chapter_id']
        chapter_text = f"{chapter['title']} {chapter.get('summary', '')}".lower()
        
        related_characters = []
        for char_name in character_names:
            if char_name.lower() in chapter_text:
                related_characters.append(char_name)
        
        st.session_state.character_chapter_mapping[chapter_id] = related_characters
        total_links += len(related_characters)
    
    print(f"✓ [Character Link] Simple matching completed: {total_links} links")
    return True

def link_characters_to_outline():
    """Link characters to outline chapters - manual management version"""
    st.markdown("### 🔗 Character-Chapter Link Management")
    
    if not st.session_state.characters_data:
        st.warning("⚠️ Please generate characters first")
        return
    
    if not st.session_state.outline_data:
        st.warning("⚠️ Please generate outline first")
        return
    
    # Debug information
    current_mapping = st.session_state.get('character_chapter_mapping', {})
    total_current_links = sum(len(chars) for chars in current_mapping.values())
    st.info(f"🔍 Debug info: Currently have {len(st.session_state.characters_data)} characters, {len(st.session_state.outline_data)} chapters, {total_current_links} links")
    
    # Auto analysis button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Smart Analyze Associations", use_container_width=True):
            with st.spinner("🔍 Performing intelligent analysis..."):
                try:
                    success = auto_relink_characters_to_outline()
                    
                    # Count association results
                    total_links = sum(len(chars) for chars in st.session_state.character_chapter_mapping.values())
                    
                    if success and total_links > 0:
                        st.success(f"✓ Smart analysis completed! Total established {total_links} character-chapter associations")
                        
                        # Show analysis results preview
                        with st.expander("👀 View Analysis Results", expanded=True):
                            for chapter_id, characters in st.session_state.character_chapter_mapping.items():
                                if characters:
                                    chapter_title = next((ch['title'] for ch in st.session_state.outline_data if ch['chapter_id'] == chapter_id), chapter_id)
                                    st.info(f"**{chapter_title}**: {', '.join(characters)}")
                    elif success and total_links == 0:
                        st.warning("⚠️ Smart analysis completed, but no obvious character-chapter associations found. Manual setup recommended")
                    else:
                        st.error("⚠️ Smart analysis failed, please check character and outline data")
                        
                except Exception as e:
                    st.error(f"⚠️ Analysis process error: {str(e)}")
                    print(f"⚠️ [Character Link] Button processing error: {str(e)}")
            
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear All Associations", use_container_width=True):
            # Count current associations
            current_links = sum(len(chars) for chars in st.session_state.character_chapter_mapping.values())
            
            st.session_state.character_chapter_mapping = {}
            
            if current_links > 0:
                st.success(f"✓ Cleared {current_links} character-chapter associations")
                print(f"✓ [Character Management] Clear all associations: {current_links}")
            else:
                st.info("ℹ️ Currently no character-chapter associations to clear")
            
            st.rerun()
    
    st.markdown("---")
    
    # Get character names list
    character_names = [char.get('name', '') for char in st.session_state.characters_data]
    
    # Manually manage character associations for each chapter
    st.markdown("### 📝 Manually Manage Chapter Characters")
    
    for i, chapter in enumerate(st.session_state.outline_data):
        chapter_id = chapter['chapter_id']
        
        with st.expander(f"**Chapter {i+1}: {chapter['title']}**", expanded=False):
            st.markdown(f"**Summary:** {chapter.get('summary', 'No summary')}")
            
            # Current associated characters
            current_characters = st.session_state.character_chapter_mapping.get(chapter_id, [])
            
            # Multi-select box for users to choose chapter characters
            selected_characters = st.multiselect(
                f"Select characters appearing in Chapter {i+1}:",
                options=character_names,
                default=current_characters,
                key=f"chapter_{chapter_id}_characters"
            )
            
            # Update associations
            if selected_characters != current_characters:
                st.session_state.character_chapter_mapping[chapter_id] = selected_characters
                st.info(f"✓ Chapter {i+1} character associations updated")
            
            # Show current association status
            if selected_characters:
                st.success(f"🔗 Associated characters: {', '.join(selected_characters)}")
            else:
                st.info("📝 No associated characters")
    
    # Show association statistics
    st.markdown("---")
    st.markdown("### 📊 Association Statistics")
    
    # Count how many chapters each character appears in
    character_chapter_count = {}
    for char_name in character_names:
        count = sum(1 for characters in st.session_state.character_chapter_mapping.values() if char_name in characters)
        character_chapter_count[char_name] = count
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Character Appearance Frequency:**")
        for char_name, count in character_chapter_count.items():
            if count > 0:
                st.text(f"👤 {char_name}: {count} chapters")
            else:
                st.text(f"👻 {char_name}: Not appeared")
    
    with col2:
        st.markdown("**Chapter Character Count:**")
        for i, chapter in enumerate(st.session_state.outline_data):
            chapter_id = chapter['chapter_id']
            char_count = len(st.session_state.character_chapter_mapping.get(chapter_id, []))
            st.text(f"📖 Chapter {i+1}: {char_count} characters")

def show_character_history_panel():
    """Show character history panel"""
    st.markdown("---")
    st.markdown("### 📜 Character Operation History")
    
    # Close history panel button
    if st.button("✖️ Close History Panel"):
        st.session_state.show_character_history = False
        st.rerun()
    
    if not st.session_state.characters_history:
        st.info("📝 No character history records")
        return
    
    # Undo/Redo buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("↶ Undo Character Operation", use_container_width=True, disabled=st.session_state.characters_history_index <= 0):
            if undo_characters_action():
                st.rerun()
    
    with col2:
        if st.button("↷ Redo Character Operation", use_container_width=True, disabled=st.session_state.characters_history_index >= len(st.session_state.characters_history) - 1):
            if redo_characters_action():
                st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Character History", use_container_width=True):
            st.session_state.characters_history = []
            st.session_state.characters_history_index = -1
            st.success("✓ Character history records cleared")
            st.rerun()
    
    st.markdown("---")
    
    # Show history record list
    st.markdown("**Character Operation History:**")
    
    for i, entry in enumerate(reversed(st.session_state.characters_history)):
        real_index = len(st.session_state.characters_history) - 1 - i
        is_current = real_index == st.session_state.characters_history_index
        
        # Create history record entry
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                status = "" if is_current else ""
                st.markdown(f"{status} `{entry['timestamp']}`")
            
            with col2:
                st.markdown(f"**{entry['action']}**")
                character_count = len(entry['characters_data']) if entry['characters_data'] else 0
                st.caption(f"Total {character_count} characters")
            
            with col3:
                if st.button("📍", key=f"goto_char_{real_index}", help="Jump to this state"):
                    st.session_state.characters_history_index = real_index
                    st.session_state.characters_data = copy.deepcopy(entry['characters_data'])
                    st.session_state.character_chapter_mapping = copy.deepcopy(entry['character_chapter_mapping'])
                    st.success(f"✓ Jumped to: {entry['action']}")
                    st.rerun()
        
        if i < len(st.session_state.characters_history) - 1:
            st.markdown("---")

def show_story_history_panel():
    """Show story history panel"""
    st.markdown("---")
    st.markdown("### 📜 Story Operation History")
    
    # Close history panel button
    if st.button("✖️ Close History Panel"):
        st.session_state.show_story_history = False
        st.rerun()
    
    if not st.session_state.story_history:
        st.info("📝 No story history records")
        return
    
    # Undo/Redo buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("↶ Undo Story Operation", use_container_width=True, disabled=st.session_state.story_history_index <= 0):
            if undo_story_action():
                st.rerun()
    
    with col2:
        if st.button("↷ Redo Story Operation", use_container_width=True, disabled=st.session_state.story_history_index >= len(st.session_state.story_history) - 1):
            if redo_story_action():
                st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Story History", use_container_width=True):
            st.session_state.story_history = []
            st.session_state.story_history_index = -1
            st.success("✓ Story history records cleared")
            st.rerun()
    
    st.markdown("---")
    
    # Show history record list
    st.markdown("**Story Operation History:**")
    
    for i, entry in enumerate(reversed(st.session_state.story_history)):
        real_index = len(st.session_state.story_history) - 1 - i
        is_current = real_index == st.session_state.story_history_index
        
        # Create history record entry
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                status = "" if is_current else ""
                st.markdown(f"{status} `{entry['timestamp']}`")
            
            with col2:
                st.markdown(f"**{entry['action']}**")
                story_count = len(entry['story_data']) if entry['story_data'] else 0
                total_words = sum(len(ch.get('plot', '')) for ch in entry['story_data']) if entry['story_data'] else 0
                st.caption(f"Total {story_count} chapters, {total_words} words")
            
            with col3:
                if st.button("📍", key=f"goto_story_{real_index}", help="Jump to this state"):
                    st.session_state.story_history_index = real_index
                    st.session_state.story_data = copy.deepcopy(entry['story_data'])
                    st.success(f"✓ Jumped to: {entry['action']}")
                    st.rerun()
        
        if i < len(st.session_state.story_history) - 1:
            st.markdown("---")

def show_character_edit_mode():
    """Character edit mode - referencing outline editing approach"""
    st.markdown("### 📝 Character Edit Mode")
    
    # Exit edit mode button
    if st.button("← Return to Character List"):
        st.session_state.character_edit_mode = False
        st.rerun()
    
    st.markdown("---")
    
    # Batch selection of characters to edit
    st.markdown("**Select characters to edit:**")
    selected_characters = st.multiselect(
        "Select Characters",
        options=[f"{i+1}. {char.get('name', f'Character {i+1}')}" for i, char in enumerate(st.session_state.characters_data)],
        default=[]
    )
    
    if selected_characters:
        st.markdown("---")
        
        # Edit selected characters
        for selection in selected_characters:
            character_idx = int(selection.split('.')[0]) - 1
            character = st.session_state.characters_data[character_idx]
            
            st.markdown(f"### 📝 Edit Character {character_idx + 1}: {character.get('name', 'Unknown Character')}")
            
            # Edit character basic information
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input(
                    "Character Name",
                    value=character.get('name', ''),
                    key=f"char_name_{character_idx}"
                )
                
                new_role = st.text_input(
                    "Character Role",
                    value=character.get('role', ''),
                    key=f"char_role_{character_idx}"
                )
            
            with col2:
                new_traits = st.text_area(
                    "Character Traits",
                    value=character.get('traits', ''),
                    height=80,
                    key=f"char_traits_{character_idx}"
                )
            
            # Edit character detailed information
            col1, col2 = st.columns(2)
            
            with col1:
                new_background = st.text_area(
                    "Character Background",
                    value=character.get('background', ''),
                    height=100,
                    key=f"char_background_{character_idx}"
                )
            
            with col2:
                new_motivation = st.text_area(
                    "Character Motivation",
                    value=character.get('motivation', ''),
                    height=100,
                    key=f"char_motivation_{character_idx}"
                )
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Regenerate This Character", key=f"regenerate_char_{character_idx}"):
                    regenerate_single_character(character_idx)
            
            with col2:
                if st.button("🗑️ Delete Character", key=f"delete_char_{character_idx}"):
                    # Save state before deletion to history
                    save_characters_to_history(f"Delete character: {character.get('name', f'Character {character_idx+1}')}", st.session_state.characters_data.copy())
                    # Execute deletion
                    deleted_character = st.session_state.characters_data.pop(character_idx)
                    st.success(f"✓ Deleted character: {deleted_character.get('name', 'Unknown Character')}")
                    
                    # Automatically re-link to outline after deletion
                    auto_relink_characters_to_outline()
                    
                    st.rerun()
            
            with col3:
                if st.button("💾 Save Changes", key=f"save_char_{character_idx}"):
                    save_character_edit(character_idx, new_name, new_role, new_traits, new_background, new_motivation)
            
            st.markdown("---")
    
    # Add new character
    st.markdown("### ➕ Add New Character")
    with st.form("add_character_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_char_name = st.text_input("Character Name")
            new_char_role = st.text_input("Character Role")
            new_char_traits = st.text_area("Character Traits", height=80)
        
        with col2:
            new_char_background = st.text_area("Character Background", height=80)
            new_char_motivation = st.text_area("Character Motivation", height=80)
        
        if st.form_submit_button("➕ Add Character"):
            if new_char_name and new_char_role:
                add_new_character(new_char_name, new_char_role, new_char_traits, new_char_background, new_char_motivation)
            else:
                st.warning("⚠️ Please fill in at least Character Name and Character Role")

def regenerate_single_character(character_idx):
    """Regenerate single character - regenerate based on current character traits"""
    try:
        character = st.session_state.characters_data[character_idx]
        
        with st.spinner(f"🔄 Regenerating character: {character.get('name', f'Character {character_idx+1}')}..."):
            # Record start time
            start_time = time.time()
            
            # Display backend call information in terminal
            print(f"📝 [Character Edit] Calling backend module: src.generation.generate_characters.generate_characters_v1")
            print(f"📝 [Character Edit] Regenerating single character: {character.get('name', 'Unknown Character')}")
            
            # Build regeneration instructions for current character
            current_name = character.get('name', 'Unknown Character')
            current_role = character.get('role', 'Unknown Role')
            
            # Create a temporary outline containing special instructions for current character
            temp_outline = copy.deepcopy(st.session_state.outline_data)
            
            # Add special instructions for character regeneration to outline
            character_regeneration_instruction = f"""
Please regenerate character "{current_name}" ({current_role}).
Requirements:
1. Maintain the character's basic role and positioning in the story
2. Can change specific traits, background and motivation
3. Name can change, but character type should remain consistent
4. Ensure consistency with the overall style of the story outline
"""
            
            # Call backend to regenerate all characters, but we only use the character at corresponding position
            new_characters = generate_characters_v1(temp_outline, max_characters=len(st.session_state.characters_data))
            
            # Record end time
            end_time = time.time()
            
            # Validate generation results
            if not new_characters or not isinstance(new_characters, list) or len(new_characters) <= character_idx:
                st.error("⚠️ Character regeneration failed: insufficient data returned from backend")
                return
            
            # Save state before regeneration to history
            old_characters_data = st.session_state.characters_data.copy()
            save_characters_to_history(f"Regenerate character: {character.get('name', f'Character {character_idx+1}')}", old_characters_data)
            
            # Replace character data
            st.session_state.characters_data[character_idx] = new_characters[character_idx]
            
            # Display results in terminal
            new_name = new_characters[character_idx].get('name', 'Unknown Character')
            print(f"⏱️ [Character Edit] Generation time: {end_time - start_time:.3f}s")
            print(f"✓ [Character Edit] Character regeneration completed: {current_name} → {new_name}")
            
            st.success(f"✓ Character regeneration completed: {current_name} → {new_name}")
            st.info(f"⏱️ Generation time: {end_time - start_time:.3f}s")
            
            # Automatically associate with outline after regeneration
            auto_relink_characters_to_outline()
            
            st.rerun()
            
    except Exception as e:
        st.error(f"⚠️ Character regeneration failed: {str(e)}")
        print(f"⚠️ [Character Edit] Character regeneration failed: {str(e)}")

def save_character_edit(character_idx, new_name, new_role, new_traits, new_background, new_motivation):
    """Save character edit"""
    # Save state before editing to history
    old_characters_data = st.session_state.characters_data.copy()
    save_characters_to_history(f"Edit character: {st.session_state.characters_data[character_idx].get('name', f'Character {character_idx+1}')}", old_characters_data)
    
    # Execute edit
    st.session_state.characters_data[character_idx]['name'] = new_name
    st.session_state.characters_data[character_idx]['role'] = new_role
    st.session_state.characters_data[character_idx]['traits'] = new_traits
    st.session_state.characters_data[character_idx]['background'] = new_background
    st.session_state.characters_data[character_idx]['motivation'] = new_motivation
    
    st.success(f"✓ Character {new_name} changes saved")
    print(f"✓ [Character Edit] Save character changes: {new_name}")
    
    # Automatically re-associate with outline
    auto_relink_characters_to_outline()

def add_new_character(name, role, traits, background, motivation):
    """Add new character"""
    try:
        # Save state before addition to history
        old_characters_data = st.session_state.characters_data.copy()
        save_characters_to_history(f"Add new character: {name}", old_characters_data)
        
        # Create new character
        new_character = {
            "name": name,
            "role": role,
            "traits": traits,
            "background": background,
            "motivation": motivation
        }
        
        # Add to character list
        st.session_state.characters_data.append(new_character)
        
        st.success(f"✓ New character added: {name}")
        print(f"➕ [Character Edit] Add new character: {name}")
        
        # Show character list preview
        st.info("👥 Current character list:")
        for i, char in enumerate(st.session_state.characters_data):
            marker = "🆕" if i == len(st.session_state.characters_data) - 1 else "👤"
            st.text(f"  {marker} {i+1}. {char.get('name', 'Unknown Character')}")
        
        # Automatically re-associate with outline
        auto_relink_characters_to_outline()
        
    except Exception as e:
        st.error(f"⚠️ Add character failed: {str(e)}")
        print(f"⚠️ [Character Edit] Add character failed: {str(e)}")

def show_character_consistency_check():
    """Show character consistency check interface"""
    st.markdown("### 🔍 Character Consistency Check")
    
    # Return button
    if st.button("← Return to Character List"):
        st.session_state.show_consistency_check = False
        st.rerun()
    
    st.markdown("---")
    
    if not st.session_state.characters_data or not st.session_state.outline_data:
        st.warning("⚠️ Need both character data and outline data to perform consistency check")
        return
    
    # Consistency check configuration
    st.markdown("### ⚙️ Check Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        check_scope = st.selectbox("Check Scope", [
            "Comprehensive Check", 
            "Basic Info Check", 
            "Character Motivation Check", 
            "Background Setting Check"
        ], help="Select the level of detail for checking")
        
        show_suggestions = st.checkbox("Show Modification Suggestions", value=True, help="Whether to show AI-suggested modification plans")
    
    with col2:
        check_level = st.selectbox("Check Level", [
            "Strict Mode",
            "Standard Mode", 
            "Relaxed Mode"
        ], index=1, help="Strictness level of checking")
        
        auto_fix = st.checkbox("Auto-fix Obvious Errors", value=False, help="Whether to automatically fix detected obvious errors")
    
    st.markdown("---")
    
    # Execute consistency check button
    if st.button("🔍 Start Consistency Check", type="primary", use_container_width=True):
        perform_consistency_check(check_scope, check_level, show_suggestions, auto_fix)

def perform_consistency_check(check_scope, check_level, show_suggestions, auto_fix):
    """Execute consistency check"""
    try:
        with st.spinner("🔍 Performing character consistency analysis..."):
            # Record start time
            start_time = time.time()
            
            print(f"✓ [Consistency Check] Start execution - scope: {check_scope}, level: {check_level}")
            
            # Build check prompts
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
            
            # Build check level configuration
            strictness_config = {
                "Strict Mode": "Strictly check all details, detect any possible inconsistencies",
                "Standard Mode": "Check main contradictions and obvious conflicts",
                "Relaxed Mode": "Only check serious logical conflicts"
            }
            
            scope_config = {
                "Comprehensive Check": "Check consistency of all character attributes with story",
                "Basic Info Check": "Check consistency of character names and positioning",
                "Character Motivation Check": "Check match between character motivations and story plot",
                "Background Setting Check": "Check consistency of character backgrounds with story worldview"
            }
            
            # Call backend intelligent analysis
            from src.utils.utils import generate_response, convert_json
            
            analysis_prompt = f"""
You are a professional story editor and character setting expert. Please perform a consistency check on the following character settings and story outline.

Check Level: {strictness_config[check_level]}
Check Scope: {scope_config[check_scope]}

Character Settings:
{json.dumps(characters_info, ensure_ascii=False, indent=2)}

Story Outline:
{json.dumps(chapters_info, ensure_ascii=False, indent=2)}

Please analyze whether each character's settings are consistent with the story outline, including:

1. **Character Positioning Consistency**: Whether the character's role and positioning meet story needs
2. **Background Setting Consistency**: Whether character background matches the story worldview
3. **Motivation Rationality**: Whether character motivations are consistent with story plot development logic
4. **Trait Coordination**: Whether character traits support their behavior in the story
5. **Name Appropriateness**: Whether character names fit the story style and worldview

Please return a JSON format check report:
{{
    "overall_consistency": "Overall consistency score (1-10)",
    "consistency_summary": "Overall consistency summary",
    "character_reports": [
        {{
            "character_name": "Character name",
            "consistency_score": "Consistency score (1-10)",
            "issues": [
                {{
                    "type": "Issue type",
                    "severity": "Severity (high/medium/low)",
                    "description": "Issue description",
                    "suggestion": "Modification suggestion"
                }}
            ],
            "strengths": ["List of strengths"]
        }}
    ],
    "cross_character_issues": [
        {{
            "characters": ["Characters involved"],
            "issue": "Character conflict issue",
            "suggestion": "Solution suggestion"
        }}
    ],
    "recommendations": [
        "Overall optimization suggestions"
    ]
}}

Return only JSON format, no other explanations.
"""
            
            # Call backend analysis
            msg = [{"role": "user", "content": analysis_prompt}]
            response = generate_response(msg)
            analysis_result = convert_json(response)
            
            end_time = time.time()
            print(f"⏱️ [Consistency Check] Analysis time: {end_time - start_time:.3f}s")
            
            if not analysis_result or not isinstance(analysis_result, dict):
                st.error("⚠️ Consistency check failed: incorrect data format returned by backend")
                return
            
            # Show check results
            display_consistency_results(analysis_result, show_suggestions, auto_fix)
            
    except Exception as e:
        st.error(f"⚠️ Consistency check failed: {str(e)}")
        print(f"⚠️ [Consistency Check] Check failed: {str(e)}")

def display_consistency_results(analysis_result, show_suggestions, auto_fix):
    """Show consistency check results"""
    st.markdown("---")
    st.markdown("## 📊 Consistency Check Report")
    
    # Overall score
    overall_score = analysis_result.get('overall_consistency', 'N/A')
    consistency_summary = analysis_result.get('consistency_summary', 'No summary')
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Create score display
        try:
            score_value = float(overall_score)
            if score_value >= 8:
                score_color = "🟢"
                score_level = "Excellent"
            elif score_value >= 6:
                score_color = "🟡"
                score_level = "Good"
            else:
                score_color = "🔴"
                score_level = "Needs Improvement"
        except:
            score_color = ""
            score_level = "Unknown"
        
        st.metric("Overall Consistency Score", f"{score_color} {overall_score}/10", delta=score_level)
    
    with col2:
        st.markdown("**🔍 Overall Evaluation:**")
        st.info(consistency_summary)
    
    st.markdown("---")
    
    # Character detailed report
    character_reports = analysis_result.get('character_reports', [])
    
    if character_reports:
        st.markdown("### 👥 Character Detailed Analysis")
        
        for report in character_reports:
            character_name = report.get('character_name', 'Unknown Character')
            consistency_score = report.get('consistency_score', 'N/A')
            issues = report.get('issues', [])
            strengths = report.get('strengths', [])
            
            with st.expander(f"**{character_name}** - Score: {consistency_score}/10", expanded=len(issues) > 0):
                
                # Show strengths
                if strengths:
                    st.markdown("**✨ Strengths:**")
                    for strength in strengths:
                        st.success(f"• {strength}")
                
                # Show issues
                if issues:
                    st.markdown("**⚠️ Issues Found:**")
                    
                    for issue in issues:
                        issue_type = issue.get('type', 'Unknown Issue')
                        severity = issue.get('severity', 'medium')
                        description = issue.get('description', 'No description')
                        suggestion = issue.get('suggestion', 'No suggestion')
                        
                        # Choose color based on severity
                        if severity == 'high':
                            st.error(f"🔴 **{issue_type}** (High)")
                        elif severity == 'medium':
                            st.warning(f"🟡 **{issue_type}** (Medium)")
                        else:
                            st.info(f"🔵 **{issue_type}** (Low)")
                        
                        st.markdown(f"   Description: {description}")
                        
                        if show_suggestions and suggestion:
                            st.markdown(f"   💡 Suggestion: {suggestion}")
                        
                        st.markdown("---")
                else:
                    st.success("✓ No obvious issues found")
    
    # Cross-character conflict analysis
    cross_character_issues = analysis_result.get('cross_character_issues', [])
    
    if cross_character_issues:
        st.markdown("### 🤝 Cross-Character Relationship Analysis")
        
        for issue in cross_character_issues:
            characters = issue.get('characters', [])
            issue_desc = issue.get('issue', 'No description')
            suggestion = issue.get('suggestion', 'No suggestion')
            
            st.warning(f"**Characters Involved:** {', '.join(characters)}")
            st.markdown(f"**Issue:** {issue_desc}")
            
            if show_suggestions and suggestion:
                st.markdown(f"**Suggestion:** {suggestion}")
            
            st.markdown("---")
    
    # Overall recommendations
    recommendations = analysis_result.get('recommendations', [])
    
    if recommendations and show_suggestions:
        st.markdown("### 💡 Optimization Recommendations")
        
        for i, rec in enumerate(recommendations):
            st.info(f"{i+1}. {rec}")
    
    # Save report
    st.markdown("---")
    if st.button("💾 Save Check Report", use_container_width=True):
        save_consistency_report(analysis_result)

def save_consistency_report(analysis_result):
    """Save consistency check report"""
    try:
        # Use real backend save function
        report_filename = f"consistency_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(analysis_result, st.session_state.current_version, report_filename)
        
        st.success(f"✓ Check report saved: {st.session_state.current_version}/{report_filename}")
        print(f"💾 [Consistency Check] Save report: {report_filename}")
        
    except Exception as e:
        st.error(f"⚠️ Save report failed: {str(e)}")
        print(f"⚠️ [Consistency Check] Save report failed: {str(e)}")

def show_character_relationships():
    """Show character relationship network interface"""
    st.markdown("### 🕸️ Character Relationship Network")
    
    # Return button
    if st.button("← Return to Character List"):
        st.session_state.show_character_relationships = False
        st.rerun()
    
    st.markdown("---")
    
    if not st.session_state.characters_data:
        st.warning("⚠️ Need character data to analyze relationship network")
        return
    
    # Relationship analysis configuration
    st.markdown("### ⚙️ Analysis Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_depth = st.selectbox("Analysis Depth", [
            "Basic Relationships",
            "Detailed Relationships", 
            "Complex Network"
        ], index=1, help="Select the level of detail for relationship analysis")
        
        include_outline = st.checkbox("Combine with Outline Analysis", value=True, help="Whether to analyze character relationships based on story outline")
    
    with col2:
        relationship_types = st.multiselect("Relationship Types", [
            "Family Relationships",
            "Friend Relationships", 
            "Hostile Relationships",
            "Cooperative Relationships",
            "Teacher-Student Relationships",
            "Superior-Subordinate Relationships",
            "Competitive Relationships",
            "Other Relationships"
        ], default=["Family Relationships", "Friend Relationships", "Hostile Relationships", "Cooperative Relationships"])
        
        show_network_graph = st.checkbox("Show Relationship Graph", value=True, help="Whether to show visualized relationship network graph")
    
    st.markdown("---")
    
    # Execute relationship analysis button
    if st.button("🔍 Start Relationship Analysis", type="primary", use_container_width=True):
        perform_relationship_analysis(analysis_depth, include_outline, relationship_types, show_network_graph)

def perform_relationship_analysis(analysis_depth, include_outline, relationship_types, show_network_graph):
    """Execute character relationship analysis"""
    try:
        with st.spinner("🕸️ Analyzing character relationship network..."):
            # Record start time
            start_time = time.time()
            
            print(f"🕸️ [Relationship Analysis] Start execution - depth: {analysis_depth}, types: {relationship_types}")
            
            # Build analysis data
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
            
            # If includes outline analysis
            outline_context = ""
            if include_outline and st.session_state.outline_data:
                chapters_info = []
                for chapter in st.session_state.outline_data:
                    chapters_info.append({
                        "chapter_id": chapter['chapter_id'],
                        "title": chapter['title'],
                        "summary": chapter.get('summary', '')
                    })
                outline_context = f"\n\nStory Outline:\n{json.dumps(chapters_info, ensure_ascii=False, indent=2)}"
            
            # Call backend intelligent analysis
            from src.utils.utils import generate_response, convert_json
            
            analysis_prompt = f"""
You are a professional story analyst and character relationship expert. Please analyze the relationship network between the following characters.

Analysis Depth: {analysis_depth}
Relationship Types: {', '.join(relationship_types)}

Character Information:
{json.dumps(characters_info, ensure_ascii=False, indent=2)}
{outline_context}

Please analyze the relationships between characters, including:

1. **Direct Relationships**: Direct connections and interactions between characters
2. **Indirect Relationships**: Connections established through other characters or events
3. **Relationship Strength**: The importance and influence of relationships
4. **Relationship Nature**: Types of relationships (friendly, hostile, neutral, etc.)
5. **Relationship Development**: Trends of relationship changes in the story

Please return relationship analysis in JSON format:
{{
    "relationship_summary": "Overall description of relationship network",
    "character_relationships": [
        {{
            "character_a": "Character A name",
            "character_b": "Character B name",
            "relationship_type": "Relationship type",
            "relationship_strength": "Relationship strength (1-10)",
            "relationship_nature": "Relationship nature (positive/negative/neutral)",
            "description": "Detailed relationship description",
            "story_context": "Manifestation in the story",
            "development_trend": "Relationship development trend"
        }}
    ],
    "character_centrality": [
        {{
            "character": "Character name",
            "centrality_score": "Centrality score (1-10)",
            "role_in_network": "Role in relationship network",
            "key_connections": ["List of important connected characters"]
        }}
    ],
    "relationship_clusters": [
        {{
            "cluster_name": "Relationship cluster name",
            "members": ["Cluster members"],
            "cluster_type": "Cluster type",
            "description": "Cluster description"
        }}
    ],
    "network_insights": [
        "Relationship network insights"
    ]
}}

Return only JSON format, no other explanations.
"""
            
            # Call backend analysis
            msg = [{"role": "user", "content": analysis_prompt}]
            response = generate_response(msg)
            analysis_result = convert_json(response)
            
            end_time = time.time()
            print(f"⏱️ [Relationship Analysis] Analysis time: {end_time - start_time:.3f}s")
            
            if not analysis_result or not isinstance(analysis_result, dict):
                st.error("⚠️ Relationship analysis failed: incorrect data format returned by backend")
                return
            
            # Show analysis results
            display_relationship_results(analysis_result, show_network_graph)
            
    except Exception as e:
        st.error(f"⚠️ Relationship analysis failed: {str(e)}")
        print(f"⚠️ [Relationship Analysis] Analysis failed: {str(e)}")

def display_relationship_results(analysis_result, show_network_graph):
    """Show character relationship analysis results"""
    st.markdown("---")
    st.markdown("## 🕸️ Character Relationship Network Analysis")
    
    # Network overview
    relationship_summary = analysis_result.get('relationship_summary', 'No summary')
    st.markdown("### 📊 Network Overview")
    st.info(relationship_summary)
    
    st.markdown("---")
    
    # Character relationship list
    relationships = analysis_result.get('character_relationships', [])
    
    if relationships:
        st.markdown("### 🤝 Character Relationship Details")
        
        # Create relationship statistics
        total_relationships = len(relationships)
        positive_relationships = len([r for r in relationships if r.get('relationship_nature') == 'positive'])
        negative_relationships = len([r for r in relationships if r.get('relationship_nature') == 'negative'])
        neutral_relationships = len([r for r in relationships if r.get('relationship_nature') == 'neutral'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Relationships", total_relationships)
        with col2:
            st.metric("Positive Relationships", positive_relationships, delta="🟢")
        with col3:
            st.metric("Negative Relationships", negative_relationships, delta="🔴")
        with col4:
            st.metric("Neutral Relationships", neutral_relationships, delta="")
        
        st.markdown("---")
        
        # Detailed relationship list
        for i, rel in enumerate(relationships):
            char_a = rel.get('character_a', 'Character A')
            char_b = rel.get('character_b', 'Character B')
            rel_type = rel.get('relationship_type', 'Unknown Relationship')
            rel_strength = rel.get('relationship_strength', 'N/A')
            rel_nature = rel.get('relationship_nature', 'neutral')
            description = rel.get('description', 'No description')
            story_context = rel.get('story_context', 'No context')
            development_trend = rel.get('development_trend', 'No trend')
            
            # Choose color based on relationship nature
            if rel_nature == 'positive':
                nature_color = "🟢"
            elif rel_nature == 'negative':
                nature_color = "🔴"
            else:
                nature_color = ""
            
            with st.expander(f"{nature_color} **{char_a} ↔ {char_b}** ({rel_type}) - Strength: {rel_strength}/10"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Relationship Nature:** {rel_nature}")
                    st.markdown(f"**Relationship Strength:** {rel_strength}/10")
                    st.markdown(f"**Relationship Type:** {rel_type}")
                
                with col2:
                    st.markdown(f"**Development Trend:** {development_trend}")
                
                st.markdown(f"**Relationship Description:** {description}")
                
                if story_context != 'No context':
                    st.markdown(f"**Story Context:** {story_context}")
    
    # Character centrality analysis
    centrality_data = analysis_result.get('character_centrality', [])
    
    if centrality_data:
        st.markdown("---")
        st.markdown("### 🎯 Character Centrality Analysis")
        
        # Sort by centrality score
        centrality_data.sort(key=lambda x: float(x.get('centrality_score', 0)), reverse=True)
        
        for cent in centrality_data:
            character = cent.get('character', 'Unknown Character')
            centrality_score = cent.get('centrality_score', 'N/A')
            role_in_network = cent.get('role_in_network', 'No description')
            key_connections = cent.get('key_connections', [])
            
            # Choose color based on centrality score
            try:
                score_value = float(centrality_score)
                if score_value >= 8:
                    score_color = "🟢"
                elif score_value >= 6:
                    score_color = "🟡"
                else:
                    score_color = ""
            except:
                score_color = ""
            
            with st.expander(f"{score_color} **{character}** - Centrality: {centrality_score}/10"):
                st.markdown(f"**Network Role:** {role_in_network}")
                
                if key_connections:
                    st.markdown(f"**Key Connections:** {', '.join(key_connections)}")
    
    # Relationship cluster analysis
    clusters = analysis_result.get('relationship_clusters', [])
    
    if clusters:
        st.markdown("---")
        st.markdown("### 👥 Relationship Cluster Analysis")
        
        for cluster in clusters:
            cluster_name = cluster.get('cluster_name', 'Unknown Cluster')
            members = cluster.get('members', [])
            cluster_type = cluster.get('cluster_type', 'Unknown Type')
            description = cluster.get('description', 'No description')
            
            with st.expander(f"**{cluster_name}** ({cluster_type}) - {len(members)} Members"):
                st.markdown(f"**Members:** {', '.join(members)}")
                st.markdown(f"**Cluster Type:** {cluster_type}")
                st.markdown(f"**Description:** {description}")
    
    # Network insights
    insights = analysis_result.get('network_insights', [])
    
    if insights:
        st.markdown("---")
        st.markdown("### 💡 Network Insights")
        
        for i, insight in enumerate(insights):
            st.info(f"{i+1}. {insight}")
    
    # Network graph visualization
    if show_network_graph and relationships:
        st.markdown("---")
        st.markdown("### 📈 Relationship Network Graph")
        
        try:
            # Create network graph
            create_relationship_network_graph(relationships, centrality_data)
        except Exception as e:
            st.warning(f"⚠️ Network graph generation failed: {str(e)}")
            st.info("📊 Try installing networkx and matplotlib libraries to support network graph visualization")
    
    # Save analysis results
    st.markdown("---")
    if st.button("💾 Save Relationship Analysis", use_container_width=True):
        save_relationship_analysis(analysis_result)

def create_relationship_network_graph(relationships, centrality_data):
    """Create relationship network diagram - using Mermaid charts"""
    try:
        # Extract all characters
        characters = set()
        for rel in relationships:
            characters.add(rel.get('character_a', ''))
            characters.add(rel.get('character_b', ''))
        
        characters = list(characters)
        
        # Create Mermaid chart code
        mermaid_code = "graph TD\n"
        
        # Add nodes (characters)
        for i, char in enumerate(characters):
            # Determine node style based on centrality
            centrality_score = 5  # Default value
            for cent in centrality_data:
                if cent.get('character') == char:
                    try:
                        centrality_score = float(cent.get('centrality_score', 5))
                    except:
                        centrality_score = 5
                    break
            
            # Choose node style based on centrality
            if centrality_score >= 8:
                node_style = f"A{i}[\"{char}<br/>⭐High Centrality\"]"
            elif centrality_score >= 6:
                node_style = f"A{i}[\"{char}<br/>🔸Medium Centrality\"]"
            else:
                node_style = f"A{i}[\"{char}\"]"
            
            mermaid_code += f"    {node_style}\n"
        
        # Add relationship edges
        for rel in relationships:
            char_a = rel.get('character_a', '')
            char_b = rel.get('character_b', '')
            rel_type = rel.get('relationship_type', 'Relationship')
            rel_nature = rel.get('relationship_nature', 'neutral')
            
            if char_a in characters and char_b in characters:
                a_idx = characters.index(char_a)
                b_idx = characters.index(char_b)
                
                # Choose edge style based on relationship nature
                if rel_nature == 'positive':
                    edge_style = f"A{a_idx} -.->|\" {rel_type}\"| A{b_idx}"
                elif rel_nature == 'negative':
                    edge_style = f"A{a_idx} -.->|\" {rel_type}\"| A{b_idx}"
                else:
                    edge_style = f"A{a_idx} -.->|\" {rel_type}\"| A{b_idx}"
                
                mermaid_code += f"    {edge_style}\n"
        
        # Show Mermaid chart
        st.markdown("#### 🕸️ Relationship Network Visualization")
        
        # Create simplified network relationship table
        create_relationship_table(relationships, centrality_data)
        
        # Show Mermaid code for user use
        with st.expander("📜 View Mermaid Chart Code", expanded=False):
            st.code(mermaid_code, language="text")
            st.info("📎 You can copy the above code to [Mermaid Online Editor](https://mermaid.live/) to view the visualization chart")
            
            # Provide direct link
            import urllib.parse
            encoded_mermaid = urllib.parse.quote(mermaid_code)
            mermaid_url = f"https://mermaid.live/edit#pako:eNpdjjEOwjAMRa8S-QduwAKCA3RhYQGxuHFoLdJ4OHa7VL17C2JBYrL1_vfekx_obUYLHShpOmgb5-2Ise6eLvJ5Y_7Eb7Ud10_Kzg=="
            st.markdown(f"🔗 [Open Mermaid Editor in New Window]({mermaid_url})")
            
        # Use HTML to simply display relationship network
        create_simple_network_html(characters, relationships)
        
    except Exception as e:
        st.error(f"⚠️ Failed to generate network graph: {str(e)}")
        print(f"⚠️ [Relationship Network] Chart generation failed: {str(e)}")

def create_relationship_table(relationships, centrality_data):
    """Create relationship network table display"""
    st.markdown("#### 📊 Relationship Network Table")
    
    # Create relationship data table
    if relationships:
        import pandas as pd
        
        table_data = []
        for rel in relationships:
            table_data.append({
                "Character A": rel.get('character_a', ''),
                "Relationship": rel.get('relationship_type', ''),
                "Character B": rel.get('character_b', ''),
                "Nature": rel.get('relationship_nature', ''),
                "Strength": rel.get('relationship_strength', ''),
                "Description": rel.get('description', '')[:50] + "..." if len(rel.get('description', '')) > 50 else rel.get('description', '')
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Show centrality ranking
    if centrality_data:
        st.markdown("#### 🏆 Character Importance Ranking")
        
        # Sort by centrality score
        sorted_centrality = sorted(centrality_data, key=lambda x: float(x.get('centrality_score', 0)), reverse=True)
        
        col1, col2, col3 = st.columns(3)
        for i, cent in enumerate(sorted_centrality[:9]):  # Show top 9
            character = cent.get('character', 'Unknown Character')
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
    """Create simple HTML network diagram"""
    st.markdown("#### 🕸️ Simplified Relationship Network Graph")
    
    if not characters or not relationships:
        st.info("📝 No relationship data available to display")
        return
    
    # Limit display quantity to avoid page overload
    max_characters = 10
    max_relationships = 15
    
    display_characters = characters[:max_characters]
    display_relationships = relationships[:max_relationships]
    
    # Character node display
    st.markdown("**👥 Character Nodes:**")
    
    # Use columns to layout characters
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
        st.info(f"... {len(characters) - max_characters} more characters not shown")
    
    st.markdown("---")
    
    # Relationship connection display
    st.markdown("**🔗 Relationship Connections:**")
    
    if not display_relationships:
        st.info("📝 No relationship data")
        return
    
    for i, rel in enumerate(display_relationships):
        char_a = rel.get('character_a', '')
        char_b = rel.get('character_b', '')
        rel_type = rel.get('relationship_type', '')
        rel_nature = rel.get('relationship_nature', '')
        rel_strength = rel.get('relationship_strength', 'N/A')
        
        # Choose color and icon based on relationship nature
        if rel_nature == 'positive':
            color = "#4caf50"  # Green
            emoji = "💚"
            bg_color = "#e8f5e8"
        elif rel_nature == 'negative':
            color = "#f44336"  # Red
            emoji = "💔"
            bg_color = "#ffebee"
        else:
            color = "#ff9800"  # Orange
            emoji = "🤝"
            bg_color = "#fff3e0"
        
        # Use Streamlit's built-in components instead of HTML
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col1:
                st.markdown(f"**{char_a}**")
            
            with col2:
                st.markdown(f"<div style='text-align: center; color: {color};'>{emoji}<br>{rel_type}</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"**{char_b}**")
            
            # Show relationship details
            if rel_strength != 'N/A':
                st.caption(f"Relationship Strength: {rel_strength}/10 | Nature: {rel_nature}")
            else:
                st.caption(f"Nature: {rel_nature}")
        
        if i < len(display_relationships) - 1:
            st.markdown("---")
    
    if len(relationships) > max_relationships:
        st.info(f"... {len(relationships) - max_relationships} more relationships not shown")

def save_relationship_analysis(analysis_result):
    """Save relationship analysis results"""
    try:
        # Use real backend save function
        report_filename = f"relationship_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(analysis_result, st.session_state.current_version, report_filename)
        
        st.success(f"✓ Relationship analysis saved: {st.session_state.current_version}/{report_filename}")
        print(f"💾 [Relationship Analysis] Save analysis: {report_filename}")
        
    except Exception as e:
        st.error(f"⚠️ Save analysis failed: {str(e)}")
        print(f"⚠️ [Relationship Analysis] Save analysis failed: {str(e)}")

def show_story_generation_interface():
    """Show story generation interface - as main process step"""
    st.header("📖 Step 3: Story Generation")
    
    # Check prerequisites
    if not st.session_state.outline_data:
        st.error("❌ Please complete Step 1 first: Generate Story Outline")
        return
    
    if not st.session_state.characters_data:
        st.error("❌ Please complete Step 2 first: Generate Character Settings")
        return
    
    # Show story generation interface based on outline and characters
    show_story_generation_mode()

def show_story_generation_mode():
    """Story generation mode"""
    st.subheader("📖 Story Content Generation and Management")
    
    # Story generation configuration
    st.markdown("### ⚙️ Story Generation Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        use_narrative_guidance = st.checkbox("Use Narrative Guidance", value=True, help="Use narrative analysis guidance from the outline")
        use_cache = st.checkbox("Use Cache", value=True, help="If story data already exists, load directly", key="story_use_cache_checkbox")
    
    with col2:
        custom_instruction = st.text_area("Custom Instructions", placeholder="Optional: Add special writing requirements or style guidance", height=80)
        auto_save = st.checkbox("Auto Save", value=True, help="Automatically save after generation", key="story_auto_save_checkbox")
    
    st.markdown("---")
    
    # Story generation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📖 Generate Story", type="primary", use_container_width=True):
            expand_story_from_outline(use_narrative_guidance, custom_instruction, use_cache, auto_save)
    
    with col2:
        if st.button("🔄 Regenerate", use_container_width=True):
            expand_story_from_outline(use_narrative_guidance, custom_instruction, use_cache=False, auto_save=auto_save)
    
    with col3:
        if st.button("📁 Load Story", use_container_width=True):
            st.session_state.show_story_loader = True
            st.rerun()
    
    st.markdown("---")
    
    # Check if story file loader needs to be displayed
    if st.session_state.get('show_story_loader', False):
        load_existing_story()
        return
    
    # Show story data
    if st.session_state.story_data:
        show_story_display()
    else:
        st.info("📝 No story data available. Please click 'Generate Story' button to start generation")
        
        # Debug information
        st.info(f"🔍 Debug: Current story data status - {type(st.session_state.get('story_data', None))}, length: {len(st.session_state.get('story_data', []))}")
        
        # Prompt user to start story generation
        st.info("📢 Click the 'Generate Story' button above to start generating detailed story based on outline and characters")

def expand_story_from_outline(use_narrative_guidance=True, custom_instruction="", use_cache=True, auto_save=True):
    """Expand story from outline and characters - integrated version"""
    try:
        # Check cache
        if use_cache and st.session_state.story_data:
            st.success("✓ Using cached story data")
            return
        
        with st.spinner("📖 Generating detailed story content..."):
            # Record start time
            start_time = time.time()
            
            # Display backend call information in terminal
            print(f"🚀 [Story Generator Integration] Calling backend module: src.generation.expand_story.expand_story_v1")
            print(f"📝 [Story Generator Integration] Input parameters: outline chapters={len(st.session_state.outline_data)}, characters={len(st.session_state.characters_data)}")
            
            # Prepare custom instructions
            final_instruction = ""
            if use_narrative_guidance:
                final_instruction += "Please strictly follow the narrative guidance of each chapter to organize content."
            if custom_instruction:
                final_instruction += f" {custom_instruction}"
            
            # Call real backend function
            from src.generation.expand_story import expand_story_v1
            story = expand_story_v1(
                st.session_state.outline_data, 
                st.session_state.characters_data, 
                custom_instruction=final_instruction if final_instruction else None
            )
            
            # Record end time
            end_time = time.time()
            
            # Display results in terminal
            print(f"⏱️ [Story Generator Integration] Generation time: {end_time - start_time:.3f}s")
            print(f"🎉 [Story Generator Integration] Story generation completed! Total generated {len(story) if story else 0} chapters")
            
            # Validate generation results
            if not story or not isinstance(story, list):
                st.error("⚠️ Story generation failed: backend returned data in incorrect format")
                print(f"⚠️ [Story Generator Integration] Backend returned data format error: {type(story)} - {str(story)[:200]}...")
                return
            
            # Supplement chapter ID and title
            for idx, chapter in enumerate(story):
                if idx < len(st.session_state.outline_data):
                    chapter.setdefault("chapter_id", st.session_state.outline_data[idx]["chapter_id"])
                    chapter.setdefault("title", st.session_state.outline_data[idx]["title"])
            
            # Save to session state
            st.session_state.story_data = story
            
            # Save to history
            save_story_to_history("Generate Story")
            
            # Display chapter list in terminal
            chapter_titles = [ch.get('title', f"Chapter {i+1}") for i, ch in enumerate(story)]
            print(f"📖 [Story Generator Integration] Generated chapters: {', '.join(chapter_titles[:3])}{'...' if len(chapter_titles) > 3 else ''}")
            
            # Auto save
            if auto_save:
                save_story_to_project()
            
            # Show success message
            st.success(f"✓ Story generation completed! Total generated {len(story)} chapters")
            st.info(f"⏱️ Generation time: {end_time - start_time:.3f}s")
            
            # Display chapter brief information
            st.info(f"📖 Generated chapters: {', '.join(chapter_titles)}")
            
            st.rerun()
            
    except Exception as e:
        st.error(f"⚠️ Story generation failed: {str(e)}")
        print(f"⚠️ [Story Generator Integration] Story generation failed: {str(e)}")

def save_story_to_project():
    """Save story to project directory"""
    try:
        if not st.session_state.story_data:
            st.warning("⚠️ No story data available to save")
            return
        
        start_time = time.time()
        # Use real backend save function
        save_json(st.session_state.story_data, st.session_state.current_version, "story.json")
        end_time = time.time()
        
        st.success(f"✓ Story saved to project directory: {st.session_state.current_version}/story.json")
        print(f"💾 [Story Generator Integration] Save story to project: {st.session_state.current_version}/story.json ({len(st.session_state.story_data)} chapters)")
        
    except Exception as e:
        st.error(f"⚠️ Save failed: {str(e)}")
        print(f"⚠️ [Story Generator Integration] Save story failed: {str(e)}")

def load_existing_story():
    """Load existing story file"""
    st.markdown("### 📁 Load Existing Story")
    
    # Add session state to prevent duplicate uploader after successful upload
    if st.session_state.get('story_file_uploaded', False):
        st.success("✅ Story file uploaded successfully! The page will refresh automatically.")
        # Reset flag after display
        st.session_state.story_file_uploaded = False
        return
    
    # Add return button
    if st.button("← Return to Story Management"):
        st.session_state.show_story_loader = False
        st.rerun()
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Select Story File", type=['json'], key="story_upload")
    
    if uploaded_file is not None:
        try:
            # Show file information
            st.info(f"📄 File name: {uploaded_file.name}")
            st.info(f" File size: {uploaded_file.size} bytes")
            
            # Reset file pointer to beginning
            uploaded_file.seek(0)
            
            # Read file content
            file_content = uploaded_file.read()
            
            # If bytes type, convert to string
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # Parse JSON
            story_data = json.loads(file_content)
            
            # Detailed validation of data format
            if not isinstance(story_data, list):
                st.error("❌ Incorrect file format: should be JSON array format")
                return
            
            if len(story_data) == 0:
                st.error("⚠️ File content is empty: no story data found")
                return
            
            # Validate story data format
            required_fields = ['plot']
            for i, chapter in enumerate(story_data):
                if not isinstance(chapter, dict):
                    st.error(f"❌ Chapter {i+1} format incorrect: should be object format")
                    return
                
                missing_fields = [field for field in required_fields if field not in chapter]
                if missing_fields:
                    st.error(f"❌ Chapter {i+1} missing required fields: {', '.join(missing_fields)}")
                    return
            
            # Load data
            st.session_state.story_data = story_data
            
            # Save to history
            save_story_to_history("Load Story")
            
            st.success(f"✓ Story data loaded successfully! Total {len(story_data)} chapters")
            st.info("🔄 Page will refresh automatically...")
            
            # Display loaded story preview
            with st.expander("📖 Loaded Story Preview", expanded=True):
                for i, chapter in enumerate(story_data[:3]):  # Only show first 3 chapters
                    title = chapter.get('title', f'Chapter {i+1}')
                    plot_preview = chapter.get('plot', 'No content')[:100] + "..." if len(chapter.get('plot', '')) > 100 else chapter.get('plot', 'No content')
                    st.text(f"{i+1}. {title}")
                    st.text(f"   {plot_preview}")
                if len(story_data) > 3:
                    st.text(f"... {len(story_data) - 3} more chapters")
            
            print(f"📁 [Story Management] Load story file: {len(story_data)} chapters")
            
            # Clear loader state
            st.session_state.show_story_loader = False
            
            # Set flag to prevent duplicate uploader
            st.session_state.story_file_uploaded = True
            st.rerun()
            
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON format error: {str(e)}")
            st.error("❌ Please ensure the file is in valid JSON format")
        except UnicodeDecodeError as e:
            st.error(f"❌ File encoding error: {str(e)}")
            st.error("❌ Please ensure the file is UTF-8 encoded")
        except Exception as e:
            st.error(f"❌ File loading failed: {str(e)}")
            print(f"⚠️ [Story Management] Load failed: {str(e)}")
    else:
        st.info("📝 Please select a JSON format story file")

def show_story_display():
    """Show story information and management interface"""
    st.markdown("### 📖 Story Content Management")
    
    story = st.session_state.story_data
    
    # Story statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Chapters", len(story))
    with col2:
        total_plot_length = sum(len(ch.get('plot', '')) for ch in story)
        st.metric("Total Words", f"{total_plot_length} words")
    with col3:
        avg_length = total_plot_length // len(story) if story else 0
        st.metric("Average Chapter Length", f"{avg_length} words")
    
    st.markdown("---")
    
    # Story management operations
    st.markdown("### 🛠️ Story Management")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 Save Story", use_container_width=True):
            save_story_to_project()
    
    with col2:
        if st.button("📄 Story History", use_container_width=True):
            st.session_state.show_story_history = True
            st.rerun()
    
    with col3:
        if st.button("🔄 Regenerate All", use_container_width=True):
            old_story_data = st.session_state.story_data.copy()
            expand_story_from_outline(use_cache=False, auto_save=True)
    
    with col4:
        if st.button("🗑️ Clear Story", use_container_width=True):
            if st.button("✅ Confirm Clear", key="confirm_clear_story"):
                save_story_to_history("Clear Story", st.session_state.story_data.copy())
                st.session_state.story_data = []
                st.success("✓ Story data cleared")
                print("🗑️ [Story Management] Story data cleared")
                st.rerun()
    
    # Display story history panel
    if st.session_state.get('show_story_history', False):
        show_story_history_panel()
    
    st.markdown("---")
    
    # Function tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Chapter Summary", "🔗 Coherence Check", "✏️ Key Adjustments", "🎨 Style Consistency"])
    
    with tab1:
        show_story_summary()
    
    with tab2:
        show_coherence_check()
    
    with tab3:
        show_story_editing()
    
    with tab4:
        show_style_consistency()

def show_story_summary():
    """Show chapter summary overview"""
    st.markdown("#### 📋 All Chapters Overview")
    
    story = st.session_state.story_data
    
    # Create summary data
    summary_data = []
    for i, chapter in enumerate(story):
        title = chapter.get('title', f'Chapter {i+1}')
        plot = chapter.get('plot', '')
        word_count = len(plot)
        
        # Generate summary (first 200 characters)
        summary = plot[:200] + "..." if len(plot) > 200 else plot
        
        summary_data.append({
            "Chapter": f"{i+1}. {title}",
            "Word Count": word_count,
            "Content Summary": summary,
            "Scene": chapter.get('scene', 'Unspecified'),
            "Characters": ', '.join(chapter.get('characters', [])) if chapter.get('characters') else 'Unspecified'
        })
    
    # Display summary table
    if summary_data:
        import pandas as pd
        df = pd.DataFrame(summary_data)
        
        # Use better display method to ensure content summary is fully displayed
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Content Summary": st.column_config.TextColumn(
                    "Content Summary",
                    width="large",
                    help="Detailed chapter content summary"
                ),
                "Chapter": st.column_config.TextColumn(
                    "Chapter",
                    width="medium"
                ),
                "Word Count": st.column_config.NumberColumn(
                    "Word Count",
                    width="small"
                ),
                "Scene": st.column_config.TextColumn(
                    "Scene", 
                    width="medium"
                ),
                "Characters": st.column_config.TextColumn(
                    "Characters",
                    width="medium"
                )
            }
        )
        
        # Detailed content viewing
        st.markdown("---")
        st.markdown("#### 📖 Detailed Content Viewing")
        
        # Select chapter to view detailed content
        selected_chapter_for_detail = st.selectbox(
            "Select chapter to view complete content",
            options=[f"{i+1}. {ch.get('title', f'Chapter {i+1}')}" for i, ch in enumerate(story)],
            index=0,
            key="detail_chapter_selector"
        )
        
        if selected_chapter_for_detail:
            detail_idx = int(selected_chapter_for_detail.split('.')[0]) - 1
            detail_chapter = story[detail_idx]
            
            with st.expander(f"📖 {detail_chapter.get('title', f'Chapter {detail_idx+1}')} - Complete Content", expanded=True):
                st.markdown(f"**Word Count:** {len(detail_chapter.get('plot', ''))} words")
                st.markdown(f"**Scene:** {detail_chapter.get('scene', 'Unspecified')}")
                st.markdown(f"**Characters:** {', '.join(detail_chapter.get('characters', [])) if detail_chapter.get('characters') else 'Unspecified'}")
                st.markdown("---")
                st.markdown("**Complete Content:**")
                st.text_area(
                    "Chapter Complete Content",
                    value=detail_chapter.get('plot', ''),
                    height=400,
                    key=f"detail_content_{detail_idx}",
                    disabled=True,
                    label_visibility="collapsed"
                )
        
        st.markdown("---")
        
        # Export summary
        if st.button("📥 Export Chapter Summary", use_container_width=True):
            summary_text = generate_story_summary_text()
            st.download_button(
                label="📄 Download Summary Text",
                data=summary_text,
                file_name=f"{st.session_state.current_version}_story_summary.txt",
                mime="text/plain"
            )

def show_coherence_check():
    """Show coherence check"""
    st.markdown("#### 🔗 Inter-Chapter Coherence Analysis")
    
    if st.button("🔍 Start Coherence Check", type="primary", use_container_width=True):
        perform_coherence_analysis()

def show_story_editing():
    """Show story editing interface"""
    st.markdown("#### ✏️ Key Chapter Adjustments")
    
    story = st.session_state.story_data
    
    # Select chapters to edit
    chapter_options = [f"{i+1}. {ch.get('title', f'Chapter {i+1}')}" for i, ch in enumerate(story)]
    selected_chapters = st.multiselect("Select chapters to rewrite", chapter_options)
    
    if selected_chapters:
        st.markdown("---")
        
        for selection in selected_chapters:
            chapter_idx = int(selection.split('.')[0]) - 1
            chapter = story[chapter_idx]
            
            with st.expander(f"📝 Edit: {chapter.get('title', f'Chapter {chapter_idx+1}')}", expanded=True):
                
                # Display current content
                st.markdown("**Current Content:**")
                st.text_area("Current Chapter Content", value=chapter.get('plot', ''), height=200, key=f"current_plot_{chapter_idx}", disabled=True, label_visibility="collapsed")
                
                # Edit options
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"🔄 Regenerate Chapter {chapter_idx+1}", key=f"regen_{chapter_idx}"):
                        regenerate_single_story_chapter(chapter_idx)
                
                with col2:
                    if st.button(f"✏️ Manual Edit Chapter {chapter_idx+1}", key=f"edit_{chapter_idx}"):
                        st.session_state[f'edit_story_{chapter_idx}'] = True
                        st.rerun()
                
                # If entering edit mode
                if st.session_state.get(f'edit_story_{chapter_idx}', False):
                    st.markdown("**Edit Content:**")
                    new_plot = st.text_area(
                        "New Story Content", 
                        value=chapter.get('plot', ''), 
                        height=300, 
                        key=f"new_plot_{chapter_idx}"
                    )
                    
                    # Suggestion file upload feature
                    st.markdown("---")
                    st.markdown("#### 📁 Smart Suggestion Files")
                    
                    uploaded_suggestions = st.file_uploader(
                        "Upload suggestion file (.json)",
                        type=['json'],
                        key=f"upload_suggestions_{chapter_idx}",
                        help="Upload previously exported smart suggestion file to execute cascading updates directly"
                    )
                    
                    if uploaded_suggestions is not None:
                        if st.button(f"⚡ Execute Update Based on Suggestion File", key=f"execute_uploaded_{chapter_idx}", type="primary"):
                            execute_uploaded_suggestions(chapter_idx, uploaded_suggestions, new_plot)
                            return
                    
                    st.markdown("---")
                    
                    # Smart conflict detection options
                    st.markdown("**🔍 Smart Detection Options:**")
                    col_detect1, col_detect2 = st.columns(2)
                    
                    with col_detect1:
                        enable_conflict_detection = st.checkbox(
                            "Enable Conflict Detection", 
                            value=True, 
                            key=f"conflict_detect_{chapter_idx}",
                            help="Detect if modifications conflict with other chapters, character settings, or outline"
                        )
                    
                    with col_detect2:
                        auto_suggest_updates = st.checkbox(
                            "Auto-suggest Updates", 
                            value=True, 
                            key=f"auto_suggest_{chapter_idx}",
                            help="If conflicts are detected, automatically suggest other parts that need updating"
                        )
                    
                    # Custom update instructions
                    custom_update_instruction = st.text_area(
                        "Custom Update Instructions (Optional)",
                        placeholder="Example: Ensure all chapters reflect the plot twist that Little Red Riding Hood is the mastermind...",
                        height=80,
                        key=f"custom_instruction_{chapter_idx}"
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"🧠 Smart Save", key=f"smart_save_{chapter_idx}", type="primary"):
                            smart_save_story_chapter_edit(
                                chapter_idx, 
                                new_plot, 
                                enable_conflict_detection, 
                                auto_suggest_updates,
                                custom_update_instruction
                            )
                    
                    with col2:
                        if st.button(f"💾 Direct Save", key=f"direct_save_{chapter_idx}"):
                            save_story_chapter_edit(chapter_idx, new_plot)
                    
                    with col3:
                        if st.button(f"❌ Cancel Edit", key=f"cancel_{chapter_idx}"):
                            st.session_state[f'edit_story_{chapter_idx}'] = False
                            st.rerun()

def show_style_consistency():
    """Show style consistency check"""
    st.markdown("#### 🎨 Style Consistency Confirmation")
    
    # Style check configuration
    col1, col2 = st.columns(2)
    
    with col1:
        check_aspects = st.multiselect("Check Aspects", [
            "Narrative Style",
            "Person Consistency", 
            "Tense Consistency",
            "Language Style",
            "Plot Style"
        ], default=["Narrative Style", "Person Consistency"])
    
    with col2:
        target_style = st.text_input("Target Style", value=st.session_state.get('current_style', 'Science Fiction Rewrite'))
    
    if st.button("🎨 Start Style Check", type="primary", use_container_width=True):
        perform_style_consistency_check(check_aspects, target_style)

def perform_coherence_analysis():
    """Execute coherence analysis"""
    try:
        with st.spinner("🔍 Analyzing inter-chapter coherence..."):
            # Use backend LLM for coherence analysis
            from src.utils.utils import generate_response, convert_json
            
            # Build analysis data
            chapters_info = []
            for i, chapter in enumerate(st.session_state.story_data):
                chapter_info = {
                    "chapter_id": chapter.get('chapter_id', f'Chapter {i+1}'),
                    "title": chapter.get('title', f'Chapter {i+1}'),
                    "plot_summary": chapter.get('plot', '')[:500] + "..." if len(chapter.get('plot', '')) > 500 else chapter.get('plot', ''),
                    "scene": chapter.get('scene', ''),
                    "characters": chapter.get('characters', [])
                }
                chapters_info.append(chapter_info)
            
            analysis_prompt = f"""
You are a professional story editor. Please analyze the coherence between the following story chapters.

Story chapters:
{json.dumps(chapters_info, ensure_ascii=False, indent=2)}

Please analyze:
1. Plot coherence: Is the plot development between chapters natural and smooth
2. Temporal coherence: Is the timeline reasonable
3. Character coherence: Are character behaviors and state changes reasonable
4. Scene coherence: Are scene transitions natural
5. Logical coherence: Is the story logic consistent

Return JSON format:
{{
    "overall_coherence": "Overall coherence score (1-10)",
    "coherence_summary": "Coherence summary",
    "chapter_analysis": [
        {{
            "chapter": "Chapter identifier",
            "coherence_score": "Coherence score (1-10)",
            "issues": ["Issues found"],
            "suggestions": ["Improvement suggestions"]
        }}
    ],
    "transition_analysis": [
        {{
            "from_chapter": "Starting chapter",
            "to_chapter": "Target chapter", 
            "transition_quality": "Transition quality score (1-10)",
            "issues": "Transition issues",
            "suggestions": "Improvement suggestions"
        }}
    ],
    "recommendations": ["Overall improvement recommendations"]
}}

Return only JSON, no other explanations.
"""
            
            start_time = time.time()
            msg = [{"role": "user", "content": analysis_prompt}]
            response = generate_response(msg)
            analysis_result = convert_json(response)
            end_time = time.time()
            
            print(f"⏱️ [Coherence Check] Analysis time: {end_time - start_time:.3f} seconds")
            
            if analysis_result and isinstance(analysis_result, dict):
                display_coherence_results(analysis_result)
            else:
                st.error("❌ Coherence analysis failed: Backend returned incorrect data format")
                
    except Exception as e:
        st.error(f"❌ Coherence analysis failed: {str(e)}")
        print(f"❌ [Coherence Check] Analysis failed: {str(e)}")

def display_coherence_results(analysis_result):
    """Show coherence analysis results"""
    st.markdown("---")
    st.markdown("## 🔍 Coherence Analysis Report")
    
    # Overall score
    overall_score = analysis_result.get('overall_coherence', 'N/A')
    coherence_summary = analysis_result.get('coherence_summary', 'No summary')
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        try:
            score_value = float(overall_score)
            if score_value >= 8:
                score_color = "🟢"
                score_level = "Excellent"
            elif score_value >= 6:
                score_color = "🟡"
                score_level = "Good"
            else:
                score_color = "🔴"
                score_level = "Needs Improvement"
        except:
            score_color = ""
            score_level = "Unknown"
        
        st.metric("Overall Coherence Score", f"{score_color} {overall_score}/10", delta=score_level)
    
    with col2:
        st.markdown("**🔍 Overall Evaluation:**")
        st.info(coherence_summary)
    
    # Chapter analysis
    chapter_analysis = analysis_result.get('chapter_analysis', [])
    if chapter_analysis:
        st.markdown("### 📖 Detailed Chapter Analysis")
        
        for analysis in chapter_analysis:
            chapter = analysis.get('chapter', 'Unknown Chapter')
            score = analysis.get('coherence_score', 'N/A')
            issues = analysis.get('issues', [])
            suggestions = analysis.get('suggestions', [])
            
            with st.expander(f"**{chapter}** - Coherence: {score}/10"):
                if issues:
                    st.markdown("**⚠️ Issues Found:**")
                    for issue in issues:
                        st.warning(f"• {issue}")
                
                if suggestions:
                    st.markdown("**💡 Improvement Suggestions:**")
                    for suggestion in suggestions:
                        st.info(f"• {suggestion}")
    
    # Transition analysis
    transition_analysis = analysis_result.get('transition_analysis', [])
    if transition_analysis:
        st.markdown("### 🔗 Chapter Transition Analysis")
        
        for transition in transition_analysis:
            from_chapter = transition.get('from_chapter', '')
            to_chapter = transition.get('to_chapter', '')
            quality = transition.get('transition_quality', 'N/A')
            issues = transition.get('issues', '')
            suggestions = transition.get('suggestions', '')
            
            with st.expander(f"**{from_chapter} → {to_chapter}** - Transition Quality: {quality}/10"):
                if issues:
                    st.warning(f"**Issues:** {issues}")
                if suggestions:
                    st.info(f"**Suggestions:** {suggestions}")
    
    # Overall recommendations
    recommendations = analysis_result.get('recommendations', [])
    if recommendations:
        st.markdown("###  Overall Improvement Suggestions")
        for rec in recommendations:
            st.info(f"• {rec}")

def perform_style_consistency_check(check_aspects, target_style):
    """Execute style consistency check"""
    try:
        with st.spinner("🔍 Checking style consistency..."):
            from src.utils.utils import generate_response, convert_json
            
            # Build check data
            story_content = []
            for i, chapter in enumerate(st.session_state.story_data):
                content = {
                    "chapter": chapter.get('title', f'Chapter {i+1}'),
                    "plot": chapter.get('plot', '')[:800] + "..." if len(chapter.get('plot', '')) > 800 else chapter.get('plot', '')
                }
                story_content.append(content)
            
            style_prompt = f"""
You are a professional literary editor. Please check the style consistency of the following story.

Target style: {target_style}
Check aspects: {', '.join(check_aspects)}

Story content:
{json.dumps(story_content, ensure_ascii=False, indent=2)}

Please analyze style consistency and return in JSON format:
{{
    "overall_consistency": "Overall consistency score (1-10)",
    "consistency_summary": "Consistency summary",
    "aspect_analysis": {{
        "Narrative Style": {{"score": "score", "issues": ["issues"], "suggestions": ["suggestions"]}},
        "Person Consistency": {{"score": "score", "issues": ["issues"], "suggestions": ["suggestions"]}},
        "Tense Consistency": {{"score": "score", "issues": ["issues"], "suggestions": ["suggestions"]}},
        "Language Style": {{"score": "score", "issues": ["issues"], "suggestions": ["suggestions"]}},
        "Plot Style": {{"score": "score", "issues": ["issues"], "suggestions": ["suggestions"]}}
    }},
    "chapter_consistency": [
        {{
            "chapter": "chapter_name",
            "consistency_score": "Consistency score (1-10)",
            "style_issues": ["style_issues"],
            "suggestions": ["suggestions"]
        }}
    ],
    "recommendations": ["overall_recommendations"]
}}

Return only JSON, no other explanations.
"""
            
            start_time = time.time()
            msg = [{"role": "user", "content": style_prompt}]
            response = generate_response(msg)
            analysis_result = convert_json(response)
            end_time = time.time()
            
            print(f"⏱️ [Style Check] Analysis time: {end_time - start_time:.3f}s")
            
            if analysis_result and isinstance(analysis_result, dict):
                display_style_consistency_results(analysis_result)
            else:
                st.error("❌ Style check failed: Backend returned incorrect data format")
                
    except Exception as e:
        st.error(f"❌ Style check failed: {str(e)}")
        print(f"🔍 [Style Check] Check failed: {str(e)}")

def display_style_consistency_results(analysis_result):
    """Show style consistency check results"""
    st.markdown("---")
    st.markdown("## 📊 Style Consistency Check Report")
    
    # Overall score
    overall_score = analysis_result.get('overall_consistency', 'N/A')
    consistency_summary = analysis_result.get('consistency_summary', 'No summary')
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        try:
            score_value = float(overall_score)
            if score_value >= 8:
                score_color = "🟢"
                score_level = "Excellent"
            elif score_value >= 6:
                score_color = "🟡"
                score_level = "Good"
            else:
                score_color = "🔴"
                score_level = "Needs Improvement"
        except:
            score_color = ""
            score_level = "Unknown"
        
        st.metric("Overall Consistency Score", f"{score_color} {overall_score}/10", delta=score_level)
    
    with col2:
        st.markdown("**🔍 Style Evaluation:**")
        st.info(consistency_summary)
    
    # Aspect analysis
    aspect_analysis = analysis_result.get('aspect_analysis', {})
    if aspect_analysis:
        st.markdown("### 📊 Aspect Analysis")
        
        for aspect, data in aspect_analysis.items():
            score = data.get('score', 'N/A')
            issues = data.get('issues', [])
            suggestions = data.get('suggestions', [])
            
            with st.expander(f"**{aspect}** - Score: {score}/10"):
                if issues:
                    st.markdown("**⚠️ Issues Found:**")
                    for issue in issues:
                        st.warning(f"• {issue}")
                
                if suggestions:
                    st.markdown("**💡 Improvement Suggestions:**")
                    for suggestion in suggestions:
                        st.info(f"• {suggestion}")
    
    # Chapter consistency
    chapter_consistency = analysis_result.get('chapter_consistency', [])
    if chapter_consistency:
        st.markdown("### 📖 Chapter Style Analysis")
        
        for analysis in chapter_consistency:
            chapter = analysis.get('chapter', 'Unknown Chapter')
            score = analysis.get('consistency_score', 'N/A')
            issues = analysis.get('style_issues', [])
            suggestions = analysis.get('suggestions', [])
            
            with st.expander(f"**{chapter}** - Style Consistency: {score}/10"):
                if issues:
                    st.markdown("**⚠️ Style Issues:**")
                    for issue in issues:
                        st.warning(f"• {issue}")
                
                if suggestions:
                    st.markdown("**💡 Improvement Suggestions:**")
                    for suggestion in suggestions:
                        st.info(f"• {suggestion}")

def regenerate_single_story_chapter(chapter_idx):
    """Regenerate single story chapter"""
    try:
        chapter = st.session_state.story_data[chapter_idx]
        outline_chapter = st.session_state.outline_data[chapter_idx] if chapter_idx < len(st.session_state.outline_data) else None
        
        if not outline_chapter:
            st.error("❌ Cannot find corresponding outline chapter")
            return
        
        with st.spinner(f"🔄 Regenerating Chapter {chapter_idx+1}..."):
            start_time = time.time()
            
            print(f"📝 [Story Edit] Regenerating Chapter {chapter_idx+1}: {outline_chapter.get('title', 'Unknown Title')}")
            
            # Save state before regeneration to history
            old_story_data = st.session_state.story_data.copy()
            save_story_to_history(f"Regenerate Chapter {chapter_idx+1}", old_story_data)
            
            # Call backend to regenerate single chapter
            from src.generation.expand_story import expand_story_v1
            
            # Only pass current chapter's outline and characters
            single_chapter_result = expand_story_v1(
                [outline_chapter], 
                st.session_state.characters_data,
                custom_instruction="Please recreate this chapter, ensuring fresh content that fits the overall story style."
            )
            
            end_time = time.time()
            
            if single_chapter_result and len(single_chapter_result) > 0:
                # Update chapter data
                new_chapter = single_chapter_result[0]
                new_chapter.setdefault("chapter_id", outline_chapter["chapter_id"])
                new_chapter.setdefault("title", outline_chapter["title"])
                
                st.session_state.story_data[chapter_idx] = new_chapter
                
                st.success(f"✅ Chapter {chapter_idx+1} regeneration completed")
                st.info(f"⏱️ Generation time: {end_time - start_time:.3f}s")
                
                print(f"✅ [Story Edit] Chapter {chapter_idx+1} regeneration completed")
                st.rerun()
            else:
                st.error("❌ Regeneration failed: Backend returned invalid data")
                
    except Exception as e:
        st.error(f"❌ Failed to regenerate Chapter {chapter_idx+1}: {str(e)}")
        print(f"❌ [Story Edit] Regeneration failed: {str(e)}")

def save_story_chapter_edit(chapter_idx, new_plot):
    """Save chapter edit"""
    try:
        # Save state before editing to history
        old_story_data = st.session_state.story_data.copy()
        save_story_to_history(f"Edit Chapter {chapter_idx+1}", old_story_data)
        
        # Update chapter content
        st.session_state.story_data[chapter_idx]['plot'] = new_plot
        
        # Clear edit state
        st.session_state[f'edit_story_{chapter_idx}'] = False
        
        st.success(f"✅ Chapter {chapter_idx+1} changes saved")
        print(f"✅ [Story Edit] Saved Chapter {chapter_idx+1} changes: {len(new_plot)} characters")
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Failed to save changes: {str(e)}")
        print(f"❌ [Story Edit] Failed to save changes: {str(e)}")

def smart_save_story_chapter_edit(chapter_idx, new_plot, enable_conflict_detection, auto_suggest_updates, custom_instruction=""):
    """Smart save chapter edit - includes conflict detection and cascaded update suggestions"""
    try:
        with st.spinner("🔍 Performing smart analysis..."):
            # Save state before editing to history
            old_story_data = st.session_state.story_data.copy()
            old_plot = st.session_state.story_data[chapter_idx]['plot']
            
            # First perform conflict detection
            conflicts_detected = False
            update_suggestions = {}
            
            if enable_conflict_detection:
                conflicts_detected, update_suggestions = detect_plot_conflicts_and_suggest_updates(
                    chapter_idx, old_plot, new_plot, custom_instruction
                )
            
            print(f"🔍 [Smart Save] Conflict detection results: conflicts_detected={conflicts_detected}, auto_suggest_updates={auto_suggest_updates}")
            print(f"🔍 [Smart Save] Update suggestions: {update_suggestions}")
            
            # Save conflict detection results to session state to ensure state persistence after button clicks
            smart_state_key = f'smart_conflict_state_{chapter_idx}'
            if conflicts_detected and auto_suggest_updates:
                st.session_state[smart_state_key] = {
                    'conflicts_detected': True,
                    'update_suggestions': update_suggestions,
                    'new_plot': new_plot,
                    'custom_instruction': custom_instruction,
                    'old_story_data': old_story_data
                }
            
            # Check if there is saved conflict state (for rerun after button clicks)
            has_smart_state = smart_state_key in st.session_state
            smart_state = st.session_state.get(smart_state_key, {})
            
            print(f"🔍 [Smart Save] State check: has_smart_state={has_smart_state}")
            
            # Display conflict handling interface
            if (conflicts_detected and auto_suggest_updates) or has_smart_state:
                print(f"🔄 [Smart Save] Entering conflict handling branch")
                
                # Use saved state data or current data
                display_suggestions = smart_state.get('update_suggestions', update_suggestions)
                display_new_plot = smart_state.get('new_plot', new_plot)
                display_custom_instruction = smart_state.get('custom_instruction', custom_instruction)
                display_old_story_data = smart_state.get('old_story_data', old_story_data)
                
                print(f"🔍 [Smart Save] Suggestion data type used: {type(display_suggestions)}")
                
                # Display conflict detection results and update suggestions
                st.markdown("---")
                st.markdown("## 🚨 Smart Conflict Detection Results")
                
                # Display detected conflicts
                if display_suggestions.get('conflicts'):
                    st.markdown("### ⚠️ Detected Conflicts:")
                    for conflict in display_suggestions['conflicts']:
                        st.warning(f"• {conflict}")
                
                # Display update suggestions
                if display_suggestions.get('suggestions'):
                    st.markdown("### 💡 Suggested Updates:")
                    
                    # Outline update suggestions
                    if display_suggestions['suggestions'].get('outline_updates'):
                        st.markdown("**📚 Outline Update Suggestions:**")
                        for update in display_suggestions['suggestions']['outline_updates']:
                            st.info(f"• {update}")
                    
                    # Character update suggestions
                    if display_suggestions['suggestions'].get('character_updates'):
                        st.markdown("**👥 Character Update Suggestions:**")
                        for update in display_suggestions['suggestions']['character_updates']:
                            st.info(f"• {update}")
                    
                    # Other chapter update suggestions
                    if display_suggestions['suggestions'].get('other_chapters'):
                        st.markdown("**📖 Other Chapter Update Suggestions:**")
                        for chapter_update in display_suggestions['suggestions']['other_chapters']:
                            chapter_num = chapter_update.get('chapter', 'Unknown')
                            suggestion = chapter_update.get('suggestion', '')
                            st.info(f"• Chapter {chapter_num}: {suggestion}")
                

                
                # Provide user choices
                st.markdown("---")
                st.markdown("### 🤔 How would you like to proceed?")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🚀 Execute Smart Updates", type="primary", key=f"execute_smart_update_{chapter_idx}"):
                        print(f"🔴🔴🔴 [Button Click] Execute smart updates button clicked! Chapter: {chapter_idx}")
                        print(f"🔴 [Button Click] Update suggestions type: {type(display_suggestions)}")
                        print(f"🔴 [Button Click] Update suggestions content: {display_suggestions}")
                        print(f"🔴 [Button Click] Custom instruction: {display_custom_instruction}")
                        
                        # Execute cascade updates
                        execute_cascade_updates(chapter_idx, display_new_plot, display_suggestions, display_custom_instruction)
                        
                        # Clear smart state
                        if smart_state_key in st.session_state:
                            del st.session_state[smart_state_key]
                            print(f"🧹 [Button Click] Smart state cleared: {smart_state_key}")
                        
                        return
                
                with col2:
                    if st.button("💾 Save Current Chapter Only", key=f"save_current_only_{chapter_idx}"):
                        save_story_to_history(f"Edit Chapter {chapter_idx+1} (ignore conflicts)", display_old_story_data)
                        st.session_state.story_data[chapter_idx]['plot'] = display_new_plot
                        st.session_state[f'edit_story_{chapter_idx}'] = False
                        
                        # Clear smart state
                        if smart_state_key in st.session_state:
                            del st.session_state[smart_state_key]
                        
                        st.success(f"✅ Chapter {chapter_idx+1} saved (conflicts not resolved)")
                        st.rerun()
                
                with col3:
                    if st.button("❌ Cancel Changes", key=f"cancel_smart_save_{chapter_idx}"):
                        st.session_state[f'edit_story_{chapter_idx}'] = False
                        
                        # Clear smart state
                        if smart_state_key in st.session_state:
                            del st.session_state[smart_state_key]
                        
                        st.info("ℹ️ Changes cancelled")
                        st.rerun()
                
            
            # Suggestions management feature (always display)
            st.markdown("---")
            st.markdown("### 📊 Suggestions Management")
            
            col_save1, col_save2, col_save3, col_save4 = st.columns(4)
            
            # with col_save1:
            #     if st.button("💾 Save Analysis Suggestions", key=f"save_suggestions_{chapter_idx}"):
            #         print(f"🔘 [UI] User clicked save suggestions button, Chapter {chapter_idx+1}")
            #         save_conflict_suggestions(chapter_idx, update_suggestions, new_plot, custom_instruction)
            with col_save1:
                if st.button("💾 Save Analysis Suggestions", key=f"save_suggestions_{chapter_idx}"):
                    print(f"🔘 [UI] User clicked save suggestions button, chapter {chapter_idx+1}")
                    
                    # Display saving process
                    with st.spinner("💾 Saving suggestions..."):
                        success = save_conflict_suggestions(chapter_idx, update_suggestions, new_plot, custom_instruction)
                    
                    if success:
                        # Post-save processing
                        st.success("✅ Suggestions saved successfully!")
                        st.balloons()  # Add celebration effect
                        
                        # Optional: short delay before refresh to let user see results
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Suggestions save failed, please check error messages")
                        st.info("ℹ️ Tip: Please check file permissions and storage space")            
            with col_save2:
                if st.button("📥 Export Suggestions File", key=f"export_suggestions_{chapter_idx}"):
                    print(f"🔘 [UI] User clicked export suggestions button, chapter {chapter_idx+1}")
                    export_suggestions_file(chapter_idx, update_suggestions, new_plot, custom_instruction)
            
            with col_save3:
                if st.button("📁 Load Saved Suggestions", key=f"load_suggestions_{chapter_idx}"):
                    st.session_state[f'show_suggestions_loader_{chapter_idx}'] = True
                    st.rerun()
            
            with col_save4:
                if st.button("📜 View Suggestions History", key=f"show_suggestions_history_{chapter_idx}"):
                    st.session_state[f'show_suggestions_history_{chapter_idx}'] = True
                    st.rerun()
            
            # Suggestions loader
            if st.session_state.get(f'show_suggestions_loader_{chapter_idx}', False):
                show_suggestions_loader(chapter_idx, new_plot, custom_instruction)
                return
            
            # Suggestions history viewer
            if st.session_state.get(f'show_suggestions_history_{chapter_idx}', False):
                show_suggestions_history_for_chapter(chapter_idx, new_plot, custom_instruction)
                return
            
            if not (conflicts_detected and auto_suggest_updates):
                # No conflicts or no need for auto suggestions, provide save option
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("💾 Save Current Chapter", type="primary", key=f"save_final_{chapter_idx}"):
                        save_story_to_history(f"Smart Edit Chapter {chapter_idx+1}", old_story_data)
                        st.session_state.story_data[chapter_idx]['plot'] = new_plot
                        st.session_state[f'edit_story_{chapter_idx}'] = False
                        
                        if not conflicts_detected:
                            st.success(f"✅ Chapter {chapter_idx+1} changes saved (no conflicts detected)")
                        else:
                            st.success(f"✅ Chapter {chapter_idx+1} changes saved")
                        
                        print(f"✅ [Smart Story Edit] Saved Chapter {chapter_idx+1} changes: {len(new_plot)} characters")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Cancel Changes", key=f"cancel_final_{chapter_idx}"):
                        st.session_state[f'edit_story_{chapter_idx}'] = False
                        st.info("ℹ️ Changes cancelled")
                        st.rerun()
                
    except Exception as e:
        st.error(f"❌ Smart save failed: {str(e)}")
        print(f"❌ [Smart Story Edit] Smart save failed: {str(e)}")

def detect_plot_conflicts_and_suggest_updates(chapter_idx, old_plot, new_plot, custom_instruction=""):
    """Enhanced conflict detection - integrating professional analysis tools"""
    try:
        print(f"🔍 [Enhanced Conflict Detection] Starting multi-dimensional analysis of Chapter {chapter_idx+1} changes")
        
        # 1. Basic semantic conflict detection (original method)
        basic_conflicts = detect_basic_semantic_conflicts(chapter_idx, old_plot, new_plot, custom_instruction)
        
        # 2. Event consistency detection (using story_evaluator)
        event_conflicts = detect_event_consistency_conflicts(chapter_idx, old_plot, new_plot)
        
        # 3. Coherence detection (using hred_coherence_evaluator)
        coherence_conflicts = detect_coherence_conflicts(chapter_idx, old_plot, new_plot)
        
        # 4. Emotional arc detection (using emotional_arc_analyzer)
        emotional_conflicts = detect_emotional_arc_conflicts(chapter_idx, old_plot, new_plot)
        
        # 5. Character state consistency detection (using character_state_tracker)
        character_state_conflicts = detect_character_state_conflicts(chapter_idx, old_plot, new_plot)
        
        # Integrate all detection results
        integrated_result = integrate_conflict_analysis_results(
            basic_conflicts, event_conflicts, coherence_conflicts, 
            emotional_conflicts, character_state_conflicts
        )
        
        print(f"✅ [Enhanced Conflict Detection] Multi-dimensional analysis completed")
        
        has_conflicts = integrated_result.get('has_conflicts', False)
        print(f"🔍 [Enhanced Conflict Detection] Final result: has_conflicts={has_conflicts}")
        print(f"🔍 [Enhanced Conflict Detection] Returned data: {integrated_result}")
        return has_conflicts, integrated_result
            
    except Exception as e:
        print(f"❌ [Enhanced Conflict Detection] Detection failed: {str(e)}")
        # Fall back to basic detection
        return detect_basic_semantic_conflicts(chapter_idx, old_plot, new_plot, custom_instruction)

def detect_basic_semantic_conflicts(chapter_idx, old_plot, new_plot, custom_instruction=""):
    """Basic semantic conflict detection (original method)"""
    try:
        from src.utils.utils import generate_response, convert_json
        
        print(f"  📝 [Basic Detection] Semantic conflict analysis")
        
        # Build analysis data
        current_outline = st.session_state.outline_data
        current_characters = st.session_state.characters_data
        current_story = st.session_state.story_data
        
        # Build conflict detection prompt
        analysis_prompt = f"""
You are a professional story editor. The user has modified the content of Chapter {chapter_idx+1} of the story. Please analyze whether this modification will conflict with other parts and provide update suggestions.

**Original Chapter Content:**
{old_plot}

**Modified Chapter Content:**
{new_plot}

**Current Outline:**
{json.dumps(current_outline, ensure_ascii=False, indent=2)}

**Current Character Settings:**
{json.dumps(current_characters, ensure_ascii=False, indent=2)}

**Other Chapter Summaries:**
{json.dumps([{"chapter": i+1, "title": ch.get('title', ''), "plot_summary": ch.get('plot', '')[:200]} for i, ch in enumerate(current_story) if i != chapter_idx], ensure_ascii=False, indent=2)}

**User Custom Instructions:**
{custom_instruction if custom_instruction else "None"}

Please analyze potential conflicts in the following aspects:
1. **Character Setting Conflicts**: Whether the modification changes the basic attributes, motivations or relationships of characters
2. **Plot Logic Conflicts**: Whether the modification contradicts the plot development in other chapters
3. **Outline Consistency**: Whether the modification deviates from the original outline settings
4. **Timeline Conflicts**: Whether the modification affects the story's timeline or causal relationships
5. **World-building Conflicts**: Whether the modification changes the basic settings or rules of the story

Return in JSON format:
{{
    "has_conflicts": true/false,
    "conflicts": [
        "specific conflict descriptions"
    ],
    "suggestions": {{
        "outline_updates": [
            "specific outline modification suggestions needed"
        ],
        "character_updates": [
            "specific character setting modification suggestions needed"
        ],
        "other_chapters": [
            {{
                "chapter": "chapter_number",
                "suggestion": "specific modification suggestion needed for this chapter"
            }}
        ]
    }},
    "severity": "low/medium/high",
    "summary": "conflict detection summary",
    "analysis_type": "basic_semantic"
}}

Return only JSON, no other explanations.
"""
        
        # Call backend analysis
        msg = [{"role": "user", "content": analysis_prompt}]
        response = generate_response(msg)
        analysis_result = convert_json(response)
        
        if analysis_result and isinstance(analysis_result, dict):
            has_conflicts = analysis_result.get('has_conflicts', False)
            return has_conflicts, analysis_result
        else:
            return False, {}
            
    except Exception as e:
        print(f"❌ [Basic Detection] Semantic analysis failed: {str(e)}")
        return False, {}

def detect_event_consistency_conflicts(chapter_idx, old_plot, new_plot):
    """Event consistency conflict detection - using story_evaluator"""
    try:
        print(f"   📅 [Event Detection] Event consistency analysis")
        
        # Create temporary story data for event extraction
        temp_story_old = st.session_state.story_data.copy()
        temp_story_new = st.session_state.story_data.copy()
        temp_story_new[chapter_idx]['plot'] = new_plot
        
        # Use story_evaluator to extract events
        from src.analysis.story_evaluator import extract_events_no_hallucination
        
        # Extract events before and after modification
        events_old = extract_events_no_hallucination(temp_story_old)
        events_new = extract_events_no_hallucination(temp_story_new)
        
        # Analyze event changes
        event_conflicts = analyze_event_changes(events_old, events_new, chapter_idx)
        
        return event_conflicts
        
    except Exception as e:
        print(f"❌ [Event Detection] Event analysis failed: {str(e)}")
        return {"has_conflicts": False, "analysis_type": "event_consistency", "error": str(e)}

def detect_coherence_conflicts(chapter_idx, old_plot, new_plot):
    """Coherence conflict detection - using hred_coherence_evaluator"""
    try:
        print(f"  🔗 [Coherence Detection] Semantic coherence analysis")
        
        # Create temporary story data
        temp_story_old = st.session_state.story_data.copy()
        temp_story_new = st.session_state.story_data.copy()
        temp_story_new[chapter_idx]['plot'] = new_plot
        
        # Use HRED coherence evaluator
        from src.analysis.hred_coherence_evaluator import HREDCoherenceEvaluator
        
        evaluator = HREDCoherenceEvaluator()
        
        # Calculate coherence scores before and after modification
        coherence_old = evaluator.evaluate_story_coherence(temp_story_old)
        coherence_new = evaluator.evaluate_story_coherence(temp_story_new)
        
        # Analyze coherence changes
        coherence_conflicts = analyze_coherence_changes(coherence_old, coherence_new, chapter_idx)
        
        return coherence_conflicts
        
    except Exception as e:
        print(f"❌ [Coherence Detection] Coherence analysis failed: {str(e)}")
        return {"has_conflicts": False, "analysis_type": "coherence", "error": str(e)}

def detect_emotional_arc_conflicts(chapter_idx, old_plot, new_plot):
    """Emotional arc conflict detection - using emotional_arc_analyzer"""
    try:
        print(f"  💝 [Emotion Detection] Emotional arc analysis")
        
        # Create temporary story data
        temp_story_old = st.session_state.story_data.copy()
        temp_story_new = st.session_state.story_data.copy()
        temp_story_new[chapter_idx]['plot'] = new_plot
        
        # Use emotional arc analyzer
        from src.analysis.emotional_arc_analyzer import DualMethodEmotionalAnalyzer
        
        analyzer = DualMethodEmotionalAnalyzer()
        
        # Convert data format to fit emotional analyzer
        def convert_story_format(story_data):
            converted = []
            for i, chapter in enumerate(story_data):
                converted.append({
                    'chapter_num': i + 1,
                    'title': chapter.get('title', f'Chapter {i+1}'),
                    'content': chapter.get('plot', '')
                })
            return converted
        
        # Analyze emotional arcs before and after modification
        emotions_old = analyzer.analyze_story_dual_method(convert_story_format(temp_story_old))
        emotions_new = analyzer.analyze_story_dual_method(convert_story_format(temp_story_new))
        
        # Analyze emotional changes
        emotional_conflicts = analyze_emotional_changes(emotions_old, emotions_new, chapter_idx)
        
        return emotional_conflicts
        
    except Exception as e:
        print(f"❌ [Emotion Detection] Emotional analysis failed: {str(e)}")
        return {"has_conflicts": False, "analysis_type": "emotional_arc", "error": str(e)}

def detect_character_state_conflicts(chapter_idx, old_plot, new_plot):
    """Character state consistency detection - using character_state_tracker"""
    try:
        print(f"  👥 [Character State Detection] Character state consistency analysis")
        
        # Dialogue data is needed here, skip if not available
        if not hasattr(st.session_state, 'dialogue_data') or not st.session_state.get('dialogue_data'):
            return {"has_conflicts": False, "analysis_type": "character_state", "skipped": "No dialogue data"}
        
        # Use character state tracker
        from src.analysis.character_state_tracker import extract_character_state_timeline
        
        # Analyze character state changes
        character_conflicts = analyze_character_state_changes(chapter_idx, old_plot, new_plot)
        
        return character_conflicts
        
    except Exception as e:
        print(f"❌ [Character State Detection] Character state analysis failed: {str(e)}")
        return {"has_conflicts": False, "analysis_type": "character_state", "error": str(e)}

def analyze_event_changes(events_old, events_new, chapter_idx):
    """Analyze event changes"""
    try:
        # Extract event descriptions for comparison
        events_old_desc = [e.get('event', '') for e in events_old if isinstance(e, dict)]
        events_new_desc = [e.get('event', '') for e in events_new if isinstance(e, dict)]
        
        # Find added, removed, and modified events
        added_events = [e for e in events_new_desc if e not in events_old_desc]
        removed_events = [e for e in events_old_desc if e not in events_new_desc]
        
        has_conflicts = len(added_events) > 0 or len(removed_events) > 0
        
        conflicts = []
        if added_events:
            conflicts.append(f"Added events: {', '.join(added_events[:3])}{'...' if len(added_events) > 3 else ''}")
        if removed_events:
            conflicts.append(f"Removed events: {', '.join(removed_events[:3])}{'...' if len(removed_events) > 3 else ''}")
        
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
    """Analyze coherence changes"""
    try:
        # Compare coherence scores
        old_score = coherence_old.get('overall_coherence_score', 0)
        new_score = coherence_new.get('overall_coherence_score', 0)
        
        score_change = new_score - old_score
        threshold = 0.1  # Coherence change threshold
        
        has_conflicts = score_change < -threshold
        
        conflicts = []
        if has_conflicts:
            conflicts.append(f"Coherence decline: {old_score:.3f} → {new_score:.3f} (decreased by {abs(score_change):.3f})")
        
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
    """Analyze emotional arc changes"""
    try:
        # Check if analysis results contain errors
        if isinstance(emotions_old, dict) and "error" in emotions_old:
            return {"has_conflicts": False, "analysis_type": "emotional_arc", "error": emotions_old["error"]}
        
        if isinstance(emotions_new, dict) and "error" in emotions_new:
            return {"has_conflicts": False, "analysis_type": "emotional_arc", "error": emotions_new["error"]}
        
        # Get RoBERTa scores (main method)
        old_scores = []
        new_scores = []
        
        # Extract scores from chapter_analysis
        if isinstance(emotions_old, dict) and "chapter_analysis" in emotions_old:
            old_scores = [ch.get('roberta_score', 0) for ch in emotions_old['chapter_analysis']]
        
        if isinstance(emotions_new, dict) and "chapter_analysis" in emotions_new:
            new_scores = [ch.get('roberta_score', 0) for ch in emotions_new['chapter_analysis']]
        
        if len(old_scores) != len(new_scores):
            return {"has_conflicts": True, "analysis_type": "emotional_arc", 
                   "conflicts": ["Emotional arc length has changed"], "severity": "medium"}
        
        # Calculate emotional change amplitude for specified chapter
        if len(old_scores) > chapter_idx and len(new_scores) > chapter_idx:
            old_emotion = old_scores[chapter_idx]
            new_emotion = new_scores[chapter_idx]
            
            emotion_change = abs(new_emotion - old_emotion)
            threshold = 0.3  # Emotional change threshold
            
            has_conflicts = emotion_change > threshold
            
            conflicts = []
            if has_conflicts:
                conflicts.append(f"Chapter {chapter_idx+1} dramatic emotional change: {old_emotion:.3f} → {new_emotion:.3f}")
            
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
        print(f"💝 [Emotional Analysis] Failed to analyze emotional changes: {str(e)}")
        return {"has_conflicts": False, "analysis_type": "emotional_arc", "error": str(e)}

def analyze_character_state_changes(chapter_idx, old_plot, new_plot):
    """Analyze character state changes"""
    try:
        # Simple character state change detection
        # Can further integrate character_state_tracker functionality here
        
        # Extract character names
        character_names = [char.get('name', '') for char in st.session_state.characters_data]
        
        conflicts = []
        for char_name in character_names:
            if char_name in old_plot and char_name in new_plot:
                # Check character context changes before and after modification
                old_context = extract_character_context(old_plot, char_name)
                new_context = extract_character_context(new_plot, char_name)
                
                if old_context != new_context:
                    conflicts.append(f"Character {char_name}'s behavior state has changed")
        
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
    """Extract character context from text"""
    # Simple implementation: find text before and after character name
    import re
    pattern = f".{{0,50}}{re.escape(character_name)}.{{0,50}}"
    matches = re.findall(pattern, text, re.IGNORECASE)
    return ' '.join(matches)

def integrate_conflict_analysis_results(basic_conflicts, event_conflicts, coherence_conflicts, 
                                      emotional_conflicts, character_state_conflicts):
    """Integrate all conflict analysis results"""
    try:
        # Collect all conflicts
        all_conflicts = []
        all_suggestions = {"outline_updates": [], "character_updates": [], "other_chapters": []}
        
        # Calculate comprehensive severity
        severity_scores = {"low": 1, "medium": 2, "high": 3}
        max_severity = 0
        
        # Process various analysis results
        analysis_results = [
            ("Basic Semantic", basic_conflicts[1] if isinstance(basic_conflicts, tuple) else basic_conflicts),
            ("Event Consistency", event_conflicts),
            ("Coherence", coherence_conflicts), 
            ("Emotional Arc", emotional_conflicts),
            ("Character State", character_state_conflicts)
        ]
        
        for analysis_name, result in analysis_results:
            if isinstance(result, dict) and result.get('has_conflicts', False):
                # Add conflict descriptions
                conflicts = result.get('conflicts', [])
                for conflict in conflicts:
                    all_conflicts.append(f"[{analysis_name}] {conflict}")
                
                # Update severity
                severity = result.get('severity', 'low')
                max_severity = max(max_severity, severity_scores.get(severity, 1))
                
                # Merge suggestions
                if 'suggestions' in result:
                    suggestions = result['suggestions']
                    if isinstance(suggestions, dict):
                        for key in all_suggestions:
                            if key in suggestions:
                                all_suggestions[key].extend(suggestions[key])
        
        # Determine final severity
        severity_map = {1: "low", 2: "medium", 3: "high"}
        final_severity = severity_map[max_severity]
        
        # Generate comprehensive report
        has_conflicts = len(all_conflicts) > 0
        
        summary = f"Multi-dimensional analysis completed, detected {len(all_conflicts)} potential conflicts"
        if has_conflicts:
            summary += f", severity: {final_severity}"
        
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
        print(f"🔗 [Result Integration] Failed to integrate analysis results: {str(e)}")
        # Fall back to basic results
        if isinstance(basic_conflicts, tuple):
            return basic_conflicts[1]
        else:
            return {"has_conflicts": False, "error": f"Integration failed: {str(e)}"}

def execute_cascade_updates(chapter_idx, new_plot, update_suggestions, custom_instruction=""):
    """Execute cascade updates"""
    print(f"🔗 [Cascade Update] Function called! Chapter: {chapter_idx}, instruction: {custom_instruction[:50] if custom_instruction else 'None'}")
    print(f"🔗 [Cascade Update] Received update suggestions: {type(update_suggestions)} - {update_suggestions}")
    
    try:
        with st.spinner("🚀 Executing smart updates..."):
            print(f"🔗 [Cascade Update] Starting smart update execution")
            print(f"🔗 [Cascade Update] Update suggestion data structure: {update_suggestions}")
            
            # Save complete state before updates
            old_story_data = st.session_state.story_data.copy()
            old_outline_data = st.session_state.outline_data.copy()
            old_characters_data = st.session_state.characters_data.copy()
            
            save_story_to_history(f"State before smart update (Chapter {chapter_idx+1})", old_story_data)
            
            update_results = {
                'story_updated': False,
                'outline_updated': False,
                'characters_updated': False,
                'other_chapters_updated': []
            }
            
            # 1. First update current chapter
            st.session_state.story_data[chapter_idx]['plot'] = new_plot
            update_results['story_updated'] = True
            
            # 2. Update other chapters (if there are suggestions)
            other_chapter_updates = update_suggestions.get('other_chapters', [])
            if not other_chapter_updates and 'suggestions' in update_suggestions:
                other_chapter_updates = update_suggestions['suggestions'].get('other_chapters', [])
            
            if other_chapter_updates:
                st.info(f"🔄 Updating related chapters... (Total {len(other_chapter_updates)} chapters)")
                print(f"🔗 [Cascade Update] Chapters that need update: {other_chapter_updates}")
                
                for i, chapter_update in enumerate(other_chapter_updates):
                    try:
                        print(f"🔄 [Cascade Update] Processing Chapter {i+1} update: {chapter_update}")
                        
                        # Parse chapter number
                        chapter_str = str(chapter_update.get('chapter', '0'))
                        # Extract numbers (may be "Chapter 1" or "Chapter 1" format)
                        import re
                        chapter_match = re.search(r'\d+', chapter_str)
                        if chapter_match:
                            target_chapter = int(chapter_match.group()) - 1
                        else:
                            print(f"❌ [Cascade Update] Unable to parse chapter number: {chapter_str}")
                            continue
                        
                        print(f"📍 [Cascade Update] Target chapter: {target_chapter+1} (index {target_chapter})")
                        
                        if 0 <= target_chapter < len(st.session_state.story_data) and target_chapter != chapter_idx:
                            suggestion = chapter_update.get('suggestion', '')
                            print(f"📝 [Cascade Update] Update suggestion: {suggestion[:100]}...")
                            
                            # Display update progress
                            with st.spinner(f"🔄 Regenerating Chapter {target_chapter+1}..."):
                                # Use LLM to regenerate this chapter
                                updated_chapter = update_single_chapter_with_context(
                                    target_chapter, suggestion, new_plot, custom_instruction
                                )
                                
                                if updated_chapter:
                                    st.session_state.story_data[target_chapter] = updated_chapter
                                    update_results['other_chapters_updated'].append(target_chapter + 1)
                                    print(f"✅ [Cascade Update] Chapter {target_chapter+1} update successful")
                                    st.success(f"✅ Chapter {target_chapter+1} has been regenerated")
                                else:
                                    print(f"❌ [Cascade Update] Chapter {target_chapter+1} update failed: no valid content returned")
                                    st.warning(f"⚠️ Chapter {target_chapter+1} update failed")
                        else:
                            print(f"⚠️ [Cascade Update] Skipping invalid chapter: {target_chapter+1}")
                                
                    except Exception as e:
                        print(f"❌ [Cascade Update] Chapter update failed: {str(e)}")
                        st.error(f"❌ Error updating chapter: {str(e)}")
                
                print(f"✅ [Cascade Update] Chapter updates completed, successful updates: {update_results['other_chapters_updated']}")
            
            # 3. Update character settings (if there are suggestions)
            character_updates = update_suggestions.get('character_updates', [])
            if not character_updates and 'suggestions' in update_suggestions:
                character_updates = update_suggestions['suggestions'].get('character_updates', [])
            
            if character_updates:
                st.info("👥 Updating character settings...")
                
                updated_characters = update_characters_with_context(character_updates, new_plot, custom_instruction)
                if updated_characters:
                    save_characters_to_history(f"Smart Character Update (Chapter {chapter_idx+1} Edit)", st.session_state.characters_data.copy())
                    st.session_state.characters_data = updated_characters
                    update_results['characters_updated'] = True
            
            # 4. Update outline (if there are suggestions)
            outline_updates = update_suggestions.get('outline_updates', [])
            if not outline_updates and 'suggestions' in update_suggestions:
                outline_updates = update_suggestions['suggestions'].get('outline_updates', [])
            
            if outline_updates:
                st.info("📚 Updating outline...")
                
                updated_outline = update_outline_with_context(outline_updates, new_plot, custom_instruction)
                if updated_outline:
                    save_to_history(f"Smart Outline Update (Chapter {chapter_idx+1} Edit)", st.session_state.outline_data.copy())
                    st.session_state.outline_data = updated_outline
                    update_results['outline_updated'] = True
            
            # Clear editing state
            st.session_state[f'edit_story_{chapter_idx}'] = False
            
            # Display update results
            st.markdown("---")
            st.markdown("## ✅ Smart Update Completed")
            
            st.success(f"✅ Chapter {chapter_idx+1} has been updated")
            
            if update_results['other_chapters_updated']:
                updated_chapters_str = ', '.join([f"Chapter {ch}" for ch in update_results['other_chapters_updated']])
                st.success(f"🔗 Related chapters updated: {updated_chapters_str}")
            
            if update_results['characters_updated']:
                st.success("👥 Character settings updated")
            
            if update_results['outline_updated']:
                st.success("📋 Outline updated")
            
            print(f"🎆 [Cascade Update] Smart update completed: {update_results}")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Smart update execution failed: {str(e)}")
        print(f"❌ [Cascade Update] Execution failed: {str(e)}")

def update_single_chapter_with_context(chapter_idx, suggestion, reference_plot, custom_instruction=""):
    """Update single chapter based on context"""
    try:
        from src.generation.expand_story import expand_story_v1
        
        # Get corresponding outline chapter
        if chapter_idx >= len(st.session_state.outline_data):
            return None
            
        outline_chapter = st.session_state.outline_data[chapter_idx]
        
        # Build smart update instruction - cascade update for plot modification
        update_instruction = f"""
Important: Based on key story plot modifications, please regenerate the detailed content for this chapter.

**Story Modification Background**:
{suggestion}

**Modified Related Chapter Content (as context)**:
{reference_plot[:800] if reference_plot else "None"}

**Current Chapter Original Setting**:
- Chapter Title: {outline_chapter.get('title', '')}
- Chapter Summary: {outline_chapter.get('summary', '')}

**Overall Story Characters**:
{'; '.join([f"{char.get('name', '')}: {char.get('role', '')}" for char in st.session_state.characters_data[:5]])}

**Regeneration Requirements**:
1. Must reflect the impact of the above story modifications
2. Maintain complete consistency with the new story logic
3. Preserve the chapter's role in the overall story
4. Ensure character behavior conforms to the modified settings
5. Generate detailed and complete story content (at least 500 words)

**User Additional Instructions**:
{custom_instruction if custom_instruction else "No special requirements"}

Please recreate the complete story content for this chapter based on the above requirements.
"""
        
        # Call backend to regenerate
        print(f"🔄 [Chapter Update] Starting to call expand_story_v1")
        print(f"📝 [Chapter Update] Update instruction length: {len(update_instruction)} characters")
        
        result = expand_story_v1(
            [outline_chapter], 
            st.session_state.characters_data,
            custom_instruction=update_instruction
        )
        
        print(f"✅ [Chapter Update] expand_story_v1 returned: {type(result)}")
        
        if result and len(result) > 0:
            updated_chapter = result[0]
            updated_chapter.setdefault("chapter_id", outline_chapter["chapter_id"])
            updated_chapter.setdefault("title", outline_chapter["title"])
            
            # Validate generated content
            new_plot = updated_chapter.get('plot', '')
            print(f"✅ [Chapter Update] Chapter {chapter_idx+1} regeneration successful")
            print(f"📝 [Chapter Update] New plot length: {len(new_plot)} characters")
            print(f"📖 [Chapter Update] New plot preview: {new_plot[:200]}...")
            
            return updated_chapter
        
        print(f"❌ [Chapter Update] expand_story_v1 returned no valid result")
        return None
        
    except Exception as e:
        print(f"❌ [Chapter Update] Update Chapter {chapter_idx+1} failed: {str(e)}")
        return None

def update_characters_with_context(character_updates, reference_plot, custom_instruction=""):
    """Update character settings based on context"""
    try:
        from src.utils.utils import generate_response, convert_json
        
        # Build character update prompt
        update_prompt = f"""
Update Character Settings based on the following changes:

Change Description:
{chr(10).join(character_updates)}

Reference Modification: {reference_plot[:300]}...
User Instruction: {custom_instruction}

Current Character Settings:
{json.dumps(st.session_state.characters_data, ensure_ascii=False, indent=2)}

Please update the relevant character settings to ensure consistency with story changes.

Return the complete updated character list in the same format as the original:
[
    {{
        "name": "Character Name",
        "role": "Character Role", 
        "traits": "Character Traits",
        "background": "Character Background",
        "motivation": "Character Motivation"
    }}
]

Return only JSON, no other explanations.
"""
        
        msg = [{"role": "user", "content": update_prompt}]
        response = generate_response(msg)
        updated_characters = convert_json(response)
        
        if updated_characters and isinstance(updated_characters, list):
            return updated_characters
        
        return None
        
    except Exception as e:
        print(f"❌ [Character Update] Update failed: {str(e)}")
        return None

def update_outline_with_context(outline_updates, reference_plot, custom_instruction=""):
    """Update outline based on context"""
    try:
        from src.utils.utils import generate_response, convert_json
        
        # Build outline update prompt
        update_prompt = f"""
Update Story Outline based on the following changes:

Change Description:
{chr(10).join(outline_updates)}

Reference Modification: {reference_plot[:300]}...
User Instruction: {custom_instruction}

Current Outline:
{json.dumps(st.session_state.outline_data, ensure_ascii=False, indent=2)}

Please update the relevant chapter outline to ensure consistency with story changes.

Return the complete updated outline in the same format as the original:
[
    {{
        "chapter_id": "Chapter X",
        "title": "Chapter Title",
        "summary": "Chapter Summary"
    }}
]

Preserve all existing fields (such as narrative_role, etc.).

Return only JSON, no other explanations.
"""
        
        msg = [{"role": "user", "content": update_prompt}]
        response = generate_response(msg)
        updated_outline = convert_json(response)
        
        if updated_outline and isinstance(updated_outline, list):
            return updated_outline
        
        return None
        
    except Exception as e:
        print(f"❌ [Outline Update] Update failed: {str(e)}")
        return None

def save_conflict_suggestions(chapter_idx, update_suggestions, new_plot, custom_instruction=""):
    """Save conflict analysis suggestions"""
    try:
        import json
        import os
        from datetime import datetime
        
        print(f"💾 [Suggestions Save] ===== Starting to save suggestions for Chapter {chapter_idx+1} =====")
        print(f"💾 [Suggestions Save] Suggestion data type: {type(update_suggestions)}")
        print(f"💾 [Suggestions Save] Suggestion data content: {str(update_suggestions)[:200]}...")
        print(f"💾 [Suggestions Save] New plot length: {len(new_plot)}")
        print(f"💾 [Suggestions Save] Custom instruction: {custom_instruction}")
        
        # Get absolute path of current working directory
        current_dir = os.getcwd()
        print(f"💾 [Suggestions Save] Current working directory: {current_dir}")
        
        # Use current story version directory - change to absolute path
        current_version = st.session_state.get('current_version', 'unknown')
        if current_version and current_version != 'unknown':
            suggestions_dir = os.path.join(current_dir, "data", "output", current_version)
        else:
            suggestions_dir = os.path.join(current_dir, "data", "saved_suggestions")
        
        # Create directory and show detailed information
        print(f"💾 [Suggestions Save] Target directory: {suggestions_dir}")
        os.makedirs(suggestions_dir, exist_ok=True)
        print(f"💾 [Suggestions Save] Directory created successfully")
        
        # Ensure update_suggestions is not empty
        if not update_suggestions:
            print("💾 [Suggestions Save] update_suggestions is empty, using default data")
            update_suggestions = {
                "message": "No conflict detection data", 
                "conflicts": [], 
                "suggestions": {},
                "has_conflicts": False,
                "analysis_type": "empty_fallback"
            }
        
        # Build save data
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "chapter_idx": chapter_idx,
            "chapter_title": st.session_state.story_data[chapter_idx].get('title', f'Chapter {chapter_idx+1}') if len(st.session_state.story_data) > chapter_idx else f'Chapter {chapter_idx+1}',
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
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"suggestions_ch{chapter_idx+1}_{timestamp}.json"
        filepath = os.path.join(suggestions_dir, filename)
        
        print(f"💾 [Suggestions Save] Complete file path: {filepath}")
        
        # Check directory permissions
        if not os.access(suggestions_dir, os.W_OK):
            error_msg = f"Cannot write to directory: {suggestions_dir}"
            print(f" [Suggestions Save] {error_msg}")
            st.error(f" Save failed: {error_msg}")
            return False
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        # Verify if file was created successfully
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"💾 [Suggestions Save] File successfully written: {filepath}")
            print(f"💾 [Suggestions Save] File size: {file_size} bytes")
            
            st.success(f"✅ Analysis suggestions saved successfully!")
            st.info(f"📁 Save location: {filepath}")
            st.info(f"📊 File size: {file_size} bytes")
            
            # Display save details
            with st.expander("📄 Save Details", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.json({
                        "Saved File": filename,
                        "Chapter": f"Chapter {chapter_idx+1}",
                        "Save Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                with col2:
                    st.json({
                        "Conflicts Count": len(update_suggestions.get('conflicts', [])),
                        "Update Suggestions": save_data['suggestions_summary'],
                        "File Path": filepath
                    })
            
            print(f"💾 [Suggestions Save] ===== Save Successful ===== : {filepath}")
            return True
        else:
            error_msg = f"File creation failed: {filepath}"
            print(f" [Suggestions Save] {error_msg}")
            st.error(f" Save failed: {error_msg}")
            return False
        
    except Exception as e:
        error_msg = f"Save suggestions failed: {str(e)}"
        print(f" [Suggestions Save] {error_msg}")
        st.error(f" {error_msg}")
        
        # Display detailed error information
        import traceback
        error_details = traceback.format_exc()
        print(f" [Suggestions Save] Detailed error: {error_details}")
        
        with st.expander("🔍 Detailed error", expanded=False):
            st.code(error_details, language="python")
        
        return False
    
def export_suggestions_file(chapter_idx, update_suggestions, new_plot, custom_instruction=""):
    """Export suggestions as downloadable file"""
    try:
        import json
        from datetime import datetime
        
        print(f"📥📥📥 [Suggestion Export] ===== Start exporting suggestions file for Chapter {chapter_idx+1} =====")
        print(f"📥 [Suggestion Export] Suggestion data type: {type(update_suggestions)}")
        print(f"📥 [Suggestion Export] Suggestion data content: {str(update_suggestions)[:200]}...")
        print(f"📥 [Suggestion Export] New plot length: {len(new_plot)}")
        
        # Ensure update_suggestions is not empty
        if not update_suggestions:
            update_suggestions = {"message": "No conflict detection data", "conflicts": [], "suggestions": {}}
        
        # Build export data
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "description": f"Chapter {chapter_idx+1} smart suggestions file",
                "chapter_idx": chapter_idx,
                "story_version": st.session_state.get('current_version', 'unknown')
            },
            "chapter_data": {
                "chapter_idx": chapter_idx,
                "chapter_title": st.session_state.story_data[chapter_idx].get('title', f'Chapter {chapter_idx+1}'),
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
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smart_suggestions_ch{chapter_idx+1}_{timestamp}.json"
        
        # Convert to JSON string
        json_string = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        # Provide download
        st.download_button(
            label="📥 Download Suggestions File",
            data=json_string,
            file_name=filename,
            mime="application/json",
            help="Download suggestions file containing complete analysis results",
            key=f"download_suggestions_{chapter_idx}"
        )
        
        st.success(f"✅ Suggestions file ready for download: {filename}")
        
        # Display export information
        with st.expander("📄 Export Details", expanded=False):
            st.json({
                "File name": filename,
                "Chapter": f"Chapter {chapter_idx+1}",
                "Conflicts count": len(update_suggestions.get('conflicts', [])),
                "Suggestion types": list(update_suggestions.get('suggestions', {}).keys()),
                "File size": f"{len(json_string)} characters"
            })
        
    except Exception as e:
        st.error(f"❌ Export suggestions file failed: {str(e)}")
        print(f"❌ [Suggestion Export] Export failed: {str(e)}")

def execute_uploaded_suggestions(chapter_idx, uploaded_file, current_plot):
    """Execute uploaded suggestions file"""
    try:
        import json
        
        # Reset file pointer
        uploaded_file.seek(0)
        
        # Read file content
        file_content = uploaded_file.read()
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8')
        
        # Parse JSON
        suggestions_data = json.loads(file_content)
        
        # Validate file format
        if not validate_suggestions_file(suggestions_data):
            st.error(" Invalid suggestion file format")
            return
        
        # Display suggestion file information
        st.markdown("---")
        st.markdown("###  Suggestion file information")
        
        export_info = suggestions_data.get('export_info', {})
        chapter_data = suggestions_data.get('chapter_data', {})
        analysis_results = suggestions_data.get('analysis_results', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Export time", export_info.get('timestamp', 'Unknown')[:19])
            st.metric("Target chapter", f"Chapter {chapter_data.get('chapter_idx', 0)+1}")
        
        with col2:
            st.metric("Conflict count", len(analysis_results.get('conflicts', [])))
            st.metric("Severity", analysis_results.get('severity', 'Unknown'))
        
        with col3:
            suggestions = analysis_results.get('suggestions', {})
            st.metric("Other chapters", len(suggestions.get('other_chapters', [])))
            st.metric("Character updates", len(suggestions.get('character_updates', [])))
        
        # Display main conflicts
        if analysis_results.get('conflicts'):
            st.markdown("** Main conflicts:**")
            for conflict in analysis_results['conflicts'][:3]:
                st.warning(f"• {conflict}")
        
        # Display update suggestions
        if suggestions.get('other_chapters'):
            st.markdown("**📖 Other chapters update suggestions:**")
            for chapter_update in suggestions['other_chapters'][:3]:
                chapter_num = chapter_update.get('chapter', 'Unknown')
                suggestion = chapter_update.get('suggestion', '')
                st.info(f"• Chapter {chapter_num}: {suggestion[:100]}{'...' if len(suggestion) > 100 else ''}")
        
        # Execute options
        st.markdown("---")
        st.markdown("###  Execution options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(" Use content from file", type="primary", key=f"execute_file_content_{chapter_idx}"):
                # Use plot and instructions saved in file
                file_plot = chapter_data.get('new_plot', current_plot)
                file_instruction = chapter_data.get('custom_instruction', '')
                
                st.session_state[f'edit_story_{chapter_idx}'] = False
                execute_cascade_updates(chapter_idx, file_plot, analysis_results, file_instruction)
                st.rerun()
        
        with col2:
            if st.button("🔄 Use current edited content", key=f"execute_current_content_{chapter_idx}"):
                # Use current edited plot but suggestions from file
                st.session_state[f'edit_story_{chapter_idx}'] = False
                execute_cascade_updates(chapter_idx, current_plot, analysis_results, "")
                st.rerun()
        
        with col3:
            if st.button(" View detailed suggestions", key=f"view_details_{chapter_idx}"):
                st.json(analysis_results)
        
    except json.JSONDecodeError as e:
        st.error(f" JSON file format error: {str(e)}")
    except UnicodeDecodeError as e:
        st.error(f" File encoding error: {str(e)}")
    except Exception as e:
        st.error(f" Process suggestion file failed: {str(e)}")
        print(f"📁 [Suggestion File Processing] Failed: {str(e)}")

def validate_suggestions_file(data):
    """Validate suggestion file format"""
    try:
        # Check necessary fields
        required_fields = ['export_info', 'chapter_data', 'analysis_results']
        for field in required_fields:
            if field not in data:
                return False
        
        # Check analysis_results structure
        analysis = data['analysis_results']
        if not isinstance(analysis.get('conflicts', []), list):
            return False
        
        if not isinstance(analysis.get('suggestions', {}), dict):
            return False
        
        return True
    except:
        return False

def show_suggestions_loader(chapter_idx, current_new_plot, current_custom_instruction=""):
    """Show suggestion loader"""
    st.markdown("---")
    st.markdown("### 📁 Load saved analysis suggestions")
    
    # Return button
    if st.button("← Return to conflict analysis", key=f"return_from_loader_{chapter_idx}"):
        st.session_state[f'show_suggestions_loader_{chapter_idx}'] = False
        st.rerun()
    
    try:
        import os
        import json
        
        # Use current story version directory
        current_version = st.session_state.get('current_version', 'unknown')
        if current_version and current_version != 'unknown':
            suggestions_dir = f"data/output/{current_version}"
        else:
            suggestions_dir = "data/saved_suggestions"
        
        if not os.path.exists(suggestions_dir):
            st.info("📂 No suggestions saved yet")
            return
        
        # Get all suggestion files
        suggestion_files = [f for f in os.listdir(suggestions_dir) if f.endswith('.json')]
        
        if not suggestion_files:
            st.info("📂 No suggestions saved yet")
            return
        
        # Sort by time (latest first)
        suggestion_files.sort(reverse=True)
        
        st.markdown(f"**Found {len(suggestion_files)} saved suggestions**")
        
        # File selector
        selected_file = st.selectbox(
            "Select suggestion file to load",
            suggestion_files,
            key=f"suggestions_file_selector_{chapter_idx}",
            format_func=lambda x: x.replace('.json', '').replace('_', ' ')
        )
        
        if selected_file:
            filepath = os.path.join(suggestions_dir, selected_file)
            
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            # Display suggestion preview
            st.markdown("####  Suggestion preview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Save time", saved_data.get('timestamp', 'Unknown')[:19])
                st.metric("Target chapter", f"Chapter {saved_data.get('chapter_idx', 0)+1}")
                st.metric("Story version", saved_data.get('story_version', 'Unknown'))
            
            with col2:
                st.metric("Conflict count", saved_data.get('conflicts_count', 0))
                suggestions_summary = saved_data.get('suggestions_summary', {})
                st.metric("Outline updates", suggestions_summary.get('outline_updates', 0))
                st.metric("Other chapters", suggestions_summary.get('other_chapters', 0))
            
            # Display conflict and suggestion details
            update_suggestions = saved_data.get('update_suggestions', {})
            
            if update_suggestions.get('conflicts'):
                st.markdown("** Detected conflicts:**")
                for conflict in update_suggestions['conflicts'][:3]:  # Display first 3
                    st.warning(f"• {conflict}")
                if len(update_suggestions['conflicts']) > 3:
                    st.info(f"... More {len(update_suggestions['conflicts']) - 3} conflicts")
            
            if update_suggestions.get('suggestions', {}).get('other_chapters'):
                st.markdown("**📖 Other chapters update suggestions:**")
                for chapter_update in update_suggestions['suggestions']['other_chapters'][:3]:
                    chapter_num = chapter_update.get('chapter', 'Unknown')
                    suggestion = chapter_update.get('suggestion', '')
                    st.info(f"• Chapter {chapter_num}: {suggestion[:100]}{'...' if len(suggestion) > 100 else ''}")
            
            # Execution options column
            st.markdown("---")
            st.markdown("####  Execution options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(" Use original content", type="primary", key=f"execute_original_{chapter_idx}"):
                    # Use saved original content
                    saved_plot = saved_data.get('new_plot', current_new_plot)
                    saved_instruction = saved_data.get('custom_instruction', current_custom_instruction)
                    
                    st.session_state[f'show_suggestions_loader_{chapter_idx}'] = False
                    
                    # Execute cascade updates
                    execute_cascade_updates(chapter_idx, saved_plot, update_suggestions, saved_instruction)
                    st.rerun()
            
            with col2:
                if st.button("🔄 Use current content", key=f"execute_current_{chapter_idx}"):
                    # Use current content but saved suggestions
                    st.session_state[f'show_suggestions_loader_{chapter_idx}'] = False
                    
                    # Execute cascade updates
                    execute_cascade_updates(chapter_idx, current_new_plot, update_suggestions, current_custom_instruction)
                    st.rerun()
            
            with col3:
                if st.button(" Delete this suggestion", key=f"delete_suggestion_{chapter_idx}"):
                    try:
                        os.remove(filepath)
                        st.success(f" Deleted suggestion file: {selected_file}")
                        st.rerun()
                    except Exception as e:
                        st.error(f" Delete failed: {str(e)}")
        
    except Exception as e:
        st.error(f"❌ Load suggestions failed: {str(e)}")
        print(f"📁 [Suggestion Loading] Load failed: {str(e)}")

def show_suggestions_history_for_chapter(chapter_idx, current_new_plot, current_custom_instruction=""):
    """Show specific chapter's suggestion history"""
    st.markdown("---")
    st.markdown(f"##  Suggestions history for Chapter {chapter_idx+1}")
    
    # Return button
    if st.button("← Return to editing", key=f"back_from_history_{chapter_idx}"):
        st.session_state[f'show_suggestions_history_{chapter_idx}'] = False
        st.rerun()
    
    try:
        import os
        import json
        from datetime import datetime
        
        # Use current story version directory
        current_version = st.session_state.get('current_version', 'unknown')
        if current_version and current_version != 'unknown':
            suggestions_dir = f"data/output/{current_version}"
        else:
            suggestions_dir = "data/saved_suggestions"
        
        if not os.path.exists(suggestions_dir):
            st.info("📂 No suggestions saved yet")
            return
        
        # Get suggestions files related to current chapter
        suggestion_files = []
        for filename in os.listdir(suggestions_dir):
            if filename.endswith('.json'):
                try:
                    filepath = os.path.join(suggestions_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check if it is the suggestion for current chapter
                    if data.get('chapter_idx') == chapter_idx:
                        suggestion_files.append((filename, data))
                except Exception as e:
                    continue
        
        if not suggestion_files:
            st.info(f"📂 Chapter {chapter_idx+1} has no suggestions saved yet")
            return
        
        # Sort by time (latest first)
        suggestion_files.sort(key=lambda x: x[1].get('timestamp', ''), reverse=True)
        
        st.markdown(f"**Found {len(suggestion_files)} suggestion records for Chapter {chapter_idx+1}**")
        
        # Display suggestion history
        for i, (filename, saved_data) in enumerate(suggestion_files):
            timestamp = saved_data.get('timestamp', 'Unknown time')
            try:
                # Format timestamp
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = timestamp
            
            with st.expander(f"📅 {formatted_time} - Suggestion Record #{i+1}", expanded=(i==0)):
                
                # Show chapter information when saved
                if 'new_plot' in saved_data:
                    st.markdown("**📝 The chapter content modification:**")
                    with st.container():
                        plot_preview = saved_data['new_plot'][:300] + "..." if len(saved_data['new_plot']) > 300 else saved_data['new_plot']
                        st.text_area(
                            "Chapter content preview", 
                            value=plot_preview, 
                            height=100, 
                            disabled=True,
                            key=f"plot_preview_{chapter_idx}_{i}"
                        )
                
                # Show custom instruction
                if saved_data.get('custom_instruction'):
                    st.markdown("** Custom instruction:**")
                    st.info(saved_data['custom_instruction'])
                
                # Show analysis results
                update_suggestions = saved_data.get('update_suggestions', {})
                
                if update_suggestions.get('conflicts'):
                    st.markdown("** Detected conflicts:**")
                    for conflict in update_suggestions['conflicts'][:3]:  # Only display first 3
                        st.warning(f"• {conflict}")
                    if len(update_suggestions['conflicts']) > 3:
                        st.info(f"... More {len(update_suggestions['conflicts']) - 3} conflicts")
                
                if update_suggestions.get('suggestions', {}).get('other_chapters'):
                    st.markdown("**📖 Other chapters update suggestions:**")
                    for chapter_update in update_suggestions['suggestions']['other_chapters'][:3]:
                        chapter_num = chapter_update.get('chapter', 'Unknown')
                        suggestion = chapter_update.get('suggestion', '')
                        st.info(f"• Chapter {chapter_num}: {suggestion[:100]}{'...' if len(suggestion) > 100 else ''}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(" Re-execute", key=f"rerun_suggestion_{chapter_idx}_{i}"):
                        # Re-execute using historical suggestions
                        st.session_state[f'show_suggestions_history_{chapter_idx}'] = False
                        execute_cascade_updates(chapter_idx, current_new_plot, update_suggestions, saved_data.get('custom_instruction', ''))
                        st.rerun()
                
                with col2:
                    if st.button("📥 Export this suggestion", key=f"export_history_{chapter_idx}_{i}"):
                        # Export this historical suggestion
                        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename_export = f"History suggestion_Chapter {chapter_idx+1}_{timestamp_str}.json"
                        
                        json_string = json.dumps(saved_data, ensure_ascii=False, indent=2)
                        
                        st.download_button(
                            label="📥 Download history suggestion",
                            data=json_string,
                            file_name=filename_export,
                            mime="application/json",
                            key=f"download_history_{chapter_idx}_{i}"
                        )
                
                with col3:
                    if st.button(" Delete record", key=f"delete_history_{chapter_idx}_{i}"):
                        try:
                            filepath = os.path.join(suggestions_dir, filename)
                            os.remove(filepath)
                            st.success(" Record deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f" Delete failed: {str(e)}")
        
    except Exception as e:
        st.error(f" Load suggestion history failed: {str(e)}")
        print(f"📅 [Suggestion History] Load failed: {str(e)}")

def show_suggestions_manager():
    """Show suggestion manager"""
    st.markdown("---")
    st.markdown("##  Smart suggestion manager")
    
    # Return button
    if st.button("← Return"):
        st.session_state.show_suggestions_manager = False
        st.rerun()
    
    try:
        import os
        import json
        from datetime import datetime
        
        # Use current story version directory
        current_version = st.session_state.get('current_version', 'unknown')
        if current_version and current_version != 'unknown':
            suggestions_dir = f"data/output/{current_version}"
        else:
            suggestions_dir = "data/saved_suggestions"
        
        if not os.path.exists(suggestions_dir):
            st.info("📂 No suggestions saved yet")
            return
        
        # Get all suggestion files
        suggestion_files = [f for f in os.listdir(suggestions_dir) if f.endswith('.json')]
        
        if not suggestion_files:
            st.info("📂 No suggestions saved yet")
            return
        
        # Sort by time (latest first)
        suggestion_files.sort(reverse=True)
        
        st.markdown(f"**Found {len(suggestion_files)} saved suggestions**")
        
        # Batch operations
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Clear All Suggestions", type="secondary"):
                try:
                    for file in suggestion_files:
                        os.remove(os.path.join(suggestions_dir, file))
                    st.success("✅ All suggestions cleared")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Clear failed: {str(e)}")
        
        # Display suggestion list
        for i, filename in enumerate(suggestion_files):
            filepath = os.path.join(suggestions_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                
                # Create suggestion card
                with st.expander(f"📄 {filename.replace('.json', '')}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Save Time", saved_data.get('timestamp', 'Unknown')[:19])
                        st.metric("Target Chapter", f"Chapter {saved_data.get('chapter_idx', 0)+1}")
                    
                    with col2:
                        st.metric("Story Version", saved_data.get('story_version', 'Unknown'))
                        st.metric("Conflict Count", saved_data.get('conflicts_count', 0))
                    
                    with col3:
                        suggestions_summary = saved_data.get('suggestions_summary', {})
                        st.metric("Other Chapters", suggestions_summary.get('other_chapters', 0))
                        st.metric("Character Updates", suggestions_summary.get('character_updates', 0))
                    
                    # Display partial suggestion content
                    update_suggestions = saved_data.get('update_suggestions', {})
                    if update_suggestions.get('conflicts'):
                        st.markdown("**⚠️ Main Conflicts:**")
                        for conflict in update_suggestions['conflicts'][:2]:
                            st.warning(f"• {conflict}")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🚀 Execute Immediately", key=f"execute_suggestion_{i}"):
                            # Load and execute suggestions
                            chapter_idx = saved_data.get('chapter_idx', 0)
                            new_plot = saved_data.get('new_plot', '')
                            custom_instruction = saved_data.get('custom_instruction', '')
                            
                            # Check if current story data matches
                            if len(st.session_state.story_data) > chapter_idx:
                                st.session_state.show_suggestions_manager = False
                                execute_cascade_updates(chapter_idx, new_plot, update_suggestions, custom_instruction)
                                st.rerun()
                            else:
                                st.error("❌ Current story data does not match suggestions")
                    
                    with col2:
                        if st.button("📋 Copy to Clipboard", key=f"copy_suggestion_{i}"):
                            # Display JSON content for copying
                            st.json(saved_data)
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_suggestion_{i}"):
                            try:
                                os.remove(filepath)
                                st.success(f"✅ Deleted: {filename}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Delete failed: {str(e)}")
            
            except Exception as e:
                st.error(f"❌ Read file failed {filename}: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Manager load failed: {str(e)}")
        print(f"📊 [Suggestion Manager] Load failed: {str(e)}")

def generate_story_summary_text():
    """Generate story summary text"""
    lines = [f"{st.session_state.current_version} Story Summary\n"]
    lines.append("=" * 50 + "\n")
    
    for i, chapter in enumerate(st.session_state.story_data):
        title = chapter.get('title', f'Chapter {i+1}')
        plot = chapter.get('plot', '')
        word_count = len(plot)
        
        lines.append(f"{i+1}. {title} ({word_count} chars)")
        lines.append(f"Scene: {chapter.get('scene', 'Not specified')}")
        lines.append(f"Characters: {', '.join(chapter.get('characters', [])) if chapter.get('characters') else 'Not specified'}")
        lines.append(f"Summary: {plot[:200]}{'...' if len(plot) > 200 else ''}")
        lines.append("-" * 30)
    
    return "\n".join(lines)

def show_chapter_order_comparison():
    """Show chapter order comparison"""
    if not st.session_state.outline_data:
        return
    
    # Check if there is reorder information
    has_reorder_info = any('original_position' in ch for ch in st.session_state.outline_data)
    
    if has_reorder_info:
        # Display reorder comparison
        st.markdown("### 🔄 Chapter Order Comparison")
        
        # Build original order mapping
        original_chapters = {}
        for ch in st.session_state.outline_data:
            if 'original_position' in ch:
                original_chapters[ch['original_position']] = ch
        
        # Display original order
        st.markdown("**🔸 Original Order:**")
        original_order_display = []
        for pos in sorted(original_chapters.keys()):
            ch = original_chapters[pos]
            original_order_display.append(f"{pos}. {ch['title']}")
        st.markdown(" → ".join(original_order_display))
        
        # Display current order
        st.markdown("**🔹 Current Order:**")
        current_order_display = []
        for i, chapter in enumerate(st.session_state.outline_data):
            orig_pos = chapter.get('original_position', '?')
            current_order_display.append(f"{i+1}. {chapter['title']} (Originally chapter {orig_pos})")
        st.markdown(" → ".join(current_order_display))
        
        # Display detailed comparison table
        st.markdown("**📊 Detailed Comparison:**")
        
        # Create comparison table data
        comparison_data = []
        for i, chapter in enumerate(st.session_state.outline_data):
            orig_pos = chapter.get('original_position', 'Unknown')
            narrative_role = chapter.get('narrative_role', 'Linear narrative')
            
            # Determine position change
            if isinstance(orig_pos, int):
                position_change = i + 1 - orig_pos
                if position_change > 0:
                    change_indicator = f"↓ +{position_change}"
                elif position_change < 0:
                    change_indicator = f"↑ {position_change}"
                else:
                    change_indicator = "→ No change"
            else:
                change_indicator = "?"
            
            comparison_data.append({
                "Current Position": f"Chapter {i+1}",
                "Chapter Title": chapter['title'],
                "Original Position": f"Chapter {orig_pos}" if isinstance(orig_pos, int) else str(orig_pos),
                "Position Change": change_indicator,
                "Narrative Role": narrative_role
            })
        
        # Display table
        import pandas as pd
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Display reorder statistics
        moved_chapters = sum(1 for ch in st.session_state.outline_data 
                           if isinstance(ch.get('original_position'), int) and 
                           st.session_state.outline_data.index(ch) + 1 != ch['original_position'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Chapters", len(st.session_state.outline_data))
        with col2:
            st.metric("Reordered Chapters", moved_chapters)
        with col3:
            st.metric("Unchanged Chapters", len(st.session_state.outline_data) - moved_chapters)
    
    else:
        # Display linear order
        st.markdown("### 📝 Current Chapter Order (Linear)")
        
        current_order = []
        for i, chapter in enumerate(st.session_state.outline_data):
            current_order.append(f"{i+1}. {chapter['title']}")
        
        st.markdown(" → ".join(current_order))
        
        # Display simple statistics
        st.info(f"ℹ️ Currently has {len(st.session_state.outline_data)} chapters, arranged in linear order")

def show_export_mode():
    """Export mode"""
    st.subheader("💾 Save and Export")
    
    # Save to file
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Save Outline:**")
        
        # Build File name
        filename = f"{st.session_state.current_version}_outline.json"
        
        # Create download button
        outline_json = json.dumps(st.session_state.outline_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Download JSON File",
            data=outline_json,
            file_name=filename,
            mime="application/json"
        )
        
        # Save to output directory
        if st.button("💾 Save to Project Directory", use_container_width=True):
            save_to_project_directory()
    
    with col2:
        st.markdown("**Export Formats:**")
        
        # Export as Markdown
        markdown_content = generate_markdown_outline()
        st.download_button(
            label="📝 Download Markdown",
            data=markdown_content,
            file_name=f"{st.session_state.current_version}_outline.md",
            mime="text/markdown"
        )
        
        # Export as text
        text_content = generate_text_outline()
        st.download_button(
            label="📄 Download Plain Text",
            data=text_content,
            file_name=f"{st.session_state.current_version}_outline.txt",
            mime="text/plain"
        )
    
    st.markdown("---")
    
    # Final confirmation
    st.markdown("### ✅ Final Confirmation")
    
    # Display final structure
    st.markdown("**Final chapter structure:**")
    for i, chapter in enumerate(st.session_state.outline_data):
        st.markdown(f"{i+1}. **{chapter['chapter_id']}**: {chapter['title']}")
        if chapter.get('summary'):
            st.markdown(f"   *{chapter['summary']}*")
    
    # Statistics
    total_chapters = len(st.session_state.outline_data)
    st.success(f"✅ Outline Editing Complete! Total {total_chapters} chapters")
    
    if st.button("✅ Continue to Next Step", type="primary", use_container_width=True):
        st.info("ℹ️ Outline is ready! You can proceed to generate character settings and story content.")

# Helper functions
def regenerate_chapter(chapter_idx, chapter):
    """Regenerate single chapter"""
    try:
        # Get current story parameters (from sidebar or session state)
        current_topic = st.session_state.get('current_topic', 'Little Red Riding Hood')
        current_style = st.session_state.get('current_style', 'Sci-fi Rewrite')
        
        # Build instructions for specific chapter
        chapter_id = chapter.get('chapter_id', f'Chapter {chapter_idx + 1}')
        current_title = chapter.get('title', f'Chapter {chapter_idx + 1}')
        
        custom_instruction = f"""
Please regenerate the content for Chapter {chapter_idx + 1}.
Original Chapter ID: {chapter_id}
Original Title: {current_title}
Requirement: Maintain consistency with overall story style, but recreate the title and summary for this chapter.
"""
        
        start_time = time.time()
        st.info(f"🔄 Regenerating Chapter {chapter_idx + 1}...")
        
        # Regenerate entire outline, then extract corresponding chapter
        new_outline = generate_outline(
            topic=current_topic, 
            style=current_style, 
            custom_instruction=custom_instruction
        )
        end_time = time.time()
        
        log_backend_operation(
            f"Regenerate Chapter {chapter_idx + 1}", 
            {
                "chapter_idx": chapter_idx, 
                "chapter_id": chapter_id,
                "topic": current_topic,
                "style": current_style,
                "custom_instruction": custom_instruction[:100] + "..."
            },
            start_time, end_time, new_outline
        )
        
        # Check generation results
        if not new_outline or not isinstance(new_outline, list):
            st.error("❌ Backend returned incorrect data format")
            st.error(f"Actual return: {type(new_outline)} - {str(new_outline)[:200]}...")
            return
            
        if len(new_outline) <= chapter_idx:
            st.warning(f"⚠️ Generated chapter count ({len(new_outline)}) is insufficient, cannot replace Chapter {chapter_idx + 1}")
            return
        
        # Get newly generated chapter
        new_chapter = new_outline[chapter_idx]
        
        # Validate format of new chapter
        if not isinstance(new_chapter, dict):
            st.error("❌ Newly generated chapter format is incorrect")
            st.error(f"Chapter type: {type(new_chapter)}, content: {str(new_chapter)}")
            return
        
        # Handle different field name formats (compatible with different formats LLM might return)
        def extract_field(chapter_data, field_name, alternatives=None, default=""):
            """Extract fields from chapter data, supporting multiple possible field names"""
            if alternatives is None:
                alternatives = []
            
            # First try standard field name
            if field_name in chapter_data:
                return chapter_data[field_name]
            
            # Try alternative field names
            for alt_name in alternatives:
                if alt_name in chapter_data:
                    return chapter_data[alt_name]
            
            return default
        
        # Extract chapter information (compatible with multiple field name formats)
        new_title = extract_field(new_chapter, 'title', ['chapter_title', 'title_text'], f'Regenerated Chapter {chapter_idx + 1}')
        new_summary = extract_field(new_chapter, 'summary', ['chapter_content', 'content', 'description'], f'This is regenerated content for Chapter {chapter_idx + 1}')
        new_chapter_id = extract_field(new_chapter, 'chapter_id', ['id', 'number'], f'Chapter {chapter_idx + 1}')
        
        # Retain some original information, update core content
        updated_chapter = {
            "chapter_id": chapter.get('chapter_id', new_chapter_id),
            "title": new_title,
            "summary": new_summary
        }
        
        # Display extracted information for debugging
        st.info(f"🔍 Extracted Chapter Information:")
        st.info(f"  - Original data: {str(new_chapter)[:200]}...")
        st.info(f"  - Extracted title: {new_title}")
        st.info(f"  - Extracted summary: {new_summary[:100]}...")
        
        # Retain original narrative analysis fields
        narrative_fields = ["new_order", "narrative_role", "narrative_instruction", "transition_hint", "original_position"]
        for field in narrative_fields:
            if field in chapter:
                updated_chapter[field] = chapter[field]
        
        # Save state before regeneration to history
        old_data = st.session_state.outline_data.copy()
        save_to_history(f"Regenerate Chapter {chapter_idx + 1}", old_data)
        
        # Update chapter data
        st.session_state.outline_data[chapter_idx] = updated_chapter
        
        st.success(f"✅ Chapter {chapter_idx + 1} regeneration completed")
        st.info(f"📝 New title: {updated_chapter['title']}")
        st.info(f"📄 New summary: {updated_chapter['summary'][:100]}...")
        
        st.rerun()
        
    except Exception as e:
        log_backend_operation(
            f"Regenerate Chapter {chapter_idx + 1} failed", 
            {"chapter_idx": chapter_idx, "error": str(e)},
            time.time(), time.time(), None, e
        )
        st.error(f"❌ Regeneration failed: {str(e)}")
        app_logger.error(f"Chapter regeneration failed for chapter {chapter_idx + 1}: {str(e)}")

# delete_chapter function removed, deletion logic handled directly in edit interface

def save_chapter_edit(chapter_idx, new_title, new_chapter_id, new_summary):
    """Save chapter edit"""
    # Save state before editing to history
    old_data = st.session_state.outline_data.copy()
    save_to_history(f"Edit Chapter {chapter_idx + 1}", old_data)
    
    # Execute edit
    st.session_state.outline_data[chapter_idx]['title'] = new_title
    st.session_state.outline_data[chapter_idx]['chapter_id'] = new_chapter_id
    st.session_state.outline_data[chapter_idx]['summary'] = new_summary
    st.success(f"✅ Chapter {chapter_idx + 1} changes saved")

def add_new_chapter(title, summary, insert_idx=None, enable_conflict_check=True):
    """Add new chapter to specified position"""
    try:
        # If no position specified, default to add at end
        if insert_idx is None:
            insert_idx = len(st.session_state.outline_data)
        
        # Save state before addition to history
        old_data = st.session_state.outline_data.copy()
        save_to_history(f"Add new chapter at position {insert_idx + 1}", old_data)
        
        # Conflict detection
        if enable_conflict_check:
            conflicts = detect_content_conflicts(title, summary, st.session_state.outline_data)
            if conflicts:
                st.warning("⚠️ Detected potential content conflicts:")
                for conflict in conflicts:
                    st.warning(f"  • {conflict}")
                
                # Provide options
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚨 Add Anyway", key="confirm_add_with_conflicts"):
                        pass  # Continue with add logic
                    else:
                        with col2:
                            if st.button("❌ Cancel Addition", key="cancel_add"):
                                st.info("ℹ️ Chapter addition cancelled")
                                return
                        
                        # Return if user did not choose to continue
                        if not st.session_state.get('confirm_add_with_conflicts', False):
                            return
        
        # Generate new chapter ID
        if insert_idx == len(st.session_state.outline_data):
            # Add to end
            new_chapter_id = f"Chapter {len(st.session_state.outline_data) + 1}"
        else:
            # Insert in middle, need to renumber
            new_chapter_id = f"Chapter {insert_idx + 1}"
        
        # Create new chapter
        new_chapter = {
            "chapter_id": new_chapter_id,
            "title": title,
            "summary": summary
        }
        
        # If there is original position information, set original position of new chapter
        if any('original_position' in ch for ch in st.session_state.outline_data):
            new_chapter['original_position'] = insert_idx + 1
        
        # Insert new chapter
        st.session_state.outline_data.insert(insert_idx, new_chapter)
        
        # Update subsequent chapter IDs
        update_chapter_ids_after_insert(insert_idx)
        
        # Display success message
        position_text = "end" if insert_idx == len(st.session_state.outline_data) - 1 else f"position {insert_idx + 1}"
        st.success(f"✅ New chapter added to {position_text}: {title}")
        
        # Display chapter list preview
        st.info("ℹ️ Current chapter order:")
        for i, ch in enumerate(st.session_state.outline_data):
            marker = "🆕" if i == insert_idx else "📄"
            st.text(f"  {marker} {i+1}. {ch['title']}")
        
    except Exception as e:
        st.error(f"❌ Add chapter failed: {str(e)}")
        app_logger.error(f"Add chapter failed: {str(e)}")

def update_chapter_ids_after_insert(insert_idx):
    """Update subsequent chapter IDs after insertion"""
    for i in range(insert_idx + 1, len(st.session_state.outline_data)):
        # Update chapter_id
        st.session_state.outline_data[i]['chapter_id'] = f"Chapter {i + 1}"

def detect_content_conflicts(new_title, new_summary, existing_chapters):
    """Detect content conflicts between new chapter and existing chapters"""
    conflicts = []
    
    # Extract key information for conflict detection
    new_content = f"{new_title} {new_summary}".lower()
    
    # Define some common conflict keyword pairs
    conflict_patterns = [
        # Role status conflicts
        (["death", "die", "dead", "sacrifice", "killed"], ["alive", "live", "survival", "save", "rescue", "revive"]),
        (["good", "kind", "righteous", "hero", "justice"], ["bad", "evil", "villain", "enemy", "wicked"]),
        (["friend", "ally", "help", "support"], ["enemy", "betrayal", "betray", "oppose", "against"]),
        
        # Location conflicts
        (["earth", "home", "hometown", "homeland"], ["alien", "space", "another world", "extraterrestrial"]),
        (["city", "urban", "town"], ["rural", "village", "countryside", "forest"]),
        
        # Time conflicts
        (["past", "memory", "history", "yesterday"], ["future", "prophecy", "tomorrow", "prediction"]),
        (["day", "morning", "noon", "daytime"], ["night", "evening", "midnight", "dusk"]),
        
        # Plot status conflicts
        (["success", "victory", "win", "complete", "achieve"], ["failure", "defeat", "lose", "fail", "abandon", "give up"]),
        (["begin", "start", "departure", "leave", "journey"], ["end", "finish", "complete", "arrive", "conclusion"]),
    ]
    
    # Check conflicts with existing chapters
    for i, chapter in enumerate(existing_chapters):
        existing_content = f"{chapter['title']} {chapter.get('summary', '')}".lower()
        
        # Check title similarity
        if similar_titles(new_title, chapter['title']):
            conflicts.append(f"Title too similar to Chapter {i+1}: '{chapter['title']}'")
        
        # Check content conflict patterns
        for positive_words, negative_words in conflict_patterns:
            has_positive_new = any(word in new_content for word in positive_words)
            has_negative_new = any(word in new_content for word in negative_words)
            has_positive_existing = any(word in existing_content for word in positive_words)
            has_negative_existing = any(word in existing_content for word in negative_words)
            
            # Detect contradictions
            if (has_positive_new and has_negative_existing) or (has_negative_new and has_positive_existing):
                conflicts.append(f"Conflict with Chapter {i+1}: '{chapter['title']}'")
                break
    
    return conflicts

def similar_titles(title1, title2):
    """Check if two titles are too similar"""
    # Simple similarity detection
    title1_words = set(title1.replace(" ", "").lower())
    title2_words = set(title2.replace(" ", "").lower())
    
    if len(title1_words) == 0 or len(title2_words) == 0:
        return False
    
    # Calculate similarity
    intersection = len(title1_words & title2_words)
    union = len(title1_words | title2_words)
    similarity = intersection / union if union > 0 else 0
    
    return similarity > 0.6  # 60% or more similarity is considered similar title

def perform_automatic_reorder():
    """Perform automatic reordering"""
    try:
        # Save state before reordering to history
        old_data = st.session_state.outline_data.copy()
        save_to_history("Automatic Reordering", old_data)
        
        # Step 1: Chapter reordering
        start_time = time.time()
        reordered = reorder_chapters(st.session_state.outline_data, mode="nonlinear")
        reorder_end = time.time()
        
        log_backend_operation(
            "Automatic Chapter Reordering", 
            {"mode": "nonlinear", "chapters": len(st.session_state.outline_data)},
            start_time, reorder_end, reordered
        )
        
        # Step 2: Narrative structure analysis
        analysis_start = time.time()
        # Dynamically get current topic and style
        topic, style = get_current_topic_and_style()
        reordered = analyze_narrative_structure(reordered, st.session_state.outline_data, topic, style)
        analysis_end = time.time()
        
        log_backend_operation(
            "Automatic Reordering - Narrative Structure Analysis", 
            {"topic": topic, "style": style},
            analysis_start, analysis_end, reordered
        )
        
        # Update outline data
        st.session_state.outline_data = reordered
        st.success("✅ Non-linear reordering completed!")
        st.rerun()
    except Exception as e:
        log_backend_operation(
            "Automatic Reordering Failed", 
            {"chapters": len(st.session_state.outline_data) if st.session_state.outline_data else 0},
            time.time(), time.time(), None, e
        )
        st.error(f"❌ Automatic reordering failed: {str(e)}")

def perform_narrative_analysis():
    """Execute narrative structure analysis"""
    try:
        # Dynamically get current topic and style
        topic, style = get_current_topic_and_style()
        
        start_time = time.time()
        analyzed = analyze_narrative_structure(
            st.session_state.outline_data, 
            st.session_state.outline_data, 
            topic, 
            style
        )
        end_time = time.time()
        
        log_backend_operation(
            "Narrative structure analysis", 
            {"topic": topic, "style": style, "chapters": len(st.session_state.outline_data)},
            start_time, end_time, analyzed
        )
        
        st.session_state.outline_data = analyzed
        st.success("✅ Narrative structure analysis completed!")
        st.rerun()
    except Exception as e:
        log_backend_operation(
            "Narrative Structure Analysis Failed", 
            {"chapters": len(st.session_state.outline_data) if st.session_state.outline_data else 0},
            time.time(), time.time(), None, e
        )
        st.error(f"❌ Narrative structure analysis failed: {str(e)}")

def apply_manual_reorder(order_input):
    """Apply manual reordering"""
    try:
        new_order = [int(x.strip()) - 1 for x in order_input.split(',')]
        if len(new_order) != len(st.session_state.outline_data):
            st.error("❌ Order count does not match chapter count")
            return
        
        # Check if input is valid
        if not all(0 <= idx < len(st.session_state.outline_data) for idx in new_order):
            st.error("❌ Order index out of range")
            return
        
        if len(set(new_order)) != len(new_order):
            st.error("❌ Duplicate chapters in order")
            return
        
        # Save state before reordering to history
        old_data = st.session_state.outline_data.copy()
        save_to_history("Manual Reordering", old_data)
        
        # Reorder chapters and add original position information
        reordered_outline = []
        for new_pos, old_idx in enumerate(new_order):
            chapter = st.session_state.outline_data[old_idx].copy()
            
            # If chapter doesn't have original_position, set to current position+1
            if 'original_position' not in chapter:
                chapter['original_position'] = old_idx + 1
            
            # Set new order information
            chapter['new_order'] = new_pos + 1
            
            reordered_outline.append(chapter)
        
        st.session_state.outline_data = reordered_outline
        
        st.success("✅ Manual reordering completed!")
        
        # Display reordering result preview
        st.info("✅ Reordering result preview:")
        for i, ch in enumerate(reordered_outline):
            orig_pos = ch.get('original_position', '?')
            st.text(f"  {i+1}. {ch['title']} (Originally chapter {orig_pos})")
        
        st.rerun()
        
    except ValueError:
        st.error("❌ Please enter a valid numeric sequence, separated by commas")
    except Exception as e:
        st.error(f"❌ Manual reordering failed: {str(e)}")

def save_to_project_directory():
    """Save to project directory"""
    try:
        start_time = time.time()
        # Use real backend save function
        save_json(st.session_state.outline_data, st.session_state.current_version, "outline.json")
        end_time = time.time()
        
        log_backend_operation(
            "Save to project directory", 
            {"version": st.session_state.current_version, "filename": "outline.json"},
            start_time, end_time, True
        )
        
        st.success(f"✅ Outline saved to project directory: {st.session_state.current_version}/outline.json")
    except Exception as e:
        log_backend_operation(
            "Save to Project Directory Failed", 
            {"version": st.session_state.current_version},
            time.time(), time.time(), None, e
        )
        st.error(f"⚠️ Save failed: {str(e)}")

def generate_markdown_outline():
    """Generate Markdown format outline"""
    markdown_lines = [f"# {st.session_state.current_version} Story Outline\n"]
    
    for i, chapter in enumerate(st.session_state.outline_data):
        markdown_lines.append(f"## {chapter['chapter_id']}: {chapter['title']}")
        if chapter.get('summary'):
            markdown_lines.append(f"\n{chapter['summary']}\n")
        
        # Add narrative analysis information
        if 'narrative_role' in chapter:
            markdown_lines.append(f"**Narrative Role:** {chapter['narrative_role']}")
        if 'narrative_instruction' in chapter:
            markdown_lines.append(f"**Narrative Guidance:** {chapter['narrative_instruction']}")
        if 'transition_hint' in chapter:
            markdown_lines.append(f"**Transition Hint:** {chapter['transition_hint']}")
        
        markdown_lines.append("---\n")
    
    return "\n".join(markdown_lines)

def generate_text_outline():
    """Generate plain text format outline"""
    text_lines = [f"{st.session_state.current_version} Story Outline\n"]
    text_lines.append("=" * 50 + "\n")
    
    for i, chapter in enumerate(st.session_state.outline_data):
        text_lines.append(f"{chapter['chapter_id']}: {chapter['title']}")
        if chapter.get('summary'):
            text_lines.append(f"Summary: {chapter['summary']}")
        
        # Add narrative analysis information
        if 'narrative_role' in chapter:
            text_lines.append(f"Narrative Role: {chapter['narrative_role']}")
        if 'narrative_instruction' in chapter:
            text_lines.append(f"Narrative Guidance: {chapter['narrative_instruction']}")
        if 'transition_hint' in chapter:
            text_lines.append(f"Transition Hint: {chapter['transition_hint']}")
        
        text_lines.append("-" * 30)
    
    return "\n".join(text_lines)

# ==================== Dialogue Generation Function ====================

def save_dialogue_to_history(action_name, old_dialogue_data=None):
    """Save dialogue data to history records"""
    try:
        if old_dialogue_data is None:
            old_dialogue_data = copy.deepcopy(st.session_state.dialogue_data) if st.session_state.dialogue_data else []
        
        # Create history record entry
        history_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action_name,
            "dialogue_data": old_dialogue_data,
            "data_length": len(old_dialogue_data) if old_dialogue_data else 0
        }
        
        # If not at the end of history records, delete subsequent records
        if st.session_state.dialogue_history_index < len(st.session_state.dialogue_history) - 1:
            st.session_state.dialogue_history = st.session_state.dialogue_history[:st.session_state.dialogue_history_index + 1]
        
        # Add new record
        st.session_state.dialogue_history.append(history_entry)
        st.session_state.dialogue_history_index = len(st.session_state.dialogue_history) - 1
        
        # Limit number of history records
        max_history = 20
        if len(st.session_state.dialogue_history) > max_history:
            st.session_state.dialogue_history = st.session_state.dialogue_history[-max_history:]
            st.session_state.dialogue_history_index = len(st.session_state.dialogue_history) - 1
        
        print(f"📜 [Dialogue History] Save operation: {action_name}, current index: {st.session_state.dialogue_history_index}")
        
    except Exception as e:
        print(f"📜 [Dialogue History] Save failed: {str(e)}")

def undo_dialogue_action():
    """Undo dialogue operation"""
    if st.session_state.dialogue_history_index > 0:
        st.session_state.dialogue_history_index -= 1
        history_entry = st.session_state.dialogue_history[st.session_state.dialogue_history_index]
        st.session_state.dialogue_data = copy.deepcopy(history_entry["dialogue_data"])
        st.success(f"↩️ Undid operation: {history_entry['action']}")
        st.rerun()
    else:
        st.warning("⚠️ No actions to undo")

def redo_dialogue_action():
    """Redo dialogue operation"""
    if st.session_state.dialogue_history_index < len(st.session_state.dialogue_history) - 1:
        st.session_state.dialogue_history_index += 1
        history_entry = st.session_state.dialogue_history[st.session_state.dialogue_history_index]
        st.session_state.dialogue_data = copy.deepcopy(history_entry["dialogue_data"])
        st.success(f"↪️ Redid operation: {history_entry['action']}")
        st.rerun()
    else:
        st.warning("⚠️ No actions to redo")

def show_dialogue_generation_interface():
    """Show dialogue generation interface - as main workflow step"""
    st.header("💬 Step 4: Dialogue Generation")
    
    # Check prerequisites
    if not st.session_state.outline_data:
        st.error("❌ Please complete Step 1 first: Generate Story Outline")
        return
    
    if not st.session_state.characters_data:
        st.error("❌ Please complete Step 2 first: Generate Characters")
        return
    
    if not st.session_state.get('story_data'):
        st.error("❌ Please complete Step 3 first: Generate Story Content")
        return
    
    # Check if dialogue generation function is available
    if not dialogue_generation_available:
        st.error("❌ Dialogue generation function not available, please check backend module imports")
        return
    
    # Show story-based dialogue generation interface
    show_dialogue_generation_mode()

def show_dialogue_generation_mode():
    """Dialogue generation mode selection"""
    st.markdown("### 💬 Dialogue Generation Options")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Generate Dialogue", "👀 Dialogue Preview", "✏️ Edit Dialogue", "📁 File Management"])
    
    with tab1:
        show_dialogue_generation_options()
    
    with tab2:
        show_dialogue_display()
    
    with tab3:
        show_dialogue_edit_mode()
    
    with tab4:
        show_dialogue_file_management()

def show_dialogue_generation_options():
    """Dialogue generation options"""
    st.markdown("#### 💬 Generate New Dialogue")
    
    # Generation parameter configuration
    col1, col2 = st.columns(2)
    
    with col1:
        use_cache = st.checkbox("Use Cache", value=True, help="Whether to use cache if dialogue data already exists", key="dialogue_use_cache_checkbox")
        auto_save = st.checkbox("Auto Save", value=True, help="Automatically save to project directory after generation", key="dialogue_auto_save_checkbox")
    
    with col2:
        behavior_model = st.selectbox(
            "Behavior Recognition Model", 
            ["gpt-4.1", "gpt-3.5-turbo", "claude-3"], 
            index=0,
            help="Model used for character behavior analysis"
        )
    
    st.markdown("---")
    
    # Generation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💬 Generate Chapter Dialogues", type="primary", use_container_width=True):
            generate_dialogues_from_story(use_cache=use_cache, auto_save=auto_save, behavior_model=behavior_model)
    
    with col2:
        if st.button("🔄 Regenerate All", use_container_width=True):
            regenerate_all_dialogues(behavior_model=behavior_model)
    
    with col3:
        if st.button("📁 Load Existing Dialogue", use_container_width=True):
            st.session_state.show_dialogue_loader_gen = True
            st.rerun()
    
    # Show dialogue loader
    if st.session_state.get('show_dialogue_loader_gen', False):
        load_existing_dialogue("generation_options")

def generate_dialogues_from_story(use_cache=True, auto_save=True, behavior_model="gpt-4.1"):
    """Generate dialogues based on story content"""
    try:
        print(f"💬 [Dialogue Generation] ===== Start generating dialogues =====")
        print(f"💬 [Dialogue Generation] Story chapters: {len(st.session_state.story_data)}")
        print(f"💬 [Dialogue Generation] Characters: {len(st.session_state.characters_data)}")
        print(f"💬 [Dialogue Generation] Use cache: {use_cache}")
        print(f"💬 [Dialogue Generation] Auto save: {auto_save}")
        print(f"💬 [Dialogue Generation] Behavior model: {behavior_model}")
        
        # Save current state to history
        save_dialogue_to_history("Pre-Generate Dialogue")
        
        with st.spinner("⚡ Analyzing story and generating dialogues..."):
            start_time = time.time()
            
            # Call backend dialogue generation function
            chapter_results, sentence_results, behavior_timeline = analyze_dialogue_insertions_v2(
                st.session_state.story_data, 
                st.session_state.characters_data
            )
            
            # If sync is needed, use chapter-level data
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
            
            # Save generated dialogue data
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
            
            # Log operation
            log_backend_operation(
                "Dialogue Generation", 
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
            
            print(f"✅ [Dialogue Generation] Chapter dialogues: {len(chapter_results_updated)}")
            print(f"✅ [Dialogue Generation] Sentence dialogues: {len(sentence_results)}")
            print(f"✅ [Dialogue Generation] Behavior timeline: {len(behavior_timeline)}")
            print(f"✅ [Dialogue Generation] ===== Generation completed =====")
            
            st.success(f"✅ Dialogue generation completed! Generated dialogue content for {len(chapter_results_updated)} chapters")
            
            # Display generation statistics
            with st.expander("📊 Generation Statistics", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Chapter Dialogues", len(chapter_results_updated))
                with col2:
                    st.metric("Sentence Dialogues", len(sentence_results))
                with col3:
                    st.metric("Behavior Events", len(behavior_timeline))
            
            # Auto save
            if auto_save:
                save_dialogue_to_project()
            
            # Save operation to history
            save_dialogue_to_history("Dialogue Generation Completed")
            
    except Exception as e:
        error_msg = f"Dialogue generation failed: {str(e)}"
        print(f"❌ [Dialogue Generation] {error_msg}")
        st.error(f" {error_msg}")
        
        # Log error
        log_backend_operation(
            "Dialogue Generation Failed", 
            {"error": str(e)},
            time.time(), time.time(), None, e
        )

def show_dialogue_display():
    """Display dialogue content"""
    if not st.session_state.get('dialogue_data'):
        st.info("📝 No dialogue data available, please generate dialogue first")
        return
    
    st.markdown("#### 💬 Dialogue Content Preview")
    
    dialogue_data = st.session_state.dialogue_data
    
    # Create sub-tabs
    subtab1, subtab2, subtab3 = st.tabs(["📖 Chapter Dialogues", "📝 Sentence Dialogues", " Behavior Timeline"])
    
    with subtab1:
        show_chapter_dialogues(dialogue_data.get("chapter_dialogues", []))
    
    with subtab2:
        show_sentence_dialogues(dialogue_data.get("sentence_dialogues", []))
    
    with subtab3:
        show_behavior_timeline(dialogue_data.get("behavior_timeline", []))

def show_chapter_dialogues(chapter_dialogues):
    """Show chapter dialogues"""
    if not chapter_dialogues:
        st.info("📝 No chapter dialogue data")
        return
    
    st.markdown("##### 📖 Chapter Dialogue Overview")
    
    # Display mode selection
    display_mode = st.radio(
        "Display Mode",
        ["Chapter Summary Dialogues", "Sentence-Level Detailed Dialogues"],
        key="chapter_dialogue_display_mode",
        help="Chapter Summary: Merge and display all sentence dialogues; Sentence-Level Detailed: Display each sentence's dialogue"
    )
    
    if display_mode == "Chapter Summary Dialogues":
        show_chapter_summary_dialogues(chapter_dialogues)
    else:
        show_chapter_sentence_dialogues(chapter_dialogues)

def show_chapter_summary_dialogues(chapter_dialogues):
    """Show chapter summary dialogues (original display method)"""
    st.markdown("#### 📖 Chapter Summary Dialogues")
    
    # Organize dialogue data by chapter
    chapter_summary = organize_dialogues_by_chapter(chapter_dialogues)
    
    # Create chapter selector
    chapter_options = [f"Chapter {i+1}" for i in range(len(chapter_summary))]
    selected_chapter = st.selectbox("Select Chapter", chapter_options, key="chapter_summary_selector")
    
    if selected_chapter:
        chapter_idx = int(selected_chapter.replace("Chapter ", "")) - 1
        
        if 0 <= chapter_idx < len(chapter_summary):
            chapter_data = chapter_summary[chapter_idx]
            
            # Show chapter information
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📖 **Chapter**: {selected_chapter}")
                if chapter_idx < len(st.session_state.story_data):
                    story_chapter = st.session_state.story_data[chapter_idx]
                    st.info(f"📝 **Title**: {story_chapter.get('title', 'Unknown')}")
            
            with col2:
                st.metric("Dialogue Turns", len(chapter_data['dialogues']))
                st.metric("Participating Characters", len(chapter_data['characters']))
            
            with col3:
                st.metric("Total Sentences", chapter_data['sentence_count'])
                st.metric("Dialogue Sentences", chapter_data['dialogue_sentence_count'])
            
            # Display character list
            if chapter_data['characters']:
                st.markdown("**👥 Participating Characters:**")
                character_cols = st.columns(min(len(chapter_data['characters']), 4))
                for i, char in enumerate(chapter_data['characters']):
                    with character_cols[i % len(character_cols)]:
                        st.markdown(f" **{char}**")
            
            st.markdown("---")
            
            # Display complete chapter dialogue
            if chapter_data['dialogues']:
                st.markdown("##### 💬 Complete Chapter Dialogue")
                
                for i, dialogue in enumerate(chapter_data['dialogues']):
                    dialogue_text = dialogue.get('dialogue', dialogue.get('line', ''))
                    speaker = dialogue.get('speaker', 'Unknown Character')
                    action = dialogue.get('action', '')
                    sentence_context = dialogue.get('sentence_context', '')
                    
                    # Create dialogue card
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        
                        with col1:
                            st.markdown(f"** {speaker}**")
                        
                        with col2:
                            st.markdown(f"💬 {dialogue_text}")
                            if action:
                                st.markdown(f"* {action}*")
                            if sentence_context:
                                with st.expander(" Scene Context", expanded=False):
                                    st.caption(sentence_context)
                        
                        # Add separator (except for last dialogue)
                        if i < len(chapter_data['dialogues']) - 1:
                            st.markdown("---")
            else:
                st.info("📝 This chapter has no dialogue content")

def organize_dialogues_by_chapter(chapter_dialogues):
    """Organize sentence-level dialogues by chapter"""
    # Assume every 6 sentences is one chapter (adjust according to your data)
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
        
        # Collect dialogues for this sentence
        dialogues = sentence_data.get("dialogue", [])
        if dialogues:
            dialogue_sentence_count += 1
            for dialogue in dialogues:
                # Add sentence context
                dialogue_with_context = dialogue.copy()
                dialogue_with_context['sentence_context'] = sentence_data.get('sentence', '')
                current_chapter_dialogues.append(dialogue_with_context)
                current_chapter_characters.add(dialogue.get('speaker', 'Unknown'))
        
        # Create a chapter every 6 sentences or when reaching the end
        if (i + 1) % sentences_per_chapter == 0 or i == len(chapter_dialogues) - 1:
            chapter_summary.append({
                'sentences': current_chapter,
                'dialogues': current_chapter_dialogues,
                'characters': list(current_chapter_characters),
                'sentence_count': sentence_count,
                'dialogue_sentence_count': dialogue_sentence_count
            })
            
            # Reset counters
            current_chapter = []
            current_chapter_dialogues = []
            current_chapter_characters = set()
            sentence_count = 0
            dialogue_sentence_count = 0
    
    return chapter_summary

def show_chapter_sentence_dialogues(chapter_dialogues):
    """Show chapter sentence-level dialogues (original display method)"""
    st.markdown("#### 📝 Sentence-Level Detailed Dialogues")
    
    # Create chapter selector (every 6 sentences as one chapter)
    sentences_per_chapter = 6
    total_chapters = (len(chapter_dialogues) + sentences_per_chapter - 1) // sentences_per_chapter
    chapter_options = [f"Chapter {i+1}" for i in range(total_chapters)]
    selected_chapter = st.selectbox("Select Chapter", chapter_options, key="chapter_sentence_selector")
    
    if selected_chapter:
        chapter_idx = int(selected_chapter.replace("Chapter ", "")) - 1
        
        # Calculate sentence range for this chapter
        start_idx = chapter_idx * sentences_per_chapter
        end_idx = min(start_idx + sentences_per_chapter, len(chapter_dialogues))
        
        st.info(f"Displaying sentences {start_idx + 1}-{end_idx}, Total {end_idx - start_idx} sentences")
        
        # Display sentence dialogues for this chapter
        for i in range(start_idx, end_idx):
            if i < len(chapter_dialogues):
                sentence_data = chapter_dialogues[i]
                
                with st.expander(f"Sentence {i+1}: {sentence_data.get('sentence', '')[:50]}...", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**📝 Original Sentence**: {sentence_data.get('sentence', '')}")
                        
                        dialogues = sentence_data.get('dialogue', [])
                        if dialogues:
                            st.markdown("**💬 Generated Dialogue**:")
                            for j, dialogue in enumerate(dialogues):
                                # Compatible with different field names
                                dialogue_text = dialogue.get('dialogue', dialogue.get('line', ''))
                                speaker = dialogue.get('speaker', '')
                                action = dialogue.get('action', '')
                                
                                st.markdown(f"  {j+1}. **{speaker}**: {dialogue_text}")
                                if action:
                                    st.markdown(f"     *{action}*")
                    
                    with col2:
                        st.markdown(f"**💬 Needs Dialogue**: {'Yes' if sentence_data.get('need_to_action') else 'No'}")
                        actors = sentence_data.get('actor_list', [])
                        if actors:
                            st.markdown(f"**👥 Participating Characters**: {', '.join(actors)}")

def show_sentence_dialogues(sentence_dialogues):
    """Display sentence-level dialogues"""
    if not sentence_dialogues:
        st.info("📝 No sentence dialogue data available")
        return
    
    st.markdown("##### 📝 Sentence-Level Dialogue Details")
    
    # Paginated display
    items_per_page = 10
    total_pages = (len(sentence_dialogues) + items_per_page - 1) // items_per_page
    
    if total_pages > 1:
        page = st.selectbox("Select Page", range(1, total_pages + 1), key="sentence_dialogue_page") - 1
    else:
        page = 0
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(sentence_dialogues))
    
    st.info(f"Displaying items {start_idx + 1}-{end_idx}, Total {len(sentence_dialogues)} items")
    
    for i in range(start_idx, end_idx):
        sentence_dialogue = sentence_dialogues[i]
        
        with st.expander(f"Sentence {i+1}: {sentence_dialogue.get('sentence', '')[:50]}...", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**📝 Original Sentence**: {sentence_dialogue.get('sentence', '')}")
                
                dialogues = sentence_dialogue.get('dialogue', [])
                if dialogues:
                    st.markdown("**💬 Generated Dialogue**:")
                    for j, dialogue in enumerate(dialogues):
                        # Compatible with different field names
                        dialogue_text = dialogue.get('dialogue', dialogue.get('line', ''))
                        speaker = dialogue.get('speaker', '')
                        action = dialogue.get('action', '')
                        
                        st.markdown(f"  {j+1}. **{speaker}**: {dialogue_text}")
                        if action:
                            st.markdown(f"     *{action}*")
            
            with col2:
                st.markdown(f"**💬 Needs Dialogue**: {'Yes' if sentence_dialogue.get('need_to_action') else 'No'}")
                actors = sentence_dialogue.get('actor_list', [])
                if actors:
                    st.markdown(f"**👥 Participating Characters**: {', '.join(actors)}")

def show_behavior_timeline(behavior_timeline):
    """Display behavior timeline"""
    if not behavior_timeline:
        st.info("📝 No behavior timeline data available")
        return
    
    st.markdown("##### 🕰️ Character Behavior Timeline")
    
    # Statistics
    characters = set(item.get("character", "") for item in behavior_timeline)
    chapters = set(item.get("chapter_id", "") for item in behavior_timeline)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Behaviors", len(behavior_timeline))
    with col2:
        st.metric("Characters Involved", len(characters))
    with col3:
        st.metric("Chapters Involved", len(chapters))
    
    # Display mode selection
    display_mode = st.radio(
        "Display Mode",
        ["Character Development Arcs", "Timeline List", "Chapter Grouping"],
        key="behavior_display_mode",
        help="Character Development Arcs: Show complete development process by character; Timeline List: Display in chronological order; Chapter Grouping: Display grouped by chapters"
    )
    
    if display_mode == "Character Development Arcs":
        show_character_development_arcs(behavior_timeline, characters)
    elif display_mode == "Timeline List":
        show_timeline_list(behavior_timeline, characters, chapters)
    else:  # Chapter grouping
        show_chapter_grouped_behavior(behavior_timeline, chapters)

def show_character_development_arcs(behavior_timeline, characters):
    """Display character development arcs"""
    st.markdown("#### 📈 Character Development Arcs")
    
    # Organize data by character
    character_arcs = {}
    for item in behavior_timeline:
        char = item.get("character", "Unknown")
        if char not in character_arcs:
            character_arcs[char] = []
        character_arcs[char].append(item)
    
    # Sort by chapter and sentence
    for char in character_arcs:
        character_arcs[char].sort(key=lambda x: (x.get("chapter_id", ""), x.get("sentence_index", 0)))
    
    # Select characters to view
    if len(characters) > 1:
        selected_chars = st.multiselect(
            "Select Characters to View",
            list(characters),
            default=list(characters)[:3] if len(characters) > 3 else list(characters),
            key="selected_chars_arc"
        )
    else:
        selected_chars = list(characters)
    
    for char in selected_chars:
        if char in character_arcs:
            with st.expander(f"👤 {char}'s Development Arc", expanded=True):
                arc_data = character_arcs[char]
                
                # Display character statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Behavior Events", len(arc_data))
                with col2:
                    chapters_involved = set(item.get("chapter_id", "") for item in arc_data)
                    st.metric("Chapters Involved", len(chapters_involved))
                with col3:
                    unique_behaviors = set(item.get("behavior", "") for item in arc_data)
                    st.metric("Behavior Types", len(unique_behaviors))
                
                # Display development timeline
                st.markdown("**📈 Development Timeline:**")
                
                for i, item in enumerate(arc_data):
                    chapter_id = item.get("chapter_id", "")
                    sentence_idx = item.get("sentence_index", 0)
                    behavior = item.get("behavior", "")
                    scene_context = item.get("scene_context", "")
                    
                    # Create timeline entry
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        st.markdown(f"**{i+1}.** `{chapter_id}`")
                        st.caption(f"Sentence {sentence_idx}")
                    
                    with col2:
                        st.markdown(f"**💭 {behavior}**")
                        if scene_context:
                            st.caption(f" {scene_context[:100]}{'...' if len(scene_context) > 100 else ''}")
                    
                    # Add connecting line (except for last one)
                    if i < len(arc_data) - 1:
                        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;↓")
                
                # Display behavior summary
                st.markdown("**📊 Behavior Summary:**")
                behavior_summary = {}
                for item in arc_data:
                    behavior = item.get("behavior", "")
                    if behavior in behavior_summary:
                        behavior_summary[behavior] += 1
                    else:
                        behavior_summary[behavior] = 1
                
                for behavior, count in sorted(behavior_summary.items(), key=lambda x: x[1], reverse=True):
                    st.markdown(f"- **{behavior}** (appeared {count} time{'s' if count > 1 else ''})")

def show_timeline_list(behavior_timeline, characters, chapters):
    """Display timeline list"""
    st.markdown("#### ⏰ Timeline List")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        selected_character = st.selectbox("Filter Character", ["All"] + list(characters), key="behavior_character_filter")
    with col2:
        selected_chapter = st.selectbox("Filter Chapter", ["All"] + list(chapters), key="behavior_chapter_filter")
    
    # Filter data
    filtered_timeline = behavior_timeline
    if selected_character != "All":
        filtered_timeline = [item for item in filtered_timeline if item.get("character") == selected_character]
    if selected_chapter != "All":
        filtered_timeline = [item for item in filtered_timeline if item.get("chapter_id") == selected_chapter]
    
    # Sort by time
    filtered_timeline.sort(key=lambda x: (x.get("chapter_id", ""), x.get("sentence_index", 0)))
    
    # Paginated display
    items_per_page = 15
    total_pages = (len(filtered_timeline) + items_per_page - 1) // items_per_page
    
    if total_pages > 1:
        page = st.selectbox("Select Page", range(1, total_pages + 1), key="behavior_timeline_page") - 1
    else:
        page = 0
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(filtered_timeline))
    
    st.info(f"Displaying items {start_idx + 1}-{end_idx}, Total {len(filtered_timeline)} items")
    
    # Display timeline
    for i in range(start_idx, end_idx):
        item = filtered_timeline[i]
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 3])
        
        with col1:
            st.markdown(f"**👤 {item.get('character', 'Unknown')}**")
        
        with col2:
            st.markdown(f"📖 {item.get('chapter_id', '')}")
        
        with col3:
            st.markdown(f"📝 Sentence {item.get('sentence_index', 0)}")
        
        with col4:
            st.markdown(f"💭 {item.get('behavior', '')}")
        
        # Display scene context
        if item.get('scene_context'):
            with st.expander(f"🎬 Scene Context {i+1}", expanded=False):
                st.text(item.get('scene_context', ''))
        
        if i < end_idx - 1:
            st.markdown("---")

def show_chapter_grouped_behavior(behavior_timeline, chapters):
    """Display behavior grouped by chapters"""
    st.markdown("#### 📖 Behavior Grouped by Chapters")
    
    # Organize data by chapters
    chapter_behaviors = {}
    for item in behavior_timeline:
        chapter = item.get("chapter_id", "Unknown Chapter")
        if chapter not in chapter_behaviors:
            chapter_behaviors[chapter] = []
        chapter_behaviors[chapter].append(item)
    
    # Sort by chapters
    sorted_chapters = sorted(chapter_behaviors.keys())
    
    for chapter in sorted_chapters:
        behaviors = chapter_behaviors[chapter]
        
        with st.expander(f"📖 {chapter} ({len(behaviors)} behavior events)", expanded=False):
            # Sort by sentence index
            behaviors.sort(key=lambda x: x.get("sentence_index", 0))
            
            # Count characters in this chapter
            chapter_characters = set(item.get("character", "") for item in behaviors)
            st.info(f"Characters involved: {', '.join(chapter_characters)}")
            
            # Display behavior list
            for i, item in enumerate(behaviors):
                col1, col2, col3 = st.columns([2, 1, 3])
                
                with col1:
                    st.markdown(f"**👤 {item.get('character', 'Unknown')}**")
                
                with col2:
                    st.markdown(f"📝 Sentence {item.get('sentence_index', 0)}")
                
                with col3:
                    st.markdown(f"💭 {item.get('behavior', '')}")
                
                if i < len(behaviors) - 1:
                    st.markdown("---")

def show_dialogue_edit_mode():
    """Dialogue editing mode"""
    if not st.session_state.get('dialogue_data'):
        st.info("📝 No dialogue data available, please generate dialogue first")
        return
    
    st.markdown("#### ✏️ Edit Dialogue Content")
    
    # History operation panel
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("↩️ Undo", use_container_width=True):
            undo_dialogue_action()
    with col2:
        if st.button("↪️ Redo", use_container_width=True):
            redo_dialogue_action()
    with col3:
        if st.button("📜 History", use_container_width=True):
            st.session_state.show_dialogue_history = not st.session_state.get('show_dialogue_history', False)
    
    # Display history panel
    if st.session_state.get('show_dialogue_history', False):
        show_dialogue_history_panel()
    
    st.markdown("---")
    
    # Edit options
    edit_tab1, edit_tab2 = st.tabs(["🔄 Regenerate", "✏️ Manual Edit"])
    
    with edit_tab1:
        show_dialogue_regeneration_options()
    
    with edit_tab2:
        show_dialogue_manual_edit()

def show_dialogue_history_panel():
    """Show dialogue history panel"""
    st.markdown("##### 📜 Dialogue Operation History")
    
    if not st.session_state.dialogue_history:
        st.info("📝 No history records")
        return
    
    # Display current position
    current_idx = st.session_state.dialogue_history_index
    total_count = len(st.session_state.dialogue_history)
    st.info(f"📍 Current position: {current_idx + 1}/{total_count}")
    
    # Display history records
    for i, entry in enumerate(reversed(st.session_state.dialogue_history)):
        actual_idx = total_count - 1 - i
        is_current = actual_idx == current_idx
        
        with st.expander(
            f"{'' if is_current else ''} {entry['action']} - {entry['timestamp'][:19]}",
            expanded=is_current
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Operation**: {entry['action']}")
            with col2:
                st.markdown(f"**Time**: {entry['timestamp'][:19]}")
            with col3:
                st.markdown(f"**Data Amount**: {entry.get('data_length', 0)} items")
            
            if not is_current:
                if st.button(f"🔄 Restore to this state", key=f"restore_dialogue_{actual_idx}"):
                    st.session_state.dialogue_history_index = actual_idx
                    st.session_state.dialogue_data = copy.deepcopy(entry["dialogue_data"])
                    st.success(f"✅ Restored to: {entry['action']}")
                    st.rerun()
        
        if i < len(st.session_state.dialogue_history) - 1:
            st.markdown("---")

def show_dialogue_regeneration_options():
    """Dialogue regeneration options"""
    st.markdown("##### 🔄 Regenerate Dialogue")
    
    # Select regeneration scope
    regen_scope = st.radio(
        "Regeneration Scope",
        ["Single Chapter", "All Chapters", "Specific Character"],
        key="dialogue_regen_scope"
    )
    
    if regen_scope == "Single Chapter":
        chapter_options = [f"Chapter {i+1}" for i in range(len(st.session_state.story_data))]
        selected_chapter = st.selectbox("Select Chapter", chapter_options, key="regen_chapter_selector")
        
        if st.button("🔄 Regenerate Chapter Dialogue", type="primary"):
            chapter_idx = int(selected_chapter.replace("Chapter ", "")) - 1
            regenerate_single_chapter_dialogue(chapter_idx)
    
    elif regen_scope == "All Chapters":
        st.warning("⚠️ This will regenerate dialogue for all chapters and may take a long time")
        
        if st.button("🔄 Regenerate All Dialogues", type="primary"):
            regenerate_all_dialogues()
    
    elif regen_scope == "Specific Character":
        characters = [char.get("name", f"Character{i+1}") for i, char in enumerate(st.session_state.characters_data)]
        selected_character = st.selectbox("Select Character", characters, key="regen_character_selector")
        
        if st.button("🔄 Regenerate Character Dialogue", type="primary"):
            regenerate_character_dialogues(selected_character)

def regenerate_single_chapter_dialogue(chapter_idx):
    """Regenerate single chapter dialogue"""
    try:
        print(f"🔄🔄🔄 [Dialogue Regen] ===== Starting regeneration for Chapter {chapter_idx+1} =====")
        
        # Save current state
        save_dialogue_to_history(f"Before regenerating Chapter {chapter_idx+1} dialogue")
        
        with st.spinner(f"🔄 Regenerating Chapter {chapter_idx+1} dialogue..."):
            # Get story content for this chapter
            if chapter_idx >= len(st.session_state.story_data):
                st.error(f"❌ Chapter index out of range: {chapter_idx}")
                return
            
            chapter_story = [st.session_state.story_data[chapter_idx]]
            
            # Call backend for regeneration
            chapter_results, sentence_results, behavior_timeline = analyze_dialogue_insertions_v2(
                chapter_story, 
                st.session_state.characters_data
            )
            
            # Update dialogue data
            if st.session_state.dialogue_data and "chapter_dialogues" in st.session_state.dialogue_data:
                # Update dialogue for specified chapter
                st.session_state.dialogue_data["chapter_dialogues"][chapter_idx] = chapter_results[0] if chapter_results else {}
                
                # Update sentence-level dialogue (need to find corresponding sentences)
                # Simplified processing here, may need more complex matching logic in practice
                if sentence_results:
                    # Find and replace sentence dialogues belonging to this chapter
                    chapter_id = st.session_state.story_data[chapter_idx].get("chapter_id", f"chapter_{chapter_idx+1}")
                    
                    # Remove old sentence dialogues for this chapter
                    old_sentence_dialogues = st.session_state.dialogue_data.get("sentence_dialogues", [])
                    new_sentence_dialogues = [s for s in old_sentence_dialogues if not s.get("sentence", "").startswith(chapter_id)]
                    
                    # Add new sentence dialogues
                    new_sentence_dialogues.extend(sentence_results)
                    st.session_state.dialogue_data["sentence_dialogues"] = new_sentence_dialogues
                
                # Update behavior timeline
                if behavior_timeline:
                    old_timeline = st.session_state.dialogue_data.get("behavior_timeline", [])
                    chapter_id = st.session_state.story_data[chapter_idx].get("chapter_id", f"chapter_{chapter_idx+1}")
                    
                    # Remove old behavior for this chapter
                    new_timeline = [b for b in old_timeline if b.get("chapter_id") != chapter_id]
                    
                    # Add new behavior
                    new_timeline.extend(behavior_timeline)
                    st.session_state.dialogue_data["behavior_timeline"] = new_timeline
            
            print(f"🔄 [Dialogue Regen] Chapter {chapter_idx+1} dialogue regeneration completed")
            st.success(f"✅ Chapter {chapter_idx+1} dialogue regeneration completed!")
            
            # Save operation to history
            save_dialogue_to_history(f"Chapter {chapter_idx+1} dialogue regeneration completed")
            
    except Exception as e:
        error_msg = f"Chapter {chapter_idx+1} dialogue regeneration failed: {str(e)}"
        print(f" [Dialogue Regen] {error_msg}")
        st.error(f" {error_msg}")

def regenerate_all_dialogues(behavior_model="gpt-4.1"):
    """Regenerate all dialogues"""
    try:
        print(f"🔄🔄🔄 [Dialogue Regen] ===== Starting regeneration of all dialogues =====")
        
        # Save current state
        save_dialogue_to_history("Before regenerating all dialogues")
        
        # Directly call generation function
        generate_dialogues_from_story(use_cache=False, auto_save=True, behavior_model=behavior_model)
        
        print(f"🔄🔄🔄 [Dialogue Regen] ===== All dialogue regeneration completed =====")
        
    except Exception as e:
        error_msg = f"Regenerating all dialogues failed: {str(e)}"
        print(f" [Dialogue Regen] {error_msg}")
        st.error(f" {error_msg}")

def regenerate_character_dialogues(character_name):
    """Regenerate specific character dialogue"""
    try:
        print(f"🔄🔄🔄 [Dialogue Regen] ===== Starting regeneration for character {character_name} =====")
        
        # Save current state
        save_dialogue_to_history(f"Before regenerating character {character_name} dialogue")
        
        with st.spinner(f"🔄 Regenerating character {character_name} dialogue..."):
            # Character-specific dialogue regeneration logic needs to be implemented here
            # Due to backend API limitations, using full regeneration temporarily
            st.warning("⚠️ Current version does not support regenerating specific character dialogue separately, will regenerate all dialogues")
            regenerate_all_dialogues()
        
        print(f"🔄 [Dialogue Regen] Character {character_name} dialogue regeneration completed")
        
    except Exception as e:
        error_msg = f"Regenerating character {character_name} dialogue failed: {str(e)}"
        print(f" [Dialogue Regen] {error_msg}")
        st.error(f" {error_msg}")

def show_dialogue_manual_edit():
    """Manual dialogue editing"""
    st.markdown("##### ✏️ Manual Dialogue Content Editing")
    
    if not st.session_state.get('dialogue_data', {}).get('chapter_dialogues'):
        st.info("📝 No chapter dialogue data available for editing")
        return
    
    # Select chapter to edit
    chapter_options = [f"Chapter {i+1}" for i in range(len(st.session_state.dialogue_data["chapter_dialogues"]))]
    selected_chapter = st.selectbox("Select Chapter to Edit", chapter_options, key="edit_chapter_selector")
    
    if selected_chapter:
        chapter_idx = int(selected_chapter.replace("Chapter ", "")) - 1
        
        if 0 <= chapter_idx < len(st.session_state.dialogue_data["chapter_dialogues"]):
            edit_chapter_dialogue(chapter_idx)

def edit_chapter_dialogue(chapter_idx):
    """Edit dialogue for specified chapter"""
    chapter_dialogue = st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]
    dialogues = chapter_dialogue.get("dialogue", [])
    
    st.markdown(f"##### Edit Chapter {chapter_idx+1} Dialogue")
    
    if not dialogues:
        st.info("📝 This chapter has no dialogue content")
        
        # Add new dialogue
        if st.button("➕ Add Dialogue", key=f"add_dialogue_{chapter_idx}"):
            add_new_dialogue_to_chapter(chapter_idx)
        return
    
    # Display existing dialogues and provide editing functionality
    for i, dialogue in enumerate(dialogues):
        # Compatible with different field names
        dialogue_text = dialogue.get('dialogue', dialogue.get('line', ''))
        speaker = dialogue.get('speaker', 'Unknown')
        
        with st.expander(f"Dialogue {i+1}: {speaker} - {dialogue_text[:30]}...", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Edit dialogue content
                new_speaker = st.text_input(
                    "Character Name", 
                    value=speaker, 
                    key=f"edit_speaker_{chapter_idx}_{i}"
                )
                
                new_dialogue = st.text_area(
                    "Dialogue Content", 
                    value=dialogue_text, 
                    key=f"edit_dialogue_{chapter_idx}_{i}",
                    height=100
                )
                
                new_action = st.text_area(
                    "Action Description", 
                    value=dialogue.get('action', ''), 
                    key=f"edit_action_{chapter_idx}_{i}",
                    height=60
                )
            
            with col2:
                # Action buttons
                if st.button("💾 Save Changes", key=f"save_dialogue_{chapter_idx}_{i}"):
                    save_dialogue_edit(chapter_idx, i, new_speaker, new_dialogue, new_action)
                
                if st.button("🗑️ Delete Dialogue", key=f"delete_dialogue_{chapter_idx}_{i}"):
                    delete_dialogue_from_chapter(chapter_idx, i)
    
    # Add new dialogue
    st.markdown("---")
    if st.button("➕ Add New Dialogue", key=f"add_new_dialogue_{chapter_idx}"):
        add_new_dialogue_to_chapter(chapter_idx)

def save_dialogue_edit(chapter_idx, dialogue_idx, new_speaker, new_dialogue, new_action):
    """Save dialogue editing"""
    try:
        print(f"💾 [Dialogue Edit] Saving changes to dialogue {dialogue_idx+1} in Chapter {chapter_idx+1}")
        
        # Save current state
        save_dialogue_to_history(f"Before editing Chapter {chapter_idx+1} dialogue {dialogue_idx+1}")
        
        # Update dialogue content - use "line" field to maintain consistency with backend data format
        st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]["dialogue"][dialogue_idx] = {
            "speaker": new_speaker,
            "line": new_dialogue,  # Use "line" field
            "action": new_action
        }
        
        # Save operation to history
        save_dialogue_to_history(f"Chapter {chapter_idx+1} dialogue {dialogue_idx+1} editing completed")
        
        st.success(f"✅ Chapter {chapter_idx+1} dialogue {dialogue_idx+1} changes saved")
        st.rerun()
        
    except Exception as e:
        error_msg = f"Save dialogue editing failed: {str(e)}"
        print(f"❌ [Dialogue Edit] {error_msg}")
        st.error(f" {error_msg}")

def delete_dialogue_from_chapter(chapter_idx, dialogue_idx):
    """Delete dialogue from chapter"""
    try:
        print(f"🗑️ [Dialogue Delete] Deleting dialogue {dialogue_idx+1} from Chapter {chapter_idx+1}")
        
        # Save current state
        save_dialogue_to_history(f"Before deleting Chapter {chapter_idx+1} dialogue {dialogue_idx+1}")
        
        # Delete dialogue
        dialogues = st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]["dialogue"]
        if 0 <= dialogue_idx < len(dialogues):
            dialogues.pop(dialogue_idx)
        
        # Save operation to history
        save_dialogue_to_history(f"Chapter {chapter_idx+1} dialogue {dialogue_idx+1} deletion completed")
        
        st.success(f"✅ Chapter {chapter_idx+1} dialogue {dialogue_idx+1} deleted")
        st.rerun()
        
    except Exception as e:
        error_msg = f"Delete dialogue failed: {str(e)}"
        print(f"❌ [Dialogue Delete] {error_msg}")
        st.error(f" {error_msg}")

def add_new_dialogue_to_chapter(chapter_idx):
    """Add new dialogue to chapter"""
    st.markdown(f"##### ➕ Add New Dialogue to Chapter {chapter_idx+1}")
    
    # Get available characters
    characters = [char.get("name", f"Character{i+1}") for i, char in enumerate(st.session_state.characters_data)]
    
    with st.form(f"add_dialogue_form_{chapter_idx}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_speaker = st.selectbox("Select Character", characters + ["Other"], key=f"new_speaker_{chapter_idx}")
            if new_speaker == "Other":
                new_speaker = st.text_input("Custom Character Name", key=f"custom_speaker_{chapter_idx}")
        
        with col2:
            st.write("")  # Placeholder
        
        new_dialogue = st.text_area("Dialogue Content", key=f"new_dialogue_content_{chapter_idx}", height=100)
        new_action = st.text_area("Action Description (Optional)", key=f"new_action_{chapter_idx}", height=60)
        
        if st.form_submit_button("➕ Add Dialogue"):
            if new_speaker and new_dialogue:
                try:
                    # Save current state
                    save_dialogue_to_history(f"Before adding new dialogue to Chapter {chapter_idx+1}")
                    
                    # Add new dialogue - use "line" field to maintain consistency with backend data format
                    new_dialogue_item = {
                        "speaker": new_speaker,
                        "line": new_dialogue,  # Use "line" field
                        "action": new_action
                    }
                    
                    if "dialogue" not in st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]:
                        st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]["dialogue"] = []
                    
                    st.session_state.dialogue_data["chapter_dialogues"][chapter_idx]["dialogue"].append(new_dialogue_item)
                    
                    # Save operation to history
                    save_dialogue_to_history(f"Adding new dialogue to Chapter {chapter_idx+1} completed")
                    
                    st.success(f"✅ New dialogue added to Chapter {chapter_idx+1}")
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"Add new dialogue failed: {str(e)}"
                    print(f"❌ [Dialogue Add] {error_msg}")
                    st.error(f" {error_msg}")
            else:
                st.error("❌ Please fill in character name and dialogue content")

def show_dialogue_file_management():
    """Dialogue file management"""
    st.markdown("#### 📁 Dialogue File Management")
    
    # File operation options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save to Project", type="primary", use_container_width=True):
            save_dialogue_to_project()
    
    with col2:
        if st.button("📁 Load Dialogue File", use_container_width=True):
            st.session_state.show_dialogue_loader_file = True
            st.rerun()
    
    with col3:
        if st.button("📤 Export Dialogue", use_container_width=True):
            export_dialogue_files()
    
    # Show dialogue loader
    if st.session_state.get('show_dialogue_loader_file', False):
        load_existing_dialogue("file_management")
    
    # Display current dialogue file information
    if st.session_state.get('dialogue_data'):
        st.markdown("---")
        st.markdown("##### 📊 Current Dialogue Data Information")
        
        dialogue_data = st.session_state.dialogue_data
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            chapter_count = len(dialogue_data.get("chapter_dialogues", []))
            st.metric("Chapter Dialogues", chapter_count)
        
        with col2:
            sentence_count = len(dialogue_data.get("sentence_dialogues", []))
            st.metric("Sentence Dialogues", sentence_count)
        
        with col3:
            behavior_count = len(dialogue_data.get("behavior_timeline", []))
            st.metric("Behavior Events", behavior_count)
        
        with col4:
            generation_params = dialogue_data.get("generation_params", {})
            timestamp = generation_params.get("timestamp", "Unknown")
            st.metric("Generation Time", timestamp[:10] if timestamp != "Unknown" else "Unknown")

def save_dialogue_to_project():
    """Save dialogue to project directory"""
    try:
        if not st.session_state.get('dialogue_data'):
            st.warning("⚠️ No dialogue data available to save")
            return
        
        print(f"💾 [Dialogue Save] ===== Starting to save dialogue to project =====")
        
        start_time = time.time()
        
        # Save chapter dialogues
        chapter_dialogues = st.session_state.dialogue_data.get("chapter_dialogues", [])
        save_json(chapter_dialogues, st.session_state.current_version, "dialogue_marks.json")
        
        # Save sentence dialogues
        sentence_dialogues = st.session_state.dialogue_data.get("sentence_dialogues", [])
        save_json(sentence_dialogues, st.session_state.current_version, "sentence_dialogues.json")
        
        # Save behavior timeline
        behavior_timeline = st.session_state.dialogue_data.get("behavior_timeline", [])
        save_json(behavior_timeline, st.session_state.current_version, "behavior_timeline_raw.json")
        
        # Save complete dialogue data
        save_json(st.session_state.dialogue_data, st.session_state.current_version, "dialogue_complete.json")
        
        end_time = time.time()
        
        # Log operation
        log_backend_operation(
            "Save Dialogue to Project", 
            {"version": st.session_state.current_version},
            start_time, end_time, 
            {
                "chapter_dialogues": len(chapter_dialogues),
                "sentence_dialogues": len(sentence_dialogues),
                "behavior_timeline": len(behavior_timeline)
            }
        )
        
        print(f"💾 [Dialogue Save] Chapter dialogues: {len(chapter_dialogues)} items")
        print(f"💾 [Dialogue Save] Sentence dialogues: {len(sentence_dialogues)} items")
        print(f"💾 [Dialogue Save] Behavior timeline: {len(behavior_timeline)} items")
        print(f"💾 [Dialogue Save] ===== Save completed =====")
        
        st.success(f"✅ Dialogue data saved to project directory: {st.session_state.current_version}/")
        
        # Display save details
        with st.expander("📄 Save Details", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.json({
                    "Version Directory": st.session_state.current_version,
                    "Chapter Dialogue File": "dialogue_marks.json",
                    "Sentence Dialogue File": "sentence_dialogues.json"
                })
            with col2:
                st.json({
                    "Behavior Timeline File": "behavior_timeline_raw.json",
                    "Complete Data File": "dialogue_complete.json",
                    "Save Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
    except Exception as e:
        error_msg = f"Save dialogue to project failed: {str(e)}"
        print(f"❌ [Dialogue Save] {error_msg}")
        st.error(f" {error_msg}")

def load_existing_dialogue(context="default"):
    """Load existing dialogue file"""
    st.markdown("##### 📁 Load Dialogue File")
    
    # Provide two loading methods
    load_method = st.radio(
        "Select Loading Method",
        ["Single File Load (Recommended)", "Multi-File Load"],
        key=f"load_method_{context}",
        help="Single File: Load complete dialogue data file; Multi-File: Load chapter dialogue, sentence dialogue, and behavior timeline files separately"
    )
    
    if load_method == "Single File Load (Recommended)":
        # Single file uploader
        uploaded_file = st.file_uploader(
            "Select Complete Dialogue File",
            type=['json'],
            help="Recommend uploading dialogue_complete.json file, which contains all dialogue data",
            key=f"dialogue_file_uploader_{context}"
        )
        
        if uploaded_file is not None:
            process_single_dialogue_file(uploaded_file, context)
    
    else:
        # Multi-file uploader
        st.markdown("##### 📁 Upload Dialogue Files Separately")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            chapter_file = st.file_uploader(
                "Chapter Dialogue File",
                type=['json'],
                help="dialogue_marks.json",
                key=f"chapter_dialogue_uploader_{context}"
            )
        
        with col2:
            sentence_file = st.file_uploader(
                "Sentence Dialogue File",
                type=['json'],
                help="sentence_dialogues.json",
                key=f"sentence_dialogue_uploader_{context}"
            )
        
        with col3:
            behavior_file = st.file_uploader(
                "Behavior Timeline File",
                type=['json'],
                help="behavior_timeline_raw.json",
                key=f"behavior_timeline_uploader_{context}"
            )
        
        if any([chapter_file, sentence_file, behavior_file]):
            process_multiple_dialogue_files(chapter_file, sentence_file, behavior_file, context)

def process_single_dialogue_file(uploaded_file, context):
    """Process single dialogue file"""
    try:
        # Read file content
        uploaded_file.seek(0)
        file_content = uploaded_file.read().decode('utf-8')
        dialogue_data = json.loads(file_content)
        
        print(f"📁 [Dialogue Load] File name: {uploaded_file.name}")
        print(f"📁 [Dialogue Load] File size: {len(file_content)} characters")
        print(f"📁 [Dialogue Load] Data type: {type(dialogue_data)}")
        
        # Validate file format
        if validate_dialogue_file(dialogue_data, uploaded_file.name):
            # Display preview
            with st.expander("📄 File Preview", expanded=True):
                if isinstance(dialogue_data, dict):
                    # Complete dialogue data format
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        chapter_count = len(dialogue_data.get("chapter_dialogues", []))
                        st.metric("Chapter Dialogues", chapter_count)
                    with col2:
                        sentence_count = len(dialogue_data.get("sentence_dialogues", []))
                        st.metric("Sentence Dialogues", sentence_count)
                    with col3:
                        behavior_count = len(dialogue_data.get("behavior_timeline", []))
                        st.metric("Behavior Events", behavior_count)
                elif isinstance(dialogue_data, list):
                    # Single data format
                    st.metric("Data Items", len(dialogue_data))
            
            # Load confirmation
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Confirm Load", type="primary", use_container_width=True, key=f"confirm_load_{context}"):
                    load_dialogue_data(dialogue_data, uploaded_file.name, context)
            
            with col2:
                if st.button("❌ Cancel", use_container_width=True, key=f"cancel_load_{context}"):
                    close_dialogue_loader(context)
        
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON parsing failed: {str(e)}")
    except Exception as e:
        st.error(f"❌ File loading failed: {str(e)}")

def process_multiple_dialogue_files(chapter_file, sentence_file, behavior_file, context):
    """Process multiple dialogue files"""
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
        
        # Load chapter dialogue file
        if chapter_file is not None:
            try:
                chapter_file.seek(0)
                chapter_content = chapter_file.read().decode('utf-8')
                chapter_data = json.loads(chapter_content)
                dialogue_data["chapter_dialogues"] = chapter_data if isinstance(chapter_data, list) else []
                files_loaded.append(f"Chapter Dialogue: {chapter_file.name}")
                print(f"📁 [Multi-File Load] Chapter dialogue file loaded successfully: {len(dialogue_data['chapter_dialogues'])} items")
            except Exception as e:
                st.error(f"❌ Chapter dialogue file loading failed: {str(e)}")
        
        # Load sentence dialogue file
        if sentence_file is not None:
            try:
                sentence_file.seek(0)
                sentence_content = sentence_file.read().decode('utf-8')
                sentence_data = json.loads(sentence_content)
                dialogue_data["sentence_dialogues"] = sentence_data if isinstance(sentence_data, list) else []
                files_loaded.append(f"Sentence Dialogue: {sentence_file.name}")
                print(f"📁 [Multi-File Load] Sentence dialogue file loaded successfully: {len(dialogue_data['sentence_dialogues'])} items")
            except Exception as e:
                st.error(f"❌ Sentence dialogue file loading failed: {str(e)}")
        
        # Load behavior timeline file
        if behavior_file is not None:
            try:
                behavior_file.seek(0)
                behavior_content = behavior_file.read().decode('utf-8')
                behavior_data = json.loads(behavior_content)
                dialogue_data["behavior_timeline"] = behavior_data if isinstance(behavior_data, list) else []
                files_loaded.append(f"Behavior Timeline: {behavior_file.name}")
                print(f"📁 [Multi-File Load] Behavior timeline file loaded successfully: {len(dialogue_data['behavior_timeline'])} items")
            except Exception as e:
                st.error(f"❌ Behavior timeline file loading failed: {str(e)}")
        
        if files_loaded:
            # Display loaded file information
            with st.expander("📁 Loaded Files", expanded=True):
                for file_info in files_loaded:
                    st.success(f" {file_info}")
                
                # Display statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Chapter Dialogues", len(dialogue_data["chapter_dialogues"]))
                with col2:
                    st.metric("Sentence Dialogues", len(dialogue_data["sentence_dialogues"]))
                with col3:
                    st.metric("Behavior Events", len(dialogue_data["behavior_timeline"]))
            
            # Load confirmation
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Confirm Load", type="primary", use_container_width=True, key=f"confirm_multi_load_{context}"):
                    load_dialogue_data(dialogue_data, "Multi-File Combination", context)
            
            with col2:
                if st.button("❌ Cancel", use_container_width=True, key=f"cancel_multi_load_{context}"):
                    close_dialogue_loader(context)
        else:
            st.warning("⚠️ Please upload at least one dialogue file")
    
    except Exception as e:
        st.error(f"❌ Multi-file loading failed: {str(e)}")

def load_dialogue_data(dialogue_data, source_name, context):
    """Load dialogue data to session state"""
    try:
        # Save current state
        save_dialogue_to_history("Before loading dialogue file")
        
        # Load data
        if isinstance(dialogue_data, dict):
            st.session_state.dialogue_data = dialogue_data
        else:
            # If single format, try to build complete format
            st.session_state.dialogue_data = {
                "chapter_dialogues": dialogue_data if "dialogue" in str(dialogue_data) else [],
                "sentence_dialogues": dialogue_data if "sentence" in str(dialogue_data) else [],
                "behavior_timeline": dialogue_data if "behavior" in str(dialogue_data) else [],
                "generation_params": {
                    "loaded_from_file": source_name,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            }
        
        # Save operation to history
        save_dialogue_to_history(f"Load dialogue file: {source_name}")
        
        st.success(f"✅ Dialogue data {source_name} loaded successfully!")
        close_dialogue_loader(context)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Load dialogue data failed: {str(e)}")

def close_dialogue_loader(context):
    """Close dialogue loader"""
    if context == "generation_options":
        st.session_state.show_dialogue_loader_gen = False
    elif context == "file_management":
        st.session_state.show_dialogue_loader_file = False

def validate_dialogue_file(data, filename):
    """Validate dialogue file format"""
    try:
        if isinstance(data, dict):
            # Complete dialogue data format validation
            required_keys = ["chapter_dialogues", "sentence_dialogues", "behavior_timeline"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                st.warning(f"⚠️ File missing fields: {', '.join(missing_keys)}, will attempt compatible loading")
            
            return True
            
        elif isinstance(data, list):
            # Single data format validation
            if not data:
                st.warning("⚠️ File is empty list")
                return True
            
            # Check if it's chapter dialogue format
            if all(isinstance(item, dict) and "dialogue" in item for item in data):
                st.info("ℹ️ Detected chapter dialogue format")
                return True
            
            # Check if it's sentence dialogue format
            if all(isinstance(item, dict) and "sentence" in item for item in data):
                st.info("ℹ️ Detected sentence dialogue format")
                return True
            
            # Check if it's behavior timeline format
            if all(isinstance(item, dict) and "behavior" in item for item in data):
                st.info("ℹ️ Detected behavior timeline format")
                return True
            
            st.warning("⚠️ Unrecognized data format, will attempt generic loading")
            return True
        
        else:
            st.error("❌ Unsupported data format, please upload JSON format dialogue file")
            return False
    
    except Exception as e:
        st.error(f"❌ File validation failed: {str(e)}")
        return False

def export_dialogue_files():
    """Export dialogue files"""
    if not st.session_state.get('dialogue_data'):
        st.warning("⚠️ No dialogue data available to export")
        return
    
    st.markdown("##### 📤 Export Dialogue Files")
    
    # Export options
    export_format = st.radio(
        "Select Export Format",
        ["Complete Data (JSON)", "Chapter Dialogues (JSON)", "Sentence Dialogues (JSON)", "Behavior Timeline (JSON)", "Readable Text (TXT)"],
        key="dialogue_export_format"
    )
    
    try:
        dialogue_data = st.session_state.dialogue_data
        
        if export_format == "Complete Data (JSON)":
            export_data = dialogue_data
            filename = f"dialogue_complete_{st.session_state.current_version}.json"
            
        elif export_format == "Chapter Dialogues (JSON)":
            export_data = dialogue_data.get("chapter_dialogues", [])
            filename = f"chapter_dialogues_{st.session_state.current_version}.json"
            
        elif export_format == "Sentence Dialogues (JSON)":
            export_data = dialogue_data.get("sentence_dialogues", [])
            filename = f"sentence_dialogues_{st.session_state.current_version}.json"
            
        elif export_format == "Behavior Timeline (JSON)":
            export_data = dialogue_data.get("behavior_timeline", [])
            filename = f"behavior_timeline_{st.session_state.current_version}.json"
            
        elif export_format == "Readable Text (TXT)":
            export_data = generate_dialogue_text_format(dialogue_data)
            filename = f"dialogue_readable_{st.session_state.current_version}.txt"
        
        # Generate download content
        if export_format.endswith("(JSON)"):
            download_content = json.dumps(export_data, ensure_ascii=False, indent=2)
        else:
            download_content = export_data
        
        # Download button
        st.download_button(
            label=f"📥 Download {filename}",
            data=download_content,
            file_name=filename,
            mime="application/json" if export_format.endswith("(JSON)") else "text/plain",
            use_container_width=True
        )
        
        # Display preview
        with st.expander("📄 Export Preview", expanded=False):
            if export_format.endswith("(JSON)"):
                st.json(export_data)
            else:
                st.text(download_content[:1000] + "..." if len(download_content) > 1000 else download_content)
        
    except Exception as e:
        st.error(f"❌ Export failed: {str(e)}")

def generate_dialogue_text_format(dialogue_data):
    """Generate readable text format dialogue"""
    lines = []
    lines.append(f"Story Dialogue Content - {st.session_state.current_version}")
    lines.append("=" * 50)
    lines.append("")
    
    # Chapter dialogues
    chapter_dialogues = dialogue_data.get("chapter_dialogues", [])
    for i, chapter in enumerate(chapter_dialogues):
        lines.append(f"Chapter {i+1} Dialogue")
        lines.append("-" * 20)
        
        dialogues = chapter.get("dialogue", [])
        if dialogues:
            for j, dialogue in enumerate(dialogues):
                speaker = dialogue.get("speaker", "Unknown")
                content = dialogue.get("dialogue", "")
                action = dialogue.get("action", "")
                
                lines.append(f"{j+1}. {speaker}: {content}")
                if action:
                    lines.append(f"   [{action}]")
                lines.append("")
        else:
            lines.append("   (No dialogue content)")
            lines.append("")
        
        lines.append("")
    
    # Behavior statistics
    behavior_timeline = dialogue_data.get("behavior_timeline", [])
    if behavior_timeline:
        lines.append("Character Behavior Statistics")
        lines.append("-" * 20)
        
        # Group statistics by character
        character_behaviors = {}
        for item in behavior_timeline:
            char = item.get("character", "Unknown")
            behavior = item.get("behavior", "")
            if char not in character_behaviors:
                character_behaviors[char] = []
            if behavior not in character_behaviors[char]:
                character_behaviors[char].append(behavior)
        
        for char, behaviors in character_behaviors.items():
            lines.append(f"{char}: {', '.join(behaviors)}")
        
        lines.append("")
    
    return "\n".join(lines)

# ==================== Story Enhancement Features ====================

def save_enhancement_to_history(action_name, old_enhancement_data=None):
    """Save story enhancement data to history"""
    try:
        if old_enhancement_data is None:
            old_enhancement_data = copy.deepcopy(st.session_state.enhanced_story_data) if st.session_state.enhanced_story_data else {}
        
        # Create history record entry
        history_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action_name,
            "enhancement_data": old_enhancement_data,
            "data_size": len(str(old_enhancement_data)) if old_enhancement_data else 0
        }
        
        # If not at the end of history records, delete subsequent records
        if st.session_state.enhancement_history_index < len(st.session_state.enhancement_history) - 1:
            st.session_state.enhancement_history = st.session_state.enhancement_history[:st.session_state.enhancement_history_index + 1]
        
        # Add new record
        st.session_state.enhancement_history.append(history_entry)
        st.session_state.enhancement_history_index = len(st.session_state.enhancement_history) - 1
        
        # Limit number of history records
        max_history = 20
        if len(st.session_state.enhancement_history) > max_history:
            st.session_state.enhancement_history = st.session_state.enhancement_history[-max_history:]
            st.session_state.enhancement_history_index = len(st.session_state.enhancement_history) - 1
        
        print(f"💾 [Enhancement History] Save operation: {action_name}, current index: {st.session_state.enhancement_history_index}")
        
    except Exception as e:
        print(f"❌ [Enhancement History] Save failed: {str(e)}")

def undo_enhancement_action():
    """Undo story enhancement operation"""
    if st.session_state.enhancement_history_index > 0:
        st.session_state.enhancement_history_index -= 1
        history_entry = st.session_state.enhancement_history[st.session_state.enhancement_history_index]
        st.session_state.enhanced_story_data = copy.deepcopy(history_entry["enhancement_data"])
        st.success(f"↩️ Undid operation: {history_entry['action']}")
        st.rerun()
    else:
        st.warning("⚠️ No actions to undo")

def redo_enhancement_action():
    """Redo story enhancement operation"""
    if st.session_state.enhancement_history_index < len(st.session_state.enhancement_history) - 1:
        st.session_state.enhancement_history_index += 1
        history_entry = st.session_state.enhancement_history[st.session_state.enhancement_history_index]
        st.session_state.enhanced_story_data = copy.deepcopy(history_entry["enhancement_data"])
        st.success(f"↪️ Redid operation: {history_entry['action']}")
        st.rerun()
    else:
        st.warning("⚠️ No actions to redo")

def show_story_enhancement_interface():
    """Display story enhancement interface - as main process step"""
    st.header("✨ Step 5: Story Enhancement")
    
    # Check prerequisites
    if not st.session_state.outline_data:
        st.error("❌ Please complete Step 1 first: Generate Story Outline")
        return
    
    if not st.session_state.characters_data:
        st.error("❌ Please complete Step 2 first: Generate Characters")
        return
    
    if not st.session_state.get('story_data'):
        st.error("❌ Please complete Step 3 first: Generate Story Content")
        return
    
    if not st.session_state.get('dialogue_data'):
        st.error("❌ Please complete Step 4 first: Generate Dialogue Content")
        return
    
    # Check if story enhancement feature is available
    if not story_enhancement_available:
        st.error("❌ Story enhancement feature unavailable, please check backend module import")
        return
    
    # Display dialogue-based story enhancement interface
    show_story_enhancement_mode()

def show_story_enhancement_mode():
    """Story enhancement mode selection"""
    st.markdown("### ✨ Story Enhancement Options")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["✨ Generate Enhanced", "📜 Enhanced Preview", "✏️ Edit Enhancement", "📁 File Management"])
    
    with tab1:
        show_enhancement_generation_options()
    
    with tab2:
        show_enhancement_display()
    
    with tab3:
        show_enhancement_edit_mode()
    
    with tab4:
        show_enhancement_file_management()

def show_enhancement_generation_options():
    """Story enhancement generation options"""
    st.markdown("#### ✨ Generate Enhanced Story")
    
    # Enhancement parameter configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📝 Enhancement Options")
        enable_transitions = st.checkbox("Add Chapter Transitions", value=True, help="Add natural transition sentences between chapters", key="gen_transitions_checkbox")
        enable_polish = st.checkbox("Polish Dialogue", value=True, help="Naturally integrate dialogue into narrative", key="gen_polish_checkbox")
        auto_save = st.checkbox("Auto Save", value=True, help="Automatically save to project directory after generation", key="gen_auto_save_checkbox")
    
    with col2:
        st.markdown("##### 🔧 Generation Parameters")
        use_cache = st.checkbox("Use Cache", value=True, help="Whether to use cache if enhanced data already exists", key="gen_use_cache_checkbox")
        
        # Display current status
        if st.session_state.get('enhanced_story_data'):
            st.info("📄 Enhanced version available")
        else:
            st.info("📄 Enhanced version not generated yet")
    
    st.markdown("---")
    
    # Generation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✨ Generate Enhanced Story", type="primary", use_container_width=True):
            generate_enhanced_story(
                enable_transitions=enable_transitions,
                enable_polish=enable_polish,
                use_cache=use_cache,
                auto_save=auto_save
            )
    
    with col2:
        if st.button("🔄 Regenerate", use_container_width=True):
            regenerate_enhanced_story(
                enable_transitions=enable_transitions,
                enable_polish=enable_polish
            )
    
    with col3:
        if st.button("📁 Load Existing Enhancement", use_container_width=True):
            st.session_state.show_enhancement_loader = True
            st.rerun()
    
    # Display enhancement loader
    if st.session_state.get('show_enhancement_loader', False):
        load_existing_enhancement("generation_options")

def generate_enhanced_story(enable_transitions=True, enable_polish=True, use_cache=True, auto_save=True):
    """Generate enhanced story"""
    try:
        print(f"✨✨✨ [Story Enhancement] ===== Starting to generate enhanced story =====")
        print(f"✨ [Story Enhancement] Add transitions: {enable_transitions}")
        print(f"✨ [Story Enhancement] Polish dialogue: {enable_polish}")
        print(f"✨ [Story Enhancement] Use cache: {use_cache}")
        print(f"✨ [Story Enhancement] Auto save: {auto_save}")
        
        # Save current state to history
        save_enhancement_to_history("Before generating enhanced story")
        
        with st.spinner("✨ Generating enhanced story..."):
            start_time = time.time()
            
            # Prepare temporary file to simulate backend call
            temp_version = f"temp_enhance_{int(time.time())}"
            
            # Create temporary directory and file
            temp_dir = f"data/output/{temp_version}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save necessary data to temporary directory
            save_json(st.session_state.outline_data, temp_version, "test_reorder_outline.json")
            save_json(st.session_state.story_data, temp_version, "story_updated.json")
            save_json(st.session_state.characters_data, temp_version, "characters.json")
            
            # Save dialogue data
            dialogue_data = st.session_state.dialogue_data
            if isinstance(dialogue_data, dict):
                sentence_dialogues = dialogue_data.get("sentence_dialogues", [])
            else:
                sentence_dialogues = dialogue_data
            
            save_json(sentence_dialogues, temp_version, "dialogue_updated.json")
            
            enhanced_content = ""
            polished_content = ""
            
            # Step 1: Add chapter transitions
            if enable_transitions:
                print("✨ [Story Enhancement] Starting to add chapter transitions...")
                enhance_story_with_transitions(task_name=temp_version, input_story_file="story_updated.json")
                
                # Read enhanced result
                enhanced_path = f"data/output/{temp_version}/enhanced_story_updated.md"
                if os.path.exists(enhanced_path):
                    with open(enhanced_path, 'r', encoding='utf-8') as f:
                        enhanced_content = f.read()
                    print("✨ [Story Enhancement] Chapter transition addition completed")
                else:
                    st.warning("⚠️ Chapter transition generation failed, will use original content")
                    enhanced_content = compile_enhanced_story_manually()
            else:
                enhanced_content = compile_enhanced_story_manually()
            
            # Step 2: Polish dialogue
            if enable_polish and enhanced_content:
                print("✨ [Story Enhancement] Starting to polish dialogue...")
                
                # Write enhanced content to temporary file for polishing
                with open(f"data/output/{temp_version}/enhanced_story_updated.md", 'w', encoding='utf-8') as f:
                    f.write(enhanced_content)
                
                polish_dialogues_in_story(task_name=temp_version, input_dialogue_file="dialogue_updated.json")
                
                # Read polishing result
                polished_path = f"data/output/{temp_version}/enhanced_story_dialogue_updated.md"
                if os.path.exists(polished_path):
                    with open(polished_path, 'r', encoding='utf-8') as f:
                        polished_content = f.read()
                    print("✨ [Story Enhancement] Dialogue polishing completed")
                else:
                    st.warning("⚠️ Dialogue polishing failed, will use transition version")
                    polished_content = enhanced_content
            else:
                polished_content = enhanced_content
            
            end_time = time.time()
            
            # Save enhancement result
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
            
            # Clean temporary files
            try:
                import shutil
                shutil.rmtree(temp_dir)
                print(f"✨ [Story Enhancement] Cleaned temporary directory: {temp_dir}")
            except Exception as e:
                print(f"❌ [Story Enhancement] Temporary directory cleanup failed: {e}")
            
            # Log operation
            log_backend_operation(
                "Story Enhancement", 
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
            
            print(f"✨ [Story Enhancement] Enhanced content length: {len(enhanced_content)}")
            print(f"✨ [Story Enhancement] Polished content length: {len(polished_content)}")
            print(f"✨✨✨ [Story Enhancement] ===== Enhancement completed =====")
            
            st.success(f"✅ Story enhancement completed! Generated {len(polished_content or enhanced_content)} characters of enhanced story")
            
            # Display enhancement statistics
            with st.expander("📈 Enhancement Statistics", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Processing Time", f"{end_time - start_time:.1f} seconds")
                with col2:
                    st.metric("Final Content Length", f"{len(polished_content or enhanced_content):,} characters")
                with col3:
                    enhancement_features = []
                    if enable_transitions:
                        enhancement_features.append("Chapter Transitions")
                    if enable_polish:
                        enhancement_features.append("Dialogue Polish")
                    st.metric("Enhancement Features", " + ".join(enhancement_features) if enhancement_features else "None")
            
            # Auto save
            if auto_save:
                save_enhancement_to_project("auto_save")
            
            # Save operation to history
            save_enhancement_to_history("Enhanced story generation completed")
            
    except Exception as e:
        error_msg = f"Story enhancement failed: {str(e)}"
        print(f"❌ [Story Enhancement] {error_msg}")
        st.error(f" {error_msg}")
        
        # Log error
        log_backend_operation(
            "Story Enhancement Failed", 
            {"error": str(e)},
            time.time(), time.time(), None, e
        )

def compile_enhanced_story_manually():
    """Manually compile enhanced story (as fallback option)"""
    try:
        print("📝 [Story Enhancement] Using manual compilation method...")
        
        # Use existing compilation functionality
        dialogue_data = st.session_state.dialogue_data
        if isinstance(dialogue_data, dict):
            sentence_dialogues = dialogue_data.get("sentence_dialogues", [])
        else:
            sentence_dialogues = dialogue_data
        
        compiled_content = compile_full_story_by_sentence(st.session_state.story_data, sentence_dialogues)
        return compiled_content
        
    except Exception as e:
        print(f"❌ [Story Enhancement] Manual compilation failed: {e}")
        return "Manual compilation failed, please check data format"

def regenerate_enhanced_story(enable_transitions=True, enable_polish=True):
    """Regenerate enhanced story"""
    # Clear existing enhancement data and force regeneration
    if st.session_state.get('enhanced_story_data'):
        save_enhancement_to_history("Before Regeneration")
        st.session_state.enhanced_story_data = {}
    
    generate_enhanced_story(
        enable_transitions=enable_transitions,
        enable_polish=enable_polish,
        use_cache=False,
        auto_save=True
    )

def show_enhancement_display():
    """Display enhanced story content"""
    if not st.session_state.get('enhanced_story_data'):
        st.info("📝 No enhanced story available, please generate first")
        return
    
    st.markdown("#### 📜 Enhanced Story Preview")
    
    enhanced_data = st.session_state.enhanced_story_data
    
    # Display enhancement information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        params = enhanced_data.get('generation_params', {})
        st.info(f"📅 Generation Time: {params.get('timestamp', 'Unknown')[:19].replace('T', ' ')}")
    
    with col2:
        processing_time = enhanced_data.get('generation_params', {}).get('processing_time', 0)
        st.info(f"⏱️ Processing Time: {processing_time:.1f} seconds")
    
    with col3:
        final_content = enhanced_data.get('final_content', '')
        st.info(f"📄 Content Length: {len(final_content):,} characters")
    
    # Display enhancement features
    params = enhanced_data.get('generation_params', {})
    enhancement_features = []
    if params.get('enable_transitions'):
        enhancement_features.append("✨ Chapter Transitions")
    if params.get('enable_polish'):
        enhancement_features.append("💬 Dialogue Polish")
    
    if enhancement_features:
        st.success(f"✅ Enabled features: {' + '.join(enhancement_features)}")
    
    st.markdown("---")
    
    # Create display tabs
    tab1, tab2, tab3 = st.tabs(["📖 Final Version", "✨ Chapter Transitions", "💬 Dialogue Polish"])
    
    with tab1:
        st.markdown("##### 📖 Final Enhanced Version")
        final_content = enhanced_data.get('final_content', '')
        if final_content:
            st.text_area("Final Enhanced Content", final_content, height=600, key="final_enhanced_content")
            
            # Download button
            if st.download_button(
                "📥 Download Final Version",
                final_content,
                file_name=f"enhanced_story_final_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            ):
                st.success(" File download started")
        else:
            st.info("📝 No Final Version content")
    
    with tab2:
        st.markdown("##### ✨ Chapter Transitions Version")
        enhanced_content = enhanced_data.get('enhanced_content', '')
        if enhanced_content:
            st.text_area("Chapter Transition Content", enhanced_content, height=600, key="transition_enhanced_content")
            
            if st.download_button(
                "📥 Download Transitions Version",
                enhanced_content,
                file_name=f"enhanced_story_transitions_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            ):
                st.success(" File download started")
        else:
            st.info("📝 No Chapter Transitions version content")
    
    with tab3:
        st.markdown("##### 💬 Dialogue Polish Version")
        polished_content = enhanced_data.get('polished_content', '')
        if polished_content:
            st.text_area("Dialogue Polish Content", polished_content, height=600, key="polished_enhanced_content")
            
            if st.download_button(
                "📥 Download Polish Version",
                polished_content,
                file_name=f"enhanced_story_polished_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            ):
                st.success(" File download started")
        else:
            st.info("📝 No Dialogue Polish version content")

def show_enhancement_edit_mode():
    """Enhanced story edit mode"""
    if not st.session_state.get('enhanced_story_data'):
        st.info("📝 No enhanced story available, please generate first")
        return
    
    st.markdown("#### ✏️ Edit Enhanced Story")
    
    # Create edit tabs
    tab1, tab2, tab3 = st.tabs(["🔄 Regenerate", "✏️ Manual Edit", "📋 History"])
    
    with tab1:
        show_enhancement_regeneration_options()
    
    with tab2:
        show_enhancement_manual_edit()
    
    with tab3:
        show_enhancement_history_panel()

def show_enhancement_regeneration_options():
    """Enhanced story regeneration options"""
    st.markdown("##### 🔄 Regenerate Enhanced Version")
    
    # Regeneration options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("** Regeneration Scope**")
        regen_scope = st.radio(
            "Select Regeneration Scope",
            ["Complete Regeneration", "Chapter Transitions Only", "Dialogue Polish Only"],
            key="enhancement_regen_scope"
        )
    
    with col2:
        st.markdown("**Generation Parameters**")
        enable_transitions = st.checkbox("Add Chapter Transitions", value=True, key="regen_transitions")
        enable_polish = st.checkbox("Polish Dialogue", value=True, key="regen_polish")
    
    st.markdown("---")
    
    # Regeneration buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Complete Regeneration", type="primary", use_container_width=True):
            regenerate_enhanced_story(enable_transitions, enable_polish)
    
    with col2:
        if st.button("✨ Regenerate Transitions Only", use_container_width=True):
            regenerate_enhanced_story(True, False)
    
    with col3:
        if st.button("💎 Polish Dialogue Only", use_container_width=True):
            regenerate_enhanced_story(False, True)

def show_enhancement_manual_edit():
    """Manual edit enhanced content"""
    st.markdown("##### ✏️ Manual Edit Enhanced Content")
    
    enhanced_data = st.session_state.enhanced_story_data
    current_content = enhanced_data.get('final_content', '')
    
    # Edit area
    edited_content = st.text_area(
        "Edit Enhanced Content",
        current_content,
        height=500,
        key="manual_edit_enhancement",
        help="Manually edit enhanced story content here"
    )
    
    # Edit operation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Edit", type="primary", use_container_width=True):
            save_manual_enhancement_edit(edited_content)
    
    with col2:
        if st.button("🔄 Reset Content", use_container_width=True):
            st.session_state['manual_edit_enhancement'] = current_content
            st.rerun()
    
    with col3:
        if st.button("🔍 Preview Changes", use_container_width=True):
            show_enhancement_edit_preview(current_content, edited_content)

def save_manual_enhancement_edit(edited_content):
    """Save manually edited enhanced content"""
    try:
        # Save state before edit to history
        save_enhancement_to_history("Before Manual Edit")
        
        # Update enhanced data
        st.session_state.enhanced_story_data['final_content'] = edited_content
        st.session_state.enhanced_story_data['manual_edited'] = True
        st.session_state.enhanced_story_data['edit_timestamp'] = datetime.datetime.now().isoformat()
        
        # Save state after edit to history
        save_enhancement_to_history("Manual Edit Completed")
        
        st.success("✅ Enhanced content has been saved")
        
        # Log operation
        print(f"✅ [Story Enhancement] Manual edit saved successfully, content length: {len(edited_content)}")
        
    except Exception as e:
        error_msg = f"Save edit failed: {str(e)}"
        print(f"❌ [Story Enhancement] {error_msg}")
        st.error(f" {error_msg}")

def show_enhancement_edit_preview(original_content, edited_content):
    """Show edit preview comparison"""
    st.markdown("##### 📝 Edit Changes Preview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original Content**")
        st.text_area("Original", original_content[:1000] + "..." if len(original_content) > 1000 else original_content, height=300, disabled=True)
        st.info(f"Original length: {len(original_content):,} characters")
    
    with col2:
        st.markdown("**Edited Content**")
        st.text_area("Edited", edited_content[:1000] + "..." if len(edited_content) > 1000 else edited_content, height=300, disabled=True)
        st.info(f"Edited length: {len(edited_content):,} characters")
    
    # Change statistics
    length_change = len(edited_content) - len(original_content)
    if length_change > 0:
        st.success(f"📈 Content increased by {length_change:,} characters")
    elif length_change < 0:
        st.warning(f"📉 Content decreased by {abs(length_change):,} characters")
    else:
        st.info("📏 Content length unchanged")

def show_enhancement_history_panel():
    """Show enhancement history panel"""
    st.markdown("##### 📜 Enhancement History")
    
    if not st.session_state.enhancement_history:
        st.info("📝 No history records")
        return
    
    # History operation controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("↩️ Undo", use_container_width=True):
            undo_enhancement_action()
    
    with col2:
        if st.button("↪️ Redo", use_container_width=True):
            redo_enhancement_action()
    
    with col3:
        current_index = st.session_state.enhancement_history_index
        total_history = len(st.session_state.enhancement_history)
        st.info(f"📍 Position: {current_index + 1}/{total_history}")
    
    st.markdown("---")
    
    # History list
    st.markdown("**📜 History Operation Records**")
    
    for i, entry in enumerate(reversed(st.session_state.enhancement_history)):
        actual_index = len(st.session_state.enhancement_history) - 1 - i
        is_current = actual_index == st.session_state.enhancement_history_index
        
        with st.expander(
            f"{'🔸' if is_current else ''} {entry['action']} - {entry['timestamp'][:19].replace('T', ' ')}",
            expanded=is_current
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Operation**: {entry['action']}")
                st.markdown(f"**Time**: {entry['timestamp'][:19].replace('T', ' ')}")
            
            with col2:
                st.markdown(f"**Data Size**: {entry['data_size']:,} characters")
                if st.button(f"📍 Jump to This Version", key=f"jump_to_{actual_index}"):
                    st.session_state.enhancement_history_index = actual_index
                    if actual_index < len(st.session_state.enhancement_history):
                        history_entry = st.session_state.enhancement_history[actual_index]
                        st.session_state.enhanced_story_data = copy.deepcopy(history_entry["enhancement_data"])
                        st.success(f"✅ Jumped to: {history_entry['action']}")
                        st.rerun()

def show_enhancement_file_management():
    """Enhanced Story File Management"""
    st.markdown("#### 📁 Enhanced Story File Management")
    
    # File operation tabs
    tab1, tab2, tab3 = st.tabs(["💾 Save Files", "📁 Load Files", "📤 Export Files"])
    
    with tab1:
        save_enhancement_to_project("file_management")
    
    with tab2:
        load_existing_enhancement("file_management")
    
    with tab3:
        export_enhancement_files()

def save_enhancement_to_project(context="default"):
    """Save Enhanced Story to Project directory"""
    if not st.session_state.get('enhanced_story_data'):
        st.info("📝 No enhancement data available to save")
        return
    
    st.markdown("##### 💾 Save Enhanced Story to Project")
    
    try:
        # Get current version information
        current_version = get_current_version()
        if not current_version:
            st.error("❌ Unable to determine current project version")
            return
        
        enhanced_data = st.session_state.enhanced_story_data
        
        # Save options
        col1, col2 = st.columns(2)
        
        with col1:
            save_final = st.checkbox("Save Final Version", value=True, key=f"save_final_checkbox_{context}")
            save_transitions = st.checkbox("Save Chapter Transitions", value=False, key=f"save_transitions_checkbox_{context}")
        
        with col2:
            save_polished = st.checkbox("Save Dialogue Polish", value=False, key=f"save_polished_checkbox_{context}")
            save_metadata = st.checkbox("Save Metadata", value=True, key=f"save_metadata_checkbox_{context}")
        
        if st.button("💾 Execute Save", type="primary", use_container_width=True, key=f"save_execute_btn_{context}"):
            saved_files = []
            
            # Save Final Version
            if save_final and enhanced_data.get('final_content'):
                final_path = f"data/output/{current_version}/enhanced_story_final.md"
                with open(final_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_data['final_content'])
                saved_files.append("enhanced_story_final.md")
            
            # Save Chapter Transitions
            if save_transitions and enhanced_data.get('enhanced_content'):
                transitions_path = f"data/output/{current_version}/enhanced_story_transitions.md"
                with open(transitions_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_data['enhanced_content'])
                saved_files.append("enhanced_story_transitions.md")
            
            # Save Dialogue Polish version
            if save_polished and enhanced_data.get('polished_content'):
                polished_path = f"data/output/{current_version}/enhanced_story_polished.md"
                with open(polished_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_data['polished_content'])
                saved_files.append("enhanced_story_polished.md")
            
            # Save metadata
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
            
            st.success(f"✅ Saved {len(saved_files)} files to data/output/{current_version}/")
            for file in saved_files:
                st.info(f"📄 {file}")
            
            print(f"✅ [Story Enhancement] Save files to project: {saved_files}")
    
    except Exception as e:
        error_msg = f"Save files failed: {str(e)}"
        print(f"❌ [Story Enhancement] {error_msg}")
        st.error(f" {error_msg}")

def load_existing_enhancement(context="default"):
    """Load existing enhancement files"""
    st.markdown("##### 📁 Load Existing Enhancement")
    
    # Add session state to prevent duplicate uploader after successful upload
    upload_flag_key = f'enhancement_file_uploaded_{context}'
    if st.session_state.get(upload_flag_key, False):
        st.success("✅ File uploaded successfully! The page will refresh automatically.")
        # Reset flag after display
        st.session_state[upload_flag_key] = False
        return
    
    uploaded_file = st.file_uploader(
        "Select Enhancement File",
        type=['md', 'json'],
        help="Supports .md files (story content) or .json files (with metadata)",
        key=f"enhancement_file_uploader_{context}"
    )
    
    if uploaded_file is not None:
        try:
            # Read file content
            uploaded_file.seek(0)
            
            if uploaded_file.name.endswith('.md'):
                # Markdown file
                content = uploaded_file.read().decode('utf-8')
                
                # Save state before loading
                save_enhancement_to_history("Before Loading Files")
                
                # Create enhancement data
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
                
                st.success(f"✅ Loaded enhanced file: {uploaded_file.name}")
                st.info(f"📄 Content length: {len(content):,} characters")
                
            elif uploaded_file.name.endswith('.json'):
                # JSON metadata file
                import json
                data = json.loads(uploaded_file.read().decode('utf-8'))
                
                if 'final_content' in data or 'enhanced_content' in data:
                    save_enhancement_to_history("Before loading JSON file")
                    st.session_state.enhanced_story_data = data
                    st.success(f"✅ Loaded enhanced data: {uploaded_file.name}")
                else:
                    st.error("❌ JSON file format incorrect, missing required content fields")
            
            # Save state after loading
            save_enhancement_to_history("File loading completed")
            
            print(f"📁 [Story Enhancement] Load file success: {uploaded_file.name}")
            
            # Set flag to prevent duplicate uploader
            st.session_state[upload_flag_key] = True
            st.rerun()
            
        except Exception as e:
            error_msg = f"Load file failed: {str(e)}"
            print(f"❌ [Story Enhancement] {error_msg}")
            st.error(f" {error_msg}")

def export_enhancement_files():
    """Export enhanced files"""
    if not st.session_state.get('enhanced_story_data'):
        st.info("📝 No enhanced data available for export")
        return
    
    st.markdown("##### 📤 Export Enhanced Files")
    
    enhanced_data = st.session_state.enhanced_story_data
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📄 Content Export**")
        
        # Final Version download
        if enhanced_data.get('final_content'):
            st.download_button(
                "📥 Download Final Version (.md)",
                enhanced_data['final_content'],
                file_name=f"enhanced_story_final_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        # Chapter Transitions version download
        if enhanced_data.get('enhanced_content'):
            st.download_button(
                "📥 Download Transitions Version (.md)",
                enhanced_data['enhanced_content'],
                file_name=f"enhanced_story_transitions_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    with col2:
        st.markdown("**📊 Data Export**")
        
        # Complete data export
        import json
        complete_data = json.dumps(enhanced_data, ensure_ascii=False, indent=2)
        st.download_button(
            "📥 Download Complete Data (.json)",
            complete_data,
            file_name=f"enhanced_story_complete_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Metadata export
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
            "📥 Download Metadata (.json)",
            metadata_json,
            file_name=f"enhanced_story_metadata_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# ================================
#  Performance Analysis Interface
# ================================

def show_performance_analysis_interface():
    """Display performance analysis interface"""
    st.header(" Performance Analysis Center")
    st.markdown("---")
    
    # Top operation bar
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("###  Computational Complexity Analysis & Performance Monitoring")
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("← Return to Main", use_container_width=True):
            st.session_state.show_performance_analysis = False
            st.rerun()
    
    # Tab interface
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Single Analysis", "🔄 Comparative Analysis", "⚡ Real-time Monitoring", "📊 Historical Reports"])
    
    with tab1:
        show_single_performance_analysis()
    
    with tab2:
        show_comparative_performance_analysis()
    
    with tab3:
        show_real_time_performance_monitor()
        
    with tab4:
        show_performance_history()


def show_single_performance_analysis():
    """Display single performance analysis"""
    st.markdown("#### 🔍 Single Execution Performance Analysis")
    
    # Load performance reports
    performance_reports = load_available_performance_reports()
    
    if not performance_reports:
        st.warning("📝 No performance analysis reports available. Please run the story generation process first to collect performance data.")
        
        # Provide quick start example options
        with st.expander("🚀 Quick Start"):
            st.markdown("""
            **How to generate performance data:**
            1. Return to main interface, create or load a story outline
            2. Complete steps such as character generation, story expansion, etc.
            3. After running the complete process, the system will automatically generate performance analysis reports
            4. Return to this interface to view detailed performance analysis
            """)
        return
    
    # Select report to analyze
    report_options = {f"{report['metadata']['task_name']} ({report['metadata']['analysis_timestamp'][:19]})": report 
                     for report in performance_reports}
    selected_report_name = st.selectbox(
        "📂 Select Report to Analyze",
        options=list(report_options.keys()),
        help="Select a performance report for detailed analysis"
    )
    
    if selected_report_name:
        selected_report = report_options[selected_report_name]
        
        # Display basic information
        display_performance_basic_info(selected_report)
        
        st.markdown("---")
        
        # Analysis details
        col1, col2 = st.columns(2)
        
        with col1:
            display_stage_performance_breakdown(selected_report)
            
        with col2:
            display_complexity_analysis_results(selected_report)
        
        st.markdown("---")
        
        # Text features analysis
        display_text_features_analysis(selected_report)
        
        st.markdown("---")
        
        # Memory and API cost detailed analysis
        col1, col2 = st.columns(2)
        
        with col1:
            display_memory_analysis(selected_report)
            
        with col2:
            display_api_cost_analysis(selected_report)


def show_comparative_performance_analysis():
    """Display comparative performance analysis"""
    st.markdown("#### 🔄 Multi-Execution Comparative Analysis")
    
    performance_reports = load_available_performance_reports()
    
    if len(performance_reports) < 2:
        st.warning("📝 At least 2 performance reports are required for Comparative Analysis.")
        return
    
    # Select reports to compare
    report_options = {f"{report['metadata']['task_name']} ({report['metadata']['analysis_timestamp'][:19]})": report 
                     for report in performance_reports}
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_reports_1 = st.multiselect(
            "📂 Select reports to compare (Baseline Group)",
            options=list(report_options.keys()),
            max_selections=5,
            help="Select performance reports as baseline"
        )
    
    with col2:
        selected_reports_2 = st.multiselect(
            "📂 Select reports to compare (Comparison Group)",
            options=list(report_options.keys()),
            max_selections=5,
            help="Select performance reports to compare against baseline"
        )
    
    if selected_reports_1 and selected_reports_2:
        reports_1 = [report_options[name] for name in selected_reports_1]
        reports_2 = [report_options[name] for name in selected_reports_2]
        
        # Perform Comparative Analysis
        comparison_result = perform_comparative_analysis(reports_1, reports_2)
        display_comparison_results(comparison_result)


def show_real_time_performance_monitor():
    """Show real-time performance monitoring"""
    st.markdown("#### ⚡ Real-time Performance Monitoring")
    
    st.info(" This feature will provide real-time performance monitoring while running the story generation process")
    
    # If there is a running task, display Real-time Monitoring
    if st.session_state.get('running_task'):
        display_real_time_monitor()
    else:
        st.markdown("""
        **Real-time Monitoring Features:**
        - 🕐 Real-time display of execution time for each stage
        - 📈 Text generation speed curve
        - 💾 Real-time computation of complexity metrics
        - 🚨 Performance anomaly alerts
        
        **Usage:**
        1. Start story generation process from main interface
        2. Switch to this tab during generation
        3. View real-time performance data
        """)


def show_performance_history():
    """Show performance history"""
    st.markdown("####  Historical Performance Reports")
    
    performance_reports = load_available_performance_reports()
    
    if not performance_reports:
        st.info("📝 No historical performance reports")
        return
    
    # Sort by time
    sorted_reports = sorted(performance_reports, 
                           key=lambda x: x['metadata']['analysis_timestamp'], 
                           reverse=True)
    
    # Display Historical Reports list
    for i, report in enumerate(sorted_reports[:20]):  # Only display the last 20
        with st.expander(f" {report['metadata']['task_name']} - {report['metadata']['analysis_timestamp'][:19]}"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Time", f"{report['metadata']['total_execution_time']:.2f} seconds")
            
            with col2:
                text_features = report.get('text_features', {})
                st.metric("Generated Words", f"{text_features.get('total_word_count', 0)} words")
            
            with col3:
                complexity = report.get('complexity_analysis', {})
                efficiency = complexity.get('efficiency_metrics', {})
                st.metric("Generation Efficiency", f"{efficiency.get('words_per_second', 0):.2f} words/second")
            
            with col4:
                summary = report.get('performance_summary', {})
                st.metric("Efficiency Rating", summary.get('efficiency_rating', 'Unknown'))
            
            # Detailed button
            if st.button(f"View Details #{i+1}", key=f"detail_{i}"):
                st.session_state.selected_detail_report = report
                st.rerun()


def load_available_performance_reports():
    """Load available performance analysis reports"""
    import os
    import json
    
    reports = []
    output_dir = "data/output"
    
    if not os.path.exists(output_dir):
        return reports
    
    try:
        # Traverse all subdirectories to find performance reports
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.startswith("performance_analysis_") and file.endswith(".json"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            report = json.load(f)
                        reports.append(report)
                    except Exception as e:
                        st.warning(f"Cannot load report {file}: {e}")
    except Exception as e:
        st.error(f"Error loading report: {e}")
    
    return reports


def display_performance_basic_info(report):
    """Display performance report basic information"""
    metadata = report.get('metadata', {})
    summary = report.get('performance_summary', {})
    
    # First row: time, words, efficiency, rating
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Execution Time",
            summary.get('total_time_formatted', f"{metadata.get('total_execution_time', 0):.2f} seconds"),
            help="Total execution time of the complete story generation process"
        )
    
    with col2:
        text_features = report.get('text_features', {})
        st.metric(
            "Generated Words",
            f"{text_features.get('total_word_count', 0)} words",
            help="Total number of Chinese characters generated"
        )
    
    with col3:
        complexity = report.get('complexity_analysis', {})
        efficiency = complexity.get('efficiency_metrics', {})
        st.metric(
            "Generation Efficiency",
            f"{efficiency.get('words_per_second', 0):.2f} words/second",
            help="Average number of words generated per second"
        )
    
    with col4:
        st.metric(
            "Efficiency Rating",
            summary.get('efficiency_rating', 'Unknown'),
            help="Overall rating based on generation efficiency"
        )
    
    # Second row: memory, API cost, token, character
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        peak_memory = metadata.get('peak_memory_usage_mb', 0)
        st.metric(
            "Peak Memory",
            f"{peak_memory:.2f} MB",
            help="Peak memory usage during generation"
        )
    
    with col2:
        total_cost = metadata.get('total_api_cost', 0)
        st.metric(
            "API Cost",
            f"${total_cost:.4f}",
            help="Total API call cost (USD)"
        )
    
    with col3:
        total_tokens = metadata.get('total_tokens', 0)
        st.metric(
            "Token Consumption",
            f"{total_tokens:,}",
            help="Total token consumption"
        )
    
    with col4:
        # Display character-related information
        character_features = text_features.get('character_features', {})
        character_count = character_features.get('character_count', 0)
        memory_per_char = peak_memory / character_count if character_count > 0 else 0
        st.metric(
            "Memory/Character",
            f"{memory_per_char:.2f} MB",
            help="Average memory per character"
        )


def display_stage_performance_breakdown(report):
    """Display stage performance breakdown"""
    st.markdown("##### ⏱️ Stage Performance Breakdown")
    
    stage_performance = report.get('stage_performance', {})
    stage_times = stage_performance.get('stage_times', {})
    stage_percentages = stage_performance.get('stage_breakdown_percentage', {})
    
    if not stage_times:
        st.info("No stage performance data")
        return
    
    # Create stage performance table
    import pandas as pd
    
    stage_data = []
    stage_name_mapping = {
        'outline_generation': ' Outline Generation',
        'chapter_reorder': '🔄 Chapter Reorder',
        'character_generation': '👥 Character Generation', 
        'story_expansion': '📝 Story Expansion',
        'dialogue_generation': '💬 Dialogue Generation',
        'story_enhancement': '✨ Story Enhancement'
    }
    
    for stage, duration in stage_times.items():
        stage_data.append({
            'Stage': stage_name_mapping.get(stage, stage),
            'Duration(seconds)': f"{duration:.3f}",
            'Percentage(%)': f"{stage_percentages.get(stage, 0):.1f}%"
        })
    
    df = pd.DataFrame(stage_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Slowest stage hint
    if stage_times:
        slowest_stage = max(stage_times.items(), key=lambda x: x[1])
        slowest_name = stage_name_mapping.get(slowest_stage[0], slowest_stage[0])
        st.info(f"🐌 Slowest stage: {slowest_name} ({slowest_stage[1]:.3f} seconds)")


def display_complexity_analysis_results(report):
    """Display complexity analysis results"""
    st.markdown("##### 🧮 Complexity Analysis")
    
    complexity = report.get('complexity_analysis', {})
    complexity_indicators = complexity.get('complexity_indicators', {})
    
    if not complexity_indicators:
        st.info("No complexity analysis data")
        return
    
    # Display complexity indicators
    with st.container():
        st.markdown("**Time Complexity Indicators:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'linear_indicator' in complexity_indicators:
                st.metric(
                    "Linear Indicator T(n)/n", 
                    f"{complexity_indicators['linear_indicator']:.6f}",
                    help="If close to constant, it means the time complexity is close to linear"
                )
        
        with col2:
            if 'sqrt_n_indicator' in complexity_indicators:
                st.metric(
                    "Square Root Indicator T(n)/√n", 
                    f"{complexity_indicators['sqrt_n_indicator']:.6f}",
                    help="Used to analyze whether it is square root complexity"
                )
        
        # Complexity estimation
        summary = report.get('performance_summary', {})
        estimated_class = summary.get('estimated_complexity_class', 'More data analysis needed')
        
        st.markdown(f"**📈 Estimated Complexity Class:** {estimated_class}")


def display_text_features_analysis(report):
    """Display text feature analysis"""
    st.markdown("#####  Text Feature Analysis")
    
    text_features = report.get('text_features', {})
    
    if not text_features:
        st.info("No text feature data")
        return
    
    # Basic statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Chapter Count", text_features.get('chapter_count', 0))
    
    with col2:
        st.metric("Total Sentence Count", text_features.get('total_sentence_count', 0))
    
    with col3:
        st.metric("Average Chapter Length", f"{text_features.get('avg_chapter_length', 0):.0f} words")
    
    with col4:
        st.metric("Average Sentence Length", f"{text_features.get('avg_sentence_length', 0):.1f} words")
    
    # Dialogue features (if any)
    dialogue_features = text_features.get('dialogue_features', {})
    if dialogue_features and dialogue_features.get('total_dialogue_count', 0) > 0:
        st.markdown("**💬 Dialogue Features:**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Dialogue Count", dialogue_features.get('total_dialogue_count', 0))
        with col2:
            st.metric("Character Count", dialogue_features.get('unique_speakers', 0))
        with col3:
            st.metric("Average Dialogue Length", f"{dialogue_features.get('avg_dialogue_length', 0):.1f} words")


def display_memory_analysis(report):
    """Display memory analysis"""
    st.markdown("#####  Memory Usage Analysis")
    
    memory_data = report.get('memory_complexity_data', {})
    
    if not memory_data or memory_data.get('peak_memory_usage_mb', 0) == 0:
        st.info("No memory monitoring data")
        return
    
    # Basic memory indicators
    peak_memory = memory_data.get('peak_memory_usage_mb', 0)
    memory_per_character = memory_data.get('memory_per_character', 0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Peak Memory", f"{peak_memory:.2f} MB")
    
    with col2:
        st.metric("Memory/Character", f"{memory_per_character:.2f} MB")
    
    # Each stage memory growth
    stage_memory = memory_data.get('stage_memory_usage', {})
    if stage_memory:
        st.markdown("**Each stage memory growth:**")
        
        # Create memory growth table
        import pandas as pd
        
        memory_increases = []
        stage_name_mapping = {
            'character_generation_increase': '👥 Character Generation',
            'story_expansion_increase': '📝 Story Expansion',
            'dialogue_generation_increase': '💬 Dialogue Generation',
            'story_enhancement_increase': '✨ Story Enhancement'
        }
        
        for stage, increase in stage_memory.items():
            if stage.endswith('_increase') and increase > 0:
                stage_name = stage_name_mapping.get(stage, stage.replace('_increase', ''))
                memory_increases.append({
                    'Stage': stage_name,
                    'Memory Growth(MB)': f"{increase:.2f}",
                    'Growth Percentage': f"{(increase/peak_memory*100):.1f}%" if peak_memory > 0 else "0%"
                })
        
        if memory_increases:
            df = pd.DataFrame(memory_increases)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Memory timeline chart (if any data)
        memory_timeline = memory_data.get('memory_timeline', [])
        if memory_timeline and len(memory_timeline) > 5:
            try:
                import matplotlib.pyplot as plt
                import numpy as np
                
                # Prepare data
                timestamps = [point['timestamp'] for point in memory_timeline]
                memory_values = [point['memory_mb'] for point in memory_timeline]
                
                # Create chart
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(timestamps, memory_values, linewidth=2, color='#1f77b4')
                ax.set_xlabel('Time (seconds)')
                ax.set_ylabel('Memory Usage (MB)')
                ax.set_title('Memory Usage Timeline')
                ax.grid(True, alpha=0.3)
                
                st.pyplot(fig)
                plt.close(fig)
            except Exception as e:
                st.warning(f"Memory timeline chart generation failed: {e}")
    
    # Character complexity vs memory
    story_features = memory_data.get('story_features', {})
    if story_features:
        st.markdown("**Character Complexity Analysis:**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Character Count", story_features.get('character_count', 0))
        with col2:
            complexity_score = story_features.get('character_complexity_score', 0)
            st.metric("Complexity Score", f"{complexity_score:.1f}")


def display_api_cost_analysis(report):
    """Display API cost analysis"""
    st.markdown("##### 💰 API Cost Analysis")
    
    api_breakdown = report.get('api_cost_breakdown', {})
    
    if not api_breakdown or api_breakdown.get('total_cost', 0) == 0:
        st.info("No API cost data")
        return
    
    # Overall cost indicators
    total_cost = api_breakdown.get('total_cost', 0)
    total_tokens = api_breakdown.get('total_tokens', 0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Cost", f"${total_cost:.6f}")
    
    with col2:
        st.metric("Total Tokens", f"{total_tokens:,}")
    
    # Each stage cost decomposition
    cost_per_stage = api_breakdown.get('cost_per_stage', {})
    if cost_per_stage:
        st.markdown("**Each stage cost decomposition:**")
        
        import pandas as pd
        
        cost_data = []
        stage_name_mapping = {
            'outline_generation': ' Outline Generation',
            'character_generation': '👥 Character Generation',
            'story_expansion': '📝 Story Expansion', 
            'dialogue_generation': '💬 Dialogue Generation',
            'story_enhancement': '✨ Story Enhancement'
        }
        
        for stage, tokens_info in cost_per_stage.items():
            stage_name = stage_name_mapping.get(stage, stage)
            cost = tokens_info.get('total_cost', 0)
            tokens = tokens_info.get('total_tokens', 0)
            api_calls = tokens_info.get('api_calls', 0)
            
            cost_data.append({
                'Stage': stage_name,
                'Cost($)': f"{cost:.6f}",
                'Tokens': f"{tokens:,}",
                'API Calls': api_calls,
                'Cost Percentage': f"{(cost/total_cost*100):.1f}%" if total_cost > 0 else "0%"
            })
        
        df = pd.DataFrame(cost_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Cost distribution pie chart
        if len(cost_data) > 1:
            try:
                import matplotlib.pyplot as plt
                
                # Prepare data
                stages = [item['Stage'] for item in cost_data]
                costs = [float(item['Cost($)']) for item in cost_data]
                
                # Create pie chart
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.pie(costs, labels=stages, autopct='%1.1f%%', startangle=90)
                ax.set_title('Each stage API cost distribution')
                
                st.pyplot(fig)
                plt.close(fig)
            except Exception as e:
                st.warning(f"Cost distribution chart generation failed: {e}")
    
    # Efficiency indicators
    if total_tokens > 0 and total_cost > 0:
        st.markdown("**Cost efficiency indicators:**")
        
        text_features = report.get('text_features', {})
        total_words = text_features.get('total_word_count', 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0
            st.metric("Cost/Token", f"${cost_per_token:.6f}")
        
        with col2:
            cost_per_word = total_cost / total_words if total_words > 0 else 0
            st.metric("Cost/Word", f"${cost_per_word:.6f}")


def perform_comparative_analysis(reports_1, reports_2):
    """Perform Comparative Analysis"""
    # Here implement Comparative Analysis logic
    # Extract key metrics for comparison
    
    def extract_metrics(reports):
        total_times = [r['metadata']['total_execution_time'] for r in reports]
        word_counts = [r.get('text_features', {}).get('total_word_count', 0) for r in reports]
        efficiencies = [r.get('complexity_analysis', {}).get('efficiency_metrics', {}).get('words_per_second', 0) for r in reports]
        
        return {
            'avg_time': sum(total_times) / len(total_times),
            'avg_words': sum(word_counts) / len(word_counts), 
            'avg_efficiency': sum(efficiencies) / len(efficiencies),
            'count': len(reports)
        }
    
    metrics_1 = extract_metrics(reports_1)
    metrics_2 = extract_metrics(reports_2)
    
    return {
        'group_1': metrics_1,
        'group_2': metrics_2,
        'comparison': {
            'time_diff': metrics_2['avg_time'] - metrics_1['avg_time'],
            'efficiency_diff': metrics_2['avg_efficiency'] - metrics_1['avg_efficiency'],
            'time_improvement': ((metrics_1['avg_time'] - metrics_2['avg_time']) / metrics_1['avg_time'] * 100) if metrics_1['avg_time'] > 0 else 0
        }
    }


def display_comparison_results(comparison):
    """Display comparison results"""
    st.markdown("####  Comparative Analysis results")
    
    col1, col2, col3 = st.columns(3)
    
    group_1 = comparison['group_1']
    group_2 = comparison['group_2']
    comp = comparison['comparison']
    
    with col1:
        st.metric(
            f"Baseline group average time (n={group_1['count']})",
            f"{group_1['avg_time']:.2f} seconds"
        )
        st.metric(
            f"Comparison group average time (n={group_2['count']})",
            f"{group_2['avg_time']:.2f} seconds",
            delta=f"{comp['time_diff']:+.2f} seconds"
        )
    
    with col2:
        st.metric(
            "Baseline group average efficiency",
            f"{group_1['avg_efficiency']:.2f} words/second"
        )
        st.metric(
            "Comparison group average efficiency", 
            f"{group_2['avg_efficiency']:.2f} words/second",
            delta=f"{comp['efficiency_diff']:+.2f} words/second"
        )
    
    with col3:
        st.metric(
            "Time improvement",
            f"{comp['time_improvement']:+.1f}%",
            help="Negative value means time increase, positive value means time decrease"
        )


def display_real_time_monitor():
    """Display Real-time Monitoring interface"""
    st.markdown("#### ⚡ Real-time Performance Monitoring")
    
    # Create placeholder for real-time update
    time_placeholder = st.empty()
    progress_placeholder = st.empty()
    stage_placeholder = st.empty()
    
    # Here can implement the real-time Monitoring logic
    # Now show simulated data
    
    with time_placeholder.container():
        st.metric("Current execution time", "127.5 seconds")
    
    with progress_placeholder.container():
        st.progress(0.75)
        st.text("Current stage: Dialogue Generation (75%)")
    
    with stage_placeholder.container():
        st.json({
            "Outline Generation": " 15.3 seconds",
            "Character Generation": " 23.1 seconds", 
            "Story Expansion": " 89.1 seconds",
            "Dialogue Generation": "🔄 In progress...",
            "Story Enhancement": " Waiting"
        })


if __name__ == "__main__":
    main()
