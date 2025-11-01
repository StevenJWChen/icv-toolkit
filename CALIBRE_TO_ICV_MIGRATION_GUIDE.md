# Best Methods to Translate Calibre DRC Deck to IC Validator

## Overview

There are **three main methods** to translate Calibre (SVRF/TVF) rule decks to IC Validator (PXL):

1. **Automated Translation with cal2pxl** (Recommended for most cases)
2. **Manual Conversion** (For complex/custom rules)
3. **Hybrid Approach** (Automated + manual refinement)

---

## Method 1: Automated Translation with cal2pxl ⭐ RECOMMENDED

### What is cal2pxl?

**cal2pxl** is Synopsys's official translation utility that converts:
- Calibre SVRF (Standard Verification Rule Format) → IC Validator PXL
- Calibre TVF (TCL Verification Format) → IC Validator PXL
- Both DRC and LVS rule decks

### Location

```bash
$ICV_HOME_DIR/contrib/cal2pxl/
```

Example paths:
```
/tools/synopsys/icv/S-2021.06/contrib/cal2pxl/
/opt/synopsys/icv/R-2020.09/contrib/cal2pxl/
```

### Basic Usage

```bash
# Navigate to cal2pxl directory
cd $ICV_HOME_DIR/contrib/cal2pxl

# Basic conversion
./cal2pxl -i <calibre_deck.svrf> -o <output_deck.rs>

# With layer mapping file
./cal2pxl -i <calibre_deck.svrf> -o <output_deck.rs> -l <layermap.txt>
```

### Common Options (typical usage)

```bash
cal2pxl \
    -i input_calibre_deck.svrf \      # Input Calibre SVRF file
    -o output_icv_deck.rs \            # Output ICV PXL file
    -l layermap.txt \                  # Layer mapping file
    -log conversion.log \              # Conversion log file
    -verbose                           # Detailed output
```

### Conversion Workflow

```
Step 1: Prepare Calibre Rule Deck
├── Collect all SVRF/TVF files
├── Note all INCLUDE files
└── Document layer definitions

Step 2: Run cal2pxl
├── Execute translation
├── Review conversion log
└── Check for warnings/errors

Step 3: Validate Converted Deck
├── Run simple test case
├── Compare results with Calibre
└── Debug any discrepancies

Step 4: Optimize (if needed)
├── Refine PXL code
├── Add comments
└── Update for ICV best practices
```

### Pros of cal2pxl

✅ **Fast** - Automated conversion saves time
✅ **Comprehensive** - Handles most SVRF constructs
✅ **Official** - Supported by Synopsys
✅ **Consistent** - Produces uniform PXL code
✅ **Batch processing** - Can convert multiple decks

### Cons of cal2pxl

❌ **Not 100% accurate** - Complex rules may need manual adjustment
❌ **Limited optimization** - Generated PXL may not be optimal
❌ **Custom macros** - Proprietary Calibre extensions may not convert
❌ **Requires validation** - Must verify results match Calibre

---

## Method 2: Manual Conversion

### When to Use Manual Conversion

- Very simple rule decks (< 50 rules)
- Highly customized Calibre rules
- cal2pxl fails or produces incorrect results
- Need to optimize for ICV performance
- Learning PXL language

### SVRF to PXL Translation Examples

#### Example 1: Width Check

**Calibre SVRF:**
```svrf
LAYER METAL1 10
M1_WIDTH { @ Minimum width = 0.09um
    WIDTH METAL1 < 0.09
}
```

**IC Validator PXL:**
```pxl
METAL1 = layer(10, 0);
M1_width = width(METAL1) < 0.09;
drc_deck(M1_width, "M1.W.1", "METAL1 minimum width violation: min = 0.09um");
```

#### Example 2: Spacing Check

**Calibre SVRF:**
```svrf
LAYER POLY 5
POLY_SPACE { @ Minimum spacing = 0.12um
    EXTERNAL POLY < 0.12
}
```

**IC Validator PXL:**
```pxl
POLY = layer(5, 0);
POLY_spacing = external_distance(POLY, POLY) < 0.12;
drc_deck(POLY_spacing, "POLY.S.1", "POLY minimum spacing violation: min = 0.12um");
```

#### Example 3: Enclosure Check

**Calibre SVRF:**
```svrf
LAYER METAL1 10
LAYER CONTACT 6
CONT_ENC { @ Metal1 enclosure of contact >= 0.01um
    ENC METAL1 CONTACT < 0.01
}
```

**IC Validator PXL:**
```pxl
METAL1 = layer(10, 0);
CONTACT = layer(6, 0);
CONT_enclosure = external_enclosure(METAL1, CONTACT) < 0.01;
drc_deck(CONT_enclosure, "CONT.EN.1", "Metal1 enclosure of contact violation: min = 0.01um");
```

#### Example 4: Boolean Operations

**Calibre SVRF:**
```svrf
LAYER POLY 5
LAYER DIFF 1
GATE = AND POLY DIFF
POLY_NOT_GATE = NOT POLY GATE
```

**IC Validator PXL:**
```pxl
POLY = layer(5, 0);
DIFF = layer(1, 0);
GATE = POLY and DIFF;
POLY_NOT_GATE = POLY not GATE;
```

### Common SVRF to PXL Function Mapping

| Calibre SVRF | IC Validator PXL | Description |
|--------------|------------------|-------------|
| `WIDTH layer < value` | `width(layer) < value` | Width check |
| `EXTERNAL layer < value` | `external_distance(layer, layer) < value` | Spacing |
| `INTERNAL layer < value` | `internal_distance(layer) < value` | Internal spacing |
| `ENC layer1 layer2 < value` | `external_enclosure(layer1, layer2) < value` | Enclosure |
| `AND layer1 layer2` | `layer1 and layer2` | Boolean AND |
| `OR layer1 layer2` | `layer1 or layer2` | Boolean OR |
| `NOT layer1 layer2` | `layer1 not layer2` | Boolean NOT |
| `AREA layer < value` | `area(layer) < value` | Area check |
| `DENSITY layer ...` | `density(layer, width, height)` | Density check |
| `DRC CHECK ...` | `drc_deck(violations, name, msg)` | Report violations |

### Pros of Manual Conversion

✅ **Full control** - Optimize for ICV performance
✅ **Better understanding** - Learn PXL deeply
✅ **Customization** - Add ICV-specific features
✅ **Clean code** - Well-structured, documented PXL

### Cons of Manual Conversion

❌ **Time-consuming** - Slow for large rule decks
❌ **Error-prone** - Manual typing introduces mistakes
❌ **Requires expertise** - Need to know both SVRF and PXL

---

## Method 3: Hybrid Approach ⭐ BEST FOR PRODUCTION

### Workflow

```
1. Run cal2pxl for bulk conversion
   └── Gets 80-90% of rules working

2. Identify problem areas
   ├── Review conversion log
   ├── Test critical rules
   └── Document issues

3. Manual refinement
   ├── Fix incorrectly converted rules
   ├── Optimize performance bottlenecks
   ├── Add ICV-specific enhancements
   └── Improve code readability

4. Validation
   ├── Run side-by-side comparison
   ├── Verify violation counts match
   └── Check runtime performance

5. Documentation
   ├── Document changes from Calibre
   ├── Note optimization techniques
   └── Create maintenance guide
```

### Example: Hybrid Conversion

```bash
# Step 1: Automated conversion
cal2pxl -i original_calibre.svrf -o converted.rs -log conv.log

# Step 2: Review log for issues
grep "WARNING\|ERROR" conv.log > issues.txt

# Step 3: Manual fixes in converted.rs
# - Fix complex macros
# - Optimize slow checks
# - Add PXL-specific features

# Step 4: Test
icv -64 -i test.gds -c top converted.rs

# Step 5: Compare with Calibre baseline
# Use same test case for both tools
```

### Pros of Hybrid Approach

✅ **Best of both worlds** - Speed + quality
✅ **Practical** - Realistic for production use
✅ **Validated** - High confidence in results
✅ **Maintainable** - Clean, documented code

---

## Comparison of Methods

| Aspect | cal2pxl (Auto) | Manual | Hybrid |
|--------|----------------|--------|--------|
| **Speed** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ |
| **Accuracy** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Effort** | Low | High | Medium |
| **Learning curve** | Low | High | Medium |
| **Code quality** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Optimization** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Best for** | Simple decks | Small decks | Production |

---

## Common Conversion Challenges

### Challenge 1: Complex Macros

**Problem:** Calibre user-defined macros may not convert properly

**Solution:**
```pxl
// Rewrite macro as PXL function
function check_spacing(polygon_set layer, real min_space, string rule) {
    polygon_set violations = external_distance(layer, layer) < min_space;
    drc_deck(violations, rule, "Spacing violation: min = " + string(min_space));
    return violations;
}
```

### Challenge 2: Layer Variables

**Problem:** Calibre VARIABLE statements don't translate directly

**Solution:**
```pxl
// Use PXL preprocessor
#define MIN_WIDTH 0.09
#define MIN_SPACE 0.12

M1_width = width(METAL1) < MIN_WIDTH;
```

### Challenge 3: Text Handling

**Problem:** Text layer operations differ between tools

**Solution:**
```pxl
// ICV text handling
TEXT_LAYER = text_layer(100, 0);
text_violations = text(TEXT_LAYER, "*", "*");  // Match all text
```

### Challenge 4: DFM Rules

**Problem:** Calibre's advanced DFM checks need special handling

**Solution:**
- Use ICV's built-in DFM functions
- May require foundry-specific PXL libraries
- Check if ICV equivalent exists

---

## Validation Strategy

### 1. Regression Testing

```bash
# Run both tools on same test case
calibre -drc calibre_deck.svrf test.gds
icv -64 -i test.gds converted_deck.rs

# Compare results
diff calibre_results.db icv_results.vue
```

### 2. Violation Count Comparison

Create a script to compare:
- Total violation count
- Violations per rule
- Violation locations

### 3. Visual Verification

Use layout viewers to spot-check:
- Load same violation database
- Check polygon highlighting matches
- Verify error markers align

---

## Best Practices

### ✅ DO

1. **Start with cal2pxl** for initial conversion
2. **Test incrementally** - Convert and validate section by section
3. **Use version control** - Track all changes
4. **Document differences** - Note Calibre vs ICV behavior
5. **Optimize later** - Get correct results first, then optimize
6. **Keep backups** - Save original Calibre deck
7. **Use comments** - Explain non-obvious conversions
8. **Check foundry support** - Verify foundry provides ICV decks

### ❌ DON'T

1. **Don't trust automated conversion blindly**
2. **Don't convert everything at once** - Test gradually
3. **Don't ignore warnings** - Review cal2pxl logs carefully
4. **Don't skip validation** - Always verify results
5. **Don't mix SVRF and PXL** - Complete the conversion
6. **Don't forget include files** - Convert all dependencies

---

## Tools and Resources

### Synopsys Resources

1. **cal2pxl utility** - `$ICV_HOME_DIR/contrib/cal2pxl/`
2. **IC Validator User Guide** - `$ICV_HOME_DIR/doc/`
3. **PXL Reference Manual** - `icvrefman.pdf`
4. **Training Videos** - Synopsys IC Validator Videos portal
5. **SolvNet** - https://solvnet.synopsys.com/

### Useful Commands

```bash
# Find cal2pxl
find $ICV_HOME_DIR -name "cal2pxl" -type f

# Check cal2pxl version
$ICV_HOME_DIR/contrib/cal2pxl/cal2pxl -version

# Get help
$ICV_HOME_DIR/contrib/cal2pxl/cal2pxl -help

# View example scripts
ls $ICV_HOME_DIR/contrib/cal2pxl/examples/
```

---

## Step-by-Step Conversion Guide

### Phase 1: Preparation (1-2 days)

1. **Inventory Calibre deck**
   - List all files
   - Document dependencies
   - Identify custom macros

2. **Setup environment**
   ```bash
   export ICV_HOME_DIR=/path/to/icv
   export PATH=$ICV_HOME_DIR/bin/LINUX.64:$PATH
   ```

3. **Create test cases**
   - Small GDS with known violations
   - Baseline results from Calibre

### Phase 2: Conversion (2-5 days)

1. **Run cal2pxl**
   ```bash
   cd $ICV_HOME_DIR/contrib/cal2pxl
   ./cal2pxl -i calibre_deck.svrf -o icv_deck.rs -log conv.log
   ```

2. **Review log file**
   ```bash
   grep -i "warning\|error\|failed" conv.log
   ```

3. **Initial test**
   ```bash
   icv -64 -i test.gds -c top icv_deck.rs
   ```

### Phase 3: Refinement (3-7 days)

1. **Fix conversion errors**
2. **Optimize slow rules**
3. **Add missing checks**
4. **Improve code structure**

### Phase 4: Validation (2-3 days)

1. **Run comprehensive tests**
2. **Compare violation counts**
3. **Visual spot-checks**
4. **Performance benchmarking**

### Phase 5: Deployment (1-2 days)

1. **Document changes**
2. **Train team**
3. **Update flows**
4. **Monitor production use**

**Total Time Estimate: 2-3 weeks for complete migration**

---

## Conclusion

### Recommended Approach for Most Teams

```
Use Hybrid Method:
1. cal2pxl for bulk conversion (Day 1)
2. Manual refinement (Days 2-7)
3. Thorough validation (Days 8-10)
4. Documentation and deployment (Days 11-14)
```

### Success Factors

✅ Allocate sufficient time
✅ Have both SVRF and PXL expertise
✅ Test thoroughly
✅ Document everything
✅ Get foundry support

---

## Quick Reference

| Need | Command/Tool |
|------|-------------|
| Automated conversion | `cal2pxl -i input.svrf -o output.rs` |
| Find cal2pxl | `$ICV_HOME_DIR/contrib/cal2pxl/` |
| PXL documentation | `$ICV_HOME_DIR/doc/icvrefman/` |
| Test conversion | `icv -64 -i test.gds output.rs` |
| Function mapping | See SVRF to PXL table above |
| Training | Synopsys SolvNet, IC Validator Videos |

---

**Last Updated:** 2025
**For:** IC Validator version S-2021.06 and later
