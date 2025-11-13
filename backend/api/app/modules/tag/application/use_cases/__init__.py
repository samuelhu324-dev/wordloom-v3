"""
Tag UseCase 层 - 业务操作编排

每个文件包含一个 UseCase 类，代表一个业务操作：
  - create_tag.py        - CreateTagUseCase
  - create_subtag.py     - CreateSubtagUseCase
  - update_tag.py        - UpdateTagUseCase
  - delete_tag.py        - DeleteTagUseCase
  - restore_tag.py       - RestoreTagUseCase
  - associate_tag.py     - AssociateTagUseCase
  - disassociate_tag.py  - DisassociateTagUseCase
  - search_tags.py       - SearchTagsUseCase
  - get_most_used_tags.py - GetMostUsedTagsUseCase

UseCase 类特点：
  1. 执行单一业务操作
  2. 编排域对象和存储库
  3. 验证业务规则
  4. 抛出特定异常
  5. 无状态设计（通过 DI 注入依赖）

导入示例:
  from .create_tag import CreateTagUseCase
  from .search_tags import SearchTagsUseCase

使用示例 (在 Router 中):
  create_tag_use_case = CreateTagUseCase(tag_repository)
  tag = await create_tag_use_case.execute(name="Python", color="#3776AB")
"""

from .create_tag import CreateTagUseCase
from .create_subtag import CreateSubtagUseCase
from .update_tag import UpdateTagUseCase
from .delete_tag import DeleteTagUseCase
from .restore_tag import RestoreTagUseCase
from .associate_tag import AssociateTagUseCase
from .disassociate_tag import DisassociateTagUseCase
from .search_tags import SearchTagsUseCase
from .get_most_used_tags import GetMostUsedTagsUseCase

__all__ = [
    "CreateTagUseCase",
    "CreateSubtagUseCase",
    "UpdateTagUseCase",
    "DeleteTagUseCase",
    "RestoreTagUseCase",
    "AssociateTagUseCase",
    "DisassociateTagUseCase",
    "SearchTagsUseCase",
    "GetMostUsedTagsUseCase",
]
