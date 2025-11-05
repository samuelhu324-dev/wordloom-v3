from __future__ import annotations
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi import HTTPException

from app.database_orbit import ORBIT_UPLOAD_DIR, ensure_orbit_dirs, ensure_orbit_extensions, ensure_orbit_tables
from app.routers.orbit import notes as orbit_notes
from app.routers.orbit import uploads as orbit_uploads
from app.routers.orbit import tags as orbit_tags
from app.routers.orbit import diagrams as orbit_diagrams
from app.routers.orbit import bookshelves as orbit_bookshelves
from app.routers.orbit import checkpoints as orbit_checkpoints
from app.routers.orbit import media as orbit_media

app = FastAPI(title="Wordloom Orbit API")
api = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_orbit_dirs()
ensure_orbit_extensions()
ensure_orbit_tables()  # 新增

# 新架构：添加图片重定向路由
# 前端请求：/uploads/{note_id}/{filename}
# 实际位置：{ORBIT_UPLOAD_DIR}/notes/{note_id}/images/{filename}
@app.get("/uploads/{note_id}/{filename}")
async def get_note_image(note_id: str, filename: str):
    """
    获取笔记的图片文件（业界标准固定路径）

    路由映射：
    - 前端请求：/uploads/{note_id}/{filename}
    - 实际文件：{upload_dir}/notes/{note_id}/images/{filename}

    Args:
        note_id: 笔记 ID
        filename: 图片文件名

    Returns:
        图片文件内容
    """
    # 构建实际文件路径
    file_path = Path(ORBIT_UPLOAD_DIR) / "notes" / note_id / "images" / filename

    # 安全检查：防止路径遍历攻击
    try:
        real_path = file_path.resolve()
        upload_base = Path(ORBIT_UPLOAD_DIR).resolve()
        if not str(real_path).startswith(str(upload_base)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid path: {e}")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {note_id}/{filename}")

    return FileResponse(file_path, media_type="image/jpeg")

# 书橱封面图路由
# 前端请求：/uploads/bookshelf/{bookshelf_id}/cover.{ext}
# 实际位置：{ORBIT_UPLOAD_DIR}/bookshelves/{bookshelf_id}/cover.{ext}
@app.get("/uploads/bookshelf/{bookshelf_id}/{filename}")
async def get_bookshelf_cover(bookshelf_id: str, filename: str):
    """
    获取书橱的封面图文件（业界标准固定路径）

    路由映射：
    - 前端请求：/uploads/bookshelf/{bookshelf_id}/{filename}
    - 实际文件：{upload_dir}/bookshelves/{bookshelf_id}/{filename}

    Args:
        bookshelf_id: 书橱 ID
        filename: 文件名（通常是 cover.jpg 等）

    Returns:
        图片文件内容
    """
    # 构建实际文件路径
    file_path = Path(ORBIT_UPLOAD_DIR) / "bookshelves" / bookshelf_id / filename

    # 安全检查：防止路径遍历攻击
    try:
        real_path = file_path.resolve()
        upload_base = Path(ORBIT_UPLOAD_DIR).resolve()
        if not str(real_path).startswith(str(upload_base)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid path: {e}")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Cover not found: {bookshelf_id}/{filename}")

    # 根据文件后缀返回正确的媒体类型
    media_type = "image/jpeg"
    if filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".gif"):
        media_type = "image/gif"
    elif filename.endswith(".webp"):
        media_type = "image/webp"
    elif filename.endswith(".svg"):
        media_type = "image/svg+xml"

    return FileResponse(file_path, media_type=media_type)

# Checkpoint marker 图片路由
# 前端请求：/uploads/checkpoints/{note_id}/{checkpoint_id}/{marker_id_short}/{filename}
# 实际位置：{ORBIT_UPLOAD_DIR}/notes/{note_id}/checkpoints/{checkpoint_id}/markers/{marker_id_short}/images/{filename}
# 其中 marker_id_short 是 marker_id 的前 8 个字符
@app.get("/uploads/checkpoints/{note_id}/{checkpoint_id}/{marker_id_short}/{filename}")
async def get_checkpoint_marker_image(note_id: str, checkpoint_id: str, marker_id_short: str, filename: str):
    """
    获取 checkpoint marker 的图片文件

    路由映射：
    - 前端请求：/uploads/checkpoints/{note_id}/{checkpoint_id}/{marker_id_short}/{filename}
    - 实际文件：{upload_dir}/notes/{note_id}/checkpoints/{checkpoint_id}/markers/{marker_id_short}/images/{filename}

    Args:
        note_id: 笔记 ID
        checkpoint_id: checkpoint ID
        marker_id_short: marker ID 的前 8 个字符
        filename: 图片文件名

    Returns:
        图片文件内容
    """
    # 构建实际文件路径
    file_path = Path(ORBIT_UPLOAD_DIR) / "notes" / note_id / "checkpoints" / checkpoint_id / "markers" / marker_id_short / "images" / filename

    # 安全检查：防止路径遍历攻击
    try:
        real_path = file_path.resolve()
        upload_base = Path(ORBIT_UPLOAD_DIR).resolve()
        if not str(real_path).startswith(str(upload_base)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid path: {e}")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {note_id}/checkpoints/{checkpoint_id}/markers/{marker_id_short}/{filename}")

    # 根据文件后缀返回正确的媒体类型
    media_type = "image/jpeg"
    if filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".gif"):
        media_type = "image/gif"
    elif filename.endswith(".webp"):
        media_type = "image/webp"
    elif filename.endswith(".svg"):
        media_type = "image/svg+xml"

    return FileResponse(file_path, media_type=media_type)


# Note 封面图路由
# 前端请求：/uploads/notes/{note_id}/cover/{filename}
# 实际位置：{ORBIT_UPLOAD_DIR}/notes/{note_id}/cover/{filename}
@app.get("/uploads/notes/{note_id}/cover/{filename}")
async def get_note_cover(note_id: str, filename: str):
    """
    获取 Note 的封面图文件

    路由映射：
    - 前端请求：/uploads/notes/{note_id}/cover/{filename}
    - 实际文件：{upload_dir}/notes/{note_id}/cover/{filename}

    Args:
        note_id: Note ID
        filename: 文件名（通常是 cover.jpg 等）

    Returns:
        图片文件内容
    """
    # 构建实际文件路径
    file_path = Path(ORBIT_UPLOAD_DIR) / "notes" / note_id / "cover" / filename

    # 安全检查：防止路径遍历攻击
    try:
        real_path = file_path.resolve()
        upload_base = Path(ORBIT_UPLOAD_DIR).resolve()
        if not str(real_path).startswith(str(upload_base)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid path: {e}")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Cover not found: {note_id}/cover/{filename}")

    # 根据文件后缀返回正确的媒体类型
    media_type = "image/jpeg"
    if filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".gif"):
        media_type = "image/gif"
    elif filename.endswith(".webp"):
        media_type = "image/webp"
    elif filename.endswith(".svg"):
        media_type = "image/svg+xml"

    return FileResponse(file_path, media_type=media_type)


api.include_router(orbit_notes.router)
api.include_router(orbit_uploads.router)
api.include_router(orbit_tags.router)
api.include_router(orbit_diagrams.router)
api.include_router(orbit_bookshelves.router)
api.include_router(orbit_checkpoints.router)
api.include_router(orbit_media.router)

# 统一媒体文件服务路由
# 前端请求：/media/workspaces/{entity_type}/{entity_id}/{filename}
# 实际位置：{ORBIT_UPLOAD_DIR}/media/workspaces/{entity_type}/{entity_id}/{filename}
@app.get("/media/workspaces/{entity_type}/{entity_id}/{filename}")
async def get_media_file(entity_type: str, entity_id: str, filename: str):
    """
    获取统一媒体文件服务端点

    路由映射：
    - 前端请求：/media/workspaces/{entity_type}/{entity_id}/{filename}
    - 实际文件：{upload_dir}/media/workspaces/{entity_type}/{entity_id}/{filename}

    Args:
        entity_type: 实体类型 (checkpoint_marker, note_cover, bookshelf_cover, etc)
        entity_id: 实体 ID
        filename: 文件名

    Returns:
        媒体文件内容
    """
    # 构建实际文件路径
    file_path = Path(ORBIT_UPLOAD_DIR) / "media" / "workspaces" / entity_type / entity_id / filename

    # 安全检查：防止路径遍历攻击
    try:
        real_path = file_path.resolve()
        upload_base = Path(ORBIT_UPLOAD_DIR).resolve()
        if not str(real_path).startswith(str(upload_base)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid path: {e}")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Media file not found: {entity_type}/{entity_id}/{filename}")

    # 根据文件后缀返回正确的媒体类型
    media_type = "application/octet-stream"
    if filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif filename.endswith(".gif"):
        media_type = "image/gif"
    elif filename.endswith(".webp"):
        media_type = "image/webp"
    elif filename.endswith(".svg"):
        media_type = "image/svg+xml"
    elif filename.endswith(".mp4"):
        media_type = "video/mp4"
    elif filename.endswith(".webm"):
        media_type = "video/webm"

    return FileResponse(file_path, media_type=media_type)


# 临时文件路由（用于业界标准的临时上传流程）
# 前端请求：/uploads/temp/{filename}
# 实际位置：{ORBIT_UPLOAD_DIR}/temp/{filename}
@app.get("/uploads/temp/{filename}")
async def get_temp_image(filename: str):
    """
    获取临时上传的图片文件

    这支持业界标准的临时上传流程：
    1. 用户上传 → /api/orbit/uploads/temp → 返回临时 URL
    2. 前端访问：/uploads/temp/{filename} → 获取文件
    3. 用户保存笔记 → /api/orbit/uploads/finalize → 文件移到永久位置

    路由映射：
    - 前端请求：/uploads/temp/{filename}
    - 实际文件：{upload_dir}/temp/{filename}

    Args:
        filename: 文件名（格式：{uuid}.{ext}）

    Returns:
        图片文件内容
    """
    # 构建实际文件路径
    file_path = Path(ORBIT_UPLOAD_DIR) / "temp" / filename

    # 安全检查：防止路径遍历攻击
    try:
        real_path = file_path.resolve()
        upload_base = Path(ORBIT_UPLOAD_DIR).resolve()
        if not str(real_path).startswith(str(upload_base)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid path: {e}")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: temp/{filename}")

    # 根据文件后缀返回正确的媒体类型
    media_type = "application/octet-stream"
    if filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif filename.endswith(".gif"):
        media_type = "image/gif"
    elif filename.endswith(".webp"):
        media_type = "image/webp"
    elif filename.endswith(".svg"):
        media_type = "image/svg+xml"

    return FileResponse(file_path, media_type=media_type)

app.include_router(api)