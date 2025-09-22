

import re, pandas as pd

df = pd.read_csv("output/bumeran_data.csv")

print("=== SHAPE ===")
print(df.shape)

print("\n=== COLUMNAS ===")
print(list(df.columns))

required = ["Job Title","Description","District","Work Mode","url"]
missing = [c for c in required if c not in df.columns]
print("\nFaltan columnas:", missing)

bad_domain = df[~df["url"].str.contains(r"^https?://www\.bumeran\.com\.pe/empleos/.*\.html$", na=False)]
print("\nLinks con dominio/formato inesperado:", len(bad_domain))

print("\nNulos por columna:")
print(df[required].isna().sum())

tiene_benef = df["Description"].str.contains(r"Beneficios|Benefits", case=False, na=False)
print("\nDescriptions que AÚN contienen 'Beneficios' (deberían ser 0):", tiene_benef.sum())

print("\n% filas con District no vacío:", (df["District"].astype(str).str.len()>0).mean().round(3))
print("% filas con Work Mode no vacío:", (df["Work Mode"].astype(str).str.len()>0).mean().round(3))

print("\nMuestra:")
print(df.head(3).to_string(index=False))
