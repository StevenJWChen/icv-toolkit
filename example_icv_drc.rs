// ============================================================================
// IC Validator DRC Example Rule Deck
// Technology: Generic Example (40nm)
// ============================================================================
// This is a PXL (Programmable Extensible Language) format file
// PXL is Synopsys IC Validator's proprietary rule language
// ============================================================================

// Header and setup
#include <icv.rh>

// ============================================================================
// LAYER DEFINITIONS
// ============================================================================
// Define layers from GDSII by layer number and datatype
// Format: LAYER_NAME = layer(gds_layer_number, gds_datatype);

DIFF     = layer(1, 0);    // Diffusion layer
POLY     = layer(5, 0);    // Polysilicon layer
NWELL    = layer(2, 0);    // N-Well layer
PWELL    = layer(3, 0);    // P-Well layer
CONTACT  = layer(6, 0);    // Contact layer
METAL1   = layer(10, 0);   // Metal 1 layer
METAL2   = layer(11, 0);   // Metal 2 layer
VIA1     = layer(15, 0);   // Via between Metal1 and Metal2

// Derived layers
NPLUS    = layer(7, 0);    // N+ implant
PPLUS    = layer(8, 0);    // P+ implant

// ============================================================================
// DESIGN RULE CHECKS
// ============================================================================

// ----------------------------------------------------------------------------
// DIFFUSION (DIFF) RULES
// ----------------------------------------------------------------------------

// DIFF.W.1: Minimum width of diffusion
DIFF_width = width(DIFF) < 0.1;
drc_deck(DIFF_width, "DIFF.W.1", "Diffusion minimum width violation: min = 0.1um");

// DIFF.S.1: Minimum spacing between diffusion regions
DIFF_spacing = external_distance(DIFF, DIFF) < 0.14;
drc_deck(DIFF_spacing, "DIFF.S.1", "Diffusion minimum spacing violation: min = 0.14um");

// DIFF.A.1: Minimum area of diffusion
DIFF_area = area(DIFF) < 0.05;
drc_deck(DIFF_area, "DIFF.A.1", "Diffusion minimum area violation: min = 0.05um^2");

// ----------------------------------------------------------------------------
// POLYSILICON (POLY) RULES
// ----------------------------------------------------------------------------

// POLY.W.1: Minimum width of polysilicon
POLY_width = width(POLY) < 0.08;
drc_deck(POLY_width, "POLY.W.1", "Poly minimum width violation: min = 0.08um");

// POLY.S.1: Minimum spacing between poly lines
POLY_spacing = external_distance(POLY, POLY) < 0.12;
drc_deck(POLY_spacing, "POLY.S.1", "Poly minimum spacing violation: min = 0.12um");

// POLY.EX.1: Minimum poly extension beyond diffusion (gate extension)
POLY_gate = POLY and DIFF;
POLY_extension = external_extension(POLY, POLY_gate, DIFF) < 0.15;
drc_deck(POLY_extension, "POLY.EX.1", "Poly extension over diffusion violation: min = 0.15um");

// ----------------------------------------------------------------------------
// POLY-DIFF INTERACTION RULES
// ----------------------------------------------------------------------------

// POLY.S.2: Minimum spacing between poly and diffusion (not gate)
POLY_not_gate = POLY not POLY_gate;
POLY_DIFF_spacing = external_distance(POLY_not_gate, DIFF) < 0.075;
drc_deck(POLY_DIFF_spacing, "POLY.S.2", "Poly to diffusion spacing violation: min = 0.075um");

// ----------------------------------------------------------------------------
// CONTACT RULES
// ----------------------------------------------------------------------------

// CONT.W.1: Contact must be square with exact dimension
// Check both width and length
CONT_width = width(CONTACT) != 0.06;
drc_deck(CONT_width, "CONT.W.1", "Contact width must be exactly 0.06um");

CONT_length = length(CONTACT) != 0.06;
drc_deck(CONT_length, "CONT.L.1", "Contact length must be exactly 0.06um");

// CONT.S.1: Minimum spacing between contacts
CONT_spacing = external_distance(CONTACT, CONTACT) < 0.08;
drc_deck(CONT_spacing, "CONT.S.1", "Contact spacing violation: min = 0.08um");

// CONT.EN.1: Minimum diffusion enclosure of contact
CONT_on_DIFF = CONTACT and DIFF;
CONT_DIFF_enclosure = external_enclosure(DIFF, CONT_on_DIFF) < 0.04;
drc_deck(CONT_DIFF_enclosure, "CONT.EN.1", "Diffusion enclosure of contact violation: min = 0.04um");

// CONT.EN.2: Minimum poly enclosure of contact
CONT_on_POLY = CONTACT and POLY;
CONT_POLY_enclosure = external_enclosure(POLY, CONT_on_POLY) < 0.03;
drc_deck(CONT_POLY_enclosure, "CONT.EN.2", "Poly enclosure of contact violation: min = 0.03um");

// ----------------------------------------------------------------------------
// METAL1 RULES
// ----------------------------------------------------------------------------

// METAL1.W.1: Minimum width of metal1
METAL1_width = width(METAL1) < 0.09;
drc_deck(METAL1_width, "METAL1.W.1", "Metal1 minimum width violation: min = 0.09um");

// METAL1.S.1: Minimum spacing between metal1 wires
METAL1_spacing = external_distance(METAL1, METAL1) < 0.09;
drc_deck(METAL1_spacing, "METAL1.S.1", "Metal1 minimum spacing violation: min = 0.09um");

// METAL1.EN.1: Minimum metal1 enclosure of contact
METAL1_CONT_enclosure = external_enclosure(METAL1, CONTACT) < 0.01;
drc_deck(METAL1_CONT_enclosure, "METAL1.EN.1", "Metal1 enclosure of contact violation: min = 0.01um");

// ----------------------------------------------------------------------------
// VIA1 RULES
// ----------------------------------------------------------------------------

// VIA1.W.1: Via must be square with exact dimension
VIA1_width = width(VIA1) != 0.07;
drc_deck(VIA1_width, "VIA1.W.1", "Via1 width must be exactly 0.07um");

// VIA1.S.1: Minimum spacing between vias
VIA1_spacing = external_distance(VIA1, VIA1) < 0.09;
drc_deck(VIA1_spacing, "VIA1.S.1", "Via1 spacing violation: min = 0.09um");

// VIA1.EN.1: Minimum metal1 enclosure of via1
VIA1_M1_enclosure = external_enclosure(METAL1, VIA1) < 0.01;
drc_deck(VIA1_M1_enclosure, "VIA1.EN.1", "Metal1 enclosure of Via1 violation: min = 0.01um");

// ----------------------------------------------------------------------------
// METAL2 RULES
// ----------------------------------------------------------------------------

// METAL2.W.1: Minimum width of metal2
METAL2_width = width(METAL2) < 0.10;
drc_deck(METAL2_width, "METAL2.W.1", "Metal2 minimum width violation: min = 0.10um");

// METAL2.S.1: Minimum spacing between metal2 wires
METAL2_spacing = external_distance(METAL2, METAL2) < 0.10;
drc_deck(METAL2_spacing, "METAL2.S.1", "Metal2 minimum spacing violation: min = 0.10um");

// METAL2.EN.1: Minimum metal2 enclosure of via1
VIA1_M2_enclosure = external_enclosure(METAL2, VIA1) < 0.015;
drc_deck(VIA1_M2_enclosure, "METAL2.EN.1", "Metal2 enclosure of Via1 violation: min = 0.015um");

// ----------------------------------------------------------------------------
// WELL RULES
// ----------------------------------------------------------------------------

// NWELL.W.1: Minimum width of nwell
NWELL_width = width(NWELL) < 0.84;
drc_deck(NWELL_width, "NWELL.W.1", "Nwell minimum width violation: min = 0.84um");

// NWELL.S.1: Minimum spacing between nwell regions
NWELL_spacing = external_distance(NWELL, NWELL) < 1.27;
drc_deck(NWELL_spacing, "NWELL.S.1", "Nwell minimum spacing violation: min = 1.27um");

// WELL.S.1: Nwell and Pwell must not overlap
WELL_overlap = NWELL and PWELL;
drc_deck(WELL_overlap, "WELL.S.1", "Nwell and Pwell overlap violation");

// ----------------------------------------------------------------------------
// DENSITY RULES (Advanced)
// ----------------------------------------------------------------------------

// METAL1.D.1: Metal1 density check
// Density must be between 20% and 80% in any 100um x 100um window
METAL1_density_low = density(METAL1, 100.0, 100.0) < 0.20;
drc_deck(METAL1_density_low, "METAL1.D.1", "Metal1 density too low: min = 20%");

METAL1_density_high = density(METAL1, 100.0, 100.0) > 0.80;
drc_deck(METAL1_density_high, "METAL1.D.2", "Metal1 density too high: max = 80%");

// ----------------------------------------------------------------------------
// WIDTH-DEPENDENT SPACING RULES (Advanced)
// ----------------------------------------------------------------------------

// METAL2.S.2: Width-dependent spacing for metal2
// If metal2 width > 1.0um, spacing must be >= 0.20um
METAL2_wide = sized_rectangles(METAL2, x > 1.0 || y > 1.0);
METAL2_wide_spacing = external_distance(METAL2_wide, METAL2) < 0.20;
drc_deck(METAL2_wide_spacing, "METAL2.S.2", "Wide Metal2 spacing violation: min = 0.20um for width > 1.0um");

// ----------------------------------------------------------------------------
// ANTENNA RULES
// ----------------------------------------------------------------------------

// ANT.1: Antenna ratio check for poly
// Ratio of poly area to gate area must be < 400
POLY_antenna = antenna_ratio(POLY, DIFF, "area") > 400;
drc_deck(POLY_antenna, "ANT.1", "Poly antenna violation: ratio > 400");

// ============================================================================
// CONDITIONAL RULES USING #ifdef
// ============================================================================

#ifdef CUSTOM_RULES
    // Custom rules that can be enabled with -D CUSTOM_RULES

    // Custom spacing rule
    DIFF_custom_spacing = external_distance(DIFF, DIFF) < 0.20;
    drc_deck(DIFF_custom_spacing, "DIFF.S.CUSTOM", "Custom diffusion spacing: min = 0.20um");

#endif

// ============================================================================
// END OF DRC DECK
// ============================================================================
