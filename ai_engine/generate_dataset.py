import pandas as pd
import random
from datetime import datetime, timedelta
import json

# -----------------------------
# 1️⃣ Load real CVE data from NVD (JSON)
# -----------------------------
with open("nvdcve/nvd_cve.json", "r", encoding="utf-8") as f:
    nvd_data = json.load(f)

cve_items = nvd_data.get("vulnerabilities", [])

# -----------------------------
# 2️⃣ Generate projects list
# -----------------------------
projects = [
    "openssl", "django", "flask", "react", "tensorflow", "pytorch",
    "angular", "vue", "kubernetes", "ansible", "git", "node", "laravel",
    "spring", "rails", "electron", "docker", "mongodb", "postgresql", "nginx"
]

# -----------------------------
# 3️⃣ Build dataset
# -----------------------------
rows = []
for idx, item in enumerate(cve_items):
    if idx >= 20000:  # Limit dataset to 20k rows
        break

    cve_details = item.get("cve", {})
    project_name = random.choice(projects)
    
    # Extract English description
    descriptions = cve_details.get("descriptions", [])
    description = next((d["value"] for d in descriptions if d["lang"] == "en"), "No description available")

    # Extract CVSS score
    metrics = cve_details.get("metrics", {})
    score = None
    for version in ["cvssMetricV31", "cvssMetricV30"]:
        if version in metrics and metrics[version]:
            score = float(metrics[version][0]["cvssData"]["baseScore"])
            break
    if score is None:
        score = round(random.uniform(4, 9), 1)

    # Severity
    critical = 1 if score >= 9 else 0
    high = 1 if 7 <= score < 9 else 0
    medium = 1 if 4 <= score < 7 else 0
    low = 1 if score < 4 else 0

    # Project metrics
    file_count = random.randint(50, 500)
    lines_of_code = file_count * random.randint(50, 300)
    dependencies_count = random.randint(0, 50)

    # Compliance & scan info
    compliance_framework = random.choice(["ISO 27001", "NIST", "GDPR", "SOC2", "HIPAA"])
    scan_type = random.choice(["Static", "Dynamic", "Dependency"])
    scan_date = (datetime.today() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    ethics_compliance_score = max(0, round(100 - (critical*15 + high*10 + medium*5 + low*2), 2))

    # Historical & recommendations
    previous_scores = json.dumps([round(ethics_compliance_score - random.uniform(0,5),2) for _ in range(3)])
    recommendations = json.dumps([
        {"text":"Update vulnerable dependency X"},
        {"text":"Refactor module Y to improve security"}
    ])
    ethical_flags = json.dumps([
        {"collects_personal_data": bool(random.getrandbits(1))},
        {"tracking_enabled": bool(random.getrandbits(1))}
    ])

    # -----------------------------
    # 4️⃣ Generate HIPAA / PII / SOC2 flags
    # -----------------------------
    hipaa_flag = 1 if "hipaa" in compliance_framework.lower() else 0
    pii_flag = random.choice([0,1]) if hipaa_flag else 0  # assume PII mostly with HIPAA
    soc2_flag = 1 if "soc2" in compliance_framework.lower() else 0

    rows.append([
        project_name, description, compliance_framework, scan_type, scan_date,
        file_count, lines_of_code, dependencies_count,
        critical+high+medium+low, critical, high, medium, low, score,
        previous_scores, recommendations, ethical_flags, ethics_compliance_score,
        hipaa_flag, pii_flag, soc2_flag
    ])

# -----------------------------
# 5️⃣ Create DataFrame & Save CSV
# -----------------------------
df = pd.DataFrame(rows, columns=[
    "project_name","description","compliance_framework","scan_type","scan_date",
    "file_count","lines_of_code","dependencies_count","issues_found",
    "critical","high","medium","low","score",
    "previous_scores","recommendations","ethical_flags","ethics_compliance_score",
    "hipaa_flag","pii_flag","soc2_flag"
])

df.to_csv("ethical_compliance_dataset.csv", index=False)
print(f"✅ Dataset generado con {len(df)} filas con HIPAA/PII/SOC2 flags.")
