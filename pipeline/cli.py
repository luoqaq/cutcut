"""Unified CLI for the CutCut Full-Automatic AI Video Editing Pipeline.

Commands:
  1. `auto`     — 100% Fully autonomous pipeline: Scan -> AI Director -> Validate -> Prepare -> Remotion Render -> QA
  2. `scan`     — Stage 1: Multimodal scan of raw videos (sharpness scores, contact sheets, audio peaks)
  3. `direct`   — Stage 2: AI Director creates EditSpec from analysis catalog & prompt
  4. `validate` — Stage 2B: Validate an EditSpec JSON against raw footage
  5. `prepare`  — Stage 3: Normalize color, denoise audio, and generate ducking envelope
  6. `build`    — Stages 2-5: Render specified EditSpec with Remotion (+ optional Jianying draft)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .director import direct_project
from .export_jianying import export_jianying_all
from .ingest import scan_directory
from .prepare import prepare_project
from .schema import compute_timeline, load_spec, validate_spec
from .verify import verify_render


def sync_to_studio(spec: dict, manifest: dict, studio_dir: Path) -> Path:
    """Copy prepared clips, master audio, and resolved props JSON into `studio/public/active`."""
    spec, total_dur = compute_timeline(spec)
    active_dir = studio_dir / "public" / "active"
    if active_dir.exists():
        shutil.rmtree(active_dir)
    (active_dir / "clips").mkdir(parents=True, exist_ok=True)

    for key, info in manifest["clips"].items():
        shutil.copy2(info["path"], active_dir / "clips" / info["file"])

    shutil.copy2(manifest["master_audio"], active_dir / "master_mix.wav")

    resolved_props = {
        "spec": spec,
        "manifest": {
            "duration": total_dur,
            "fps": manifest["fps"],
            "width": manifest["width"],
            "height": manifest["height"],
            "masterAudioSrc": "active/master_mix.wav",
            "clips": {
                k: {
                    "src": f"active/clips/{v['file']}",
                    "width": v["width"],
                    "height": v["height"],
                    "duration": v["duration"],
                }
                for k, v in manifest["clips"].items()
            },
        },
    }
    props_path = studio_dir / "src" / "active_props.json"
    props_path.write_text(json.dumps(resolved_props, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[studio] Synced assets & props -> {props_path}", flush=True)
    return props_path


def render_with_remotion(spec: dict, studio_dir: Path, output_mp4: Path) -> None:
    env = os.environ.copy()
    nvm_bins = sorted((Path.home() / ".nvm/versions/node").glob("*/bin")) if (Path.home() / ".nvm/versions/node").exists() else []
    extra_paths = ["/opt/homebrew/bin", "/usr/local/bin"] + [str(p) for p in reversed(nvm_bins)]
    env["PATH"] = ":".join(extra_paths) + ":" + env.get("PATH", "")

    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "npx", "remotion", "render", "src/index.ts", "CutCutEdit",
        str(output_mp4.resolve()),
        "--codec=h264", "--crf=18", "--pixel-format=yuv420p",
    ]
    print(f"[remotion] Rendering -> {output_mp4} ...", flush=True)
    subprocess.run(cmd, cwd=str(studio_dir), env=env, check=True)


def run_build_pipeline(
    spec: dict,
    spec_path: Path,
    source_dir: Path,
    studio_dir: Path,
    build_dir: Path,
    out_name: str | None = None,
    export_jianying: bool = False,
) -> Path:
    errs, warns = validate_spec(spec, source_dir)
    for w in warns:
        print(f"[validate] WARN: {w}", flush=True)
    if errs:
        for e in errs:
            print(f"[validate] ERROR: {e}", flush=True)
        sys.exit(1)

    manifest = prepare_project(spec, source_dir, build_dir)

    if export_jianying:
        print("[jianying] Exporting optional Jianying draft bundle...", flush=True)
        export_jianying_all(spec, manifest, build_dir)
    else:
        print("[jianying] Skipped Jianying draft (pure autonomous Remotion mode).", flush=True)

    sync_to_studio(spec, manifest, studio_dir)

    name = out_name or spec.get("output_filename") or f"{spec['project_id']}.mp4"
    if not name.endswith(".mp4"):
        name += ".mp4"
    output_mp4 = build_dir / name

    render_with_remotion(spec, studio_dir, output_mp4)
    verify_render(spec, output_mp4, build_dir / "qa")
    print(f"🎉 [success] Final ready-to-publish MP4 created: {output_mp4}", flush=True)
    return output_mp4


def main() -> None:
    parser = argparse.ArgumentParser(description="CutCut Full-Automatic AI Video Editing Pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # 1. auto: 100% end-to-end autonomous command
    p_auto = sub.add_parser("auto", help="Fully Autonomous AI Editing: Raw Videos -> Final MP4")
    p_auto.add_argument("--source", required=True, type=Path, help="Folder containing raw camera/phone footage")
    p_auto.add_argument("--out-dir", required=True, type=Path, help="Target project output directory")
    p_auto.add_argument("--prompt", required=True, type=str, help="Creative direction prompt for AI director")
    p_auto.add_argument("--duration", type=float, default=20.0, help="Target total video duration (seconds)")
    p_auto.add_argument("--studio", default=Path("studio"), type=Path, help="Remotion studio directory")
    p_auto.add_argument("--jianying", action="store_true", help="Also export optional Jianying Pro draft")

    # 2. scan: Stage 1
    p_scan = sub.add_parser("scan", help="Stage 1: Multimodal scan of raw video directory")
    p_scan.add_argument("--source", required=True, type=Path)
    p_scan.add_argument("--out", required=True, type=Path)
    p_scan.add_argument("--interval", type=float, default=4.0)

    # 3. direct: Stage 2
    p_dir = sub.add_parser("direct", help="Stage 2: AI Director generates EditSpec JSON")
    p_dir.add_argument("--analysis", required=True, type=Path, help="Analysis folder containing catalog.json")
    p_dir.add_argument("--source", required=True, type=Path, help="Raw source folder")
    p_dir.add_argument("--prompt", required=True, type=str, help="Creative prompt")
    p_dir.add_argument("--out-spec", required=True, type=Path, help="Where to save edit_spec.json")
    p_dir.add_argument("--duration", type=float, default=20.0)

    # 4. validate: Stage 2B
    p_val = sub.add_parser("validate", help="Stage 2B: Validate an EditSpec JSON")
    p_val.add_argument("--spec", required=True, type=Path)
    p_val.add_argument("--source", required=True, type=Path)

    # 5. build: Stages 3-5
    p_build = sub.add_parser("build", help="Run Stages 3-5 (Prepare -> Remotion Render -> QA)")
    p_build.add_argument("--spec", required=True, type=Path)
    p_build.add_argument("--source", required=True, type=Path)
    p_build.add_argument("--studio", default=Path("studio"), type=Path)
    p_build.add_argument("--out-name", default=None, type=str)
    p_build.add_argument("--jianying", action="store_true", help="Also export optional Jianying Pro draft")

    args = parser.parse_args()

    if args.cmd == "auto":
        source_dir = args.source.resolve()
        out_dir = args.out_dir.resolve()
        studio_dir = args.studio.resolve()
        analysis_dir = out_dir / "analysis"

        print(f"🚀 [CutCut Auto] Starting full-automatic editing pipeline for '{args.prompt}'...", flush=True)

        # Step 1: Scan raw footage
        print("\n--- [Stage 1/5] Multimodal Ingest & Contact Sheet Generation ---", flush=True)
        scan_directory(source_dir, analysis_dir, interval=4.0)

        # Step 2: AI Director creates EditSpec
        print("\n--- [Stage 2/5] AI Director Scripting & Framing Composition ---", flush=True)
        spec = direct_project(
            analysis_dir=analysis_dir,
            source_dir=source_dir,
            prompt=args.prompt,
            target_duration=args.duration,
        )
        spec_path = out_dir / "edit_spec.json"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[director] Saved generated EditSpec -> {spec_path}", flush=True)

        # Step 3-5: Prepare, Render, QA
        print("\n--- [Stage 3-5] Preprocess, Remotion Render & Verification ---", flush=True)
        run_build_pipeline(
            spec=spec,
            spec_path=spec_path,
            source_dir=source_dir,
            studio_dir=studio_dir,
            build_dir=out_dir,
            export_jianying=args.jianying,
        )
        return

    if args.cmd == "scan":
        scan_directory(args.source.resolve(), args.out.resolve(), interval=args.interval)
        return

    if args.cmd == "direct":
        spec = direct_project(
            analysis_dir=args.analysis.resolve(),
            source_dir=args.source.resolve(),
            prompt=args.prompt,
            target_duration=args.duration,
        )
        args.out_spec.parent.mkdir(parents=True, exist_ok=True)
        args.out_spec.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Generated EditSpec -> {args.out_spec}")
        return

    if args.cmd == "validate":
        spec = load_spec(args.spec.resolve())
        errs, warns = validate_spec(spec, args.source.resolve())
        for w in warns:
            print(f"WARN: {w}")
        for e in errs:
            print(f"ERROR: {e}")
        if errs:
            sys.exit(1)
        print(f"OK: {len(spec['shots'])} shots, total {spec['computed_duration']}s.")
        return

    if args.cmd == "build":
        spec_path = args.spec.resolve()
        build_dir = spec_path.parent
        source_dir = args.source.resolve()
        studio_dir = args.studio.resolve()

        spec = load_spec(spec_path)
        run_build_pipeline(
            spec=spec,
            spec_path=spec_path,
            source_dir=source_dir,
            studio_dir=studio_dir,
            build_dir=build_dir,
            out_name=args.out_name,
            export_jianying=args.jianying,
        )


if __name__ == "__main__":
    main()
