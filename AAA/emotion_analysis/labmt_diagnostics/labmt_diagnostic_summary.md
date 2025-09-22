# LabMT Deep Diagnostic Report

**Generated:** 2025-09-13 13:44:38

## Critical Issues Found

🚨 **NEGATION HANDLING**: Current LabMT implementation does NOT handle negation or context reversal.
   - Detection rate: 60.0%
   - Impact: Sentences like 'not good' are treated as positive

📊 **COVERAGE ANALYSIS**:
   - Mean coverage rate: 99.6%
   - Low coverage stories: 0/54

🔤 **STOPWORDS IMPACT**:
   - Stopwords in dictionary: 30.8%
   - Score change without stopwords: 54.2%

## Recommendations

1. **Implement negation handling** - Add context-aware sentiment reversal
2. **Improve tokenization** - Handle contractions and punctuation better
3. **Filter stopwords** - Remove or weight down non-content words
4. **Add smoothing** - Apply temporal smoothing to reduce noise
5. **Validate coverage** - Ensure >85% vocabulary coverage per text

## Files Generated

- `labmt_diagnostic_report.json`: Complete diagnostic data
- `labmt_coverage_distribution.png`: Coverage rate distribution
- `labmt_coverage_by_genre.png`: Coverage by genre comparison
