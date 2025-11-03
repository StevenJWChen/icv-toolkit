# Matching Variables Between Calibre and ICV Pairs

A comprehensive guide for identifying, comparing, and synchronizing variable definitions between Calibre SVRF and ICV PXL files to ensure complete translation coverage.

---

## Table of Contents

1. [The Variable Matching Problem](#the-variable-matching-problem)
2. [Understanding Variable Types](#understanding-variable-types)
3. [Automated Variable Comparison Tool](#automated-variable-comparison-tool)
4. [Manual Comparison Strategies](#manual-comparison-strategies)
5. [Matching Strategies](#matching-strategies)
6. [Common Missing Variable Patterns](#common-missing-variable-patterns)
7. [Step-by-Step Synchronization Workflow](#step-by-step-synchronization-workflow)
8. [Best Practices](#best-practices)

---

## The Variable Matching Problem

### What Are Variables in This Context?

In Calibre (SVRF) and ICV (PXL), "variables" are:

**1. Layer Definitions**
```svrf
// Calibre
LAYER METAL1 10
LAYER VIA1 30
```
```rust
// ICV
METAL1 = layer(10, 0);
VIA1 = layer(30, 0);
```

**2. Intermediate Results (Derived Layers)**
```svrf
// Calibre
metal1_wide = SIZE METAL1 BY 0.1
via_overlap = AND METAL1 VIA1
```
```rust
// ICV
metal1_wide = size(METAL1, 0.1);
via_overlap = and(METAL1, VIA1);
```

**3. Check Results**
```svrf
// Calibre
m1_width_errors = WIDTH METAL1 < 0.09
```
```rust
// ICV
m1_width_errors = width(METAL1) < 0.09;
```

### The Problem

When you have Calibre and ICV pairs:
- ❌ Some variables exist in Calibre but not in ICV
- ❌ Some variables exist in ICV but not in Calibre
- ❌ Some variables have different names
- ❌ Some variables are defined differently

**This causes:**
- Incomplete translations
- Missing DRC checks
- Different results between tools
- Difficult debugging

---

## Understanding Variable Types

### Type 1: Layer Definitions (Should Always Match)

**Calibre:**
```svrf
LAYER METAL1 10
LAYER METAL1_WIDE 10 DATATYPE 1
LAYER VIA1 30
```

**ICV (should match exactly):**
```rust
METAL1 = layer(10, 0);
METAL1_WIDE = layer(10, 1);
VIA1 = layer(30, 0);
```

**Status:** ✅ Must be identical

---

### Type 2: Derived Layers (Intermediate Results)

**Calibre:**
```svrf
// Sizing operations
metal1_grown = SIZE METAL1 BY 0.1
metal1_shrink = SIZE METAL1 BY -0.05

// Boolean operations
m1_via_overlap = AND METAL1 VIA1
metal_any = OR METAL1 METAL2
```

**ICV:**
```rust
// Same operations
metal1_grown = size(METAL1, 0.1);
metal1_shrink = size(METAL1, -0.05);
m1_via_overlap = and(METAL1, VIA1);
metal_any = or(METAL1, METAL2);
```

**Status:** ⚠️ Should match but names might differ

---

### Type 3: DRC Check Results

**Calibre:**
```svrf
M1_WIDTH { @ Width check
    m1_width_errors = WIDTH METAL1 < 0.09
}
```

**ICV:**
```rust
// Width check
m1_width_errors = width(METAL1) < 0.09;
drc_deck(m1_width_errors, "M1_WIDTH", "Width violation");
```

**Status:** ⚠️ Should match but might be named differently

---

### Type 4: Tool-Specific Variables

**Calibre-only:**
```svrf
// Calibre-specific constructs
CONNECT M1 BY VIA1 TO M2  // No direct ICV equivalent
DFM_RULES { ... }          // Calibre DFM features
```

**ICV-only:**
```rust
// ICV-specific constructs
polygon_density = density(METAL1, window_size=100);
antenna_ratio = antenna_check(METAL1, gate_layer);
```

**Status:** ❌ Cannot be directly matched (tool-specific)

---

## Automated Variable Comparison Tool

I'll create a Python script to automatically compare variables between Calibre and ICV files.

### Script: `compare_variables.py`

```python
#!/usr/bin/env python3
"""
Compare variable definitions between Calibre SVRF and ICV PXL files.
Identifies missing, mismatched, and unique variables.
"""

import re
import sys
from collections import defaultdict

class VariableComparator:
    def __init__(self):
        self.cal_variables = {}  # name -> definition
        self.icv_variables = {}  # name -> definition

    def parse_calibre(self, filepath):
        """Parse Calibre SVRF file for variable definitions."""
        print(f"Parsing Calibre file: {filepath}")

        with open(filepath, 'r') as f:
            content = f.read()

        # Pattern 1: LAYER definitions
        layer_pattern = r'^\s*LAYER\s+(\w+)\s+(\d+)(?:\s+DATATYPE\s+(\d+))?'
        for match in re.finditer(layer_pattern, content, re.MULTILINE):
            name = match.group(1)
            layer_num = match.group(2)
            datatype = match.group(3) or '0'
            self.cal_variables[name] = {
                'type': 'layer',
                'definition': f'LAYER {name} {layer_num} DATATYPE {datatype}',
                'line': content[:match.start()].count('\n') + 1
            }

        # Pattern 2: Variable assignments (derived layers)
        # Matches: var_name = OPERATION ...
        assign_pattern = r'^\s*(\w+)\s*=\s*([A-Z]+)\s+(.+?)(?:\n|$)'
        for match in re.finditer(assign_pattern, content, re.MULTILINE):
            name = match.group(1)
            operation = match.group(2)
            args = match.group(3).strip()
            if name not in self.cal_variables:  # Don't overwrite layers
                self.cal_variables[name] = {
                    'type': 'derived',
                    'definition': f'{name} = {operation} {args}',
                    'line': content[:match.start()].count('\n') + 1
                }

        # Pattern 3: Variables in rule blocks
        # Matches: RULE_NAME { var = CHECK ... }
        rule_var_pattern = r'^\s*(\w+)\s*{\s*[^}]*?^\s*(\w+)\s*=\s*([A-Z]+)\s+(.+?)$'
        for match in re.finditer(rule_var_pattern, content, re.MULTILINE | re.DOTALL):
            var_name = match.group(2)
            operation = match.group(3)
            args = match.group(4).strip()
            if var_name not in self.cal_variables:
                self.cal_variables[var_name] = {
                    'type': 'check',
                    'definition': f'{var_name} = {operation} {args}',
                    'line': content[:match.start()].count('\n') + 1
                }

        print(f"  Found {len(self.cal_variables)} Calibre variables")
        return self.cal_variables

    def parse_icv(self, filepath):
        """Parse ICV PXL file for variable definitions."""
        print(f"Parsing ICV file: {filepath}")

        with open(filepath, 'r') as f:
            content = f.read()

        # Pattern 1: Layer definitions
        # Matches: VAR = layer(num, datatype);
        layer_pattern = r'^\s*(\w+)\s*=\s*layer\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*;'
        for match in re.finditer(layer_pattern, content, re.MULTILINE):
            name = match.group(1)
            layer_num = match.group(2)
            datatype = match.group(3)
            self.icv_variables[name] = {
                'type': 'layer',
                'definition': f'{name} = layer({layer_num}, {datatype});',
                'line': content[:match.start()].count('\n') + 1
            }

        # Pattern 2: Variable assignments (derived layers/checks)
        # Matches: var_name = operation(...);
        assign_pattern = r'^\s*(\w+)\s*=\s*([a-z_]+)\s*\(([^;]+)\)\s*;'
        for match in re.finditer(assign_pattern, content, re.MULTILINE):
            name = match.group(1)
            operation = match.group(2)
            args = match.group(3).strip()
            if name not in self.icv_variables:  # Don't overwrite layers
                self.icv_variables[name] = {
                    'type': 'derived',
                    'definition': f'{name} = {operation}({args});',
                    'line': content[:match.start()].count('\n') + 1
                }

        # Pattern 3: Comparison operations
        # Matches: var = expr < value;
        comp_pattern = r'^\s*(\w+)\s*=\s*(.+?)\s*([<>=]+)\s*([^;]+)\s*;'
        for match in re.finditer(comp_pattern, content, re.MULTILINE):
            name = match.group(1)
            if name not in self.icv_variables:
                expr = match.group(2).strip()
                op = match.group(3)
                value = match.group(4).strip()
                self.icv_variables[name] = {
                    'type': 'check',
                    'definition': f'{name} = {expr} {op} {value};',
                    'line': content[:match.start()].count('\n') + 1
                }

        print(f"  Found {len(self.icv_variables)} ICV variables")
        return self.icv_variables

    def compare(self):
        """Compare Calibre and ICV variables."""
        print("\n" + "="*70)
        print("VARIABLE COMPARISON REPORT")
        print("="*70 + "\n")

        cal_names = set(self.cal_variables.keys())
        icv_names = set(self.icv_variables.keys())

        # Statistics
        total_cal = len(cal_names)
        total_icv = len(icv_names)
        matching = len(cal_names & icv_names)
        cal_only = len(cal_names - icv_names)
        icv_only = len(icv_names - cal_names)

        print(f"SUMMARY:")
        print(f"  Calibre variables:        {total_cal}")
        print(f"  ICV variables:            {total_icv}")
        print(f"  Matching (same name):     {matching}")
        print(f"  Calibre-only:             {cal_only}")
        print(f"  ICV-only:                 {icv_only}")
        print(f"  Match rate:               {matching/total_cal*100:.1f}%")
        print()

        # Variables in both (matching names)
        if matching > 0:
            print(f"✅ MATCHING VARIABLES ({matching}):")
            print("-" * 70)
            for name in sorted(cal_names & icv_names):
                cal_info = self.cal_variables[name]
                icv_info = self.icv_variables[name]
                print(f"  {name}")
                print(f"    Calibre (line {cal_info['line']}): {cal_info['definition'][:60]}")
                print(f"    ICV     (line {icv_info['line']}): {icv_info['definition'][:60]}")
            print()

        # Variables only in Calibre (missing in ICV)
        if cal_only > 0:
            print(f"⚠️  MISSING IN ICV ({cal_only}):")
            print("-" * 70)
            print("These variables are defined in Calibre but missing in ICV:")
            print()

            # Group by type
            by_type = defaultdict(list)
            for name in sorted(cal_names - icv_names):
                var_type = self.cal_variables[name]['type']
                by_type[var_type].append(name)

            for var_type, names in sorted(by_type.items()):
                print(f"  {var_type.upper()} variables ({len(names)}):")
                for name in names:
                    info = self.cal_variables[name]
                    print(f"    {name:30s} (line {info['line']:4d}): {info['definition'][:50]}")
                print()

        # Variables only in ICV (missing in Calibre)
        if icv_only > 0:
            print(f"⚠️  MISSING IN CALIBRE ({icv_only}):")
            print("-" * 70)
            print("These variables are defined in ICV but missing in Calibre:")
            print()

            # Group by type
            by_type = defaultdict(list)
            for name in sorted(icv_names - cal_names):
                var_type = self.icv_variables[name]['type']
                by_type[var_type].append(name)

            for var_type, names in sorted(by_type.items()):
                print(f"  {var_type.upper()} variables ({len(names)}):")
                for name in names:
                    info = self.icv_variables[name]
                    print(f"    {name:30s} (line {info['line']:4d}): {info['definition'][:50]}")
                print()

        # Recommendations
        print("="*70)
        print("RECOMMENDATIONS:")
        print("="*70)

        if cal_only > 0:
            print(f"\n1. Add {cal_only} missing variables to ICV file:")
            print("   - Review 'MISSING IN ICV' section above")
            print("   - Translate Calibre syntax to ICV/PXL syntax")
            print("   - Add to ICV file in appropriate location")

        if icv_only > 0:
            print(f"\n2. Review {icv_only} ICV-only variables:")
            print("   - Check if they should exist in Calibre")
            print("   - Or if they are ICV-specific optimizations")
            print("   - Document any intentional differences")

        if matching < total_cal * 0.8:
            print(f"\n3. Match rate is low ({matching/total_cal*100:.1f}%):")
            print("   - Review variable naming conventions")
            print("   - Consider renaming for consistency")
            print("   - Use this tool regularly during translation")

        print("\n" + "="*70)

        return {
            'matching': matching,
            'cal_only': cal_only,
            'icv_only': icv_only,
            'total_cal': total_cal,
            'total_icv': total_icv
        }

    def generate_sync_script(self, output_file):
        """Generate a script to add missing variables to ICV."""
        print(f"\nGenerating sync script: {output_file}")

        cal_names = set(self.cal_variables.keys())
        icv_names = set(self.icv_variables.keys())
        missing_in_icv = cal_names - icv_names

        if not missing_in_icv:
            print("  No missing variables - files are in sync!")
            return

        with open(output_file, 'w') as f:
            f.write("// AUTO-GENERATED: Missing variables to add to ICV file\n")
            f.write(f"// Generated from Calibre->ICV comparison\n")
            f.write(f"// Total missing: {len(missing_in_icv)}\n\n")

            # Group by type
            by_type = defaultdict(list)
            for name in sorted(missing_in_icv):
                var_type = self.cal_variables[name]['type']
                by_type[var_type].append(name)

            # Layers first
            if 'layer' in by_type:
                f.write("// ===== MISSING LAYER DEFINITIONS =====\n")
                for name in by_type['layer']:
                    cal_def = self.cal_variables[name]['definition']
                    # Try to convert to ICV syntax
                    match = re.match(r'LAYER\s+(\w+)\s+(\d+)\s+DATATYPE\s+(\d+)', cal_def)
                    if match:
                        layer_name = match.group(1)
                        layer_num = match.group(2)
                        datatype = match.group(3)
                        f.write(f"{layer_name} = layer({layer_num}, {datatype});\n")
                    f.write(f"// Original Calibre: {cal_def}\n\n")

            # Derived layers
            if 'derived' in by_type:
                f.write("\n// ===== MISSING DERIVED LAYERS =====\n")
                for name in by_type['derived']:
                    cal_def = self.cal_variables[name]['definition']
                    f.write(f"// TODO: Translate this to ICV syntax:\n")
                    f.write(f"// {cal_def}\n")
                    f.write(f"// {name} = ...;\n\n")

            # Checks
            if 'check' in by_type:
                f.write("\n// ===== MISSING DRC CHECKS =====\n")
                for name in by_type['check']:
                    cal_def = self.cal_variables[name]['definition']
                    f.write(f"// TODO: Translate this to ICV syntax:\n")
                    f.write(f"// {cal_def}\n")
                    f.write(f"// {name} = ...;\n")
                    f.write(f"// drc_deck({name}, \"RULE_NAME\", \"Description\");\n\n")

        print(f"  Wrote {len(missing_in_icv)} missing variables to {output_file}")
        print(f"  Review and edit before adding to your ICV file")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Compare variables between Calibre SVRF and ICV PXL files'
    )
    parser.add_argument('-c', '--calibre', required=True,
                       help='Calibre SVRF file')
    parser.add_argument('-i', '--icv', required=True,
                       help='ICV PXL file')
    parser.add_argument('-s', '--sync-script',
                       help='Generate sync script (output file)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    # Create comparator
    comp = VariableComparator()

    # Parse both files
    try:
        comp.parse_calibre(args.calibre)
        comp.parse_icv(args.icv)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing files: {e}")
        sys.exit(1)

    # Compare
    stats = comp.compare()

    # Generate sync script if requested
    if args.sync_script:
        comp.generate_sync_script(args.sync_script)

    # Exit code based on match rate
    match_rate = stats['matching'] / stats['total_cal'] if stats['total_cal'] > 0 else 0
    if match_rate < 0.8:
        print(f"\n⚠️  Warning: Low match rate ({match_rate*100:.1f}%)")
        sys.exit(1)
    elif stats['cal_only'] > 0 or stats['icv_only'] > 0:
        print(f"\n⚠️  Warning: Variables are not in sync")
        sys.exit(1)
    else:
        print(f"\n✅ Success: All variables match!")
        sys.exit(0)


if __name__ == '__main__':
    main()
```

Save this as `compare_variables.py` and make it executable:
```bash
chmod +x compare_variables.py
```

---

## Manual Comparison Strategies

### Strategy 1: Side-by-Side Diff

```bash
# Extract all variable names from Calibre
grep -E "^\s*(LAYER|[a-z_]+\s*=)" calibre.svrf | \
  sed 's/^\s*//' | cut -d' ' -f1-2 | sort > calibre_vars.txt

# Extract all variable names from ICV
grep -E "^\s*\w+\s*=" icv.rs | \
  sed 's/^\s*//' | cut -d'=' -f1 | sort | uniq > icv_vars.txt

# Compare
diff -y calibre_vars.txt icv_vars.txt
```

---

### Strategy 2: Count Variables by Type

**Calibre:**
```bash
echo "Layers: $(grep -c '^\s*LAYER' calibre.svrf)"
echo "Variables: $(grep -c '^\s*\w\+\s*=' calibre.svrf)"
echo "Rules: $(grep -c '^\s*\w\+\s*{' calibre.svrf)"
```

**ICV:**
```bash
echo "Layers: $(grep -c 'layer(' icv.rs)"
echo "Variables: $(grep -c '^\s*\w\+\s*=' icv.rs)"
echo "drc_deck calls: $(grep -c 'drc_deck(' icv.rs)"
```

---

### Strategy 3: Visual Comparison in Editor

Use VSCode or similar with split view:

1. Open both files side-by-side
2. Jump to layer definitions section
3. Compare line-by-line
4. Mark missing variables with TODO comments

---

## Matching Strategies

### Strategy A: Add All Missing Variables

**Goal:** Make ICV file contain ALL variables from Calibre

**When to use:**
- Complete translation needed
- Must match Calibre exactly
- Used for verification/comparison

**Steps:**
```bash
# 1. Run comparison
python3 compare_variables.py -c calibre.svrf -i icv.rs -s missing.rs

# 2. Review missing.rs
cat missing.rs

# 3. Manually translate and add to ICV file
# Edit icv.rs and add translated versions

# 4. Re-run comparison to verify
python3 compare_variables.py -c calibre.svrf -i icv.rs
```

---

### Strategy B: Remove Unused Variables

**Goal:** Remove variables that aren't actually used

**When to use:**
- ICV file has experimental code
- Cleaning up after failed attempts
- Optimizing for clarity

**Steps:**
```bash
# Find variables that are defined but never used
for var in $(grep '^\s*\w\+\s*=' icv.rs | cut -d'=' -f1); do
    count=$(grep -c "$var" icv.rs)
    if [ $count -eq 1 ]; then
        echo "Unused: $var"
    fi
done
```

---

### Strategy C: Rename for Consistency

**Goal:** Make variable names match between Calibre and ICV

**When to use:**
- Names differ slightly (m1_width vs M1_WIDTH)
- Establishing naming convention
- Improving readability

**Example:**
```bash
# Standardize to lowercase with underscores
# Calibre: M1_WIDTH
# ICV: change M1_WIDTH to m1_width

# Or keep Calibre convention in ICV
# Calibre: M1_WIDTH
# ICV: keep as M1_WIDTH (not m1_width)
```

---

### Strategy D: Hybrid Approach (Recommended)

**Combines all strategies:**

1. **Identify critical variables** (must match):
   - All layer definitions
   - All DRC check results
   - All variables used in drc_deck() calls

2. **Add missing critical variables** to ICV

3. **Remove unused variables** from ICV

4. **Document intentional differences:**
   ```rust
   // NOTE: calibre_specific_var intentionally not translated
   // Reason: Calibre-only DFM feature not supported in ICV
   ```

5. **Rename for consistency** where it helps

---

## Common Missing Variable Patterns

### Pattern 1: Layer Datatypes

**Problem:** Calibre has multiple datatypes, ICV missingsome

**Calibre:**
```svrf
LAYER METAL1 10                  // Base layer
LAYER METAL1_WIDE 10 DATATYPE 1  // Wide metal
LAYER METAL1_THIN 10 DATATYPE 2  // Thin metal
```

**ICV (incomplete):**
```rust
METAL1 = layer(10, 0);  // Only base layer!
```

**Solution:** Add all datatypes
```rust
METAL1 = layer(10, 0);
METAL1_WIDE = layer(10, 1);
METAL1_THIN = layer(10, 2);
```

---

### Pattern 2: Intermediate Boolean Results

**Problem:** Calibre builds up complex expressions with intermediate variables

**Calibre:**
```svrf
// Step by step
m1_via_overlap = AND METAL1 VIA1
m1_via_m2 = AND m1_via_overlap METAL2
valid_via = AND m1_via_m2 (NOT via_blockage)
```

**ICV (missing intermediates):**
```rust
// Only final result
valid_via = and(and(and(METAL1, VIA1), METAL2), not(via_blockage));
```

**Problem:** Hard to debug, doesn't match Calibre structure

**Solution:** Add intermediate variables
```rust
m1_via_overlap = and(METAL1, VIA1);
m1_via_m2 = and(m1_via_overlap, METAL2);
valid_via = and(m1_via_m2, not(via_blockage));
```

---

### Pattern 3: Size/Grow Operations

**Problem:** Calibre uses SIZE operations extensively

**Calibre:**
```svrf
metal1_grown = SIZE METAL1 BY 0.1
metal1_shrunk = SIZE METAL1 BY -0.05
metal2_overlap = AND metal1_grown METAL2
```

**ICV (missing):**
```rust
METAL1 = layer(10, 0);
METAL2 = layer(20, 0);
// Missing: metal1_grown, metal1_shrunk, metal2_overlap
```

**Solution:** Add all SIZE operations
```rust
METAL1 = layer(10, 0);
METAL2 = layer(20, 0);
metal1_grown = size(METAL1, 0.1);
metal1_shrunk = size(METAL1, -0.05);
metal2_overlap = and(metal1_grown, METAL2);
```

---

### Pattern 4: Selective Operations

**Problem:** Calibre uses SELECT, INTERACT which might be missing in ICV

**Calibre:**
```svrf
// Select small polygons
metal1_small = SELECT METAL1 BY AREA < 0.5

// Interact with another layer
poly_near_diff = INTERACT POLY DIFF
```

**ICV equivalent:**
```rust
// Need to translate to ICV operations
metal1_small = area(METAL1) < 0.5;
poly_near_diff = interact(POLY, DIFF);
```

---

### Pattern 5: Text/Label Layers

**Problem:** Text layers often missing in initial translation

**Calibre:**
```svrf
LAYER TEXT 63
LAYER METAL1_TEXT 10 TEXTTYPE 1
```

**ICV (often forgotten):**
```rust
// Missing text layers!
```

**Solution:**
```rust
TEXT = layer(63, 0);
METAL1_TEXT = layer_text(10, 1);  // or text_layer(10, 1)
```

---

## Step-by-Step Synchronization Workflow

### Step 1: Initial Comparison

```bash
# Run the comparison tool
python3 compare_variables.py \
    -c calibre_deck.svrf \
    -i icv_deck.rs \
    -s missing_vars.rs
```

**Review output:**
- How many variables match?
- How many are missing in ICV?
- How many are ICV-only?

---

### Step 2: Categorize Missing Variables

Create a spreadsheet or text file:

```
Variable Name     | Type    | Priority | Notes
------------------|---------|-----------|---------------------------------
METAL1_WIDE       | layer   | HIGH     | Used in 5 checks
metal1_grown      | derived | HIGH     | Needed for overlap checks
temp_var_123      | derived | LOW      | Debug variable, can skip
dfm_density       | check   | SKIP     | Calibre DFM feature, no ICV equivalent
```

**Priority levels:**
- **HIGH:** Must have (used in final checks)
- **MEDIUM:** Nice to have (intermediate results)
- **LOW:** Optional (debug/temporary)
- **SKIP:** Cannot or should not translate

---

### Step 3: Translate Missing Variables

For each HIGH and MEDIUM priority variable:

```bash
# 1. Find definition in Calibre
grep -n "variable_name" calibre.svrf

# 2. Understand what it does
# Read the context

# 3. Translate to ICV syntax
# See translation examples below

# 4. Add to ICV file in appropriate section
vim icv.rs
```

**Translation reference:**

| Calibre | ICV |
|---------|-----|
| `SIZE METAL1 BY 0.1` | `size(METAL1, 0.1)` |
| `AND LAYER1 LAYER2` | `and(LAYER1, LAYER2)` |
| `OR LAYER1 LAYER2` | `or(LAYER1, LAYER2)` |
| `NOT LAYER1` | `not(LAYER1)` |
| `INTERACT LAYER1 LAYER2` | `interact(LAYER1, LAYER2)` |
| `SELECT LAYER BY AREA < 0.5` | `area(LAYER) < 0.5` |
| `WIDTH LAYER < 0.09` | `width(LAYER) < 0.09` |
| `EXTERNAL LAYER < 0.10` | `external(LAYER) < 0.10` |

---

### Step 4: Add Variables to ICV File

**Organize by section:**

```rust
// ===== LAYER DEFINITIONS =====
METAL1 = layer(10, 0);
METAL1_WIDE = layer(10, 1);
METAL2 = layer(20, 0);
VIA1 = layer(30, 0);

// ===== DERIVED LAYERS (SIZING) =====
metal1_grown = size(METAL1, 0.1);
metal1_shrunk = size(METAL1, -0.05);

// ===== DERIVED LAYERS (BOOLEAN) =====
m1_via_overlap = and(METAL1, VIA1);
m1_via_m2 = and(m1_via_overlap, METAL2);
metal_any = or(METAL1, METAL2);

// ===== DRC CHECKS =====
m1_width_errors = width(METAL1) < 0.09;
drc_deck(m1_width_errors, "M1_WIDTH", "Width violation");

m1_space_errors = external(METAL1) < 0.10;
drc_deck(m1_space_errors, "M1_SPACE", "Spacing violation");
```

---

### Step 5: Re-run Comparison

```bash
# Check if we fixed everything
python3 compare_variables.py \
    -c calibre_deck.svrf \
    -i icv_deck.rs

# Expected output should show:
# - Increased match count
# - Reduced "missing in ICV" count
# - All HIGH priority variables now matching
```

---

### Step 6: Document Differences

Add comments for intentional differences:

```rust
// ===== NOTES ON CALIBRE DIFFERENCES =====
// The following Calibre variables are intentionally not translated:
// - dfm_density: Calibre-specific DFM feature
// - temp_debug_layer: Temporary Calibre debugging variable
// - antenna_check_old: Obsolete check, removed in ICV version
//
// The following ICV variables have no Calibre equivalent:
// - optimized_metal_any: ICV-specific optimization
// - polygon_density: ICV advanced feature
```

---

### Step 7: Test Both Files

```bash
# Run Calibre
calibre -drc calibre_deck.svrf -layout test.gds

# Run ICV
icv -i icv_deck.rs -design test.gds

# Compare results
python3 compare_drc_results.py -c calibre.rpt -i icv.log -v
```

If results differ, check if missing variables are the cause.

---

## Best Practices

### 1. Keep Variable Names Consistent

✅ **Good:**
```svrf
// Calibre
METAL1 = ...
m1_width_errors = ...
```
```rust
// ICV - same names!
METAL1 = layer(10, 0);
m1_width_errors = width(METAL1) < 0.09;
```

❌ **Bad:**
```svrf
// Calibre
METAL1 = ...
m1_width_errors = ...
```
```rust
// ICV - different names!
metal1 = layer(10, 0);  // lowercase!
metal1_w_err = width(metal1) < 0.09;  // abbreviated!
```

---

### 2. Use Comments to Mark Correspondence

```rust
// From Calibre rule: M1_WIDTH (line 145)
m1_width_errors = width(METAL1) < 0.09;
drc_deck(m1_width_errors, "M1_WIDTH", "Calibre rule M1_WIDTH");
```

---

### 3. Run Comparison Regularly

```bash
# Add to your workflow:
make compare:
    @python3 compare_variables.py -c calibre.svrf -i icv.rs
    @echo "Check complete!"

# Run it frequently:
make compare
```

---

### 4. Version Control Both Files Together

```bash
# Commit both files together
git add calibre_deck.svrf icv_deck.rs
git commit -m "Add METAL3 layer to both Calibre and ICV decks"
```

This ensures they stay in sync.

---

### 5. Use Naming Conventions

**Establish conventions like:**
- Layers: `UPPERCASE` (METAL1, VIA1)
- Derived layers: `lowercase_with_underscores` (metal1_grown, m1_via_overlap)
- Check results: `*_errors` or `*_violations` (m1_width_errors, m1_space_violations)
- Temporary: `temp_*` (temp_debug, temp_test)

---

### 6. Create a Variable Map Document

```markdown
# Variable Mapping: Calibre ↔ ICV

## Layers
| Calibre | ICV | Notes |
|---------|-----|-------|
| METAL1 | METAL1 | Exact match |
| M1_TXT | METAL1_TEXT | Name differs |

## Derived Layers
| Calibre | ICV | Notes |
|---------|-----|-------|
| metal1_big | metal1_grown | Different names, same operation |
| dfm_var | (none) | Calibre-only DFM feature |

## Checks
| Calibre | ICV | Notes |
|---------|-----|-------|
| M1_WIDTH_CHK | m1_width_errors | Name differs |
```

---

### 7. Automate with Makefiles

```makefile
# Makefile for keeping Calibre and ICV in sync

.PHONY: compare sync test all

compare:
	@echo "Comparing Calibre and ICV variables..."
	@python3 compare_variables.py -c calibre.svrf -i icv.rs

sync:
	@echo "Generating sync script..."
	@python3 compare_variables.py -c calibre.svrf -i icv.rs -s missing_vars.rs
	@echo "Review missing_vars.rs and add to icv.rs manually"

test:
	@echo "Running both tools..."
	@calibre -drc calibre.svrf -layout test.gds
	@icv -i icv.rs -design test.gds
	@python3 compare_drc_results.py -c calibre.rpt -i icv.log

all: compare sync test
```

---

## Complete Example

### Before Synchronization

**Calibre (`before.svrf`):**
```svrf
LAYER METAL1 10
LAYER METAL2 20
LAYER VIA1 30

metal1_grown = SIZE METAL1 BY 0.05
m1_via_overlap = AND METAL1 VIA1
m1_via_m2 = AND m1_via_overlap METAL2

M1_WIDTH { WIDTH METAL1 < 0.09 }
M1_SPACE { EXTERNAL METAL1 < 0.10 }
VIA_CHECK {
    via_bad = NOT m1_via_m2
}
```

**ICV (`before.rs`):**
```rust
// Missing METAL2, VIA1
METAL1 = layer(10, 0);

// Missing all derived layers!

// Only one check
m1_width_errors = width(METAL1) < 0.09;
drc_deck(m1_width_errors, "M1_WIDTH", "Width violation");
```

### Run Comparison

```bash
$ python3 compare_variables.py -c before.svrf -i before.rs

SUMMARY:
  Calibre variables:        8
  ICV variables:            2
  Matching (same name):     1
  Calibre-only:             7
  ICV-only:                 1
  Match rate:               12.5%

⚠️ MISSING IN ICV (7):
  LAYER variables (2):
    METAL2                         (line   2): LAYER METAL2 20 DATATYPE 0
    VIA1                           (line   3): LAYER VIA1 30 DATATYPE 0

  DERIVED variables (3):
    metal1_grown                   (line   5): metal1_grown = SIZE METAL1 BY 0.05
    m1_via_overlap                 (line   6): m1_via_overlap = AND METAL1 VIA1
    m1_via_m2                      (line   7): m1_via_m2 = AND m1_via_overlap METAL2

  CHECK variables (2):
    M1_SPACE                       (line   10): EXTERNAL METAL1 < 0.10
    via_bad                        (line   12): via_bad = NOT m1_via_m2
```

### After Synchronization

**ICV (`after.rs`):**
```rust
// ===== LAYER DEFINITIONS =====
METAL1 = layer(10, 0);
METAL2 = layer(20, 0);  // ADDED
VIA1 = layer(30, 0);    // ADDED

// ===== DERIVED LAYERS =====
metal1_grown = size(METAL1, 0.05);             // ADDED
m1_via_overlap = and(METAL1, VIA1);            // ADDED
m1_via_m2 = and(m1_via_overlap, METAL2);       // ADDED

// ===== DRC CHECKS =====
m1_width_errors = width(METAL1) < 0.09;
drc_deck(m1_width_errors, "M1_WIDTH", "Width violation");

m1_space_errors = external(METAL1) < 0.10;     // ADDED
drc_deck(m1_space_errors, "M1_SPACE", "Spacing violation");

via_bad = not(m1_via_m2);                      // ADDED
drc_deck(via_bad, "VIA_CHECK", "Via structure violation");
```

### Verify Synchronization

```bash
$ python3 compare_variables.py -c before.svrf -i after.rs

SUMMARY:
  Calibre variables:        8
  ICV variables:            8
  Matching (same name):     8
  Calibre-only:             0
  ICV-only:                 0
  Match rate:               100.0%

✅ Success: All variables match!
```

---

## Summary

To match variables between Calibre and ICV pairs:

1. **Use the comparison tool** to identify mismatches
2. **Categorize missing variables** by priority
3. **Translate high-priority variables** from SVRF to PXL
4. **Add to ICV file** in organized sections
5. **Re-run comparison** to verify
6. **Document intentional differences**
7. **Test both tools** to ensure results match

**Key tools:**
- `compare_variables.py` - Automated comparison
- `grep`/`diff` - Manual comparison
- Variable mapping document
- Regular testing workflow

**Success criteria:**
- All critical variables (layers, checks) match
- Match rate > 80%
- Results from both tools are equivalent
- Differences are documented

---

**Ready to synchronize your Calibre and ICV files!** 🎯
