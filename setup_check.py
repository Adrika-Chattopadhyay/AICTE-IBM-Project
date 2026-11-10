"""
Fitness Buddy — Setup Verification Script
Run this to check all dependencies and configuration.
"""

import sys
import os


def check(label: str, passed: bool, detail: str = ""):
    icon = "[OK]  " if passed else "[FAIL]"
    msg = f"{icon} {label}"
    if detail:
        msg += f" - {detail}"
    print(msg)
    return passed


def main():
    print("\n" + "=" * 60)
    print("  Fitness Buddy - Setup Verification")
    print("=" * 60 + "\n")

    all_ok = True

    # Python version
    ok = sys.version_info >= (3, 9)
    all_ok &= check("Python version", ok, f"Python {sys.version_info.major}.{sys.version_info.minor}")

    # Required packages
    packages = [
        ("streamlit", "streamlit"),
        ("dotenv", "python-dotenv"),
        ("requests", "requests"),
        ("pandas", "pandas"),
        ("plotly", "plotly"),
        ("pydantic", "pydantic"),
    ]

    for module, package in packages:
        try:
            __import__(module)
            all_ok &= check(f"Package: {package}", True)
        except ImportError:
            all_ok &= check(f"Package: {package}", False, f"Run: pip install {package}")

    # IBM watsonx.ai (optional for demo mode)
    try:
        import ibm_watsonx_ai
        check("IBM watsonx.ai SDK", True, "Live AI available")
    except ImportError:
        check("IBM watsonx.ai SDK", False, "Run: pip install ibm-watsonx-ai (optional — demo mode works without)")

    # .env file
    env_exists = os.path.exists(".env")
    all_ok &= check(".env file", env_exists, "Created" if env_exists else "Copy env.example to .env")

    # IBM credentials
    if env_exists:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("IBM_API_KEY", "")
        project_id = os.getenv("IBM_PROJECT_ID", "")
        configured = (
            api_key and api_key != "your_ibm_api_key_here"
            and project_id and project_id != "your_watsonx_project_id_here"
        )
        check(
            "IBM credentials configured",
            configured,
            "Live AI active" if configured else "Demo mode (add real keys to .env for live AI)",
        )

    # Local modules
    for module in ["granite_client", "guardrails", "features", "progress_store"]:
        exists = os.path.exists(f"{module}.py")
        all_ok &= check(f"Module: {module}.py", exists)

    print("\n" + "=" * 60)
    if all_ok:
        print("[OK] All checks passed! Run: streamlit run app.py")
    else:
        print("[!!] Some checks failed. See above for fixes.")
        print("     The app will still run in demo mode.")
    print("=" * 60 + "\n")

    print("To start the app:")
    print("   streamlit run app.py\n")
    print("IBM Cloud setup:")
    print("   1. Sign up at https://cloud.ibm.com (free)")
    print("   2. Create a watsonx.ai project")
    print("   3. Generate an API key")
    print("   4. Add credentials to .env\n")


if __name__ == "__main__":
    main()
