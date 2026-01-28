"""
Generador de reportes Excel consolidados para procesamiento batch.

Este módulo crea un archivo Excel con una hoja por equipo y
una hoja resumen comparativa.
"""

import logging
from pathlib import Path
from typing import Dict, List, Set
import pandas as pd
import xlsxwriter

from config import EXCEL_CONFIG, THRESHOLDS, BATCH_CONFIG, TASK_TYPE_DISPLAY_ORDER
from batch_processor import TeamResult


logger = logging.getLogger(__name__)


class BatchReportGenerator:
    """Generador de reportes Excel consolidados."""

    def __init__(
        self,
        results: List[TeamResult],
        output_path: str
    ):
        """
        Inicializa el generador de reportes batch.

        Args:
            results: Lista de TeamResult con métricas de cada equipo.
            output_path: Ruta donde guardar el archivo Excel.
        """
        self.results = [r for r in results if r.success]
        self.output_path = output_path
        self.workbook = None
        self.formats = {}

        if not self.results:
            raise ValueError("No hay resultados exitosos para generar reporte")

        # Detectar todos los tipos de tareas presentes en los resultados
        self.task_types = self._detect_task_types()
        logger.info(f"Tipos de tareas detectados: {', '.join(self.task_types)}")

    def _detect_task_types(self) -> List[str]:
        """
        Detecta todos los tipos de tareas presentes en los resultados de los equipos.

        Returns:
            Lista ordenada de tipos de tareas.
        """
        all_task_types: Set[str] = set()

        # Recolectar todos los tipos de tareas del summary de cada equipo
        for result in self.results:
            summary = result.summary
            # Buscar claves que terminen en '_delivered'
            for key in summary.keys():
                if key.endswith('_delivered') and key != 'total_delivered':
                    # Extraer el nombre del tipo (ej: 'hdu_delivered' -> 'HDU')
                    task_type = key.replace('_delivered', '').upper()
                    # Primera letra mayúscula, resto como está (ej: 'HDU', 'Bug', 'Solicitud')
                    if task_type.lower() in ['hdu', 'bug', 'solicitud', 'spike', 'tech', 'backlog']:
                        # Casos especiales de capitalización
                        if task_type.lower() == 'hdu':
                            task_type = 'HDU'
                        else:
                            task_type = task_type.capitalize()
                    all_task_types.add(task_type)

        # Ordenar según TASK_TYPE_DISPLAY_ORDER, luego alfabéticamente
        ordered_types = []
        for task_type in TASK_TYPE_DISPLAY_ORDER:
            if task_type in all_task_types:
                ordered_types.append(task_type)
                all_task_types.remove(task_type)

        # Agregar los restantes en orden alfabético
        ordered_types.extend(sorted(all_task_types))

        return ordered_types

    def generate(self) -> str:
        """
        Genera el reporte Excel consolidado.

        Returns:
            Ruta del archivo generado.
        """
        logger.info(f"Generando reporte consolidado: {self.output_path}")

        self.workbook = xlsxwriter.Workbook(self.output_path, {'nan_inf_to_errors': True})
        self._create_formats()

        # 1. Crear hoja resumen comparativa (primera hoja)
        self._create_summary_sheet()

        # 2. Crear una hoja por equipo
        for result in sorted(self.results, key=lambda r: r.team_name):
            self._create_team_sheet(result)

        self.workbook.close()
        logger.info(f"Reporte consolidado guardado: {self.output_path}")

        return self.output_path

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
            'align': 'left'
        })

        # Subtitle format
        self.formats['subtitle'] = self.workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'left',
            'italic': True
        })

        # Number formats
        self.formats['number'] = self.workbook.add_format({
            'num_format': EXCEL_CONFIG['number_format'],
            'align': 'center'
        })

        self.formats['integer'] = self.workbook.add_format({
            'num_format': '0',
            'align': 'center'
        })

        self.formats['text'] = self.workbook.add_format({
            'align': 'left'
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

        # Team name format (for highlighting)
        self.formats['team_productive'] = self.workbook.add_format({
            'bold': True,
            'bg_color': '#E2EFDA',
            'align': 'left',
            'border': 1
        })

        self.formats['team_development'] = self.workbook.add_format({
            'bold': True,
            'bg_color': '#DDEBF7',
            'align': 'left',
            'border': 1
        })

    def _create_summary_sheet(self) -> None:
        """Crea la hoja de resumen comparativo de todos los equipos."""
        sheet_name = BATCH_CONFIG.get('summary_sheet_name', 'Resumen Comparativo')
        worksheet = self.workbook.add_worksheet(sheet_name)

        # Configurar anchos dinámicos
        num_task_type_cols = len(self.task_types)
        last_col_letter = chr(ord('O') + num_task_type_cols)  # O es la columna base + tipos de tareas
        worksheet.set_column('A:A', 25)  # Equipo
        worksheet.set_column('B:B', 15)  # Tipo
        worksheet.set_column(f'C:{last_col_letter}', 14)  # Métricas

        row = 0

        # Título
        worksheet.write(row, 0, 'RESUMEN COMPARATIVO DE EQUIPOS', self.formats['title'])
        row += 2

        # Headers dinámicos basados en tipos de tareas detectados
        headers = [
            'Equipo', 'Tipo DoD', 'Tamaño', 'Sprints',
            'Throughput Prom.', 'Velocity Prom.', 'Cycle Time Prom.',
            'Predictibilidad (%)', 'Predict. HDU (%)',
            'Eficiencia', 'Retrabajo (%)',
            'Total Entregadas'
        ]
        # Agregar columnas de tipos de tareas dinámicamente
        headers.extend(self.task_types)
        # Agregar columnas finales
        headers.extend(['Mejor Sprint', 'Peor Sprint'])

        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])

        row += 1

        # Datos por equipo
        for result in sorted(self.results, key=lambda r: r.team_name):
            summary = result.summary

            # Formato según tipo de equipo
            team_fmt = self.formats['team_productive'] if result.team_type == 'Productivo' else self.formats['team_development']

            worksheet.write(row, 0, result.team_name, team_fmt)
            worksheet.write(row, 1, result.team_type, self.formats['text'])
            worksheet.write(row, 2, result.team_size, self.formats['integer'])
            worksheet.write(row, 3, summary.get('total_sprints', 0), self.formats['integer'])
            worksheet.write(row, 4, summary.get('avg_throughput', 0), self.formats['number'])
            worksheet.write(row, 5, summary.get('avg_velocity', 0), self.formats['number'])
            worksheet.write(row, 6, summary.get('avg_cycle_time', 0), self.formats['number'])

            # Predictibilidad con formato condicional
            pred = summary.get('avg_predictability', 0)
            pred_fmt = self._get_predictability_format(pred)
            worksheet.write(row, 7, pred, pred_fmt)

            # Predictibilidad HDU
            pred_hdu = self._calculate_avg_predictability_hdu(result.sprint_metrics)
            pred_hdu_fmt = self._get_predictability_format(pred_hdu)
            worksheet.write(row, 8, pred_hdu, pred_hdu_fmt)

            worksheet.write(row, 9, summary.get('avg_efficiency', 0), self.formats['number'])

            # Retrabajo con formato condicional
            rework = summary.get('avg_rework', 0)
            rework_fmt = self._get_rework_format(rework)
            worksheet.write(row, 10, rework, rework_fmt)

            worksheet.write(row, 11, summary.get('total_delivered', 0), self.formats['integer'])

            # Escribir columnas de tipos de tareas dinámicamente
            col_idx = 12
            for task_type in self.task_types:
                key = f'{task_type.lower()}_delivered'
                value = summary.get(key, 0)
                worksheet.write(row, col_idx, value, self.formats['integer'])
                col_idx += 1

            # Columnas finales (Mejor/Peor Sprint)
            best_sprint = summary.get('best_sprint', {})
            worksheet.write(row, col_idx, f"{best_sprint.get('name', 'N/A')} ({best_sprint.get('throughput', 0)})", self.formats['text'])
            col_idx += 1

            worst_sprint = summary.get('worst_sprint', {})
            worksheet.write(row, col_idx, f"{worst_sprint.get('name', 'N/A')} ({worst_sprint.get('throughput', 0)})", self.formats['text'])

            row += 1

        # Línea de totales/promedios
        row += 1
        worksheet.write(row, 0, 'PROMEDIO GENERAL', self.formats['header'])

        # Calcular promedios
        num_teams = len(self.results)
        if num_teams > 0:
            avg_throughput = sum(r.summary.get('avg_throughput', 0) for r in self.results) / num_teams
            avg_velocity = sum(r.summary.get('avg_velocity', 0) for r in self.results) / num_teams
            avg_cycle_time = sum(r.summary.get('avg_cycle_time', 0) for r in self.results) / num_teams
            avg_pred = sum(r.summary.get('avg_predictability', 0) for r in self.results) / num_teams
            avg_eff = sum(r.summary.get('avg_efficiency', 0) for r in self.results) / num_teams
            avg_rework = sum(r.summary.get('avg_rework', 0) for r in self.results) / num_teams
            total_delivered = sum(r.summary.get('total_delivered', 0) for r in self.results)

            # Calcular totales de cada tipo de tarea dinámicamente
            task_type_totals = {}
            for task_type in self.task_types:
                key = f'{task_type.lower()}_delivered'
                total = sum(r.summary.get(key, 0) for r in self.results)
                task_type_totals[task_type] = total

            worksheet.write(row, 4, avg_throughput, self.formats['number'])
            worksheet.write(row, 5, avg_velocity, self.formats['number'])
            worksheet.write(row, 6, avg_cycle_time, self.formats['number'])
            worksheet.write(row, 7, avg_pred, self._get_predictability_format(avg_pred))
            worksheet.write(row, 9, avg_eff, self.formats['number'])
            worksheet.write(row, 10, avg_rework, self._get_rework_format(avg_rework))
            worksheet.write(row, 11, total_delivered, self.formats['integer'])

            # Escribir totales de tipos de tareas dinámicamente
            col_idx = 12
            for task_type in self.task_types:
                worksheet.write(row, col_idx, task_type_totals[task_type], self.formats['integer'])
                col_idx += 1

    def _create_team_sheet(self, result: TeamResult) -> None:
        """
        Crea una hoja con métricas detalladas de un equipo.

        Args:
            result: TeamResult con los datos del equipo.
        """
        # Nombre de hoja (max 31 caracteres en Excel)
        sheet_name = result.team_name[:31]
        worksheet = self.workbook.add_worksheet(sheet_name)

        # Configurar anchos dinámicos
        num_task_type_cols = len(self.task_types)
        last_col_letter = chr(ord('Q') + num_task_type_cols)  # Q es la columna base + tipos de tareas (agregamos Retrabajo Vel.)
        worksheet.set_column('A:A', 15)
        worksheet.set_column(f'B:{last_col_letter}', 14)

        row = 0

        # Título con info del equipo
        worksheet.write(row, 0, f'MÉTRICAS: {result.team_name}', self.formats['title'])
        row += 1
        worksheet.write(row, 0, f'Tipo DoD: {result.team_type} | Tamaño: {result.team_size}', self.formats['subtitle'])
        row += 2

        # Headers dinámicos de métricas por sprint
        headers = [
            'Sprint', 'Mes', 'Throughput', 'Velocity', 'Total Estimado',
            'Cycle Time Prom.', 'Cycle Time Med.', 'CT HDU Prom.', 'CT HDU Med.',
            'Predictibilidad (%)', 'Predict. HDU (%)', 'Eficiencia',
            'Retrabajo Est. (%)', 'Retrabajo Log. (%)', 'Retrabajo Vel. (%)',
            'Total Tareas', 'Entregadas'
        ]
        # Agregar columnas de tipos de tareas dinámicamente
        headers.extend(self.task_types)

        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])

        row += 1

        # Datos por sprint
        df = result.sprint_metrics
        if df.empty:
            worksheet.write(row, 0, 'No hay datos disponibles', self.formats['text'])
            return

        for _, sprint_row in df.iterrows():
            col = 0
            worksheet.write(row, col, sprint_row.get('Sprint', ''), self.formats['text'])
            col += 1
            worksheet.write(row, col, sprint_row.get('Month', ''), self.formats['text'])
            col += 1
            worksheet.write(row, col, sprint_row.get('Throughput', 0), self.formats['integer'])
            col += 1
            worksheet.write(row, col, sprint_row.get('Velocity', 0), self.formats['number'])
            col += 1
            worksheet.write(row, col, sprint_row.get('Total_Estimated', 0), self.formats['number'])
            col += 1
            worksheet.write(row, col, sprint_row.get('Cycle_Time_Avg', 0), self.formats['number'])
            col += 1
            worksheet.write(row, col, sprint_row.get('Cycle_Time_Median', 0), self.formats['number'])
            col += 1
            worksheet.write(row, col, sprint_row.get('Cycle_Time_HDU_Avg', 0), self.formats['number'])
            col += 1
            worksheet.write(row, col, sprint_row.get('Cycle_Time_HDU_Median', 0), self.formats['number'])
            col += 1

            # Predictibilidad con formato
            pred = sprint_row.get('Predictability', 0)
            worksheet.write(row, col, pred, self._get_predictability_format(pred))
            col += 1

            pred_hdu = sprint_row.get('Predictability_HDU', 0)
            worksheet.write(row, col, pred_hdu, self._get_predictability_format(pred_hdu))
            col += 1

            worksheet.write(row, col, sprint_row.get('Efficiency', 0), self.formats['number'])
            col += 1

            # Retrabajo con formato
            rework = sprint_row.get('Rework', 0)
            worksheet.write(row, col, rework, self._get_rework_format(rework))
            col += 1

            rework_ach = sprint_row.get('Rework_Achieved', 0)
            worksheet.write(row, col, rework_ach, self._get_rework_format(rework_ach))
            col += 1

            rework_vel = sprint_row.get('Rework_Velocity', 0)
            worksheet.write(row, col, rework_vel, self._get_rework_format(rework_vel))
            col += 1

            worksheet.write(row, col, sprint_row.get('Total_Tasks', 0), self.formats['integer'])
            col += 1
            worksheet.write(row, col, sprint_row.get('Delivered_Tasks', 0), self.formats['integer'])
            col += 1

            # Escribir columnas de tipos de tareas dinámicamente
            for task_type in self.task_types:
                key = f'{task_type}_Delivered'
                value = sprint_row.get(key, 0)
                worksheet.write(row, col, value, self.formats['integer'])
                col += 1

            row += 1

    def _get_predictability_format(self, value: float):
        """Retorna formato según valor de predictibilidad."""
        if pd.isna(value):
            return self.formats['number']
        if value >= THRESHOLDS['predictability_good']:
            return self.formats['good']
        elif value >= THRESHOLDS['predictability_warning']:
            return self.formats['warning']
        return self.formats['danger']

    def _get_rework_format(self, value: float):
        """Retorna formato según valor de retrabajo (inverso)."""
        if pd.isna(value):
            return self.formats['number']
        if value <= THRESHOLDS['rework_good']:
            return self.formats['good']
        elif value <= THRESHOLDS['rework_warning']:
            return self.formats['warning']
        return self.formats['danger']

    def _calculate_avg_predictability_hdu(self, sprint_metrics: pd.DataFrame) -> float:
        """Calcula promedio de predictibilidad HDU."""
        if sprint_metrics.empty or 'Predictability_HDU' not in sprint_metrics.columns:
            return 0.0
        valid_values = sprint_metrics['Predictability_HDU'].dropna()
        if len(valid_values) == 0:
            return 0.0
        return valid_values.mean()


def generate_batch_report(
    results: List[TeamResult],
    output_path: str
) -> str:
    """
    Genera un reporte Excel consolidado.

    Args:
        results: Lista de TeamResult.
        output_path: Ruta de salida.

    Returns:
        Ruta del archivo generado.
    """
    generator = BatchReportGenerator(results, output_path)
    return generator.generate()
