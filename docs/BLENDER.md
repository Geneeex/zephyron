# Editable rover and mission scenes

Open `research/blender/Zephyron_Research_Missions.blend` in Blender. The public copy was saved and reopened with Blender 4.3.2. It contains the complete editable rover and nine saved mission scenes. Its image textures are packed, so an external texture download is not needed. Editable labels use Blender builtin Bfont; proprietary font bytes are not bundled.

| Scene | Illustration | Saved frame | Manuscript figure |
|---|---|---:|---:|
| M01 | Environmental water sampling | 1 | 25 |
| M02 | Controlled obstacle approach | 1 | 28 |
| M03 | Gas leak reconnaissance | 1 | 26 |
| M04 | Radiation survey | 1 | 27 |
| M05 | Stationary solar and UV monitoring | 1 | 30 |
| M06 | Supervised visual reconnaissance | 1 | 36, first panel |
| M07 | Manipulator retrieval | 96 | 29 |
| M08 | Communications and logging | 1 | 36, second panel |
| M09 | Orthographic design baseline | 1 | 7, second image |

Choose a scene using Blender's scene selector. The files under `research/blender/renders/` are the existing 1800 × 1200 manuscript renders. Those renders predate the public model's label-typeface substitution from Bahnschrift to builtin Bfont; a new render will show the replacement typeface. The saved render destinations use Blender-relative paths such as `//renders/M01.png`; `//` means the folder containing the `.blend` file.

## Validate without rendering

Run from the repository root using a Blender executable available on your system:

```sh
blender --python-exit-code 1 --background research/blender/Zephyron_Research_Missions.blend --python scripts/render_blender_scene.py -- --scene M09 --check-only
```

This opens the saved model and checks all nine scene cameras, intended frames, relative render paths, packed external images and builtin-only fonts. It produces no new render and does not save the model. The helper requires Blender's Python interpreter; ordinary `python` cannot import `bpy` unless separately installed.

## Render an existing scene

```sh
blender --python-exit-code 1 --background research/blender/Zephyron_Research_Missions.blend --python scripts/render_blender_scene.py -- --scene M09 --output build/blender/M09.png
```

Change `M09` to `M01`–`M08` as needed. The helper selects frame 96 for M07 and frame 1 for the other scenes. Output paths must be PNG paths within the repository. It creates the output directory and leaves the saved model unchanged. Rendering time depends on your hardware. The scene uses its saved Cycles settings; exact pixels may differ across Blender versions and rendering devices.

On Windows, replace `blender` with the full path to `blender.exe` if it is not on PATH. In PowerShell, prefix a quoted executable path with `&`.

## What was checked

`research/blender/model_verification.json` records a fresh reopen of the portable public copy. Object transforms, non-text mesh vertex/topology data, scene membership, camera settings and stored frames were fingerprinted before and after the portability edits. The fingerprint excludes text font settings and generated text outlines; these intentionally change when a font is replaced. The fingerprint and packed texture byte hashes matched. The original source model remained unchanged. All nine saved scenes reopened with the intended camera and frame, and no linked libraries or unpacked external texture files were found. No new full render was performed for this portability check.

The public copy replaces Bahnschrift with Blender builtin Bfont in 73 editable text curves and removes the proprietary packed font data. The text remains editable; labels may have different glyph shapes and widths. The rover geometry, materials, cameras and scene setup are retained. Packaging edits use relative render and packed-asset paths, current embedded model notes, removal of obsolete embedded construction snippets, and compressed storage. Those snippets described an earlier baseline and were not a complete reconstruction workflow. This repository provides the saved editable model plus a rerender helper; it does not claim a from-scratch procedural rebuild.

## Engineering interpretation

The scenes depict proposed missions and an industrial design interpretation of the author-supplied photographs. They are not physical trial records, dynamics simulations, manufacturing CAD or a validated digital twin. Units are meters, and the selected analytical baseline is documented in the manuscript and `research/new_design_baseline.json`. A visually represented component does not establish an implemented function or an experimentally validated rating. No load, endurance, collision, environmental sealing, sensor calibration or detection-accuracy result can be inferred from these renders.
