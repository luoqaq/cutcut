from pathlib import Path
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[1] / "桌搭"
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(parents=True, exist_ok=True)
FONT = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 17)


def run(args):
    return subprocess.run(args, check=True, capture_output=True)


def frame(source, second, output, width=480):
    if not output.exists():
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
             "-threads", "2", "-ss", str(second), "-i", str(source),
             "-frames:v", "1", "-an", "-vf", f"scale={width}:-2",
             "-threads", "1", str(output)])
    return output


def sheet(source, times, name):
    thumbs = []
    for second in times:
        output = ANALYSIS / f"{source.stem}-{second:07.2f}.jpg"
        frame(source, second, output)
        thumbs.append((second, output))
    tw, th, label = 400, 225, 31
    columns = 4
    rows = (len(thumbs) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * tw, rows * (th + label)), "#151515")
    draw = ImageDraw.Draw(canvas)
    for idx, (second, file) in enumerate(thumbs):
        x, y = (idx % columns) * tw, (idx // columns) * (th + label)
        im = Image.open(file).convert("RGB")
        im.thumbnail((tw, th))
        canvas.paste(im, (x + (tw - im.width) // 2, y))
        stamp = f"{source.stem} {int(second)//60:02}:{second%60:05.2f}"
        draw.text((x + 8, y + th + 5), stamp, font=FONT, fill="white")
    destination = ANALYSIS / name
    canvas.save(destination, quality=90)
    return destination


if __name__ == "__main__":
    inventory = []
    for filename in ["C0408.MP4", "C0409.MP4", "C0410.MP4"]:
        source = SOURCE / filename
        metadata = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(source)]).stdout)
        duration = float(metadata["format"]["duration"])
        times = [float(t) for t in range(0, int(duration), 15)]
        contact = sheet(source, times, f"{source.stem}-overview.jpg")
        inventory.append({"source": str(source), "metadata": metadata, "samples": times, "contact_sheet": str(contact)})
        print(json.dumps({"source": filename, "contact_sheet": str(contact), "sample_count": len(times)}, ensure_ascii=False), flush=True)
    (ANALYSIS / "inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2))
