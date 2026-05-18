"""Build the gemini-data-agent demo video end-to-end."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1920, 1080
FG = "#0f172a"
FG_MUTED = "#475569"
ACCENT = "#0d9488"   # teal-600 (MongoDB-ish)
ACCENT_2 = "#16a34a"
BG = "#ffffff"
PANEL = "#f8fafc"
CODE_BG = "#0f172a"
CODE_FG = "#e2e8f0"

SF = "/System/Library/Fonts/SFNS.ttf"
SFI = "/System/Library/Fonts/SFNSItalic.ttf"
MONO = "/System/Library/Fonts/SFNSMono.ttf"
if not Path(MONO).exists():
    MONO = "/System/Library/Fonts/Menlo.ttc"


def font(size, mono=False, italic=False):
    path = MONO if mono else (SFI if italic else SF)
    return ImageFont.truetype(path, size)


@dataclass
class Slide:
    name: str
    narration: str
    draw: callable


def base(img, d, title=None, eyebrow=None):
    d.rectangle([(0, H - 56), (W, H)], fill=PANEL)
    d.text((48, H - 44), "gemini-data-agent", font=font(22), fill=FG)
    d.text((W - 620, H - 44), "github.com/MukundaKatta/gemini-data-agent", font=font(22), fill=FG_MUTED)
    if eyebrow:
        d.text((96, 80), eyebrow.upper(), font=font(26), fill=ACCENT)
    if title:
        d.text((96, 130), title, font=font(72), fill=FG)
        d.rectangle([(96, 230), (220, 236)], fill=ACCENT)


def draw_title(img, d):
    d.rectangle([(0, 0), (W, H)], fill=BG)
    d.rectangle([(0, H - 56), (W, H)], fill=PANEL)
    d.text((48, H - 44), "github.com/MukundaKatta/gemini-data-agent", font=font(22), fill=FG_MUTED)
    d.text((W - 270, H - 44), "Apache 2.0", font=font(22), fill=FG_MUTED)
    d.text((96, 320), "gemini-data-agent", font=font(120), fill=FG)
    d.rectangle([(96, 470), (340, 480)], fill=ACCENT)
    d.text((96, 520), "Natural-language MongoDB queries", font=font(48), fill=FG_MUTED)
    d.text((96, 580), "via Gemini + the MongoDB MCP server.", font=font(48), fill=FG_MUTED)
    d.text((96, 740), "Google Cloud Rapid Agent Hackathon,", font=font(32), fill=FG)
    d.text((96, 785), "MongoDB partner track.", font=font(32), fill=FG)


def draw_problem(img, d):
    base(img, d, title="The setup", eyebrow="Why this agent")
    lines = [
        "Every product team has a MongoDB cluster",
        "and a stakeholder asking, how many users are on the pro plan,",
        "what was last month's revenue, who hasn't logged in in 30 days.",
        "Answering each one means writing a fresh aggregation pipeline.",
        "What if the stakeholder could ask directly?",
    ]
    y = 320
    for line in lines:
        d.text((96, y), line, font=font(38), fill=FG)
        y += 72


def draw_architecture(img, d):
    base(img, d, title="How it works", eyebrow="Architecture")
    box_w = 380
    boxes = [
        ("User question", "users per plan?", ACCENT),
        ("ADK LlmAgent", "Gemini 2.5 on Vertex AI", FG),
        ("MongoDB MCP", "list_databases, count, aggregate, ...", ACCENT_2),
    ]
    x = (W - 3 * box_w - 100) // 2
    for label, sub, color in boxes:
        d.rounded_rectangle([(x, 360), (x + box_w, 490)], radius=14, outline=color, width=4, fill=BG)
        d.text((x + 24, 380), label, font=font(34), fill=FG)
        d.text((x + 24, 430), sub, font=font(22), fill=FG_MUTED)
        x += box_w + 50
    a1 = ((W - 3 * box_w - 100) // 2) + box_w + 6
    a2 = a1 + box_w + 50
    d.text((a1, 410), "→", font=font(60), fill=FG_MUTED)
    d.text((a2, 410), "→", font=font(60), fill=FG_MUTED)
    d.text((96, 600), "MCP tool surface matches the official mongodb-mcp-server (npm).", font=font(30), fill=FG)
    d.text((96, 650), "Flip one flag and the agent targets a real cluster.", font=font(30), fill=FG)
    d.text((96, 780), "Six tools: list_databases, list_collections, collection_schema,", font=font(28, italic=True), fill=FG_MUTED)
    d.text((96, 820), "find, count, aggregate.", font=font(28, italic=True), fill=FG_MUTED)


def draw_question(img, d):
    base(img, d, title="The query", eyebrow="Live agent run")
    d.text((96, 320), "User asks:", font=font(36), fill=FG_MUTED)
    d.rounded_rectangle([(96, 380), (W - 96, 500)], radius=16, fill=PANEL)
    d.text((130, 410), '"How many users are on each plan? Compare them."',
           font=font(38), fill=FG)
    d.text((96, 560), "Agent walks four MongoDB tools:", font=font(32), fill=FG_MUTED)
    steps = [
        "1.  list_databases       →  acme_prod, acme_analytics",
        "2.  list_collections     →  users, orders, products, ...",
        "3.  collection_schema    →  plan: enum free | starter | pro | enterprise",
        "4.  aggregate            →  group by plan, count by sum 1",
    ]
    y = 630
    for s in steps:
        d.text((130, y), s, font=font(26, mono=True), fill=FG)
        y += 50


def draw_answer(img, d):
    base(img, d, title="The answer", eyebrow="Real Vertex AI run")
    d.text((96, 320), "Direct counts from the aggregate response:", font=font(34), fill=FG_MUTED)
    rows = [
        ("free",       "269"),
        ("starter",    "127"),
        ("pro",         "73"),
        ("enterprise",  "31"),
        ("Total",      "500"),
    ]
    y = 400
    for plan, count in rows:
        emphasis = ACCENT_2 if plan == "Total" else FG
        d.text((96, y),  plan, font=font(36, mono=True), fill=emphasis)
        d.text((500, y), count, font=font(36, mono=True), fill=emphasis)
        y += 56
    d.text((96, 780), "Numbers cited verbatim from the tool output. No hallucination.",
           font=font(28, italic=True), fill=FG_MUTED)
    d.text((96, 820), "The agent walked all four MongoDB MCP tools in 7 events.",
           font=font(28, italic=True), fill=FG_MUTED)


def draw_code(img, d):
    base(img, d, title="The implementation", eyebrow="Six lines of ADK")
    code = (
        "from google.adk.agents import LlmAgent\n"
        "from google.adk.tools.mcp_tool import McpToolset\n"
        "from gemini_data_agent.agent import _mongo_toolset\n"
        "\n"
        "agent = LlmAgent(\n"
        "    model='gemini-2.5-flash',\n"
        "    name='gemini_data_agent',\n"
        "    instruction=SYSTEM_PROMPT,\n"
        "    tools=[_mongo_toolset(stub=True)],\n"
        ")"
    )
    d.rounded_rectangle([(96, 320), (W - 96, H - 130)], radius=18, fill=CODE_BG)
    yy = 360
    for line in code.split("\n"):
        d.text((130, yy), line, font=font(30, mono=True), fill=CODE_FG)
        yy += 46


def draw_close(img, d):
    d.rectangle([(0, 0), (W, H)], fill=BG)
    d.text((96, 200), "gemini-data-agent", font=font(96), fill=FG)
    d.rectangle([(96, 320), (340, 330)], fill=ACCENT)
    d.text((96, 370), "github.com/MukundaKatta/gemini-data-agent", font=font(38, mono=True), fill=ACCENT)
    d.text((96, 450), "gemini-data-agent-1029931682737.us-central1.run.app", font=font(36, mono=True), fill=ACCENT_2)
    d.text((96, 580), "Google Cloud Agent Builder (ADK)", font=font(34), fill=FG_MUTED)
    d.text((96, 630), "+ Gemini 2.5 on Vertex AI", font=font(34), fill=FG_MUTED)
    d.text((96, 680), "+ MongoDB MCP server (stub for demos, real-cluster ready)", font=font(34), fill=FG_MUTED)
    d.text((96, 820), "Apache 2.0. Mukunda Katta, independent.", font=font(28, italic=True), fill=FG_MUTED)
    d.text((96, 865), "Submission for Google Cloud Rapid Agent Hackathon, MongoDB track.", font=font(28, italic=True), fill=FG_MUTED)


SLIDES = [
    Slide("01_title",
          "Gemini data agent. Natural language MongoDB queries via Gemini and the Mongo D B M C P server, built on Google Cloud's Agent Development Kit.",
          draw_title),
    Slide("02_problem",
          "Every product team has a Mongo D B cluster and a stakeholder asking, how many users are on the pro plan, what was last month's revenue, who hasn't logged in in thirty days. Answering each one means writing a fresh aggregation pipeline. What if the stakeholder could ask directly.",
          draw_problem),
    Slide("03_architecture",
          "Three boxes. A user question goes into an A D K L L M agent powered by Gemini two point five on Vertex A I. The agent uses M C P toolset to call the Mongo D B M C P server with six tools list databases, list collections, collection schema, find, count, aggregate. Stub for demos, real cluster one env var away.",
          draw_architecture),
    Slide("04_question",
          "Here is a real query. The user asks, how many users are on each plan, compare them. The agent walks four tools. List databases finds acme prod. List collections finds users. Collection schema reveals the plan enum. Aggregate runs the group by.",
          draw_question),
    Slide("05_answer",
          "The answer comes back direct. Two sixty nine free, one twenty seven starter, seventy three pro, thirty one enterprise. Total five hundred. These are verbatim counts from the Mongo M C P aggregate response. No hallucination. The agent ran all four tool calls in seven events.",
          draw_answer),
    Slide("06_code",
          "The agent fits in six lines of Google's A D K. One L L M agent, one M C P toolset bound to the stub or real Mongo server, a Gemini model, and a system prompt that defines the discover-then-query workflow.",
          draw_code),
    Slide("07_close",
          "Gemini data agent. Apache two point zero. Submission for the Google Cloud Rapid Agent Hackathon, Mongo D B partner track. Thank you.",
          draw_close),
]


def render_slides(outdir):
    paths = []
    for sl in SLIDES:
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        sl.draw(img, d)
        p = outdir / f"{sl.name}.png"
        img.save(p, "PNG", optimize=True)
        paths.append(p)
        print(f"  rendered {p.name}")
    return paths


def render_audio(outdir):
    paths = []
    for sl in SLIDES:
        wav = outdir / f"{sl.name}.aiff"
        m4a = outdir / f"{sl.name}.m4a"
        subprocess.run(["say", "-v", "Samantha", "-r", "175", "-o", str(wav), sl.narration], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                        "-c:a", "aac", "-b:a", "128k", str(m4a)], check=True)
        wav.unlink(missing_ok=True)
        paths.append(m4a)
        print(f"  spoke   {m4a.name}")
    return paths


def render_segments(outdir, slide_pngs, audio_m4as):
    segs = []
    for sl, png, m4a in zip(SLIDES, slide_pngs, audio_m4as):
        out = outdir / f"seg_{sl.name}.mp4"
        dur = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(m4a)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        seg_dur = float(dur) + 0.4
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-loop", "1", "-i", str(png),
            "-i", str(m4a),
            "-af", "apad=pad_dur=0.4",
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-r", "30", "-t", f"{seg_dur:.2f}",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest", str(out),
        ], check=True)
        segs.append(out)
        print(f"  segment {out.name}  ({seg_dur:.2f}s)")
    return segs


def concat(outdir, segs):
    list_file = outdir / "concat.txt"
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in segs) + "\n")
    out = outdir / "demo.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy", str(out),
    ], check=True)
    return out


def main():
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "gemini-data-agent" / ".video-build"
    outdir.mkdir(parents=True, exist_ok=True)
    for needed in ("ffmpeg", "ffprobe", "say"):
        if shutil.which(needed) is None:
            sys.exit(f"missing tool: {needed}")
    print("[1/4] slides...")
    slides = render_slides(outdir)
    print("[2/4] audio...")
    audios = render_audio(outdir)
    print("[3/4] segments...")
    segs = render_segments(outdir, slides, audios)
    print("[4/4] concat...")
    final = concat(outdir, segs)
    size = final.stat().st_size / (1024 * 1024)
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(final)],
        capture_output=True, text=True,
    ).stdout.strip()
    print(f"\nDONE: {final}  ({size:.1f} MB, {float(dur):.1f}s)")


if __name__ == "__main__":
    main()
