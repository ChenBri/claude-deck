// claude-deck enclosure. Provisional: per DECISIONS.md #49/#52, the real
// fabrication file gets cut after the electronics arrive and every cutout
// can be measured against the real part. This is a visualization model,
// dimensions from docs/BOM.md and docs/HARDWARE.md where they exist, sane
// standard-part sizes and my own judgement where they don't - flagged
// inline wherever that's the case. Retro terminal look per DECISIONS.md
// #39: no reference image was given, so the proportions here are a first
// design pass, not a locked shape.
//
// Stage 2: every cutout (front face, control deck, back panel) plus
// simple stand-in geometry for the knobs/keycaps/knobs so it reads as a
// real control panel and not just a box with holes. Still solid (no wall
// thickness / hollow interior yet) - that's the next pass once this
// layout is confirmed, since it doesn't change anything visible from
// outside.
//
// Stage 3: real-world scale check. 180x100 (was 170x100, was 160x100)
// turned out to be a bare-minimum-clearance number, not a comfortable
// one - adding up genuine finger-clearance between every cluster (not
// just "doesn't overlap") came to roughly 250-280mm wide once actually
// totalled up. Rebuilt at 260x150 with every position redone for real
// spacing, agreed on directly rather than another round of reactive
// single-mm growth.
//
// Stage 4 (superseded by stage 5 below): briefly tried a 4.0in 480x320
// SPI panel at 260x180. Turned out "260mm width, 150-220mm height" was
// describing the SCREEN Chen wanted, not the case - a screen that size
// is a real 11.6in monitor-class panel, not an SPI TFT at all.
//
// Stage 5: 11.6in 1366x768 HDMI panel, 257x144mm active area (real
// laptop-panel size, HDMI + driver board, common and cheap). This is
// a different display interface, not just a bigger hole - SPI is out,
// HDMI is in; firmware/deck/ui/render.py's OUTPUT_WIDTH/HEIGHT and
// firmware/deck/panel/sim.py's window size move with it, and
// docs/HARDWARE.md's SPI0 pin reservations for the display go away.
//
// A screen this wide also eats nearly the entire reasonable case
// width on its own, so the meters/lamps/legend no longer fit beside
// it the way the small display's did - they moved to a row below the
// screen instead. Case grew to 300x290 to hold the screen, that row,
// and a bit of real bezel margin around each.

/* [Case envelope] */
case_width      = 300;   // was 260; the screen alone is 257mm wide
case_depth      = 130;   // was 120; a driver board needs a bit more housing depth than the old SPI TFT
case_height     = 290;   // was 180; screen (144mm) + the meter/lamp/legend row now stacks below it

/* [Control deck] */
deck_depth        = 55;
deck_front_height = 10;
deck_back_height  = 40;  // unchanged - this is about reach ergonomics, not screen size

/* [Rear face] */
rear_face_depth = 40;   // was 30; more room behind the panel for the HDMI driver board

/* [Rendering] */
$fn = 32;

// ============================================================
// Derived geometry
// ============================================================
front_apron_depth = case_depth - rear_face_depth - deck_depth;
y1 = front_apron_depth;              // deck's front edge, along the depth axis
y2 = y1 + deck_depth;                // deck's back edge = rear face's front plane
face_height = case_height - deck_back_height;
slope_rise   = deck_back_height - deck_front_height;
slope_angle  = atan2(slope_rise, deck_depth);   // degrees above horizontal
slope_length = sqrt(deck_depth * deck_depth + slope_rise * slope_rise);

CUT = 200; // oversized cutter dimension, sliced away by later intersections where needed

// ============================================================
// Small helpers
// ============================================================
module rounded_rect(w, h, r) {
    hull()
        for (dx = [-1, 1]) for (dy = [-1, 1])
            translate([dx * (w / 2 - r), dy * (h / 2 - r)])
                circle(r = r);
}

// Places children on the sloped deck. Local (x, s, z): x is across the
// case width (unchanged by the slope), s is distance up the slope from
// its front edge, z is height above the deck surface (its normal).
module on_deck(x, s, z = 0) {
    translate([x, y1, deck_front_height])
        rotate([slope_angle, 0, 0])
            translate([0, s, z])
                children();
}

// Places children on the rear vertical face. Local (x, z) match world
// X and Z; the face's own plane is at world Y = y2.
module on_face(x, z) {
    translate([x, y2, z])
        children();
}

// A cutter cylinder driven straight through the rear face (+Y).
module face_hole(d, h = CUT) {
    rotate([-90, 0, 0])
        cylinder(d = d, h = h, $fn = 48);
}

// A cutter cylinder driven straight through the deck, along its normal.
module deck_hole(d, h = CUT) {
    translate([0, 0, -h / 2])
        cylinder(d = d, h = h, $fn = 48);
}

module deck_square_hole(w, h_cut = CUT) {
    translate([0, 0, -h_cut / 2])
        linear_extrude(height = h_cut)
            square([w, w], center = true);
}

// ============================================================
// Outer shell (still solid - wall thickness is the next pass)
// ============================================================
module shell_silhouette() {
    profile = [
        [0, 0],
        [0, deck_front_height],
        [y1, deck_front_height],
        [y2, deck_back_height],
        [y2, case_height],
        [case_depth, case_height],
        [case_depth, 0],
    ];
    rotate([90, 0, 90])
        linear_extrude(height = case_width)
            polygon(profile);
}

// ============================================================
// Front face: display bezel, halo groove, meter/lamp/legend row
// ============================================================
// Real 11.6in 1366x768 HDMI panel active area (DECISIONS.md #20).
// Was 2.4in 320x240 (49x37mm), briefly 4.0in 480x320 (85x56mm) -
// this is a different display interface (HDMI, not SPI), not just a
// bigger hole; see the stage 5 note above.
display_w = 257;
display_h = 144;
display_x = case_width / 2;

halo_margin = 15;      // groove sits this far outside the bezel opening
halo_groove_w = 4;
halo_groove_depth = 1.5;

// Screen sits in the upper part of the face, with a 12mm margin to
// the case top; everything else lives in a row below it, since a
// screen this wide leaves no room to flank it the way the small
// display's meters/lamps used to.
display_z = case_height - 12 - halo_margin - display_h / 2;

row_z = display_z - display_h / 2 - halo_margin - 12 - 20;   // meters + lamps row, below the halo
legend_z = deck_back_height + 7;                              // legend strip, near the bottom of the face

lamp_dia = 5;          // a real part size (BOM: chrome 5mm bezel holders), not grown
lamp_count = 5;
lamp_pitch = 20;
lamp_z = row_z;

meter_dia = 34;        // a real part size (BOM: Kaisaya 34mm meter), not grown
meter_offset_x = 100;   // either side of the display centreline, within the row below the screen
meter_z = row_z;

legend_w = 180;
legend_h = 9;
legend_depth = 1.5;

module front_face_cuts() {
    // display: rectangular, not round - cut directly rather than via face_hole()
    translate([display_x, y2 - 1, display_z])
        rotate([-90, 0, 0])
            linear_extrude(height = CUT)
                square([display_w, display_h], center = true);

    // halo groove: a shallow rounded-rect ring around the bezel opening
    translate([display_x, y2 - halo_groove_depth, display_z])
        rotate([-90, 0, 0])
            linear_extrude(height = halo_groove_depth + 0.01)
                difference() {
                    rounded_rect(display_w + 2 * halo_margin, display_h + 2 * halo_margin, 10);
                    rounded_rect(display_w + 2 * halo_margin - halo_groove_w, display_h + 2 * halo_margin - halo_groove_w, 9);
                }

    // lamps: READY WORKING BLOCKED DONE LINK, centred in the row below the screen
    for (i = [0 : lamp_count - 1])
        on_face(display_x + (i - (lamp_count - 1) / 2) * lamp_pitch, lamp_z)
            face_hole(lamp_dia);

    // meters: CONTEXT (left), FIVE_HOUR (right), same row as the lamps
    on_face(display_x - meter_offset_x, meter_z) face_hole(meter_dia);
    on_face(display_x + meter_offset_x, meter_z) face_hole(meter_dia);

    // legend strip: shallow backlit recess, not a through-hole
    translate([display_x, y2 - legend_depth, legend_z])
        rotate([-90, 0, 0])
            linear_extrude(height = legend_depth + 0.01)
                rounded_rect(legend_w, legend_h, 2);
}

// ============================================================
// Control deck: rotary, encoder, mech keys, toggles, joystick,
// Game Boy buttons, APPROVE/DENY, panic
// ============================================================
rotary_dia   = 10;
encoder_dia  = 7.5;
mech_key_cut = 14;
toggle_dia   = 6.5;
joystick_cut = 26;
approve_deny_dia = 19.2;
panic_dia    = 22;
gb_button_cut = 14;

// back row: nearer the rear face, for "set once" controls
back_row_s = slope_length - 12;
mech_key_x = [95, 117, 139, 161];   // 22mm pitch: a real ~7mm gap around a 15mm keycap
toggle_x   = [190, 210, 230];       // 20mm pitch

// front row: nearer the front edge, for hands-on controls
front_row_s = 22;

module deck_cuts() {
    on_deck(30, back_row_s) deck_hole(rotary_dia);
    on_deck(65, back_row_s) deck_hole(encoder_dia);
    for (x = mech_key_x) on_deck(x, back_row_s) deck_square_hole(mech_key_cut);
    for (x = toggle_x)   on_deck(x, back_row_s) deck_hole(toggle_dia);

    on_deck(35, front_row_s) deck_square_hole(joystick_cut);

    // Game Boy buttons: A upper-right / B lower-left of each other,
    // START/SELECT a smaller pair alongside - same relative layout as
    // firmware/deck/panel/sim.py's drawn mockup. Real spacing now: a
    // 14mm cut never gets closer than a ~20mm centre distance.
    on_deck(120, front_row_s + 10) deck_square_hole(gb_button_cut); // A
    on_deck(100, front_row_s - 10) deck_square_hole(gb_button_cut); // B
    on_deck(135, front_row_s - 6)  deck_square_hole(gb_button_cut); // SELECT
    on_deck(155, front_row_s - 6)  deck_square_hole(gb_button_cut); // START

    on_deck(195, front_row_s) deck_hole(approve_deny_dia);
    on_deck(222, front_row_s) deck_hole(approve_deny_dia);
    on_deck(244, front_row_s) deck_hole(panic_dia);
}

// ============================================================
// Back panel: USB-C, barrel jack, rocker switch, SD card slot
// ============================================================
usbc_w = 10; usbc_h = 4;
barrel_dia = 12;
rocker_dia = 20;   // KCD1 is really a rounded-rect "boat" shape; round is a simplification for now
sd_slot_w = 15; sd_slot_h = 3;

back_panel_z = (deck_back_height + case_height) / 2; // mid-height of the rear face's back side

module back_panel_cuts() {
    translate([50, case_depth - CUT / 2, back_panel_z])
        rotate([-90, 0, 0])
            linear_extrude(height = CUT)
                square([usbc_w, usbc_h], center = true);

    translate([110, case_depth - CUT / 2, back_panel_z])
        rotate([-90, 0, 0])
            cylinder(d = barrel_dia, h = CUT, $fn = 48);

    translate([170, case_depth - CUT / 2, back_panel_z])
        rotate([-90, 0, 0])
            cylinder(d = rocker_dia, h = CUT, $fn = 48);

    translate([230, case_depth - CUT / 2, back_panel_z])
        rotate([-90, 0, 0])
            linear_extrude(height = CUT)
                square([sd_slot_w, sd_slot_h], center = true);
}

// ============================================================
// Stand-in caps/knobs, so this reads as a control panel and not just
// a box with holes in it. Purely cosmetic, not real part geometry.
// ============================================================
module knob(dia, height) {
    color("Silver") cylinder(d = dia, h = height, $fn = 32);
}

module keycap(w, height) {
    color("DarkOrange") cube([w, w, height], center = true);
}

module deck_decor() {
    on_deck(30, back_row_s) translate([0,0,0]) knob(20, 12);
    on_deck(65, back_row_s) knob(14, 10);
    for (x = mech_key_x) on_deck(x, back_row_s) translate([0, 0, 2]) keycap(mech_key_cut + 1, 4);
    on_deck(120, front_row_s + 10) translate([0, 0, 2]) keycap(gb_button_cut + 1, 4);
    on_deck(100, front_row_s - 10) translate([0, 0, 2]) keycap(gb_button_cut + 1, 4);
    on_deck(135, front_row_s - 6)  translate([0, 0, 2]) keycap(gb_button_cut + 1, 4);
    on_deck(155, front_row_s - 6)  translate([0, 0, 2]) keycap(gb_button_cut + 1, 4);
    // APPROVE/DENY/panic decor caps dropped: they render invisible under
    // --render specifically (a color/CGAL quirk I couldn't pin down, not
    // a geometry problem) while sitting a few lines from a working knob().
    // The holes themselves are correctly cut either way.
    on_deck(35, front_row_s) color("DarkOrange") translate([0, 0, 6]) sphere(d = 12, $fn = 24);
}

// ============================================================
// Assemble
// ============================================================
difference() {
    shell_silhouette();
    front_face_cuts();
    deck_cuts();
    back_panel_cuts();
}
deck_decor();
