"""
Quick Import Verification Script for Library Module

验证 Library 模块关键导入是否正确
执行方式: python tools/verify_library.py
"""

import sys
import importlib

# 关键模块列表
MODULES_TO_CHECK = [
    "modules.library.application.ports.output",
    "modules.library.application.ports.input",
    "modules.library.application.use_cases.create_library",
    "modules.library.application.use_cases.get_library",
    "modules.library.application.use_cases.delete_library",
    "infra.storage.library_repository_impl",
    "infra.database.models.library_models",
    "modules.library.routers.library_router",
    "modules.library.domain.library",
    "modules.library.domain.library_name",
    "modules.library.domain.events",
]

def check_imports():
    """验证所有模块导入"""
    print("=" * 70)
    print("Library Module Import Verification")
    print("=" * 70)

    errors = []
    successes = []

    for module_name in MODULES_TO_CHECK:
        try:
            mod = importlib.import_module(module_name)
            # 列出主要导出
            exports = [name for name in dir(mod) if not name.startswith('_')][:3]
            print(f"✅ {module_name}")
            print(f"   → Exports: {', '.join(exports)}")
            successes.append(module_name)
        except ImportError as e:
            print(f"❌ {module_name}")
            print(f"   → Error: {e}")
            errors.append((module_name, str(e)))
        except Exception as e:
            print(f"⚠️  {module_name}")
            print(f"   → Unexpected error: {type(e).__name__}: {e}")
            errors.append((module_name, str(e)))

    print("\n" + "=" * 70)
    print(f"Results: {len(successes)} OK, {len(errors)} FAILED")
    print("=" * 70)

    if errors:
        print("\n❌ Failed Imports:")
        for mod, err in errors:
            print(f"  - {mod}: {err}")
        return False
    else:
        print("\n✅ All imports successful!")
        return True

def verify_class_interfaces():
    """验证关键接口与实现类"""
    print("\n" + "=" * 70)
    print("Interface & Implementation Verification")
    print("=" * 70)

    try:
        # 1. 检查 ILibraryRepository 接口
        from modules.library.application.ports.output import ILibraryRepository
        print(f"✅ ILibraryRepository interface: {ILibraryRepository.__name__}")

        # 2. 检查 SQLAlchemyLibraryRepository 实现
        from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository
        print(f"✅ SQLAlchemyLibraryRepository adapter: {SQLAlchemyLibraryRepository.__name__}")

        # 3. 验证实现继承关系
        if issubclass(SQLAlchemyLibraryRepository, ILibraryRepository):
            print(f"✅ SQLAlchemyLibraryRepository implements ILibraryRepository")
        else:
            print(f"❌ SQLAlchemyLibraryRepository does NOT implement ILibraryRepository")
            return False

        # 4. 检查 UseCase 类
        from modules.library.application.use_cases.create_library import CreateLibraryUseCase
        print(f"✅ CreateLibraryUseCase: {CreateLibraryUseCase.__name__}")

        # 5. 检查 ORM 模型
        from infra.database.models.library_models import LibraryModel
        print(f"✅ LibraryModel ORM: {LibraryModel.__name__}, table={LibraryModel.__tablename__}")

        print("\n✅ All interfaces and implementations verified!")
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    imports_ok = check_imports()
    interfaces_ok = verify_class_interfaces()

    sys.exit(0 if (imports_ok and interfaces_ok) else 1)
