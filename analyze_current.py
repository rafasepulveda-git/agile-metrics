"""
Script para analizar el archivo de ejemplo con el código actual.
"""
import pandas as pd
import sys
sys.path.insert(0, 'C:\\Proyectos\\agile-metrics')

# Leer el archivo Excel
file_path = r'C:\Proyectos\agile-metrics\Backlog_Planning_No_paquetizado_All_Tasks_1768419897.xlsx'
df_raw = pd.read_excel(file_path, header=1)

# La primera fila contiene los nombres reales de las columnas
new_columns = df_raw.iloc[0].tolist()
df = df_raw.iloc[1:].copy()
df.columns = new_columns
df.reset_index(drop=True, inplace=True)

print("=" * 80)
print("ESTRUCTURA DEL ARCHIVO")
print("=" * 80)
print(f"\nDimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
print(f"\nColumnas disponibles:")
for col in df.columns:
    print(f"  - {col}")

print("\n" + "=" * 80)
print("PRIMERAS 10 FILAS")
print("=" * 80)
print(df.head(10).to_string())

print("\n" + "=" * 80)
print("VALORES ÚNICOS EN COLUMNAS CLAVE")
print("=" * 80)

# Mostrar valores únicos de columnas importantes
important_cols = ['Estado', 'Tipo Tarea', 'Sprint', 'Sprint Completed?']
for col in important_cols:
    if col in df.columns:
        unique_vals = df[col].dropna().unique()
        print(f"\n{col} ({len(unique_vals)} valores únicos):")
        for val in sorted(unique_vals, key=str):
            count = (df[col] == val).sum()
            print(f"  - {val}: {count} tareas")

print("\n" + "=" * 80)
print("RESUMEN DE DATOS NUMÉRICOS")
print("=" * 80)
numeric_cols = ['Estimación Original', 'Puntos Logrados']
for col in numeric_cols:
    if col in df.columns:
        print(f"\n{col}:")
        print(f"  - Total: {df[col].sum()}")
        print(f"  - Promedio: {df[col].mean():.2f}")
        print(f"  - Valores no nulos: {df[col].notna().sum()}/{len(df)}")
