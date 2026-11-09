# BLANK_MODEL.FCStd - the kit's blank FreeCAD document (31bv B1)

Built once by the kit's own delivery surgery (`kit_deliver.build`) from a GUI-saved delivery: every body, mesh and reference dropped with its payload, the
structure kept, every label written generically. A project's first delivery starts from it (`PROJECT_START.md` 2). Everything in it except the six groups (G0 the palette, G1-G5) is
an EXAMPLE and says so in its label: the placeholder body is replaced by the project's first body, the two marker blocks are copied and moved where a region is
marked, the four colour shapes only carry the named colours. Nothing in it belongs to any project.

| object | group (its label) | what |
|---|---|---|
| `PLACEHOLDER_BODY` (shown) | G1_PRINT (`1  THE PART - the model of record, what the project makes`) | an example body, a 60 x 40 x 5 plate, that the first body REPLACES: `kit deliver R01 --no-review "the first body - nothing to review against" --template <this file> --target PLACEHOLDER_BODY --model <brep>` (the placeholder then takes the body's own name) |
| `MARKER_BOX`, `MARKER_PYRAMID` (hidden) | G4_MARKERS (`4  MARKER BLOCKS`) | two example marker blocks (red, transparent) - a region to cut or copy out of an assembly is marked by placing copies of these |
| `COLOUR_PRINT` box, `COLOUR_ASSEMBLY` cylinder, `COLOUR_REFERENCE` sphere, `COLOUR_MARKER` wedge (hidden) | G0_PALETTE (`0  NAMED COLOURS`) | four example shapes, one per named colour, the colour in each label: a body the project makes 204,204,204 (light grey); a purchased or assembly part 140,166,204 (steel blue); a reference - a scan, a datum, a measured part - 204,184,140 (sand); a marker block 230,51,51 (red) |
| (empty) | G2_ASSEMBLY (`2  ASSEMBLY CONTEXT`), G3_REFERENCE (`3  REFERENCE`), G5_SOURCE (`5  SOURCE`) | where `--add-body` / `--mesh` specs put the parts around the model, the references and the inputs a delivery was made from; a group the template keeps hidden is shown when a shown body goes into it (said at the delivery) |

The colours are `ShapeColor` properties (the form FreeCAD's GUI paints - `HOW_TO_DELIVER_A_COLOURED_MODEL.md`); `kit deliverycheck <this file> --no-review "<why>"` passes on it.
What is NOT acceptance: a headless check. The client's look in the GUI is.
