#!/usr/bin/env python3
"""Safely register `CutCut-pet-douyin-v02` into local Mac Jianying Pro drafts (with automatic index backup)."""
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent / "native_draft" / "CutCut-pet-douyin-v02"
DRAFT_ROOT = Path("/Users/luo/Movies/JianyingPro/User Data/Projects/com.lveditor.draft")
TARGET = DRAFT_ROOT / "CutCut-pet-douyin-v02"
INDEX = DRAFT_ROOT / "root_meta_info.json"

def ensure_closed():
    out = subprocess.run(["/bin/ps", "-axo", "comm="], check=True, capture_output=True, text=True).stdout
    names = {"jianyingpro", "jianying", "videofusion-macos", "剪映专业版", "剪映"}
    if any(Path(line.strip()).name.casefold() in names for line in out.splitlines() if line.strip()):
        raise SystemExit("⚠️ 请先完全退出「剪映专业版」(Cmd+Q)，再运行此安装脚本，以免剪映覆盖草稿索引。")

def main():
    ensure_closed()
    if not INDEX.exists():
        raise SystemExit(f"未找到剪映草稿索引: {INDEX}")
    raw = INDEX.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    backup_dir = DRAFT_ROOT / ".cutcut_backups"
    backup_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(INDEX, backup_dir / f"root_meta_info.{ts}.bak.json")

    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(BUNDLE, TARGET)

    meta = json.loads((TARGET / "draft_meta_info.json").read_text(encoding="utf-8"))
    draft_id = meta["draft_id"]
    data["all_draft_store"] = [e for e in data.get("all_draft_store", []) if e.get("draft_name") != "CutCut-pet-douyin-v02" and e.get("draft_id") != draft_id]
    data["all_draft_store"].insert(0, {
        "draft_id": draft_id,
        "draft_name": "CutCut-pet-douyin-v02",
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
    })
    if isinstance(data.get("draft_ids"), list) and draft_id not in data["draft_ids"]:
        data["draft_ids"].append(draft_id)
    INDEX.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已成功导入剪映草稿箱：{TARGET.name}！现在打开剪映专业版即可在首页看到并二次编辑。")

if __name__ == "__main__":
    main()
