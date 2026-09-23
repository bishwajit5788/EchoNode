// ==============================================================================
// EchoNode - Bedside Audio Device 3D Printable Enclosure
// Target Board: Waveshare ESP32-S3 1.85-inch Round Display (360x360)
// Battery: KP Original 702635 600mAh LiPo (7mm x 26mm x 35mm)
// Acoustics: Dual 8-ohm micro-speakers with dedicated acoustic resonance chambers
// ==============================================================================

$fn = 90; // High resolution curves

// Part to render: "both", "top", "bottom", "exploded"
part = "both"; 

// --- Primary Dimensions (in mm) ---
case_od            = 82.0;  // Outer diameter of the bedside puck
case_height_top    = 16.0;  // Top shell height
case_height_bottom = 18.0;  // Bottom shell height
wall_thickness     = 2.4;   // Rigid outer shell thickness

// Display Aperture (Waveshare 1.85" round screen)
lcd_glass_dia      = 54.0;  // Active display + bezel diameter
lcd_view_dia       = 48.0;  // Viewable circular window
lcd_recess_depth   = 2.0;   // Seating step depth

// Battery Bay (KP Original 702635 600mAh LiPo: 7.0 x 26.0 x 35.0 mm)
batt_x             = 28.0;  // Margin + clearance
batt_y             = 37.0;
batt_z             = 8.0;

// Dual Speaker Chambers (15mm x 24mm micro-speakers)
spk_width          = 16.0;
spk_length         = 25.0;
spk_depth          = 6.5;

// Cutouts & Fasteners
usbc_w             = 10.0;
usbc_h             = 4.5;
sd_w               = 13.0;
sd_h               = 2.5;
screw_post_dia     = 6.0;
screw_hole_dia     = 2.2;   // For M2 self-tapping or heat-set insert

// ==============================================================================
// TOP SHELL MODULE
// ==============================================================================
module top_shell() {
    difference() {
        // Outer Body with smooth chamfered lip
        union() {
            cylinder(h = case_height_top - 2, d = case_od);
            translate([0, 0, case_height_top - 2])
                cylinder(h = 2, d1 = case_od, d2 = case_od - 4);
        }

        // Inner Cavity
        translate([0, 0, -1])
            cylinder(h = case_height_top - wall_thickness + 1, d = case_od - (wall_thickness * 2));

        // Circular Display Window (Aperture through the top)
        translate([0, 0, -1])
            cylinder(h = case_height_top + 3, d = lcd_view_dia);

        // Circular Display Recessed Rim (Seats the round glass/bezel flush)
        translate([0, 0, case_height_top - lcd_recess_depth])
            cylinder(h = lcd_recess_depth + 1, d = lcd_glass_dia);

        // Acoustic Grille Ports (Left & Right micro-speaker sound slits)
        for (side = [-1, 1]) {
            translate([side * (case_od / 2 - wall_thickness - 1), 0, case_height_top / 2]) {
                for (slot = [-10:4:10]) {
                    translate([0, slot, 0])
                        rotate([0, 90, 0])
                            cylinder(h = wall_thickness * 2 + 2, d = 1.6, center = true);
                }
            }
        }
    }

    // Screw Mounting Bosses (4x symmetrical alignment pillars)
    for (a = [45, 135, 225, 315]) {
        rotate([0, 0, a]) {
            translate([(case_od / 2) - wall_thickness - 4, 0, 0]) {
                difference() {
                    cylinder(h = case_height_top - wall_thickness, d = screw_post_dia);
                    cylinder(h = case_height_top, d = screw_hole_dia);
                }
            }
        }
    }

    // PCB Support Ledge for Waveshare Round Board
    difference() {
        translate([0, 0, case_height_top - lcd_recess_depth - 3.5])
            cylinder(h = 2.0, d = lcd_glass_dia + 4);
        translate([0, 0, case_height_top - lcd_recess_depth - 4])
            cylinder(h = 4.0, d = lcd_glass_dia - 1.5);
    }
}

// ==============================================================================
// BOTTOM SHELL MODULE
// ==============================================================================
module bottom_shell() {
    difference() {
        // Base Cylinder
        cylinder(h = case_height_bottom, d = case_od);

        // Internal Cavity
        translate([0, 0, wall_thickness])
            cylinder(h = case_height_bottom + 1, d = case_od - (wall_thickness * 2));

        // USB-C Charging & Programming Port Cutout
        translate([0, -(case_od / 2 + 1), wall_thickness + 3])
            cube([usbc_w, wall_thickness * 2 + 2, usbc_h], center = true);

        // MicroSD Access Slot (Opposite side)
        translate([0, (case_od / 2 + 1), wall_thickness + 3])
            cube([sd_w, wall_thickness * 2 + 2, sd_h], center = true);

        // Fastener Counter-Bores on the bottom exterior
        for (a = [45, 135, 225, 315]) {
            rotate([0, 0, a]) {
                translate([(case_od / 2) - wall_thickness - 4, 0, -1]) {
                    cylinder(h = wall_thickness + 2, d = screw_hole_dia + 0.4);
                    cylinder(h = 2.0, d = 4.5); // Screw head recess
                }
            }
        }
    }

    // Battery Isolation Tray (Prevents LiPo pressure against PCB & bedding)
    translate([0, 0, wall_thickness]) {
        difference() {
            translate([-batt_x / 2 - 1.2, -batt_y / 2 - 1.2, 0])
                cube([batt_x + 2.4, batt_y + 2.4, batt_z]);
            translate([-batt_x / 2, -batt_y / 2, 0])
                cube([batt_x, batt_y, batt_z + 1]);
            // Wire clearance pass-through
            translate([0, batt_y / 2, batt_z / 2])
                cube([6, 4, batt_z + 1], center = true);
        }
    }

    // Dual Speaker Mounting Brackets
    for (side = [-1, 1]) {
        translate([side * (case_od / 2 - spk_width / 2 - wall_thickness - 2), 0, wall_thickness]) {
            difference() {
                translate([-spk_width / 2 - 1, -spk_length / 2 - 1, 0])
                    cube([spk_width + 2, spk_length + 2, spk_depth]);
                translate([-spk_width / 2, -spk_length / 2, 0])
                    cube([spk_width, spk_length, spk_depth + 1]);
            }
        }
    }

    // Screw Bosses on Bottom Shell
    for (a = [45, 135, 225, 315]) {
        rotate([0, 0, a]) {
            translate([(case_od / 2) - wall_thickness - 4, 0, wall_thickness]) {
                difference() {
                    cylinder(h = case_height_bottom - wall_thickness, d = screw_post_dia);
                    cylinder(h = case_height_bottom, d = screw_hole_dia);
                }
            }
        }
    }
}

// ==============================================================================
// RENDER SELECTOR
// ==============================================================================
if (part == "top") {
    top_shell();
} else if (part == "bottom") {
    bottom_shell();
} else if (part == "exploded") {
    translate([0, 0, case_height_bottom + 15])
        top_shell();
    bottom_shell();
} else {
    // Both side-by-side for print bed layout
    translate([-case_od / 2 - 5, 0, 0])
        bottom_shell();
    translate([case_od / 2 + 5, 0, 0])
        rotate([180, 0, 0])
            translate([0, 0, -case_height_top])
                top_shell();
}
