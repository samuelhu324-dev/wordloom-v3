#!/usr/bin/env python3
"""
Module Migration Script: domains/ → modules/

This script automates the migration of 4 modules from the experimental
location (backend/api/app/domains/) to the production location
(backend/api/app/modules/).

Features:
  1. Copy module folders with all files
  2. Update all import paths (domains.* → modules.*)
  3. Verify migration completeness
  4. Generate migration report
  5. Optional cleanup of old files

Usage:
  python migrate_modules.py

Output:
  - Migrated modules in backend/api/app/modules/
  - Updated import paths throughout
  - Migration report in migrate_report.txt
"""

import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import List, Tuple


class ModuleMigrator:
    """Handles automated module migration"""

    def __init__(self):
        # ✅ 正确的路径：modules/domains/ 是源，modules/ 是目标
        self.source_base = Path("backend/api/app/modules/domains")
        self.dest_base = Path("backend/api/app/modules")
        self.modules = ["library", "bookshelf", "book", "block"]
        self.report = []
        self.errors = []

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {level:8} {message}"
        print(log_msg)
        self.report.append(log_msg)

    def migrate_module(self, module_name: str) -> bool:
        """
        Migrate a single module from source to destination

        Steps:
          1. Create destination directory if not exists
          2. Copy all files
          3. Update import paths
          4. Verify completion
        """
        try:
            self.log(f"Starting migration of module: {module_name}")

            source_dir = self.source_base / module_name
            dest_dir = self.dest_base / module_name

            # Step 1: Verify source exists
            if not source_dir.exists():
                self.log(f"❌ Source directory not found: {source_dir}", "ERROR")
                self.errors.append(f"Source not found: {source_dir}")
                return False

            self.log(f"✅ Source found: {source_dir}")

            # Step 2: Clear destination if exists (backup first)
            if dest_dir.exists():
                backup_dir = dest_dir.with_name(f"{module_name}_backup_pre_migrate")
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.move(str(dest_dir), str(backup_dir))
                self.log(f"✅ Backed up existing destination to: {backup_dir}")

            # Step 3: Copy entire module directory
            shutil.copytree(str(source_dir), str(dest_dir), dirs_exist_ok=True)
            self.log(f"✅ Copied module to: {dest_dir}")

            # Step 4: Update all imports in the copied files
            updated_count = self.update_imports_in_module(dest_dir, module_name)
            self.log(f"✅ Updated {updated_count} import statements")

            # Step 5: Verify key files exist
            required_files = [
                "domain.py",
                "service.py",
                "repository.py",
                "models.py",
                "schemas.py",
                "router.py",
                "exceptions.py",
                "__init__.py",
            ]

            missing_files = []
            for filename in required_files:
                if not (dest_dir / filename).exists():
                    missing_files.append(filename)

            if missing_files:
                self.log(
                    f"⚠️  Missing files in {module_name}: {', '.join(missing_files)}",
                    "WARN",
                )

            self.log(f"✅ Migration of {module_name} completed successfully!")
            return True

        except Exception as e:
            self.log(f"❌ Error migrating {module_name}: {str(e)}", "ERROR")
            self.errors.append(f"Migration error for {module_name}: {str(e)}")
            return False

    def update_imports_in_module(self, module_dir: Path, module_name: str) -> int:
        """
        Update all import paths in a module's Python files

        Replacements:
          from domains.xxx import yyy → from modules.xxx import yyy
          import domains.xxx as yyy → import modules.xxx as yyy
          from domains import xxx → from modules import xxx
        """
        updated_count = 0

        for py_file in module_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                original_content = content

                # Pattern 1: from domains.xxx import yyy
                content = re.sub(
                    r"from\s+domains\.(\w+)",
                    r"from modules.\1",
                    content,
                )

                # Pattern 2: import domains.xxx
                content = re.sub(
                    r"import\s+domains\.(\w+)",
                    r"import modules.\1",
                    content,
                )

                # Pattern 3: from domains import
                content = re.sub(
                    r"from\s+domains\s+import",
                    r"from modules import",
                    content,
                )

                # Pattern 4: from .domains
                content = re.sub(
                    r"from\s+\.domains\.(\w+)",
                    r"from .modules.\1",
                    content,
                )

                # Only write if content changed
                if content != original_content:
                    py_file.write_text(content, encoding="utf-8")
                    # Count how many patterns were replaced
                    changes = len(re.findall(r"from modules\.|import modules\.", content))
                    updated_count += changes
                    self.log(
                        f"  → Updated imports in {py_file.relative_to(module_dir)}"
                    )

            except Exception as e:
                self.log(
                    f"  ⚠️  Error processing {py_file}: {str(e)}", "WARN"
                )

        return updated_count

    def verify_migration(self) -> bool:
        """
        Verify that migration was successful

        Checks:
          1. All 4 modules exist in destination
          2. No remaining 'domains' imports in migrated files
          3. All required files present
        """
        self.log("=" * 60)
        self.log("VERIFICATION PHASE", "INFO")
        self.log("=" * 60)

        all_valid = True

        for module_name in self.modules:
            dest_dir = self.dest_base / module_name

            # Check 1: Directory exists
            if not dest_dir.exists():
                self.log(f"❌ {module_name}: Directory not found", "ERROR")
                all_valid = False
                continue

            # Check 2: Required files exist
            required_files = [
                "domain.py",
                "service.py",
                "repository.py",
                "models.py",
                "schemas.py",
                "router.py",
                "exceptions.py",
                "__init__.py",
            ]

            missing = [f for f in required_files if not (dest_dir / f).exists()]

            if missing:
                self.log(
                    f"❌ {module_name}: Missing files: {', '.join(missing)}",
                    "ERROR",
                )
                all_valid = False
            else:
                self.log(f"✅ {module_name}: All required files present")

            # Check 3: No remaining 'domains' imports
            domains_imports = self.find_remaining_domains_imports(dest_dir)
            if domains_imports:
                self.log(
                    f"⚠️  {module_name}: Found {len(domains_imports)} remaining 'domains' imports",
                    "WARN",
                )
                for file_path in domains_imports[:3]:  # Show first 3
                    self.log(f"    → {file_path}")
                if len(domains_imports) > 3:
                    self.log(f"    → ... and {len(domains_imports) - 3} more")

        return all_valid

    def find_remaining_domains_imports(self, module_dir: Path) -> List[str]:
        """Find any remaining 'domains' imports"""
        remaining = []

        for py_file in module_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if re.search(r"(from|import)\s+domains", content):
                    remaining.append(str(py_file.relative_to(module_dir)))
            except Exception:
                pass

        return remaining

    def generate_report(self):
        """Generate and save migration report"""
        report_file = Path("migrate_report.txt")

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("WORDLOOM MODULE MIGRATION REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source:      backend/api/app/modules/domains/\n")
            f.write(f"Destination: backend/api/app/modules/\n")
            f.write(f"Modules:     {', '.join(self.modules)}\n")
            f.write("\n")

            if self.errors:
                f.write("ERRORS:\n")
                f.write("-" * 70 + "\n")
                for error in self.errors:
                    f.write(f"  ❌ {error}\n")
                f.write("\n")

            f.write("LOG:\n")
            f.write("-" * 70 + "\n")
            for log_line in self.report:
                f.write(f"{log_line}\n")

            f.write("\n")
            f.write("=" * 70 + "\n")
            f.write("NEXT STEPS:\n")
            f.write("=" * 70 + "\n")
            f.write("1. Review this report for any errors or warnings\n")
            f.write("2. Run: pytest backend/api/app/tests/ -v\n")
            f.write("3. Check for remaining 'domains' imports:\n")
            f.write("   grep -r 'from domains' backend/api/app/modules/\n")
            f.write("   grep -r 'import domains' backend/api/app/modules/\n")
            f.write("4. Update DDD_RULES.yaml filepath fields\n")
            f.write("5. Delete old modules/domains/ folder (optional)\n")
            f.write("6. Commit migration to git\n")

        self.log(f"✅ Report saved to: {report_file}")

    def run_migration(self) -> bool:
        """
        Execute complete migration workflow

        Steps:
          1. Migrate each module
          2. Verify success
          3. Generate report
          4. Return success status
        """
        self.log("=" * 60)
        self.log("WORDLOOM MODULE MIGRATION STARTING", "START")
        self.log("=" * 60)

        # Phase 1: Migrate each module
        self.log("")
        self.log("PHASE 1: MIGRATING MODULES", "INFO")
        self.log("=" * 60)

        migration_results = {}
        for module_name in self.modules:
            success = self.migrate_module(module_name)
            migration_results[module_name] = success
            self.log("")

        # Phase 2: Verify migration
        self.log("")
        all_valid = self.verify_migration()

        # Phase 3: Generate report
        self.log("")
        self.generate_report()

        # Final summary
        self.log("")
        self.log("=" * 60)
        successful = sum(1 for v in migration_results.values() if v)
        self.log(f"MIGRATION COMPLETE: {successful}/{len(self.modules)} modules successful")
        self.log("=" * 60)

        return all_valid and successful == len(self.modules)


def main():
    """Main entry point"""
    try:
        migrator = ModuleMigrator()
        success = migrator.run_migration()

        if success:
            print("\n" + "=" * 60)
            print("✅ MIGRATION SUCCESSFUL!")
            print("=" * 60)
            print("\n📋 Next steps:")
            print("  1. Review migrate_report.txt")
            print("  2. Run pytest to verify tests pass")
            print("  3. Check for remaining 'domains' imports")
            print("  4. Update DDD_RULES.yaml")
            print("  5. Delete backend/api/app/modules/domains/ folder")
            print("\n")
            return 0
        else:
            print("\n" + "=" * 60)
            print("❌ MIGRATION COMPLETED WITH ERRORS")
            print("=" * 60)
            print("\n⚠️  Please review migrate_report.txt for details\n")
            return 1

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}\n")
        return 2


if __name__ == "__main__":
    exit(main())
