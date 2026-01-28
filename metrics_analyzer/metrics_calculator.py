"""
Cálculo de métricas de performance ágil.

Este módulo calcula todas las métricas requeridas a nivel de sprint y mes,
incluyendo Throughput, Velocity, Cycle Time, Predictibilidad, Eficiencia y Retrabajo.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from utils import get_task_types_to_track


logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculador de métricas ágiles."""

    def __init__(self, df: pd.DataFrame, team_size: int):
        """
        Inicializa el calculador de métricas.

        Args:
            df: DataFrame procesado con los datos.
            team_size: Número de miembros del equipo.
        """
        self.df = df.copy()
        self.team_size = team_size
        self.sprint_metrics: Optional[pd.DataFrame] = None
        self.month_metrics: Optional[pd.DataFrame] = None

        # Determinar tipos de tareas a trackear (dinámico basado en datos y configuración)
        self.task_types_to_track = get_task_types_to_track(df, 'Tipo Tarea')

        logger.info(f"Calculador inicializado con {len(df)} tareas y equipo de {team_size} personas")
        logger.info(f"Tipos de tareas detectados: {', '.join(self.task_types_to_track)}")

    def calculate_all_metrics(self) -> None:
        """Calcula todas las métricas (sprint y mes)."""
        logger.info("Calculando métricas por sprint...")
        self.sprint_metrics = self._calculate_sprint_metrics()

        logger.info("Calculando métricas por mes...")
        self.month_metrics = self._calculate_month_metrics()

        logger.info("Cálculo de métricas completado")

    def _calculate_sprint_metrics(self) -> pd.DataFrame:
        """
        Calcula métricas por sprint unificado.

        Sprints con el mismo número base se agrupan juntos.
        Ejemplo: 'Sprint 07 FIDSIN' y 'Sprint 07 Auto3P' se unifican como 'Sprint 7'.

        Returns:
            DataFrame con métricas por sprint unificado.
        """
        # Usar Sprint_Unified en lugar de Sprint para agrupar
        unified_sprints = sorted(self.df['Sprint_Unified'].unique())
        metrics = []

        for unified_sprint in unified_sprints:
            # Obtener todas las tareas con el mismo sprint unificado
            sprint_data = self.df[self.df['Sprint_Unified'] == unified_sprint]

            # Obtener nombres originales de sprints que se están unificando
            original_sprints = sprint_data['Sprint'].unique()

            sprint_metrics = self._calculate_single_sprint_metrics(
                unified_sprint,
                sprint_data,
                original_sprints
            )
            metrics.append(sprint_metrics)

        df_metrics = pd.DataFrame(metrics)
        return df_metrics

    def _calculate_single_sprint_metrics(
        self,
        sprint: str,
        sprint_data: pd.DataFrame,
        original_sprints: list = None
    ) -> Dict:
        """
        Calcula métricas para un sprint unificado.

        Args:
            sprint: Nombre del sprint unificado.
            sprint_data: DataFrame filtrado para el sprint (puede incluir múltiples sprints originales).
            original_sprints: Lista de nombres originales de sprints que se unifican.

        Returns:
            Diccionario con todas las métricas del sprint.
        """
        # Tareas entregadas (incluye todas las tareas, originales y copias)
        delivered = sprint_data[sprint_data['Is_Delivered']]

        # 1. THROUGHPUT: Número de tareas entregadas
        throughput = len(delivered)

        # 2. VELOCITY: Suma de:
        #    - Estimación Original de tareas que llegaron al DoD (entregadas)
        #    - Puntos Logrados de tareas que NO llegaron al DoD (no entregadas)
        not_delivered = sprint_data[~sprint_data['Is_Delivered']]

        velocity_delivered = delivered['Estimación Original'].sum()
        velocity_not_delivered = not_delivered['Puntos Logrados'].fillna(0).sum()
        velocity = velocity_delivered + velocity_not_delivered

        # 3. CYCLE TIME: Promedio y mediana
        cycle_times = delivered['Cycle_Time_Days'].dropna()
        cycle_time_avg = cycle_times.mean() if len(cycle_times) > 0 else np.nan
        cycle_time_median = cycle_times.median() if len(cycle_times) > 0 else np.nan

        # 3b. CYCLE TIME HDU: Solo tareas HDU
        hdu_delivered = delivered[delivered['Tipo Tarea'] == 'HDU']
        cycle_times_hdu = hdu_delivered['Cycle_Time_Days'].dropna()
        cycle_time_hdu_avg = cycle_times_hdu.mean() if len(cycle_times_hdu) > 0 else np.nan
        cycle_time_hdu_median = cycle_times_hdu.median() if len(cycle_times_hdu) > 0 else np.nan

        # 4. PREDICTIBILIDAD: Puntos entregados / Total puntos comprometidos
        # Puntos comprometidos = Estimación Original de TODAS las tareas del sprint
        # Puntos entregados = Estimación Original de tareas completadas
        committed_points = sprint_data['Estimación Original'].sum()
        delivered_points = delivered['Estimación Original'].sum()

        if committed_points > 0:
            predictability = (delivered_points / committed_points) * 100
        else:
            predictability = np.nan

        # 4b. PREDICTIBILIDAD HDU: Solo considerando tareas HDU
        hdu_tasks = sprint_data[sprint_data['Tipo Tarea'] == 'HDU']
        hdu_delivered = hdu_tasks[hdu_tasks['Is_Delivered']]
        committed_points_hdu = hdu_tasks['Estimación Original'].sum()
        delivered_points_hdu = hdu_delivered['Estimación Original'].sum()

        if committed_points_hdu > 0:
            predictability_hdu = (delivered_points_hdu / committed_points_hdu) * 100
        else:
            predictability_hdu = np.nan

        # TOTAL ESTIMADO: Suma de Estimación Original de todas las tareas del sprint
        total_estimated = sprint_data['Estimación Original'].sum()

        # 5. EFICIENCIA: Velocity / Miembros del equipo
        efficiency = velocity / self.team_size if self.team_size > 0 else np.nan

        # 6. RETRABAJO (basado en Estimación Original): Puntos estimados de bugs / Total puntos estimados entregados
        bugs_delivered = delivered[delivered['Is_Bug']]
        bug_points_estimated = bugs_delivered['Estimación Original'].sum()
        total_points_estimated = delivered['Estimación Original'].sum()

        if total_points_estimated > 0:
            rework = (bug_points_estimated / total_points_estimated) * 100
        else:
            rework = np.nan

        # 6b. RETRABAJO SOBRE VELOCITY (basado en Estimación Original):
        # Puntos de historia de bugs entregados / Velocity
        # Usa Estimación Original de bugs entregados dividido por el velocity total del sprint
        if velocity > 0:
            rework_achieved = (bug_points_estimated / velocity) * 100
        else:
            rework_achieved = np.nan

        # 6c. RETRABAJO SOBRE VELOCITY (basado en Puntos Logrados/Efectivos):
        # Puntos logrados o entregados de bugs / Velocity
        # Para cada bug, usa Puntos Logrados si existe, sino Estimación Original
        bug_points_effective = 0
        for _, bug_row in bugs_delivered.iterrows():
            if pd.notna(bug_row['Puntos Logrados']):
                bug_points_effective += bug_row['Puntos Logrados']
            else:
                bug_points_effective += bug_row['Estimación Original']

        if velocity > 0:
            rework_velocity = (bug_points_effective / velocity) * 100
        else:
            rework_velocity = np.nan

        # Obtener el mes si está disponible
        month = sprint_data['Month'].iloc[0] if 'Month' in sprint_data.columns else None

        # Crear descripción de sprints originales si hay múltiples
        original_sprints_str = ', '.join(sorted(original_sprints)) if original_sprints is not None and len(original_sprints) > 1 else None

        # Conteo dinámico de tareas entregadas por tipo
        task_type_counts = {}
        for task_type in self.task_types_to_track:
            count = len(delivered[delivered['Tipo Tarea'] == task_type])
            task_type_counts[f'{task_type}_Delivered'] = count

        # Construir diccionario de retorno
        result = {
            'Sprint': sprint,
            'Original_Sprints': original_sprints_str,  # Nuevo campo
            'Month': month,
            'Throughput': throughput,
            'Velocity': velocity,
            'Total_Estimated': total_estimated,
            'Cycle_Time_Avg': cycle_time_avg,
            'Cycle_Time_Median': cycle_time_median,
            'Cycle_Time_HDU_Avg': cycle_time_hdu_avg,
            'Cycle_Time_HDU_Median': cycle_time_hdu_median,
            'Predictability': predictability,
            'Predictability_HDU': predictability_hdu,
            'Efficiency': efficiency,
            'Rework': rework,
            'Rework_Achieved': rework_achieved,
            'Rework_Velocity': rework_velocity,
            'Total_Tasks': len(sprint_data),
            'Delivered_Tasks': throughput,
        }

        # Agregar conteos de tipos de tareas dinámicamente
        result.update(task_type_counts)

        # Agregar campos adicionales
        result.update({
            'Bug_Points_Estimated': bug_points_estimated,
            'Total_Points_Estimated': total_points_estimated,
            'Committed_Points': committed_points,
            'Delivered_Points': delivered_points,
            'Committed_Points_HDU': committed_points_hdu,
            'Delivered_Points_HDU': delivered_points_hdu
        })

        return result

    def _calculate_month_metrics(self) -> pd.DataFrame:
        """
        Calcula métricas por mes.

        Returns:
            DataFrame con métricas por mes.
        """
        if 'Month' not in self.df.columns or self.df['Month'].isna().all():
            logger.warning("No hay mapeo de meses disponible")
            return pd.DataFrame()

        months = sorted(self.df['Month'].dropna().unique())
        metrics = []

        for month in months:
            month_data = self.df[self.df['Month'] == month]
            month_metrics = self._calculate_single_month_metrics(month, month_data)
            metrics.append(month_metrics)

        df_metrics = pd.DataFrame(metrics)
        return df_metrics

    def _calculate_single_month_metrics(self, month: str, month_data: pd.DataFrame) -> Dict:
        """
        Calcula métricas para un mes específico usando sprints unificados.

        Args:
            month: Nombre del mes.
            month_data: DataFrame filtrado para el mes.

        Returns:
            Diccionario con todas las métricas del mes.
        """
        # Obtener sprints UNIFICADOS del mes
        unified_sprints_in_month = month_data['Sprint_Unified'].unique()
        num_sprints = len(unified_sprints_in_month)

        # Tareas entregadas (incluye todas las tareas)
        delivered = month_data[month_data['Is_Delivered']]

        # 1. THROUGHPUT: Total de tareas entregadas en el mes
        throughput_total = len(delivered)
        throughput_avg = throughput_total / num_sprints if num_sprints > 0 else np.nan

        # 2. VELOCITY: Promedio de velocity de los sprints UNIFICADOS del mes
        sprint_velocities = []
        for unified_sprint in unified_sprints_in_month:
            sprint_data = month_data[month_data['Sprint_Unified'] == unified_sprint]
            sprint_delivered = sprint_data[sprint_data['Is_Delivered']]
            sprint_not_delivered = sprint_data[~sprint_data['Is_Delivered']]

            # Velocity = Estimación Original de entregadas + Puntos Logrados de no entregadas
            velocity_delivered = sprint_delivered['Estimación Original'].sum()
            velocity_not_delivered = sprint_not_delivered['Puntos Logrados'].fillna(0).sum()
            velocity = velocity_delivered + velocity_not_delivered

            sprint_velocities.append(velocity)

        velocity_avg = np.mean(sprint_velocities) if sprint_velocities else np.nan
        velocity_total = sum(sprint_velocities) if sprint_velocities else 0

        # 3. CYCLE TIME: Promedio de los promedios de cada sprint UNIFICADO
        sprint_cycle_times = []
        for unified_sprint in unified_sprints_in_month:
            sprint_data = month_data[month_data['Sprint_Unified'] == unified_sprint]
            sprint_delivered = sprint_data[sprint_data['Is_Delivered']]

            cycle_times = sprint_delivered['Cycle_Time_Days'].dropna()
            if len(cycle_times) > 0:
                sprint_avg = cycle_times.mean()
                sprint_cycle_times.append(sprint_avg)

        cycle_time_avg = np.mean(sprint_cycle_times) if sprint_cycle_times else np.nan

        # Mediana calculada sobre todas las tareas del mes (no cambia)
        all_cycle_times = delivered['Cycle_Time_Days'].dropna()
        cycle_time_median = all_cycle_times.median() if len(all_cycle_times) > 0 else np.nan

        # 3b. CYCLE TIME HDU: Promedio de los promedios de cada sprint (solo HDU)
        sprint_cycle_times_hdu = []
        for unified_sprint in unified_sprints_in_month:
            sprint_data = month_data[month_data['Sprint_Unified'] == unified_sprint]
            sprint_delivered = sprint_data[sprint_data['Is_Delivered']]
            hdu_delivered = sprint_delivered[sprint_delivered['Tipo Tarea'] == 'HDU']

            cycle_times_hdu = hdu_delivered['Cycle_Time_Days'].dropna()
            if len(cycle_times_hdu) > 0:
                sprint_avg_hdu = cycle_times_hdu.mean()
                sprint_cycle_times_hdu.append(sprint_avg_hdu)

        cycle_time_hdu_avg = np.mean(sprint_cycle_times_hdu) if sprint_cycle_times_hdu else np.nan

        # Mediana HDU calculada sobre todas las tareas HDU del mes
        hdu_delivered_all = delivered[delivered['Tipo Tarea'] == 'HDU']
        all_cycle_times_hdu = hdu_delivered_all['Cycle_Time_Days'].dropna()
        cycle_time_hdu_median = all_cycle_times_hdu.median() if len(all_cycle_times_hdu) > 0 else np.nan

        # 4. PREDICTIBILIDAD: Promedio de predictibilidad de sprints UNIFICADOS del mes
        sprint_predictabilities = []
        for unified_sprint in unified_sprints_in_month:
            sprint_data = month_data[month_data['Sprint_Unified'] == unified_sprint]
            sprint_delivered = sprint_data[sprint_data['Is_Delivered']]

            # Comprometido = TODAS las tareas del sprint unificado
            committed = sprint_data['Estimación Original'].sum()
            # Entregado = Tareas completadas
            delivered_pts = sprint_delivered['Estimación Original'].sum()

            if committed > 0:
                pred = (delivered_pts / committed) * 100
                sprint_predictabilities.append(pred)

        predictability = np.mean(sprint_predictabilities) if sprint_predictabilities else np.nan

        # 4b. PREDICTIBILIDAD HDU: Promedio de predictibilidad HDU de sprints UNIFICADOS del mes
        sprint_predictabilities_hdu = []
        for unified_sprint in unified_sprints_in_month:
            sprint_data = month_data[month_data['Sprint_Unified'] == unified_sprint]
            hdu_tasks = sprint_data[sprint_data['Tipo Tarea'] == 'HDU']
            hdu_delivered = hdu_tasks[hdu_tasks['Is_Delivered']]

            # Comprometido HDU = TODAS las tareas HDU del sprint unificado
            committed_hdu = hdu_tasks['Estimación Original'].sum()
            # Entregado HDU = Tareas HDU completadas
            delivered_pts_hdu = hdu_delivered['Estimación Original'].sum()

            if committed_hdu > 0:
                pred_hdu = (delivered_pts_hdu / committed_hdu) * 100
                sprint_predictabilities_hdu.append(pred_hdu)

        predictability_hdu = np.mean(sprint_predictabilities_hdu) if sprint_predictabilities_hdu else np.nan

        # TOTAL ESTIMADO: Suma y promedio de Estimación Original por mes
        sprint_totals_estimated = []
        for unified_sprint in unified_sprints_in_month:
            sprint_data = month_data[month_data['Sprint_Unified'] == unified_sprint]
            total_est = sprint_data['Estimación Original'].sum()
            sprint_totals_estimated.append(total_est)

        total_estimated_total = sum(sprint_totals_estimated) if sprint_totals_estimated else 0
        total_estimated_avg = np.mean(sprint_totals_estimated) if sprint_totals_estimated else np.nan

        # 5. EFICIENCIA: Promedio de eficiencia de sprints del mes
        efficiency_avg = velocity_avg / self.team_size if self.team_size > 0 else np.nan

        # 6. RETRABAJO (basado en Estimación Original): Puntos estimados de bugs / Total puntos estimados entregados
        bugs_delivered = delivered[delivered['Is_Bug']]
        bug_points_estimated = bugs_delivered['Estimación Original'].sum()
        total_points_estimated = delivered['Estimación Original'].sum()

        if total_points_estimated > 0:
            rework = (bug_points_estimated / total_points_estimated) * 100
        else:
            rework = np.nan

        # 6b. RETRABAJO SOBRE VELOCITY (basado en Estimación Original):
        # Puntos de historia de bugs entregados / Velocity total del mes
        # Usa Estimación Original de bugs entregados dividido por el velocity total del mes
        if velocity_total > 0:
            rework_achieved = (bug_points_estimated / velocity_total) * 100
        else:
            rework_achieved = np.nan

        # 6c. RETRABAJO SOBRE VELOCITY (basado en Puntos Logrados/Efectivos):
        # Puntos logrados o entregados de bugs / Velocity
        # Para cada bug, usa Puntos Logrados si existe, sino Estimación Original
        bug_points_effective = 0
        for _, bug_row in bugs_delivered.iterrows():
            if pd.notna(bug_row['Puntos Logrados']):
                bug_points_effective += bug_row['Puntos Logrados']
            else:
                bug_points_effective += bug_row['Estimación Original']

        if velocity_total > 0:
            rework_velocity = (bug_points_effective / velocity_total) * 100
        else:
            rework_velocity = np.nan

        return {
            'Month': month,
            'Num_Sprints': num_sprints,
            'Sprints': ', '.join(sorted(unified_sprints_in_month)),  # Mostrar sprints unificados
            'Throughput_Total': throughput_total,
            'Throughput_Avg': throughput_avg,
            'Velocity_Total': velocity_total,
            'Velocity_Avg': velocity_avg,
            'Total_Estimated_Total': total_estimated_total,
            'Total_Estimated_Avg': total_estimated_avg,
            'Cycle_Time_Avg': cycle_time_avg,
            'Cycle_Time_Median': cycle_time_median,
            'Cycle_Time_HDU_Avg': cycle_time_hdu_avg,
            'Cycle_Time_HDU_Median': cycle_time_hdu_median,
            'Predictability': predictability,
            'Predictability_HDU': predictability_hdu,
            'Efficiency': efficiency_avg,
            'Rework': rework,
            'Rework_Achieved': rework_achieved,
            'Rework_Velocity': rework_velocity,
            'Total_Tasks': len(month_data),
            'Delivered_Tasks': throughput_total
        }

    def get_sprint_metrics(self) -> pd.DataFrame:
        """
        Obtiene las métricas por sprint.

        Returns:
            DataFrame con métricas por sprint.

        Raises:
            ValueError: Si no se han calculado las métricas.
        """
        if self.sprint_metrics is None:
            raise ValueError("Las métricas no han sido calculadas. Ejecute calculate_all_metrics() primero.")

        return self.sprint_metrics.copy()

    def get_month_metrics(self) -> pd.DataFrame:
        """
        Obtiene las métricas por mes.

        Returns:
            DataFrame con métricas por mes.

        Raises:
            ValueError: Si no se han calculado las métricas.
        """
        if self.month_metrics is None:
            raise ValueError("Las métricas no han sido calculadas. Ejecute calculate_all_metrics() primero.")

        return self.month_metrics.copy()

    def get_summary(self) -> Dict:
        """
        Obtiene un resumen ejecutivo de las métricas.

        Returns:
            Diccionario con resumen de métricas.
        """
        if self.sprint_metrics is None:
            raise ValueError("Las métricas no han sido calculadas.")

        # Métricas generales
        total_sprints = len(self.sprint_metrics)
        total_delivered = self.sprint_metrics['Throughput'].sum()
        avg_throughput = self.sprint_metrics['Throughput'].mean()
        avg_velocity = self.sprint_metrics['Velocity'].mean()
        avg_cycle_time = self.sprint_metrics['Cycle_Time_Avg'].mean()
        avg_predictability = self.sprint_metrics['Predictability'].mean()
        avg_efficiency = self.sprint_metrics['Efficiency'].mean()
        avg_rework = self.sprint_metrics['Rework'].mean()
        avg_rework_achieved = self.sprint_metrics['Rework_Achieved'].mean()
        avg_rework_velocity = self.sprint_metrics['Rework_Velocity'].mean()

        # Mejor y peor sprint por throughput
        best_sprint = self.sprint_metrics.loc[self.sprint_metrics['Throughput'].idxmax()]
        worst_sprint = self.sprint_metrics.loc[self.sprint_metrics['Throughput'].idxmin()]

        # Conteo dinámico de tareas entregadas por tipo
        delivered_tasks = self.df[self.df['Is_Delivered']]
        task_type_summary = {}
        for task_type in self.task_types_to_track:
            count = len(delivered_tasks[delivered_tasks['Tipo Tarea'] == task_type])
            task_type_summary[f'{task_type.lower()}_delivered'] = count

        # Construir diccionario base
        result = {
            'total_sprints': total_sprints,
            'total_delivered': int(total_delivered),
            'avg_throughput': avg_throughput,
            'avg_velocity': avg_velocity,
            'avg_cycle_time': avg_cycle_time,
            'avg_predictability': avg_predictability,
            'avg_efficiency': avg_efficiency,
            'avg_rework': avg_rework,
            'avg_rework_achieved': avg_rework_achieved,
            'avg_rework_velocity': avg_rework_velocity,
            'best_sprint': {
                'name': best_sprint['Sprint'],
                'throughput': int(best_sprint['Throughput'])
            },
            'worst_sprint': {
                'name': worst_sprint['Sprint'],
                'throughput': int(worst_sprint['Throughput'])
            },
            'team_size': self.team_size
        }

        # Agregar conteos de tipos de tareas
        result.update(task_type_summary)

        return result

    def print_summary(self) -> None:
        """Imprime un resumen ejecutivo de las métricas."""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("RESUMEN EJECUTIVO DE MÉTRICAS")
        print("=" * 60)
        print(f"\nTamaño del equipo: {summary['team_size']} personas")
        print(f"Sprints analizados: {summary['total_sprints']}")
        print(f"Tareas entregadas: {summary['total_delivered']}")
        print(f"\nPROMEDIOS:")
        print(f"  • Throughput: {summary['avg_throughput']:.1f} tareas/sprint")
        print(f"  • Velocity: {summary['avg_velocity']:.1f} puntos/sprint")
        print(f"  • Cycle Time: {summary['avg_cycle_time']:.1f} días")
        print(f"  • Predictibilidad: {summary['avg_predictability']:.1f}%")
        print(f"  • Eficiencia: {summary['avg_efficiency']:.1f} puntos/persona")
        print(f"  • Retrabajo: {summary['avg_rework']:.1f}%")
        print(f"\nMEJOR SPRINT: {summary['best_sprint']['name']} ({summary['best_sprint']['throughput']} tareas)")
        print(f"PEOR SPRINT: {summary['worst_sprint']['name']} ({summary['worst_sprint']['throughput']} tareas)")


def calculate_metrics(
    df: pd.DataFrame,
    team_size: int,
    verbose: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Función de conveniencia para calcular métricas en un solo paso.

    Args:
        df: DataFrame procesado.
        team_size: Número de miembros del equipo.
        verbose: Si es True, imprime resumen.

    Returns:
        Tupla (sprint_metrics, month_metrics).
    """
    calculator = MetricsCalculator(df, team_size)
    calculator.calculate_all_metrics()

    if verbose:
        calculator.print_summary()

    return calculator.get_sprint_metrics(), calculator.get_month_metrics()
