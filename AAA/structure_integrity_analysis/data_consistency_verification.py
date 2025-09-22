#!/usr/bin/env python3
"""
Data Consistency Verification

Verify that all analysis files correctly reflect the updated dataset
with 57 total samples (54 main + 3 baseline).
"""

import json
import re
from pathlib import Path

def verify_data_consistency():
    """Verify all files reflect the correct sample counts and baseline data."""
    
    print("🔍 Verifying Data Consistency Across All Files...")
    print("="*60)
    
    # Expected values based on new data
    expected = {
        'total_samples': 57,
        'main_samples': 54, 
        'baseline_samples': 3,
        'baseline_chapter_mean': 14.0,
        'baseline_chapter_std': 8.717797887081348
    }
    
    issues_found = []
    files_checked = []
    
    # Check JSON file
    json_path = Path("structure_analysis_results/comprehensive_structure_report.json")
    if json_path.exists():
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        print("📊 Checking JSON Report...")
        
        # Check sample counts
        actual_total = data['analysis_metadata']['total_stories_analyzed']
        actual_main = data['analysis_metadata']['main_samples_analyzed'] 
        actual_baseline = data['analysis_metadata']['baseline_samples_analyzed']
        
        if actual_total == expected['total_samples']:
            print(f"  ✅ Total samples: {actual_total}")
        else:
            issues_found.append(f"JSON total samples: expected {expected['total_samples']}, got {actual_total}")
            
        if actual_main == expected['main_samples']:
            print(f"  ✅ Main samples: {actual_main}")
        else:
            issues_found.append(f"JSON main samples: expected {expected['main_samples']}, got {actual_main}")
            
        if actual_baseline == expected['baseline_samples']:
            print(f"  ✅ Baseline samples: {actual_baseline}")
        else:
            issues_found.append(f"JSON baseline samples: expected {expected['baseline_samples']}, got {actual_baseline}")
        
        # Check baseline statistics
        if 'baseline_comparison' in data:
            baseline_data = data['baseline_comparison']
            actual_baseline_mean = baseline_data['chapter_count']['baseline_mean']
            actual_baseline_std = baseline_data['chapter_count']['baseline_std']
            
            if abs(actual_baseline_mean - expected['baseline_chapter_mean']) < 0.1:
                print(f"  ✅ Baseline chapter mean: {actual_baseline_mean}")
            else:
                issues_found.append(f"Baseline chapter mean: expected {expected['baseline_chapter_mean']}, got {actual_baseline_mean}")
                
            if abs(actual_baseline_std - expected['baseline_chapter_std']) < 0.1:
                print(f"  ✅ Baseline chapter std: {actual_baseline_std:.3f}")
            else:
                issues_found.append(f"Baseline chapter std: expected {expected['baseline_chapter_std']:.3f}, got {actual_baseline_std:.3f}")
        
        files_checked.append("comprehensive_structure_report.json")
    
    # Check Markdown report
    md_path = Path("structure_analysis_results/structure_analysis_report.md")
    if md_path.exists():
        print("\n📝 Checking Markdown Report...")
        
        with open(md_path, 'r') as f:
            content = f.read()
        
        # Check for correct total sample count
        if f"{expected['total_samples']} generated stories" in content:
            print(f"  ✅ Total samples mentioned correctly: {expected['total_samples']}")
        else:
            # Look for any mention of total samples
            total_matches = re.findall(r'(\d+) generated stories', content)
            if total_matches:
                issues_found.append(f"MD total samples: expected {expected['total_samples']}, found {total_matches}")
            else:
                print("  ⚠️ No total sample count found in MD report")
        
        files_checked.append("structure_analysis_report.md")
    
    # Check summary documents
    summary_files = [
        "hybrid_weight_implementation_summary.md",
        "honest_weight_analysis_conclusion.md", 
        "README.md"
    ]
    
    for file_name in summary_files:
        file_path = Path(file_name)
        if file_path.exists():
            print(f"\n📋 Checking {file_name}...")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for outdated sample references
            outdated_patterns = [
                r'总样本.*54[^个主样本]',  # 总样本: 54 (but not 54个主样本)
                r'56.*故事',
                r'2.*个baseline',
                r'两个基线'
            ]
            
            for pattern in outdated_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    issues_found.append(f"{file_name}: Found potentially outdated reference: {matches}")
            
            files_checked.append(file_name)
    
    # Check visualization timestamps
    print(f"\n🖼️ Checking Visualization Timestamps...")
    png_files = list(Path("structure_analysis_results").glob("*.png"))
    
    if png_files:
        # Get creation times
        timestamps = []
        for png_file in png_files:
            timestamp = png_file.stat().st_mtime
            timestamps.append(timestamp)
        
        # Check if all visualizations were generated at similar times (within 1 minute)
        if len(set(int(t/60) for t in timestamps)) <= 1:  # All within same minute
            print(f"  ✅ All {len(png_files)} visualizations generated together")
            print(f"  📅 Generated at: {max(timestamps)}")
        else:
            issues_found.append("Visualizations have inconsistent timestamps - may need regeneration")
    
    # Summary
    print(f"\n📋 VERIFICATION SUMMARY")
    print("="*60)
    print(f"Files checked: {len(files_checked)}")
    print(f"Files: {', '.join(files_checked)}")
    
    if issues_found:
        print(f"\n❌ Issues found ({len(issues_found)}):")
        for i, issue in enumerate(issues_found, 1):
            print(f"  {i}. {issue}")
        return False
    else:
        print(f"\n✅ All files are consistent with new data!")
        print(f"✅ Total: {expected['total_samples']} samples ({expected['main_samples']} main + {expected['baseline_samples']} baseline)")
        print(f"✅ Baseline statistics updated: {expected['baseline_chapter_mean']:.1f} ± {expected['baseline_chapter_std']:.1f} chapters")
        return True

def main():
    """Main verification function."""
    try:
        is_consistent = verify_data_consistency()
        
        if is_consistent:
            print(f"\n🎉 DATA CONSISTENCY VERIFICATION PASSED!")
            print("All analysis files correctly reflect the updated dataset.")
        else:
            print(f"\n⚠️ DATA CONSISTENCY ISSUES DETECTED!")
            print("Some files may need manual updates.")
        
        return is_consistent
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    result = main()
