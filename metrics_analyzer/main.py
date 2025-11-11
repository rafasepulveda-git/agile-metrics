#!/usr/bin/env python3
"""
Analizador de Métricas de Performance Ágil.

Este script analiza datos exportados de Monday.com y genera métricas
de performance ágil incluyendo Throughput, Velocity, Cycle Time,
Predictibilidad, Eficiencia y Retrabajo.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict

from config import (
    DEFAULT_SPRINT_MAPPING,
    DELIVERY_DATE_COLUMNS_PRODUCTIVE,
    DELIVERY_DATE_COLUMNS_DEVELOPMENT
)
from data_loader import load_and_validate_data
from data_processor import process_data
from metrics_calculator import MetricsCalculator
from visualizations import generate_dashboards
from report_generator import generate_excel_report
from utils import (
    setup_logging,
    parse_sprint_mapping,
    validate_team_size,
    print_section_header,
    print_success,
    print_warning,
    print_error,
    print_info,
    format_file_size
)
import pandas as pd


logger = logging.getLogger(__name__)


def get_args() -> argparse.Namespace:
    """
    Parsea los argumentos de línea de comandos.

    Returns:
        Namespace con los argumentos parseados.
    """
    parser = argparse.ArgumentParser(
        description='Analizador de Métricas de Performance Ágil para datos de Monday.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Uso básico
  python main.py --input mi_archivo.xlsx

  # Con mapeo de sprints personalizado
  python main.py --input datos.xlsx --sprint-map "Sprint 2:Julio,Sprint 3:Agosto"

  # Generar solo Excel (sin gráficos)
  python main.py --input datos.xlsx --excel-only

  # Modo verbose para debugging
  python main.py --input datos.xlsx --verbose
        """
    )

    parser.add_argument(
        '--input',
        '-i',
        type=str,
        required=True,
        help='Archivo Excel de Monday.com a analizar'
    )

    parser.add_argument(
        '--output',
        '-o',
        type=str,
        default='.',
        help='Directorio de salida para los reportes (por defecto: directorio actual)'
    )

    parser.add_argument(
        '--sprint-map',
        type=str,
        default=None,
        help='Mapeo de sprints a meses en formato "Sprint 2:Julio,Sprint 3:Agosto"'
    )

    parser.add_argument(
        '--excel-only',
        action='store_true',
        help='Generar solo reporte Excel (sin gráficos)'
    )

    parser.add_argument(
        '--charts-only',
        action='store_true',
        help='Generar solo gráficos (sin Excel)'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Modo verbose (mostrar logs detallados)'
    )

    return parser.parse_args()


def prompt_team_type() -> str:
    """
    Pregunta al usuario el tipo de equipo.

    Returns:
        Tipo de equipo ('Productivo' o 'En Desarrollo').
    """
    print_section_header("CONFIGURACIÓN DEL EQUIPO")
    print("\nSeleccione el tipo de equipo:")
    print("  1. Productivo (estados entregados: 11-13)")
    print("  2. En Desarrollo (estados entregados: 9-13)")

    while True:
        choice = input("\nIngrese su opción (1 o 2): ").strip()

        if choice == '1':
            return 'Productivo'
        elif choice == '2':
            return 'En Desarrollo'
        else:
            print_error("Opción inválida. Por favor ingrese 1 o 2.")


def prompt_team_name() -> str:
    """
    Pregunta al usuario el nombre del equipo.

    Returns:
        Nombre del equipo.
    """
    print("\nIngrese el nombre del equipo:")

    while True:
        team_name = input("Nombre del equipo: ").strip()

        if not team_name:
            print_error("El nombre del equipo no puede estar vacío.")
            continue

        # Validar que no tenga caracteres inválidos para nombres de archivo
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in team_name for char in invalid_chars):
            print_error(f"El nombre no puede contener estos caracteres: {' '.join(invalid_chars)}")
            continue

        return team_name


def prompt_team_size() -> int:
    """
    Pregunta al usuario el tamaño del equipo.

    Returns:
        Número de miembros del equipo.
    """
    print("\nIngrese el número de miembros del equipo:")

    while True:
        try:
            size_str = input("Tamaño del equipo: ").strip()
            team_size = validate_team_size(size_str)
            return team_size
        except ValueError as e:
            print_error(str(e))


def prompt_sprint_mapping() -> Dict[str, str]:
    """
    Pregunta al usuario si quiere usar el mapeo por defecto o personalizado.

    Returns:
        Diccionario con el mapeo de sprints a meses.
    """
    print("\n¿Desea usar el mapeo de sprints por defecto?")
    print("Mapeo por defecto:")
    for sprint, month in DEFAULT_SPRINT_MAPPING.items():
        print(f"  {sprint} -> {month}")

    while True:
        choice = input("\nUsar mapeo por defecto? (s/n): ").strip().lower()

        if choice == 's':
            return DEFAULT_SPRINT_MAPPING
        elif choice == 'n':
            print("\nIngrese el mapeo personalizado en formato:")
            print("Sprint 2:Julio,Sprint 3:Agosto,Sprint 4:Agosto")

            while True:
                try:
                    mapping_str = input("\nMapeo: ").strip()
                    mapping = parse_sprint_mapping(mapping_str)
                    return mapping
                except ValueError as e:
                    print_error(str(e))
        else:
            print_error("Por favor ingrese 's' o 'n'")


def prompt_delivery_date_column(df: pd.DataFrame, team_type: str) -> str:
    """
    Detecta columnas de fecha disponibles y permite al usuario seleccionar
    cuál usar como fecha de entrega para el cálculo de Cycle Time.

    Args:
        df: DataFrame con los datos cargados.
        team_type: Tipo de equipo ('Productivo' o 'En Desarrollo').

    Returns:
        Nombre de la columna a usar como fecha de entrega.
    """
    # Seleccionar lista de columnas según tipo de equipo
    if team_type == 'Productivo':
        date_columns = DELIVERY_DATE_COLUMNS_PRODUCTIVE
        default_column = 'Fecha Término'
    else:  # En Desarrollo
        date_columns = DELIVERY_DATE_COLUMNS_DEVELOPMENT
        default_column = 'Fecha Certificado QA'

    # Detectar columnas de fecha disponibles y con datos
    available_columns = []
    for col in date_columns:
        if col in df.columns:
            # Contar cuántos valores no-nulos tiene
            non_null_count = df[col].notna().sum()
            if non_null_count > 0:
                available_columns.append({
                    'name': col,
                    'count': non_null_count,
                    'percentage': (non_null_count / len(df)) * 100
                })

    if not available_columns:
        print_warning(f"No se encontraron columnas de fecha con datos para calcular Cycle Time.")
        print_warning(f"Columnas buscadas para equipo '{team_type}': {', '.join(date_columns)}")
        print_warning("El Cycle Time no podrá ser calculado.")
        return None

    # Si solo hay una columna disponible, usarla automáticamente
    if len(available_columns) == 1:
        col_name = available_columns[0]['name']
        print_info(f"Usando columna de fecha: {col_name} ({available_columns[0]['percentage']:.1f}% completitud)")
        return col_name

    # Si la columna por defecto está disponible y tiene datos, preguntar si usarla
    default_col = next((c for c in available_columns if c['name'] == default_column), None)
    if default_col:
        print(f"\nSe encontró la columna '{default_column}' con datos (recomendada para equipos {team_type}).")
        print(f"Registros con fecha: {default_col['count']} ({default_col['percentage']:.1f}%)")

        choice = input(f"\n¿Usar '{default_column}' como fecha de entrega? (s/n): ").strip().lower()
        if choice == 's':
            return default_column

    # Mostrar todas las opciones disponibles
    print(f"\nSeleccione la columna de fecha a usar como fecha de entrega para Cycle Time (equipo {team_type}):")
    for idx, col_info in enumerate(available_columns, start=1):
        print(f"  {idx}. {col_info['name']}")
        print(f"     Registros con fecha: {col_info['count']} ({col_info['percentage']:.1f}%)")

    while True:
        try:
            choice = input(f"\nIngrese su opción (1-{len(available_columns)}): ").strip()
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(available_columns):
                selected_col = available_columns[choice_idx]['name']
                print_success(f"Usando columna: {selected_col}")
                return selected_col
            else:
                print_error(f"Opción inválida. Por favor ingrese un número entre 1 y {len(available_columns)}.")
        except ValueError:
            print_error("Por favor ingrese un número válido.")


def print_final_report(
    summary: Dict,
    excel_path: str = None,
    sprint_dashboard_path: str = None,
    month_dashboard_path: str = None
) -> None:
    """
    Imprime el reporte final con rutas de archivos generados.

    Args:
        summary: Diccionario con resumen ejecutivo.
        excel_path: Ruta del archivo Excel generado.
        sprint_dashboard_path: Ruta del dashboard de sprints.
        month_dashboard_path: Ruta del dashboard de meses.
    """
    print_section_header("PROCESO COMPLETADO EXITOSAMENTE", "=")

    # Mostrar archivos generados
    print("\nArchivos generados:")

    if excel_path:
        size = Path(excel_path).stat().st_size
        print_success(f"Excel: {excel_path} ({format_file_size(size)})")

    if sprint_dashboard_path:
        size = Path(sprint_dashboard_path).stat().st_size
        print_success(f"Dashboard Sprints: {sprint_dashboard_path} ({format_file_size(size)})")

    if month_dashboard_path and Path(month_dashboard_path).exists():
        size = Path(month_dashboard_path).stat().st_size
        print_success(f"Dashboard Meses: {month_dashboard_path} ({format_file_size(size)})")

    # Resumen ejecutivo
    print("\nRESUMEN:")
    print_info(f"Sprints analizados: {summary['total_sprints']}")
    print_info(f"Tareas entregadas: {summary['total_delivered']}")
    print_info(f"Throughput promedio: {summary['avg_throughput']:.1f} tareas/sprint")
    print_info(f"Velocity promedio: {summary['avg_velocity']:.1f} puntos/sprint")
    print_info(f"Predictibilidad promedio: {summary['avg_predictability']:.1f}%")
    print_info(f"Eficiencia promedio: {summary['avg_efficiency']:.1f} puntos/persona")

    # Alertas
    print("\nALERTAS:")
    if summary['avg_predictability'] < 70:
        print_warning(f"Predictibilidad baja ({summary['avg_predictability']:.1f}% - meta: 70%)")

    if summary['avg_rework'] > 30:
        print_warning(f"Retrabajo alto ({summary['avg_rework']:.1f}% - meta: <30%)")

    if summary['worst_sprint']['throughput'] == 0:
        print_warning(f"Sprint {summary['worst_sprint']['name']} tuvo 0 tareas entregadas")

    print("\n" + "=" * 60)
    print("Para más detalles, revise el archivo Excel y los dashboards.")
    print("=" * 60)


def main() -> int:
    """
    Función principal del programa.

    Returns:
        Código de salida (0 = éxito, 1 = error).
    """
    # Parsear argumentos
    args = get_args()

    # Configurar logging
    setup_logging(verbose=args.verbose)

    try:
        # Banner inicial
        print_section_header("ANALIZADOR DE MÉTRICAS DE PERFORMANCE ÁGIL", "=")

        # 1. Cargar y validar datos
        print_section_header("PASO 1: Carga y Validación de Datos")
        df = load_and_validate_data(args.input, verbose=args.verbose)

        # 2. Configuración interactiva
        team_name = prompt_team_name()
        team_type = prompt_team_type()
        team_size = prompt_team_size()

        sprint_mapping = None
        if args.sprint_map:
            sprint_mapping = parse_sprint_mapping(args.sprint_map)
            print_success("Usando mapeo de sprints personalizado")
        else:
            sprint_mapping = prompt_sprint_mapping()

        # Seleccionar columna de fecha para Cycle Time según tipo de equipo
        delivery_date_column = prompt_delivery_date_column(df, team_type)
        if delivery_date_column is None:
            # Fallback según tipo de equipo
            delivery_date_column = 'Fecha Certificado QA' if team_type == 'En Desarrollo' else 'Fecha Ready for Production'
            print_warning(f"Usando fallback: {delivery_date_column}")

        # 3. Procesar datos
        print_section_header("PASO 2: Procesamiento de Datos")
        processed_df = process_data(
            df,
            team_type=team_type,
            sprint_mapping=sprint_mapping,
            delivery_date_column=delivery_date_column,
            verbose=args.verbose
        )

        if len(processed_df) == 0:
            print_error("No hay datos válidos para procesar después del filtrado")
            return 1

        # 4. Calcular métricas
        print_section_header("PASO 3: Cálculo de Métricas")
        calculator = MetricsCalculator(processed_df, team_size)
        calculator.calculate_all_metrics()

        sprint_metrics = calculator.get_sprint_metrics()
        month_metrics = calculator.get_month_metrics()
        summary = calculator.get_summary()

        if args.verbose:
            calculator.print_summary()

        # 5. Generar reportes
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        excel_path = None
        sprint_dashboard_path = None
        month_dashboard_path = None

        if not args.charts_only:
            print_section_header("PASO 4: Generación de Reporte Excel")
            excel_filename = f'{team_name}_Metricas_Performance.xlsx'
            excel_path = str(output_dir / excel_filename)
            generate_excel_report(sprint_metrics, month_metrics, summary, excel_path)
            print_success("Reporte Excel generado")

        if not args.excel_only:
            print_section_header("PASO 5: Generación de Dashboards")
            dashboards = generate_dashboards(sprint_metrics, month_metrics, str(output_dir), team_name)
            sprint_dashboard_path = dashboards.get('sprint_dashboard')
            month_dashboard_path = dashboards.get('month_dashboard')
            print_success("Dashboards generados")

        # 6. Reporte final
        print_final_report(
            summary,
            excel_path=excel_path,
            sprint_dashboard_path=sprint_dashboard_path,
            month_dashboard_path=month_dashboard_path
        )

        return 0

    except FileNotFoundError as e:
        print_error(f"Archivo no encontrado: {e}")
        logger.exception("FileNotFoundError")
        return 1

    except ValueError as e:
        print_error(f"Error de validación: {e}")
        logger.exception("ValueError")
        return 1

    except Exception as e:
        print_error(f"Error inesperado: {e}")
        logger.exception("Unexpected error")
        return 1


if __name__ == '__main__':
    sys.exit(main())
