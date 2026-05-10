import os
import zipfile
import tempfile
import shutil

ALLOWED_EXTENSIONS = (
    ".py", ".js", ".json", ".java", ".cpp", ".c",
    ".txt", ".md", ".php", ".html", ".css"
)

MAX_FILE_SIZE_MB = 50


# -----------------------------------
# File validation
# -----------------------------------
def is_allowed_file(filename):
    return filename.lower().endswith(ALLOWED_EXTENSIONS)


def validate_file(file_path):
    """
    Validate size + extension
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return False, "File exceeds 50MB limit"

    if not is_allowed_file(file_path):
        return False, "Unsupported file type"

    return True, "OK"


# -----------------------------------
# ZIP Extraction
# -----------------------------------
def extract_zip(file_path):
    """
    Extract ZIP to temp directory
    """
    temp_dir = tempfile.mkdtemp(prefix="escc_")

    try:
        with zipfile.ZipFile(file_path, "r") as z:
            z.extractall(temp_dir)
    except zipfile.BadZipFile:
        shutil.rmtree(temp_dir)
        raise ValueError("Invalid ZIP file")

    return temp_dir


# -----------------------------------
# Collect analyzable files
# -----------------------------------
def collect_files(base_path):
    """
    Recursively collect allowed files
    """
    files = []
    for root, _, filenames in os.walk(base_path):
        for name in filenames:
            if is_allowed_file(name):
                files.append(os.path.join(root, name))
    return files


# -----------------------------------
# Cleanup helper
# -----------------------------------
def cleanup_temp(path):
    """
    Safely remove temp folders
    """
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
    except Exception:
        pass


# -----------------------------------
# Scan mode helper
# -----------------------------------
def normalize_scan_type(scan_type):
    """
    Frontend se aane wale scan_type ko sanitize kare
    """
    if scan_type not in ["standard", "deep"]:
        return "standard"
    return scan_type


# -----------------------------------
# Preference resolver
# -----------------------------------
def resolve_preferences(prefs):
    """
    Preferences ko normalize kare
    """
    return {
        "ethical": bool(prefs.get("ethical", True)),
        "security": bool(prefs.get("security", True)),
        "performance": bool(prefs.get("performance", False))
    }


# -----------------------------------
# Score aggregation (Multiple files)
# -----------------------------------
def aggregate_results(results):
    """
    Multiple files ke scores ko aggregate kare
    """
    if not results:
        return {
            "ethical_score": 0,
            "security_score": 0,
            "files_scanned": 0,
            "issues": {}
        }

    ethical_avg = sum(r["ethical_score"] for r in results) / len(results)
    security_avg = sum(r["security_score"] for r in results) / len(results)

    total_issues = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for r in results:
        for k in total_issues:
            total_issues[k] += r["issues"].get(k, 0)

    return {
        "ethical_score": round(ethical_avg, 2),
        "security_score": round(security_avg, 2),
        "files_scanned": len(results),
        "issues": total_issues
    }
