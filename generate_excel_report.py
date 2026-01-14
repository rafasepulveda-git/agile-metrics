"""
Script para generar el reporte Excel con todas las métricas.
"""
import pandas as pd
import sys
sys.path.insert(0, 'C:\\Proyectos\\agile-metrics\\metrics_analyzer')

from data_processor import DataProcessor
from metrics_calculator import MetricsCalculator
from report_generator import generate_excel_report

# Configuración
file_path = r'C:\Proyectos\agile-metrics\Backlog_Planning_No_paquetizado_All_Tasks_1768419897.xlsx'
team_type = 'Productivo'
team_size = 6
output_file = 'Metricas_Performance_Equipo.xlsx'

# Mapeo de sprints a meses
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
print("GENERANDO REPORTE EXCEL")
print("=" * 80)
print(f"Archivo de entrada: {file_path}")
print(f"Tipo de equipo: {team_type}")
print(f"Tamaño del equipo: {team_size} personas")
print(f"Archivo de salida: {output_file}")
print()

try:
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

    # Agregar columna "Sprint Completed?" = 'v' para todos (asumir completados)
    df['Sprint Completed?'] = 'v'

    # Determinar qué columna de fecha usar
    date_cols = ['Fecha Término', 'Fecha Ready for Production', 'Fecha paso a Producción']
    delivery_date_column = 'Fecha Término'  # Por defecto
    for col in date_cols:
        if col in df.columns and df[col].notna().sum() > 0:
            delivery_date_column = col
            break

    print(f"Procesando datos...")

    # Procesar datos
    processor = DataProcessor(
        df,
        team_type=team_type,
        sprint_mapping=sprint_mapping,
        delivery_date_column=delivery_date_column
    )
    processed_df = processor.process()

    print(f"Total de tareas procesadas: {len(processed_df)}")
    print(f"Sprints completados: {processed_df['Sprint'].nunique()}")
    print()

    # Calcular métricas
    print("Calculando métricas...")
    calculator = MetricsCalculator(processed_df, team_size)
    calculator.calculate_all_metrics()

    sprint_metrics = calculator.get_sprint_metrics()
    month_metrics = calculator.get_month_metrics()
    summary = calculator.get_summary()

    print(f"Métricas por sprint: {len(sprint_metrics)} sprints")
    print(f"Métricas por mes: {len(month_metrics)} meses")
    print()

    # Generar reporte Excel
    print("Generando reporte Excel...")
    output_path = generate_excel_report(
        sprint_metrics=sprint_metrics,
        month_metrics=month_metrics,
        summary=summary,
        output_path=output_file
    )

    print()
    print("=" * 80)
    print("REPORTE GENERADO EXITOSAMENTE")
    print("=" * 80)
    print(f"Archivo: {output_path}")
    print()
    print("Columnas incluidas:")
    print("  - Sprint / Mes")
    print("  - Throughput (tareas entregadas)")
    print("  - Velocity (puntos logrados)")
    print("  - Total Estimado (puntos estimados)")
    print("  - Cycle Time (Promedio y Mediana)")
    print("  - Cycle Time HDU (Promedio y Mediana)")
    print("  - Predictabilidad (todas las tareas)")
    print("  - Predictabilidad HDU (solo tareas HDU)")
    print("  - Eficiencia (puntos/persona)")
    print("  - Retrabajo Estimado (% bugs sobre estimación)")
    print("  - Retrabajo Logrado (% bugs sobre puntos logrados)")
    print()
    print("El archivo incluye formato condicional para facilitar la interpretación.")
    print()

except Exception as e:
    print(f"\nERROR al generar reporte: {e}")
    import traceback
    traceback.print_exc()
