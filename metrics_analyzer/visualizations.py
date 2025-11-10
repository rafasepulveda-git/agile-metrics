"""
Generación de visualizaciones para métricas ágiles.

Este módulo crea dashboards con múltiples gráficos de las métricas calculadas.
"""

import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import numpy as np
from config import COLORS, CHART_CONFIG


logger = logging.getLogger(__name__)

# Configurar estilo de seaborn
sns.set_style("whitegrid")
plt.rcParams['font.size'] = CHART_CONFIG['label_fontsize']


class DashboardGenerator:
    """Generador de dashboards visuales."""

    def __init__(self, sprint_metrics: pd.DataFrame, month_metrics: pd.DataFrame):
        """
        Inicializa el generador de dashboards.

        Args:
            sprint_metrics: DataFrame con métricas por sprint.
            month_metrics: DataFrame con métricas por mes.
        """
        self.sprint_metrics = sprint_metrics
        self.month_metrics = month_metrics

    def generate_sprint_dashboard(self, output_path: str) -> None:
        """
        Genera dashboard con métricas por sprint.

        Args:
            output_path: Ruta donde guardar el PNG.
        """
        logger.info("Generando dashboard de métricas por sprint...")

        fig = plt.figure(figsize=CHART_CONFIG['figsize_dashboard'])
        gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)

        # 1. Throughput por sprint
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_throughput_sprint(ax1)

        # 2. Velocity por sprint
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_velocity_sprint(ax2)

        # 3. Cycle Time promedio por sprint
        ax3 = fig.add_subplot(gs[0, 2])
        self._plot_cycle_time_sprint(ax3)

        # 4. Predictibilidad por sprint
        ax4 = fig.add_subplot(gs[1, 0])
        self._plot_predictability_sprint(ax4)

        # 5. Eficiencia por sprint
        ax5 = fig.add_subplot(gs[1, 1])
        self._plot_efficiency_sprint(ax5)

        # 6. Retrabajo por sprint
        ax6 = fig.add_subplot(gs[1, 2])
        self._plot_rework_sprint(ax6)

        # Título general
        fig.suptitle('Dashboard de Métricas por Sprint', fontsize=16, fontweight='bold')

        # Guardar
        plt.savefig(output_path, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Dashboard guardado en: {output_path}")

    def generate_month_dashboard(self, output_path: str) -> None:
        """
        Genera dashboard con métricas por mes.

        Args:
            output_path: Ruta donde guardar el PNG.
        """
        if self.month_metrics.empty:
            logger.warning("No hay datos de métricas mensuales para visualizar")
            return

        logger.info("Generando dashboard de métricas por mes...")

        fig = plt.figure(figsize=CHART_CONFIG['figsize_dashboard'])
        gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)

        # 1. Throughput por mes
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_throughput_month(ax1)

        # 2. Velocity por mes
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_velocity_month(ax2)

        # 3. Cycle Time promedio por mes
        ax3 = fig.add_subplot(gs[0, 2])
        self._plot_cycle_time_month(ax3)

        # 4. Predictibilidad por mes
        ax4 = fig.add_subplot(gs[1, 0])
        self._plot_predictability_month(ax4)

        # 5. Eficiencia por mes
        ax5 = fig.add_subplot(gs[1, 1])
        self._plot_efficiency_month(ax5)

        # 6. Retrabajo por mes
        ax6 = fig.add_subplot(gs[1, 2])
        self._plot_rework_month(ax6)

        # Título general
        fig.suptitle('Dashboard de Métricas por Mes', fontsize=16, fontweight='bold')

        # Guardar
        plt.savefig(output_path, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Dashboard guardado en: {output_path}")

    # Métodos auxiliares para gráficos por sprint

    def _plot_throughput_sprint(self, ax) -> None:
        """Gráfico de barras de throughput por sprint."""
        data = self.sprint_metrics[['Sprint', 'Throughput']].copy()

        ax.bar(data['Sprint'], data['Throughput'], color=COLORS['primary'], alpha=0.8)
        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Tareas', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Throughput por Sprint', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Agregar valores en las barras
        for i, v in enumerate(data['Throughput']):
            ax.text(i, v + 0.3, str(int(v)), ha='center', va='bottom', fontsize=9)

    def _plot_velocity_sprint(self, ax) -> None:
        """Gráfico de barras de velocity por sprint."""
        data = self.sprint_metrics[['Sprint', 'Velocity']].copy()

        ax.bar(data['Sprint'], data['Velocity'], color=COLORS['success'], alpha=0.8)
        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Puntos', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Velocity por Sprint', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Agregar valores en las barras
        for i, v in enumerate(data['Velocity']):
            ax.text(i, v + 0.5, f"{v:.1f}", ha='center', va='bottom', fontsize=9)

    def _plot_cycle_time_sprint(self, ax) -> None:
        """Gráfico de barras de cycle time por sprint."""
        data = self.sprint_metrics[['Sprint', 'Cycle_Time_Avg']].copy()
        data = data.dropna(subset=['Cycle_Time_Avg'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Cycle Time', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Cycle Time Promedio por Sprint', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        ax.bar(data['Sprint'], data['Cycle_Time_Avg'], color=COLORS['secondary'], alpha=0.8)
        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Días', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Cycle Time Promedio por Sprint', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Agregar valores en las barras
        for i, (sprint, v) in enumerate(zip(data['Sprint'], data['Cycle_Time_Avg'])):
            ax.text(i, v + 0.3, f"{v:.1f}", ha='center', va='bottom', fontsize=9)

    def _plot_predictability_sprint(self, ax) -> None:
        """Gráfico de barras de predictibilidad por sprint."""
        data = self.sprint_metrics[['Sprint', 'Predictability']].copy()
        data = data.dropna(subset=['Predictability'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Predictibilidad', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Predictibilidad por Sprint', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        # Colorear según umbrales
        colors = []
        for val in data['Predictability']:
            if val >= 70:
                colors.append(COLORS['success'])
            elif val >= 40:
                colors.append(COLORS['warning'])
            else:
                colors.append(COLORS['danger'])

        ax.bar(data['Sprint'], data['Predictability'], color=colors, alpha=0.8)
        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Porcentaje (%)', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Predictibilidad por Sprint', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])
        ax.axhline(y=70, color='green', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(y=40, color='orange', linestyle='--', alpha=0.5, linewidth=1)

        # Agregar valores en las barras
        for i, (sprint, v) in enumerate(zip(data['Sprint'], data['Predictability'])):
            ax.text(i, v + 1, f"{v:.1f}%", ha='center', va='bottom', fontsize=9)

    def _plot_efficiency_sprint(self, ax) -> None:
        """Gráfico de barras de eficiencia por sprint."""
        data = self.sprint_metrics[['Sprint', 'Efficiency']].copy()
        data = data.dropna(subset=['Efficiency'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Eficiencia', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Eficiencia por Sprint', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        ax.bar(data['Sprint'], data['Efficiency'], color=COLORS['primary'], alpha=0.8)
        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Puntos/Persona', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Eficiencia por Sprint', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Agregar valores en las barras
        for i, (sprint, v) in enumerate(zip(data['Sprint'], data['Efficiency'])):
            ax.text(i, v + 0.1, f"{v:.1f}", ha='center', va='bottom', fontsize=9)

    def _plot_rework_sprint(self, ax) -> None:
        """Gráfico de barras de retrabajo por sprint."""
        data = self.sprint_metrics[['Sprint', 'Rework']].copy()
        data = data.dropna(subset=['Rework'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Retrabajo', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Retrabajo por Sprint', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        # Colorear según umbrales (inverso: menos es mejor)
        colors = []
        for val in data['Rework']:
            if val <= 15:
                colors.append(COLORS['success'])
            elif val <= 30:
                colors.append(COLORS['warning'])
            else:
                colors.append(COLORS['danger'])

        ax.bar(data['Sprint'], data['Rework'], color=colors, alpha=0.8)
        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Porcentaje (%)', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Retrabajo por Sprint', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])
        ax.axhline(y=15, color='green', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(y=30, color='orange', linestyle='--', alpha=0.5, linewidth=1)

        # Agregar valores en las barras
        for i, (sprint, v) in enumerate(zip(data['Sprint'], data['Rework'])):
            ax.text(i, v + 0.5, f"{v:.1f}%", ha='center', va='bottom', fontsize=9)

    # Métodos auxiliares para gráficos por mes

    def _plot_throughput_month(self, ax) -> None:
        """Gráfico de barras de throughput total por mes."""
        data = self.month_metrics[['Month', 'Throughput_Total']].copy()

        ax.bar(data['Month'], data['Throughput_Total'], color=COLORS['primary'], alpha=0.8)

        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Tareas (Total)', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Throughput Total por Mes', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Agregar valores en las barras
        for i, (month, v) in enumerate(zip(data['Month'], data['Throughput_Total'])):
            ax.text(i, v + 0.3, f"{int(v)}", ha='center', va='bottom', fontsize=9)

    def _plot_velocity_month(self, ax) -> None:
        """Gráfico de barras de velocity promedio por mes."""
        data = self.month_metrics[['Month', 'Velocity_Avg']].copy()

        ax.bar(data['Month'], data['Velocity_Avg'], color=COLORS['success'], alpha=0.8)

        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Puntos (Promedio)', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Velocity Promedio por Mes', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Agregar valores en las barras
        for i, (month, v) in enumerate(zip(data['Month'], data['Velocity_Avg'])):
            ax.text(i, v + 0.5, f"{v:.1f}", ha='center', va='bottom', fontsize=9)

    def _plot_cycle_time_month(self, ax) -> None:
        """Gráfico de barras de cycle time por mes."""
        data = self.month_metrics[['Month', 'Cycle_Time_Avg']].copy()
        data = data.dropna(subset=['Cycle_Time_Avg'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Cycle Time', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Cycle Time Promedio por Mes', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        ax.bar(data['Month'], data['Cycle_Time_Avg'], color=COLORS['secondary'], alpha=0.8)
        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Días', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Cycle Time Promedio por Mes', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

    def _plot_predictability_month(self, ax) -> None:
        """Gráfico de barras de predictibilidad por mes."""
        data = self.month_metrics[['Month', 'Predictability']].copy()
        data = data.dropna(subset=['Predictability'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Predictibilidad', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Predictibilidad por Mes', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        colors = [COLORS['success'] if v >= 70 else COLORS['warning'] if v >= 40 else COLORS['danger']
                  for v in data['Predictability']]

        ax.bar(data['Month'], data['Predictability'], color=colors, alpha=0.8)
        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Porcentaje (%)', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Predictibilidad por Mes', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])
        ax.axhline(y=70, color='green', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(y=40, color='orange', linestyle='--', alpha=0.5, linewidth=1)

    def _plot_efficiency_month(self, ax) -> None:
        """Gráfico de barras de eficiencia por mes."""
        data = self.month_metrics[['Month', 'Efficiency']].copy()
        data = data.dropna(subset=['Efficiency'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Eficiencia', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Eficiencia por Mes', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        ax.bar(data['Month'], data['Efficiency'], color=COLORS['primary'], alpha=0.8)
        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Puntos/Persona', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Eficiencia por Mes', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

    def _plot_rework_month(self, ax) -> None:
        """Gráfico de barras de retrabajo por mes."""
        data = self.month_metrics[['Month', 'Rework']].copy()
        data = data.dropna(subset=['Rework'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Retrabajo', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Retrabajo por Mes', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        colors = [COLORS['success'] if v <= 15 else COLORS['warning'] if v <= 30 else COLORS['danger']
                  for v in data['Rework']]

        ax.bar(data['Month'], data['Rework'], color=colors, alpha=0.8)
        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Porcentaje (%)', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Retrabajo por Mes', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.tick_params(axis='x', rotation=45, labelsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])
        ax.axhline(y=15, color='green', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(y=30, color='orange', linestyle='--', alpha=0.5, linewidth=1)


def generate_dashboards(
    sprint_metrics: pd.DataFrame,
    month_metrics: pd.DataFrame,
    output_dir: str = '.'
) -> dict:
    """
    Genera todos los dashboards y los guarda.

    Args:
        sprint_metrics: DataFrame con métricas por sprint.
        month_metrics: DataFrame con métricas por mes.
        output_dir: Directorio donde guardar los archivos.

    Returns:
        Diccionario con las rutas de los archivos generados.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    generator = DashboardGenerator(sprint_metrics, month_metrics)

    # Generar dashboards
    sprint_dashboard_path = output_path / 'metricas_por_sprint_dashboard.png'
    month_dashboard_path = output_path / 'metricas_por_mes_dashboard.png'

    generator.generate_sprint_dashboard(str(sprint_dashboard_path))

    if not month_metrics.empty:
        generator.generate_month_dashboard(str(month_dashboard_path))

    return {
        'sprint_dashboard': str(sprint_dashboard_path),
        'month_dashboard': str(month_dashboard_path) if not month_metrics.empty else None
    }
