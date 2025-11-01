#!/usr/bin/env python3
"""
Minimal SVRF to PXL Translator - Working Prototype
Demonstrates core translation functionality

Usage:
    python mini_translator_prototype.py -i input.svrf -o output.rs
"""

import re
import argparse
from dataclasses import dataclass
from typing import List, Optional, Union
from enum import Enum


# ============================================================================
# Data Structures (Intermediate Representation)
# ============================================================================

class CheckType(Enum):
    WIDTH = "width"
    SPACING = "spacing"
    ENCLOSURE = "enclosure"
    AREA = "area"
    BOOLEAN = "boolean"


@dataclass
class LayerDef:
    """Layer definition"""
    name: str
    gds_layer: int
    gds_datatype: int = 0

    def to_pxl(self) -> str:
        return f"{self.name} = layer({self.gds_layer}, {self.gds_datatype});"


@dataclass
class WidthCheck:
    """Width check rule"""
    rule_name: str
    layer: str
    operator: str
    value: float
    comment: Optional[str] = None

    def to_pxl(self) -> str:
        lines = []
        if self.comment:
            lines.append(f"// {self.comment}")

        violation_var = f"{self.rule_name}_violations"
        lines.append(f"{violation_var} = width({self.layer}) {self.operator} {self.value};")
        lines.append(
            f'drc_deck({violation_var}, "{self.rule_name}", '
            f'"Width violation: {self.operator} {self.value}um");'
        )
        return "\n".join(lines)


@dataclass
class SpacingCheck:
    """Spacing check rule"""
    rule_name: str
    layer: str
    operator: str
    value: float
    comment: Optional[str] = None

    def to_pxl(self) -> str:
        lines = []
        if self.comment:
            lines.append(f"// {self.comment}")

        violation_var = f"{self.rule_name}_violations"
        lines.append(
            f"{violation_var} = external_distance({self.layer}, {self.layer}) "
            f"{self.operator} {self.value};"
        )
        lines.append(
            f'drc_deck({violation_var}, "{self.rule_name}", '
            f'"Spacing violation: {self.operator} {self.value}um");'
        )
        return "\n".join(lines)


@dataclass
class EnclosureCheck:
    """Enclosure check rule"""
    rule_name: str
    outer_layer: str
    inner_layer: str
    operator: str
    value: float
    comment: Optional[str] = None

    def to_pxl(self) -> str:
        lines = []
        if self.comment:
            lines.append(f"// {self.comment}")

        violation_var = f"{self.rule_name}_violations"
        lines.append(
            f"{violation_var} = external_enclosure({self.outer_layer}, {self.inner_layer}) "
            f"{self.operator} {self.value};"
        )
        lines.append(
            f'drc_deck({violation_var}, "{self.rule_name}", '
            f'"Enclosure violation: {self.operator} {self.value}um");'
        )
        return "\n".join(lines)


@dataclass
class BooleanOp:
    """Boolean operation"""
    result_name: str
    operation: str  # AND, OR, NOT
    layer1: str
    layer2: Optional[str] = None
    comment: Optional[str] = None

    def to_pxl(self) -> str:
        lines = []
        if self.comment:
            lines.append(f"// {self.comment}")

        op_map = {'AND': 'and', 'OR': 'or', 'NOT': 'not'}
        pxl_op = op_map.get(self.operation.upper(), 'and')

        if self.layer2:
            lines.append(f"{self.result_name} = {self.layer1} {pxl_op} {self.layer2};")
        else:
            lines.append(f"{self.result_name} = {pxl_op} {self.layer1};")

        return "\n".join(lines)


# ============================================================================
# Simple SVRF Parser (Regex-based for prototype)
# ============================================================================

class SVRFParser:
    """Simple regex-based SVRF parser for common constructs"""

    def __init__(self):
        self.layers = {}
        self.rules = []
        self.current_rule_name = None

    def parse_file(self, filename: str):
        """Parse SVRF file"""
        with open(filename, 'r') as f:
            content = f.read()

        # Remove C-style comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Process line by line
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith('//'):
                i += 1
                continue

            # Layer definition: LAYER METAL1 10
            if line.startswith('LAYER '):
                self._parse_layer(line)
                i += 1
                continue

            # Rule block: RULE_NAME { ... }
            if '{' in line:
                rule_name = line.split('{')[0].strip()
                self.current_rule_name = rule_name

                # Extract comment if present
                comment = None
                if '@' in line:
                    comment = line.split('@')[1].split('}')[0].strip()

                # Find matching closing brace
                brace_count = line.count('{') - line.count('}')
                rule_lines = [line]
                i += 1

                while i < len(lines) and brace_count > 0:
                    rule_lines.append(lines[i])
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    i += 1

                rule_body = '\n'.join(rule_lines)
                self._parse_rule_block(rule_name, rule_body, comment)
                continue

            # Assignment: RESULT = AND LAYER1 LAYER2
            if '=' in line and not line.startswith('LAYER'):
                self._parse_assignment(line)
                i += 1
                continue

            i += 1

    def _parse_layer(self, line: str):
        """Parse layer definition"""
        # LAYER METAL1 10 or LAYER METAL1 10 0
        match = re.match(r'LAYER\s+(\w+)\s+(\d+)(?:\s+(\d+))?', line)
        if match:
            name = match.group(1)
            gds_layer = int(match.group(2))
            gds_datatype = int(match.group(3)) if match.group(3) else 0

            layer = LayerDef(name, gds_layer, gds_datatype)
            self.layers[name] = layer

    def _parse_rule_block(self, rule_name: str, block: str, comment: Optional[str]):
        """Parse rule block"""
        # WIDTH check
        if 'WIDTH' in block:
            match = re.search(r'WIDTH\s+(\w+)\s*([<>=!]+)\s*([\d.]+)', block)
            if match:
                layer = match.group(1)
                operator = match.group(2)
                value = float(match.group(3))
                self.rules.append(WidthCheck(rule_name, layer, operator, value, comment))

        # EXTERNAL (spacing) check
        elif 'EXTERNAL' in block:
            match = re.search(r'EXTERNAL\s+(\w+)\s*([<>=!]+)\s*([\d.]+)', block)
            if match:
                layer = match.group(1)
                operator = match.group(2)
                value = float(match.group(3))
                self.rules.append(SpacingCheck(rule_name, layer, operator, value, comment))

        # INTERNAL (spacing) check
        elif 'INTERNAL' in block:
            match = re.search(r'INTERNAL\s+(\w+)\s*([<>=!]+)\s*([\d.]+)', block)
            if match:
                layer = match.group(1)
                operator = match.group(2)
                value = float(match.group(3))
                # Use same structure as EXTERNAL
                self.rules.append(SpacingCheck(rule_name, layer, operator, value, comment))

        # ENC (enclosure) check
        elif 'ENC' in block:
            match = re.search(r'ENC\s+(\w+)\s+(\w+)\s*([<>=!]+)\s*([\d.]+)', block)
            if match:
                outer = match.group(1)
                inner = match.group(2)
                operator = match.group(3)
                value = float(match.group(4))
                self.rules.append(EnclosureCheck(rule_name, outer, inner, operator, value, comment))

    def _parse_assignment(self, line: str):
        """Parse assignment statements"""
        # RESULT = AND LAYER1 LAYER2
        match = re.match(r'(\w+)\s*=\s*(AND|OR|NOT)\s+(\w+)(?:\s+(\w+))?', line)
        if match:
            result = match.group(1)
            operation = match.group(2)
            layer1 = match.group(3)
            layer2 = match.group(4)

            # Extract comment if present
            comment = None
            if '@' in line:
                comment = line.split('@')[1].strip()

            self.rules.append(BooleanOp(result, operation, layer1, layer2, comment))


# ============================================================================
# PXL Generator
# ============================================================================

class PXLGenerator:
    """Generate PXL code from intermediate representation"""

    def __init__(self):
        self.output_lines = []

    def generate_header(self) -> str:
        """Generate PXL header"""
        return """// ============================================================================
// Automatically Generated by SVRF-to-PXL Translator (Prototype)
// ============================================================================
// This file was automatically translated from Calibre SVRF format
// Manual review and validation recommended
// ============================================================================

#include <icv.rh>

"""

    def generate_layers(self, layers: dict) -> str:
        """Generate layer definitions"""
        lines = []
        lines.append("// ============================================================================")
        lines.append("// LAYER DEFINITIONS")
        lines.append("// ============================================================================\n")

        for layer in sorted(layers.values(), key=lambda x: x.gds_layer):
            lines.append(layer.to_pxl())

        lines.append("")
        return "\n".join(lines)

    def generate_rules(self, rules: list) -> str:
        """Generate DRC rules"""
        lines = []
        lines.append("// ============================================================================")
        lines.append("// DRC RULES")
        lines.append("// ============================================================================\n")

        for rule in rules:
            lines.append(rule.to_pxl())
            lines.append("")  # Blank line between rules

        return "\n".join(lines)

    def generate_footer(self) -> str:
        """Generate PXL footer"""
        return """// ============================================================================
// END OF DRC DECK
// ============================================================================
"""

    def generate(self, parser: SVRFParser) -> str:
        """Generate complete PXL file"""
        output = []
        output.append(self.generate_header())
        output.append(self.generate_layers(parser.layers))
        output.append(self.generate_rules(parser.rules))
        output.append(self.generate_footer())

        return "\n".join(output)


# ============================================================================
# Main Program
# ============================================================================

def main():
    """Main translator program"""
    arg_parser = argparse.ArgumentParser(
        description='Translate Calibre SVRF to IC Validator PXL (Prototype)',
        epilog='This is a minimal prototype supporting basic SVRF constructs'
    )

    arg_parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input SVRF file'
    )

    arg_parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output PXL file'
    )

    arg_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    arg_parser.add_argument(
        '--stats',
        action='store_true',
        help='Show translation statistics'
    )

    args = arg_parser.parse_args()

    try:
        # Parse SVRF
        if args.verbose:
            print(f"Parsing {args.input}...")

        parser = SVRFParser()
        parser.parse_file(args.input)

        if args.verbose or args.stats:
            print(f"  Layers found: {len(parser.layers)}")
            print(f"  Rules found: {len(parser.rules)}")

            # Count by type
            width_count = sum(1 for r in parser.rules if isinstance(r, WidthCheck))
            spacing_count = sum(1 for r in parser.rules if isinstance(r, SpacingCheck))
            enc_count = sum(1 for r in parser.rules if isinstance(r, EnclosureCheck))
            bool_count = sum(1 for r in parser.rules if isinstance(r, BooleanOp))

            print(f"    Width checks: {width_count}")
            print(f"    Spacing checks: {spacing_count}")
            print(f"    Enclosure checks: {enc_count}")
            print(f"    Boolean ops: {bool_count}")

        # Generate PXL
        if args.verbose:
            print(f"Generating PXL...")

        generator = PXLGenerator()
        pxl_code = generator.generate(parser)

        # Write output
        with open(args.output, 'w') as f:
            f.write(pxl_code)

        if args.verbose:
            print(f"Successfully wrote {args.output}")

        print("Translation completed successfully!")

        if args.stats:
            print(f"\nOutput statistics:")
            print(f"  Lines: {len(pxl_code.split(chr(10)))}")
            print(f"  Size: {len(pxl_code)} bytes")

    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e}")
        return 1

    except Exception as e:
        print(f"Error during translation: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
