#!/usr/bin/env python3
"""
Compare variable definitions between Calibre SVRF and ICV PXL files.
Identifies missing, mismatched, and unique variables.

Usage:
    python3 compare_variables.py -c calibre.svrf -i icv.rs
    python3 compare_variables.py -c calibre.svrf -i icv.rs -s missing.rs
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
        assign_pattern = r'^\s*(\w+)\s*=\s*([A-Z]+)\s+(.+?)(?=\n|$)'
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
        # Matches lines inside { } that look like assignments
        rule_block_pattern = r'^\s*(\w+)\s*\{[^}]*\}'
        for rule_match in re.finditer(rule_block_pattern, content, re.MULTILINE | re.DOTALL):
            block_content = rule_match.group(0)
            # Find assignments within this block
            block_assign_pattern = r'^\s*(\w+)\s*=\s*([A-Z]+)\s+(.+?)$'
            for assign_match in re.finditer(block_assign_pattern, block_content, re.MULTILINE):
                var_name = assign_match.group(1)
                operation = assign_match.group(2)
                args = assign_match.group(3).strip()
                if var_name not in self.cal_variables:
                    self.cal_variables[var_name] = {
                        'type': 'check',
                        'definition': f'{var_name} = {operation} {args}',
                        'line': content[:rule_match.start() + assign_match.start()].count('\n') + 1
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
        # Matches: var = expr < value; or var = expr > value;
        comp_pattern = r'^\s*(\w+)\s*=\s*(.+?)\s*([<>=!]+)\s*([^;]+)\s*;'
        for match in re.finditer(comp_pattern, content, re.MULTILINE):
            name = match.group(1)
            if name not in self.icv_variables:
                expr = match.group(2).strip()
                op = match.group(3)
                value = match.group(4).strip()
                # Skip if this looks like a function call (already caught above)
                if '(' not in expr or not expr.endswith(')'):
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
        if total_cal > 0:
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
                print(f"    Calibre (line {cal_info['line']:4d}): {cal_info['definition'][:60]}")
                print(f"    ICV     (line {icv_info['line']:4d}): {icv_info['definition'][:60]}")
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
            print("   - Use -s option to generate sync script")

        if icv_only > 0:
            print(f"\n2. Review {icv_only} ICV-only variables:")
            print("   - Check if they should exist in Calibre")
            print("   - Or if they are ICV-specific optimizations")
            print("   - Document any intentional differences")

        if total_cal > 0 and matching < total_cal * 0.8:
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
        description='Compare variables between Calibre SVRF and ICV PXL files',
        epilog='Example: python3 compare_variables.py -c calibre.svrf -i icv.rs -s missing.rs'
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
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Compare
    stats = comp.compare()

    # Generate sync script if requested
    if args.sync_script:
        comp.generate_sync_script(args.sync_script)

    # Exit code based on match rate
    if stats['total_cal'] > 0:
        match_rate = stats['matching'] / stats['total_cal']
        if match_rate < 0.8:
            print(f"\n⚠️  Warning: Low match rate ({match_rate*100:.1f}%)")
            sys.exit(1)
        elif stats['cal_only'] > 0 or stats['icv_only'] > 0:
            print(f"\n⚠️  Warning: Variables are not in sync")
            sys.exit(1)
        else:
            print(f"\n✅ Success: All variables match!")
            sys.exit(0)
    else:
        print("\n⚠️  Warning: No Calibre variables found")
        sys.exit(1)


if __name__ == '__main__':
    main()
