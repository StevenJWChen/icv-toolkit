# Semantic Variable Mapping Between Calibre and ICV

Understanding and documenting the complex relationships between Calibre SVRF and ICV PXL variables, where one variable may represent many, or many may consolidate into one.

---

## Table of Contents

1. [The Semantic Mapping Problem](#the-semantic-mapping-problem)
2. [Types of Variable Relationships](#types-of-variable-relationships)
3. [Mapping Patterns](#mapping-patterns)
4. [Creating a Variable Mapping Document](#creating-a-variable-mapping-document)
5. [Automated Semantic Analysis](#automated-semantic-analysis)
6. [Real-World Examples](#real-world-examples)
7. [Best Practices](#best-practices)

---

## The Semantic Mapping Problem

### Not All Variables Match 1:1

**Common misconception:**
> "If Calibre has 50 variables, ICV should also have 50 variables"

**Reality:**
> Variables represent **concepts**, not just names. The same concept can be represented differently in each tool.

### Three Key Insights

1. **Consolidation** - Multiple Calibre variables → Single ICV variable
2. **Decomposition** - Single Calibre variable → Multiple ICV variables
3. **Equivalence** - Different names/implementations, same meaning

---

## Types of Variable Relationships

### Relationship 1: One-to-One (1:1)

**Most straightforward** - Direct name and concept match

**Example:**
```svrf
// Calibre
LAYER METAL1 10
```
```rust
// ICV
METAL1 = layer(10, 0);
```

**Mapping:**
```
Calibre: METAL1  <-->  ICV: METAL1
```

**Status:** ✅ Perfect match

---

### Relationship 2: Many-to-One (N:1) - Consolidation

**Multiple Calibre variables represented by one ICV variable**

**Example 1: Layer Datatypes**
```svrf
// Calibre - Separate variables for each width class
LAYER METAL1 10                  // Base
LAYER METAL1_WIDE 10 DATATYPE 1  // Wide metal
LAYER METAL1_NARROW 10 DATATYPE 2 // Narrow metal

// Used separately
wide_check = WIDTH METAL1_WIDE < 0.20
narrow_check = WIDTH METAL1_NARROW < 0.09
```

```rust
// ICV - One variable with conditions
METAL1 = layer(10, 0);

// Distinguish by width in checks
wide_metal = width(METAL1) >= 0.20;
narrow_metal = width(METAL1) < 0.20;
wide_check = width(wide_metal) < 0.20;
narrow_check = width(narrow_metal) < 0.09;
```

**Mapping:**
```
Calibre: METAL1_WIDE    ┐
Calibre: METAL1_NARROW  ├──>  ICV: METAL1 (with width conditions)
Calibre: METAL1         ┘
```

**Reason:** ICV uses filtering instead of separate layers

---

**Example 2: Boolean Intermediates**
```svrf
// Calibre - Multiple intermediate steps
step1 = AND METAL1 VIA1
step2 = AND step1 METAL2
step3 = AND step2 (NOT blockage)
final_result = step3
```

```rust
// ICV - Direct expression (consolidated)
final_result = and(and(and(METAL1, VIA1), METAL2), not(blockage));
```

**Mapping:**
```
Calibre: step1  ┐
Calibre: step2  ├──>  ICV: final_result (all-in-one)
Calibre: step3  │
Calibre: final_result ┘
```

**Reason:** ICV encourages compact expressions

---

### Relationship 3: One-to-Many (1:N) - Decomposition

**Single Calibre variable split into multiple ICV variables**

**Example 1: Error Aggregation**
```svrf
// Calibre - One variable for all violations
all_metal1_errors = OR m1_width_errors m1_space_errors m1_enc_errors
```

```rust
// ICV - Separate reporting for each type
m1_width_errors = width(METAL1) < 0.09;
drc_deck(m1_width_errors, "M1_WIDTH", "Width violation");

m1_space_errors = external(METAL1) < 0.10;
drc_deck(m1_space_errors, "M1_SPACE", "Spacing violation");

m1_enc_errors = enclosure(CONTACT, METAL1) < 0.05;
drc_deck(m1_enc_errors, "M1_ENC", "Enclosure violation");

// Note: all_metal1_errors doesn't exist as single variable
```

**Mapping:**
```
                           ┌──> ICV: m1_width_errors
Calibre: all_metal1_errors ├──> ICV: m1_space_errors
                           └──> ICV: m1_enc_errors
```

**Reason:** ICV best practice is separate drc_deck() calls

---

**Example 2: Density Regions**
```svrf
// Calibre - Single density variable
metal_density = DENSITY METAL1 WINDOW 100 100
```

```rust
// ICV - Separate variables for over/under density
metal_density_map = density(METAL1, window_size=100);
over_density = metal_density_map > 0.80;
under_density = metal_density_map < 0.20;

drc_deck(over_density, "METAL_DENSITY_HIGH", "Density > 80%");
drc_deck(under_density, "METAL_DENSITY_LOW", "Density < 20%");
```

**Mapping:**
```
                           ┌──> ICV: metal_density_map
Calibre: metal_density ────┼──> ICV: over_density
                           └──> ICV: under_density
```

**Reason:** ICV separates calculation from checking

---

### Relationship 4: Semantic Equivalence (Different Names/Approaches)

**Same concept, completely different implementation**

**Example 1: Via Checking**
```svrf
// Calibre - Uses CONNECT
CONNECT M1 BY VIA1 TO M2
bad_vias = SINGLECON VIA1 M1 M2
```

```rust
// ICV - Uses Boolean operations
via_on_m1 = and(VIA1, METAL1);
via_on_m2 = and(VIA1, METAL2);
via_complete = and(via_on_m1, via_on_m2);
bad_vias = not(via_complete);
```

**Mapping:**
```
Calibre: (CONNECT concept)  <≈≈>  ICV: via_complete (Boolean approach)
Calibre: bad_vias           <≈≈>  ICV: bad_vias (same name, different method)
```

**Reason:** Tools use different paradigms for connectivity

---

**Example 2: Antenna Rules**
```svrf
// Calibre - Built-in antenna check
antenna_violations = ANTENNA METAL1 GATE_LAYER RATIO 400
```

```rust
// ICV - Manual calculation
gate_area = area(GATE_LAYER);
metal1_area = area(METAL1);
antenna_ratio = metal1_area / gate_area;
antenna_violations = antenna_ratio > 400;
```

**Mapping:**
```
Calibre: antenna_violations  <≈≈>  ICV: antenna_violations (different calculation)
Calibre: (implicit ratio)    <≈≈>  ICV: antenna_ratio (explicit variable)
```

**Reason:** Different built-in functions available

---

## Mapping Patterns

### Pattern 1: Layer Consolidation

**Calibre approach:** Separate layers for variants
```svrf
LAYER METAL1_MIN 10 DATATYPE 0
LAYER METAL1_TYP 10 DATATYPE 1
LAYER METAL1_MAX 10 DATATYPE 2

min_width = WIDTH METAL1_MIN < 0.08
typ_width = WIDTH METAL1_TYP < 0.09
max_width = WIDTH METAL1_MAX < 0.10
```

**ICV approach:** One layer with conditions
```rust
METAL1 = layer(10, 0);  // All variants on this layer

// Filter by context or width
metal1_min = /* context-specific filtering */;
metal1_typ = /* context-specific filtering */;
metal1_max = /* context-specific filtering */;

min_width = width(metal1_min) < 0.08;
typ_width = width(metal1_typ) < 0.09;
max_width = width(metal1_max) < 0.10;
```

**Mapping document:**
```yaml
pattern: layer_consolidation
calibre_vars: [METAL1_MIN, METAL1_TYP, METAL1_MAX]
icv_vars: [METAL1]
relationship: N:1
note: "ICV uses single layer with filtering"
```

---

### Pattern 2: Check Decomposition

**Calibre approach:** Aggregate violations
```svrf
// All violations together
all_violations = OR width_err space_err enc_err
```

**ICV approach:** Separate reporting
```rust
// Each reported separately
drc_deck(width_err, "WIDTH", "...");
drc_deck(space_err, "SPACE", "...");
drc_deck(enc_err, "ENC", "...");
// No "all_violations" variable
```

**Mapping document:**
```yaml
pattern: check_decomposition
calibre_vars: [all_violations]
icv_vars: [width_err, space_err, enc_err]
relationship: 1:N
note: "ICV reports each error type separately"
```

---

### Pattern 3: Intermediate Elimination

**Calibre approach:** Step-by-step construction
```svrf
temp1 = SIZE METAL1 BY 0.1
temp2 = AND temp1 VIA1
temp3 = AND temp2 METAL2
final = temp3
```

**ICV approach:** Direct expression
```rust
final = and(and(size(METAL1, 0.1), VIA1), METAL2);
// temp1, temp2, temp3 don't exist
```

**Mapping document:**
```yaml
pattern: intermediate_elimination
calibre_vars: [temp1, temp2, temp3, final]
icv_vars: [final]
relationship: N:1
note: "ICV eliminates intermediate variables"
```

---

### Pattern 4: Explicit vs Implicit

**Calibre approach:** Implicit intermediate calculations
```svrf
// ANTENNA command implicitly calculates areas and ratios
violations = ANTENNA METAL GATE RATIO 400
```

**ICV approach:** Explicit calculations
```rust
// Everything explicit
metal_area = area(METAL);
gate_area = area(GATE);
antenna_ratio = metal_area / gate_area;
violations = antenna_ratio > 400;
```

**Mapping document:**
```yaml
pattern: explicit_vs_implicit
calibre_vars: [violations]  # implicit: ratio calculation
icv_vars: [metal_area, gate_area, antenna_ratio, violations]
relationship: 1:N
note: "ICV makes implicit calculations explicit"
```

---

## Creating a Variable Mapping Document

### Template: Variable Mapping Table

Create `VARIABLE_MAPPING.md` for your project:

```markdown
# Variable Mapping: Calibre ↔ ICV

## 1:1 Mappings (Direct correspondence)

| Calibre Variable | ICV Variable | Type | Notes |
|------------------|--------------|------|-------|
| METAL1 | METAL1 | layer | Exact match |
| METAL2 | METAL2 | layer | Exact match |
| m1_width_errors | m1_width_errors | check | Same name, same meaning |

## N:1 Mappings (Many Calibre → One ICV)

### Group: Metal1 Variants
| Calibre Variables | ICV Variable | Reason |
|-------------------|--------------|--------|
| METAL1_WIDE (10,1) | METAL1 | ICV uses width filtering |
| METAL1_NARROW (10,2) | METAL1 | instead of separate layers |
| METAL1_BASE (10,0) | METAL1 | |

**ICV Implementation:**
```rust
METAL1 = layer(10, 0);
wide_metal = width(METAL1) >= 0.20;
narrow_metal = width(METAL1) < 0.20;
```

### Group: Boolean Intermediates
| Calibre Variables | ICV Variable | Reason |
|-------------------|--------------|--------|
| via_step1 | via_complete | Consolidated into |
| via_step2 | via_complete | single expression |
| via_step3 | via_complete | |

**ICV Implementation:**
```rust
via_complete = and(and(METAL1, VIA1), METAL2);
```

## 1:N Mappings (One Calibre → Many ICV)

### Group: Error Reporting
| Calibre Variable | ICV Variables | Reason |
|------------------|---------------|--------|
| all_m1_errors | m1_width_errors | ICV reports each |
| | m1_space_errors | error type |
| | m1_enc_errors | separately |

**Calibre:**
```svrf
all_m1_errors = OR width_err space_err enc_err
```

**ICV:**
```rust
drc_deck(m1_width_errors, "M1_WIDTH", "...");
drc_deck(m1_space_errors, "M1_SPACE", "...");
drc_deck(m1_enc_errors, "M1_ENC", "...");
```

## Semantic Equivalents (Different implementation)

| Calibre Variable | ICV Variable(s) | Difference |
|------------------|-----------------|------------|
| antenna_violations | antenna_ratio, violations | ICV explicit calculation |
| connected_vias | via_complete | Different method (CONNECT vs Boolean) |

## Calibre-Only Variables (No ICV equivalent)

| Calibre Variable | Reason Not In ICV |
|------------------|-------------------|
| dfm_density_var | Calibre-specific DFM feature |
| debug_temp_123 | Temporary debug variable |

## ICV-Only Variables (No Calibre equivalent)

| ICV Variable | Reason Not In Calibre |
|--------------|------------------------|
| optimized_metal | ICV-specific optimization |
| cached_result | ICV performance optimization |

## Statistics

- Total Calibre variables: 50
- Total ICV variables: 42
- Direct 1:1 mappings: 25
- N:1 consolidations: 15 → 8
- 1:N decompositions: 5 → 12
- Semantic equivalents: 5 ↔ 7
- Calibre-only: 5
- ICV-only: 3

## Match Rate Calculation

**Simple name matching:** 25/50 = 50% ❌ Misleading!

**Semantic matching:**
- Mapped: 25 (1:1) + 15 (N:1) + 5 (1:N) + 5 (equiv) = 50
- Coverage: 50/50 = 100% ✅ Accurate!
```

---

## Automated Semantic Analysis

### Enhanced Comparison Script

Create `semantic_compare.py`:

```python
#!/usr/bin/env python3
"""
Semantic variable comparison with relationship mapping.
"""

import re
from collections import defaultdict

class SemanticComparator:
    def __init__(self):
        self.cal_vars = {}
        self.icv_vars = {}
        self.mappings = {
            'one_to_one': [],      # Direct matches
            'many_to_one': [],     # N Calibre → 1 ICV
            'one_to_many': [],     # 1 Calibre → N ICV
            'semantic_equiv': [],   # Different but equivalent
            'cal_only': [],        # No ICV equivalent
            'icv_only': []         # No Calibre equivalent
        }

    def analyze_relationships(self):
        """Analyze semantic relationships between variables."""

        # 1. Find direct name matches (1:1)
        cal_names = set(self.cal_vars.keys())
        icv_names = set(self.icv_vars.keys())
        direct_matches = cal_names & icv_names

        for name in direct_matches:
            self.mappings['one_to_one'].append({
                'calibre': [name],
                'icv': [name],
                'type': '1:1'
            })

        # 2. Find layer consolidations (N:1)
        # Look for patterns like METAL1, METAL1_WIDE, METAL1_NARROW → METAL1
        layer_groups = defaultdict(list)
        for cal_var in self.cal_vars:
            # Extract base name (before underscore)
            base = cal_var.split('_')[0]
            layer_groups[base].append(cal_var)

        for base, cal_vars in layer_groups.items():
            if len(cal_vars) > 1 and base in icv_names:
                self.mappings['many_to_one'].append({
                    'calibre': cal_vars,
                    'icv': [base],
                    'type': 'N:1',
                    'pattern': 'layer_consolidation'
                })

        # 3. Find intermediate eliminations (N:1)
        # Look for patterns like temp1, temp2, temp3 → final
        # (requires dependency analysis)

        # 4. Find error decompositions (1:N)
        # Look for aggregate errors split into specific types
        # Pattern: all_*_errors → [width_errors, space_errors, ...]

        # 5. Identify semantic equivalents
        # (requires manual specification or AI analysis)

        return self.mappings

    def generate_mapping_document(self, output_file):
        """Generate markdown documentation of mappings."""
        with open(output_file, 'w') as f:
            f.write("# Variable Mapping: Calibre ↔ ICV\n\n")

            # Statistics
            f.write("## Statistics\n\n")
            f.write(f"- Total Calibre variables: {len(self.cal_vars)}\n")
            f.write(f"- Total ICV variables: {len(self.icv_vars)}\n")
            f.write(f"- 1:1 mappings: {len(self.mappings['one_to_one'])}\n")
            f.write(f"- N:1 consolidations: {len(self.mappings['many_to_one'])}\n")
            f.write(f"- 1:N decompositions: {len(self.mappings['one_to_many'])}\n")
            f.write("\n")

            # 1:1 Mappings
            f.write("## 1:1 Mappings\n\n")
            f.write("| Calibre | ICV | Type |\n")
            f.write("|---------|-----|------|\n")
            for mapping in self.mappings['one_to_one']:
                cal = mapping['calibre'][0]
                icv = mapping['icv'][0]
                var_type = self.cal_vars[cal].get('type', 'unknown')
                f.write(f"| {cal} | {icv} | {var_type} |\n")
            f.write("\n")

            # N:1 Mappings
            if self.mappings['many_to_one']:
                f.write("## N:1 Consolidations\n\n")
                for mapping in self.mappings['many_to_one']:
                    cal_vars = ', '.join(mapping['calibre'])
                    icv_var = mapping['icv'][0]
                    pattern = mapping.get('pattern', 'unknown')
                    f.write(f"### {icv_var}\n")
                    f.write(f"**Calibre:** {cal_vars}\n")
                    f.write(f"**ICV:** {icv_var}\n")
                    f.write(f"**Pattern:** {pattern}\n\n")

        print(f"Generated mapping document: {output_file}")

# Usage would be similar to compare_variables.py
# but with semantic analysis
```

---

## Real-World Examples

### Example 1: Metal Stack with Width Classes

**Calibre:** Separate layers for each width class
```svrf
// Physical layout has all on layer 10
// But designer uses datatypes to mark width class
LAYER M1_WIDE 10 DATATYPE 10    // Wide traces (>0.5um)
LAYER M1_STD 10 DATATYPE 0      // Standard (0.1-0.5um)
LAYER M1_THIN 10 DATATYPE 20    // Thin (<0.1um)

// Different rules for each
M1_WIDE_RULES {
    WIDTH M1_WIDE < 0.50
    SPACE M1_WIDE < 0.50
}

M1_STD_RULES {
    WIDTH M1_STD < 0.10
    SPACE M1_STD < 0.12
}

M1_THIN_RULES {
    WIDTH M1_THIN < 0.07
    SPACE M1_THIN < 0.08
}
```

**ICV:** One layer, classify by measured width
```rust
// Single layer definition
M1 = layer(10, 0);  // Get all metal1 regardless of datatype

// Classify by actual measured width
m1_wide_shapes = width(M1) >= 0.50;
m1_std_shapes = (width(M1) >= 0.10) and (width(M1) < 0.50);
m1_thin_shapes = width(M1) < 0.10;

// Apply appropriate rules
m1_wide_width_err = width(m1_wide_shapes) < 0.50;
drc_deck(m1_wide_width_err, "M1_WIDE_WIDTH", "Wide metal width < 0.50");

m1_std_width_err = width(m1_std_shapes) < 0.10;
drc_deck(m1_std_width_err, "M1_STD_WIDTH", "Std metal width < 0.10");

m1_thin_width_err = width(m1_thin_shapes) < 0.07;
drc_deck(m1_thin_width_err, "M1_THIN_WIDTH", "Thin metal width < 0.07");
```

**Mapping:**
```yaml
M1_WIDE (Calibre)  ┐
M1_STD (Calibre)   ├──> M1 (ICV) + width classification
M1_THIN (Calibre)  ┘

Relationship: 3:1 (N:1)
Reason: ICV dynamically classifies by measured width
```

---

### Example 2: Via Connectivity Check

**Calibre:** Built-in CONNECT paradigm
```svrf
// Define connectivity
CONNECT M1 BY VIA1 TO M2
CONNECT M2 BY VIA2 TO M3

// Find floating vias (not properly connected)
floating_via1 = SINGLECON VIA1 M1 M2
floating_via2 = SINGLECON VIA2 M2 M3

// Aggregate
all_bad_vias = OR floating_via1 floating_via2
```

**ICV:** Boolean approach (no CONNECT equivalent)
```rust
// Metal layers
M1 = layer(10, 0);
M2 = layer(20, 0);
M3 = layer(30, 0);
VIA1 = layer(15, 0);
VIA2 = layer(25, 0);

// VIA1 connectivity
via1_on_m1 = and(VIA1, M1);
via1_on_m2 = and(VIA1, M2);
via1_connected = and(via1_on_m1, via1_on_m2);
floating_via1 = not(via1_connected);

// VIA2 connectivity
via2_on_m2 = and(VIA2, M2);
via2_on_m3 = and(VIA2, M3);
via2_connected = and(via2_on_m2, via2_on_m3);
floating_via2 = not(via2_connected);

// Report
drc_deck(floating_via1, "VIA1_FLOAT", "VIA1 not connected");
drc_deck(floating_via2, "VIA2_FLOAT", "VIA2 not connected");
```

**Mapping:**
```yaml
Calibre:
  - CONNECT (concept, not a variable)
  - floating_via1
  - floating_via2
  - all_bad_vias

ICV:
  - via1_on_m1, via1_on_m2, via1_connected (intermediates)
  - via2_on_m2, via2_on_m3, via2_connected (intermediates)
  - floating_via1
  - floating_via2
  - (no all_bad_vias aggregate)

Relationship: Semantic equivalence with decomposition
Calibre: 3 variables (implicit connectivity)
ICV: 8 variables (explicit Boolean logic)
```

---

### Example 3: Density Checking

**Calibre:** Single density variable
```svrf
// Calculate density in 100x100um windows
m1_density = DENSITY METAL1 WINDOW 100 100

// Check both over and under density
DENSITY_ERRORS {
    over_dense = m1_density > 0.80
    under_dense = m1_density < 0.20
}
```

**ICV:** Separate variables for analysis and checking
```rust
// Density calculation
m1_density_map = density(METAL1, window_size=100);

// Separate over/under checks
over_dense_regions = m1_density_map > 0.80;
under_dense_regions = m1_density_map < 0.20;

// Report separately
drc_deck(over_dense_regions, "M1_DENSITY_HIGH", "Density > 80%");
drc_deck(under_dense_regions, "M1_DENSITY_LOW", "Density < 20%");

// Optional: combined for analysis
density_violations = or(over_dense_regions, under_dense_regions);
```

**Mapping:**
```yaml
Calibre:
  - m1_density (1 variable, both calculations)
  - over_dense (within rule block)
  - under_dense (within rule block)

ICV:
  - m1_density_map (explicit calculation)
  - over_dense_regions (separate check)
  - under_dense_regions (separate check)
  - density_violations (optional aggregate)

Relationship: 1:N decomposition
Calibre: 1 density variable used for multiple checks
ICV: 3-4 variables (calculation + separate checks)
```

---

## Best Practices

### 1. Create Mapping Documentation Early

**Start mapping from day 1:**
```bash
# Create mapping doc
touch VARIABLE_MAPPING.md

# Document as you translate
# Don't wait until the end!
```

**Template for each mapping:**
```markdown
### Variable Group: [Name]

**Calibre (N variables):**
- var1: description
- var2: description

**ICV (M variables):**
- var_a: description
- var_b: description

**Relationship:** N:M

**Reason for difference:**
[Explain why the mapping is not 1:1]

**Code example:**
[Show both implementations side-by-side]
```

---

### 2. Use Consistent Commenting

**In Calibre file:**
```svrf
// ICV equivalent: M1 with width filtering
LAYER M1_WIDE 10 DATATYPE 1
LAYER M1_STD 10 DATATYPE 0
```

**In ICV file:**
```rust
// Calibre equivalent: M1_WIDE, M1_STD (separate layers)
M1 = layer(10, 0);
m1_wide = width(M1) >= 0.20;
m1_std = width(M1) < 0.20;
```

---

### 3. Track Semantic Equivalence, Not Just Names

**DON'T just count matching names:**
```
❌ Match rate: 25/50 = 50%
```

**DO track semantic coverage:**
```
✅ Coverage: 50/50 concepts mapped = 100%
   - 25 direct (1:1)
   - 15 consolidated (N:1)
   - 5 decomposed (1:N)
   - 5 equivalent (different approach)
```

---

### 4. Validate Functionally, Not Textually

**Don't rely on variable counts:**
```bash
# This is meaningless:
❌ grep -c "=" calibre.svrf  # 50 variables
❌ grep -c "=" icv.rs        # 42 variables
❌ Conclusion: Missing 8 variables!  # WRONG!
```

**DO validate with actual results:**
```bash
# This matters:
✅ Run both tools on same layout
✅ Compare DRC results
✅ If results match → mapping is correct
```

---

### 5. Use Intermediate Variables Wisely

**Calibre style (many intermediates):**
```svrf
step1 = AND M1 VIA1
step2 = AND step1 M2
step3 = NOT step2
final = step3
```

**ICV option 1 (compact):**
```rust
final = not(and(and(M1, VIA1), M2));
```

**ICV option 2 (explicit, RECOMMENDED for mapping):**
```rust
// Keep intermediates to match Calibre structure
step1 = and(M1, VIA1);
step2 = and(step1, M2);
step3 = not(step2);
final = step3;
```

**Why keep intermediates?**
- Easier to debug
- Clearer mapping to Calibre
- Simpler verification
- Better documentation

---

### 6. Document Tool-Specific Differences

**Create TOOL_DIFFERENCES.md:**
```markdown
# Calibre vs ICV Implementation Differences

## Connectivity
- **Calibre:** CONNECT keyword defines layer connectivity
- **ICV:** Manual Boolean operations for connectivity
- **Impact:** More variables in ICV implementation

## Density
- **Calibre:** DENSITY returns single map
- **ICV:** Separate density() and threshold checks
- **Impact:** 2-3x more variables in ICV

## Antenna
- **Calibre:** ANTENNA built-in with implicit calculations
- **ICV:** Manual area calculations and ratio checks
- **Impact:** ICV makes implicit steps explicit
```

---

## Summary

### Key Takeaways

1. **Don't expect 1:1 variable matching**
   - Different tools, different approaches
   - Same functionality ≠ same variable count

2. **Three main relationship types:**
   - **N:1 Consolidation** - Multiple Calibre → Single ICV
   - **1:N Decomposition** - Single Calibre → Multiple ICV
   - **Semantic Equivalence** - Different implementation, same result

3. **Documentation is critical:**
   - Create `VARIABLE_MAPPING.md`
   - Track relationships, not just names
   - Comment both files with cross-references

4. **Validation is functional:**
   - Run both tools
   - Compare results
   - Matching results = correct mapping

5. **When in doubt, be explicit:**
   - Keep intermediate variables in ICV
   - Makes mapping clearer
   - Easier to verify
   - Simpler to debug

---

## Quick Reference

### Mapping Checklist

- [ ] Create `VARIABLE_MAPPING.md` document
- [ ] Identify direct 1:1 matches
- [ ] Find N:1 consolidations (especially layers)
- [ ] Find 1:N decompositions (especially checks)
- [ ] Document semantic equivalents
- [ ] Mark Calibre-only variables (with reasons)
- [ ] Mark ICV-only variables (with reasons)
- [ ] Add cross-reference comments in both files
- [ ] Calculate semantic coverage (not just name matching)
- [ ] Validate with functional testing

### When Variables Don't Match

**Ask these questions:**

1. **Is one variable representing many?**
   - Look for consolidation patterns
   - Check if ICV uses filtering instead of separate layers

2. **Is one variable split into many?**
   - Look for decomposition patterns
   - Check if ICV reports separately what Calibre aggregates

3. **Are they semantically equivalent?**
   - Compare what the variables represent
   - Check if functionality is the same despite different names/methods

4. **Is it tool-specific?**
   - Some features don't translate
   - Document as Calibre-only or ICV-only

5. **Can I keep intermediates for clarity?**
   - Consider matching Calibre's structure in ICV
   - Helps with verification and debugging

---

**Remember:** The goal is not identical variable lists, but equivalent functionality!** ✅

