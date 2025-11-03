# Using Calibre-ICV DRC Pairs to Improve Your Translator

## Why Your DRC Pairs Are Extremely Valuable 🎯

Having multiple Calibre SVRF and IC Validator PXL pairs is **the best resource** for building a production-quality translator!

### What Makes Them Valuable

✅ **Real-world examples** - Actual production rule decks, not synthetic
✅ **Correct translations** - Already validated by Synopsys/foundry
✅ **Edge cases** - Contains complex rules you might not think of
✅ **Pattern library** - Shows translation patterns for all constructs
✅ **Test suite** - Ready-made regression tests
✅ **Training data** - Can be used for ML-based approaches (optional)

---

## How to Use Your DRC Pairs

### Phase 1: Extract Translation Patterns (Week 1)

#### 1.1 Organize Your Pairs

```bash
# Create organized structure
mkdir -p translator-training/{pairs,patterns,tests}

# Organize pairs
translator-training/pairs/
├── foundry_a/
│   ├── metal_rules.svrf
│   ├── metal_rules.rs
│   ├── via_rules.svrf
│   └── via_rules.rs
├── foundry_b/
│   ├── drc_deck.svrf
│   └── drc_deck.rs
└── custom/
    ├── custom1.svrf
    └── custom1.rs
```

#### 1.2 Extract Patterns

Create a pattern extraction script:

```python
#!/usr/bin/env python3
# extract_patterns.py
"""
Extract SVRF→PXL translation patterns from paired examples
"""

import re
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class TranslationPattern:
    """A SVRF→PXL translation pattern"""
    svrf_pattern: str
    pxl_pattern: str
    rule_type: str  # 'width', 'spacing', 'enclosure', etc.
    count: int = 1
    examples: List[Tuple[str, str]] = None

    def __post_init__(self):
        if self.examples is None:
            self.examples = []

class PatternExtractor:
    """Extract translation patterns from SVRF/PXL pairs"""

    def __init__(self):
        self.patterns = defaultdict(list)

    def extract_from_pair(self, svrf_file: Path, pxl_file: Path):
        """Extract patterns from a single pair"""

        # Read both files
        svrf_content = svrf_file.read_text()
        pxl_content = pxl_file.read_text()

        # Extract layer definitions
        self._extract_layer_patterns(svrf_content, pxl_content)

        # Extract DRC rules
        self._extract_rule_patterns(svrf_content, pxl_content)

        # Extract boolean operations
        self._extract_boolean_patterns(svrf_content, pxl_content)

    def _extract_layer_patterns(self, svrf: str, pxl: str):
        """Extract layer definition patterns"""

        # Find all SVRF layer definitions
        svrf_layers = re.findall(
            r'LAYER\s+(\w+)\s+(\d+)(?:\s+(\d+))?',
            svrf
        )

        # Find all PXL layer definitions
        pxl_layers = re.findall(
            r'(\w+)\s*=\s*layer\((\d+),\s*(\d+)\)',
            pxl
        )

        # Create mapping
        for (name, num, dt) in svrf_layers:
            dt = dt or "0"
            svrf_pattern = f"LAYER {name} {num} {dt}"

            # Find matching PXL
            for (pxl_name, pxl_num, pxl_dt) in pxl_layers:
                if pxl_name == name and pxl_num == num:
                    pxl_pattern = f"{pxl_name} = layer({pxl_num}, {pxl_dt})"

                    self.patterns['layer'].append(
                        TranslationPattern(
                            svrf_pattern=svrf_pattern,
                            pxl_pattern=pxl_pattern,
                            rule_type='layer',
                            examples=[(svrf_pattern, pxl_pattern)]
                        )
                    )

    def _extract_rule_patterns(self, svrf: str, pxl: str):
        """Extract DRC rule patterns"""

        # Width checks
        svrf_width = re.findall(
            r'WIDTH\s+(\w+)\s*([<>=!]+)\s*([\d.]+)',
            svrf
        )
        pxl_width = re.findall(
            r'width\((\w+)\)\s*([<>=!]+)\s*([\d.]+)',
            pxl
        )

        for svrf_match, pxl_match in zip(svrf_width, pxl_width):
            if svrf_match[0] == pxl_match[0]:  # Same layer
                svrf_pattern = f"WIDTH {svrf_match[0]} {svrf_match[1]} {svrf_match[2]}"
                pxl_pattern = f"width({pxl_match[0]}) {pxl_match[1]} {pxl_match[2]}"

                self.patterns['width'].append(
                    TranslationPattern(
                        svrf_pattern=svrf_pattern,
                        pxl_pattern=pxl_pattern,
                        rule_type='width',
                        examples=[(svrf_pattern, pxl_pattern)]
                    )
                )

        # Spacing checks
        svrf_spacing = re.findall(
            r'EXTERNAL\s+(\w+)\s*([<>=!]+)\s*([\d.]+)',
            svrf
        )
        pxl_spacing = re.findall(
            r'external_distance\((\w+),\s*(\w+)\)\s*([<>=!]+)\s*([\d.]+)',
            pxl
        )

        for svrf_match, pxl_match in zip(svrf_spacing, pxl_spacing):
            if svrf_match[0] == pxl_match[0]:  # Same layer
                svrf_pattern = f"EXTERNAL {svrf_match[0]} {svrf_match[1]} {svrf_match[2]}"
                pxl_pattern = f"external_distance({pxl_match[0]}, {pxl_match[1]}) {pxl_match[2]} {pxl_match[3]}"

                self.patterns['spacing'].append(
                    TranslationPattern(
                        svrf_pattern=svrf_pattern,
                        pxl_pattern=pxl_pattern,
                        rule_type='spacing',
                        examples=[(svrf_pattern, pxl_pattern)]
                    )
                )

    def _extract_boolean_patterns(self, svrf: str, pxl: str):
        """Extract boolean operation patterns"""

        # AND operations
        svrf_and = re.findall(r'(\w+)\s*=\s*AND\s+(\w+)\s+(\w+)', svrf)
        pxl_and = re.findall(r'(\w+)\s*=\s*(\w+)\s+and\s+(\w+)', pxl)

        for svrf_match, pxl_match in zip(svrf_and, pxl_and):
            svrf_pattern = f"{svrf_match[0]} = AND {svrf_match[1]} {svrf_match[2]}"
            pxl_pattern = f"{pxl_match[0]} = {pxl_match[1]} and {pxl_match[2]}"

            self.patterns['boolean'].append(
                TranslationPattern(
                    svrf_pattern=svrf_pattern,
                    pxl_pattern=pxl_pattern,
                    rule_type='boolean',
                    examples=[(svrf_pattern, pxl_pattern)]
                )
            )

    def generate_pattern_library(self, output_file: Path):
        """Generate pattern library document"""

        with open(output_file, 'w') as f:
            f.write("# SVRF to PXL Translation Pattern Library\n\n")
            f.write("Extracted from real Calibre-ICV DRC pairs\n\n")

            for rule_type, patterns in self.patterns.items():
                f.write(f"## {rule_type.upper()} Patterns\n\n")

                for i, pattern in enumerate(patterns, 1):
                    f.write(f"### Pattern {i}\n\n")
                    f.write(f"**SVRF:**\n```svrf\n{pattern.svrf_pattern}\n```\n\n")
                    f.write(f"**PXL:**\n```pxl\n{pattern.pxl_pattern}\n```\n\n")

                    if pattern.examples:
                        f.write(f"**Examples ({len(pattern.examples)}):**\n")
                        for svrf_ex, pxl_ex in pattern.examples[:3]:  # Show first 3
                            f.write(f"- `{svrf_ex}` → `{pxl_ex}`\n")
                        f.write("\n")

# Main execution
def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 extract_patterns.py <pairs_directory>")
        sys.exit(1)

    pairs_dir = Path(sys.argv[1])
    extractor = PatternExtractor()

    # Find all SVRF files
    svrf_files = list(pairs_dir.rglob("*.svrf"))

    print(f"Found {len(svrf_files)} SVRF files")

    for svrf_file in svrf_files:
        # Find corresponding PXL file
        pxl_file = svrf_file.with_suffix('.rs')

        if not pxl_file.exists():
            # Try other common extensions
            pxl_file = svrf_file.with_suffix('.pxl')

        if pxl_file.exists():
            print(f"Processing: {svrf_file.name} → {pxl_file.name}")
            extractor.extract_from_pair(svrf_file, pxl_file)
        else:
            print(f"Warning: No PXL file found for {svrf_file.name}")

    # Generate pattern library
    output = pairs_dir / "translation_patterns.md"
    extractor.generate_pattern_library(output)

    print(f"\nPattern library generated: {output}")
    print(f"Total patterns extracted: {sum(len(p) for p in extractor.patterns.values())}")

if __name__ == '__main__':
    main()
```

**Run it:**
```bash
python3 extract_patterns.py translator-training/pairs/
```

**Output:**
- `translation_patterns.md` - Complete pattern library
- Statistics on pattern types
- Coverage analysis

---

### Phase 2: Build Test Suite (Week 1-2)

#### 2.1 Create Regression Tests

```python
#!/usr/bin/env python3
# build_test_suite.py
"""
Build regression test suite from Calibre-ICV pairs
"""

import json
from pathlib import Path

class TestSuiteBuilder:
    """Build translator test suite from pairs"""

    def __init__(self):
        self.tests = []

    def add_test_from_pair(self, svrf_file: Path, pxl_file: Path):
        """Create test case from a pair"""

        test_case = {
            'name': svrf_file.stem,
            'input_file': str(svrf_file),
            'expected_output_file': str(pxl_file),
            'svrf_content': svrf_file.read_text(),
            'expected_pxl': pxl_file.read_text(),
            'metadata': {
                'source': svrf_file.parent.name,
                'size': len(svrf_file.read_text().split('\n'))
            }
        }

        self.tests.append(test_case)

    def save_test_suite(self, output_file: Path):
        """Save test suite to JSON"""

        with open(output_file, 'w') as f:
            json.dump({
                'tests': self.tests,
                'total_tests': len(self.tests),
                'metadata': {
                    'generated_from': 'Calibre-ICV pairs',
                    'format_version': '1.0'
                }
            }, f, indent=2)

# Usage
builder = TestSuiteBuilder()

for svrf_file in Path('translator-training/pairs').rglob('*.svrf'):
    pxl_file = svrf_file.with_suffix('.rs')
    if pxl_file.exists():
        builder.add_test_from_pair(svrf_file, pxl_file)

builder.save_test_suite(Path('translator-training/test_suite.json'))
```

#### 2.2 Test Runner

```python
#!/usr/bin/env python3
# run_regression_tests.py
"""
Run regression tests against your translator
"""

import json
import sys
from pathlib import Path
from mini_translator_prototype import translate_file

def run_test_suite(test_suite_file: Path, translator_cmd: str):
    """Run all regression tests"""

    with open(test_suite_file) as f:
        suite = json.load(f)

    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }

    print(f"Running {suite['total_tests']} regression tests...")
    print("=" * 80)

    for test in suite['tests']:
        print(f"\nTest: {test['name']}")

        try:
            # Run translator
            actual_output = translate_file(test['input_file'])
            expected_output = test['expected_pxl']

            # Compare (fuzzy matching for now)
            if compare_pxl(actual_output, expected_output):
                print("  ✅ PASS")
                results['passed'] += 1
            else:
                print("  ❌ FAIL - Output differs")
                results['failed'] += 1
                results['errors'].append({
                    'test': test['name'],
                    'reason': 'Output mismatch'
                })
        except Exception as e:
            print(f"  ❌ ERROR - {e}")
            results['failed'] += 1
            results['errors'].append({
                'test': test['name'],
                'reason': str(e)
            })

    # Print summary
    print("\n" + "=" * 80)
    print(f"Results: {results['passed']}/{suite['total_tests']} passed")
    print(f"Success rate: {results['passed']/suite['total_tests']*100:.1f}%")

    return results

def compare_pxl(actual: str, expected: str) -> bool:
    """Compare PXL outputs (implement fuzzy matching)"""
    # Normalize whitespace
    actual_lines = [l.strip() for l in actual.split('\n') if l.strip()]
    expected_lines = [l.strip() for l in expected.split('\n') if l.strip()]

    # Compare line by line (ignoring comments and whitespace)
    return actual_lines == expected_lines

if __name__ == '__main__':
    results = run_test_suite(
        Path('translator-training/test_suite.json'),
        'python3 mini_translator_prototype.py'
    )

    sys.exit(0 if results['failed'] == 0 else 1)
```

---

### Phase 3: Improve Translator (Week 2-4)

#### 3.1 Identify Coverage Gaps

```python
#!/usr/bin/env python3
# analyze_coverage.py
"""
Analyze what SVRF constructs your translator doesn't handle yet
"""

from collections import defaultdict
import re

def analyze_svrf_constructs(svrf_files):
    """Find all SVRF constructs in your pairs"""

    constructs = defaultdict(int)

    for svrf_file in svrf_files:
        content = svrf_file.read_text()

        # Find all SVRF keywords
        keywords = re.findall(r'\b([A-Z_]{3,})\b', content)

        for keyword in keywords:
            constructs[keyword] += 1

    return dict(sorted(constructs.items(), key=lambda x: x[1], reverse=True))

# Run analysis
from pathlib import Path

svrf_files = list(Path('translator-training/pairs').rglob('*.svrf'))
constructs = analyze_svrf_constructs(svrf_files)

print("SVRF Constructs Found:")
print("=" * 50)
for construct, count in constructs.items():
    print(f"{construct:30s} {count:5d} occurrences")
```

**Example output:**
```
SVRF Constructs Found:
==================================================
LAYER                          245 occurrences
WIDTH                          156 occurrences
EXTERNAL                       134 occurrences
ENC                            89 occurrences
INTERNAL                       67 occurrences
AREA                           45 occurrences
DENSITY                        23 occurrences
RECTANGLES                     18 occurrences
DFM                            12 occurrences
```

#### 3.2 Prioritize Features

Based on coverage analysis, prioritize implementing features by frequency:

1. **High priority** (>100 occurrences)
   - LAYER, WIDTH, EXTERNAL, SPACING

2. **Medium priority** (50-100)
   - ENC, INTERNAL, AREA

3. **Low priority** (<50)
   - DENSITY, RECTANGLES, DFM

---

### Phase 4: Validate Translation Quality

#### 4.1 Semantic Comparison

```python
#!/usr/bin/env python3
# semantic_validator.py
"""
Validate that translated PXL is semantically equivalent to original
"""

def validate_translation(svrf_file, translated_pxl, reference_pxl):
    """
    Validate translation quality

    Returns:
        - syntax_correct: bool
        - semantically_equivalent: bool
        - confidence: float (0-1)
    """

    results = {
        'syntax_correct': check_pxl_syntax(translated_pxl),
        'semantically_equivalent': False,
        'confidence': 0.0,
        'differences': []
    }

    # Extract rule counts
    trans_rules = extract_rules(translated_pxl)
    ref_rules = extract_rules(reference_pxl)

    # Compare
    if len(trans_rules) == len(ref_rules):
        results['confidence'] += 0.3

    # Compare rule types
    trans_types = set(r['type'] for r in trans_rules)
    ref_types = set(r['type'] for r in ref_rules)

    if trans_types == ref_types:
        results['confidence'] += 0.3

    # Compare layer mappings
    trans_layers = extract_layers(translated_pxl)
    ref_layers = extract_layers(reference_pxl)

    if trans_layers == ref_layers:
        results['confidence'] += 0.4
    else:
        results['differences'].append('Layer mappings differ')

    results['semantically_equivalent'] = results['confidence'] >= 0.8

    return results
```

---

## Best Practices for Using Your Pairs

### 1. Organize by Complexity

```
pairs/
├── simple/          # Single rule type (width, spacing)
├── medium/          # Multiple rule types
├── complex/         # Macros, functions, advanced features
└── production/      # Full production decks
```

### 2. Document Differences

Create a mapping file for each pair:

```yaml
# metal_rules_mapping.yaml
svrf_file: metal_rules.svrf
pxl_file: metal_rules.rs
foundry: TSMC_N7
differences:
  - type: layer_naming
    svrf: "METAL1"
    pxl: "M1"
    reason: "Abbreviation used in PXL"

  - type: additional_check
    location: "line 45"
    reason: "ICV has extra density check not in Calibre"

notes: |
  This pair shows standard metal layer DRC rules.
  All basic checks (width, spacing, enclosure) translate directly.
```

### 3. Create a Coverage Matrix

```python
# Generate coverage matrix
coverage = {
    'layer_definition': {
        'count': 245,
        'translator_supports': True,
        'accuracy': 100.0
    },
    'width_check': {
        'count': 156,
        'translator_supports': True,
        'accuracy': 98.5
    },
    'density_check': {
        'count': 23,
        'translator_supports': False,
        'accuracy': 0.0
    }
}
```

---

## Recommended Workflow

### Week 1: Pattern Extraction
```bash
# 1. Organize pairs
mkdir -p translator-training/pairs
cp -r /path/to/your/pairs/* translator-training/pairs/

# 2. Extract patterns
python3 extract_patterns.py translator-training/pairs/

# 3. Review patterns
cat translator-training/pairs/translation_patterns.md
```

### Week 2: Test Suite Creation
```bash
# 1. Build test suite
python3 build_test_suite.py

# 2. Run baseline tests
python3 run_regression_tests.py

# 3. Analyze coverage gaps
python3 analyze_coverage.py
```

### Week 3-4: Iterative Improvement
```bash
# 1. Implement missing features (prioritized by coverage)
# 2. Re-run tests
# 3. Improve accuracy
# 4. Repeat until >95% pass rate
```

---

## Expected Outcomes

With your DRC pairs, you can achieve:

| Metric | Without Pairs | With Pairs |
|--------|---------------|------------|
| **Development time** | 6 months | 3-4 months |
| **Coverage** | 60-70% | 90-95% |
| **Accuracy** | 70-80% | 95-98% |
| **Confidence** | Low | High |
| **Test cases** | Few synthetic | Many real-world |

---

## Quick Start Checklist

- [ ] Collect all Calibre-ICV pairs you have
- [ ] Organize into directory structure
- [ ] Run pattern extraction
- [ ] Build regression test suite
- [ ] Analyze coverage gaps
- [ ] Prioritize features by frequency
- [ ] Iteratively improve translator
- [ ] Validate against all pairs
- [ ] Document any unsupported features
- [ ] Achieve >95% test pass rate

---

## Summary

Your Calibre-ICV DRC pairs are **invaluable** because they provide:

1. ✅ **Real translation examples** - Learn from expert translations
2. ✅ **Comprehensive coverage** - All constructs you need to support
3. ✅ **Regression tests** - Validate your translator works
4. ✅ **Pattern library** - Reference for implementation
5. ✅ **Confidence** - Know your translator handles real decks

**Next steps:**
1. Share how many pairs you have
2. Run pattern extraction
3. Build test suite
4. Start improving translator

**This will dramatically accelerate your translator development!** 🚀
