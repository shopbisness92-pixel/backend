import os
import sys
import json
import re

try:
    import joblib
    import numpy as np
    HAS_ML = True
except ImportError:
    HAS_ML = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model_escc.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "encoders.pkl")

# -----------------------------
# Static + Rule Based Scan
# -----------------------------
def scan_file_for_issues(file_path):
    critical = high = medium = 0
    loc = 0
    findings = []
    has_hipaa = has_pii = has_soc2 = 0

    try:
        if not os.path.exists(file_path):
            return 0, 0, 0, 0, [], 0, 0, 0

        # File ka naam extract karein (e.g., "views.py")
        file_name = os.path.basename(file_path)

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines() # Saari lines list mein le lein
            loc = len(lines)

            # Ab har line ko index ke saath scan karein
            for idx, line in enumerate(lines):
                line_no = idx + 1  # 1-based indexing ke liye
                
                # --- CRITICAL ---
                # Hardcoded Secret
                if re.search(r'(password|api_key|token)\s*[:=]', line, re.I):
                    critical += 1
                    findings.append({
                        "severity": "Critical", 
                        "type": "Hardcoded Secret",
                        "line": line_no, 
                        "file": file_name,
                        "message": f"Sensitive key/password found on line {line_no}"
                    })

                # RCE Risk
                if any(x in line for x in ["eval(", "exec(", "os.system("]):
                    critical += 1
                    findings.append({
                        "severity": "Critical", 
                        "type": "RCE Risk",
                        "line": line_no,
                        "file": file_name,
                        "message": "Potentially dangerous function execution detected."
                    })

                # --- HIGH ---
                # Insecure Protocol
                if "http://" in line and "localhost" not in line:
                    high += 1
                    findings.append({
                        "severity": "High", 
                        "type": "Insecure Protocol",
                        "line": line_no,
                        "file": file_name,
                        "message": "Insecure HTTP protocol used."
                    })

                # PII Detection (Email)
                if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', line):
                    high += 1
                    has_pii = 1
                    findings.append({
                        "severity": "High", 
                        "type": "PII Detected",
                        "line": line_no,
                        "file": file_name,
                        "message": "Personally Identifiable Information (Email) found."
                    })

                # HIPAA
                hipaa_words = ["hipaa", "phi", "medical record", "diagnosis", "mrn"]
                if any(w in line.lower() for w in hipaa_words):
                    high += 1
                    has_hipaa = 1
                    findings.append({
                        "severity": "High", 
                        "type": "HIPAA Sensitive Data",
                        "line": line_no,
                        "file": file_name,
                        "message": "HIPAA related health data keyword detected."
                    })

                # SOC2
                soc2_words = ["soc2", "security controls", "confidentiality", "privacy"]
                if any(w in line.lower() for w in soc2_words):
                    high += 1
                    has_soc2 = 1
                    findings.append({
                        "severity": "High", 
                        "type": "SOC2 Compliance Related",
                        "line": line_no,
                        "file": file_name,
                        "message": "Compliance-related keyword detected."
                    })

                # --- MEDIUM ---
                if "TODO" in line:
                    medium += 1
                    findings.append({
                        "severity": "Medium", 
                        "type": "Technical Debt",
                        "line": line_no,
                        "file": file_name,
                        "message": "Unfinished task (TODO) found."
                    })

    except Exception as e:
        # Debugging ke liye aap isse print kar sakte hain
        pass

    return critical, high, medium, loc, findings, has_hipaa, has_pii, has_soc2
# -----------------------------
# ML Feature Builder
# -----------------------------
def extract_ml_features(loc, critical, high, medium, has_hipaa, has_pii, has_soc2):
    total = critical + high + medium
    compliance_score = has_hipaa + has_pii + has_soc2
    return np.array([[loc, critical, high, medium, has_hipaa, has_pii, has_soc2, total, compliance_score]])


# -----------------------------
# Main Analysis
# -----------------------------
def run_analysis(file_path):

    critical, high, medium, loc, vulns, has_hipaa, has_pii, has_soc2 = scan_file_for_issues(file_path)
    total_issues = critical + high + medium

    base_score = 100
    penalty = (critical * 25) + (high * 15) + (medium * 5)
    static_score = max(5, base_score - penalty)

    final_score = static_score

    # -----------------------------
    # ML Risk Adjustment
    # -----------------------------
    if HAS_ML and os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)

            X = extract_ml_features(
                loc, critical, high, medium, has_hipaa, has_pii, has_soc2
            )

            ml_risk = model.predict(X)[0]

            # Combine Rule + ML
            final_score = round((static_score * 0.5) + (ml_risk * 0.5), 2)

        except:
            pass

    return {
        "ethical_score": float(final_score),
        "security_score": float(max(5, final_score - (critical * 3))),
        "vulnerabilities": vulns,
        "details": {
            "critical": critical,
            "high": high,
            "medium": medium,
            "total_issues": total_issues,
            "lines_analyzed": loc,
            "hipaa_flag": bool(has_hipaa),
            "pii_flag": bool(has_pii),
            "soc2_flag": bool(has_soc2)  # NEW
        }
    }


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            result = run_analysis(sys.argv[1])
            sys.stdout.write(json.dumps(result))
        else:
            sys.stdout.write(json.dumps({"error": "No file path"}))
    except Exception as e:
        sys.stdout.write(json.dumps({"error": str(e)}))
