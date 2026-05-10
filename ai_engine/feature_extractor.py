def extract_features(row):
    """
    Extrae características de una fila del dataset para análisis o ML.
    'row' es una fila del DataFrame (df.iloc[i])
    """
    # Intentamos obtener la extensión del archivo desde la descripción 
    # o asignar una por defecto si no existe el campo 'file_name'
    try:
        # Si tienes una columna de nombre de archivo o ruta:
        file_ext = row['project_name'].split('.')[-1] 
    except:
        file_ext = "unknown"

    return {
        "project": row["project_name"],
        "framework": row["compliance_framework"],
        "scan_type": row["scan_type"],
        "file_type": file_ext,
        "issue_count": row["issues_found"],
        "critical_issues": row["critical"],
        "risk_score": row["score"],
        "ethics_score": row["ethics_compliance_score"]
    }

# --- Ejemplo de uso con el DataFrame generado ---
# features = extract_features(df.iloc[0])
# print(features)