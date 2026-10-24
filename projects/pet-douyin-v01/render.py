"""Render the reviewed local pet rough cut without controlling any desktop app."""

from pathlib import Path
import json
import math
import subprocess
import wave

import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[1] / "桌搭"
ASSETS = ROOT / "assets"
CLIPS = ROOT / "clips"
OUTPUT = ROOT / "陪班搭子-抖音粗剪-v01.mp4"
FPS = 25
W, H = 1080, 1920

SCENES = [
    {"file": "C0409.MP4", "start": 164.2, "duration": 2.8, "cx": .40, "height": 2160, "y": 0, "note": "正脸反应开场"},
    {"file": "C0410.MP4", "start": .5, "duration": 3.2, "cx": .83, "height": 2160, "y": 0, "note": "工位与陪班搭子，右侧保留脸和键盘"},
    {"file": "C0408.MP4", "start": 123.6, "duration": 3.2, "cx": .43, "height": 2160, "y": 0, "note": "被抱到桌面趴下，动作连接"},
    {"file": "C0408.MP4", "start": 126.0, "duration": 4.4, "cx": .42, "height": 1728, "y": 432, "note": "趴着被摸，保留反应"},
    {"file": "C0410.MP4", "start": 90.0, "duration": 3.2, "cx": .53, "height": 2160, "y": 0, "note": "挠下巴互动"},
    {"file": "C0410.MP4", "start": 193.3, "duration": 3.6, "cx": .48, "height": 2160, "y": 0, "note": "小爪子和手部互动"},
    {"file": "C0410.MP4", "start": 58.0, "duration": 4.0, "cx": .51, "height": 2160, "y": 0, "note": "回到正脸反应，避开走近镜头后的截头画面"},
    {"file": "C0408.MP4", "start": 145.0, "duration": 3.6, "cx": .42, "height": 1728, "y": 432, "note": "放松趴着收尾"},
]

CAPTIONS = [
    (.20, 3.40, "说好陪我上班的", 1500),
    (5.40, 9.60, "工位是占上了", 220),
    (10.20, 17.00, "工作内容：等摸摸", 220),
    (24.40, 27.90, "这班，属它最舒服", 220),
]


def run(args, logfile):
    with logfile.open("w") as log:
        subprocess.run(args, check=True, stdout=log, stderr=subprocess.STDOUT)


def create_music(duration):
    """Original soft plucked instrumental; no downloaded music or stock sample."""
    sr = 48000
    signal = np.zeros((math.ceil((duration + 2) * sr), 2), dtype=np.float64)
    beat = 60 / 96
    rng = np.random.default_rng(22)

    def note(midi, start, length, gain, pan=0, bass=False):
        freq = 440 * 2 ** ((midi - 69) / 12)
        tt = np.arange(int(length * sr)) / sr
        attack = np.minimum(tt / .008, 1)
        decay = np.exp(-tt * (3.1 if bass else 4.8))
        tone = np.sin(2 * np.pi * freq * tt) + .23 * np.sin(2 * np.pi * 2 * freq * tt) * np.exp(-tt * 5)
        tone += .06 * np.sin(2 * np.pi * 3 * freq * tt) * np.exp(-tt * 10)
        tone *= attack * decay * gain
        tail = np.minimum((length - tt) / .05, 1).clip(0, 1)
        tone *= tail
        at = round(start * sr)
        end = min(len(signal), at + len(tone))
        if end <= at:
            return
        signal[at:end, 0] += tone[:end-at] * math.sqrt((1-pan)/2)
        signal[at:end, 1] += tone[:end-at] * math.sqrt((1+pan)/2)

    chords = [(48, 60, 64, 67, 71), (45, 57, 60, 64, 67), (41, 53, 57, 60, 64), (43, 55, 59, 62, 64)]
    melody = [
        [76, None, 79, 76, 74, None, 72, None],
        [72, 76, None, 79, 76, None, 74, None],
        [72, None, 69, 72, 76, None, 74, None],
        [71, None, 74, 76, 74, None, 72, None],
    ]
    for bar in range(math.ceil(duration / (4 * beat))):
        base = bar * 4 * beat
        chord = chords[bar % 4]
        note(chord[0], base, 1.5, .045, bass=True)
        note(chord[0] + 12, base + 2 * beat, 1, .024, bass=True)
        for j in range(8):
            note(chord[1+j % 4], base + j * beat / 2, .85, .018, pan=-.25)
            m = melody[bar % 4][j]
            if m is not None:
                note(m, base + j * beat / 2, .8, .045, pan=.20)
        # Quiet brushed texture, not a sharp synthetic snare.
        for j in [1, 3]:
            at = round((base + j * beat) * sr)
            n = int(.055 * sr)
            if at + n < len(signal):
                noise = rng.normal(0, 1, n) * np.exp(-np.arange(n)/sr*90) * .002
                signal[at:at+n] += noise[:, None]
    dry = signal.copy()
    for seconds, gain in [(.105, .12), (.213, .07), (.337, .035)]:
        lag = round(seconds * sr)
        signal[lag:] += dry[:-lag, ::-1] * gain
    signal = signal[:round(duration * sr)]
    signal[:int(.04*sr)] *= np.linspace(0, 1, int(.04*sr))[:, None]
    signal[-int(.7*sr):] *= np.linspace(1, 0, int(.7*sr))[:, None]
    signal *= .65 / max(np.abs(signal).max(), .001)
    path = ASSETS / "original-soft-plucks.wav"
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes((signal * 32767).astype("<i2").tobytes())
    return path


def main():
    for p in [ASSETS, CLIPS]:
        p.mkdir(parents=True, exist_ok=True)
    clock = 0
    for i, s in enumerate(SCENES):
        s["timeline_start"] = round(clock, 3)
        clock += s["duration"]
        s["timeline_end"] = round(clock, 3)
        ch = s["height"]
        cw = int(ch * 9 / 16) // 2 * 2
        x = round((s["cx"] * 3840 - cw/2) / 2) * 2
        s["crop"] = {"x": x, "y": s["y"], "width": cw, "height": ch}
        destination = CLIPS / f"{i+1:02d}.mp4"
        gamma = 1.08 if s["file"] == "C0409.MP4" else 1.035
        vf = f"setpts=PTS-STARTPTS,crop={cw}:{ch}:{x}:{s['y']},scale={W}:{H}:flags=lanczos,setsar=1,fps={FPS},eq=contrast=1.02:gamma={gamma}:saturation=1.025,format=yuv420p"
        run(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-nostdin", "-y", "-threads", "2",
             "-ss", str(s["start"]), "-i", str(SOURCE / s["file"]), "-t", str(s["duration"]),
             "-an", "-vf", vf, "-filter_threads", "1", "-c:v", "h264_videotoolbox", "-b:v", "12M",
             "-profile:v", "high", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-video_track_timescale", "25000", str(destination)],
            ROOT / f"render-shot-{i+1:02d}.log")
        print(f"shot {i+1}/{len(SCENES)} rendered", flush=True)
    clock = round(clock, 3)
    (ROOT / "timeline.json").write_text(json.dumps({"fps": FPS, "width": W, "height": H, "duration": clock, "scenes": SCENES, "captions": CAPTIONS, "audio": "Original procedural instrumental; source speech is not transcribed or used."}, ensure_ascii=False, indent=2))
    listing = ROOT / "concat.txt"
    listing.write_text("".join(f"file '{(CLIPS / f'{i+1:02d}.mp4').as_posix()}'\n" for i in range(len(SCENES))))
    music = create_music(clock)
    font = "/System/Library/Fonts/STHeiti Medium.ttc"
    filters = []
    for i, (start, end, text, position_y) in enumerate(CAPTIONS):
        path = ASSETS / f"caption-{i+1}.txt"
        path.write_text(text)
        alpha = f"if(lt(t,{start+.12}),(t-{start})/.12,if(gt(t,{end-.12}),({end}-t)/.12,1))"
        filters.append(f"drawtext=fontfile='{font}':textfile='{path}':fontsize=62:fontcolor=white:borderw=4:bordercolor=black@0.65:shadowcolor=black@0.35:shadowx=0:shadowy=3:x=(w-text_w)/2:y={position_y}:alpha='{alpha}':enable='between(t,{start},{end})'")
    run(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-nostdin", "-y", "-threads", "2",
         "-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(music),
         "-map", "0:v:0", "-map", "1:a:0", "-vf", ",".join(filters), "-filter_threads", "1",
         "-af", "loudnorm=I=-18:TP=-1.5:LRA=7,afade=t=out:st=27.3:d=0.7", "-ar", "48000",
         "-c:v", "h264_videotoolbox", "-b:v", "9M", "-profile:v", "high", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-c:a", "aac", "-b:a", "192k", "-t", str(clock), "-movflags", "+faststart", str(OUTPUT)], ROOT / "render-final.log")
    print(OUTPUT, flush=True)


if __name__ == "__main__":
    main()
