"""Stage 1: Multimodal Media Ingest & High-Density Shot Cataloging.

Solves v01's 'blind 15s frame-only sampling' by combining:
1. Stream metadata & rotation matrix detection (handling both 4K camera & vertical phone clips)
2. 1-second resolution audio profiling (RMS dBFS, high-freq interaction energy for typing/pet sounds, noise spike warnings)
3. High-density visual contact sheets stamped with exact timecode, sharpness score, and audio activity indicators.
"""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"


def _bin(cmd: str, fallback: str) -> str:
    return cmd if Path(cmd).exists() else fallback


def probe_media(path: Path) -> dict:
    ffprobe = _bin(FFPROBE, "ffprobe")
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    raw = json.loads(proc.stdout)
    v_stream = next((s for s in raw.get("streams", []) if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in raw.get("streams", []) if s.get("codec_type") == "audio"), None)

    rotation = 0
    for sd in v_stream.get("side_data_list", []):
        if "rotation" in sd:
            rotation = int(sd["rotation"])
    if rotation == 0:
        rot_tag = v_stream.get("tags", {}).get("rotate")
        if rot_tag:
            rotation = int(rot_tag)

    raw_w = int(v_stream.get("width", 0))
    raw_h = int(v_stream.get("height", 0))
    display_w, display_h = (raw_h, raw_w) if abs(rotation) in (90, 270) else (raw_w, raw_h)

    fps_str = v_stream.get("avg_frame_rate") or v_stream.get("r_frame_rate") or "25/1"
    if "/" in fps_str:
        num, den = fps_str.split("/", 1)
        fps = round(float(num) / max(float(den), 1.0), 3)
    else:
        fps = float(fps_str)

    duration = float(raw.get("format", {}).get("duration") or v_stream.get("duration") or 0.0)

    return {
        "file": path.name,
        "path": str(path.resolve()),
        "duration": round(duration, 3),
        "raw_width": raw_w,
        "raw_height": raw_h,
        "rotation": rotation,
        "display_width": display_w,
        "display_height": display_h,
        "orientation": "portrait" if display_h > display_w else "landscape",
        "fps": fps,
        "video_codec": v_stream.get("codec_name"),
        "has_audio": a_stream is not None,
        "audio_codec": a_stream.get("codec_name") if a_stream else None,
        "creation_time": raw.get("format", {}).get("tags", {}).get("creation_time"),
    }


def analyze_audio_profile(path: Path, duration: float) -> dict:
    """Decode mono 16kHz PCM and compute per-second RMS dBFS & spectral band cues."""
    ffmpeg = _bin(FFMPEG, "ffmpeg")
    sr = 16000
    proc = subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"
        ],
        check=True,
        capture_output=True,
    )
    samples = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    total_secs = max(1, int(math.ceil(duration)))
    per_sec = []
    interaction_peaks = []
    loud_spikes = []

    for sec in range(total_secs):
        chunk = samples[sec * sr : (sec + 1) * sr]
        if len(chunk) < sr // 4:
            break
        rms = float(np.sqrt(np.mean(chunk ** 2) + 1e-12))
        dbfs = round(20.0 * math.log10(max(rms, 1e-6)), 1)

        # FFT spectral bands:
        # 500-1400 Hz often captures car horns; 1600-5500 Hz captures crisp keyboard clicks & puppy squeaks
        spec = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
        freqs = np.fft.rfftfreq(len(chunk), d=1.0 / sr)
        total_e = float(np.sum(spec ** 2) + 1e-9)
        mid_horn_e = float(np.sum(spec[(freqs >= 450) & (freqs < 1300)] ** 2)) / total_e
        crisp_hi_e = float(np.sum(spec[(freqs >= 1600) & (freqs <= 6000)] ** 2)) / total_e

        tag = "ambient"
        if dbfs > -16.5 and mid_horn_e > 0.55:
            tag = "horn_or_loud_mid"
            loud_spikes.append(sec)
        elif dbfs > -34.0 and crisp_hi_e > 0.22:
            tag = "crisp_detail"  # typing, clicks, puppy whimpers
            interaction_peaks.append(sec)

        per_sec.append({
            "sec": sec,
            "dbfs": dbfs,
            "crisp_ratio": round(crisp_hi_e, 3),
            "tag": tag,
        })

    mean_dbfs = round(float(np.mean([p["dbfs"] for p in per_sec])), 1) if per_sec else -60.0
    return {
        "mean_dbfs": mean_dbfs,
        "crisp_interaction_seconds": interaction_peaks[:40],
        "loud_spike_seconds": loud_spikes[:30],
        "per_second": per_sec,
    }


def _sharpness_score(im: Image.Image) -> float:
    gray = np.asarray(im.convert("L"), dtype=np.float32)
    gx = np.diff(gray, axis=1)
    gy = np.diff(gray, axis=0)
    score = float(np.var(gx) + np.var(gy))
    return round(min(99.9, math.sqrt(score) * 3.2), 1)


def generate_contact_sheets(
    media_info: dict,
    audio_profile: Optional[dict],
    out_dir: Path,
    interval: float = 4.0,
    max_per_sheet: int = 24,
) -> List[str]:
    """Extract frames at `interval` seconds and build readable contact sheets."""
    ffmpeg = _bin(FFMPEG, "ffmpeg")
    src = Path(media_info["path"])
    stem = src.stem
    frames_dir = out_dir / "frames" / stem
    frames_dir.mkdir(parents=True, exist_ok=True)

    is_portrait = media_info["orientation"] == "portrait"
    tw, th = (240, 426) if is_portrait else (400, 225)
    cols = 6 if is_portrait else 4
    label_h = 34

    duration = media_info["duration"]
    times = []
    t = 0.5
    while t < duration - 0.3:
        times.append(round(t, 2))
        t += interval

    # Fast single-pass frame extraction using fps filter
    pattern = frames_dir / "f_%05d.jpg"
    existing = sorted(frames_dir.glob("f_*.jpg"))
    if len(existing) < max(1, len(times) - 2):
        scale_vf = f"fps=1/{interval}:round=near,scale={tw}:{th}:force_original_aspect_ratio=decrease"
        subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-threads", "4", "-i", str(src), "-an",
                "-vf", scale_vf, "-q:v", "4", str(pattern)
            ],
            check=True,
        )
        existing = sorted(frames_dir.glob("f_*.jpg"))

    font = ImageFont.truetype(FONT_PATH, 14)
    audio_by_sec: Dict[int, dict] = {}
    if audio_profile:
        for item in audio_profile.get("per_second", []):
            audio_by_sec[item["sec"]] = item

    sheets = []
    total_items = min(len(times), len(existing))
    for page_idx, start_i in enumerate(range(0, total_items, max_per_sheet)):
        batch_indices = range(start_i, min(total_items, start_i + max_per_sheet))
        rows = (len(batch_indices) + cols - 1) // cols
        canvas = Image.new("RGB", (cols * tw, rows * (th + label_h)), "#121316")
        draw = ImageDraw.Draw(canvas)

        for local_i, idx in enumerate(batch_indices):
            sec = idx * interval
            fpath = existing[idx]
            im = Image.open(fpath).convert("RGB")
            sharp = _sharpness_score(im)
            x = (local_i % cols) * tw
            y = (local_i // cols) * (th + label_h)
            canvas.paste(im, (x + (tw - im.width) // 2, y + (th - im.height) // 2))

            a_item = audio_by_sec.get(int(sec), {})
            dbfs = a_item.get("dbfs", -60.0)
            a_tag = a_item.get("tag", "")
            badge = " [CRISP]" if a_tag == "crisp_detail" else (" [NOISE!]" if a_tag == "horn_or_loud_mid" else "")
            color = "#7ee787" if a_tag == "crisp_detail" else ("#ff7b72" if a_tag == "horn_or_loud_mid" else "#e6edf3")

            stamp = f"{int(sec)//60:02d}:{sec%60:04.1f} ({sec:.1f}s) S:{sharp:.0f} {dbfs:.0f}dB{badge}"
            draw.text((x + 6, y + th + 8), stamp, font=font, fill=color)

        sheet_path = out_dir / f"{stem}_sheet_{page_idx + 1:02d}.jpg"
        canvas.save(sheet_path, quality=88)
        sheets.append(str(sheet_path))

    return sheets


def scan_directory(source_dir: Path, out_dir: Path, interval: float = 4.0) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    exts = {".mp4", ".mov", ".mkv", ".m4v"}
    files = sorted([p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in exts])

    catalog = {
        "source_dir": str(source_dir.resolve()),
        "sample_interval_sec": interval,
        "media": [],
    }

    for f in files:
        print(f"[scan] Probing {f.name} ...", flush=True)
        info = probe_media(f)
        audio_prof = analyze_audio_profile(f, info["duration"]) if info["has_audio"] else None
        print(f"[scan] Rendering contact sheets for {f.name} ({info['orientation']}, {info['duration']}s) ...", flush=True)
        sheets = generate_contact_sheets(info, audio_prof, out_dir, interval=interval)
        catalog["media"].append({
            "info": info,
            "audio_summary": {
                "mean_dbfs": audio_prof["mean_dbfs"] if audio_prof else None,
                "crisp_interaction_seconds": audio_prof["crisp_interaction_seconds"] if audio_prof else [],
                "loud_spike_seconds": audio_prof["loud_spike_seconds"] if audio_prof else [],
            },
            "contact_sheets": sheets,
        })

    catalog_path = out_dir / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2))
    print(f"[scan] Saved catalog -> {catalog_path}", flush=True)
    return catalog_path
