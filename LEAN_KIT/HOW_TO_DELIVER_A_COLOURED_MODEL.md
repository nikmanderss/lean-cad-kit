# HOW TO DELIVER A COLOURED MODEL — the method, proven 2026-09-16

> **The recipe is `kit deliver`, both halves (2026-09-24):** `--target` for a B-rep round, `--mesh` for a mesh round
> (`PRINT_READINESS.md` step 7); it edits the zip as below and runs `kit deliverycheck` itself. `kit mesh meshdoc` and
> `kit mesh zip` are its prior art. **This file is the WHY** behind its gates.

the client, over many rounds: *"assembly context is no longer colored (again, you have reverted to grey many
times and it's a standing bug)"* … *"Colors applied. Write out to a file the correct way to apply them
for future agents."*

This is that file. The implementation is `kit deliver` (`kit\kit_deliver.py`).

> **All three faults are separate, they look identical on screen, and fixing
> one does not fix the others** — `kit accept` should gate on all three, not just the first.

---

## The three separate faults that each produce a grey model

### 1. `freecadcmd` deletes every colour, silently

`freecadcmd` has **no GUI**, so App objects have **no ViewObject**. Colour, appearance, transparency,
display mode and visibility do not exist in that process. When it saves a document, FreeCAD writes an
`.FCStd` with **no `GuiDocument.xml` at all** — and that file is the only place those properties live.

Measured: `Deliverables\R19\model\R19_MYPART.FCStd` and `R20\model\R20_MYPART.FCStd`, both produced by
opening a template in `freecadcmd` and re-saving, contain **no `GuiDocument.xml`**. The R10 template has
one, 120,385 bytes.

**No amount of care inside a console script can fix this — the information is not in the process.**
`FreeCADGui.setupWithoutGUI()` does not help either: it returns OK and still creates no ViewObjects
(tested, FreeCAD 1.1.3).

**→ Never open and re-save a document to deliver it. Edit the `.FCStd` zip instead.** An `.FCStd` is a
zip: swap the one entry that holds the body (`<Object>.Shape.brp`), edit `Document.xml` and
`GuiDocument.xml` as **text**, and copy every other entry through byte for byte. Side benefit: the console
re-save produced a **378 MB** file; the zip swap produces **52 MB** from the same body.

### 2. An orphaned zip entry breaks the whole colour table

FreeCAD registers every `file="X"` it meets while parsing `Document.xml` and `GuiDocument.xml`, then reads
the zip against that registration. **The reference list and the payload entries must agree exactly.** An
entry with no reference — or a reference with no entry — breaks the mapping and every object falls back to
default grey. No error, no warning.

This is what happened when the dead R10 mesh was removed: deleting its `<ViewProvider>` de-registered
`ShapeAppearance_PRINT` while that entry was still written into the zip.

**→ Gate it. Refuse to write the file unless both sets are empty:**

```python
refs    = set(re.findall(r'file="([^"]+)"', doc)) | set(re.findall(r'file="([^"]+)"', gui))
payload = set(zip_entries) - {"Document.xml", "GuiDocument.xml"} - dropped_files
orphan  = payload - refs      # must be empty
missing = refs - payload      # must be empty
```

Reference: R10 template 111 refs / 111 entries, clean. Delivered R21 109 / 109, clean.

### 3. `ShapeAppearance` is NOT what paints the part in this document

This is the one that cost the most. The colours were in the file the whole time and were **not being
used**. Every object carries the same App-level `Materials::PropertyMaterial` (uuid
`7f9fd73b-50c9-41d8-b7b2-575a030c1eeb`, the Default card), and in FreeCAD 1.1 that wins over the stored
`ShapeAppearance` MaterialList — so every part renders Default grey.

**→ State the colour as `App::PropertyColor` (`ShapeColor`) in the ViewProvider.** That is what R50 —
a revision that demonstrably *did* show colour — uses, and writing it fixed this model:

```xml
<Property name="ShapeColor" type="App::PropertyColor" status="1">
    <PropertyColor value="3952156927"/>
</Property>
```

Encoding: `value = (r << 24) | (g << 16) | (b << 8) | a`, alpha `255`. Insert it after the
`ShapeAppearance` property (keeps the properties in name order) and **increment that ViewProvider's
`<Properties Count="N">`** — a count that disagrees with the number of `<Property>` children is another
silent failure.

---

## Reading the colours that are already in the file

They live in the `ShapeAppearance` MaterialList entry each ViewProvider names — one zip entry per object
(`ShapeAppearance`, `ShapeAppearance1`, … named, not positional). Layout:

```
int32 count, then per material 4 x uint32: ambient, diffuse, specular, emissive
```

Each uint32 is little-endian, so **the bytes read `[a, b, g, r]`** — the diffuse slot is `raw[8:12]` and
the colour is `(raw[11], raw[10], raw[9])`.

**Prove the byte order before trusting it.** Read it the wrong way round and every colour comes out
channel-reversed and still looks plausible. `MARKER_BOX`'s own label says *"red, transparent"*: it decodes
`#ff0000` as `[a,b,g,r]` and `#0000ff` the other way. That single object settles it.

The colours in this model, decoded correctly:

| object | colour | | object | colour |
|---|---|---|---|---|
| `P_Bracket` | `#eb963c` | | `P_Gasket` | `#cdaf82` |
| `P_Fitting_A` / `P_Fitting_B` | `#d7b446` | | `P_Hose_L` / `P_Hose_R` | `#50bec8` |
| `P_Module` | `#d75050` | | `P_Cable` | `#966ed2` |
| `P_Block_A` / `P_Block_B` | `#5a8cd2` | | `Cover` | `#6ebe6e` |
| `P_Pad` | `#96969b` | | `MARKER_BOX` / `MARKER_PYRAMID` | `#ff0000` |
| `P_Insulation` | `#f0f0eb` | | `BODY_BREP` (the print body) | `#c8c8cd` |

---

## Visibility — a separate setting, and it hides the colour

`Visibility` exists **twice**: as an `App::PropertyBool` in `Document.xml` and as a ViewObject property in
`GuiDocument.xml`. **The GUI one is what the viewer obeys.** Set both.

In the R10 template `BODY_BREP` is **hidden** and every `P_*` part **visible**, because the visible
print body used to be the R10 mesh. Delete that mesh without fixing visibility and the document opens with
no part. Hide the assembly to "fix" that and the document opens with no colour — the only thing left
visible is the part, which really is grey (`#c8c8cd`). Both complaints, one setting.

Deliver with the part **and** the coloured assembly shown; hide only the reference scans, datums and
markers.

---

## The check before handing over

Not "are the bytes there" — **are they wired up**. Verifying the ingredients is not verifying the dish;
that mistake was made twice here.

1. `GuiDocument.xml` is present in the zip.
2. `orphan` and `missing` file-table sets are both empty.
3. `GuiDocument.xml` parses as valid XML (`ET.fromstring`).
4. Every ViewProvider's declared `Properties Count` equals its actual `<Property>` count.
5. Every part that should be coloured has a `ShapeColor` property with the expected value.
6. The print body's `Visibility` is `true` in **both** XML files.
7. The document opens in `freecadcmd` with the expected object count and a valid solid.

Then look at it. Opening the file in the FreeCAD GUI (or a screenshot of a FreeCAD GUI session) is the only proof
the colour actually paints — the headless tools cannot render one.

---

## Placements — what FreeCAD reads back on reload (31br B5, measured 2026-10-30 on FreeCAD 1.1.3)

A probe of four files, each reopened by the kernel:

| case | written | read back |
|---|---|---|
| P1 | a Part::Feature placed in the kernel (-90° about X, moved), saved by FreeCAD | the Placement, the vertex where it should be |
| P2 | the same XML Placement over an IDENTITY `.brp` (the kit's `--target` swap of a GUI-placed body) | **Placement reset to identity** — the body sits at the brep's own place |
| P3 | an identity XML Placement over a LOCATED `.brp` (`shape.Placement` set, exported) | the brep's location, as the Placement |
| P4 | both, agreeing | the placement |
| M1 / M2 | a Mesh::Feature's XML Placement over an UNPLACED `.bms` | the Placement applied **once** to the kernel |
| M3 | a mesh whose points were transformed, identity Placement | the points where they are |

So: **a body's `.brp` location is what FreeCAD reads back; a mesh's XML Placement is.** `kit deliver` writes a body's placement both ways (the brep baked by
`kit place`'s kernel step, the XML to match) and a mesh's as the XML alone; a `--target` swap carries the template body's own Placement into the swapped
brep (it used to reset to identity — an agent's "a GUI Placement survives the swap" was not true). `kit place` records every placement in
`claude_code\PLACEMENTS.json`.
