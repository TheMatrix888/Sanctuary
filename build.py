"""
Sanctuary Executable Builder.
Compiles the standalone single-file binary using PyInstaller,
routing all caches, specifications, and binaries into .pyinstaller/
to keep the repository root pristine.
"""
import subprocess
import sys
from pathlib import Path


def build() -> int:
    project_root = Path(__file__).resolve().parent
    icon_path = project_root / "resources" / "icons" / "shiro.ico"
    resources_dir = project_root / "resources"
    output_dir = project_root / ".pyinstaller"
    dist_dir = output_dir / "dist"
    build_dir = output_dir / "build"
    main_script = project_root / "main.py"

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 64)
    print("  Sanctuary // Shiro Engine -- PyInstaller Builder")
    print("=" * 64)
    print(f"  Project root   : {project_root}")
    print(f"  Build output   : {dist_dir}")
    print(f"  Main script    : {main_script}")
    print(f"  Window icon    : {icon_path}")
    print("=" * 64)

    # Ensure isolated output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve active python interpreter (venv or system)
    python_exe = sys.executable

    # PyInstaller execution arguments
    cmd = [
        python_exe,
        "-m",
        "PyInstaller",
        "--name",
        "Sanctuary",
        "--icon",
        str(icon_path),
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        "--specpath",
        str(output_dir),
        "--add-data",
        f"{resources_dir};resources",
        "--clean",
        "--onefile",
        str(main_script),
    ]

    print("\n[+] Launching PyInstaller...")
    result = subprocess.run(cmd, cwd=project_root)

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if result.returncode == 0:
        exe_path = dist_dir / "Sanctuary.exe"
        size_mb = exe_path.stat().st_size / (1024 * 1024) if exe_path.exists() else 0.0
        print("\n" + "=" * 64)
        print("  BUILD SUCCESSFUL! [OK]")
        print(f"  Binary: {exe_path} ({size_mb:.1f} MB)")
        print("=" * 64)
    else:
        print("\n" + "=" * 64)
        print(f"  BUILD FAILED with exit code {result.returncode}")
        print("=" * 64)

    return result.returncode


if __name__ == "__main__":
    sys.exit(build())
