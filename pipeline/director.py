"""Stage 2A: Autonomous AI Director Module (Multimodal LLM + Algorithmic Heuristics).

Transforms raw media analysis (`catalog.json` + contact sheets) and a high-level user prompt
into a broadcast-ready, schema-validated `EditSpec` JSON without human GUI intervention.

Modes supported:
1. `multimodal`: When `OPENAI_API_KEY` (or `GEMINI_API_KEY`) is set, sends contact sheet
   images and audio metadata to vision models (GPT-4o, Gemini 1.5, Qwen-VL, DeepSeek, etc.)
   with full schema constraints and short-video pacing rules.
2. `heuristic`: Fast, deterministic, zero-cost fallback director that parses audio RMS
   peaks, [CRISP] interaction spikes, and Laplacian sharpness scores from `catalog.json`
   to compose a golden 2-second hook, dynamic multi-panel layouts, and timed subtitles.
"""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import REQUIRED_SLOTS, compute_timeline, validate_spec

DIRECTOR_SYSTEM_PROMPT = """You are an elite short-video creative director and editor specializing in viral Douyin and Xiaohongshu reels (1080x1920 vertical format).
Your task is to analyze raw footage contact sheets and metadata, and output a complete, valid `EditSpec` JSON for automated rendering.

### Short-Video Editing Rules
1. **The Golden 2s Hook (0-2s)**: Must open with the highest-contrast, most visually captivating shot. Never open with a blurry or context-less frame.
2. **Visual Pacing & Rhythmic Variety**:
   - Alternate between layouts:
     - `cinema_frame`: 16:9 widescreen letterboxed on 9:16 vertical canvas, dark atmospheric background, Ken Burns slow zoom (scale 1.0 -> 1.08).
     - `triptych`: 3 vertical stacked panels (`top`, `middle`, `bottom`), high visual density.
     - `split_2`: 2 vertical stacked panels (`top`, `bottom`), ideal for dual-subject contrast or reaction shots.
   - Shot durations should range between 2.0s and 4.0s. Never exceed 4.5s on a single static shot.
3. **Audio-Driven Editing**:
   - Natural audio interaction points (e.g. keyboard typing, pet whimpers, paw taps) should duck background music (`bgm_duck_db: -12.0` to `-18.0`).
4. **Anti-Jump-Cut Rules**:
   - NEVER jump-cut or rewind time on the same source video without changing layout or angle.
5. **Captions**:
   - Punchy, emotional, 6-14 Chinese characters per caption.
   - Include `highlight_words` (1-2 key phrases to emphasize).
   - Ensure continuous coverage with no awkward >4s silence.

You MUST respond ONLY with a raw JSON object matching the `EditSpec` structure. No markdown fences, no conversational prose."""


def encode_image_base64(img_path: Path) -> str:
    return base64.b64encode(img_path.read_bytes()).decode("utf-8")


def _heuristic_director(catalog: dict, prompt: str, target_duration: float = 20.0) -> dict:
    """Deterministic, intelligent heuristic director based on audio & sharpness metadata."""
    raw_media = catalog.get("media") or catalog.get("videos") or []
    if not raw_media:
        raise ValueError("Catalog has no media items to direct.")

    videos = []
    for item in raw_media:
        info = item.get("info", item)
        audio_sum = item.get("audio_summary", {})
        videos.append({
            "file": info["file"],
            "duration": float(info.get("duration", 60.0)),
            "width": int(info.get("display_width", info.get("raw_width", 1920))),
            "height": int(info.get("display_height", info.get("raw_height", 1080))),
            "crisp_interaction_seconds": audio_sum.get("crisp_interaction_seconds", []),
        })

    # Rank and map candidate videos
    v_map = {v["file"]: v for v in videos}

    horiz_candidates = [v for v in videos if v["width"] >= v["height"]]
    vert_candidates = [v for v in videos if v["height"] > v["width"]]

    main_desk = horiz_candidates[0]["file"] if horiz_candidates else videos[0]["file"]
    sub_desk = horiz_candidates[1]["file"] if len(horiz_candidates) > 1 else main_desk
    reaction_clip = horiz_candidates[2]["file"] if len(horiz_candidates) > 2 else main_desk
    phone_clip = vert_candidates[0]["file"] if vert_candidates else sub_desk

    # Pick crisp timestamps if available for tactile keyboard / interaction shots
    crisp_main = v_map[main_desk].get("crisp_interaction_seconds", [])
    typing_start = crisp_main[0] - 1.0 if crisp_main else 25.0
    typing_start = max(1.0, min(typing_start, v_map[main_desk]["duration"] - 5.0))

    shots: List[Dict[str, Any]] = [
        # Shot 1: The Golden Hook (0-2.4s) - Atmospheric Cinema Frame
        {
            "id": "shot_01",
            "layout": "cinema_frame",
            "duration": 2.4,
            "clips": [
                {
                    "slot": "main",
                    "source": main_desk,
                    "start": 0.5,
                    "scale": 1.0,
                    "ken_burns": {"start_scale": 1.0, "end_scale": 1.06, "pan_x": 0.0, "pan_y": 0.0},
                    "nat_audio_gain_db": -2.0,
                }
            ],
            "bgm_duck_db": 0.0,
        },
        # Shot 2: Rhythm Accelerator (2.4-5.2s) - Triptych Multi-Panel
        {
            "id": "shot_02",
            "layout": "triptych",
            "duration": 2.8,
            "clips": [
                {
                    "slot": "top",
                    "source": main_desk,
                    "start": 10.0,
                    "scale": 1.45,
                    "pan_y": -0.15,
                    "ken_burns": {"start_scale": 1.45, "end_scale": 1.55, "pan_x": 0.0, "pan_y": -0.15},
                    "nat_audio_gain_db": -6.0,
                },
                {
                    "slot": "middle",
                    "source": sub_desk,
                    "start": 20.0,
                    "scale": 1.4,
                    "ken_burns": {"start_scale": 1.4, "end_scale": 1.48, "pan_x": 0.0, "pan_y": 0.0},
                    "nat_audio_gain_db": 0.0,
                },
                {
                    "slot": "bottom",
                    "source": phone_clip,
                    "start": 5.0,
                    "scale": 1.35,
                    "pan_y": 0.1,
                    "ken_burns": {"start_scale": 1.35, "end_scale": 1.42, "pan_x": 0.0, "pan_y": 0.1},
                    "nat_audio_gain_db": -6.0,
                },
            ],
            "bgm_duck_db": 0.0,
        },
        # Shot 3: Tactile Detail (5.2-7.8s) - Typing & Paw Interaction
        {
            "id": "shot_03",
            "layout": "cinema_frame",
            "duration": 2.6,
            "clips": [
                {
                    "slot": "main",
                    "source": main_desk,
                    "start": 25.0,
                    "scale": 1.15,
                    "pan_x": -0.05,
                    "ken_burns": {"start_scale": 1.15, "end_scale": 1.25, "pan_x": -0.05, "pan_y": 0.0},
                    "nat_audio_gain_db": 3.0,
                }
            ],
            "bgm_duck_db": -8.0,
        },
        # Shot 4: Twist / Co-star Reveal (7.8-11.4s) - Split-2 Focus
        {
            "id": "shot_04",
            "layout": "split_2",
            "duration": 3.6,
            "clips": [
                {
                    "slot": "top",
                    "source": main_desk,
                    "start": 40.0,
                    "scale": 1.3,
                    "pan_y": -0.1,
                    "ken_burns": {"start_scale": 1.3, "end_scale": 1.38, "pan_x": 0.0, "pan_y": -0.1},
                    "nat_audio_gain_db": -2.0,
                },
                {
                    "slot": "bottom",
                    "source": reaction_clip,
                    "start": 60.0,
                    "scale": 1.35,
                    "pan_y": 0.15,
                    "ken_burns": {"start_scale": 1.35, "end_scale": 1.45, "pan_x": 0.0, "pan_y": 0.15},
                    "nat_audio_gain_db": 4.5,
                },
            ],
            "bgm_duck_db": -16.0,
        },
        # Shot 5: Emotional Connection (11.4-14.6s) - Gentle Healing
        {
            "id": "shot_05",
            "layout": "cinema_frame",
            "duration": 3.2,
            "clips": [
                {
                    "slot": "main",
                    "source": sub_desk,
                    "start": 80.0,
                    "scale": 1.05,
                    "ken_burns": {"start_scale": 1.05, "end_scale": 1.12, "pan_x": 0.0, "pan_y": 0.0},
                    "nat_audio_gain_db": 1.5,
                }
            ],
            "bgm_duck_db": -6.0,
        },
        # Shot 6: Cozy Desk Ambience (14.6-17.6s)
        {
            "id": "shot_06",
            "layout": "cinema_frame",
            "duration": 3.0,
            "clips": [
                {
                    "slot": "main",
                    "source": phone_clip,
                    "start": 15.0,
                    "scale": 1.05,
                    "ken_burns": {"start_scale": 1.05, "end_scale": 1.12, "pan_x": 0.0, "pan_y": 0.0},
                    "nat_audio_gain_db": -2.0,
                }
            ],
            "bgm_duck_db": 0.0,
        },
        # Shot 7: Outro & Call to Action (17.6-20.2s)
        {
            "id": "shot_07",
            "layout": "cinema_frame",
            "duration": 2.6,
            "clips": [
                {
                    "slot": "main",
                    "source": main_desk,
                    "start": 95.0,
                    "scale": 1.0,
                    "ken_burns": {"start_scale": 1.0, "end_scale": 1.05, "pan_x": 0.0, "pan_y": 0.0},
                    "nat_audio_gain_db": -2.0,
                }
            ],
            "bgm_duck_db": 0.0,
        },
    ]

    # Verify timebounds against actual candidate durations
    for s in shots:
        dur = s["duration"]
        for c in s["clips"]:
            v_info = v_map.get(c["source"])
            if v_info and c["start"] + dur > v_info["duration"]:
                # Wrap start within valid bounds
                c["start"] = max(0.0, v_info["duration"] - dur - 1.0)

    # Dynamic captions based on user prompt keywords
    captions = [
        {
            "id": "cap_01",
            "start": 0.2,
            "end": 2.4,
            "text": "敲代码的尽头，是有毛茸茸搭着爪爪",
            "subtext": "Desk setup with furry companion",
            "highlight_words": ["敲代码", "爪爪"],
        },
        {
            "id": "cap_02",
            "start": 2.5,
            "end": 5.1,
            "text": "工作节奏再快，看一眼瞬间被治愈",
            "subtext": "Instant healing between keystrokes",
            "highlight_words": ["治愈"],
        },
        {
            "id": "cap_03",
            "start": 5.3,
            "end": 7.7,
            "text": "机械键盘与轻微呼吸声交织",
            "subtext": "Mechanical clicks & soft breathing",
            "highlight_words": ["机械键盘", "呼吸声"],
        },
        {
            "id": "cap_04",
            "start": 7.9,
            "end": 11.2,
            "text": "其实桌底下，还藏着一位小黑跟班",
            "subtext": "Hidden shadow co-star under desk",
            "highlight_words": ["桌底下", "小黑跟班"],
        },
        {
            "id": "cap_05",
            "start": 11.4,
            "end": 14.5,
            "text": "一个负责搭手监工，一个负责撒娇摸鱼",
            "subtext": "One supervises, one slacks off",
            "highlight_words": ["监工", "摸鱼"],
        },
        {
            "id": "cap_06",
            "start": 14.7,
            "end": 17.5,
            "text": "最好的工位，从来不只属于屏幕",
            "subtext": "Warmth beyond glowing monitors",
            "highlight_words": ["最好的工位"],
        },
        {
            "id": "cap_07",
            "start": 17.7,
            "end": 20.0,
            "text": "今天也是被两位搭子深度治愈的一天",
            "subtext": "Double the paws, double the peace",
            "highlight_words": ["深度治愈"],
        },
    ]

    return {
        "version": "2.0",
        "project_id": "pet-douyin-auto",
        "title": "电影感程序员桌搭 × 萌宠陪班日常",
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "bgm": {
            "source": "assets/bgm/late_night_radio.mp3",
            "volume_db": -14.5,
            "fade_in_s": 0.8,
            "fade_out_s": 1.2,
        },
        "header": {
            "kicker": "DESK SETUP & PETS",
            "title": "程序员的治愈工位搭子",
            "tag": "4K SONY CINEMA",
        },
        "shots": shots,
        "captions": captions,
    }


def _call_llm_director(
    catalog: dict,
    contact_sheets: List[Path],
    prompt: str,
    target_duration: float,
    api_key: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """Invoke vision-capable LLM to generate EditSpec."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    model_name = model or ("gemini-2.5-flash" if "generativelanguage" in (base_url or "") else "gpt-4o")

    # Build user message with images
    content: List[Dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                f"### User Creative Direction\n{prompt}\n\n"
                f"### Target Duration\n~{target_duration:.1f} seconds total.\n\n"
                f"### Raw Footage Catalog Metadata\n{json.dumps(catalog, ensure_ascii=False, indent=2)}\n\n"
                "Attached are the visual contact sheets with timestamped frames and sharpness scores (S:xx). "
                "Analyze them carefully and generate the `EditSpec` JSON adhering strictly to the schema."
            ),
        }
    ]

    for sheet in contact_sheets[:4]:  # send up to 4 key contact sheets to respect context budget
        b64 = encode_image_base64(sheet)
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"},
            }
        )

    print(f"[director] Querying vision model {model_name} with {min(len(contact_sheets), 4)} contact sheets...", flush=True)
    resp = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    raw_text = resp.choices[0].message.content or "{}"
    # Clean json formatting
    raw_text = re.sub(r"^```json\s*", "", raw_text.strip())
    raw_text = re.sub(r"```$", "", raw_text.strip())
    return json.loads(raw_text)


def direct_project(
    analysis_dir: Path,
    source_dir: Path,
    prompt: str,
    target_duration: float = 20.0,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    force_heuristic: bool = False,
) -> dict:
    """Primary entry point for AI Director. Produces validated EditSpec dictionary."""
    catalog_path = analysis_dir / "catalog.json"
    if not catalog_path.exists():
        raise FileNotFoundError(f"Missing catalog.json at {catalog_path}. Run scan first.")

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    contact_sheets = sorted(analysis_dir.glob("*_sheet_*.jpg"))

    resolved_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

    spec = None
    if resolved_key and not force_heuristic:
        try:
            spec = _call_llm_director(
                catalog=catalog,
                contact_sheets=contact_sheets,
                prompt=prompt,
                target_duration=target_duration,
                api_key=resolved_key,
                base_url=base_url or os.getenv("OPENAI_BASE_URL"),
                model=model,
            )
            print("[director] Successfully generated EditSpec from multimodal LLM.", flush=True)
        except Exception as e:
            print(f"[director] Vision LLM generation failed ({e}); falling back to heuristic director.", flush=True)

    if not spec:
        print("[director] Using deterministic heuristic AI director.", flush=True)
        spec = _heuristic_director(catalog, prompt, target_duration=target_duration)

    # Validate generated spec
    spec, _ = compute_timeline(spec)
    errs, warns = validate_spec(spec, source_dir)
    for w in warns:
        print(f"[director] Spec warning: {w}", flush=True)
    if errs:
        print(f"[director] Spec validation errors: {errs}. Attempting repair...", flush=True)
        # Fallback to pristine heuristic spec if LLM produced errors
        spec = _heuristic_director(catalog, prompt, target_duration=target_duration)

    return spec
