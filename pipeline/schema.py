"""Stage 2: Declarative EditSpec Schema & Automated Editorial QA Validator.

Prevents structural editing bugs seen in rough-cut v01:
- Detects accidental same-source time rewind / overlapping jump cuts
- Verifies source media bounds against probed durations
- Checks caption overlaps, out-of-bounds timings, and long dead-air gaps
- Validates layout slot completeness (cinema_frame, triptych, split_2, full_bleed)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from .ingest import probe_media

REQUIRED_SLOTS = {
    "cinema_frame": ["main"],
    "full_bleed": ["main"],
    "split_2": ["top", "bottom"],
    "triptych": ["top", "middle", "bottom"],
}


def load_spec(spec_path: Path) -> dict:
    return json.loads(spec_path.read_text(encoding="utf-8"))


def compute_timeline(spec: dict) -> Tuple[dict, float]:
    """Annotate each shot with computed `timeline_start` and `timeline_end`."""
    cursor = 0.0
    for idx, shot in enumerate(spec.get("shots", [])):
        dur = float(shot["duration"])
        shot["index"] = idx
        shot["timeline_start"] = round(cursor, 3)
        cursor += dur
        shot["timeline_end"] = round(cursor, 3)
    total_duration = round(cursor, 3)
    spec["computed_duration"] = total_duration
    return spec, total_duration


def validate_spec(spec: dict, source_dir: Path) -> Tuple[List[str], List[str]]:
    """Return `(errors, warnings)` for an EditSpec."""
    errors: List[str] = []
    warnings: List[str] = []

    shots = spec.get("shots", [])
    if not shots:
        errors.append("EditSpec contains no shots.")
        return errors, warnings

    spec, total_dur = compute_timeline(spec)
    media_cache: Dict[str, dict] = {}

    prev_main_src = None
    prev_main_range = (0.0, 0.0)

    for shot in shots:
        sid = shot.get("id", f"shot_{shot['index']}")
        layout = shot.get("layout", "cinema_frame")
        if layout not in REQUIRED_SLOTS:
            errors.append(f"[{sid}] Unsupported layout '{layout}'. Allowed: {list(REQUIRED_SLOTS)}")
            continue

        dur = float(shot.get("duration", 0))
        if dur <= 0.2:
            errors.append(f"[{sid}] Shot duration {dur}s is too short (must be > 0.2s).")

        clips = shot.get("clips", [])
        slots_present = [c.get("slot") for c in clips]
        expected = REQUIRED_SLOTS[layout]
        if sorted(slots_present) != sorted(expected):
            errors.append(f"[{sid}] Layout '{layout}' requires slots {expected}, got {slots_present}.")

        for c in clips:
            src_name = c.get("source")
            src_path = source_dir / src_name if src_name else None
            if not src_path or not src_path.exists():
                errors.append(f"[{sid}:{c.get('slot')}] Source file not found: {src_path}")
                continue
            if src_name not in media_cache:
                media_cache[src_name] = probe_media(src_path)
            m_info = media_cache[src_name]

            start = float(c.get("start", 0.0))
            speed = float(c.get("speed", 1.0))
            src_end = start + dur * speed
            if start < 0:
                errors.append(f"[{sid}:{c.get('slot')}] Negative start {start}s.")
            if src_end > m_info["duration"] + 0.05:
                errors.append(
                    f"[{sid}:{c.get('slot')}] Source range [{start:.2f}s, {src_end:.2f}s] "
                    f"exceeds {src_name} duration ({m_info['duration']:.2f}s)."
                )

            # Check consecutive single-frame jump-cut / time rewind bug (like v01 shot 3->4)
            if layout in ("cinema_frame", "full_bleed") and c.get("slot") == "main":
                if prev_main_src == src_name:
                    p_start, p_end = prev_main_range
                    if start < p_end and start >= p_start - 1.0:
                        errors.append(
                            f"[{sid}] Time-rewind / overlapping jump cut detected on {src_name}: "
                            f"previous shot ended at {p_end:.2f}s, current starts at {start:.2f}s!"
                        )
                    elif abs(start - p_end) < 0.8:
                        warnings.append(
                            f"[{sid}] Near-contiguous cut on same source {src_name} "
                            f"({p_end:.2f}s -> {start:.2f}s); ensure framing/scale changes enough to avoid a jump cut."
                        )
                prev_main_src = src_name
                prev_main_range = (start, src_end)
            else:
                prev_main_src = None

    # Validate captions
    captions = sorted(spec.get("captions", []), key=lambda x: float(x["start"]))
    last_cap_end = 0.0
    for idx, cap in enumerate(captions):
        cid = cap.get("id", f"cap_{idx+1}")
        cs = float(cap["start"])
        ce = float(cap["end"])
        if ce <= cs:
            errors.append(f"[{cid}] Caption end ({ce}s) <= start ({cs}s).")
        if ce > total_dur + 0.15:
            errors.append(f"[{cid}] Caption end ({ce}s) exceeds total timeline duration ({total_dur}s).")
        if cs < last_cap_end - 0.02:
            errors.append(f"[{cid}] Caption overlaps previous caption ({cs}s < {last_cap_end}s).")
        if cs - last_cap_end > 4.8:
            warnings.append(
                f"[{cid}] Long caption gap of {cs - last_cap_end:.1f}s between {last_cap_end:.1f}s and {cs:.1f}s."
            )
        last_cap_end = ce

    if total_dur - last_cap_end > 4.5:
        warnings.append(f"Trailing {total_dur - last_cap_end:.1f}s of video has no captions.")

    return errors, warnings
