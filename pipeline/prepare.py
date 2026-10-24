"""Stage 3: Asset Preparation, Color Normalization & Ducking Audio Mixer.

Prepares clean, upright, frame-accurate proxy/master clips and multi-stem audio:
1. Video clips: auto-rotates portrait phone footage, normalizes to bt709 & target FPS,
   applies subtle cinematic color polish, and writes fast-seeking MP4s for Remotion & Jianying.
2. Audio stems: extracts & denoises selected natural sound moments (keyboard clicks, puppy whimpers),
   applies smooth sidechain-style envelope ducking to the BGM track, and outputs:
   - `bgm_raw_trimmed.wav` (for Jianying independent BGM track)
   - `nat_clips/*.wav` (for Jianying independent natural sound track)
   - `master_mix.wav` (loudness-normalized -15 LUFS master audio for Remotion direct render)
"""

from __future__ import annotations

import json
import math
import subprocess
import wave
from pathlib import Path
from typing import Dict, List

import numpy as np

from .ingest import FFMPEG, probe_media
from .schema import compute_timeline


def _ffmpeg() -> str:
    return FFMPEG if Path(FFMPEG).exists() else "ffmpeg"


def _read_wav_float(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        raw = wf.readframes(wf.getnframes())
    arr = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    if ch == 1:
        arr = np.stack([arr, arr], axis=1)
    else:
        arr = arr.reshape(-1, ch)[:, :2]
    return arr, sr


def _write_wav_float(path: Path, signal: np.ndarray, sr: int = 48000) -> None:
    clipped = np.clip(signal, -0.99, 0.99)
    pcm = (clipped * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def prepare_project(spec: dict, source_dir: Path, build_dir: Path) -> dict:
    """Prepare all video segments and mixed/stem audio into `build_dir/prepared`."""
    ffmpeg = _ffmpeg()
    spec, total_dur = compute_timeline(spec)
    fps = int(spec.get("fps", 30))

    prep_dir = build_dir / "prepared"
    clips_dir = prep_dir / "clips"
    audio_dir = prep_dir / "audio"
    nat_dir = audio_dir / "nat_clips"
    for d in (clips_dir, audio_dir, nat_dir):
        d.mkdir(parents=True, exist_ok=True)

    media_meta: Dict[str, dict] = {}
    sr = 48000
    total_samples = int(math.ceil((total_dur + 0.5) * sr))
    nat_timeline = np.zeros((total_samples, 2), dtype=np.float64)
    duck_envelope = np.ones(total_samples, dtype=np.float64)

    bgm_cfg = spec.get("bgm", {})
    duck_db = float(bgm_cfg.get("duck_db", -5.5))
    duck_linear = 10.0 ** (duck_db / 20.0)

    prepared_manifest = {
        "project_id": spec["project_id"],
        "fps": fps,
        "width": int(spec.get("width", 1080)),
        "height": int(spec.get("height", 1920)),
        "duration": total_dur,
        "clips": {},
        "nat_audio_events": [],
    }

    for shot in spec["shots"]:
        sid = shot["id"]
        dur = float(shot["duration"])
        t_start = float(shot["timeline_start"])

        for c in shot["clips"]:
            slot = c["slot"]
            src_name = c["source"]
            src_path = source_dir / src_name
            if src_name not in media_meta:
                media_meta[src_name] = probe_media(src_path)
            m_info = media_meta[src_name]

            start = float(c.get("start", 0.0))
            speed = float(c.get("speed", 1.0))
            # Add tiny 0.15s tail pad so frame rounding never hits EOF early
            src_read_dur = min(dur * speed + 0.15, max(0.2, m_info["duration"] - start))
            clip_key = f"{sid}_{slot}"
            out_video = clips_dir / f"{clip_key}.mp4"

            # Subtle per-camera exposure/color harmonization
            gamma = float(c.get("gamma", 1.06 if src_name == "C0409.MP4" else 1.03))
            contrast = float(c.get("contrast", 1.03))
            saturation = float(c.get("saturation", 1.04))

            # Scale max dimension to 1920 while preserving display aspect ratio (auto-rotates phone video!)
            max_dim = 1920
            vf_parts = ["setpts=PTS-STARTPTS"]
            if abs(speed - 1.0) > 1e-3:
                vf_parts.append(f"setpts=PTS/{speed:.4f}")
            vf_parts.extend([
                f"scale='if(gt(iw,ih),min({max_dim},iw),-2)':'if(gt(iw,ih),-2,min({max_dim},ih))':flags=lanczos",
                "setsar=1",
                f"fps={fps}",
                f"eq=contrast={contrast}:gamma={gamma}:saturation={saturation}",
                "format=yuv420p",
            ])

            out_dur = round(dur + 0.12, 3)
            print(f"[prepare] Trimming {clip_key} <- {src_name} @{start:.2f}s ({dur:.2f}s) ...", flush=True)
            subprocess.run(
                [
                    ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                    "-threads", "4", "-ss", f"{start:.3f}", "-i", str(src_path),
                    "-t", f"{src_read_dur:.3f}", "-an",
                    "-vf", ",".join(vf_parts),
                    "-c:v", "h264_videotoolbox", "-b:v", "14M", "-profile:v", "high",
                    "-g", "15", "-pix_fmt", "yuv420p",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-t", f"{out_dur:.3f}",
                    str(out_video),
                ],
                check=True,
            )

            out_info = probe_media(out_video)
            prepared_manifest["clips"][clip_key] = {
                "file": out_video.name,
                "path": str(out_video.resolve()),
                "width": out_info["display_width"],
                "height": out_info["display_height"],
                "duration": out_info["duration"],
                "source": src_name,
                "source_start": start,
            }

            # Optional natural audio extraction & cleanup
            if c.get("keep_audio", False) and m_info["has_audio"]:
                nat_wav = nat_dir / f"{clip_key}.wav"
                hp = int(c.get("audio_highpass_hz", 180))
                lp = int(c.get("audio_lowpass_hz", 7200))
                gain_db = float(c.get("audio_gain_db", 0.0))
                af_parts = [
                    f"highpass=f={hp}",
                    f"lowpass=f={lp}",
                    "afftdn=nf=-24",
                ]
                if abs(speed - 1.0) > 1e-3 and 0.5 <= speed <= 2.0:
                    af_parts.append(f"atempo={speed:.4f}")
                if abs(gain_db) > 0.05:
                    af_parts.append(f"volume={gain_db:.2f}dB")
                fade_out_st = max(0.05, dur - 0.12)
                af_parts.append("afade=t=in:st=0:d=0.08")
                af_parts.append(f"afade=t=out:st={fade_out_st:.3f}:d=0.12")

                subprocess.run(
                    [
                        ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                        "-ss", f"{start:.3f}", "-i", str(src_path), "-t", f"{dur * speed:.3f}",
                        "-vn", "-af", ",".join(af_parts),
                        "-ar", str(sr), "-ac", "2", "-c:a", "pcm_s16le",
                        "-t", f"{dur:.3f}", str(nat_wav),
                    ],
                    check=True,
                )
                nat_sig, _ = _read_wav_float(nat_wav)
                s_idx = int(round(t_start * sr))
                e_idx = min(total_samples, s_idx + len(nat_sig))
                if e_idx > s_idx:
                    nat_timeline[s_idx:e_idx] += nat_sig[: e_idx - s_idx]
                    # Apply smooth ducking window with 0.25s attack/release ramps
                    ramp = int(0.25 * sr)
                    d_start = max(0, s_idx - ramp)
                    d_end = min(total_samples, e_idx + ramp)
                    win = np.full(d_end - d_start, duck_linear, dtype=np.float64)
                    if s_idx - d_start > 0:
                        win[: s_idx - d_start] = np.linspace(1.0, duck_linear, s_idx - d_start)
                    if d_end - e_idx > 0:
                        win[-(d_end - e_idx) :] = np.linspace(duck_linear, 1.0, d_end - e_idx)
                    duck_envelope[d_start:d_end] = np.minimum(duck_envelope[d_start:d_end], win)

                prepared_manifest["nat_audio_events"].append({
                    "id": f"nat_{clip_key}",
                    "path": str(nat_wav.resolve()),
                    "timeline_start": t_start,
                    "duration": dur,
                    "source": src_name,
                })

    # Prepare BGM stem + Master Mix
    n_exact = int(round(total_dur * sr))
    nat_exact = nat_timeline[:n_exact]
    nat_stem_path = audio_dir / "nat_stem.wav"
    _write_wav_float(nat_stem_path, nat_exact, sr=sr)

    bgm_file = bgm_cfg.get("file")
    bgm_exact = np.zeros((n_exact, 2), dtype=np.float64)
    bgm_trimmed_path = None

    if bgm_file:
        bgm_src = Path(bgm_file)
        if not bgm_src.is_absolute():
            bgm_src = (build_dir.parents[1] / bgm_file).resolve() if not (build_dir / bgm_file).exists() else (build_dir / bgm_file).resolve()
        bgm_start = float(bgm_cfg.get("start", 0.0))
        bgm_vol_db = float(bgm_cfg.get("volume_db", -12.0))
        fade_in = float(bgm_cfg.get("fade_in", 0.35))
        fade_out = float(bgm_cfg.get("fade_out", 1.1))
        bgm_trimmed_path = audio_dir / "bgm_trimmed.wav"

        af_bgm = [
            f"volume={bgm_vol_db:.2f}dB",
            f"afade=t=in:st=0:d={fade_in:.2f}",
            f"afade=t=out:st={max(0.1, total_dur - fade_out):.2f}:d={fade_out:.2f}",
        ]
        subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-ss", f"{bgm_start:.3f}", "-stream_loop", "-1", "-i", str(bgm_src),
                "-vn", "-af", ",".join(af_bgm),
                "-ar", str(sr), "-ac", "2", "-c:a", "pcm_s16le",
                "-t", f"{total_dur:.3f}", str(bgm_trimmed_path),
            ],
            check=True,
        )
        bgm_raw, _ = _read_wav_float(bgm_trimmed_path)
        if len(bgm_raw) >= n_exact:
            bgm_exact = bgm_raw[:n_exact]
        else:
            bgm_exact[: len(bgm_raw)] = bgm_raw

    raw_mix = bgm_exact * duck_envelope[:n_exact, None] + nat_exact
    raw_mix_path = audio_dir / "raw_mix.wav"
    _write_wav_float(raw_mix_path, raw_mix, sr=sr)

    master_mix_path = audio_dir / "master_mix.wav"
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-i", str(raw_mix_path),
            "-af", "loudnorm=I=-15.5:TP=-1.5:LRA=9",
            "-ar", str(sr), "-ac", "2", "-c:a", "pcm_s16le",
            "-t", f"{total_dur:.3f}", str(master_mix_path),
        ],
        check=True,
    )

    prepared_manifest["master_audio"] = str(master_mix_path.resolve())
    prepared_manifest["bgm_stem"] = str(bgm_trimmed_path.resolve()) if bgm_trimmed_path else None
    prepared_manifest["nat_stem"] = str(nat_stem_path.resolve())

    manifest_path = prep_dir / "manifest.json"
    manifest_path.write_text(json.dumps(prepared_manifest, ensure_ascii=False, indent=2))
    print(f"[prepare] Done -> {manifest_path}", flush=True)
    return prepared_manifest
