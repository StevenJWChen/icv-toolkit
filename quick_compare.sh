#!/bin/bash
#
# Quick Statistical Comparison of Calibre vs ICV Results
# Compares violation counts - fastest verification method
#
# Usage: ./quick_compare.sh <calibre_log> <icv_log>
#

set -e

if [ $# -ne 2 ]; then
    echo "Usage: $0 <calibre_log> <icv_log>"
    echo ""
    echo "Example:"
    echo "  $0 calibre_drc.rpt icv_drc.log"
    exit 1
fi

CALIBRE_LOG=$1
ICV_LOG=$2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "QUICK DRC COMPARISON: Calibre vs IC Validator"
echo "========================================================================"
echo ""

# Check files exist
if [ ! -f "$CALIBRE_LOG" ]; then
    echo "Error: Calibre log file not found: $CALIBRE_LOG"
    exit 1
fi

if [ ! -f "$ICV_LOG" ]; then
    echo "Error: ICV log file not found: $ICV_LOG"
    exit 1
fi

echo "Calibre log: $CALIBRE_LOG"
echo "ICV log:     $ICV_LOG"
echo ""

# Extract Calibre statistics
echo "CALIBRE RESULTS:"
echo "------------------------------------------------------------------------"

# Total violations (adjust grep pattern based on your Calibre output format)
CAL_TOTAL=$(grep -i "TOTAL.*RESULTS\|TOTAL.*VIOLATIONS" "$CALIBRE_LOG" | \
            grep -o '[0-9]\+' | head -1 || echo "0")

echo "  Total violations: $CAL_TOTAL"

# Per-rule counts (adjust pattern as needed)
echo "  Rules with violations:"
grep "RULECHECK" "$CALIBRE_LOG" | while read line; do
    rule=$(echo "$line" | awk '{print $2}')
    # Count violations for this rule (simplified)
    count=$(grep -c "$rule" "$CALIBRE_LOG" || echo "0")
    if [ "$count" -gt 1 ]; then
        echo "    $rule: $count"
    fi
done | head -10

echo ""

# Extract ICV statistics
echo "IC VALIDATOR RESULTS:"
echo "------------------------------------------------------------------------"

# Total violations (adjust grep pattern based on your ICV output format)
ICV_TOTAL=$(grep -i "TOTAL\|violations" "$ICV_LOG" | \
            grep -o '[0-9]\+' | head -1 || echo "0")

echo "  Total violations: $ICV_TOTAL"

# Per-rule counts
echo "  Rules with violations:"
grep -i "drc_deck\|violation" "$ICV_LOG" | head -10 | while read line; do
    echo "    $line"
done

echo ""

# Comparison
echo "========================================================================"
echo "COMPARISON"
echo "========================================================================"
echo ""

printf "%-30s %10s %10s %10s\n" "Metric" "Calibre" "ICV" "Match?"
echo "------------------------------------------------------------------------"

if [ "$CAL_TOTAL" -eq "$ICV_TOTAL" ]; then
    printf "%-30s %10s %10s ${GREEN}%10s${NC}\n" \
           "Total Violations" "$CAL_TOTAL" "$ICV_TOTAL" "✓ YES"
    MATCH=true
else
    diff=$((CAL_TOTAL - ICV_TOTAL))
    printf "%-30s %10s %10s ${RED}%10s${NC}\n" \
           "Total Violations" "$CAL_TOTAL" "$ICV_TOTAL" "✗ NO (Δ$diff)"
    MATCH=false
fi

echo ""

# Overall result
echo "========================================================================"
if [ "$MATCH" = true ]; then
    echo -e "${GREEN}✅ MATCH${NC}"
    echo "Total violation counts match!"
    echo ""
    echo "Next steps:"
    echo "  1. For detailed verification, use: python3 compare_drc_results.py"
    echo "  2. Check individual rule counts match"
    echo "  3. Verify violation locations match"
else
    echo -e "${RED}❌ MISMATCH${NC}"
    echo "Total violation counts differ!"
    echo ""
    echo "Investigation needed:"
    echo "  1. Check if same GDS file was used"
    echo "  2. Verify same run mode (hier/flat)"
    echo "  3. Review rule deck translations"
    echo "  4. Use: python3 compare_drc_results.py for detailed analysis"
fi
echo "========================================================================"

# Exit code
if [ "$MATCH" = true ]; then
    exit 0
else
    exit 1
fi
