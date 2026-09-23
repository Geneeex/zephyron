"""Render one existing Zephyron scene; run with Blender's Python interpreter.

Example (from the repository root):
blender --python-exit-code 1 --background research/blender/Zephyron_Research_Missions.blend \
  --python scripts/render_blender_scene.py -- \
  --scene M09 --output build/blender/M09.png

Use --check-only to validate the saved model without rendering. This script does
not reconstruct the rover from scratch and never saves changes to the blend file.
"""

import argparse
import json
from pathlib import Path
import sys

import bpy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", choices=[f"M{i:02}" for i in range(1, 10)], default="M09")
    parser.add_argument("--output", help="PNG path relative to the repository root")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    root = Path(__file__).resolve().parents[1]
    model = root / "research/blender/Zephyron_Research_Missions.blend"
    if not bpy.data.filepath or Path(bpy.data.filepath).resolve() != model.resolve():
        raise RuntimeError("Open this repository's saved Zephyron model before running the helper.")
    scenes = sorted((s for s in bpy.data.scenes if s.name.startswith("M0")), key=lambda s: s.name)
    if len(scenes) != 9:
        raise RuntimeError(f"Expected nine mission scenes, found {len(scenes)}")
    external_images = [im.name for im in bpy.data.images
                       if im.source == "FILE" and not im.packed_file]
    if external_images:
        raise RuntimeError("Unpacked external images: " + ", ".join(external_images))
    if any(f.filepath != "<builtin>" or f.packed_file for f in bpy.data.fonts):
        raise RuntimeError("Expected builtin-only fonts in this public model")
    for scene in scenes:
        expected_frame = 96 if scene.name.startswith("M07") else 1
        if not scene.camera or scene.frame_current != expected_frame:
            raise RuntimeError(f"Missing camera or unexpected stored frame: {scene.name}")
        if not scene.render.filepath.startswith("//"):
            raise RuntimeError(f"Render path is not Blender-relative: {scene.name}")
    scene = next(s for s in scenes if s.name.startswith(args.scene + " "))
    bpy.context.window.scene = scene
    scene.frame_set(96 if args.scene == "M07" else 1)
    bpy.context.view_layer.update()
    if args.check_only:
        print(json.dumps({"status": "PASS", "scene_count": len(scenes),
                          "selected_scene": args.scene, "frame": scene.frame_current,
                          "unpacked_external_images": external_images,
                          "render_performed": False, "builtin_only_fonts": True}))
        return
    relative = Path(args.output or f"build/blender/{args.scene}.png")
    if relative.is_absolute():
        raise ValueError("--output must be relative to the repository root")
    output = (root / relative).resolve()
    if not output.is_relative_to(root) or output.suffix.lower() != ".png":
        raise ValueError("--output must identify a .png within the repository")
    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print(json.dumps({"status": "rendered", "scene": args.scene,
                      "frame": scene.frame_current,
                      "output": output.relative_to(root).as_posix(),
                      "saved_model_modified": False}))


if __name__ == "__main__":
    main()
