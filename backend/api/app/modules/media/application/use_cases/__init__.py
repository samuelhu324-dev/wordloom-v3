"""
Media UseCase 层 - 业务操作编排

每个文件包含一个 UseCase 类，代表一个业务操作：
  - upload_image.py              - UploadImageUseCase
  - upload_video.py              - UploadVideoUseCase
  - delete_media.py              - DeleteMediaUseCase
  - restore_media.py             - RestoreMediaUseCase
  - purge_media.py               - PurgeMediaUseCase
  - associate_media.py           - AssociateMediaUseCase
  - disassociate_media.py        - DisassociateMediaUseCase
  - get_media.py                 - GetMediaUseCase
  - update_media_metadata.py     - UpdateMediaMetadataUseCase

UseCase 类特点：
  1. 执行单一业务操作
  2. 编排域对象和存储库
  3. 验证业务规则
  4. 抛出特定异常
  5. 无状态设计（通过 DI 注入依赖）

导入示例:
  from .upload_image import UploadImageUseCase
  from .delete_media import DeleteMediaUseCase

使用示例 (在 Router 中):
  upload_image_use_case = UploadImageUseCase(media_repository)
  media = await upload_image_use_case.execute(
      filename="photo.png",
      mime_type=MediaMimeType.PNG,
      file_size=2097152,
      storage_key="uuid-key"
  )
"""

from .upload_image import UploadImageUseCase
from .upload_video import UploadVideoUseCase
from .delete_media import DeleteMediaUseCase
from .restore_media import RestoreMediaUseCase
from .purge_media import PurgeMediaUseCase
from .associate_media import AssociateMediaUseCase
from .disassociate_media import DisassociateMediaUseCase
from .get_media import GetMediaUseCase
from .update_media_metadata import UpdateMediaMetadataUseCase

__all__ = [
    "UploadImageUseCase",
    "UploadVideoUseCase",
    "DeleteMediaUseCase",
    "RestoreMediaUseCase",
    "PurgeMediaUseCase",
    "AssociateMediaUseCase",
    "DisassociateMediaUseCase",
    "GetMediaUseCase",
    "UpdateMediaMetadataUseCase",
]
