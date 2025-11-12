"""
Generación de visualizaciones para métricas ágiles.

Este módulo crea dashboards con múltiples gráficos de las métricas calculadas.
Soporta múltiples versiones de visualizaciones.
"""

import logging
from pathlib import Path
from typing import Optional, Literal
import pandas as pd
from config import VERSION


logger = logging.getLogger(__name__)


def generate_dashboards(
    sprint_metrics: pd.DataFrame,
    month_metrics: pd.DataFrame,
    output_dir: str = '.',
    team_name: str = 'Equipo',
    chart_version: Literal['v1', 'v2'] = 'v1'
) -> tuple[Optional[str], Optional[str]]:
    """
    Genera dashboards de métricas con la versión de gráficos especificada.

    Args:
        sprint_metrics: DataFrame con métricas por sprint.
        month_metrics: DataFrame con métricas por mes.
        output_dir: Directorio donde guardar los dashboards.
        team_name: Nombre del equipo (para nombres de archivos).
        chart_version: Versión de gráficos a usar:
            - 'v1': Gráficos clásicos (barras simples)
            - 'v2': Gráficos mejorados (control charts, box plots, gauges, etc.)

    Returns:
        Tupla (ruta_dashboard_sprint, ruta_dashboard_mes).
    """
    logger.info(f"Generando dashboards con versión de gráficos: {chart_version}")

    if chart_version == 'v1':
        # Usar visualizaciones clásicas
        from visualizations_v1 import DashboardGenerator
        logger.info("Usando gráficos clásicos (v1)")
    elif chart_version == 'v2':
        # Usar visualizaciones mejoradas
        from visualizations_v2 import DashboardGenerator
        logger.info("Usando gráficos mejorados (v2)")
    else:
        raise ValueError(f"Versión de gráficos no soportada: {chart_version}. Use 'v1' o 'v2'.")

    generator = DashboardGenerator(sprint_metrics, month_metrics)

    # Generar dashboard de sprints
    sprint_dashboard_path = f"{output_dir}/{team_name}_metricas_por_sprint_dashboard.png"
    generator.generate_sprint_dashboard(sprint_dashboard_path)
    logger.info(f"Dashboard de sprints guardado: {sprint_dashboard_path}")

    # Generar dashboard mensual si hay datos
    month_dashboard_path = None
    if not month_metrics.empty:
        month_dashboard_path = f"{output_dir}/{team_name}_metricas_por_mes_dashboard.png"
        generator.generate_month_dashboard(month_dashboard_path)
        logger.info(f"Dashboard mensual guardado: {month_dashboard_path}")
    else:
        logger.warning("No hay datos mensuales para generar dashboard.")

    return sprint_dashboard_path, month_dashboard_path
