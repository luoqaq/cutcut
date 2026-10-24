"""Stage 4B: Dual-Format Jianying Pro Exporter (Native Mac 11.4 Draft + FCPXML + SRT).

Generates editable project files alongside Remotion's finished MP4 render:
1. `captions.srt` — Standard SRT subtitles
2. `timeline.fcpxml` — Final Cut Pro XML v1.9 multi-track timeline
3. `native_draft/` + `install_to_jianying.py` — Mac Jianying Pro 11.4 native draft bundle
   with independent video layers, separate BGM & natural sound stems, and editable native text objects.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid5

from .schema import compute_timeline

NAMESPACE_CUT = UUID("8b7d31e2-6412-4a8e-9b28-1f90c3e7d201")

MATERIAL_GROUPS = (
    "ai_translates audio_balances audio_effects audio_fades audio_track_indexes "
    "audios beats canvases chromas color_curves digital_humans drafts effects "
    "flowers green_screens handwrites hsl images log_color_wheels loudnesses "
    "manual_deformations masks material_animations material_colors "
    "multi_language_refs placeholders plugin_effects primary_color_wheels "
    "realtime_denoises shapes smart_crops smart_relights sound_channel_mappings "
    "speeds stickers tail_leaders text_templates texts time_marks transitions "
    "video_effects video_trackings videos vocal_beautifys vocal_separations"
).split()


def _us(seconds: float) -> int:
    return max(0, int(round(float(seconds) * 1_000_000)))


def _srt_time(seconds: float) -> str:
    ms_total = max(0, int(round(seconds * 1000)))
    hh = ms_total // 3_600_000
    mm = (ms_total % 3_600_000) // 60_000
    ss = (ms_total % 60_000) // 1000
    ms = ms_total % 1000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def write_srt(spec: dict, out_path: Path) -> Path:
    lines = []
    for idx, cap in enumerate(spec.get("captions", []), start=1):
        text = cap["text"]
        if cap.get("subtext"):
            text = f"{text}\n{cap['subtext']}"
        lines.append(f"{idx}\n{_srt_time(cap['start'])} --> {_srt_time(cap['end'])}\n{text}\n")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def write_fcpxml(spec: dict, manifest: dict, out_path: Path) -> Path:
    spec, total_dur = compute_timeline(spec)
    fps = int(spec.get("fps", 30))
    w = int(spec.get("width", 1080))
    h = int(spec.get("height", 1920))

    def ftime(sec: float) -> str:
        frames = int(round(sec * fps))
        return f"{frames}/{fps}s"

    assets_xml = []
    asset_ids = {}
    idx_counter = 1

    for key, info in manifest["clips"].items():
        aid = f"r{idx_counter + 1}"
        idx_counter += 1
        asset_ids[key] = aid
        uri = Path(info["path"]).as_uri()
        assets_xml.append(
            f'    <asset id="{aid}" name="{html.escape(key)}" src="{html.escape(uri)}" '
            f'start="0s" duration="{ftime(info["duration"])}" hasVideo="1" hasAudio="0" format="r1"/>'
        )

    bgm_aid = None
    if manifest.get("bgm_stem"):
        bgm_aid = f"r{idx_counter + 1}"
        idx_counter += 1
        uri = Path(manifest["bgm_stem"]).as_uri()
        assets_xml.append(
            f'    <asset id="{bgm_aid}" name="bgm_stem" src="{html.escape(uri)}" '
            f'start="0s" duration="{ftime(total_dur)}" hasVideo="0" hasAudio="1"/>'
        )

    nat_aid = None
    if manifest.get("nat_stem"):
        nat_aid = f"r{idx_counter + 1}"
        idx_counter += 1
        uri = Path(manifest["nat_stem"]).as_uri()
        assets_xml.append(
            f'    <asset id="{nat_aid}" name="nat_stem" src="{html.escape(uri)}" '
            f'start="0s" duration="{ftime(total_dur)}" hasVideo="0" hasAudio="1"/>'
        )

    spine_xml = []
    for shot in spec["shots"]:
        sid = shot["id"]
        t0 = shot["timeline_start"]
        dur = shot["duration"]
        layout = shot["layout"]

        primary_slot = "middle" if layout == "triptych" else ("top" if layout == "split_2" else "main")
        main_key = f"{sid}_{primary_slot}"
        aid = asset_ids[main_key]

        attached = []
        if layout == "triptych":
            for lane, slot in [(1, "top"), (2, "bottom")]:
                sub_key = f"{sid}_{slot}"
                said = asset_ids[sub_key]
                attached.append(
                    f'          <asset-clip name="{html.escape(sub_key)}" lane="{lane}" ref="{said}" '
                    f'offset="0s" start="0s" duration="{ftime(dur)}"/>'
                )
        elif layout == "split_2":
            sub_key = f"{sid}_bottom"
            said = asset_ids[sub_key]
            attached.append(
                f'          <asset-clip name="{html.escape(sub_key)}" lane="1" ref="{said}" '
                f'offset="0s" start="0s" duration="{ftime(dur)}"/>'
            )

        if shot["index"] == 0:
            if bgm_aid:
                attached.append(
                    f'          <asset-clip name="BGM" lane="-1" ref="{bgm_aid}" '
                    f'offset="0s" start="0s" duration="{ftime(total_dur)}" role="music"/>'
                )
            if nat_aid:
                attached.append(
                    f'          <asset-clip name="NatSound" lane="-2" ref="{nat_aid}" '
                    f'offset="0s" start="0s" duration="{ftime(total_dur)}" role="dialogue"/>'
                )

        if attached:
            inner = "\n".join(attached)
            spine_xml.append(
                f'        <asset-clip name="{html.escape(main_key)}" ref="{aid}" '
                f'offset="{ftime(t0)}" start="0s" duration="{ftime(dur)}">\n{inner}\n        </asset-clip>'
            )
        else:
            spine_xml.append(
                f'        <asset-clip name="{html.escape(main_key)}" ref="{aid}" '
                f'offset="{ftime(t0)}" start="0s" duration="{ftime(dur)}"/>'
            )

    xml_text = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
  <resources>
    <format id="r1" name="FFVideoFormat{w}x{h}p{fps}" frameDuration="1/{fps}s" width="{w}" height="{h}"/>
{chr(10).join(assets_xml)}
  </resources>
  <library>
    <event name="{html.escape(spec.get('title', spec['project_id']))}">
      <project name="{html.escape(spec.get('title', spec['project_id']))}">
        <sequence format="r1" duration="{ftime(total_dur)}" tcStart="0s" tcFormat="NDF">
          <spine>
{chr(10).join(spine_xml)}
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
"""
    out_path.write_text(xml_text, encoding="utf-8")
    return out_path


def _platform() -> dict:
    return {
        "app_id": 3704,
        "app_source": "lv",
        "app_version": "11.4.0",
        "os": "mac",
        "os_version": "",
        "device_id": "",
        "hard_disk_id": "",
        "mac_address": "",
    }


def build_jianying_native_bundle(
    spec: dict,
    manifest: dict,
    export_dir: Path,
    target_draft_root: Path | None = None,
) -> dict:
    """Create a standalone native Jianying draft folder + safe installer script."""
    spec, total_dur = compute_timeline(spec)
    project_name = f"CutCut-{spec['project_id']}"
    project_uuid = uuid5(NAMESPACE_CUT, project_name)
    project_id = str(project_uuid).upper()

    bundle_dir = export_dir / "native_draft" / project_name
    res_dir = bundle_dir / "Resources"
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    res_dir.mkdir(parents=True, exist_ok=True)

    # Determine final path prefix that Jianying will see when installed into draft_root
    if target_draft_root is None:
        target_draft_root = Path.home() / "Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    final_project_dir = (target_draft_root / project_name).resolve()

    def ident(label: str) -> str:
        return str(uuid5(project_uuid, label)).upper()

    materials = {g: [] for g in MATERIAL_GROUPS}
    registry = []
    tracks: dict[tuple[str, str], dict] = {}
    copied_files: dict[str, str] = {}
    media_materials: dict[str, dict] = {}

    def ensure_track(t_type: str, t_name: str) -> dict:
        key = (t_type, t_name)
        if key not in tracks:
            tracks[key] = {
                "id": ident(f"track:{t_type}:{t_name}"),
                "type": t_type,
                "name": t_name,
                "is_default_name": False,
                "attribute": 0,
                "flag": 0,
                "segments": [],
            }
        return tracks[key]

    def register_media(src_path: str, kind: str, width: int, height: int, dur_s: float, label: str) -> str:
        src_p = Path(src_path).resolve()
        if str(src_p) not in copied_files:
            ext = src_p.suffix.lower()
            fname = f"{len(copied_files) + 1:04d}_{src_p.stem}{ext}"
            shutil.copy2(src_p, res_dir / fname)
            copied_files[str(src_p)] = fname
        final_media_path = str(final_project_dir / "Resources" / copied_files[str(src_p)])
        m_key = f"{kind}:{final_media_path}"
        dur_us = _us(dur_s)

        if m_key not in media_materials:
            mid = ident(f"mat:{m_key}")
            if kind == "video":
                mat = {
                    "id": mid, "type": "video", "path": final_media_path,
                    "material_name": label, "duration": dur_us,
                    "width": width, "height": height, "has_audio": False,
                    "check_flag": 63487, "local_material_id": "", "local_id": "",
                    "material_id": mid, "origin_material_id": "", "material_url": "",
                    "media_path": "", "source": 0, "source_platform": 0,
                    "category_id": "", "category_name": "", "team_id": "",
                    "request_id": "", "formula_id": "", "picture_from": "none",
                    "picture_set_category_id": "", "picture_set_category_name": "",
                    "aigc_type": "none", "aigc_item_id": "", "aigc_history_id": "",
                    "audio_fade": None, "cartoon_path": "", "freeze": None,
                    "crop": {
                        "upper_left_x": 0.0, "upper_left_y": 0.0,
                        "upper_right_x": 1.0, "upper_right_y": 0.0,
                        "lower_left_x": 0.0, "lower_left_y": 1.0,
                        "lower_right_x": 1.0, "lower_right_y": 1.0,
                    },
                    "crop_ratio": "free", "crop_scale": 1.0, "extra_type_option": 0,
                    "is_ai_generate_content": False, "is_copyright": False,
                    "is_text_edit_overdub": False, "is_unified_beauty_mode": False,
                    "intensifies_path": "", "intensifies_audio_path": "",
                    "reverse_path": "", "reverse_intensifies_path": "",
                    "object_locked": None, "smart_motion": None,
                    "matting": {"flag": 0, "has_use_quick_brush": False, "has_use_quick_eraser": False, "interactiveTime": [], "path": "", "strokes": []},
                    "stable": {"matrix_path": "", "stable_level": 0, "time_range": {"start": 0, "duration": 0}},
                    "video_algorithm": {"algorithms": [], "complement_frame_config": None, "deflicker": None, "gameplay_configs": [], "motion_blur_config": None, "noise_reduction": None, "path": "", "quality_enhance": None, "time_range": None},
                }
                materials["videos"].append(mat)
            else:
                mat = dict.fromkeys((
                    "aigc_history_id aigc_item_id category_id category_name effect_id "
                    "formula_id intensifies_path local_material_id music_id query "
                    "request_id resource_id search_id source_from team_id text_id "
                    "tone_category_id tone_category_name tone_effect_id tone_effect_name "
                    "tone_platform tone_second_category_id tone_second_category_name "
                    "tone_speaker tone_type video_id"
                ).split(), "")
                mat.update({
                    "id": mid, "type": "extract_music", "app_id": 0,
                    "path": final_media_path, "name": label,
                    "duration": dur_us, "check_flag": 1, "source_platform": 0,
                    "copyright_limit_type": "none", "is_ai_clone_tone": False,
                    "is_text_edit_overdub": False, "is_ugc": False, "wave_points": [],
                })
                materials["audios"].append(mat)

            media_materials[m_key] = mat
            registry.append({
                "id": ident(f"reg:{m_key}"), "type": 0,
                "metetype": "video" if kind == "video" else "music",
                "file_Path": final_media_path, "extra_info": label,
                "width": width, "height": height, "duration": dur_us,
                "create_time": 0, "import_time": 0, "import_time_ms": 0, "item_source": 1,
                "md5": "", "roughcut_time_range": {"start": -1, "duration": -1},
                "sub_time_range": {"start": -1, "duration": -1},
            })
        return media_materials[m_key]["id"]

    def make_segment(seg_key: str, mid: str, kind: str, start_s: float, dur_s: float, tx: float = 0.0, ty: float = 0.0, scale: float = 1.0, vol: float = 1.0) -> dict:
        refs = []
        if kind != "text":
            sp_id = ident(f"speed:{seg_key}")
            materials["speeds"].append({"id": sp_id, "type": "speed", "mode": 0, "speed": 1.0, "curve_speed": None})
            ch_id = ident(f"chan:{seg_key}")
            materials["sound_channel_mappings"].append({"id": ch_id, "type": "none", "audio_channel_mapping": 0, "is_config_open": False})
            vc_id = ident(f"vocal:{seg_key}")
            materials["vocal_separations"].append({"id": vc_id, "type": "vocal_separation", "choice": 0, "production_path": "", "time_range": None})
            refs.extend([sp_id, ch_id, vc_id])
        if kind == "video":
            cv_id = ident(f"canvas:{seg_key}")
            materials["canvases"].append({"id": cv_id, "type": "canvas_color", "color": "", "blur": 0.0, "album_image": "", "image": "", "image_id": "", "image_name": "", "team_id": "", "source_platform": 0})
            refs.append(cv_id)

        visual = None if kind == "audio" else {
            "alpha": 1.0,
            "flip": {"horizontal": False, "vertical": False},
            "rotation": 0.0,
            "scale": {"x": scale, "y": scale},
            "transform": {"x": tx, "y": ty},
        }
        return {
            "id": ident(f"seg:{seg_key}"),
            "material_id": mid,
            "extra_material_refs": refs,
            "source_timerange": None if kind == "text" else {"start": 0, "duration": _us(dur_s)},
            "target_timerange": {"start": _us(start_s), "duration": _us(dur_s)},
            "speed": 1.0,
            "volume": vol,
            "last_nonzero_volume": vol if vol else 1.0,
            "clip": visual,
            "visible": True,
            "reverse": False,
            "track_attribute": 0,
            "track_render_index": 0,
            "render_index": 0,
            "caption_info": None,
            "cartoon": False,
            "group_id": "",
            "common_keyframes": [],
            "keyframe_refs": [],
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "enable_adjust": kind == "video",
            "enable_lut": kind == "video",
            "enable_color_correct_adjust": False,
            "enable_color_curves": True,
            "enable_color_match_adjust": False,
            "enable_color_wheels": True,
            "enable_smart_color_adjust": False,
            "hdr_settings": None if kind == "audio" else {"intensity": 1.0, "mode": 1, "nits": 1000},
            "uniform_scale": None if kind == "audio" else {"on": True, "value": scale},
            "template_id": "",
            "template_scene": "default",
            "responsive_layout": {"enable": False, "horizontal_pos_layout": 0, "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0},
        }

    # 1. Populate Video Tracks
    for shot in spec["shots"]:
        sid = shot["id"]
        t0 = shot["timeline_start"]
        dur = shot["duration"]
        layout = shot["layout"]

        if layout in ("cinema_frame", "full_bleed"):
            ckey = f"{sid}_main"
            cinfo = manifest["clips"][ckey]
            mid = register_media(cinfo["path"], "video", cinfo["width"], cinfo["height"], cinfo["duration"], ckey)
            # In 9:16 Jianying canvas, landscape clip default fit-width=1.0 creates centered 16:9 cinema frame!
            scale = 1.85 if (layout == "full_bleed" and cinfo["width"] > cinfo["height"]) else 1.0
            ensure_track("video", "video_main").segments if False else None
            ensure_track("video", "video_main")["segments"].append(
                make_segment(ckey, mid, "video", t0, dur, tx=0.0, ty=0.04 if layout == "cinema_frame" else 0.0, scale=scale)
            )
        elif layout == "split_2":
            for t_name, slot, ty in [("video_main", "top", 0.28), ("video_overlay_1", "bottom", -0.28)]:
                ckey = f"{sid}_{slot}"
                cinfo = manifest["clips"][ckey]
                mid = register_media(cinfo["path"], "video", cinfo["width"], cinfo["height"], cinfo["duration"], ckey)
                ensure_track("video", t_name)["segments"].append(
                    make_segment(ckey, mid, "video", t0, dur, tx=0.0, ty=ty, scale=0.96)
                )
        elif layout == "triptych":
            for t_name, slot, ty in [
                ("video_overlay_1", "top", 0.42),
                ("video_main", "middle", 0.0),
                ("video_overlay_2", "bottom", -0.42),
            ]:
                ckey = f"{sid}_{slot}"
                cinfo = manifest["clips"][ckey]
                mid = register_media(cinfo["path"], "video", cinfo["width"], cinfo["height"], cinfo["duration"], ckey)
                ensure_track("video", t_name)["segments"].append(
                    make_segment(ckey, mid, "video", t0, dur, tx=0.0, ty=ty, scale=0.94)
                )

    # 2. Populate Independent Audio Tracks (BGM + Natural Sound Clips)
    if manifest.get("bgm_stem"):
        bgm_mid = register_media(manifest["bgm_stem"], "audio", 0, 0, total_dur, "BGM_LoFi_Warm")
        ensure_track("audio", "audio_bgm")["segments"].append(
            make_segment("bgm_main", bgm_mid, "audio", 0.0, total_dur, vol=0.85)
        )

    for ev in manifest.get("nat_audio_events", []):
        nat_mid = register_media(ev["path"], "audio", 0, 0, ev["duration"], ev["id"])
        ensure_track("audio", "audio_nat_sound")["segments"].append(
            make_segment(ev["id"], nat_mid, "audio", ev["timeline_start"], ev["duration"], vol=1.0)
        )

    # 3. Populate Editable Native Text Tracks
    def add_text_clip(track_name: str, tid: str, text: str, start_s: float, dur_s: float, ty: float, px_size: float, hex_color: str) -> None:
        mat_id = ident(f"text_mat:{tid}")
        rgb = [int(hex_color[i : i + 2], 16) / 255.0 for i in (1, 3, 5)]
        style = {
            "range": [0, len(text.encode("utf-16-le")) // 2],
            "size": round(px_size / 6.0, 2),
            "bold": True,
            "italic": False,
            "underline": False,
            "strokes": [{"content": {"solid": {"alpha": 0.75, "color": [0.0, 0.0, 0.0]}}, "width": 0.06}],
            "fill": {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": rgb}}},
        }
        materials["texts"].append({
            "id": mat_id, "type": "text", "check_flag": 7,
            "content": json.dumps({"text": text, "styles": [style]}, ensure_ascii=False),
            "alignment": 1, "typesetting": 0, "global_alpha": 1.0,
            "letter_spacing": 0.02, "line_spacing": 0.04,
            "line_feed": 1, "line_max_width": 0.86, "force_apply_line_max_width": False,
        })
        ensure_track("text", track_name)["segments"].append(
            make_segment(tid, mat_id, "text", start_s, dur_s, tx=0.0, ty=ty)
        )

    header_tag = spec.get("theme", {}).get("header_tag")
    if header_tag:
        add_text_clip("text_header", "header_01", header_tag, 0.0, total_dur, ty=0.80, px_size=36, hex_color="#F3C98B")

    for idx, cap in enumerate(spec.get("captions", []), start=1):
        cs = float(cap["start"])
        cdur = round(float(cap["end"]) - cs, 3)
        add_text_clip("text_caption_main", f"cap_main_{idx}", cap["text"], cs, cdur, ty=-0.62, px_size=50, hex_color="#FFFFFF")
        if cap.get("subtext"):
            add_text_clip("text_caption_sub", f"cap_sub_{idx}", cap["subtext"], cs, cdur, ty=-0.71, px_size=34, hex_color="#F3C98B")

    # Sort tracks and assign render indices
    ordered_tracks = sorted(tracks.values(), key=lambda tr: {"video": 0, "audio": 1, "text": 2}[tr["type"]])
    v_idx = 0
    for tr in ordered_tracks:
        tr["segments"].sort(key=lambda s: s["target_timerange"]["start"])
        for seg in tr["segments"]:
            layer = 14000 + v_idx if tr["type"] == "text" else v_idx
            seg["render_index"] = 0 if tr["type"] == "audio" else layer
            seg["track_render_index"] = seg["render_index"]
        if tr["type"] != "audio":
            if tr["type"] == "video" and v_idx > 0:
                tr["flag"] = 2
            v_idx += 1

    now_us = int(datetime.now(timezone.utc).timestamp() * 1_000_000)
    total_us = _us(total_dur)
    total_bytes = sum(f.stat().st_size for f in res_dir.iterdir() if f.is_file())

    draft_info = {
        "id": project_id, "name": project_name, "version": 360000,
        "new_version": "112.0.0", "source": "default", "duration": total_us,
        "fps": float(spec.get("fps", 30)), "color_space": 0,
        "create_time": 0, "update_time": 0,
        "canvas_config": {"width": int(spec.get("width", 1080)), "height": int(spec.get("height", 1920)), "ratio": "9:16", "background": None},
        "materials": materials, "tracks": ordered_tracks,
        "platform": _platform(), "last_modified_platform": _platform(),
        "keyframes": {k: [] for k in ("adjusts", "audios", "effects", "filters", "handwrites", "stickers", "texts", "videos")},
        "keyframe_graph_list": [], "relationships": [],
        "render_index_track_mode_on": False, "free_render_index_mode_on": False,
        "static_cover_image_path": "", "cover": None, "retouch_cover": None,
        "extra_info": None, "group_container": None, "mutable_config": None, "time_marks": None,
        "config": {
            "maintrack_adsorb": False, "material_save_mode": 0, "video_mute": False,
            "adjust_max_index": 1, "combination_max_index": 1, "sticker_max_index": 1,
            "extract_audio_last_index": 1, "record_audio_last_index": 1, "original_sound_last_index": 1,
            "attachment_info": [], "export_range": None, "lyrics_recognition_id": "", "lyrics_sync": True,
            "lyrics_taskinfo": [], "subtitle_recognition_id": "", "subtitle_sync": True,
            "subtitle_taskinfo": [], "subtitle_keywords_config": None, "system_font_list": [], "zoom_info_params": None,
        },
    }

    draft_meta = {
        "draft_id": project_id, "draft_name": project_name,
        "draft_fold_path": str(final_project_dir), "draft_root_path": str(target_draft_root),
        "draft_cover": "", "draft_type": "", "draft_new_version": "",
        "draft_is_invisible": False, "draft_is_from_deeplink": "false",
        "draft_is_ai_packaging_used": False, "draft_is_ai_shorts": False, "draft_is_article_video_draft": False,
        "draft_materials": [{"type": g, "value": registry if g == 0 else []} for g in range(8)],
        "draft_materials_copied_info": [], "draft_segment_extra_info": [],
        "draft_timeline_materials_size_": total_bytes, "draft_removable_storage_device": "",
        "draft_cloud_materials": [], "draft_cloud_last_action_download": False,
        "draft_deeplink_url": "", "draft_cloud_purchase_info": "",
        "draft_cloud_capcut_purchase_info": "", "draft_cloud_videocut_purchase_info": "",
        "draft_cloud_template_id": "", "draft_cloud_tutorial_info": "",
        "cloud_package_completed_time": "", "tm_draft_cloud_completed": "",
        "tm_draft_cloud_modified": 0, "tm_draft_create": now_us,
        "tm_draft_modified": now_us, "tm_draft_removed": 0, "tm_duration": total_us,
        "draft_enterprise_info": {"draft_enterprise_extra": "", "draft_enterprise_id": "", "draft_enterprise_name": "", "enterprise_material": []},
    }

    (bundle_dir / "draft_info.json").write_text(json.dumps(draft_info, ensure_ascii=False, indent=2), encoding="utf-8")
    (bundle_dir / "draft_meta_info.json").write_text(json.dumps(draft_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write safe one-click installer script
    installer_path = export_dir / "install_to_jianying.py"
    installer_code = f'''#!/usr/bin/env python3
"""Safely register `{project_name}` into local Mac Jianying Pro drafts (with automatic index backup)."""
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent / "native_draft" / "{project_name}"
DRAFT_ROOT = Path("{str(target_draft_root)}")
TARGET = DRAFT_ROOT / "{project_name}"
INDEX = DRAFT_ROOT / "root_meta_info.json"

def ensure_closed():
    out = subprocess.run(["/bin/ps", "-axo", "comm="], check=True, capture_output=True, text=True).stdout
    names = {{"jianyingpro", "jianying", "videofusion-macos", "剪映专业版", "剪映"}}
    if any(Path(line.strip()).name.casefold() in names for line in out.splitlines() if line.strip()):
        raise SystemExit("⚠️ 请先完全退出「剪映专业版」(Cmd+Q)，再运行此安装脚本，以免剪映覆盖草稿索引。")

def main():
    ensure_closed()
    if not INDEX.exists():
        raise SystemExit(f"未找到剪映草稿索引: {{INDEX}}")
    raw = INDEX.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    backup_dir = DRAFT_ROOT / ".cutcut_backups"
    backup_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(INDEX, backup_dir / f"root_meta_info.{{ts}}.bak.json")

    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(BUNDLE, TARGET)

    meta = json.loads((TARGET / "draft_meta_info.json").read_text(encoding="utf-8"))
    draft_id = meta["draft_id"]
    data["all_draft_store"] = [e for e in data.get("all_draft_store", []) if e.get("draft_name") != "{project_name}" and e.get("draft_id") != draft_id]
    data["all_draft_store"].insert(0, {{
        "draft_id": draft_id,
        "draft_name": "{project_name}",
        "draft_fold_path": str(TARGET),
        "draft_root_path": str(DRAFT_ROOT),
        "draft_json_file": str(TARGET / "draft_info.json"),
        "draft_cover": str(TARGET / "draft_cover.jpg") if (TARGET / "draft_cover.jpg").exists() else "",
        "draft_is_invisible": False,
        "draft_type": "",
        "draft_new_version": "",
        "streaming_edit_draft_ready": True,
        "draft_timeline_materials_size": meta["draft_timeline_materials_size_"],
        "tm_duration": meta["tm_duration"],
        "tm_draft_create": meta["tm_draft_create"],
        "tm_draft_modified": meta["tm_draft_modified"],
        "tm_draft_removed": 0,
    }})
    if isinstance(data.get("draft_ids"), list) and draft_id not in data["draft_ids"]:
        data["draft_ids"].append(draft_id)
    INDEX.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已成功导入剪映草稿箱：{{TARGET.name}}！现在打开剪映专业版即可在首页看到并二次编辑。")

if __name__ == "__main__":
    main()
'''
    installer_path.write_text(installer_code, encoding="utf-8")
    os.chmod(installer_path, 0o755)

    return {
        "project_name": project_name,
        "bundle_dir": str(bundle_dir),
        "installer_script": str(installer_path),
        "track_count": len(ordered_tracks),
        "bundled_media_files": len(copied_files),
        "bundled_bytes": total_bytes,
    }


def export_jianying_all(spec: dict, manifest: dict, build_dir: Path) -> dict:
    export_dir = build_dir / "jianying_export"
    export_dir.mkdir(parents=True, exist_ok=True)
    srt_path = write_srt(spec, export_dir / "captions.srt")
    fcpxml_path = write_fcpxml(spec, manifest, export_dir / "timeline.fcpxml")
    native_res = build_jianying_native_bundle(spec, manifest, export_dir)

    summary = {
        "srt": str(srt_path),
        "fcpxml": str(fcpxml_path),
        "native_draft": native_res,
    }
    (export_dir / "export_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[jianying] Exported SRT, FCPXML, and Native Draft Bundle -> {export_dir}", flush=True)
    return summary
