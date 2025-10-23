# -*- coding: utf-8 -*-
"""
GIF Maker · save to project assets + thumbnail
- Uses ffmpeg when available; falls back to MoviePy 2.x
- Always saves to <PROJECT_ROOT>/assets/static/media/{gif,thumb} unless overridden
Run: streamlit run gif_maker.py
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path
import streamlit as st

# ----------------- Page -----------------
st.set_page_config(page_title="GIF Maker (Assets + Thumbnail)", page_icon="🎞️", layout="centered")
st.title("🎞️ GIF Maker · Assets Saver + 📸 Thumbnail")

# ----------------- Env / Paths -----------------
DEFAULT_GIF  = "assets/static/media/gif"
DEFAULT_THB  = "assets/static/media/thumb"

ENV_GIF  = os.getenv("WL_GIF_DIR", DEFAULT_GIF)
ENV_THB  = os.getenv("WL_THUMB_DIR", DEFAULT_THB)
ENV_ROOT = os.getenv("WL_PROJECT_ROOT")

if ENV_ROOT:
    PROJECT_ROOT = Path(ENV_ROOT).expanduser().resolve()
else:
    # assuming this file sits in WordloomFrontend/streamlit/
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

GIF_OUT_DIR   = (PROJECT_ROOT / ENV_GIF).resolve()
THUMB_OUT_DIR = (PROJECT_ROOT / ENV_THB).resolve()
GIF_OUT_DIR.mkdir(parents=True, exist_ok=True)
THUMB_OUT_DIR.mkdir(parents=True, exist_ok=True)

def proj_path(*parts) -> Path:
    return PROJECT_ROOT.joinpath(*parts)

# ----------------- UI: upload & options -----------------
uploaded = st.file_uploader("Upload video / 上传视频", type=["mp4", "mov", "webm", "mkv"])
width = st.selectbox("GIF Width 宽度", [480, 640, 720], index=1)
fps = st.slider("FPS 帧率", 6, 24, 8, 1)
duration = st.slider("Duration 时长（秒）", 5, 12, 8, 1)
start_time = st.text_input("Start 起始时间 (ss 或 hh:mm:ss)", "0")
loop = st.checkbox("Loop 无限循环", True)

# ----------------- Naming helpers -----------------
def slugify(name: str) -> str:
    base = re.sub(r"[^\w\-]+", "_", name.strip())
    base = re.sub(r"_+", "_", base).strip("_")
    return base or "video"

stem_from_upload = "demo"
if uploaded is not None:
    try:
        stem_from_upload = Path(uploaded.name).stem
    except Exception:
        pass
auto_stem = slugify(stem_from_upload)

append_spec = st.checkbox("文件名追加规格后缀（_640w_8fps_8s）/ Append spec suffix", True)
spec_suffix = f"_{width}w_{fps}fps_{duration}s" if append_spec else ""

out_gif_default   = f"{auto_stem}{spec_suffix}.gif"
out_thumb_default = f"{auto_stem}_thumb.jpg"

out_name   = st.text_input("Output GIF 文件名（.gif）", out_gif_default)
thumb_name = st.text_input("缩略图文件名（.jpg）", out_thumb_default)

# ----------------- Thumbnail options -----------------
st.markdown("---")
st.subheader("📸 缩略图 / Thumbnail")
gen_thumb   = st.checkbox("生成缩略图 Generate thumbnail", True)
thumb_width = st.selectbox("缩略图宽度 Thumbnail width", [200, 240, 320, 360, 480], index=1)
thumb_method = st.radio("缩略图算法 / Method",
                        ["smart-thumbnail（自动挑清晰帧）", "first-frame（第一帧）", "at-time（在指定秒）"],
                        index=0, horizontal=True)
thumb_time = st.number_input("at-time：取帧秒数（仅在上面选择 at-time 生效）", min_value=0.0, max_value=600.0, value=2.0, step=0.5)
thumb_overlay = st.checkbox("在缩略图中央叠加 ▶ 播放图标（Pillow 实现）", False)

# ----------------- Save-to-project -----------------
st.markdown("---")
st.subheader("📦 保存到项目 / Save to project assets")

save_to_project = st.checkbox("保存到仓库 assets 结构（建议开启）/ Save to repo assets", True)
project_root_ui = st.text_input("项目根目录 Project root（用于拼装 assets 路径）",
                                value=str(PROJECT_ROOT),
                                help="示例：D:\\Project\\Wordloom 或 /home/user/Wordloom")
gif_dir_rel_ui  = st.text_input("GIF 相对目录（相对于项目根）", ENV_GIF)
img_dir_rel_ui  = st.text_input("缩略图相对目录（相对于项目根）", ENV_THB)

def normalize_start(s: str) -> str:
    s = str(s).strip()
    if s.isdigit():
        return s
    parts = s.split(":")
    if len(parts) == 2:
        return f"00:{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    if len(parts) == 3:
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
    return "0"

# ----------------- FFmpeg helpers -----------------
CHOCO_BIN = r"C:\ProgramData\chocolatey\bin"

def has_ffmpeg() -> bool:
    try:
        r = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return r.returncode == 0
    except Exception:
        return False

def ensure_ffmpeg_in_path():
    if not has_ffmpeg() and Path(CHOCO_BIN).exists():
        os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + CHOCO_BIN

def ffmpeg_version_str() -> str:
    try:
        r = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if r.stdout:
            return r.stdout.splitlines()[0]
    except Exception:
        pass
    return "ffmpeg not found / 未检测到 ffmpeg"

def convert_ffmpeg(src: Path, dst: Path, start: str, dur: int, width: int, fps: int, loop_flag: bool):
    pal = src.with_suffix(".palette.png")
    vf1 = f"fps={fps},scale={width}:-1:flags=lanczos,palettegen"
    cmd1 = ["ffmpeg", "-y", "-ss", start, "-t", str(dur), "-i", str(src), "-vf", vf1, str(pal)]
    st.code(" ".join(cmd1), language="bash")
    r1 = subprocess.run(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r1.returncode != 0:
        raise RuntimeError("ffmpeg palettegen failed · 生成调色板失败")

    lavfi = f"fps={fps},scale={width}:-1:flags=lanczos [x]; [x][1:v] paletteuse"
    cmd2 = ["ffmpeg", "-y", "-ss", start, "-t", str(dur), "-i", str(src), "-i", str(pal), "-lavfi", lavfi, str(dst)]
    st.code(" ".join(cmd2), language="bash")
    r2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r2.returncode != 0:
        raise RuntimeError("ffmpeg paletteuse failed · 调色板合成失败")

def convert_moviepy(src: Path, dst: Path, start: str, dur: int, width: int, fps: int, loop_flag: bool):
    from moviepy import VideoFileClip  # MoviePy 2.x
    # parse start seconds
    ss = 0
    if ":" in start:
        parts = [int(x) for x in start.split(":")]
        if len(parts) == 3:
            ss = parts[0]*3600 + parts[1]*60 + parts[2]
        elif len(parts) == 2:
            ss = parts[0]*60 + parts[1]
    else:
        try:
            ss = int(start)
        except Exception:
            ss = 0
    clip = VideoFileClip(str(src))
    sub = clip.subclip(ss, min(clip.duration, ss + dur)).resize(width=width)
    try:
        sub.write_gif(str(dst), fps=fps, loop=0 if loop_flag else 1)
    finally:
        clip.close()
        sub.close()

# ----------------- Thumbnail -----------------
def gen_thumbnail_ffmpeg(gif_path: Path, jpg_path: Path, width: int, method_ui: str, t: float):
    if "smart" in method_ui:
        vf = f"thumbnail,scale={width}:-1:flags=lanczos"
        cmd = ["ffmpeg", "-y", "-i", str(gif_path), "-vf", vf, "-frames:v", "1", str(jpg_path)]
    elif "first" in method_ui:
        vf = f"select=eq(n\\,0),scale={width}:-1:flags=lanczos"
        cmd = ["ffmpeg", "-y", "-i", str(gif_path), "-vf", vf, "-frames:v", "1", str(jpg_path)]
    else:
        vf = f"scale={width}:-1:flags=lanczos"
        cmd = ["ffmpeg", "-y", "-ss", str(max(0.0, t)), "-i", str(gif_path), "-vframes", "1", "-vf", vf, str(jpg_path)]
    st.code(" ".join(cmd), language="bash")
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg thumbnail 生成失败")

def gen_thumbnail_pillow(gif_path: Path, jpg_path: Path, width: int, overlay: bool):
    from PIL import Image, ImageDraw
    im = Image.open(str(gif_path))
    try:
        im.seek(0)
    except Exception:
        pass
    im = im.convert("RGB")
    w, h = im.size
    nh = int(h * (width / float(w)))
    im = im.resize((width, nh))
    if overlay:
        draw = ImageDraw.Draw(im)
        cx, cy = width // 2, nh // 2
        r = max(20, width // 10)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(0, 0, 0, 90))
        tri = [(cx - r//3, cy - r//2), (cx - r//3, cy + r//2), (cx + r//2, cy)]
        draw.polygon(tri, fill=(255, 255, 255))
    im.save(str(jpg_path), quality=92)

# ----------------- Header info -----------------
def open_folder(path: Path):
    try:
        os.startfile(str(path))
    except Exception:
        pass

ensure_ffmpeg_in_path()
st.caption("🔍 " + ffmpeg_version_str())
st.caption("💡 若未检测到 ffmpeg，已尝试临时加入 Chocolatey 路径。")
st.caption(f"📁 PROJECT_ROOT = {PROJECT_ROOT}")
st.caption(f"📂 GIF_DIR = {GIF_OUT_DIR}")
st.caption(f"📂 THUMB_DIR = {THUMB_OUT_DIR}")

# ----------------- Action -----------------
if st.button("Convert / 开始转换", type="primary", disabled=not uploaded):
    if not uploaded:
        st.warning("请先上传一个视频 / Please upload a video.")
    else:
        with tempfile.TemporaryDirectory() as td:
            # write upload to temp
            src = Path(td) / uploaded.name
            src.write_bytes(uploaded.getvalue())

            # determine output targets & start
            tmp_gif = Path(td) / (out_name if out_name.lower().endswith('.gif') else out_name + '.gif')
            start = normalize_start(start_time)

            # do conversion
            try:
                if has_ffmpeg():
                    with st.spinner("Using ffmpeg (palette optimized)… 正在用 ffmpeg 调色板优化转换…"):
                        convert_ffmpeg(src, tmp_gif, start, int(duration), int(width), int(fps), bool(loop))
                else:
                    with st.spinner("未检测到 ffmpeg，使用 MoviePy 回退方案…"):
                        convert_moviepy(src, tmp_gif, start, int(duration), int(width), int(fps), bool(loop))
            except Exception as e:
                st.error(f"转换失败：{e}")
            else:
                st.success("✅ GIF 完成")
                st.image(str(tmp_gif), caption=tmp_gif.name)

                # save to project
                if save_to_project:
                    gif_out = GIF_OUT_DIR / tmp_gif.name
                    gif_out.parent.mkdir(parents=True, exist_ok=True)
                    gif_out.write_bytes(tmp_gif.read_bytes())
                    st.success(f"📁 已保存到项目：{gif_out}")
                    st.button('打开 GIF 文件夹 · Open GIF Folder', on_click=lambda: open_folder(gif_out.parent))
                else:
                    gif_out = tmp_gif

                # thumbnail
                thumb_tmp = Path(td) / (thumb_name if thumb_name.lower().endswith('.jpg') else thumb_name + '.jpg')
                if gen_thumb:
                    try:
                        if has_ffmpeg():
                            with st.spinner("ffmpeg 生成缩略图…"):
                                gen_thumbnail_ffmpeg(gif_out, thumb_tmp, int(thumb_width), thumb_method, float(thumb_time))
                        else:
                            with st.spinner("Pillow 生成缩略图…"):
                                gen_thumbnail_pillow(gif_out, thumb_tmp, int(thumb_width), bool(thumb_overlay))
                        if save_to_project:
                            thumb_out = THUMB_OUT_DIR / thumb_tmp.name
                            thumb_out.parent.mkdir(parents=True, exist_ok=True)
                            thumb_out.write_bytes(thumb_tmp.read_bytes())
                            st.success(f"📁 缩略图已保存到项目：{thumb_out}")
                            st.button('打开缩略图文件夹 · Open Thumbnail Folder', on_click=lambda: open_folder(thumb_out.parent))
                        else:
                            thumb_out = thumb_tmp
                        st.image(str(thumb_out), caption=thumb_out.name)
                    except Exception as e:
                        st.warning(f"缩略图生成失败：{e}")
