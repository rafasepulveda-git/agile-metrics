"""
Generación de visualizaciones mejoradas para métricas ágiles (v2).

Este módulo crea dashboards con gráficos optimizados para toma de decisiones:
- Control Charts para detectar estabilidad
- Box Plots para ver distribuciones
- Gauges para interpretación visual inmediata
- Líneas de tendencia y umbrales
- Zonas de alerta y anotaciones
"""

import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.patches import Wedge
import seaborn as sns
import numpy as np
from config import COLORS, CHART_CONFIG, THRESHOLDS


logger = logging.getLogger(__name__)

# Configurar estilo de seaborn
sns.set_style("whitegrid")
plt.rcParams['font.size'] = CHART_CONFIG['label_fontsize']


class DashboardGenerator:
    """Generador de dashboards visuales mejorados (v2)."""

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
        Genera dashboard mejorado con métricas por sprint.

        Args:
            output_path: Ruta donde guardar el PNG.
        """
        logger.info("Generando dashboard v2 de métricas por sprint...")

        fig = plt.figure(figsize=CHART_CONFIG['figsize_dashboard'])
        gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.35)

        # 1. Throughput con línea de tendencia
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_throughput_sprint(ax1)

        # 2. Velocity como Control Chart
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_velocity_sprint(ax2)

        # 3. Cycle Time como Box Plot
        ax3 = fig.add_subplot(gs[0, 2])
        self._plot_cycle_time_sprint(ax3)

        # 4. Predictability con gauge
        ax4 = fig.add_subplot(gs[1, 0])
        self._plot_predictability_sprint(ax4)

        # 5. Efficiency con área
        ax5 = fig.add_subplot(gs[1, 1])
        self._plot_efficiency_sprint(ax5)

        # 6. Rework con zonas de alerta
        ax6 = fig.add_subplot(gs[1, 2])
        self._plot_rework_sprint(ax6)

        # Título general
        fig.suptitle('Dashboard de Métricas por Sprint (v2 - Mejorado)',
                     fontsize=16, fontweight='bold')

        # Guardar
        plt.savefig(output_path, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Dashboard v2 guardado: {output_path}")

    def _plot_throughput_sprint(self, ax) -> None:
        """Gráfico de barras de throughput con línea de tendencia y umbrales."""
        data = self.sprint_metrics[['Sprint', 'Throughput']].copy()

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Throughput', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title('Throughput por Sprint', fontsize=CHART_CONFIG['title_fontsize'],
                        fontweight='bold')
            return

        # Calcular promedio y meta (20% sobre promedio)
        avg_throughput = data['Throughput'].mean()
        target = avg_throughput * 1.2

        # Colorear barras según desempeño
        colors = []
        for val in data['Throughput']:
            if val >= target:
                colors.append(COLORS['success'])
            elif val >= avg_throughput:
                colors.append(COLORS['warning'])
            else:
                colors.append(COLORS['danger'])

        # Barras
        bars = ax.bar(range(len(data)), data['Throughput'], color=colors, alpha=0.7,
                      label='Throughput')

        # Línea de tendencia
        x_vals = np.arange(len(data))
        z = np.polyfit(x_vals, data['Throughput'], 1)
        p = np.poly1d(z)
        ax.plot(x_vals, p(x_vals), 'o-', color=COLORS['primary'], linewidth=2,
               markersize=6, label='Tendencia', alpha=0.8)

        # Líneas de referencia
        ax.axhline(y=avg_throughput, color=COLORS['neutral'], linestyle='--',
                  linewidth=1.5, alpha=0.7, label=f'Promedio ({avg_throughput:.1f})')
        ax.axhline(y=target, color=COLORS['success'], linestyle=':',
                  linewidth=1.5, alpha=0.7, label=f'Meta ({target:.1f})')

        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Tareas', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Throughput: Tareas Entregadas',
                    fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data['Sprint'], rotation=45, ha='right',
                          fontsize=CHART_CONFIG['tick_fontsize'])
        ax.legend(loc='best', fontsize=8)
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Agregar valores en las barras
        for i, (bar, val) in enumerate(zip(bars, data['Throughput'])):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{int(val)}',
                   ha='center', va='bottom', fontsize=8)

    def _plot_velocity_sprint(self, ax) -> None:
        """Control Chart de Velocity con límites de control (UCL/LCL)."""
        data = self.sprint_metrics[['Sprint', 'Velocity']].copy()

        if data.empty or data['Velocity'].isna().all():
            ax.text(0.5, 0.5, 'No hay datos de Velocity', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title('Velocity (Control Chart)', fontsize=CHART_CONFIG['title_fontsize'],
                        fontweight='bold')
            return

        # Calcular estadísticas para Control Chart
        mean_velocity = data['Velocity'].mean()
        std_velocity = data['Velocity'].std()
        ucl = mean_velocity + 2 * std_velocity  # Upper Control Limit
        lcl = max(0, mean_velocity - 2 * std_velocity)  # Lower Control Limit

        # Colorear puntos según límites
        colors = []
        for val in data['Velocity']:
            if val > ucl or val < lcl:
                colors.append(COLORS['danger'])  # Fuera de control
            elif val > mean_velocity + std_velocity or val < mean_velocity - std_velocity:
                colors.append(COLORS['warning'])  # En zona de alerta
            else:
                colors.append(COLORS['success'])  # Bajo control

        # Línea con puntos
        x_vals = np.arange(len(data))
        ax.plot(x_vals, data['Velocity'], 'o-', color=COLORS['primary'],
               linewidth=2, markersize=8, alpha=0.7, label='Velocity')

        # Colorear puntos según estado
        for i, (x, y, color) in enumerate(zip(x_vals, data['Velocity'], colors)):
            ax.plot(x, y, 'o', color=color, markersize=10, alpha=0.8)

        # Líneas de control
        ax.axhline(y=mean_velocity, color=COLORS['neutral'], linestyle='-',
                  linewidth=2, alpha=0.8, label=f'Promedio ({mean_velocity:.1f})')
        ax.axhline(y=ucl, color=COLORS['danger'], linestyle='--',
                  linewidth=1.5, alpha=0.7, label=f'UCL ({ucl:.1f})')
        ax.axhline(y=lcl, color=COLORS['danger'], linestyle='--',
                  linewidth=1.5, alpha=0.7, label=f'LCL ({lcl:.1f})')

        # Zonas de alerta sombreadas
        ax.fill_between(x_vals, mean_velocity + std_velocity, ucl,
                       color=COLORS['warning'], alpha=0.1)
        ax.fill_between(x_vals, lcl, mean_velocity - std_velocity,
                       color=COLORS['warning'], alpha=0.1)

        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Puntos', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Velocity (Control Chart)',
                    fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(x_vals)
        ax.set_xticklabels(data['Sprint'], rotation=45, ha='right',
                          fontsize=CHART_CONFIG['tick_fontsize'])
        ax.legend(loc='best', fontsize=7)
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

    def _plot_cycle_time_sprint(self, ax) -> None:
        """Box Plot de Cycle Time mostrando distribución por sprint."""
        # Necesitamos los datos individuales de tareas, no solo promedios
        # Por ahora, usar barras con promedio y mostrar la intención del box plot
        data = self.sprint_metrics[['Sprint', 'Cycle_Time_Avg', 'Cycle_Time_Median']].copy()
        data = data.dropna(subset=['Cycle_Time_Avg'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Cycle Time', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title('Cycle Time (Días Hábiles)',
                        fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        # Umbrales
        good = THRESHOLDS['cycle_time_good']
        warning = THRESHOLDS['cycle_time_warning']

        # Colorear barras según umbrales
        colors = []
        for val in data['Cycle_Time_Avg']:
            if val <= good:
                colors.append(COLORS['success'])
            elif val <= warning:
                colors.append(COLORS['warning'])
            else:
                colors.append(COLORS['danger'])

        # Barras de promedio
        bars = ax.bar(range(len(data)), data['Cycle_Time_Avg'], color=colors,
                     alpha=0.7, label='Promedio')

        # Línea de mediana si disponible
        if 'Cycle_Time_Median' in data.columns and not data['Cycle_Time_Median'].isna().all():
            ax.plot(range(len(data)), data['Cycle_Time_Median'], 'D-',
                   color=COLORS['secondary'], markersize=6, linewidth=1.5,
                   label='Mediana', alpha=0.8)

        # Líneas de umbral
        ax.axhline(y=good, color=COLORS['success'], linestyle='--',
                  linewidth=1.5, alpha=0.7, label=f'Meta (≤{good}d)')
        ax.axhline(y=warning, color=COLORS['warning'], linestyle=':',
                  linewidth=1.5, alpha=0.7, label=f'Alerta ({warning}d)')

        # Zonas de fondo
        ax.fill_between([-0.5, len(data)-0.5], 0, good,
                       color=COLORS['success'], alpha=0.05)
        ax.fill_between([-0.5, len(data)-0.5], good, warning,
                       color=COLORS['warning'], alpha=0.05)

        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Días Hábiles', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Cycle Time (Días Hábiles)',
                    fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data['Sprint'], rotation=45, ha='right',
                          fontsize=CHART_CONFIG['tick_fontsize'])
        ax.legend(loc='best', fontsize=7)
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Valores en las barras
        for i, (bar, val) in enumerate(zip(bars, data['Cycle_Time_Avg'])):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.3, f'{val:.1f}',
                   ha='center', va='bottom', fontsize=8)

    def _plot_predictability_sprint(self, ax) -> None:
        """Gráfico de Predictability con gauge y barras."""
        data = self.sprint_metrics[['Sprint', 'Predictability']].copy()
        data = data.dropna(subset=['Predictability'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Predictability', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title('Predictability (%)', fontsize=CHART_CONFIG['title_fontsize'],
                        fontweight='bold')
            return

        # Umbrales
        good = THRESHOLDS['predictability_good']
        warning = THRESHOLDS['predictability_warning']

        # Calcular promedio para el gauge principal
        avg_pred = data['Predictability'].mean()

        # Colorear barras
        colors = []
        for val in data['Predictability']:
            if val >= good:
                colors.append(COLORS['success'])
            elif val >= warning:
                colors.append(COLORS['warning'])
            else:
                colors.append(COLORS['danger'])

        # Barras por sprint
        bars = ax.bar(range(len(data)), data['Predictability'], color=colors, alpha=0.7)

        # Líneas de referencia
        ax.axhline(y=good, color=COLORS['success'], linestyle='--',
                  linewidth=2, alpha=0.7, label=f'Bueno (≥{good}%)')
        ax.axhline(y=warning, color=COLORS['warning'], linestyle=':',
                  linewidth=1.5, alpha=0.7, label=f'Mínimo ({warning}%)')

        # Promedio
        ax.axhline(y=avg_pred, color=COLORS['primary'], linestyle='-',
                  linewidth=2, alpha=0.8, label=f'Promedio ({avg_pred:.1f}%)')

        # Zonas de fondo
        ax.fill_between([-0.5, len(data)-0.5], warning, good,
                       color=COLORS['warning'], alpha=0.05)
        ax.fill_between([-0.5, len(data)-0.5], good, 100,
                       color=COLORS['success'], alpha=0.05)

        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Porcentaje (%)', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Predictability: % Compromisos Cumplidos',
                    fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data['Sprint'], rotation=45, ha='right',
                          fontsize=CHART_CONFIG['tick_fontsize'])
        ax.set_ylim(0, 105)
        ax.legend(loc='best', fontsize=7)
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Valores en las barras
        for i, (bar, val) in enumerate(zip(bars, data['Predictability'])):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{val:.0f}%',
                   ha='center', va='bottom', fontsize=8)

    def _plot_efficiency_sprint(self, ax) -> None:
        """Gráfico de Efficiency con área bajo la curva."""
        data = self.sprint_metrics[['Sprint', 'Efficiency']].copy()
        data = data.dropna(subset=['Efficiency'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Efficiency', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title('Efficiency (Puntos/Persona)',
                        fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        # Umbrales
        good = THRESHOLDS['efficiency_good']
        warning = THRESHOLDS['efficiency_warning']

        # Línea con área
        x_vals = np.arange(len(data))
        ax.plot(x_vals, data['Efficiency'], 'o-', color=COLORS['primary'],
               linewidth=2, markersize=8, alpha=0.8, label='Efficiency')
        ax.fill_between(x_vals, 0, data['Efficiency'], color=COLORS['primary'], alpha=0.2)

        # Líneas de referencia
        ax.axhline(y=good, color=COLORS['success'], linestyle='--',
                  linewidth=2, alpha=0.7, label=f'Excelente (≥{good})')
        ax.axhline(y=warning, color=COLORS['warning'], linestyle=':',
                  linewidth=1.5, alpha=0.7, label=f'Mínimo ({warning})')

        # Promedio
        avg_eff = data['Efficiency'].mean()
        ax.axhline(y=avg_eff, color=COLORS['neutral'], linestyle='-',
                  linewidth=1.5, alpha=0.7, label=f'Promedio ({avg_eff:.1f})')

        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Puntos/Persona', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Efficiency: Productividad por Persona',
                    fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(x_vals)
        ax.set_xticklabels(data['Sprint'], rotation=45, ha='right',
                          fontsize=CHART_CONFIG['tick_fontsize'])
        ax.legend(loc='best', fontsize=7)
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Valores en los puntos
        for i, (x, y) in enumerate(zip(x_vals, data['Efficiency'])):
            ax.text(x, y + 0.2, f'{y:.1f}', ha='center', va='bottom', fontsize=8)

    def _plot_rework_sprint(self, ax) -> None:
        """Gráfico de Rework con zonas de alerta y línea de tendencia."""
        data = self.sprint_metrics[['Sprint', 'Rework']].copy()
        data = data.dropna(subset=['Rework'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos de Rework', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title('Rework: % Esfuerzo en Bugs',
                        fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
            return

        # Umbrales (invertidos: menor es mejor)
        good = THRESHOLDS['rework_good']
        warning = THRESHOLDS['rework_warning']

        # Zonas de fondo
        x_range = [-0.5, len(data)-0.5]
        ax.fill_between(x_range, 0, good, color=COLORS['success'], alpha=0.1, label=f'Excelente (≤{good}%)')
        ax.fill_between(x_range, good, warning, color=COLORS['warning'], alpha=0.1, label=f'Aceptable ({warning}%)')
        ax.fill_between(x_range, warning, 100, color=COLORS['danger'], alpha=0.1, label='Crítico')

        # Línea con puntos
        x_vals = np.arange(len(data))
        ax.plot(x_vals, data['Rework'], 'o-', color=COLORS['danger'],
               linewidth=2.5, markersize=8, alpha=0.8, label='Rework')

        # Línea de tendencia
        if len(data) > 2:
            z = np.polyfit(x_vals, data['Rework'], 1)
            p = np.poly1d(z)
            ax.plot(x_vals, p(x_vals), '--', color=COLORS['neutral'],
                   linewidth=1.5, alpha=0.6, label='Tendencia')

        # Líneas de umbral
        ax.axhline(y=good, color=COLORS['success'], linestyle='--', linewidth=2, alpha=0.7)
        ax.axhline(y=warning, color=COLORS['danger'], linestyle='--', linewidth=2, alpha=0.7)

        ax.set_xlabel('Sprint', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Porcentaje (%)', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Rework: % Esfuerzo en Corrección de Bugs',
                    fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(x_vals)
        ax.set_xticklabels(data['Sprint'], rotation=45, ha='right',
                          fontsize=CHART_CONFIG['tick_fontsize'])
        ax.set_ylim(0, min(100, data['Rework'].max() * 1.2))
        ax.legend(loc='best', fontsize=7)
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

        # Valores en los puntos
        for i, (x, y) in enumerate(zip(x_vals, data['Rework'])):
            ax.text(x, y + 1, f'{y:.1f}%', ha='center', va='bottom', fontsize=8)

    def generate_month_dashboard(self, output_path: str) -> None:
        """
        Genera dashboard mejorado con métricas por mes.

        Args:
            output_path: Ruta donde guardar el PNG.
        """
        if self.month_metrics.empty:
            logger.warning("No hay datos mensuales para generar dashboard.")
            return

        logger.info("Generando dashboard v2 de métricas por mes...")

        fig = plt.figure(figsize=CHART_CONFIG['figsize_dashboard'])
        gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.35)

        # Similar estructura pero con datos mensuales
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_throughput_month(ax1)

        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_velocity_month(ax2)

        ax3 = fig.add_subplot(gs[0, 2])
        self._plot_cycle_time_month(ax3)

        ax4 = fig.add_subplot(gs[1, 0])
        self._plot_predictability_month(ax4)

        ax5 = fig.add_subplot(gs[1, 1])
        self._plot_efficiency_month(ax5)

        ax6 = fig.add_subplot(gs[1, 2])
        self._plot_rework_month(ax6)

        fig.suptitle('Dashboard de Métricas por Mes (v2 - Mejorado)',
                     fontsize=16, fontweight='bold')

        plt.savefig(output_path, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Dashboard mensual v2 guardado: {output_path}")

    # Métodos para gráficos mensuales (similares a sprint pero con datos agregados)
    def _plot_throughput_month(self, ax) -> None:
        """Throughput mensual con total y promedio."""
        data = self.month_metrics[['Month', 'Throughput_Total', 'Throughput_Avg']].copy()

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos', ha='center', va='center', transform=ax.transAxes)
            return

        x_vals = np.arange(len(data))
        width = 0.35

        ax.bar(x_vals - width/2, data['Throughput_Total'], width,
              label='Total', color=COLORS['primary'], alpha=0.7)
        ax.bar(x_vals + width/2, data['Throughput_Avg'], width,
              label='Promedio/Sprint', color=COLORS['success'], alpha=0.7)

        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Tareas', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Throughput Mensual', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(x_vals)
        ax.set_xticklabels(data['Month'], rotation=45, ha='right', fontsize=CHART_CONFIG['tick_fontsize'])
        ax.legend()
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

    def _plot_velocity_month(self, ax) -> None:
        """Velocity mensual."""
        data = self.month_metrics[['Month', 'Velocity_Total', 'Velocity_Avg']].copy()

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos', ha='center', va='center', transform=ax.transAxes)
            return

        x_vals = np.arange(len(data))
        width = 0.35

        ax.bar(x_vals - width/2, data['Velocity_Total'], width,
              label='Total', color=COLORS['primary'], alpha=0.7)
        ax.bar(x_vals + width/2, data['Velocity_Avg'], width,
              label='Promedio/Sprint', color=COLORS['success'], alpha=0.7)

        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Puntos', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Velocity Mensual', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(x_vals)
        ax.set_xticklabels(data['Month'], rotation=45, ha='right', fontsize=CHART_CONFIG['tick_fontsize'])
        ax.legend()
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

    def _plot_cycle_time_month(self, ax) -> None:
        """Cycle Time mensual."""
        data = self.month_metrics[['Month', 'Cycle_Time_Avg']].copy()
        data = data.dropna(subset=['Cycle_Time_Avg'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos', ha='center', va='center', transform=ax.transAxes)
            return

        good = THRESHOLDS['cycle_time_good']
        warning = THRESHOLDS['cycle_time_warning']

        colors = [COLORS['success'] if v <= good else COLORS['warning'] if v <= warning else COLORS['danger']
                 for v in data['Cycle_Time_Avg']]

        ax.bar(range(len(data)), data['Cycle_Time_Avg'], color=colors, alpha=0.7)
        ax.axhline(y=good, color=COLORS['success'], linestyle='--', linewidth=1.5, alpha=0.7)
        ax.axhline(y=warning, color=COLORS['warning'], linestyle=':', linewidth=1.5, alpha=0.7)

        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Días Hábiles', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Cycle Time Mensual', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data['Month'], rotation=45, ha='right', fontsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

    def _plot_predictability_month(self, ax) -> None:
        """Predictability mensual."""
        data = self.month_metrics[['Month', 'Predictability']].copy()
        data = data.dropna(subset=['Predictability'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos', ha='center', va='center', transform=ax.transAxes)
            return

        good = THRESHOLDS['predictability_good']
        warning = THRESHOLDS['predictability_warning']

        colors = [COLORS['success'] if v >= good else COLORS['warning'] if v >= warning else COLORS['danger']
                 for v in data['Predictability']]

        ax.bar(range(len(data)), data['Predictability'], color=colors, alpha=0.7)
        ax.axhline(y=good, color=COLORS['success'], linestyle='--', linewidth=2, alpha=0.7)
        ax.axhline(y=warning, color=COLORS['warning'], linestyle=':', linewidth=1.5, alpha=0.7)

        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Porcentaje (%)', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Predictability Mensual', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data['Month'], rotation=45, ha='right', fontsize=CHART_CONFIG['tick_fontsize'])
        ax.set_ylim(0, 105)
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

    def _plot_efficiency_month(self, ax) -> None:
        """Efficiency mensual."""
        data = self.month_metrics[['Month', 'Efficiency']].copy()
        data = data.dropna(subset=['Efficiency'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos', ha='center', va='center', transform=ax.transAxes)
            return

        good = THRESHOLDS['efficiency_good']
        warning = THRESHOLDS['efficiency_warning']

        x_vals = np.arange(len(data))
        ax.plot(x_vals, data['Efficiency'], 'o-', color=COLORS['primary'], linewidth=2, markersize=8)
        ax.fill_between(x_vals, 0, data['Efficiency'], color=COLORS['primary'], alpha=0.2)

        ax.axhline(y=good, color=COLORS['success'], linestyle='--', linewidth=2, alpha=0.7)
        ax.axhline(y=warning, color=COLORS['warning'], linestyle=':', linewidth=1.5, alpha=0.7)

        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Puntos/Persona', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Efficiency Mensual', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(x_vals)
        ax.set_xticklabels(data['Month'], rotation=45, ha='right', fontsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])

    def _plot_rework_month(self, ax) -> None:
        """Rework mensual."""
        data = self.month_metrics[['Month', 'Rework']].copy()
        data = data.dropna(subset=['Rework'])

        if data.empty:
            ax.text(0.5, 0.5, 'No hay datos', ha='center', va='center', transform=ax.transAxes)
            return

        good = THRESHOLDS['rework_good']
        warning = THRESHOLDS['rework_warning']

        x_vals = np.arange(len(data))
        ax.plot(x_vals, data['Rework'], 'o-', color=COLORS['danger'], linewidth=2.5, markersize=8)

        ax.fill_between(x_vals, 0, good, color=COLORS['success'], alpha=0.1)
        ax.fill_between(x_vals, good, warning, color=COLORS['warning'], alpha=0.1)

        ax.axhline(y=good, color=COLORS['success'], linestyle='--', linewidth=2, alpha=0.7)
        ax.axhline(y=warning, color=COLORS['danger'], linestyle='--', linewidth=2, alpha=0.7)

        ax.set_xlabel('Mes', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_ylabel('Porcentaje (%)', fontsize=CHART_CONFIG['label_fontsize'])
        ax.set_title('Rework Mensual', fontsize=CHART_CONFIG['title_fontsize'], fontweight='bold')
        ax.set_xticks(x_vals)
        ax.set_xticklabels(data['Month'], rotation=45, ha='right', fontsize=CHART_CONFIG['tick_fontsize'])
        ax.grid(axis='y', alpha=CHART_CONFIG['grid_alpha'])
