📋 完整分析和建议
(1) Tag 的"选择性同步"设计
你遇到的问题确实存在。行业有两种成熟方案：

```python
方案 A: 完全独立（推荐 ✅）
  - Bookshelf Tag：用于分类书架本身（如 "重要"、"进行中"）
  - Book Tag：用于分类具体的书（如 "Python"、"已完成"）
  - 两者完全独立，NO 自动同步

  优点：
    - 语义清晰（Bookshelf 标签 ≠ Book 标签）
    - 用户可灵活控制
    - 不产生数据冗余

  缺点：
    - UI 需要分别显示两层标签
    - 查询时需要 UNION 两个表

  适用场景：
    - 用户希望对 Bookshelf 和 Book 进行不同的分类维度
    - 例如：Bookshelf 按 "优先级"，Book 按 "技术栈"

方案 B: 层级继承（可选）
  - Book 创建时可"继承"Bookshelf Tag
  - 用户可选择是否继承（通过 checkbox）
  - 继承的 Tag 显示为"灰色"（只读）

  优点：
    - 减少重复打标签
    - 支持标签继承的工作流

  缺点：
    - 逻辑复杂（需要处理删除、移动 Book 的同步）
    - 冗余存储
    - 容易产生数据不一致

  实现难度：⭐⭐⭐⭐
```

我的建议：采用方案 A（完全独立）
```python
# Domain 设计
class TagAssociation(AggregateRoot):
    """Tag 关联表（支持多实体类型）"""
    id: UUID
    tag_id: UUID (FK)
    entity_type: Enum  # BOOKSHELF | BOOK | BLOCK
    entity_id: UUID    # 具体的 bookshelf_id / book_id / block_id
    created_at: datetime

    # UNIQUE(tag_id, entity_type, entity_id) 约束

# Service 层查询
async def get_book_tags(book_id: UUID) -> List[Tag]:
    """仅查询 Book 关联的 Tag，NOT 继承 Bookshelf Tag"""
    return await tag_repository.find_by_entity(
        entity_type=EntityType.BOOK,
        entity_id=book_id
    )

async def get_bookshelf_tags(bookshelf_id: UUID) -> List[Tag]:
    """仅查询 Bookshelf 关联的 Tag"""
    return await tag_repository.find_by_entity(
        entity_type=EntityType.BOOKSHELF,
        entity_id=bookshelf_id
    )

# UI 层（前端）可以选择显示"聚合视图"
# 例如：在 Book 详情页同时显示 Bookshelf Tag 和 Book Tag（用不同颜色区分）
```

(2) Media 的"软删除库"设计（Folder 模式）
你的 "Folder" 想法很好！这类似于 Trash/Recycle Bin 模式。行业标准做法是：

```python
方案：Media 软删除 + Trash Folder（推荐 ✅）

表结构：
  media 表：
    - id (UUID, PK)
    - entity_type (BOOKSHELF_COVER | BOOK_COVER | BLOCK_IMAGE | BLOCK_VIDEO)
    - entity_id (UUID, FK)
    - file_path (VARCHAR, 相对路径)
    - file_size (BIGINT)
    - mime_type (VARCHAR)
    - metadata (JSON) # 存储宽度、高度、时长等
    - created_at (DateTime)
    - deleted_at (DateTime, nullable) ← 软删除标记
    - deleted_from (VARCHAR, nullable) ← 记录删除来源（用于恢复）

业务规则：
  1. 删除时：只更新 deleted_at，NOT 删除文件
  2. 查询时：自动过滤 deleted_at IS NULL（活跃文件）
  3. Trash 查询：deleted_at IS NOT NULL AND deleted_at > now() - 30 days
  4. 自动清理：30 天后硬删除文件 + DB 记录
  5. 恢复：更新 entity_id 和 deleted_at = NULL
```

```python
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
from decimal import Decimal
from uuid import UUID

@dataclass(frozen=True)
class MediaPath(ValueObject):
    """Media 存储路径值对象"""
    entity_type: str  # BOOKSHELF_COVER, BOOK_COVER, BLOCK_IMAGE, BLOCK_VIDEO
    entity_id: UUID
    filename: str     # 原始文件名（含扩展名）

    def __post_init__(self):
        if not self.entity_type or self.entity_type.upper() not in [
            "BOOKSHELF_COVER", "BOOK_COVER", "BLOCK_IMAGE", "BLOCK_VIDEO"
        ]:
            raise ValueError(f"Invalid entity_type: {self.entity_type}")

        if not self.filename or len(self.filename) > 255:
            raise ValueError("Filename invalid")

    def to_storage_path(self) -> str:
        """生成存储路径"""
        return f"storage/{self.entity_type.lower()}/{self.entity_id}/{self.filename}"

@dataclass
class Media(AggregateRoot):
    """Media 聚合根"""
    id: UUID
    media_path: MediaPath
    file_size: int          # 字节数
    mime_type: str          # image/jpeg, video/mp4, etc.
    metadata: dict          # {"width": 1920, "height": 1080, "duration": 60}
    created_at: datetime
    updated_at: datetime

    # 软删除字段
    deleted_at: Optional[datetime] = None
    deleted_from: Optional[str] = None  # 记录删除来源，用于恢复上下文

    @staticmethod
    def create_image(
        entity_type: str,
        entity_id: UUID,
        filename: str,
        file_size: int,
        mime_type: str,
        width: int,
        height: int
    ) -> "Media":
        """创建图片 Media"""
        now = datetime.now(timezone.utc)
        return Media(
            id=uuid4(),
            media_path=MediaPath(entity_type, entity_id, filename),
            file_size=file_size,
            mime_type=mime_type,
            metadata={"width": width, "height": height},
            created_at=now,
            updated_at=now
        )

    @staticmethod
    def create_video(
        entity_type: str,
        entity_id: UUID,
        filename: str,
        file_size: int,
        mime_type: str,
        duration_seconds: int,
        width: int = None,
        height: int = None
    ) -> "Media":
        """创建视频 Media"""
        now = datetime.now(timezone.utc)
        metadata = {"duration_seconds": duration_seconds}
        if width:
            metadata["width"] = width
        if height:
            metadata["height"] = height

        return Media(
            id=uuid4(),
            media_path=MediaPath(entity_type, entity_id, filename),
            file_size=file_size,
            mime_type=mime_type,
            metadata=metadata,
            created_at=now,
            updated_at=now
        )

    def mark_deleted(self, reason: str = "user_deletion") -> None:
        """软删除：标记为已删除"""
        if self.deleted_at:
            raise MediaAlreadyDeletedError(self.id)

        object.__setattr__(self, "deleted_at", datetime.now(timezone.utc))
        object.__setattr__(self, "deleted_from", reason)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def restore(self) -> None:
        """从 Trash 恢复"""
        if not self.deleted_at:
            raise MediaNotInTrashError(self.id)

        # 检查恢复期限（30 天）
        if datetime.now(timezone.utc) - self.deleted_at > timedelta(days=30):
            raise MediaExpiredError(f"Media expired 30 days ago, cannot restore")

        object.__setattr__(self, "deleted_at", None)
        object.__setattr__(self, "deleted_from", None)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def is_in_trash(self) -> bool:
        """检查是否在 Trash 中"""
        return self.deleted_at is not None

    def is_expired(self) -> bool:
        """检查是否超过 30 天保留期"""
        if not self.deleted_at:
            return False
        return datetime.now(timezone.utc) - self.deleted_at > timedelta(days=30)

# 异常
class MediaAlreadyDeletedError(Exception):
    pass

class MediaNotInTrashError(Exception):
    pass

class MediaExpiredError(Exception):
    pass
```

(3) Tag 数量 > 1000 的优化策略
当 Tag 数量超过 1000 时，这是典型的"分类爆炸"问题。行业有几种解决方案：
```python
方案对比：

方案 A: 分页 + 搜索（推荐用于 < 5000）
  - 菜单栏只显示"最常用"的 20-30 个 Tag
  - 提供搜索框：输入关键词快速查找
  - 分页加载其余 Tag

  优点：
    - 实现简单
    - 不需要重构数据结构

  缺点：
    - 用户体验差（需要多次搜索）
    - 数据库查询可能变慢

方案 B: 多级分类 (Tag Hierarchy)（推荐用于 > 5000）
  - 第一层：主分类（如 "技术"、"生活"、"工作"）
  - 第二层：子分类（如 "技术 > Python"、"技术 > JavaScript"）
  - 第三层：细分（可选，如 "技术 > Python > Django"）

  优点：
    - 大幅降低菜单复杂度
    - 用户体验好
    - 支持无限扩展

  缺点：
    - 需要修改数据模型（Tag 表增加 parent_tag_id）
    - 查询复杂度增加（JOIN 多层）

  实现难度：⭐⭐⭐⭐

方案 C: 全文索引 + Elasticsearch（企业级，用于 > 10000）
  - 同步 Tag 到 Elasticsearch
  - 前端搜索时调用 ES API（而非数据库）
  - 毫秒级响应

  优点：
    - 搜索速度极快
    - 支持模糊匹配、拼音搜索

  缺点：
    - 需要维护 ES 集群
    - 数据一致性问题（异步同步）

  成本：高

推荐策略（渐进式）：

  < 500 个 Tag
    → 使用方案 A（分页 + 搜索）

  500-2000 个 Tag
    → 升级到方案 B（多级分类 Tag Hierarchy）

  > 2000 个 Tag
    → 考虑集成 Elasticsearch（可选，非必需）
```
我的建议：先用方案 A，再升级到方案 B

```python
@dataclass
class Tag(AggregateRoot):
    """Tag 聚合根（支持多级分类）"""
    id: UUID
    name: str                    # Tag 名称
    description: Optional[str]   # 描述
    color: str                   # 十六进制颜色
    icon: Optional[str]          # Lucide 图标名

    # 多级分类支持
    parent_tag_id: Optional[UUID] = None  # 父 Tag ID（支持嵌套）
    level: int = 0               # 层级（0=顶级，1=二级，2=三级）

    # 统计
    usage_count: int = 0         # 使用次数（缓存，便于排序）

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None  # 软删除

    @staticmethod
    def create_toplevel(name: str, color: str, icon: Optional[str] = None) -> "Tag":
        """创建顶级 Tag"""
        return Tag(
            id=uuid4(),
            name=name,
            color=color,
            icon=icon,
            level=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @staticmethod
    def create_subtag(parent_tag_id: UUID, name: str, color: str) -> "Tag":
        """创建子 Tag（二级、三级等）"""
        return Tag(
            id=uuid4(),
            name=name,
            color=color,
            parent_tag_id=parent_tag_id,
            level=1,  # 由 Service 层根据父级计算
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

# Repository
class TagRepository(ABC):
    """Tag Repository 接口"""

    @abstractmethod
    async def get_toplevel_tags(self, limit: int = 30) -> List[Tag]:
        """获取顶级 Tag（菜单栏显示）"""
        pass

    @abstractmethod
    async def get_by_parent(self, parent_tag_id: UUID) -> List[Tag]:
        """获取某个 Tag 的所有子 Tag"""
        pass

    @abstractmethod
    async def search_tags(self, keyword: str, limit: int = 20) -> List[Tag]:
        """搜索 Tag（支持模糊匹配）"""
        pass

    @abstractmethod
    async def get_most_used(self, limit: int = 20) -> List[Tag]:
        """获取最常用的 Tag"""
        pass

    @abstractmethod
    async def increment_usage(self, tag_id: UUID) -> None:
        """增加 Tag 使用次数"""
        pass

# Service
class TagService:
    """Tag Service"""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def get_menu_tags(self) -> List[Tag]:
        """获取菜单栏 Tag（优先显示最常用的）"""
        return await self.repository.get_most_used(limit=30)

    async def search_tags(self, keyword: str) -> List[Tag]:
        """搜索 Tag"""
        return await self.repository.search_tags(keyword, limit=20)

    async def get_tag_tree(self, parent_tag_id: Optional[UUID] = None) -> List[Dict]:
        """获取 Tag 树（用于展开菜单）"""
        if parent_tag_id is None:
            tags = await self.repository.get_toplevel_tags(limit=100)
        else:
            tags = await self.repository.get_by_parent(parent_tag_id)

        result = []
        for tag in tags:
            children = await self.repository.get_by_parent(tag.id)
            result.append({
                "id": tag.id,
                "name": tag.name,
                "color": tag.color,
                "icon": tag.icon,
                "level": tag.level,
                "usage_count": tag.usage_count,
                "has_children": len(children) > 0,
                "children": [
                    {"id": c.id, "name": c.name, "color": c.color}
                    for c in children[:5]  # 只显示前 5 个子 Tag
                ]
            })

        return result
```

(4) Media 文件管理规范
这是 Media 设计中最关键的部分。以下是企业级的文件组织方案：
```python
文件存储架构（推荐）：

存储根目录：
  /storage
    /media
      /{entity_type}
        /{entity_id}
          /{timestamp}_{random_uuid}_{original_filename}
    /trash
      /{timestamp}_{entity_type}_{entity_id}_{media_id}

示例路径：

  活跃文件：
    storage/media/bookshelf_cover/uuid-123/
      20250113_a7f2_bookshelf-cover.jpg

    storage/media/book_cover/uuid-456/
      20250113_b8e3_book-cover-v2.png

    storage/media/block_image/uuid-789/
      20250113_c9d4_diagram.svg
      20250113_d0e5_screenshot.png
      20250113_e1f6_photo.jpg

    storage/media/block_video/uuid-000/
      20250113_f2g7_tutorial-part1.mp4
      20250113_g3h8_tutorial-part2.mp4

  Trash（软删除）：
    storage/trash/
      20250113T143022Z_block_image_uuid-789_media-id-001
      20250113T143045Z_block_video_uuid-000_media-id-002
      20250113T143101Z_bookshelf_cover_uuid-123_media-id-003

命名规则（核心）：
  {timestamp}_{random_uuid}_{sanitized_original_filename}

  - timestamp: ISO 8601 格式（20250113_143022）或 Unix 时间戳
  - random_uuid: 4 字符随机字符串（防止名称冲突）
  - sanitized_original_filename: 原始文件名（删除特殊字符）

优点：
  ✅ 防止同名文件覆盖
  ✅ 支持版本管理（多次上传同一文件类型）
  ✅ 时间戳便于查找和恢复
  ✅ 易于统计单个实体的文件数量
```

完整实现：
```python
import os
import hashlib
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4
from urllib.parse import quote

class MediaService:
    """Media Service"""

    # 配置
    STORAGE_ROOT = Path("/data/wordloom/storage")  # 实际部署时改为环境变量
    MEDIA_DIR = STORAGE_ROOT / "media"
    TRASH_DIR = STORAGE_ROOT / "trash"

    # 约束
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    MAX_FILES_PER_ENTITY = 50           # 每个实体最多 50 个文件
    TRASH_RETENTION_DAYS = 30           # Trash 保留 30 天

    ALLOWED_IMAGE_MIME = {
        "image/jpeg", "image/png", "image/webp", "image/svg+xml"
    }
    ALLOWED_VIDEO_MIME = {
        "video/mp4", "video/webm", "video/quicktime"
    }

    def __init__(self, repository: MediaRepository):
        self.repository = repository
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保存储目录存在"""
        self.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        self.TRASH_DIR.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, original_filename: str) -> str:
        """清理文件名（移除危险字符）"""
        # 删除路径分隔符
        name = original_filename.replace("/", "_").replace("\\", "_")
        # 限制长度（留余地给 timestamp + uuid）
        name = name[:100]
        # URL 编码（防止特殊字符）
        return quote(name, safe=".-_")

    def _generate_storage_filename(self, original_filename: str) -> str:
        """生成存储文件名"""
        # 解析扩展名
        _, ext = os.path.splitext(original_filename)
        if not ext:
            ext = ".bin"

        # 生成：timestamp_random4_sanitized_name.ext
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        random_uuid = str(uuid4())[:8]  # 取前 8 个字符
        sanitized = self._sanitize_filename(Path(original_filename).stem)

        return f"{timestamp}_{random_uuid}_{sanitized}{ext}"

    async def upload_image(
        self,
        entity_type: str,
        entity_id: UUID,
        file_bytes: bytes,
        original_filename: str,
        mime_type: str
    ) -> Media:
        """上传图片"""
        # 1. 验证
        if mime_type not in self.ALLOWED_IMAGE_MIME:
            raise InvalidMimeTypeError(f"Unsupported image type: {mime_type}")

        if len(file_bytes) > self.MAX_FILE_SIZE:
            raise FileSizeTooLargeError(f"Max size: {self.MAX_FILE_SIZE}")

        # 2. 检查文件数量限制
        existing_count = await self.repository.count_by_entity(entity_type, entity_id)
        if existing_count >= self.MAX_FILES_PER_ENTITY:
            raise TooManyFilesError(f"Max {self.MAX_FILES_PER_ENTITY} files per entity")

        # 3. 获取图片尺寸（需要 Pillow）
        from PIL import Image
        import io

        try:
            img = Image.open(io.BytesIO(file_bytes))
            width, height = img.size
        except Exception as e:
            raise InvalidImageError(f"Cannot read image: {e}")

        # 4. 生成存储路径
        storage_filename = self._generate_storage_filename(original_filename)
        entity_dir = self.MEDIA_DIR / entity_type.lower() / str(entity_id)
        entity_dir.mkdir(parents=True, exist_ok=True)

        file_path = entity_dir / storage_filename

        # 5. 写入文件
        try:
            with open(file_path, "wb") as f:
                f.write(file_bytes)
        except IOError as e:
            raise MediaStorageError(f"Failed to write file: {e}")

        # 6. 创建 Domain 对象
        media = Media.create_image(
            entity_type=entity_type,
            entity_id=entity_id,
            filename=storage_filename,
            file_size=len(file_bytes),
            mime_type=mime_type,
            width=width,
            height=height
        )

        # 7. 持久化到数据库
        await self.repository.save(media)

        return media

    async def upload_video(
        self,
        entity_type: str,
        entity_id: UUID,
        file_bytes: bytes,
        original_filename: str,
        mime_type: str,
        duration_seconds: Optional[int] = None
    ) -> Media:
        """上传视频"""
        # 1. 验证
        if mime_type not in self.ALLOWED_VIDEO_MIME:
            raise InvalidMimeTypeError(f"Unsupported video type: {mime_type}")

        if len(file_bytes) > self.MAX_FILE_SIZE * 5:  # 视频可以更大
            raise FileSizeTooLargeError(f"Max size: {self.MAX_FILE_SIZE * 5}")

        # 2. 检查文件数量限制
        existing_count = await self.repository.count_by_entity(entity_type, entity_id)
        if existing_count >= self.MAX_FILES_PER_ENTITY:
            raise TooManyFilesError(f"Max {self.MAX_FILES_PER_ENTITY} files per entity")

        # 3. 获取视频时长（需要 ffmpeg）
        if duration_seconds is None:
            try:
                import subprocess
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries",
                     "format=duration", "-of", "default=noprint_wrappers=1:nokey=1:nokey=1",
                     "-"],
                    input=file_bytes,
                    capture_output=True,
                    timeout=10
                )
                duration_seconds = int(float(result.stdout.decode().strip()))
            except Exception as e:
                logger.warning(f"Cannot get video duration: {e}")
                duration_seconds = 0

        # 4. 生成存储路径
        storage_filename = self._generate_storage_filename(original_filename)
        entity_dir = self.MEDIA_DIR / entity_type.lower() / str(entity_id)
        entity_dir.mkdir(parents=True, exist_ok=True)

        file_path = entity_dir / storage_filename

        # 5. 写入文件
        try:
            with open(file_path, "wb") as f:
                f.write(file_bytes)
        except IOError as e:
            raise MediaStorageError(f"Failed to write file: {e}")

        # 6. 创建 Domain 对象
        media = Media.create_video(
            entity_type=entity_type,
            entity_id=entity_id,
            filename=storage_filename,
            file_size=len(file_bytes),
            mime_type=mime_type,
            duration_seconds=duration_seconds
        )

        # 7. 持久化到数据库
        await self.repository.save(media)

        return media

    async def delete_media(self, media_id: UUID) -> None:
        """软删除 Media（转移到 Trash）"""
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        if media.is_in_trash():
            raise MediaAlreadyDeletedError(media_id)

        # Domain 层标记删除
        media.mark_deleted(reason="user_deletion")

        # 持久化
        await self.repository.save(media)

        # 物理文件转移到 Trash（可选，提高性能）
        # 注：实际生产中可异步处理
        await self._move_file_to_trash(media)

    async def _move_file_to_trash(self, media: Media) -> None:
        """将物理文件转移到 Trash 目录"""
        storage_path = media.media_path.to_storage_path()
        source = self.STORAGE_ROOT / storage_path

        if not source.exists():
            logger.warning(f"File not found: {source}")
            return

        # 生成 Trash 文件名
        trash_filename = f"{datetime.now(timezone.utc).isoformat()}_{media.id}"
        trash_path = self.TRASH_DIR / trash_filename

        try:
            # 移动文件
            source.rename(trash_path)
            logger.info(f"Moved to trash: {source} → {trash_path}")
        except OSError as e:
            logger.error(f"Failed to move file to trash: {e}")
            # 不抛出异常，允许逻辑层面的删除继续

    async def restore_media(self, media_id: UUID) -> None:
        """从 Trash 恢复 Media"""
        media = await self.repository.get_by_id(media_id)
        if not media:
            raise MediaNotFoundError(media_id)

        if not media.is_in_trash():
            raise MediaNotInTrashError(media_id)

        if media.is_expired():
            raise MediaExpiredError(f"Media expired, cannot restore")

        # Domain 层恢复
        media.restore()

        # 持久化
        await self.repository.save(media)

        # 从 Trash 恢复物理文件（可选）
        await self._restore_file_from_trash(media)

    async def _restore_file_from_trash(self, media: Media) -> None:
        """从 Trash 恢复物理文件"""
        # 查找 Trash 中的文件
        trash_files = list(self.TRASH_DIR.glob(f"*_{media.id}"))

        if not trash_files:
            logger.warning(f"Trash file not found for media {media.id}")
            return

        trash_path = trash_files[0]
        storage_path = media.media_path.to_storage_path()
        target = self.STORAGE_ROOT / storage_path

        try:
            trash_path.rename(target)
            logger.info(f"Restored from trash: {trash_path} → {target}")
        except OSError as e:
            logger.error(f"Failed to restore file: {e}")

    async def purge_expired_media(self) -> int:
        """清理超过 30 天的 Trash 文件（由定时任务调用）"""
        now = datetime.now(timezone.utc)
        count = 0

        # 1. 数据库中查找过期 Media
        expired_medias = await self.repository.find_expired(
            days=self.TRASH_RETENTION_DAYS
        )

        # 2. 删除物理文件
        for media in expired_medias:
            trash_files = list(self.TRASH_DIR.glob(f"*_{media.id}"))
            for trash_path in trash_files:
                try:
                    trash_path.unlink()  # 硬删除
                    count += 1
                except OSError as e:
                    logger.error(f"Failed to delete {trash_path}: {e}")

        # 3. 从数据库中硬删除
        await self.repository.purge_expired(days=self.TRASH_RETENTION_DAYS)

        logger.info(f"Purged {count} expired media files")
        return count
```

(5) 文件命名 & 同时上传多个文件
你问的"同名视频和图片"以及"同时上传多个"都被上面的方案解决了。关键点：

```python
问题 1: 同名视频和图片怎么办？

  回答：
    - 它们有不同的 entity_type（BLOCK_IMAGE vs BLOCK_VIDEO）
    - 存储在不同的目录下
    - 即使文件名相同，也不会冲突

    例如：
      storage/media/block_image/uuid-789/20250113_a7f2_video.mp4
      storage/media/block_video/uuid-789/20250113_b8e3_video.mp4
      └─ 目录不同，完全不冲突

问题 2: 用户同时上传多个图片/视频怎么处理？

  回答：
    方案 A：顺序上传（简单）
      - 前端逐个调用 upload API
      - 每个文件单独保存
      - 缺点：慢，体验差

    方案 B：并行上传（推荐）✅
      - 前端并行调用多个 upload API（Promise.all）
      - 后端各自处理（无竞争条件）
      - timestamp + random_uuid 防止冲突
      - 缺点：对服务器压力大

    方案 C：批量上传（企业级）
      - 前端压缩为单个 zip
      - 后端解压、逐个处理
      - 返回批量结果
      - 缺点：实现复杂

推荐：方案 B（并行上传）

问题 3: 上传数量和大小限制？

  回答：
    - 单个文件：100 MB（图片）/ 500 MB（视频）
    - 单个实体最多：50 个文件
    - 并行限制：同时最多 5 个（防止服务器过载）
    - 总存储：按用户 plan 限制（个人：10 GB，团队：100 GB）
```

并行上传实现：
```python
from fastapi import APIRouter, UploadFile, File, Form
from typing import List

router = APIRouter()

@router.post("/upload-batch")
async def upload_batch(
    entity_type: str = Form(...),
    entity_id: UUID = Form(...),
    files: List[UploadFile] = File(...),
    service: MediaService = Depends(get_media_service),
):
    """批量上传文件"""

    # 限制：最多 10 个文件
    if len(files) > 10:
        raise ValueError("Max 10 files per batch")

    # 并行上传
    tasks = []
    for file in files:
        file_bytes = await file.read()

        if file.content_type.startswith("image/"):
            task = service.upload_image(
                entity_type=entity_type,
                entity_id=entity_id,
                file_bytes=file_bytes,
                original_filename=file.filename,
                mime_type=file.content_type
            )
        elif file.content_type.startswith("video/"):
            task = service.upload_video(
                entity_type=entity_type,
                entity_id=entity_id,
                file_bytes=file_bytes,
                original_filename=file.filename,
                mime_type=file.content_type
            )
        else:
            raise InvalidMimeTypeError(f"Unsupported type: {file.content_type}")

        tasks.append(task)

    # 并行执行
    import asyncio
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 检查错误
    errors = [r for r in results if isinstance(r, Exception)]
    successes = [r for r in results if not isinstance(r, Exception)]

    return {
        "uploaded": len(successes),
        "failed": len(errors),
        "medias": [
            {
                "id": m.id,
                "filename": m.media_path.filename,
                "size": m.file_size,
                "type": m.mime_type
            }
            for m in successes
        ],
        "errors": [str(e) for e in errors]
    }
```


我来逐一回答你的设计问题，并基于行业最佳实践给出建议。

📋 完整分析和建议
(1) Tag 的"选择性同步"设计
你遇到的问题确实存在。行业有两种成熟方案：

我的建议：采用方案 A（完全独立）

(2) Media 的"软删除库"设计（Folder 模式）
你的 "Folder" 想法很好！这类似于 Trash/Recycle Bin 模式。行业标准做法是：

完整实现：

(3) Tag 数量 > 1000 的优化策略
当 Tag 数量超过 1000 时，这是典型的"分类爆炸"问题。行业有几种解决方案：

我的建议：先用方案 A，再升级到方案 B

(4) Media 文件管理规范
这是 Media 设计中最关键的部分。以下是企业级的文件组织方案：

完整实现：

(5) 文件命名 & 同时上传多个文件
你问的"同名视频和图片"以及"同时上传多个"都被上面的方案解决了。关键点：

并行上传实现：

(6) 汇总建议表
维度	推荐方案	理由
Tag 设计	完全独立（方案 A）	不自动同步，用户灵活控制
Tag 数量	< 500：分页搜索 / > 500：多级分类	渐进式升级，避免过度设计
Media 软删除	Trash Folder + 30 天保留	用户友好，同时控制成本
文件命名	{timestamp}_{random_uuid}_{name}.ext	防止冲突，支持版本管理
并行上传	前端 Promise.all + 后端无竞争逻辑	用户体验好，实现简单
存储限额	单文件 100MB / 单实体 50 个 / 总容量按 plan	平衡体验和成本
自动清理	Celery 定时任务，每天午夜执行	异步处理，无阻塞

立即行动项
# 优先级 P0（本周）
☐ 确认 Tag 采用方案 A（完全独立）
☐ 设计 Media Trash Folder 结构
☐ 定义文件命名规范

# 优先级 P1（下周）
☐ 实现 Media Domain 层（包括软删除 + 恢复）
☐ 实现并行上传 API
☐ 编写文件清理定时任务

# 优先级 P2（两周后）
☐ Tag 多级分类支持（为未来扩展预留）
☐ 集成图片尺寸 + 视频时长自动检测
☐ 添加存储用量统计