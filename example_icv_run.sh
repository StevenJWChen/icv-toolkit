#!/bin/bash
# ============================================================================
# Example script to run IC Validator DRC
# ============================================================================

# Set IC Validator home directory
export ICV_HOME_DIR="/path/to/synopsys/icv/S-2021.06"
export PATH="${ICV_HOME_DIR}/bin/LINUX.64:${PATH}"

# Input files
GDS_FILE="your_design.gds"
TOP_CELL="top_module"
DRC_RUNSET="example_icv_drc.rs"

# Output files
OUTPUT_DIR="./drc_results"
mkdir -p ${OUTPUT_DIR}

# Run IC Validator DRC
icv -64 \
    -i ${GDS_FILE} \
    -c ${TOP_CELL} \
    -f GDSII \
    -D CUSTOM_RULES \
    -vue \
    -dp 4 \
    -o ${OUTPUT_DIR} \
    ${DRC_RUNSET}

# Check results
if [ -f "${OUTPUT_DIR}/${TOP_CELL}.LAYOUT_ERRORS" ]; then
    echo "DRC completed. Check results in ${OUTPUT_DIR}"
    echo "View results with: icv_vue -64 -load ${OUTPUT_DIR}/${TOP_CELL}.vue"
else
    echo "DRC run may have failed. Check log files."
fi
