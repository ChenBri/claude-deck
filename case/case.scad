// claude-deck enclosure. Provisional: per DECISIONS.md #49/#52, the real
// fabrication file gets cut after the electronics arrive and every cutout
// can be measured against the real part. This is a visualization model,
// dimensions from docs/BOM.md and docs/HARDWARE.md where they exist, sane
// standard-part sizes and my own judgement where they don't - flagged
// inline wherever that's the case. Retro terminal look per DECISIONS.md
// #39: no reference image was given, so the proportions here are a first
// design pass, not a locked shape.
//
// Stage 1 of this file: the outer shell silhouette only, solid, no wall
// thickness and no cutouts yet - just to check the overall proportions
// read as "retro terminal" before building anything on top of it.

/* [Case envelope] */
// Overall width. DECISIONS.md #40 says 160mm, but #53 (joystick) and #55
// (Game Boy buttons) both already flagged this as likely needing to grow;
// starting from that grown number rather than the original.
case_width      = 170;
// Total footprint, front to back.
case_depth      = 120;
// Total height at the tallest point (the rear face).
case_height     = 100;

/* [Control deck] */
// How far the sloped control deck projects forward, per #40's "55mm deep".
deck_depth        = 55;
// Height of the low front lip, where the deck's leading edge sits.
deck_front_height = 12;
// Height where the deck meets the base of the rear vertical face - this is
// the comfortable reach height for the rotary switch, encoder, joystick
// etc. Not specified in DECISIONS.md; chosen for a gentle, comfortable
// slope rather than to hit the letter of "upper face 95mm" (see note below).
deck_back_height  = 52;

/* [Rear face] */
// NOTE on #40: "Upper face 95mm, deck 55mm deep" doesn't fully resolve
// geometrically once the deck has to rise to a usable knob height - a 95mm
// face plus a deck rising to anywhere above a few mm would overshoot the
// 100mm case height. This model treats deck_back_height as the real
// constraint (ergonomics) and lets the rear face be whatever's left above
// it, rather than forcing exactly 95mm. Flagging this rather than quietly
// picking one: happy to redo it either way once you've seen this.
rear_face_depth = 30; // the rear face's own footprint depth, holds the display/electronics stack

/* [Rendering] */
$fn = 48;

module shell_silhouette() {
    front_apron_depth = case_depth - rear_face_depth - deck_depth;
    y1 = front_apron_depth;       // deck's front edge
    y2 = y1 + deck_depth;         // deck's back edge / rear face's front surface

    profile = [
        [0, 0],
        [0, deck_front_height],
        [y1, deck_front_height],       // flat low apron in front of the deck
        [y2, deck_back_height],        // sloped deck
        [y2, case_height],             // up the rear face
        [case_depth, case_height],     // flat top
        [case_depth, 0],               // down the back wall
    ];

    rotate([90, 0, 90])
        linear_extrude(height = case_width)
            polygon(profile);
}

shell_silhouette();
