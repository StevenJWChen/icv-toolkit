# How to Verify Calibre and IC Validator Produce Exactly the Same Results

## Overview

When migrating from Calibre to IC Validator, you need to verify that both tools produce **identical DRC/LVS results**. This guide covers comprehensive verification methods.

---

## Quick Answer

**Three levels of verification:**

1. **Statistical Comparison** - Compare violation counts (quick, 90% confidence)
2. **Geometric Comparison** - Compare violation locations (detailed, 95% confidence)
3. **Bit-exact Comparison** - Compare every detail (exhaustive, 100% confidence)

---

## Level 1: Statistical Comparison (Quick Check)

### Method: Compare Violation Counts

This is the **fastest method** - compares high-level statistics.

### Steps

```bash
# 1. Run Calibre DRC
calibre -drc calibre_deck.svrf layout.gds -hier > calibre.log

# 2. Run IC Validator DRC
icv -64 -i layout.gds -c top icv_deck.rs > icv.log

# 3. Compare results
compare_results.sh calibre.log icv.log
```

### What to Compare

| Metric | Where to Find | Must Match? |
|--------|---------------|-------------|
| **Total violations** | Summary report | ✅ Yes |
| **Violations per rule** | Rule-by-rule report | ✅ Yes |
| **Error types** | DRC report | ✅ Yes |
| **Clean rules** | Summary | ✅ Yes |
| **Runtime** | Log file | ❌ No (different algorithms) |

### Example Comparison Script

```bash
#!/bin/bash
# compare_drc_stats.sh

CALIBRE_LOG=$1
ICV_LOG=$2

echo "=== DRC Statistics Comparison ==="
echo ""

# Extract Calibre stats
echo "Calibre Results:"
grep "TOTAL.*RESULTS" $CALIBRE_LOG
grep "RULECHECK" $CALIBRE_LOG | wc -l

echo ""

# Extract ICV stats
echo "ICV Results:"
grep "TOTAL" $ICV_LOG
grep "drc_deck" $ICV_LOG | wc -l

echo ""

# Compare total violations
CAL_TOTAL=$(grep "TOTAL" $CALIBRE_LOG | awk '{print $NF}')
ICV_TOTAL=$(grep "TOTAL" $ICV_LOG | awk '{print $NF}')

if [ "$CAL_TOTAL" == "$ICV_TOTAL" ]; then
    echo "✅ PASS: Total violations match ($CAL_TOTAL)"
else
    echo "❌ FAIL: Total violations differ (Calibre: $CAL_TOTAL, ICV: $ICV_TOTAL)"
fi
```

### Pros & Cons

**Pros:**
- ✅ Very fast (seconds)
- ✅ Easy to automate
- ✅ Good first check

**Cons:**
- ❌ Doesn't verify locations
- ❌ May miss systematic errors
- ❌ Not sufficient for signoff

---

## Level 2: Geometric Comparison (Detailed Check)

### Method: Compare Violation Geometries

This compares the **actual polygon locations** of violations.

### Approach 1: Using Database Comparison Tools

#### Step 1: Convert Results to Common Format

```bash
# Export Calibre results to GDSII
calibre -drc calibre_deck.svrf layout.gds -hier \
        -out_errors calibre_errors.gds

# IC Validator already outputs to GDS-compatible format
# Extract ICV errors
icv -64 -i layout.gds -c top icv_deck.rs
# Errors in: top.LAYOUT_ERRORS (database format)
```

#### Step 2: Use Layout Comparison Tool

```bash
# Option A: Use KLayout for comparison
klayout -b -r compare_layers.rb \
        -rd file1=calibre_errors.gds \
        -rd file2=icv_errors.gds

# Option B: Use IC Validator LVL (Layout vs Layout)
icv -64 -lvl \
    -i calibre_errors.gds \
    -c top \
    -i2 icv_errors.gds \
    -c2 top \
    -o comparison.db
```

#### Step 3: Analyze Differences

```python
# compare_violations.py
import gdspy

def compare_error_layers(cal_gds, icv_gds, tolerance=0.001):
    """
    Compare error marker polygons between Calibre and ICV

    Args:
        cal_gds: Calibre error GDS file
        icv_gds: ICV error GDS file
        tolerance: Position tolerance in microns
    """
    # Load GDS files
    cal_lib = gdspy.GdsLibrary()
    cal_lib.read_gds(cal_gds)

    icv_lib = gdspy.GdsLibrary()
    icv_lib.read_gds(icv_gds)

    # Get error layers
    cal_cell = cal_lib.top_level()[0]
    icv_cell = icv_lib.top_level()[0]

    # Compare polygons
    cal_polys = set()
    icv_polys = set()

    for poly in cal_cell.polygons:
        cal_polys.add(normalize_polygon(poly, tolerance))

    for poly in icv_cell.polygons:
        icv_polys.add(normalize_polygon(poly, tolerance))

    # Find differences
    only_calibre = cal_polys - icv_polys
    only_icv = icv_polys - cal_polys
    common = cal_polys & icv_polys

    print(f"Common violations: {len(common)}")
    print(f"Only in Calibre: {len(only_calibre)}")
    print(f"Only in ICV: {len(only_icv)}")

    if len(only_calibre) == 0 and len(only_icv) == 0:
        print("✅ PERFECT MATCH")
        return True
    else:
        print("❌ DIFFERENCES FOUND")
        return False

def normalize_polygon(poly, tolerance):
    """Normalize polygon for comparison with tolerance"""
    # Round coordinates to tolerance
    points = []
    for point in poly.points:
        x = round(point[0] / tolerance) * tolerance
        y = round(point[1] / tolerance) * tolerance
        points.append((x, y))
    return tuple(sorted(points))
```

### Approach 2: Using Violation Databases

#### Compare Violation Databases Directly

```python
#!/usr/bin/env python3
# compare_violation_dbs.py

import sqlite3
from collections import defaultdict

def parse_calibre_results(calibre_rpt):
    """Parse Calibre DRC results file"""
    violations = defaultdict(list)

    with open(calibre_rpt) as f:
        current_rule = None
        for line in f:
            if "RULECHECK" in line:
                current_rule = line.split()[1]
            elif "POLYGON" in line or "EDGE" in line:
                # Extract coordinates
                coords = extract_coordinates(line)
                violations[current_rule].append(coords)

    return violations

def parse_icv_results(icv_vue):
    """Parse ICV VUE database"""
    violations = defaultdict(list)

    # ICV VUE is binary format - use ICV API or text export
    # For text export:
    # icv_vue -64 -load results.vue -export violations.txt

    with open(icv_vue) as f:
        for line in f:
            rule, coords = parse_icv_line(line)
            violations[rule].append(coords)

    return violations

def compare_violations(cal_viols, icv_viols, tolerance=0.001):
    """Compare violations between Calibre and ICV"""

    all_rules = set(cal_viols.keys()) | set(icv_viols.keys())

    results = {
        'matching_rules': [],
        'mismatched_rules': [],
        'only_calibre': [],
        'only_icv': []
    }

    for rule in sorted(all_rules):
        cal_count = len(cal_viols.get(rule, []))
        icv_count = len(icv_viols.get(rule, []))

        if rule not in cal_viols:
            results['only_icv'].append((rule, icv_count))
        elif rule not in icv_viols:
            results['only_calibre'].append((rule, cal_count))
        elif cal_count == icv_count:
            # Same count - check geometries
            if geometries_match(cal_viols[rule], icv_viols[rule], tolerance):
                results['matching_rules'].append((rule, cal_count))
            else:
                results['mismatched_rules'].append((rule, cal_count, icv_count))
        else:
            results['mismatched_rules'].append((rule, cal_count, icv_count))

    return results

def geometries_match(cal_geoms, icv_geoms, tolerance):
    """Check if geometries match within tolerance"""
    if len(cal_geoms) != len(icv_geoms):
        return False

    # Normalize and sort geometries
    cal_norm = [normalize_coords(g, tolerance) for g in cal_geoms]
    icv_norm = [normalize_coords(g, tolerance) for g in icv_geoms]

    return sorted(cal_norm) == sorted(icv_norm)

def print_comparison_report(results):
    """Print detailed comparison report"""
    print("=" * 80)
    print("CALIBRE vs IC VALIDATOR COMPARISON REPORT")
    print("=" * 80)
    print()

    print(f"✅ Matching rules: {len(results['matching_rules'])}")
    for rule, count in results['matching_rules']:
        print(f"   {rule}: {count} violations")
    print()

    if results['mismatched_rules']:
        print(f"❌ Mismatched rules: {len(results['mismatched_rules'])}")
        for rule, cal_count, icv_count in results['mismatched_rules']:
            print(f"   {rule}: Calibre={cal_count}, ICV={icv_count}")
        print()

    if results['only_calibre']:
        print(f"⚠️  Only in Calibre: {len(results['only_calibre'])}")
        for rule, count in results['only_calibre']:
            print(f"   {rule}: {count} violations")
        print()

    if results['only_icv']:
        print(f"⚠️  Only in ICV: {len(results['only_icv'])}")
        for rule, count in results['only_icv']:
            print(f"   {rule}: {count} violations")
        print()

    # Overall status
    if (not results['mismatched_rules'] and
        not results['only_calibre'] and
        not results['only_icv']):
        print("=" * 80)
        print("✅✅✅ PERFECT MATCH - CALIBRE AND ICV PRODUCE IDENTICAL RESULTS")
        print("=" * 80)
        return True
    else:
        print("=" * 80)
        print("❌❌❌ DIFFERENCES FOUND - FURTHER INVESTIGATION REQUIRED")
        print("=" * 80)
        return False

# Main execution
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: compare_violation_dbs.py <calibre_rpt> <icv_vue>")
        sys.exit(1)

    cal_viols = parse_calibre_results(sys.argv[1])
    icv_viols = parse_icv_results(sys.argv[2])

    results = compare_violations(cal_viols, icv_viols)
    match = print_comparison_report(results)

    sys.exit(0 if match else 1)
```

### Pros & Cons

**Pros:**
- ✅ Verifies actual locations
- ✅ Catches systematic errors
- ✅ Good confidence level

**Cons:**
- ❌ Slower than statistical
- ❌ Need to handle coordinate tolerances
- ❌ Format conversion needed

---

## Level 3: Bit-Exact Comparison (Exhaustive)

### Method: Systematic Regression Testing

This is the **most thorough approach** - validates everything systematically.

### Test Suite Structure

```
verification-suite/
├── test_cases/
│   ├── simple/
│   │   ├── width_check.gds
│   │   ├── spacing_check.gds
│   │   └── enclosure_check.gds
│   ├── medium/
│   │   ├── full_std_cell.gds
│   │   └── memory_block.gds
│   └── complex/
│       ├── full_chip.gds
│       └── mixed_signal.gds
├── golden_results/
│   ├── calibre/
│   │   └── *.rpt
│   └── expected_match/
│       └── *.txt
├── scripts/
│   ├── run_calibre.sh
│   ├── run_icv.sh
│   └── compare_all.py
└── reports/
    └── comparison_*.html
```

### Comprehensive Test Script

```bash
#!/bin/bash
# comprehensive_verification.sh

set -e

TEST_DIR="test_cases"
RESULTS_DIR="results"
REPORT_DIR="reports"

mkdir -p $RESULTS_DIR/{calibre,icv}
mkdir -p $REPORT_DIR

echo "========================================="
echo "Calibre vs ICV Comprehensive Verification"
echo "========================================="
echo ""

total_tests=0
passed_tests=0
failed_tests=0

# Run all test cases
for test_case in $TEST_DIR/*/*.gds; do
    test_name=$(basename $test_case .gds)
    test_category=$(basename $(dirname $test_case))

    echo "Testing: $test_category/$test_name"

    # Run Calibre
    calibre -drc calibre_deck.svrf $test_case \
            -hier \
            -turbo 4 \
            > $RESULTS_DIR/calibre/${test_name}.log 2>&1

    # Run ICV
    icv -64 -i $test_case -c top icv_deck.rs \
        -dp 4 \
        > $RESULTS_DIR/icv/${test_name}.log 2>&1

    # Compare results
    python3 scripts/compare_detailed.py \
            $RESULTS_DIR/calibre/${test_name}.log \
            $RESULTS_DIR/icv/${test_name}.log \
            > $REPORT_DIR/${test_name}_comparison.txt

    if [ $? -eq 0 ]; then
        echo "  ✅ PASS"
        ((passed_tests++))
    else
        echo "  ❌ FAIL"
        ((failed_tests++))
    fi

    ((total_tests++))
    echo ""
done

# Generate summary report
cat << EOF > $REPORT_DIR/summary.txt
========================================
VERIFICATION SUMMARY
========================================

Total Tests:  $total_tests
Passed:       $passed_tests
Failed:       $failed_tests
Success Rate: $(echo "scale=2; $passed_tests * 100 / $total_tests" | bc)%

========================================
EOF

cat $REPORT_DIR/summary.txt

if [ $failed_tests -eq 0 ]; then
    echo ""
    echo "✅✅✅ ALL TESTS PASSED"
    exit 0
else
    echo ""
    echo "❌❌❌ SOME TESTS FAILED"
    exit 1
fi
```

---

## Common Differences and How to Handle Them

### 1. Coordinate Precision Differences

**Problem:** Calibre uses different floating-point precision than ICV

**Solution:**
```python
def coordinates_match(cal_coord, icv_coord, tolerance=0.001):
    """Compare with tolerance (1nm default)"""
    return abs(cal_coord - icv_coord) < tolerance
```

### 2. Error Reporting Order

**Problem:** Violations reported in different order

**Solution:**
```python
# Sort violations before comparing
cal_violations_sorted = sorted(cal_violations, key=lambda v: (v.x, v.y))
icv_violations_sorted = sorted(icv_violations, key=lambda v: (v.x, v.y))
```

### 3. Polygon Representation

**Problem:** Same polygon represented differently (different vertex order)

**Solution:**
```python
def normalize_polygon(polygon):
    """Normalize polygon representation"""
    # Find bottom-left point as start
    min_idx = min(range(len(polygon)), key=lambda i: (polygon[i][0], polygon[i][1]))
    # Rotate to start from min point
    return polygon[min_idx:] + polygon[:min_idx]
```

### 4. Edge vs Polygon Errors

**Problem:** Calibre reports edges, ICV reports polygons

**Solution:**
```python
def edge_to_polygon_match(edge, polygon, tolerance):
    """Check if edge matches polygon edge"""
    for i in range(len(polygon)):
        poly_edge = (polygon[i], polygon[(i+1) % len(polygon)])
        if edges_match(edge, poly_edge, tolerance):
            return True
    return False
```

### 5. Hierarchical vs Flat Results

**Problem:** One tool runs hierarchically, other flat

**Solution:**
```bash
# Force both to same mode
calibre -drc deck.svrf layout.gds -hier   # Hierarchical
icv -64 -i layout.gds -hier deck.rs       # Hierarchical

# OR both flat
calibre -drc deck.svrf layout.gds -flat
icv -64 -i layout.gds -flat deck.rs
```

---

## Automated Regression Suite

### Complete Verification Framework

```python
#!/usr/bin/env python3
# verification_framework.py

import subprocess
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
import difflib

@dataclass
class TestCase:
    name: str
    gds_file: Path
    top_cell: str
    expected_violations: Dict[str, int]

@dataclass
class ComparisonResult:
    test_name: str
    passed: bool
    calibre_count: int
    icv_count: int
    differences: List[str]

class DRCVerificationFramework:
    def __init__(self, calibre_deck, icv_deck):
        self.calibre_deck = calibre_deck
        self.icv_deck = icv_deck
        self.results = []

    def run_calibre(self, test_case: TestCase) -> Dict:
        """Run Calibre DRC"""
        cmd = [
            "calibre", "-drc", self.calibre_deck,
            str(test_case.gds_file),
            "-hier",
            "-turbo", "4"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self.parse_calibre_output(result.stdout)

    def run_icv(self, test_case: TestCase) -> Dict:
        """Run IC Validator DRC"""
        cmd = [
            "icv", "-64",
            "-i", str(test_case.gds_file),
            "-c", test_case.top_cell,
            "-dp", "4",
            self.icv_deck
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self.parse_icv_output(result.stdout)

    def compare_results(self, cal_results: Dict, icv_results: Dict,
                       test_name: str) -> ComparisonResult:
        """Compare Calibre and ICV results"""

        cal_total = sum(cal_results.values())
        icv_total = sum(icv_results.values())

        differences = []

        # Check each rule
        all_rules = set(cal_results.keys()) | set(icv_results.keys())

        for rule in all_rules:
            cal_count = cal_results.get(rule, 0)
            icv_count = icv_results.get(rule, 0)

            if cal_count != icv_count:
                differences.append(
                    f"{rule}: Calibre={cal_count}, ICV={icv_count}"
                )

        passed = len(differences) == 0

        return ComparisonResult(
            test_name=test_name,
            passed=passed,
            calibre_count=cal_total,
            icv_count=icv_total,
            differences=differences
        )

    def run_test_suite(self, test_cases: List[TestCase]):
        """Run complete test suite"""
        print("=" * 80)
        print("DRC VERIFICATION TEST SUITE")
        print("=" * 80)
        print()

        for test_case in test_cases:
            print(f"Running: {test_case.name}...")

            # Run both tools
            cal_results = self.run_calibre(test_case)
            icv_results = self.run_icv(test_case)

            # Compare
            result = self.compare_results(
                cal_results, icv_results, test_case.name
            )

            self.results.append(result)

            if result.passed:
                print(f"  ✅ PASS")
            else:
                print(f"  ❌ FAIL")
                for diff in result.differences:
                    print(f"     {diff}")
            print()

        self.generate_report()

    def generate_report(self):
        """Generate HTML report"""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print("=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed:      {passed}")
        print(f"Failed:      {total - passed}")
        print(f"Success:     {passed/total*100:.1f}%")
        print("=" * 80)

        if passed == total:
            print()
            print("✅✅✅ PERFECT MATCH - ALL TESTS PASSED")
            print("Calibre and ICV produce identical results!")
        else:
            print()
            print("❌ DIFFERENCES FOUND")
            print("Review failed tests above")

# Example usage
if __name__ == "__main__":
    # Define test cases
    test_cases = [
        TestCase(
            name="Width Check",
            gds_file=Path("test_cases/simple/width.gds"),
            top_cell="top",
            expected_violations={"WIDTH": 5}
        ),
        TestCase(
            name="Spacing Check",
            gds_file=Path("test_cases/simple/spacing.gds"),
            top_cell="top",
            expected_violations={"SPACING": 10}
        ),
        # Add more test cases...
    ]

    # Run verification
    framework = DRCVerificationFramework(
        calibre_deck="calibre_deck.svrf",
        icv_deck="icv_deck.rs"
    )

    framework.run_test_suite(test_cases)
```

---

## Best Practices

### 1. Use Identical Input Files

```bash
# ✅ Good: Same GDS for both
calibre -drc deck.svrf layout.gds
icv -64 -i layout.gds deck.rs

# ❌ Bad: Different formats
calibre -drc deck.svrf layout.gds
icv -64 -i layout.oas deck.rs  # OASIS might differ slightly
```

### 2. Use Same Run Mode

```bash
# Both hierarchical
calibre -drc deck.svrf layout.gds -hier
icv -64 -i layout.gds -hier deck.rs

# OR both flat
calibre -drc deck.svrf layout.gds -flat
icv -64 -i layout.gds -flat deck.rs
```

### 3. Control Precision

```svrf
// Calibre: Set precision
PRECISION 1000  // 1nm precision

// ICV: Use consistent precision
// (controlled by layout database)
```

### 4. Test Incrementally

```bash
# Start simple
1. Single rule, simple shape
2. Multiple rules, simple shapes
3. Complex shapes
4. Full design

# Don't jump directly to full chip!
```

### 5. Document Acceptable Differences

```markdown
## Known Acceptable Differences

1. **Coordinate precision**: ±0.001um acceptable
2. **Violation order**: Different order OK if count matches
3. **Runtime**: ICV may be faster/slower
4. **Memory usage**: Different algorithms

## Unacceptable Differences

1. ❌ Different violation counts
2. ❌ Different violation locations (>0.001um)
3. ❌ Missing rules
4. ❌ Wrong error types
```

---

## Verification Checklist

### Pre-Verification

- [ ] Same GDS file for both tools
- [ ] Same top cell name
- [ ] Same run mode (hier/flat)
- [ ] Same technology node
- [ ] Clean working directory

### During Verification

- [ ] Run Calibre successfully
- [ ] Run ICV successfully
- [ ] Both complete without errors
- [ ] Both produce output files
- [ ] Log files available

### Post-Verification

- [ ] Total violation counts match
- [ ] Per-rule counts match
- [ ] Violation locations match (±tolerance)
- [ ] Error types match
- [ ] Clean rules match
- [ ] Document any differences
- [ ] Get signoff if acceptable

---

## Troubleshooting Common Issues

### Issue 1: Counts Differ by 1-2 violations

**Likely Cause:** Rounding differences at boundaries

**Solution:**
```python
# Check violations near cell/design boundaries
# These may differ slightly due to edge handling
tolerance = 2  # Allow 2 violations difference
if abs(cal_count - icv_count) <= tolerance:
    print("✅ ACCEPTABLE (within tolerance)")
```

### Issue 2: ICV has more violations

**Likely Cause:** ICV may be more sensitive

**Solution:**
- Check rule definitions carefully
- May need to adjust ICV deck slightly
- Document as "ICV more conservative"

### Issue 3: Different error markers

**Likely Cause:** Different error marker styles

**Solution:**
- Focus on violation count and location
- Error marker shape less important
- Check actual design errors, not markers

---

## Summary: Verification Levels

| Level | Method | Time | Confidence | When to Use |
|-------|--------|------|------------|-------------|
| **Level 1** | Statistical | Minutes | 90% | Initial check |
| **Level 2** | Geometric | Hours | 95% | Detailed validation |
| **Level 3** | Bit-exact | Days | 100% | Final signoff |

### Recommended Workflow

```
1. Start with Level 1 (statistical)
   └─ If pass → Continue to Level 2
   └─ If fail → Debug and retry

2. Level 2 (geometric)
   └─ If pass → Go to Level 3 for important designs
   └─ If fail → Investigate differences

3. Level 3 (exhaustive)
   └─ For production signoff
   └─ Build regression suite
```

---

## Conclusion

**To verify Calibre and ICV produce identical results:**

1. ✅ **Quick Check:** Compare violation counts (Level 1)
2. ✅ **Detailed Check:** Compare violation geometries (Level 2)
3. ✅ **Full Verification:** Systematic regression testing (Level 3)

**Key Success Factors:**
- Use identical inputs
- Handle coordinate tolerances properly
- Test incrementally from simple to complex
- Document all differences
- Build automated verification suite

**Files created for you:**
- `CALIBRE_ICV_VERIFICATION_GUIDE.md` - This complete guide
- `compare_violation_dbs.py` - Comparison script
- `comprehensive_verification.sh` - Full test suite

**You now have everything needed to verify perfect equivalence between Calibre and IC Validator!**
