"""
Script para analizar el archivo de ejemplo con el código actual
y mostrar los resultados antes de modificar el código.
"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, 'C:\\Proyectos\\agile-metrics\\metrics_analyzer')

from data_loader import DataLoader
from data_processor import DataProcessor
from metrics_calculator import MetricsCalculator

# Configuración
file_path = r'C:\Proyectos\agile-metrics\Backlog_Planning_No_paquetizado_All_Tasks_1768419897.xlsx'
team_type = 'Productivo'
team_size = 6

# Mapeo de sprints a meses (2 sprints por mes, agosto a diciembre)
sprint_mapping = {
    'Sprint 3': 'Agosto',
    'Sprint 4': 'Agosto',
    'Sprint 5': 'Septiembre',
    'Sprint 6': 'Septiembre',
    'Sprint 7': 'Octubre',
    'Sprint 8': 'Octubre',
    'Sprint 9': 'Noviembre',
    'Sprint 10': 'Noviembre',
    'Sprint 11': 'Diciembre',
    'Sprint 12': 'Diciembre'
}

print("=" * 80)
print("ANÁLISIS CON CÓDIGO ACTUAL")
print("=" * 80)
print(f"Tipo de equipo: {team_type}")
print(f"Tamaño del equipo: {team_size} personas")
print(f"Estados DoD (Productivo): 11. Ready for Product Release, 12. Validación a Producción, 13. Producción")
print()

# Leer archivo (manejo especial para el formato de Monday)
df_raw = pd.read_excel(file_path, header=1)
new_columns = df_raw.iloc[0].tolist()
df = df_raw.iloc[1:].copy()

# Manejar columnas duplicadas: agregar sufijos
cols = pd.Series(new_columns)
for dup in cols[cols.duplicated()].unique():
    dup_indices = [i for i, x in enumerate(new_columns) if x == dup]
    for i, idx in enumerate(dup_indices):
        if i > 0:  # Mantener la primera sin sufijo
            new_columns[idx] = f"{dup}_{i}"

df.columns = new_columns
df.reset_index(drop=True, inplace=True)

# Verificar columnas
print("Columnas después de limpiar duplicados:")
for col in df.columns:
    print(f"  - {col}")
print()

# Agregar columna "Sprint Completed?" = 'v' para todos (asumir completados)
df['Sprint Completed?'] = 'v'

# Determinar qué columna de fecha usar
date_cols = ['Fecha Término', 'Fecha Ready for Production', 'Fecha paso a Producción']
delivery_date_column = 'Fecha Término'  # Por defecto
for col in date_cols:
    if col in df.columns and df[col].notna().sum() > 0:
        delivery_date_column = col
        break

print(f"Columna de fecha usada para Cycle Time: {delivery_date_column}")
print()

try:
    # Procesar datos
    processor = DataProcessor(
        df,
        team_type=team_type,
        sprint_mapping=sprint_mapping,
        delivery_date_column=delivery_date_column
    )
    processed_df = processor.process()

    print("=" * 80)
    print("RESUMEN DE PROCESAMIENTO")
    print("=" * 80)
    stats = processor.get_summary_stats()
    print(f"Total de tareas procesadas: {stats['total_tasks']}")
    print(f"Sprints completados: {stats['completed_sprints']}")
    print(f"Tareas entregadas (DoD): {stats['delivered_tasks']}")
    print(f"Estados de entrega: {stats['delivery_states']}")
    print()

    # Calcular métricas
    calculator = MetricsCalculator(processed_df, team_size)
    calculator.calculate_all_metrics()

    sprint_metrics = calculator.get_sprint_metrics()
    month_metrics = calculator.get_month_metrics()

    print("=" * 80)
    print("MÉTRICAS POR SPRINT - CÓDIGO ACTUAL")
    print("=" * 80)
    print()

    # Mostrar métricas de sprint
    for idx, row in sprint_metrics.iterrows():
        print(f"{'-' * 80}")
        print(f"{row['Sprint']} ({row['Month']})")
        print(f"{'-' * 80}")
        print(f"  Throughput: {int(row['Throughput'])} tareas")
        print(f"  Velocity: {row['Velocity']:.1f} puntos")
        print(f"  Total Estimado: {row['Total_Estimated']:.1f} puntos")
        print(f"  Cycle Time (Promedio): {row['Cycle_Time_Avg']:.1f} dias" if not pd.isna(row['Cycle_Time_Avg']) else "  Cycle Time (Promedio): N/A")
        print(f"  Cycle Time (Mediana): {row['Cycle_Time_Median']:.1f} dias" if not pd.isna(row['Cycle_Time_Median']) else "  Cycle Time (Mediana): N/A")
        print(f"  Cycle Time HDU (Promedio): {row['Cycle_Time_HDU_Avg']:.1f} dias" if not pd.isna(row['Cycle_Time_HDU_Avg']) else "  Cycle Time HDU (Promedio): N/A")
        print(f"  Cycle Time HDU (Mediana): {row['Cycle_Time_HDU_Median']:.1f} dias" if not pd.isna(row['Cycle_Time_HDU_Median']) else "  Cycle Time HDU (Mediana): N/A")
        print(f"  Predictabilidad: {row['Predictability']:.1f}%" if not pd.isna(row['Predictability']) else "  Predictabilidad: N/A")
        print(f"  Predictabilidad HDU: {row['Predictability_HDU']:.1f}%" if not pd.isna(row['Predictability_HDU']) else "  Predictabilidad HDU: N/A")
        print(f"  Eficiencia: {row['Efficiency']:.1f} puntos/persona" if not pd.isna(row['Efficiency']) else "  Eficiencia: N/A")
        print(f"  Retrabajo Estimado: {row['Rework']:.1f}%" if not pd.isna(row['Rework']) else "  Retrabajo Estimado: N/A")
        print(f"  Retrabajo Logrado: {row['Rework_Achieved']:.1f}%" if not pd.isna(row['Rework_Achieved']) else "  Retrabajo Logrado: N/A")
        print(f"  Total tareas: {int(row['Total_Tasks'])}")
        print(f"  Puntos comprometidos: {row['Committed_Points']:.1f}")
        print(f"  Puntos entregados: {row['Delivered_Points']:.1f}")
        print()

    print("=" * 80)
    print("MÉTRICAS POR MES - CÓDIGO ACTUAL")
    print("=" * 80)
    print()

    # Mostrar métricas de mes
    for idx, row in month_metrics.iterrows():
        print(f"{'-' * 80}")
        print(f"{row['Month']} (Sprints: {row['Sprints']})")
        print(f"{'-' * 80}")
        print(f"  Throughput Total: {int(row['Throughput_Total'])} tareas")
        print(f"  Throughput Promedio: {row['Throughput_Avg']:.1f} tareas/sprint")
        print(f"  Velocity Total: {row['Velocity_Total']:.1f} puntos")
        print(f"  Velocity Promedio: {row['Velocity_Avg']:.1f} puntos/sprint")
        print(f"  Total Estimado Total: {row['Total_Estimated_Total']:.1f} puntos")
        print(f"  Total Estimado Promedio: {row['Total_Estimated_Avg']:.1f} puntos/sprint")
        print(f"  Cycle Time (Promedio): {row['Cycle_Time_Avg']:.1f} dias" if not pd.isna(row['Cycle_Time_Avg']) else "  Cycle Time (Promedio): N/A")
        print(f"  Cycle Time (Mediana): {row['Cycle_Time_Median']:.1f} dias" if not pd.isna(row['Cycle_Time_Median']) else "  Cycle Time (Mediana): N/A")
        print(f"  Cycle Time HDU (Promedio): {row['Cycle_Time_HDU_Avg']:.1f} dias" if not pd.isna(row['Cycle_Time_HDU_Avg']) else "  Cycle Time HDU (Promedio): N/A")
        print(f"  Cycle Time HDU (Mediana): {row['Cycle_Time_HDU_Median']:.1f} dias" if not pd.isna(row['Cycle_Time_HDU_Median']) else "  Cycle Time HDU (Mediana): N/A")
        print(f"  Predictabilidad: {row['Predictability']:.1f}%" if not pd.isna(row['Predictability']) else "  Predictabilidad: N/A")
        print(f"  Predictabilidad HDU: {row['Predictability_HDU']:.1f}%" if not pd.isna(row['Predictability_HDU']) else "  Predictabilidad HDU: N/A")
        print(f"  Eficiencia: {row['Efficiency']:.1f} puntos/persona" if not pd.isna(row['Efficiency']) else "  Eficiencia: N/A")
        print(f"  Retrabajo Estimado: {row['Rework']:.1f}%" if not pd.isna(row['Rework']) else "  Retrabajo Estimado: N/A")
        print(f"  Retrabajo Logrado: {row['Rework_Achieved']:.1f}%" if not pd.isna(row['Rework_Achieved']) else "  Retrabajo Logrado: N/A")
        print(f"  Total tareas: {int(row['Total_Tasks'])}")
        print()

    # Desglose por tipo de tarea para throughput
    print("=" * 80)
    print("DESGLOSE DE THROUGHPUT POR TIPO DE TAREA - CÓDIGO ACTUAL")
    print("=" * 80)
    print()

    # Por sprint
    print("POR SPRINT:")
    print()
    for sprint in sorted(processed_df['Sprint'].unique()):
        sprint_data = processed_df[processed_df['Sprint'] == sprint]
        delivered = sprint_data[sprint_data['Is_Delivered']]

        print(f"{sprint}:")
        for tipo in sorted(delivered['Tipo Tarea'].unique()):
            count = len(delivered[delivered['Tipo Tarea'] == tipo])
            print(f"  - {tipo}: {count} tareas")
        print(f"  TOTAL: {len(delivered)} tareas")
        print()

    # Por mes
    print("POR MES:")
    print()
    for month in ['Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']:
        month_data = processed_df[processed_df['Month'] == month]
        if len(month_data) == 0:
            continue
        delivered = month_data[month_data['Is_Delivered']]

        print(f"{month}:")
        for tipo in sorted(delivered['Tipo Tarea'].unique()):
            count = len(delivered[delivered['Tipo Tarea'] == tipo])
            print(f"  - {tipo}: {count} tareas")
        print(f"  TOTAL: {len(delivered)} tareas")
        print()

    # Resumen ejecutivo
    summary = calculator.get_summary()
    print("=" * 80)
    print("RESUMEN EJECUTIVO - CÓDIGO ACTUAL")
    print("=" * 80)
    print(f"Tamaño del equipo: {summary['team_size']} personas")
    print(f"Sprints analizados: {summary['total_sprints']}")
    print(f"Tareas entregadas: {summary['total_delivered']}")
    print(f"\nPROMEDIOS:")
    print(f"  • Throughput: {summary['avg_throughput']:.1f} tareas/sprint")
    print(f"  • Velocity: {summary['avg_velocity']:.1f} puntos/sprint")
    print(f"  • Cycle Time: {summary['avg_cycle_time']:.1f} días")
    print(f"  • Predictabilidad: {summary['avg_predictability']:.1f}%")
    print(f"  • Eficiencia: {summary['avg_efficiency']:.1f} puntos/persona")
    print(f"  • Retrabajo Estimado: {summary['avg_rework']:.1f}%")
    print(f"  • Retrabajo Logrado: {summary['avg_rework_achieved']:.1f}%")

except Exception as e:
    print(f"\nERROR al procesar: {e}")
    import traceback
    traceback.print_exc()
