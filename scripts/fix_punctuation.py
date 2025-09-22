 #!/usr/bin/env python3
"""
Fix Chinese punctuation in English text files
Replace Chinese punctuation marks with English equivalents
"""

import os
import re
from pathlib import Path

def fix_punctuation_in_text(content):
    """Replace Chinese punctuation with English punctuation"""
    # Dictionary of Chinese -> English punctuation replacements
    punctuation_map = {
        '，': ',',     # Chinese comma -> English comma
        '。': '.',     # Chinese period -> English period
        '！': '!',     # Chinese exclamation -> English exclamation
        '？': '?',     # Chinese question -> English question
        '；': ';',     # Chinese semicolon -> English semicolon
        '：': ':',     # Chinese colon -> English colon
        '"': '"',     # Chinese left quote -> English quote
        '"': '"',     # Chinese right quote -> English quote
        ''': "'",     # Chinese left single quote -> English single quote
        ''': "'",     # Chinese right single quote -> English single quote
        '（': '(',     # Chinese left parenthesis -> English left parenthesis
        '）': ')',     # Chinese right parenthesis -> English right parenthesis
    }
    
    # Apply replacements
    fixed_content = content
    for chinese_punct, english_punct in punctuation_map.items():
        fixed_content = fixed_content.replace(chinese_punct, english_punct)
    
    return fixed_content

def fix_punctuation_in_file(file_path):
    """Fix punctuation in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count Chinese punctuation before fixing
        chinese_punct_count = sum(content.count(punct) for punct in ['，', '。', '！', '？', '；', '：', '"', '"', ''', ''', '（', '）'])
        
        if chinese_punct_count == 0:
            print(f"✅ {file_path}: No Chinese punctuation found")
            return 0
        
        fixed_content = fix_punctuation_in_text(content)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"🔧 {file_path}: Fixed {chinese_punct_count} Chinese punctuation marks")
        return chinese_punct_count
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return 0

def main():
    """Main function to fix punctuation in the experiment directory"""
    experiment_dir = Path("data/output/theuglyduckling_abo_nonlinear_T0.7_s2")
    
    if not experiment_dir.exists():
        print(f"❌ Experiment directory not found: {experiment_dir}")
        return
    
    print(f"🔍 Scanning directory: {experiment_dir}")
    
    # File extensions to process
    target_extensions = ['.md', '.json', '.txt']
    total_fixes = 0
    files_processed = 0
    
    for file_path in experiment_dir.rglob('*'):
        if file_path.is_file() and file_path.suffix in target_extensions:
            fixes = fix_punctuation_in_file(file_path)
            total_fixes += fixes
            files_processed += 1
    
    print(f"\n📊 Summary:")
    print(f"   Files processed: {files_processed}")
    print(f"   Total punctuation fixes: {total_fixes}")
    print(f"   Status: {'✅ Complete' if total_fixes > 0 else '✅ No fixes needed'}")

if __name__ == "__main__":
    main()
