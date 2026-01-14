"""
Script para verificar el cálculo de predictabilidad antes de modificar.
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

# Convertir Estimación Original a numérico
df['Estimación Original'] = pd.to_numeric(df['Estimación Original'], errors='coerce')
df['Puntos Logrados'] = pd.to_numeric(df['Puntos Logrados'], errors='coerce')

# Identificar tareas en DoD
df['Is_DoD'] = df['Estado'].isin(DELIVERY_STATES_PRODUCTIVE)

print("=" * 80)
print("ANÁLISIS DE PREDICTABILIDAD - PUNTOS ESTIMADOS QUE ALCANZARON DoD")
print("=" * 80)
print()
print("Estados DoD: 11. Ready for Product Release, 12. Validación a Producción, 13. Producción")
print()

# Filtrar filas con Sprint válido
df = df[df['Sprint'].notna()]

# Análisis por sprint
sprints = sorted(df['Sprint'].dropna().unique(), key=lambda x: int(str(x).split()[-1]) if 'Sprint' in str(x) else 0)

print("=" * 80)
print("DETALLE POR SPRINT")
print("=" * 80)
print()

total_committed_all = 0
total_delivered_all = 0

for sprint in sprints:
    sprint_data = df[df['Sprint'] == sprint]
    dod_tasks = sprint_data[sprint_data['Is_DoD']]

    # Puntos comprometidos: TODAS las tareas del sprint
    committed_points = sprint_data['Estimación Original'].sum()

    # Puntos entregados (DoD): Solo tareas que alcanzaron DoD
    delivered_points = dod_tasks['Estimación Original'].sum()

    # Predictabilidad
    predictability = (delivered_points / committed_points * 100) if committed_points > 0 else 0

    total_committed_all += committed_points
    total_delivered_all += delivered_points

    print(f"{sprint}")
    print(f"  Total tareas en sprint: {len(sprint_data)}")
    print(f"  Tareas que alcanzaron DoD: {len(dod_tasks)}")
    print(f"  Puntos comprometidos (Estimación Original de TODAS las tareas): {committed_points:.1f}")
    print(f"  Puntos entregados (Estimación Original de tareas en DoD): {delivered_points:.1f}")
    print(f"  Predictabilidad calculada: {predictability:.1f}%")

    # Desglose por estado DoD
    if len(dod_tasks) > 0:
        print(f"  Desglose por estado DoD:")
        for estado in sorted(dod_tasks['Estado'].unique()):
            estado_tasks = dod_tasks[dod_tasks['Estado'] == estado]
            estado_points = estado_tasks['Estimación Original'].sum()
            print(f"    - {estado}: {len(estado_tasks)} tareas, {estado_points:.1f} puntos")

    print()

print("=" * 80)
print("RESUMEN GENERAL")
print("=" * 80)
print(f"Total puntos comprometidos (todos los sprints): {total_committed_all:.1f}")
print(f"Total puntos entregados en DoD (todos los sprints): {total_delivered_all:.1f}")
print(f"Predictabilidad global: {(total_delivered_all / total_committed_all * 100):.1f}%")
print()

# Comparación con Puntos Logrados
print("=" * 80)
print("COMPARACIÓN: ESTIMACIÓN ORIGINAL vs PUNTOS LOGRADOS (tareas en DoD)")
print("=" * 80)
print()

for sprint in sprints:
    sprint_data = df[df['Sprint'] == sprint]
    dod_tasks = sprint_data[sprint_data['Is_DoD']]

    if len(dod_tasks) > 0:
        delivered_estimation = dod_tasks['Estimación Original'].sum()
        delivered_achieved = dod_tasks['Puntos Logrados'].sum()

        print(f"{sprint}")
        print(f"  Puntos de Estimación Original (tareas DoD): {delivered_estimation:.1f}")
        print(f"  Puntos Logrados (tareas DoD): {delivered_achieved:.1f}")
        print(f"  Diferencia: {(delivered_achieved - delivered_estimation):.1f}")
        print()
