#!/usr/bin/env python3
"""
Compare Calibre and IC Validator DRC Results
Verifies that both tools produce identical results

Usage:
    python3 compare_drc_results.py -c calibre.rpt -i icv.log [-t 0.001]
"""

import re
import argparse
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set
import sys


@dataclass
class Violation:
    """Represents a single DRC violation"""
    rule: str
    x: float
    y: float
    type: str  # 'width', 'spacing', 'enclosure', etc.

    def __hash__(self):
        # Round to avoid floating point comparison issues
        return hash((self.rule, round(self.x, 3), round(self.y, 3)))

    def __eq__(self, other):
        if not isinstance(other, Violation):
            return False
        return (self.rule == other.rule and
                abs(self.x - other.x) < 0.001 and
                abs(self.y - other.y) < 0.001)


class CalibreParser:
    """Parse Calibre DRC results"""

    def parse_file(self, filename: str) -> Dict[str, List[Violation]]:
        """Parse Calibre DRC report"""
        violations = defaultdict(list)
        current_rule = None

        try:
            with open(filename, 'r') as f:
                for line in f:
                    # Rule check header
                    if 'RULECHECK' in line:
                        match = re.search(r'RULECHECK\s+(\S+)', line)
                        if match:
                            current_rule = match.group(1)

                    # Violation with coordinates
                    # Example: POLYGON ( 10.5 20.3 ) ( 15.7 25.8 )
                    elif 'POLYGON' in line and current_rule:
                        coords = self._extract_coords(line)
                        if coords:
                            violations[current_rule].append(
                                Violation(current_rule, coords[0], coords[1], 'polygon')
                            )

                    # Edge violation
                    elif 'EDGE' in line and current_rule:
                        coords = self._extract_coords(line)
                        if coords:
                            violations[current_rule].append(
                                Violation(current_rule, coords[0], coords[1], 'edge')
                            )

        except FileNotFoundError:
            print(f"Error: File not found: {filename}")
            sys.exit(1)

        return dict(violations)

    def _extract_coords(self, line: str) -> Tuple[float, float]:
        """Extract coordinates from line"""
        # Match patterns like ( 10.5 20.3 )
        matches = re.findall(r'\(\s*([-\d.]+)\s+([-\d.]+)\s*\)', line)
        if matches:
            # Use first coordinate as representative point
            return (float(matches[0][0]), float(matches[0][1]))
        return None


class ICVParser:
    """Parse IC Validator DRC results"""

    def parse_file(self, filename: str) -> Dict[str, List[Violation]]:
        """Parse ICV log/report"""
        violations = defaultdict(list)

        try:
            with open(filename, 'r') as f:
                for line in f:
                    # Look for violation reports
                    # ICV format varies, adjust as needed
                    if 'violation' in line.lower():
                        match = re.search(r'(\w+).*?([-\d.]+)[,\s]+([-\d.]+)', line)
                        if match:
                            rule = match.group(1)
                            x = float(match.group(2))
                            y = float(match.group(3))
                            violations[rule].append(
                                Violation(rule, x, y, 'unknown')
                            )

        except FileNotFoundError:
            print(f"Error: File not found: {filename}")
            sys.exit(1)

        return dict(violations)


class DRCComparator:
    """Compare DRC results from Calibre and ICV"""

    def __init__(self, tolerance: float = 0.001):
        self.tolerance = tolerance

    def compare(self, cal_violations: Dict[str, List[Violation]],
                icv_violations: Dict[str, List[Violation]]) -> Dict:
        """
        Compare violations from both tools

        Returns dict with comparison results
        """
        results = {
            'matching_rules': [],
            'mismatched_rules': [],
            'only_calibre': [],
            'only_icv': [],
            'total_calibre': 0,
            'total_icv': 0,
            'perfect_match': False
        }

        # Get all unique rule names
        all_rules = set(cal_violations.keys()) | set(icv_violations.keys())

        for rule in sorted(all_rules):
            cal_viols = cal_violations.get(rule, [])
            icv_viols = icv_violations.get(rule, [])

            cal_count = len(cal_viols)
            icv_count = len(icv_viols)

            results['total_calibre'] += cal_count
            results['total_icv'] += icv_count

            # Rule only in Calibre
            if rule not in icv_violations:
                results['only_calibre'].append({
                    'rule': rule,
                    'count': cal_count
                })

            # Rule only in ICV
            elif rule not in cal_violations:
                results['only_icv'].append({
                    'rule': rule,
                    'count': icv_count
                })

            # Rule in both - compare counts and locations
            elif cal_count == icv_count:
                # Counts match - check if locations match
                if self._violations_match(cal_viols, icv_viols):
                    results['matching_rules'].append({
                        'rule': rule,
                        'count': cal_count
                    })
                else:
                    results['mismatched_rules'].append({
                        'rule': rule,
                        'calibre_count': cal_count,
                        'icv_count': icv_count,
                        'reason': 'locations differ'
                    })
            else:
                # Counts differ
                results['mismatched_rules'].append({
                    'rule': rule,
                    'calibre_count': cal_count,
                    'icv_count': icv_count,
                    'reason': 'counts differ'
                })

        # Overall match
        results['perfect_match'] = (
            len(results['mismatched_rules']) == 0 and
            len(results['only_calibre']) == 0 and
            len(results['only_icv']) == 0
        )

        return results

    def _violations_match(self, cal_viols: List[Violation],
                         icv_viols: List[Violation]) -> bool:
        """Check if violation lists match within tolerance"""
        if len(cal_viols) != len(icv_viols):
            return False

        # Convert to sets for comparison (using custom __eq__ with tolerance)
        cal_set = set(cal_viols)
        icv_set = set(icv_viols)

        # Check if all violations in one set have a match in the other
        for cal_viol in cal_set:
            found_match = False
            for icv_viol in icv_set:
                if self._violations_equal(cal_viol, icv_viol):
                    found_match = True
                    break
            if not found_match:
                return False

        return True

    def _violations_equal(self, v1: Violation, v2: Violation) -> bool:
        """Check if two violations are equal within tolerance"""
        return (v1.rule == v2.rule and
                abs(v1.x - v2.x) < self.tolerance and
                abs(v1.y - v2.y) < self.tolerance)


def print_report(results: Dict):
    """Print detailed comparison report"""

    print("=" * 80)
    print("CALIBRE vs IC VALIDATOR DRC COMPARISON REPORT")
    print("=" * 80)
    print()

    # Summary statistics
    print("SUMMARY STATISTICS")
    print("-" * 80)
    print(f"Total violations (Calibre): {results['total_calibre']}")
    print(f"Total violations (ICV):     {results['total_icv']}")
    print(f"Matching rules:             {len(results['matching_rules'])}")
    print(f"Mismatched rules:           {len(results['mismatched_rules'])}")
    print(f"Only in Calibre:            {len(results['only_calibre'])}")
    print(f"Only in ICV:                {len(results['only_icv'])}")
    print()

    # Matching rules
    if results['matching_rules']:
        print("✅ MATCHING RULES (Perfect Match)")
        print("-" * 80)
        for item in results['matching_rules']:
            print(f"   {item['rule']:30s} {item['count']:5d} violations")
        print()

    # Mismatched rules
    if results['mismatched_rules']:
        print("❌ MISMATCHED RULES")
        print("-" * 80)
        for item in results['mismatched_rules']:
            print(f"   {item['rule']:30s} Calibre: {item['calibre_count']:5d}  "
                  f"ICV: {item['icv_count']:5d}  ({item['reason']})")
        print()

    # Only in Calibre
    if results['only_calibre']:
        print("⚠️  RULES ONLY IN CALIBRE")
        print("-" * 80)
        for item in results['only_calibre']:
            print(f"   {item['rule']:30s} {item['count']:5d} violations")
        print()

    # Only in ICV
    if results['only_icv']:
        print("⚠️  RULES ONLY IN ICV")
        print("-" * 80)
        for item in results['only_icv']:
            print(f"   {item['rule']:30s} {item['count']:5d} violations")
        print()

    # Overall result
    print("=" * 80)
    if results['perfect_match']:
        print("✅✅✅ PERFECT MATCH")
        print("Calibre and IC Validator produce IDENTICAL results!")
    else:
        print("❌ DIFFERENCES FOUND")
        print("Calibre and IC Validator results differ.")
        print("Review mismatched rules above for details.")
    print("=" * 80)

    return results['perfect_match']


def main():
    parser = argparse.ArgumentParser(
        description='Compare Calibre and IC Validator DRC results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic comparison
  python3 compare_drc_results.py -c calibre.rpt -i icv.log

  # With custom tolerance (10nm)
  python3 compare_drc_results.py -c calibre.rpt -i icv.log -t 0.01

  # Verbose output
  python3 compare_drc_results.py -c calibre.rpt -i icv.log -v
        """
    )

    parser.add_argument(
        '-c', '--calibre',
        required=True,
        help='Calibre DRC report file'
    )

    parser.add_argument(
        '-i', '--icv',
        required=True,
        help='IC Validator log/report file'
    )

    parser.add_argument(
        '-t', '--tolerance',
        type=float,
        default=0.001,
        help='Coordinate tolerance in microns (default: 0.001 = 1nm)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    if args.verbose:
        print(f"Parsing Calibre results from: {args.calibre}")

    # Parse Calibre results
    cal_parser = CalibreParser()
    cal_violations = cal_parser.parse_file(args.calibre)

    if args.verbose:
        print(f"  Found {sum(len(v) for v in cal_violations.values())} violations "
              f"in {len(cal_violations)} rules")
        print(f"Parsing ICV results from: {args.icv}")

    # Parse ICV results
    icv_parser = ICVParser()
    icv_violations = icv_parser.parse_file(args.icv)

    if args.verbose:
        print(f"  Found {sum(len(v) for v in icv_violations.values())} violations "
              f"in {len(icv_violations)} rules")
        print()

    # Compare results
    comparator = DRCComparator(tolerance=args.tolerance)
    results = comparator.compare(cal_violations, icv_violations)

    # Print report
    match = print_report(results)

    # Exit code
    sys.exit(0 if match else 1)


if __name__ == '__main__':
    main()
