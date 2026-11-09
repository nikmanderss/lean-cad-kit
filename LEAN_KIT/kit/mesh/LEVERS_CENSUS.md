# LEVER CENSUS - every environment-variable lever the scripts in this folder read (generated; the `class` and `note` columns are yours)

**Fill `class` for every row: `CARD`, `CONSTANT` or `DEAD`.** Nothing else in the process reads the code's default as
an answer once this is done: `kit mesh` refuses a step whose CARD levers are not set for the run, by name.

* **CARD** - a number a card decides (it differs per card, piece or region). It must be SET for every run - in the
  run's env file or `--set` - and the value in the example file is the example's decision, not yours.
* **CONSTANT** - an algorithm constant no card changes. The code default IS the value; write why in `note`.
* **DEAD** - read only by scripts that are not in the chain (`in chain` = no) and are not run. Say so in `note`;
  the script is a candidate for removal.
* `in chain` = no means only scripts outside the canonical chain read it; the note names them. Whether they
  are the round's live drivers or dead ends is the classifier's call - the census states the fact and proposes nothing.

`kit levers --check` lists what is still unclassified and which CARD levers the example file sets. Re-run
`kit levers --census` after the scripts change: it keeps every class already given and adds the new rows.

Classified by the kit maintainer, 2026-09-24, from the agent's notes (NOTES_FOR_KIT 2.9, 3a-3c) and a project's extract script, whose
19 hard-coded `--set`s were "V2's accepted recipe" - the default taken as the answer the client forbade (2026-09-17). Every one of
them is CARD here: a project keeps them in an env file it passes with `--env` (the EXAMPLE CASE, named as such), never in
a wrapper and never in the code. "CONSTANT-off" = a specialty lever that is off unless the card turns it on (the agent 2.9).

| lever | default in code | read by | in chain | set by example | class | note |
|---|---|---|---|---|---|---|
| `CC_ABSORB` | `"0.5"` | `_blobcore.py` | yes | no | CONSTANT | reproduction error the seam absorbs (recipe 0.3 via --set; the code's 0.5 is the loose bound) |
| `CC_ADDONLY` | `"0"` | `_ccextract.py` | yes | no | CARD | 1 for every FILL (L79, R1); 0 only where the card says it trims |
| `CC_ADDONLY_BOXES` | `""` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: add-only inside listed boxes only, when the card names them |
| `CC_ALLOW` | `-` | `_blobcore.py` | yes | no | CONSTANT | CONSTANT-off: an allowance the card states |
| `CC_ALLOW_UNREVIEWED` | `-` | `_collect.py` | yes | no | CONSTANT | CONSTANT-off: trial assemblies only, never the delivery (the client 2026-09-23) |
| `CC_ATLAS` | `""` | `_ccdeliver_zip.py` | yes | no | CONSTANT | filled by kit mesh from the project's atlas |
| `CC_ATLAS_MANIFEST` | `""` | `_ccextract.py` | yes | no | CONSTANT | filled by kit mesh from the atlas record; name it when the atlas carries none |
| `CC_BAND` | `"4.0"` | `_ccextract.py` | yes | no | CARD | band at the box walls; >= a quarter of the smallest box dimension, never under 3 (measured) |
| `CC_BASE` | `""` | `_blobcore.py`, `_final.py`, `_finalgates.py` | yes | no | CARD | the crop (core) / the one unchanged base (final, gates) - a path, per run |
| `CC_BASE_OK` | `""` | `_ccweld.py` | yes | no | CONSTANT | CONSTANT-off: a base accepted by name; a crop or a refined crop needs none |
| `CC_BLOB` | `-` | `_blobgrow.py`, `_islandgrow.py` | yes | no | CARD | the core to grow - a path, per run |
| `CC_BLOBS` | `""` | `_ccrefine.py` | yes | no | CARD | the core(s) whose walls refine the base - paths, per run |
| `CC_BODY` | `-` | `_ccrefine.py`, `_ccweld.py` | yes | no | CARD | the base: the crop (refine) / the refined crop (weld) - a path, per run |
| `CC_BOX` | `-` | `_blobcore.py`, `_ccextract.py`, `_ccthin.py` | yes | no | CARD | the extract box (R3-R5, R9) |
| `CC_CHAIN_OK` | `""` | `_ccweld.py` | yes | no | CONSTANT | CONSTANT-off: the client's words when the client allows a chained base (L12) |
| `CC_CLOSE` | `"1.2"` | `_ccextract.py` | yes | no | CARD | fills gaps under 2x it; lower it beside openings (recipe 1.2) |
| `CC_CORES` | `""` | `_ccrefine.py` | yes | no | CONSTANT | CONSTANT-off: analytic cores; the route uses edit-zone blobs |
| `CC_CORE_BLOB` | `""` | `_ccweld.py` | yes | no | CARD | the edit-zone core - a path, per run |
| `CC_CORE_CEN` | `-` | `_ccweld.py` | yes | no | CONSTANT | ellipsoid-core era; set "0 0 0" when a blob is given (the blob's box overrides) |
| `CC_CORE_RAD` | `-` | `_ccweld.py` | yes | no | CONSTANT | ellipsoid-core era; set "1 1 1" when a blob is given |
| `CC_CORE_ROUND` | `"0"` | `_ccweld.py` | yes | no | CONSTANT | ellipsoid-core era; 0 with a blob |
| `CC_DECERR` | `"0.04"` | `_ccweld.py` | yes | no | CARD | mm the patch decimation may move the surface (recipe 0.02) |
| `CC_DECIM` | `"0.0"` | `_ccweld.py` | yes | no | CARD | patch decimation fraction (recipe 0.55; 0 = none) |
| `CC_DEV` | `"0.02"` | `_ccexport_regions.py`, `_ccextract.py`, `_ccrefine.py`, `_ccweld.py` | yes | no | CARD | tessellation deflection; recipe 0.08 for the body, 0.02 for region exports |
| `CC_DRY` | `-` | `_ccneedle.py` | yes | no | CONSTANT | CONSTANT-off: report without cutting |
| `CC_DUMP_BASE` | `""` | `_ccweld.py` | yes | no | CONSTANT | CONSTANT-off: re-write an STL base beside the run (the agent 2.12: 3.2 GB in one round) |
| `CC_DUMP_PARTS` | `-` | `_ccweld.py` | yes | no | CONSTANT | CONSTANT-off: diagnosis halves |
| `CC_EDITBOX` | `""` | `_ccextract.py` | yes | no | CARD | where cleaning is allowed ("b1; b2" = a union); empty = the whole box, said on purpose |
| `CC_EDITBOXRAMP` | `"1.0"` | `_ccextract.py` | yes | no | CARD | ramp inside the edit box faces (recipe 1.0; boxes under 2x ramp never reach full weight - R3) |
| `CC_EDITED_EPS` | `"0.02"` | `_ccextract.py` | yes | no | CONSTANT | the zone model's threshold (the agent diagnosis 2026-09-22) |
| `CC_EDITRAMP` | `"1.0"` | `_ccextract.py` | yes | no | CONSTANT | ramp of the reach mask |
| `CC_EDITREACH` | `"0"` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: the reach mask is driven by the lump choice, not a radius |
| `CC_EXTENT` | `""` | `_ccrefine.py`, `_ccspikes.py`, `_final.py`, `_finalgates.py` | yes | no | CONSTANT | filled by kit mesh: the union of the atlas boxes (no project number in the kit) |
| `CC_FCSTD` | `-` | `_guiload.py` | yes | no | CARD | the file to load - a path, per run |
| `CC_FEATANG` | `"50.0"` | `_ccweld.py` | yes | no | CONSTANT | feature-edge angle of the smoother |
| `CC_FINAL_OUT` | `-` | `_final.py` | yes | no | CONSTANT | default <work>\final; a trial names its own folder |
| `CC_FREEZE_REGIONS` | `""` | `_ccextract.py` | yes | no | CARD | every frozen atlas region within 5 mm of the box (R2); empty only when there is none, said |
| `CC_GATE_BOX` | `-` | `_ccextract.py` | yes | no | CARD | where the reinsertion gate measures (edit box + ~3 mm); it must reach the extract box walls (R23) |
| `CC_GROW` | `"0"` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: route A2 (grow and union, 2026-09-25) - > 0 writes a COPY for `kit union`, grown this many mm x the edit weight (trial value 0.25, not yet run); the reinsertion gate becomes report-only and SNAP is skipped; a grown copy is never welded |
| `CC_GROW_SHRINK` | `"0.15"` | `_ccextract.py` | yes | no | CONSTANT | with CC_GROW only: mm the copy is shrunk inside the body x (1 - edit weight) - walls, frozen and keeper surfaces - so the union never meets it on a coincident surface; must be > 0 (refused otherwise); raise it if the union shows slivers where the copy crosses the body |
| `CC_H` | `"0.15"` | `_ccextract.py` | yes | no | CARD | coarse cell (recipe 0.18) |
| `CC_HALO` | `"6.0"` | `_ccextract.py` | yes | no | CONSTANT | distance-query halo round the grid |
| `CC_HARD` | `"0.50"` | `_ccthin.py` | yes | no | CONSTANT | the process minimum wall (MJF) |
| `CC_HFINE` | `"0"` | `_ccextract.py` | yes | no | CARD | fine cell for the output (recipe 0.09; 0.12 with H 0.24 on big boxes - R9) |
| `CC_REGION_MESHES` | `""` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: MESH MODE only (CC_SHAPE an STL crop): the folder of `<region>.stl` atlas surfaces that keepers and frozen regions are read from (e.g. `jobs\<J>\work\regions\`); the B-rep mode uses the face manifest instead |
| `CC_GROUP` | `-` | `_ccdeliver_zip.py` | yes | no | CARD | `<name>\|<label>`: the map's objects inside ONE hidden, collapsed App::DocumentObjectGroup (the client, 2026-09-24: "the entire colored atlas should be in an unexpanded, hidden part"); named per delivery (R32: `G5_ATLAS_v6`) |
| `CC_HIDE_MAP` | `-` | `_ccdeliver_zip.py` | yes | no | CONSTANT | CONSTANT-off: hide the map objects at open |
| `CC_IN` | `-` | `_ccnmfix.py`, `_ccspikes.py` | yes | no | CARD | input mesh - a path, per run |
| `CC_INSET` | `"1.6"` | `_blobcore.py` | yes | no | CONSTANT | refusal inset from the capped wall (M + 0.3 = 1.8 with M 1.5) |
| `CC_JOB` | `os.path.basename(os.path.dirname(WORK` | `_finalgates.py` | yes | no | CONSTANT | filled by kit mesh |
| `CC_JOIN` | `"seamweld"` | `_ccweld.py` | yes | no | CARD | seammerge (the join that closed every refined seam); zipper only with CC_ZIPPER_WHY |
| `CC_KEEPBAND` | `"0.6"` | `_ccextract.py` | yes | no | CARD | keeper band (recipe 0.40) |
| `CC_KEEPHARD` | `"0.35"` | `_ccextract.py` | yes | no | CARD | hard hold distance (recipe 0.15) |
| `CC_KEEPSKIN` | `"0"` | `_ccextract.py` | yes | no | CARD | keeper skin inside the edit region (recipe 0.10 with vanes) |
| `CC_KEEP_ADD` | `"0"` | `_ccextract.py` | yes | no | CARD | one-sided keepers (recipe 1) |
| `CC_KEEP_FACES_AT` | `""` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: faces under points become keepers when the card names them |
| `CC_KEEP_REGIONS` | `""` | `_ccextract.py` | yes | no | CARD | atlas regions held one-sided (recipe: vanes); empty only when none, said |
| `CC_KEEP_RELEASE_BOXES` | `""` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: keepers hold nothing inside the listed boxes (L80) |
| `CC_LARGEST` | `"1"` | `_ccextract.py` | yes | no | CONSTANT | keep the largest region; discarded ones are recorded for the weld |
| `CC_M` | `"1.5"` | `_blobcore.py` | yes | no | CONSTANT | the core grow (R12); a card may lower it with a note |
| `CC_MANIFEST` | `-` | `_finalgates.py` | yes | no | CARD | the final's manifest - a path, per run |
| `CC_MAP` | `-` | `_ccdeliver_zip.py` | yes | no | CARD | the approved region map FCStd - a path, per delivery |
| `CC_MARGIN` | `"0.5"` | `_ccspikes.py` | yes | no | CONSTANT | spike margin beyond the extent |
| `CC_MATCHTOL` | `"0.10"` | `_ccextract.py` | yes | no | CARD | reinsertion tolerance (recipe 0.12; 0.14 on knife-thin vane edges, said) |
| `CC_MAXLOOP` | `"15"` | `_islandgrow.py` | yes | no | CONSTANT | rim loops under this length become core |
| `CC_MAXOPEN` | `"20"` | `_finalgates.py` | yes | no | CONSTANT | allowed open+non-manifold delta |
| `CC_MAXPAIR` | `"6.0"` | `_ccweld.py` | yes | no | CONSTANT | loop-pairing distance |
| `CC_MAXT` | `"40.0"` | `_ccthin.py` | yes | no | CONSTANT | ray length |
| `CC_MESHDOC` | `-` | `_ccdeliver_zip.py` | yes | no | CARD | the throw-away mesh document - a path, per delivery |
| `CC_MESHES` | `-` | `_ccmeshdoc.py` | yes | no | CARD | the meshes to deliver - paths, per delivery |
| `CC_MESHVIEW` | `-` | `_ccdeliver_zip.py` | yes | no | CARD | name:visible:r,g,b per mesh, per delivery |
| `CC_NAME` | `"reworked"` | `_final.py` | yes | no | CONSTANT | the result's stem |
| `CC_NEARMARG` | `"2.0"` | `_ccweld.py` | yes | no | CONSTANT | the near-core clip margin; the crop margin must exceed it plus the extract pad |
| `CC_NEWREF` | `-` | `_ccthin.py` | yes | no | CONSTANT | CONSTANT-off: rays only from triangles not in the base (the gates set it) |
| `CC_NUDGE` | `"0.002"` | `_ccnmfix.py` | yes | no | CONSTANT | split-vertex nudge |
| `CC_OFF` | `"0.01"` | `_ccthin.py` | yes | no | CONSTANT | ray start offset |
| `CC_OPEN` | `"0.35"` | `_ccextract.py` | yes | no | CARD | removes tabs under 2x it (recipe 0.35) |
| `CC_OPENINGS` | `-` | `_finalgates.py` | yes | no | CONSTANT | CONSTANT-off: the project's designed-openings json, when it has one |
| `CC_OUT` | `""` | `_blobcore.py`, `_blobgrow.py`, `_ccdeliver_zip.py`, `_ccmeshdoc.py`, `_ccnmfix.py`, `_ccrefine.py`, `_ccspikes.py`, `_ccweld.py`, `_finalgates.py`, `_islandgrow.py` | yes | no | CARD | the output - a path, per run (a killed run's output is renamed .KILLED) |
| `CC_OUTDIR` | `-` | `_ccexport_regions.py`, `_guiload.py` | yes | no | CARD | the output folder - per run |
| `CC_OUT_STL` | `""` | `_ccextract.py` | yes | no | CARD | the patch - a path, per run |
| `CC_PAD` | `"2.0"` | `_ccextract.py` | yes | no | CARD | air pad round the box (recipe 3.0) |
| `CC_PASSBAND` | `"0.05"` | `_ccweld.py` | yes | no | CARD | patch smoothing passband (recipe 0.05; one job needed 0.02) |
| `CC_PATCH` | `-` | `_blobcore.py`, `_ccweld.py` | yes | no | CARD | the patch - a path, per run |
| `CC_PCLEAN` | `"0.0"` | `_ccweld.py` | yes | no | CONSTANT | CONSTANT-off |
| `CC_PNG` | `-` | `_blobcore.py` | yes | no | CARD | the core picture - a path, per run (open it) |
| `CC_POINTS` | `-` | `_blobgrow.py` | yes | no | CARD | the points to grow over, per run |
| `CC_QUANT` | `"1e-4"` | `_ccmerge.py` | no | no | DEAD | _ccmerge is superseded by kit splice (the final is one splice pass) |
| `CC_REF` | `-` | `_ccneedle.py`, `_ccnmfix.py` | yes | no | CARD | the base the repairs must not touch - a path, per run (R19) |
| `CC_REFINE_L` | `"0.3"` | `_ccrefine.py` | yes | no | CONSTANT | edges crossing a core wall are split under this (the route's recipe value) |
| `CC_REGIONS` | `-` | `_ccexport_regions.py` | yes | no | CARD | the regions to export, per run |
| `CC_RESULT` | `-` | `_ccthin.py`, `_finalgates.py` | yes | no | CARD | the result mesh - a path, per run |
| `CC_RESULTS` | `-` | `_ccmerge.py` | no | no | DEAD | _ccmerge is superseded by kit splice |
| `CC_SAMPLE` | `"20000"` | `_ccthin.py` | yes | no | CONSTANT | ray sample count (the gates set it) |
| `CC_SEAL1` | `"0"` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: one-cell air nodes between solids made solid where the card says (R10) |
| `CC_SEAMSTEP` | `"0"` | `_ccweld.py` | yes | no | CONSTANT | CONSTANT-off |
| `CC_SEAMTOL` | `"0.15"` | `_ccweld.py` | yes | no | CONSTANT | THE CEILING (the client 2026-09-21): may be lowered, never raised |
| `CC_SEL` | `-` | `_blobcore.py` | yes | no | CARD | the small box on the defect, per run |
| `CC_SHAPE` | `-` | `_ccextract.py` | yes | no | CARD | the model of record (brep) - a path |
| `CC_SIGMA` | `"0.45"` | `_ccextract.py` | yes | no | CARD | blur (recipe 0.75; <= half the local wall - R6) |
| `CC_SIGNFAR` | `"1.5"` | `_ccextract.py` | yes | no | CONSTANT | sign-vote distance in cells |
| `CC_SMOOTH` | `"0"` | `_ccweld.py` | yes | no | CARD | patch smoothing iterations (recipe 25; one job 80) |
| `CC_SNAP` | `"0"` | `_ccextract.py` | yes | no | CARD | keeper snap distance (recipe 0.25) |
| `CC_SPECK` | `"1.0"` | `_ccspikes.py` | yes | no | CONSTANT | loose shells under this size (mm) are specks |
| `CC_SPIKE_MARGIN` | `"0.5"` | `_ccrefine.py` | yes | no | CONSTANT | flap margin beyond the extent |
| `CC_SPINE_X` | `"0"` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: one part's keeper rule (the project: 10.30); off unless all three are set |
| `CC_SPINE_Z` | `"0"` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: the example part 89.60; see CC_SPINE_X |
| `CC_SRCDIR` | `-` | `_ccexport_regions.py` | yes | no | CARD | where the region surfaces are, per project |
| `CC_STANDOFF` | `"0.15"` | `_ccneedle.py` | yes | no | CONSTANT | stand-off from the fitted quadric |
| `CC_THIN` | `"0.70"` | `_ccthin.py` | yes | no | CONSTANT | the reliability wall |
| `CC_TIPTURN` | `"150"` | `_ccneedle.py` | yes | no | CONSTANT | needle tip angle |
| `CC_TIPTURN2` | `"135"` | `_ccneedle.py` | yes | no | CONSTANT | needle tip angle, short fins |
| `CC_TOL` | `"0.12"` | `_blobcore.py` | yes | no | CONSTANT | "edit" = patch points more than this off the body (recipe 0.10-0.12) |
| `CC_TRIM` | `-` | `_blobcore.py` | yes | no | CONSTANT | CONSTANT-off: a trim box, with the recipe's guard |
| `CC_UNION_STL` | `""` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: designed solids (closed STLs, `;`-separated) unioned into the body's field before cleaning - a drawn addition such as the client's heatsink-plate rail (2026-09-24); the card names the files |
| `CC_TURN` | `"120"` | `_ccneedle.py` | yes | no | CONSTANT | folded-edge angle |
| `CC_VANE_AREA` | `"0"` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: the example part 400; see CC_SPINE_X |
| `CC_VPNAME` | `""` | `_ccdeliver_zip.py` | yes | no | CONSTANT | CONSTANT-off: the template's mesh view provider by name; found by MaterialList otherwise |
| `CC_VPTEMPLATE` | `-` | `_ccdeliver_zip.py` | yes | no | CARD | the GUI-saved template holding one coloured mesh - a path, per project |
| `CC_WELD` | `-` | `_islandgrow.py` | yes | no | CARD | the weld to read rim loops from, per run |
| `CC_WORK` | `-` | `_ccextract.py`, `_ccthin.py`, `_ccweld.py`, `_collect.py`, `_final.py`, `_finalgates.py` | yes | no | CONSTANT | filled by kit mesh: the job's work folder |
| `CC_ZBRIDGE` | `""` | `_ccextract.py` | yes | no | CONSTANT | CONSTANT-off: connect two sections in the field where the card says (R7) |
| `CC_ZIPPER_WHY` | `""` | `_ccweld.py` | yes | no | CONSTANT | CONSTANT-off: the reason for a zipper join (comparison only) |
| `CC_ZLID` | `"0"` | `_ccextract.py` | yes | no | CARD | the lid above which the field is the body's own (recipe 0 = none; one case needed one) |
| `CC_ZRAMP` | `"2.0"` | `_ccextract.py` | yes | no | CONSTANT | lid ramp |
