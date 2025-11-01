# Building Your Own SVRF-to-PXL Translator

## Why Build Your Own Translator?

### Good Reasons ✅
- **cal2pxl limitations** - Doesn't handle your specific use cases
- **Custom requirements** - Need specific optimizations or features
- **Learning/Research** - Understanding both languages deeply
- **Proprietary extensions** - Your SVRF has custom macros/extensions
- **Integration needs** - Want to integrate with existing tools/workflows
- **Control** - Full control over translation logic
- **IP concerns** - Cannot use Synopsys tools for some reason

### Consider Alternatives First ⚠️
- **Time investment** - 3-6 months for full-featured translator
- **Maintenance burden** - SVRF/PXL evolve, need updates
- **Edge cases** - Many corner cases to handle
- **Testing** - Requires extensive validation
- **cal2pxl works** - Already handles 80-90% of cases

---

## Recommended Approach

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TRANSLATION PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SVRF Input                                                   │
│      ↓                                                        │
│  ┌──────────────┐                                            │
│  │  Lexer       │ → Tokens                                   │
│  └──────────────┘                                            │
│      ↓                                                        │
│  ┌──────────────┐                                            │
│  │  Parser      │ → Abstract Syntax Tree (AST)               │
│  └──────────────┘                                            │
│      ↓                                                        │
│  ┌──────────────┐                                            │
│  │  Semantic    │ → Validated & Annotated AST                │
│  │  Analyzer    │                                            │
│  └──────────────┘                                            │
│      ↓                                                        │
│  ┌──────────────┐                                            │
│  │  Translator  │ → PXL AST                                  │
│  └──────────────┘                                            │
│      ↓                                                        │
│  ┌──────────────┐                                            │
│  │  Code        │ → PXL Output                               │
│  │  Generator   │                                            │
│  └──────────────┘                                            │
│      ↓                                                        │
│  PXL Output                                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Recommendations

### Option 1: Python ⭐ RECOMMENDED

**Why Python?**
- ✅ Rich parsing libraries (PLY, ANTLR, Lark)
- ✅ Rapid development
- ✅ Excellent string manipulation
- ✅ Good testing frameworks
- ✅ Easy to maintain

**Libraries:**
```python
# Parsing
- PLY (Python Lex-Yacc)
- Lark (modern parsing toolkit)
- ANTLR4 (with Python target)

# AST manipulation
- ast (built-in)
- astor (AST to source)

# Testing
- pytest
- unittest
```

**Pros:**
- Fast development (2-3 months)
- Easy to extend
- Large ecosystem

**Cons:**
- Slower runtime than compiled languages
- Not ideal for very large decks (10K+ rules)

### Option 2: Java/Kotlin

**Why Java/Kotlin?**
- ✅ ANTLR is Java-native
- ✅ Good performance
- ✅ Strong type system
- ✅ Enterprise-grade

**Libraries:**
```java
// Parsing
- ANTLR4 (grammar-based)
- JavaCC (parser generator)

// Build tools
- Maven/Gradle
```

**Pros:**
- Better performance
- Static typing catches errors
- Good for large projects

**Cons:**
- More verbose
- Longer development time (4-6 months)

### Option 3: C++

**Why C++?**
- ✅ Maximum performance
- ✅ Similar to PXL/SVRF implementation

**Libraries:**
```cpp
// Parsing
- ANTLR4 (C++ target)
- Flex/Bison
- Boost.Spirit

// String handling
- Boost libraries
```

**Pros:**
- Best performance
- Can handle huge decks

**Cons:**
- Longest development time (6+ months)
- More complex to maintain
- Memory management overhead

### Option 4: Go

**Why Go?**
- ✅ Good balance of speed and simplicity
- ✅ Easy to deploy (single binary)
- ✅ Good concurrency support

**Pros:**
- Fast compilation
- Easy deployment
- Growing ecosystem

**Cons:**
- Fewer parsing libraries
- Less mature tooling for this domain

---

## My Recommendation: Python with Lark ⭐⭐⭐

### Rationale:
1. **Fastest time-to-market** - 2-3 months for MVP
2. **Lark** - Modern, fast, and maintainable
3. **Easy iteration** - Quick to test and refine
4. **Good enough performance** - Handles typical decks fine
5. **Maintainability** - Easy for others to contribute

---

## Implementation Strategy

### Phase 1: Foundation (Weeks 1-2)

#### 1.1 Study the Languages

**SVRF Analysis:**
```bash
# Collect sample SVRF files
- Calibre documentation
- Your existing rule decks
- Foundry examples

# Document constructs
- Layer definitions
- DRC operations
- Boolean operations
- Macros and functions
- Preprocessor directives
```

**PXL Analysis:**
```bash
# Study PXL syntax
- IC Validator documentation
- Example PXL files
- Function reference
- Data types and structures
```

#### 1.2 Define Scope

**Minimum Viable Product (MVP):**
```
✓ Layer definitions (LAYER)
✓ Basic DRC checks (WIDTH, EXTERNAL, INTERNAL, ENC)
✓ Boolean operations (AND, OR, NOT)
✓ Simple expressions
✓ Comments
✓ Output formatting
```

**Phase 2 Features:**
```
◯ Macros and functions
◯ Preprocessor (#include, #define)
◯ Complex operations (AREA, DENSITY, etc.)
◯ Advanced features
◯ Optimization
```

### Phase 2: Lexer & Parser (Weeks 3-4)

#### Using Lark (Recommended)

**Grammar Definition:**
```python
# svrf_grammar.lark

start: statement+

statement: layer_def
         | drc_check
         | assignment
         | comment

layer_def: "LAYER" IDENTIFIER NUMBER

drc_check: IDENTIFIER "{" operation "}"

operation: width_check
         | spacing_check
         | enclosure_check
         | boolean_op

width_check: "WIDTH" layer_ref OPERATOR value

spacing_check: "EXTERNAL" layer_ref OPERATOR value

enclosure_check: "ENC" layer_ref layer_ref OPERATOR value

boolean_op: "AND" layer_ref layer_ref
          | "OR" layer_ref layer_ref
          | "NOT" layer_ref layer_ref

layer_ref: IDENTIFIER

OPERATOR: "<" | ">" | "<=" | ">=" | "==" | "!="
value: NUMBER ["um" | "nm"]

IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+(\.[0-9]+)?/
COMMENT: "//" /[^\n]*/

%import common.WS
%ignore WS
%ignore COMMENT
```

**Parser Implementation:**
```python
from lark import Lark, Transformer, v_args

# Load grammar
with open('svrf_grammar.lark') as f:
    svrf_parser = Lark(f.read(), start='start')

# Parse SVRF
def parse_svrf(input_file):
    with open(input_file) as f:
        content = f.read()
    tree = svrf_parser.parse(content)
    return tree
```

### Phase 3: AST Transformation (Weeks 5-6)

**SVRF AST to Intermediate Representation:**

```python
class SVRFToIR(Transformer):
    """Transform SVRF parse tree to intermediate representation"""

    def layer_def(self, items):
        name, number = items
        return LayerDef(name=str(name), number=int(number))

    def width_check(self, items):
        layer, operator, value = items
        return WidthCheck(
            layer=str(layer),
            operator=str(operator),
            value=float(value)
        )

    def spacing_check(self, items):
        layer, operator, value = items
        return SpacingCheck(
            layer=str(layer),
            operator=str(operator),
            value=float(value)
        )

    def boolean_op(self, items):
        op, layer1, layer2 = items
        return BooleanOp(
            operation=str(op),
            layer1=str(layer1),
            layer2=str(layer2)
        )
```

**Intermediate Representation Classes:**

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class LayerDef:
    name: str
    number: int
    datatype: int = 0

@dataclass
class WidthCheck:
    layer: str
    operator: str
    value: float
    rule_name: Optional[str] = None

@dataclass
class SpacingCheck:
    layer: str
    operator: str
    value: float
    rule_name: Optional[str] = None

@dataclass
class EnclosureCheck:
    outer_layer: str
    inner_layer: str
    operator: str
    value: float
    rule_name: Optional[str] = None

@dataclass
class BooleanOp:
    operation: str  # AND, OR, NOT
    layer1: str
    layer2: str
    result_name: str

@dataclass
class RuleDeck:
    layers: List[LayerDef]
    checks: List  # Mix of check types
    metadata: dict
```

### Phase 4: Translation Engine (Weeks 7-8)

**IR to PXL Translator:**

```python
class IRToPXL:
    """Translate intermediate representation to PXL"""

    def __init__(self):
        self.layers = {}
        self.checks = []

    def translate_layer(self, layer_def: LayerDef) -> str:
        """Translate layer definition"""
        return f"{layer_def.name} = layer({layer_def.number}, {layer_def.datatype});"

    def translate_width_check(self, check: WidthCheck) -> str:
        """Translate width check"""
        rule_name = check.rule_name or f"{check.layer}_width"
        pxl_code = []

        # Generate check
        pxl_code.append(
            f"{rule_name} = width({check.layer}) {check.operator} {check.value};"
        )

        # Generate violation reporting
        pxl_code.append(
            f'drc_deck({rule_name}, "{rule_name.upper()}", '
            f'"Width violation: {check.operator} {check.value}um");'
        )

        return "\n".join(pxl_code)

    def translate_spacing_check(self, check: SpacingCheck) -> str:
        """Translate spacing check"""
        rule_name = check.rule_name or f"{check.layer}_spacing"
        pxl_code = []

        pxl_code.append(
            f"{rule_name} = external_distance({check.layer}, {check.layer}) "
            f"{check.operator} {check.value};"
        )

        pxl_code.append(
            f'drc_deck({rule_name}, "{rule_name.upper()}", '
            f'"Spacing violation: {check.operator} {check.value}um");'
        )

        return "\n".join(pxl_code)

    def translate_enclosure(self, check: EnclosureCheck) -> str:
        """Translate enclosure check"""
        rule_name = check.rule_name or f"{check.outer_layer}_{check.inner_layer}_enc"
        pxl_code = []

        pxl_code.append(
            f"{rule_name} = external_enclosure({check.outer_layer}, "
            f"{check.inner_layer}) {check.operator} {check.value};"
        )

        pxl_code.append(
            f'drc_deck({rule_name}, "{rule_name.upper()}", '
            f'"Enclosure violation: {check.operator} {check.value}um");'
        )

        return "\n".join(pxl_code)

    def translate_boolean(self, op: BooleanOp) -> str:
        """Translate boolean operation"""
        op_map = {
            'AND': 'and',
            'OR': 'or',
            'NOT': 'not'
        }

        pxl_op = op_map.get(op.operation.upper(), 'and')

        return f"{op.result_name} = {op.layer1} {pxl_op} {op.layer2};"

    def generate_header(self) -> str:
        """Generate PXL file header"""
        return """// Automatically generated by SVRF-to-PXL Translator
// Do not edit manually

#include <icv.rh>

// ============================================================================
// LAYER DEFINITIONS
// ============================================================================
"""

    def generate_footer(self) -> str:
        """Generate PXL file footer"""
        return """
// ============================================================================
// END OF DRC DECK
// ============================================================================
"""

    def translate_deck(self, ir_deck: RuleDeck) -> str:
        """Translate complete rule deck"""
        output = []

        # Header
        output.append(self.generate_header())

        # Layers
        for layer in ir_deck.layers:
            output.append(self.translate_layer(layer))

        output.append("\n// ============================================================================")
        output.append("// DRC CHECKS")
        output.append("// ============================================================================\n")

        # Checks
        for check in ir_deck.checks:
            if isinstance(check, WidthCheck):
                output.append(self.translate_width_check(check))
            elif isinstance(check, SpacingCheck):
                output.append(self.translate_spacing_check(check))
            elif isinstance(check, EnclosureCheck):
                output.append(self.translate_enclosure(check))
            elif isinstance(check, BooleanOp):
                output.append(self.translate_boolean(check))
            output.append("")

        # Footer
        output.append(self.generate_footer())

        return "\n".join(output)
```

### Phase 5: Main Program (Week 9)

**Command-Line Interface:**

```python
#!/usr/bin/env python3
"""
SVRF to PXL Translator
Converts Calibre SVRF rule decks to IC Validator PXL format
"""

import argparse
import sys
from pathlib import Path
from lark import Lark, UnexpectedInput

from svrf_parser import SVRFParser
from ir_builder import IRBuilder
from pxl_generator import PXLGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Translate Calibre SVRF to IC Validator PXL'
    )

    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input SVRF file'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output PXL file'
    )

    parser.add_argument(
        '-l', '--layermap',
        help='Layer mapping file'
    )

    parser.add_argument(
        '--log',
        help='Log file for translation messages'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate output PXL syntax'
    )

    args = parser.parse_args()

    # Setup logging
    if args.log:
        log_file = open(args.log, 'w')
    else:
        log_file = sys.stdout

    try:
        # Parse SVRF
        if args.verbose:
            print(f"Parsing {args.input}...", file=log_file)

        svrf_parser = SVRFParser()
        parse_tree = svrf_parser.parse(args.input)

        if args.verbose:
            print(f"  Found {len(parse_tree.layers)} layers", file=log_file)
            print(f"  Found {len(parse_tree.checks)} checks", file=log_file)

        # Build intermediate representation
        if args.verbose:
            print("Building intermediate representation...", file=log_file)

        ir_builder = IRBuilder()
        ir_deck = ir_builder.build(parse_tree)

        # Apply layer mapping if provided
        if args.layermap:
            if args.verbose:
                print(f"Applying layer map {args.layermap}...", file=log_file)
            ir_builder.apply_layermap(ir_deck, args.layermap)

        # Generate PXL
        if args.verbose:
            print(f"Generating PXL output...", file=log_file)

        pxl_generator = PXLGenerator()
        pxl_code = pxl_generator.generate(ir_deck)

        # Write output
        with open(args.output, 'w') as f:
            f.write(pxl_code)

        if args.verbose:
            print(f"Successfully wrote {args.output}", file=log_file)

        # Validate if requested
        if args.validate:
            if args.verbose:
                print("Validating PXL syntax...", file=log_file)
            # TODO: Implement PXL syntax validation

        print("Translation completed successfully!", file=log_file)
        return 0

    except UnexpectedInput as e:
        print(f"Parse error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    finally:
        if args.log and log_file != sys.stdout:
            log_file.close()


if __name__ == '__main__':
    sys.exit(main())
```

### Phase 6: Testing (Weeks 10-11)

**Test Strategy:**

```python
# tests/test_translator.py

import pytest
from svrf_to_pxl import translate

class TestBasicTranslation:

    def test_layer_definition(self):
        svrf = "LAYER METAL1 10"
        pxl = translate(svrf)
        assert "METAL1 = layer(10, 0);" in pxl

    def test_width_check(self):
        svrf = """
        LAYER METAL1 10
        M1_WIDTH { @ Width check
            WIDTH METAL1 < 0.09
        }
        """
        pxl = translate(svrf)
        assert "width(METAL1) < 0.09" in pxl
        assert "drc_deck" in pxl

    def test_spacing_check(self):
        svrf = """
        LAYER POLY 5
        POLY_SPACE { @ Spacing check
            EXTERNAL POLY < 0.12
        }
        """
        pxl = translate(svrf)
        assert "external_distance(POLY, POLY) < 0.12" in pxl

    def test_boolean_operations(self):
        svrf = """
        LAYER POLY 5
        LAYER DIFF 1
        GATE = AND POLY DIFF
        """
        pxl = translate(svrf)
        assert "GATE = POLY and DIFF" in pxl

    def test_enclosure(self):
        svrf = """
        LAYER METAL1 10
        LAYER CONTACT 6
        M1_CONT_ENC { @ Enclosure
            ENC METAL1 CONTACT < 0.01
        }
        """
        pxl = translate(svrf)
        assert "external_enclosure(METAL1, CONTACT) < 0.01" in pxl

class TestComplexRules:
    # Add tests for complex scenarios
    pass

class TestEdgeCases:
    # Add tests for edge cases
    pass
```

**Regression Test Suite:**

```python
# tests/test_regression.py

import os
from pathlib import Path

class TestRegressionSuite:
    """Test against known good translations"""

    def test_foundry_deck_conversion(self):
        """Test conversion of real foundry deck"""
        svrf_file = "tests/data/foundry_deck.svrf"
        expected_pxl = "tests/data/foundry_deck_expected.rs"

        actual_pxl = translate_file(svrf_file)

        # Compare semantically, not textually
        assert semantically_equivalent(actual_pxl, expected_pxl)

    def test_rule_count_preservation(self):
        """Ensure all rules are translated"""
        svrf_file = "tests/data/test_deck.svrf"

        svrf_rules = count_rules(svrf_file)
        pxl_rules = count_rules(translate_file(svrf_file))

        assert svrf_rules == pxl_rules
```

---

## Project Structure

```
svrf-to-pxl-translator/
├── README.md
├── setup.py
├── requirements.txt
├── svrf_to_pxl/
│   ├── __init__.py
│   ├── cli.py                    # Command-line interface
│   ├── grammar/
│   │   └── svrf.lark            # SVRF grammar
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── lexer.py
│   │   ├── parser.py
│   │   └── ast_nodes.py
│   ├── ir/
│   │   ├── __init__.py
│   │   ├── intermediate.py       # IR data structures
│   │   └── builder.py            # AST to IR
│   ├── translator/
│   │   ├── __init__.py
│   │   ├── pxl_generator.py     # IR to PXL
│   │   └── optimizer.py         # Optional optimization
│   └── utils/
│       ├── __init__.py
│       ├── layermap.py          # Layer mapping
│       └── validator.py         # Validation
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_translator.py
│   ├── test_integration.py
│   └── data/
│       ├── test_decks/          # Test SVRF files
│       └── expected/            # Expected PXL outputs
├── docs/
│   ├── user_guide.md
│   ├── developer_guide.md
│   └── svrf_coverage.md         # Supported SVRF features
└── examples/
    ├── simple_deck.svrf
    ├── simple_deck.rs
    └── complex_deck.svrf
```

---

## Development Timeline

### Minimum Viable Product (3 months)

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Setup & Design** | 2 weeks | Architecture, grammar design |
| **Lexer & Parser** | 2 weeks | SVRF parser working |
| **IR Layer** | 2 weeks | Intermediate representation |
| **PXL Generator** | 2 weeks | Basic PXL output |
| **Testing** | 2 weeks | Test suite, validation |
| **Documentation** | 2 weeks | User guide, examples |

### Full Featured Version (6 months)

Add:
- Advanced SVRF features (macros, functions)
- Optimization passes
- Better error messages
- Performance tuning
- Comprehensive documentation

---

## Best Practices

### 1. Start Simple
```python
# MVP: Handle these first
- Layer definitions
- Width checks
- Spacing checks
- Basic boolean operations

# Phase 2: Add these
- Enclosure checks
- Area checks
- Complex expressions

# Phase 3: Advanced
- Macros
- Preprocessor
- Optimization
```

### 2. Test-Driven Development

```python
# Write test first
def test_width_translation():
    svrf = "WIDTH METAL1 < 0.09"
    expected = "width(METAL1) < 0.09"
    assert translate(svrf) == expected

# Then implement
def translate_width(ast_node):
    # Implementation
    pass
```

### 3. Iterative Development

```
Iteration 1: 10 rules working
Iteration 2: 50 rules working
Iteration 3: 100 rules working
Iteration 4: 500 rules working
...
```

### 4. Validation Strategy

```python
def validate_translation(svrf_file, pxl_file):
    """
    Validate translation by comparing:
    1. Rule count
    2. Layer count
    3. Check types
    4. (Optionally) Run both and compare violations
    """
    pass
```

---

## Key Challenges & Solutions

### Challenge 1: SVRF Complexity

**Problem:** SVRF has many edge cases and extensions

**Solution:**
- Start with common subset (80% of rules)
- Incrementally add features
- Document unsupported features clearly

### Challenge 2: Semantic Differences

**Problem:** SVRF and PXL don't map 1:1

**Solution:**
- Use intermediate representation
- Allow for manual annotation
- Provide mapping documentation

### Challenge 3: Performance

**Problem:** Large rule decks (10K+ rules)

**Solution:**
- Profile and optimize hotspots
- Use efficient data structures
- Consider parallel processing

### Challenge 4: Testing

**Problem:** Hard to validate correctness

**Solution:**
- Unit tests for each feature
- Regression tests with real decks
- Cross-validation with cal2pxl
- Run both tools, compare results

---

## Tools & Libraries

### Parsing Tools

| Tool | Language | Pros | Cons |
|------|----------|------|------|
| **Lark** | Python | Modern, fast, maintainable | Python only |
| **ANTLR** | Multi-language | Powerful, mature | Steep learning curve |
| **PLY** | Python | Simple, stable | Older approach |
| **Flex/Bison** | C/C++ | Fast, traditional | C/C++ complexity |

### Testing Tools

```python
# Python
pytest              # Unit testing
hypothesis          # Property-based testing
coverage.py         # Code coverage

# Java
JUnit               # Unit testing
AssertJ             # Fluent assertions
JaCoCo              # Code coverage
```

---

## Example: Complete Mini-Translator

See next section for a working prototype...

---

## Deployment

### As Python Package

```bash
# Install
pip install svrf-to-pxl

# Use
svrf2pxl -i input.svrf -o output.rs
```

### As Standalone Binary

```bash
# Build with PyInstaller
pyinstaller --onefile cli.py

# Use
./svrf2pxl -i input.svrf -o output.rs
```

---

## Maintenance

### Version Control
- Use Git
- Tag releases
- Maintain changelog

### Documentation
- Keep grammar up-to-date
- Document supported features
- Provide examples

### Testing
- Add tests for bug fixes
- Regression test suite
- CI/CD pipeline

---

## Summary

### Recommended Stack
```
Language:  Python 3.9+
Parser:    Lark
Testing:   pytest
Timeline:  3 months MVP, 6 months full
```

### Success Factors
1. ✅ Start with MVP (basic rules only)
2. ✅ Test extensively
3. ✅ Validate against cal2pxl
4. ✅ Document limitations clearly
5. ✅ Iterate based on real decks

### Expected Results
- MVP: Handle 60-70% of typical decks
- V1.0: Handle 80-90% of typical decks
- V2.0: Handle 95%+ with optimizations

---

## Next Steps

Ready to start? See the `MINI_TRANSLATOR_PROTOTYPE.py` file for a working example!
