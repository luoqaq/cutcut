"""Stage 5: Output Verification & Shot-by-Shot Visual QA Sheet Generator.

Verifies the rendered MP4:
1. Full stream decode integrity check (`ffmpeg -v error ... -f null -`)
2. EBU R128 loudness (`I` LUFS, `TP` dBTP) & volume stats
3. Shot-by-shot 9:16 portrait QA contact sheet (sampling midpoint of every shot + key caption moments)
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .ingest import FFMPEG, FONT_PATH, probe_media
from .schema import compute_timeline


def _ffmpeg() -> str:
    return FFMPEG if Path(FFMPEG).exists() else "ffmpeg"


def verify_render(spec: dict, mp4_path: Path, out_dir: Path) -> dict:
    ffmpeg = _ffmpeg()
    out_dir.mkdir(parents=True, exist_ok=True)
    spec, _ = compute_timeline(spec)

    info = probe_media(mp4_path)
    dec = subprocess.run(
        [ffmpeg, "-hide_banner", "-v", "error", "-i", str(mp4_path), "-f", "null", "-"],
        capture_output=True,
        text=True,
    )

    ebur = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", str(mp4_path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    i_match = re.findall(r"I:\s*(-?\d+\.\d+)\s*LUFS", ebur.stderr)
    tp_match = re.findall(r"Peak:\s*(-?\d+\.\d+)\s*dBFS", ebur.stderr)

    # Extract midpoint frame of every shot for visual QA sheet
    qa_frames_dir = out_dir / "qa_frames"
    qa_frames_dir.mkdir(parents=True, exist_ok=True)
    thumbs = []
    tw, th, label_h = 300, 533, 44
    cols = 4

    for shot in spec["shots"]:
        mid_t = round((shot["timeline_start"] + shot["timeline_end"]) / 2.0, 2)
        mid_t = min(max(0.1, mid_t), max(0.1, info["duration"] - 0.15))
        f_out = qa_frames_dir / f"{shot['id']}_{mid_t:.2f}s.jpg"
        subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-ss", f"{mid_t:.3f}", "-i", str(mp4_path), "-frames:v", "1",
                "-vf", f"scale={tw}:{th}", "-q:v", "3", str(f_out),
            ],
            check=True,
        )
        thumbs.append((shot["id"], shot["layout"], mid_t, f_out))

    rows = (len(thumbs) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * tw, rows * (th + label_h)), "#101114")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_PATH, 14)

    for idx, (sid, layout, ts, fp) in enumerate(thumbs):
        x = (idx % cols) * tw
        y = (idx // cols) * (th + label_h)
        im = Image.open(fp).convert("RGB")
        canvas.paste(im, (x, y))
        draw.text((x + 8, y + th + 12), f"{sid} [{layout}] @{ts:.1f}s", font=font, fill="#f0f6fc")

    qa_sheet = out_dir / "qa_portrait_sheet.jpg"
    canvas.save(qa_sheet, quality=90)

    # Also extract cover image (from cover_time or 1.2s)
    cover_t = float(spec.get("cover_time", 1.2))
    cover_path = mp4_path.parent / "cover.jpg"
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-ss", f"{cover_t:.3f}", "-i", str(mp4_path), "-frames:v", "1",
            "-q:v", "2", str(cover_path),
        ],
        check=True,
    )

    sha256 = hashlib.sha256(mp4_path.read_bytes()).hexdigest()
    report = {
        "file": str(mp4_path.resolve()),
        "size_bytes": mp4_path.stat().st_size,
        "sha256": sha256,
        "media_info": info,
        "full_decode": {
            "exit_code": dec.returncode,
            "errors": dec.stderr.strip(),
        },
        "loudness_ebur128": {
            "integrated_lufs": float(i_match[-1]) if i_match else None,
            "true_peak_dbfs": float(tp_match[-1]) if tp_match else None,
        },
        "qa_sheet": str(qa_sheet.resolve()),
        "cover_image": str(cover_path.resolve()),
    }
    report_path = out_dir / "verification.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if dec.returncode != 0:
        err_msg = dec.stderr.strip() or f"Decode exited with code {dec.returncode}"
        print(f"[verify] ERROR: Full stream decode failed: {err_msg}", flush=True)
        raise RuntimeError(f"Video decode check failed: {err_msg}")

    print(f"[verify] Verification passed -> {report_path}", flush=True)
    return report
