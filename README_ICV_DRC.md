# IC Validator DRC Example

This directory contains example files for running DRC (Design Rule Check) with Synopsys IC Validator.

## Files

- **example_icv_drc.rs** - Main DRC rule deck in PXL format
- **example_icv_run.sh** - Shell script to run ICV DRC
- **README_ICV_DRC.md** - This file

## IC Validator DRC Overview

IC Validator uses **PXL (Programmable Extensible Language)** for writing DRC rules. PXL is a C-like language specific to Synopsys IC Validator.

## Common DRC Functions in PXL

### Measurement Functions

| Function | Description | Example |
|----------|-------------|---------|
| `width(layer)` | Measures width of polygons | `width(METAL1) < 0.09` |
| `length(layer)` | Measures length of polygons | `length(POLY) < 0.08` |
| `area(layer)` | Measures area of polygons | `area(DIFF) < 0.05` |
| `external_distance(layer1, layer2)` | Spacing between layers | `external_distance(POLY, POLY) < 0.12` |
| `internal_distance(layer)` | Internal spacing within layer | `internal_distance(METAL1) < 0.09` |

### Enclosure Functions

| Function | Description |
|----------|-------------|
| `external_enclosure(outer, inner)` | Checks if outer layer encloses inner layer |
| `external_extension(layer1, intersection, layer2)` | Checks extension of layer1 beyond intersection |

### Boolean Operations

| Function | Description | Example |
|----------|-------------|---------|
| `and` | Intersection | `POLY and DIFF` |
| `or` | Union | `NPLUS or PPLUS` |
| `not` | Difference | `POLY not DIFF` |
| `xor` | Exclusive OR | `NWELL xor PWELL` |

### Advanced Functions

| Function | Description |
|----------|-------------|
| `density(layer, width, height)` | Calculates density in a window |
| `antenna_ratio(metal, gate, type)` | Checks antenna ratios |
| `sized_rectangles(layer, condition)` | Selects rectangles based on size |

## Running IC Validator DRC

### Command Line

```bash
icv -64 \
    -i <gds_file> \
    -c <top_cell> \
    -f GDSII \
    -D <define_variable> \
    -I <include_dir> \
    -vue \
    -dp <num_threads> \
    <runset_file>
```

### Key Options

- `-64` - Run in 64-bit mode
- `-i` - Input layout file (GDSII or OASIS)
- `-c` - Top cell name
- `-f` - Format (GDSII, OASIS)
- `-D` - Define preprocessor variables
- `-I` - Include directories for header files
- `-vue` - Generate VUE database for viewing violations
- `-dp` - Number of parallel processes
- `-clf` - Command line arguments file
- `-o` - Output directory

### Using Arguments File

Create a file `drc_args_file`:

```
-i your_design.gds
-c top_module
-f GDSII
-D CUSTOM_RULES
-I /path/to/includes
```

Then run:
```bash
icv -64 -clf drc_args_file example_icv_drc.rs
```

## Viewing Results

### Using IC Validator VUE (Violation User Environment)

```bash
icv_vue -64 -load results.vue
```

### Using IC Validator Workbench (ICVWB)

```bash
# Start ICVWB with layout
icvwb -socket 1234 your_design.gds &

# Start VUE with connection to ICVWB
icv_vue -64 -load results.vue -lay icwb -layArgs Port 1234
```

This allows you to:
- Browse violations in VUE
- Cross-probe to layout in ICVWB
- Navigate between errors and layout

## Rule Deck Structure

### 1. Header and Includes
```pxl
#include <icv.rh>
```

### 2. Layer Definitions
```pxl
METAL1 = layer(10, 0);  // GDS layer 10, datatype 0
```

### 3. DRC Rules
```pxl
// Rule check
METAL1_width = width(METAL1) < 0.09;

// Report violations
drc_deck(METAL1_width, "METAL1.W.1", "Metal1 width violation: min = 0.09um");
```

### 4. Conditional Rules
```pxl
#ifdef CUSTOM_RULES
    // Rules enabled only when -D CUSTOM_RULES is specified
#endif
```

## Example Rules Included

The example DRC deck includes:

### Basic Checks
- Minimum width checks (DIFF, POLY, METAL1, METAL2)
- Minimum spacing checks
- Minimum area checks

### Geometric Checks
- Enclosure rules (contacts, vias)
- Extension rules (poly over gate)
- Overlap checks (wells)

### Advanced Checks
- Density checks (metal density in windows)
- Width-dependent spacing rules
- Antenna ratio checks

## Common DRC Violations

| Violation Type | Description |
|----------------|-------------|
| Width | Feature is too narrow |
| Spacing | Features are too close together |
| Enclosure | Outer layer doesn't fully enclose inner layer |
| Extension | Layer doesn't extend far enough |
| Area | Feature area is too small |
| Density | Too much or too little metal in an area |
| Antenna | Metal area to gate area ratio too high |

## Best Practices

1. **Layer Definitions**: Always define all layers at the beginning
2. **Naming Convention**: Use descriptive rule names (e.g., METAL1.W.1)
3. **Comments**: Comment each rule with the actual requirement
4. **Modularity**: Use #include to organize rules into multiple files
5. **Conditional Compilation**: Use #ifdef for optional checks
6. **Error Messages**: Provide clear, actionable error messages

## Range Syntax in ICV

For layer/datatype specifications:
```bash
# Layers 4-5, datatypes 0-1
-iln "4-5,0-1"
```

For dimension checks, use comparison operators:
```pxl
width(METAL1) > 1.0   // Width greater than 1.0um
width(METAL1) < 0.09  // Width less than 0.09um
width(METAL1) >= 0.5  // Width greater than or equal to 0.5um
width(METAL1) != 0.06 // Width not equal to 0.06um
```

## Debugging Tips

1. **Check syntax errors**: ICV will report line numbers
2. **Use -verbose flag**: Get more detailed output
3. **Test incrementally**: Comment out rules to isolate issues
4. **Check layer definitions**: Verify GDS layer numbers match
5. **Review log files**: Check `.log` files for warnings

## Resources

- IC Validator User Guide (Synopsys documentation)
- PXL Reference Manual (Synopsys documentation)
- Your foundry PDK documentation
- Technology DRC rule specifications

## Support

For detailed syntax and advanced features, refer to:
- IC Validator User Guide
- IC Validator Reference Manual (icvrefman)
- Synopsys SolvNet support portal
