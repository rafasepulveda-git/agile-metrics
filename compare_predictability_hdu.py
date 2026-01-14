"""
Script para comparar predictabilidad: todas las tareas vs solo HDU.
"""
import pandas as pd
import sys
sys.path.insert(0, 'C:\\Proyectos\\agile-metrics\\metrics_analyzer')

from config import DELIVERY_STATES_PRODUCTIVE

# Configuración
file_path = r'C:\Proyectos\agile-metrics\Backlog_Planning_No_paquetizado_All_Tasks_1768419897.xlsx'

# Leer archivo
df_raw = pd.read_excel(file_path, header=1)
new_columns = df_raw.iloc[0].tolist()
df = df_raw.iloc[1:].copy()

# Manejar columnas duplicadas
cols = pd.Series(new_columns)
for dup in cols[cols.duplicated()].unique():
    dup_indices = [i for i, x in enumerate(new_columns) if x == dup]
    for i, idx in enumerate(dup_indices):
        if i > 0:
            new_columns[idx] = f"{dup}_{i}"

df.columns = new_columns
df.reset_index(drop=True, inplace=True)

# Convertir columnas numéricas
df['Estimación Original'] = pd.to_numeric(df['Estimación Original'], errors='coerce')
df['Puntos Logrados'] = pd.to_numeric(df['Puntos Logrados'], errors='coerce')

# Identificar tareas en DoD
df['Is_DoD'] = df['Estado'].isin(DELIVERY_STATES_PRODUCTIVE)

# Filtrar filas con Sprint válido
df = df[df['Sprint'].notna()]

# Análisis por sprint
sprints = sorted(df['Sprint'].dropna().unique(), key=lambda x: int(str(x).split()[-1]) if 'Sprint' in str(x) else 0)

print("=" * 80)
print("COMPARATIVA DE PREDICTABILIDAD: TODAS LAS TAREAS vs SOLO HDU")
print("=" * 80)
print()

# Tabla comparativa
results = []

for sprint in sprints:
    sprint_data = df[df['Sprint'] == sprint]
    sprint_hdu = sprint_data[sprint_data['Tipo Tarea'] == 'HDU']

    # === TODAS LAS TAREAS ===
    dod_all = sprint_data[sprint_data['Is_DoD']]
    committed_all = sprint_data['Estimación Original'].sum()
    delivered_all = dod_all['Estimación Original'].sum()
    pred_all = (delivered_all / committed_all * 100) if committed_all > 0 else 0

    # === SOLO HDU ===
    dod_hdu = sprint_hdu[sprint_hdu['Is_DoD']]
    committed_hdu = sprint_hdu['Estimación Original'].sum()
    delivered_hdu = dod_hdu['Estimación Original'].sum()
    pred_hdu = (delivered_hdu / committed_hdu * 100) if committed_hdu > 0 else 0

    # === DIFERENCIA ===
    diff = pred_hdu - pred_all

    results.append({
        'Sprint': sprint,
        'Total_Tasks_All': len(sprint_data),
        'DoD_Tasks_All': len(dod_all),
        'Committed_All': committed_all,
        'Delivered_All': delivered_all,
        'Pred_All': pred_all,
        'Total_Tasks_HDU': len(sprint_hdu),
        'DoD_Tasks_HDU': len(dod_hdu),
        'Committed_HDU': committed_hdu,
        'Delivered_HDU': delivered_hdu,
        'Pred_HDU': pred_hdu,
        'Diff': diff
    })

# Mostrar resultados
print("DETALLE POR SPRINT:")
print()

for r in results:
    print(f"{'-' * 80}")
    print(f"{r['Sprint']}")
    print(f"{'-' * 80}")
    print()

    print("  TODAS LAS TAREAS (HDU + Bug + Solicitud):")
    print(f"    Total tareas: {r['Total_Tasks_All']}")
    print(f"    Tareas en DoD: {r['DoD_Tasks_All']}")
    print(f"    Puntos comprometidos: {r['Committed_All']:.1f}")
    print(f"    Puntos entregados: {r['Delivered_All']:.1f}")
    print(f"    Predictabilidad: {r['Pred_All']:.1f}%")
    print()

    print("  SOLO TAREAS HDU:")
    print(f"    Total tareas HDU: {r['Total_Tasks_HDU']}")
    print(f"    Tareas HDU en DoD: {r['DoD_Tasks_HDU']}")
    print(f"    Puntos comprometidos (HDU): {r['Committed_HDU']:.1f}")
    print(f"    Puntos entregados (HDU): {r['Delivered_HDU']:.1f}")
    print(f"    Predictabilidad (HDU): {r['Pred_HDU']:.1f}%")
    print()

    print(f"  DIFERENCIA: {r['Diff']:+.1f}% {'(HDU mejor)' if r['Diff'] > 0 else '(HDU peor)' if r['Diff'] < 0 else '(igual)'}")
    print()

# Resumen en tabla
print("=" * 80)
print("TABLA RESUMEN")
print("=" * 80)
print()

print(f"{'Sprint':<12} {'Pred All':<12} {'Pred HDU':<12} {'Diferencia':<15} {'Comentario'}")
print("-" * 80)
for r in results:
    comentario = "HDU mejor" if r['Diff'] > 5 else "HDU peor" if r['Diff'] < -5 else "Similar"
    print(f"{r['Sprint']:<12} {r['Pred_All']:>6.1f}%     {r['Pred_HDU']:>6.1f}%     {r['Diff']:>+6.1f}%         {comentario}")

# Totales globales
total_committed_all = sum(r['Committed_All'] for r in results)
total_delivered_all = sum(r['Delivered_All'] for r in results)
pred_global_all = (total_delivered_all / total_committed_all * 100) if total_committed_all > 0 else 0

total_committed_hdu = sum(r['Committed_HDU'] for r in results)
total_delivered_hdu = sum(r['Delivered_HDU'] for r in results)
pred_global_hdu = (total_delivered_hdu / total_committed_hdu * 100) if total_committed_hdu > 0 else 0

diff_global = pred_global_hdu - pred_global_all

print()
print("=" * 80)
print("TOTALES GLOBALES")
print("=" * 80)
print()
print("TODAS LAS TAREAS:")
print(f"  Total puntos comprometidos: {total_committed_all:.1f}")
print(f"  Total puntos entregados: {total_delivered_all:.1f}")
print(f"  Predictabilidad global: {pred_global_all:.1f}%")
print()
print("SOLO HDU:")
print(f"  Total puntos comprometidos (HDU): {total_committed_hdu:.1f}")
print(f"  Total puntos entregados (HDU): {total_delivered_hdu:.1f}")
print(f"  Predictabilidad global (HDU): {pred_global_hdu:.1f}%")
print()
print(f"DIFERENCIA GLOBAL: {diff_global:+.1f}% {'(HDU mejor)' if diff_global > 0 else '(HDU peor)' if diff_global < 0 else '(igual)'}")
print()

# Análisis adicional
print("=" * 80)
print("ANÁLISIS ADICIONAL")
print("=" * 80)
print()

# Sprints donde HDU es significativamente mejor/peor
mejor = [r for r in results if r['Diff'] > 10]
peor = [r for r in results if r['Diff'] < -10]
similar = [r for r in results if -10 <= r['Diff'] <= 10]

print(f"Sprints donde HDU tiene MEJOR predictabilidad (+10% o más): {len(mejor)}")
for r in mejor:
    print(f"  - {r['Sprint']}: {r['Pred_HDU']:.1f}% vs {r['Pred_All']:.1f}% (diferencia: {r['Diff']:+.1f}%)")

print()
print(f"Sprints donde HDU tiene PEOR predictabilidad (-10% o menos): {len(peor)}")
for r in peor:
    print(f"  - {r['Sprint']}: {r['Pred_HDU']:.1f}% vs {r['Pred_All']:.1f}% (diferencia: {r['Diff']:+.1f}%)")

print()
print(f"Sprints donde HDU tiene predictabilidad SIMILAR (-10% a +10%): {len(similar)}")
for r in similar:
    print(f"  - {r['Sprint']}: {r['Pred_HDU']:.1f}% vs {r['Pred_All']:.1f}% (diferencia: {r['Diff']:+.1f}%)")
