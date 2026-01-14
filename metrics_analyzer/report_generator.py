"""
Generación de reportes Excel para métricas ágiles.

Este módulo crea archivos Excel con múltiples hojas, formato condicional
y visualización profesional de las métricas calculadas.
"""

import logging
from pathlib import Path
from typing import Dict
import pandas as pd
import xlsxwriter
from config import EXCEL_CONFIG, THRESHOLDS


logger = logging.getLogger(__name__)


class ExcelReportGenerator:
    """Generador de reportes Excel."""

    def __init__(
        self,
        sprint_metrics: pd.DataFrame,
        month_metrics: pd.DataFrame,
        summary: Dict,
        output_path: str
    ):
        """
        Inicializa el generador de reportes.

        Args:
            sprint_metrics: DataFrame con métricas por sprint.
            month_metrics: DataFrame con métricas por mes.
            summary: Diccionario con resumen ejecutivo.
            output_path: Ruta donde guardar el archivo Excel.
        """
        self.sprint_metrics = sprint_metrics
        self.month_metrics = month_metrics
        self.summary = summary
        self.output_path = output_path
        self.workbook = None
        self.formats = {}

    def generate(self) -> None:
        """Genera el reporte Excel completo."""
        logger.info(f"Generando reporte Excel: {self.output_path}")

        # Crear workbook con opciones para manejar NaN/INF
        self.workbook = xlsxwriter.Workbook(self.output_path, {'nan_inf_to_errors': True})

        # Crear formatos
        self._create_formats()

        # Crear hojas
        self._create_executive_summary_sheet()
        self._create_sprint_metrics_sheet()

        if not self.month_metrics.empty:
            self._create_month_metrics_sheet()

        # Cerrar workbook
        self.workbook.close()

        logger.info(f"Reporte Excel guardado en: {self.output_path}")

    def _create_formats(self) -> None:
        """Crea los formatos para el Excel."""
        # Header format
        self.formats['header'] = self.workbook.add_format({
            'bold': True,
            'bg_color': EXCEL_CONFIG['header_bg_color'],
            'font_color': EXCEL_CONFIG['header_font_color'],
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        # Title format
        self.formats['title'] = self.workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left',
            'valign': 'vcenter'
        })

        # Number formats
        self.formats['number'] = self.workbook.add_format({
            'num_format': EXCEL_CONFIG['number_format'],
            'align': 'center'
        })

        self.formats['percent'] = self.workbook.add_format({
            'num_format': EXCEL_CONFIG['percent_format'],
            'align': 'center'
        })

        self.formats['integer'] = self.workbook.add_format({
            'num_format': '0',
            'align': 'center'
        })

        # Conditional formats
        self.formats['good'] = self.workbook.add_format({
            'bg_color': '#C6EFCE',
            'font_color': '#006100',
            'num_format': EXCEL_CONFIG['number_format'],
            'align': 'center'
        })

        self.formats['warning'] = self.workbook.add_format({
            'bg_color': '#FFEB9C',
            'font_color': '#9C5700',
            'num_format': EXCEL_CONFIG['number_format'],
            'align': 'center'
        })

        self.formats['danger'] = self.workbook.add_format({
            'bg_color': '#FFC7CE',
            'font_color': '#9C0006',
            'num_format': EXCEL_CONFIG['number_format'],
            'align': 'center'
        })

    def _create_executive_summary_sheet(self) -> None:
        """Crea la hoja de resumen ejecutivo."""
        worksheet = self.workbook.add_worksheet('Resumen Ejecutivo')

        # Configurar anchos de columna
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 20)

        row = 0

        # Título
        worksheet.write(row, 0, 'RESUMEN EJECUTIVO DE MÉTRICAS', self.formats['title'])
        row += 2

        # Información general
        worksheet.write(row, 0, 'Tamaño del equipo:', self.formats['header'])
        worksheet.write(row, 1, self.summary['team_size'], self.formats['integer'])
        row += 1

        worksheet.write(row, 0, 'Sprints analizados:', self.formats['header'])
        worksheet.write(row, 1, self.summary['total_sprints'], self.formats['integer'])
        row += 1

        worksheet.write(row, 0, 'Tareas entregadas:', self.formats['header'])
        worksheet.write(row, 1, self.summary['total_delivered'], self.formats['integer'])
        row += 2

        # Métricas promedio
        worksheet.write(row, 0, 'PROMEDIOS', self.formats['title'])
        row += 1

        metrics_data = [
            ('Throughput (tareas/sprint)', self.summary['avg_throughput']),
            ('Velocity (puntos/sprint)', self.summary['avg_velocity']),
            ('Cycle Time (días)', self.summary['avg_cycle_time']),
            ('Predictibilidad (%)', self.summary['avg_predictability']),
            ('Eficiencia (puntos/persona)', self.summary['avg_efficiency']),
            ('Retrabajo (%)', self.summary['avg_rework'])
        ]

        for metric_name, metric_value in metrics_data:
            worksheet.write(row, 0, metric_name, self.formats['header'])
            worksheet.write(row, 1, metric_value, self.formats['number'])
            row += 1

        row += 1

        # Mejor y peor sprint
        worksheet.write(row, 0, 'MEJOR SPRINT', self.formats['title'])
        row += 1
        worksheet.write(row, 0, 'Sprint:', self.formats['header'])
        worksheet.write(row, 1, self.summary['best_sprint']['name'])
        row += 1
        worksheet.write(row, 0, 'Throughput:', self.formats['header'])
        worksheet.write(row, 1, self.summary['best_sprint']['throughput'], self.formats['integer'])
        row += 2

        worksheet.write(row, 0, 'PEOR SPRINT', self.formats['title'])
        row += 1
        worksheet.write(row, 0, 'Sprint:', self.formats['header'])
        worksheet.write(row, 1, self.summary['worst_sprint']['name'])
        row += 1
        worksheet.write(row, 0, 'Throughput:', self.formats['header'])
        worksheet.write(row, 1, self.summary['worst_sprint']['throughput'], self.formats['integer'])

    def _create_sprint_metrics_sheet(self) -> None:
        """Crea la hoja de métricas por sprint."""
        worksheet = self.workbook.add_worksheet('Métricas por Sprint')

        # Preparar datos
        df = self.sprint_metrics.copy()

        # Seleccionar y renombrar columnas
        columns_to_show = {
            'Sprint': 'Sprint',
            'Month': 'Mes',
            'Throughput': 'Throughput',
            'Velocity': 'Velocity',
            'Total_Estimated': 'Total Estimado',
            'Cycle_Time_Avg': 'Cycle Time Prom.',
            'Cycle_Time_Median': 'Cycle Time Med.',
            'Cycle_Time_HDU_Avg': 'Cycle Time HDU Prom.',
            'Cycle_Time_HDU_Median': 'Cycle Time HDU Med.',
            'Predictability': 'Predictibilidad (%)',
            'Predictability_HDU': 'Predictibilidad HDU (%)',
            'Efficiency': 'Eficiencia',
            'Rework': 'Retrabajo Est. (%)',
            'Rework_Achieved': 'Retrabajo Logr. (%)',
            'Total_Tasks': 'Total Tareas',
            'Delivered_Tasks': 'Tareas Entregadas'
        }

        df_display = df[list(columns_to_show.keys())].rename(columns=columns_to_show)

        # Escribir headers
        for col_num, column_name in enumerate(df_display.columns):
            worksheet.write(0, col_num, column_name, self.formats['header'])

        # Escribir datos con formato condicional
        for row_num, row_data in enumerate(df_display.values, start=1):
            for col_num, value in enumerate(row_data):
                column_name = df_display.columns[col_num]

                # Aplicar formato según columna
                if pd.isna(value):
                    worksheet.write(row_num, col_num, 'N/A')
                elif column_name in ['Throughput', 'Total Tareas', 'Tareas Entregadas']:
                    worksheet.write(row_num, col_num, int(value), self.formats['integer'])
                elif column_name in ['Velocity', 'Total Estimado', 'Cycle Time Prom.', 'Cycle Time Med.',
                                     'Cycle Time HDU Prom.', 'Cycle Time HDU Med.', 'Eficiencia']:
                    worksheet.write(row_num, col_num, value, self.formats['number'])
                elif column_name == 'Predictibilidad (%)':
                    # Formato condicional para predictibilidad
                    if value >= THRESHOLDS['predictability_good']:
                        fmt = self.formats['good']
                    elif value >= THRESHOLDS['predictability_warning']:
                        fmt = self.formats['warning']
                    else:
                        fmt = self.formats['danger']
                    worksheet.write(row_num, col_num, value, fmt)
                elif column_name == 'Predictibilidad HDU (%)':
                    # Formato condicional para predictibilidad HDU (mismo que predictibilidad)
                    if value >= THRESHOLDS['predictability_good']:
                        fmt = self.formats['good']
                    elif value >= THRESHOLDS['predictability_warning']:
                        fmt = self.formats['warning']
                    else:
                        fmt = self.formats['danger']
                    worksheet.write(row_num, col_num, value, fmt)
                elif column_name == 'Retrabajo Est. (%)':
                    # Formato condicional para retrabajo estimado (inverso: menos es mejor)
                    if value <= THRESHOLDS['rework_good']:
                        fmt = self.formats['good']
                    elif value <= THRESHOLDS['rework_warning']:
                        fmt = self.formats['warning']
                    else:
                        fmt = self.formats['danger']
                    worksheet.write(row_num, col_num, value, fmt)
                elif column_name == 'Retrabajo Logr. (%)':
                    # Formato condicional para retrabajo logrado (inverso: menos es mejor)
                    if value <= THRESHOLDS['rework_good']:
                        fmt = self.formats['good']
                    elif value <= THRESHOLDS['rework_warning']:
                        fmt = self.formats['warning']
                    else:
                        fmt = self.formats['danger']
                    worksheet.write(row_num, col_num, value, fmt)
                else:
                    worksheet.write(row_num, col_num, value)

        # Ajustar anchos de columna
        for col_num, column_name in enumerate(df_display.columns):
            max_len = max(len(str(column_name)), 12)
            worksheet.set_column(col_num, col_num, max_len + 2)

    def _create_month_metrics_sheet(self) -> None:
        """Crea la hoja de métricas por mes."""
        worksheet = self.workbook.add_worksheet('Métricas por Mes')

        # Preparar datos
        df = self.month_metrics.copy()

        # Seleccionar y renombrar columnas
        columns_to_show = {
            'Month': 'Mes',
            'Num_Sprints': 'Num. Sprints',
            'Sprints': 'Sprints',
            'Throughput_Total': 'Throughput Total',
            'Throughput_Avg': 'Throughput Prom.',
            'Velocity_Total': 'Velocity Total',
            'Velocity_Avg': 'Velocity Prom.',
            'Total_Estimated_Total': 'Total Estimado Total',
            'Total_Estimated_Avg': 'Total Estimado Prom.',
            'Cycle_Time_Avg': 'Cycle Time Prom.',
            'Cycle_Time_Median': 'Cycle Time Med.',
            'Cycle_Time_HDU_Avg': 'Cycle Time HDU Prom.',
            'Cycle_Time_HDU_Median': 'Cycle Time HDU Med.',
            'Predictability': 'Predictibilidad (%)',
            'Predictability_HDU': 'Predictibilidad HDU (%)',
            'Efficiency': 'Eficiencia',
            'Rework': 'Retrabajo Est. (%)',
            'Rework_Achieved': 'Retrabajo Logr. (%)'
        }

        df_display = df[list(columns_to_show.keys())].rename(columns=columns_to_show)

        # Escribir headers
        for col_num, column_name in enumerate(df_display.columns):
            worksheet.write(0, col_num, column_name, self.formats['header'])

        # Escribir datos con formato condicional
        for row_num, row_data in enumerate(df_display.values, start=1):
            for col_num, value in enumerate(row_data):
                column_name = df_display.columns[col_num]

                # Aplicar formato según columna
                if pd.isna(value):
                    worksheet.write(row_num, col_num, 'N/A')
                elif column_name in ['Num. Sprints', 'Throughput Total']:
                    worksheet.write(row_num, col_num, int(value), self.formats['integer'])
                elif column_name in ['Throughput Prom.', 'Velocity Total', 'Velocity Prom.',
                                     'Total Estimado Total', 'Total Estimado Prom.',
                                     'Cycle Time Prom.', 'Cycle Time Med.',
                                     'Cycle Time HDU Prom.', 'Cycle Time HDU Med.',
                                     'Eficiencia']:
                    worksheet.write(row_num, col_num, value, self.formats['number'])
                elif column_name == 'Predictibilidad (%)':
                    if value >= THRESHOLDS['predictability_good']:
                        fmt = self.formats['good']
                    elif value >= THRESHOLDS['predictability_warning']:
                        fmt = self.formats['warning']
                    else:
                        fmt = self.formats['danger']
                    worksheet.write(row_num, col_num, value, fmt)
                elif column_name == 'Predictibilidad HDU (%)':
                    if value >= THRESHOLDS['predictability_good']:
                        fmt = self.formats['good']
                    elif value >= THRESHOLDS['predictability_warning']:
                        fmt = self.formats['warning']
                    else:
                        fmt = self.formats['danger']
                    worksheet.write(row_num, col_num, value, fmt)
                elif column_name == 'Retrabajo Est. (%)':
                    if value <= THRESHOLDS['rework_good']:
                        fmt = self.formats['good']
                    elif value <= THRESHOLDS['rework_warning']:
                        fmt = self.formats['warning']
                    else:
                        fmt = self.formats['danger']
                    worksheet.write(row_num, col_num, value, fmt)
                elif column_name == 'Retrabajo Logr. (%)':
                    if value <= THRESHOLDS['rework_good']:
                        fmt = self.formats['good']
                    elif value <= THRESHOLDS['rework_warning']:
                        fmt = self.formats['warning']
                    else:
                        fmt = self.formats['danger']
                    worksheet.write(row_num, col_num, value, fmt)
                else:
                    worksheet.write(row_num, col_num, value)

        # Ajustar anchos de columna
        for col_num, column_name in enumerate(df_display.columns):
            if column_name == 'Sprints':
                worksheet.set_column(col_num, col_num, 25)
            else:
                max_len = max(len(str(column_name)), 12)
                worksheet.set_column(col_num, col_num, max_len + 2)


def generate_excel_report(
    sprint_metrics: pd.DataFrame,
    month_metrics: pd.DataFrame,
    summary: Dict,
    output_path: str = 'Metricas_Performance_Equipo.xlsx'
) -> str:
    """
    Genera un reporte Excel completo.

    Args:
        sprint_metrics: DataFrame con métricas por sprint.
        month_metrics: DataFrame con métricas por mes.
        summary: Diccionario con resumen ejecutivo.
        output_path: Ruta donde guardar el archivo.

    Returns:
        Ruta del archivo generado.
    """
    generator = ExcelReportGenerator(sprint_metrics, month_metrics, summary, output_path)
    generator.generate()

    return output_path
