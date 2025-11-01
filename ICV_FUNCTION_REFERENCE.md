# Where Are IC Validator PXL Functions Defined?

## Overview

The functions like `drc_deck()`, `external_enclosure()`, `width()`, etc. are **built-in functions** in IC Validator's PXL (Programmable Extensible Language). They are NOT user-defined functions but rather part of the IC Validator core library.

## Function Definition Locations

### 1. **Header Files (.rh files)**

The built-in functions are declared in header files located in the IC Validator installation directory:

```
$ICV_HOME_DIR/include/*.rh
```

Common header files include:
- **icv.rh** - Main IC Validator header file (included in most rule decks)
- **icv_drc.rh** - DRC-specific functions
- **icv_lvs.rh** - LVS-specific functions
- **icv_fill.rh** - Fill-related functions

Typical installation paths:
```
/tools/synopsys/icv/S-2021.06/include/icv.rh
/opt/synopsys/icv/R-2020.09/include/icv.rh
$SYNOPSYS_HOME/icv/<version>/include/icv.rh
```

### 2. **IC Validator Reference Manual (icvrefman)**

The complete function reference is documented in:
- **Document**: IC Validator Reference Manual
- **Filename**: icvrefman.pdf or icvrefman (HTML)
- **Access**: Synopsys SolvNet or installed with IC Validator

Location after installation:
```
$ICV_HOME_DIR/doc/icvrefman/icvrefman.pdf
```

### 3. **Compiled into IC Validator Binary**

The actual implementation is compiled into the IC Validator executable:
```
$ICV_HOME_DIR/bin/LINUX.64/icv
```

These are **native functions** written in C/C++ by Synopsys and exposed to the PXL scripting layer.

## How to Include Functions in Your Rule Deck

### Basic Include

```pxl
// At the top of your .rs file
#include <icv.rh>
```

This single include gives you access to all standard DRC/LVS functions.

### Additional Includes (if needed)

```pxl
#include <icv.rh>          // Main header
#include <icv_drc.rh>      // Additional DRC functions
#include <icv_lvs.rh>      // Additional LVS functions
```

## Common Built-in Function Categories

### 1. **Measurement Functions**
Defined in: `icv.rh`, implemented in IC Validator core

| Function | Description |
|----------|-------------|
| `width(layer)` | Measures width of geometries |
| `length(layer)` | Measures length of geometries |
| `area(layer)` | Measures area of polygons |
| `perimeter(layer)` | Measures perimeter of polygons |
| `angle(layer)` | Measures angles in geometries |

### 2. **Distance/Spacing Functions**
Defined in: `icv.rh`

| Function | Description |
|----------|-------------|
| `external_distance(layer1, layer2)` | Spacing between separate geometries |
| `internal_distance(layer)` | Internal spacing within same layer |
| `external_enclosure(outer, inner)` | Enclosure distance from outer to inner |
| `internal_enclosure(layer)` | Self-enclosure measurements |
| `external_extension(layer1, intersection, layer2)` | Extension of layer1 beyond intersection |

### 3. **Boolean Operations**
Defined in: `icv.rh`

| Function | Description |
|----------|-------------|
| `and` | Intersection of layers |
| `or` | Union of layers |
| `not` | Difference/subtraction |
| `xor` | Exclusive OR |
| `grow(layer, distance)` | Expand layer by distance |
| `shrink(layer, distance)` | Shrink layer by distance |

### 4. **Selection/Filtering Functions**
Defined in: `icv.rh`

| Function | Description |
|----------|-------------|
| `sized_rectangles(layer, condition)` | Select rectangles by size |
| `sized(layer, condition)` | Select geometries by dimension |
| `by_polygon_count(layer, count)` | Select by number of vertices |
| `angle_edge(layer, angle)` | Select edges by angle |

### 5. **Density Functions**
Defined in: `icv.rh`

| Function | Description |
|----------|-------------|
| `density(layer, width, height)` | Calculate density in window |
| `window_density(layer, window_layer)` | Density in specified windows |

### 6. **Output/Reporting Functions**
Defined in: `icv.rh`

| Function | Description |
|----------|-------------|
| `drc_deck(violations, rule_name, message)` | Report DRC violations |
| `lvs_deck(...)` | Report LVS violations |
| `save(layer, filename)` | Save layer to file |

### 7. **Advanced Functions**
Defined in: `icv.rh` and specialized headers

| Function | Description |
|----------|-------------|
| `antenna_ratio(metal, gate, type)` | Antenna ratio checks |
| `net_area(layer)` | Calculate total net area |
| `rectangles(layer)` | Extract rectangular shapes |
| `holes(layer)` | Extract hole geometries |
| `edges(layer)` | Extract edges |
| `corners(layer)` | Extract corner points |

## How to Find Function Documentation

### Method 1: Check Installed Documentation

```bash
# Navigate to IC Validator installation
cd $ICV_HOME_DIR

# Look for documentation
ls -la doc/
ls -la doc/icvrefman/

# Open reference manual
evince doc/icvrefman/icvrefman.pdf  # or xdg-open
```

### Method 2: Use IC Validator Help

```bash
# Launch IC Validator with help
icv -help

# Look for specific function help (if available)
icv -help function_name
```

### Method 3: Check Header Files Directly

```bash
# View the main header file
cd $ICV_HOME_DIR/include
less icv.rh

# Search for function declarations
grep -n "external_enclosure" icv.rh
grep -n "width" icv.rh
```

### Method 4: Access Synopsys Documentation Portal

1. Go to: https://www.synopsys.com/support/synopsys-documentation.html
2. Login with your Synopsys account
3. Navigate to: IC Validator → Reference Manual
4. Search for function names

### Method 5: Use SolvNet (Synopsys Support)

- URL: https://solvnet.synopsys.com/
- Login required (Synopsys customer account)
- Search for: "IC Validator Reference Manual" or "PXL function reference"

## Example: Typical Header File Structure

The `icv.rh` file typically contains declarations like:

```c
// Hypothetical structure (actual file is proprietary)

// Measurement functions
extern polygon_set width(polygon_set layer);
extern polygon_set length(polygon_set layer);
extern polygon_set area(polygon_set layer);

// Distance functions
extern polygon_set external_distance(polygon_set layer1, polygon_set layer2);
extern polygon_set external_enclosure(polygon_set outer, polygon_set inner);

// Reporting functions
extern void drc_deck(polygon_set violations, string rule_name, string message);

// Boolean operations
extern polygon_set and(polygon_set layer1, polygon_set layer2);
extern polygon_set or(polygon_set layer1, polygon_set layer2);
extern polygon_set not(polygon_set layer1, polygon_set layer2);
```

Note: The actual implementation details are proprietary to Synopsys.

## Why You Can't See the Source Code

The PXL functions are:
1. **Proprietary**: Owned by Synopsys, not open source
2. **Compiled**: Implemented in C/C++, compiled into binary
3. **Optimized**: Highly optimized for performance on large layouts
4. **Protected**: Part of Synopsys intellectual property

## Creating Your Own Functions

While you can't modify built-in functions, you CAN create user-defined functions:

```pxl
// User-defined function in PXL
function check_metal_width(polygon_set metal, real min_width, string rule_name) {
    polygon_set violations = width(metal) < min_width;
    drc_deck(violations, rule_name, "Metal width < " + string(min_width));
    return violations;
}

// Usage
check_metal_width(METAL1, 0.09, "M1.W.1");
```

## Quick Reference: Where to Look

| Need | Location |
|------|----------|
| Function declaration | `$ICV_HOME_DIR/include/icv.rh` |
| Function documentation | `$ICV_HOME_DIR/doc/icvrefman/` |
| Function implementation | Compiled in `$ICV_HOME_DIR/bin/LINUX.64/icv` (binary) |
| Examples | PDK rule decks, foundry documentation |
| Help | Synopsys SolvNet, IC Validator User Guide |

## Summary

**The PXL functions are:**
- ✓ Built into IC Validator (not user-defined)
- ✓ Declared in header files (`icv.rh`)
- ✓ Documented in IC Validator Reference Manual
- ✓ Implemented in compiled C/C++ code
- ✓ Accessed via `#include <icv.rh>` in your rule deck

**To learn about specific functions:**
1. Check `$ICV_HOME_DIR/doc/icvrefman/`
2. Access Synopsys SolvNet documentation
3. Review example rule decks from your PDK
4. Consult IC Validator User Guide

## Additional Resources

- **IC Validator User Guide** (icvug) - Usage and workflow
- **IC Validator Reference Manual** (icvrefman) - Complete function reference
- **PXL Language Reference** - PXL syntax and programming
- **Foundry PDK Documentation** - Technology-specific examples
- **Synopsys Training** - IC Validator courses and workshops
