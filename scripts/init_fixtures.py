"""
Complete prototype initialization script.
Generates all keys, credentials, and necessary files.
"""

import sys
import subprocess
from pathlib import Path


def run_script(script_name: str, base_dir: Path) -> None:
    """
    Executes a Python script and handles errors.
    
    Args:
        script_name: Name of script to execute (relative to scripts/)
        base_dir: Project base directory
    """
    script_path = base_dir / "scripts" / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=base_dir,
        check=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)


def main() -> None:
    """Main initialization function."""
    base_dir = Path(__file__).parent.parent
    fixtures_dir = base_dir / "fixtures"
    
    # Create necessary directories
    (fixtures_dir / "keys").mkdir(parents=True, exist_ok=True)
    (fixtures_dir / "requests").mkdir(parents=True, exist_ok=True)
    (fixtures_dir / "status").mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("COMPLETE PROTOTYPE INITIALIZATION")
    print("=" * 60)
    
    steps = [
        ("Generating Ed25519 keys", "generate_keys.py"),
        ("Building JWKS", "build_jwks.py"),
        ("Generating VC-JWT", "mint_vc_jwt.py"),
        ("Generating delegation chains", "mint_sdjwt_dg.py"),
        ("Generating negative test cases", "mint_negative_cases.py"),
        ("Generating DG-LD", "mint_dg_ld.py"),
    ]
    
    for step_name, script_name in steps:
        print(f"\n[STEP] {step_name}...")
        try:
            run_script(script_name, base_dir)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Error in {step_name}: {e.stderr}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Error in {step_name}: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[OK] INITIALIZATION COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Start server: python scripts/start_server.py")
    print("3. Run tests: python scripts/tests/test_all_scenarios.py --include-blockchain")
    print("4. See README.md for detailed usage instructions")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInitialization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)
