"""
Configuración por defecto para el analizador de métricas ágiles.

Este módulo contiene todas las constantes, mapeos y umbrales utilizados
en el análisis de métricas de performance ágil.
"""

from typing import Dict, List


# Versión del analizador
VERSION = '1.1.1'


# Mapeo por defecto de sprints a meses
DEFAULT_SPRINT_MAPPING: Dict[str, str] = {
    'Sprint 2': 'Julio',
    'Sprint 3': 'Agosto',
    'Sprint 4': 'Agosto',
    'Sprint 5': 'Septiembre',
    'Sprint 6': 'Septiembre',
    'Sprint 7': 'Octubre',
    'Sprint 8': 'Octubre',
    'Sprint 9': 'Noviembre',
    'Sprint 10': 'Noviembre',
    'Sprint 11': 'Diciembre',
    'Sprint 12': 'Diciembre',
}

# Estados que indican entrega para equipos PRODUCTIVOS
DELIVERY_STATES_PRODUCTIVE: List[str] = [
    '11. Ready for Product Release',
    '12. Validación a Producción',
    '13. Producción'
]

# Estados que indican entrega para equipos EN DESARROLLO
DELIVERY_STATES_DEVELOPMENT: List[str] = [
    '9. Certificado QA',
    '10. UAT',
    '11. Ready for Product Release',
    '12. Validación a Producción',
    '13. Producción'
]

# Estados de Work In Progress
WIP_STATES: List[str] = [
    '2. Ready to Devs',
    '3. In Development',
    '4. Ready for Testing',
    '5. Testing Interno',
    '6. Merge',
    '7. Ready for QA',
    '8. In QA',
    '9. Certificado QA',
    '10. Ready for UAT'
]

# Tipos de tarea que son features
FEATURE_TYPES: List[str] = ['HDU', 'Solicitud']

# Tipos de tarea que son bugs
BUG_TYPES: List[str] = ['Bug']

# Umbrales para clasificación
THRESHOLDS: Dict[str, float] = {
    'predictability_good': 70,
    'predictability_warning': 40,
    'efficiency_good': 8.0,
    'efficiency_warning': 5.0,
    'rework_good': 15,
    'rework_warning': 30,
    'cycle_time_good': 7,
    'cycle_time_warning': 14,
}

# Colores para gráficos
COLORS: Dict[str, str] = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'success': '#06A77D',
    'warning': '#F77F00',
    'danger': '#D00000',
    'neutral': '#666666',
    'light': '#E8E8E8'
}

# Columnas requeridas (críticas) en el Excel de Monday.com
REQUIRED_COLUMNS: List[str] = [
    'Name',
    'Estado',
    'Tipo Tarea',
    'Estimación Original',
    'Fecha Inicio',
    'Sprint',
]

# Columnas opcionales (deseables pero no críticas)
OPTIONAL_COLUMNS: List[str] = [
    'Estado QA',
    'Estado UAT',
    'Puntos Logrados',
    'Fecha Término',
    'Fecha Certificado QA',
    'Fecha UAT',
    'Fecha Ready for Production',
    'Fecha paso a Producción',
    'Ciclos UAT',
    'Carry over'
]

# Columnas de fecha que pueden usarse como fecha de entrega para Cycle Time - Equipos Productivos
DELIVERY_DATE_COLUMNS_PRODUCTIVE: List[str] = [
    'Fecha Término',
    'Fecha Ready for Production',
    'Fecha paso a Producción'
]

# Columnas de fecha que pueden usarse como fecha de entrega para Cycle Time - Equipos En Desarrollo
DELIVERY_DATE_COLUMNS_DEVELOPMENT: List[str] = [
    'Fecha Término',
    'Fecha Certificado QA',
    'Fecha UAT',
    'Fecha Ready for Production',
    'Fecha paso a Producción'
]

# Configuración de visualizaciones
CHART_CONFIG: Dict[str, any] = {
    'dpi': 100,
    'figsize_dashboard': (20, 12),
    'title_fontsize': 14,
    'label_fontsize': 10,
    'tick_fontsize': 9,
    'grid_alpha': 0.3,
}

# Configuración de Excel
EXCEL_CONFIG: Dict[str, any] = {
    'date_format': 'DD/MM/YYYY',
    'number_format': '0.00',
    'percent_format': '0.0%',
    'header_bg_color': '#2E86AB',
    'header_font_color': '#FFFFFF',
}

# Número de sprints por mes (por defecto)
SPRINTS_PER_MONTH: int = 2

# Sufijos que indican tareas copiadas (a excluir)
COPY_SUFFIXES: List[str] = ['(copy)', '(copia)', '(Copy)', '(Copia)']

# Feriados nacionales de Chile (2024-2025)
# Formato: 'YYYY-MM-DD'
# Puede ser modificado según el país o necesidades específicas
HOLIDAYS: List[str] = [
    # 2024
    '2024-01-01',  # Año Nuevo
    '2024-03-29',  # Viernes Santo
    '2024-03-30',  # Sábado Santo
    '2024-05-01',  # Día del Trabajo
    '2024-05-21',  # Día de las Glorias Navales
    '2024-06-20',  # Día de los Pueblos Indígenas (anteriormente Corpus Christi)
    '2024-06-29',  # San Pedro y San Pablo
    '2024-07-16',  # Día de la Virgen del Carmen
    '2024-08-15',  # Asunción de la Virgen
    '2024-09-18',  # Día de la Independencia
    '2024-09-19',  # Día de las Glorias del Ejército
    '2024-09-20',  # Feriado adicional
    '2024-10-12',  # Encuentro de Dos Mundos
    '2024-10-31',  # Día de las Iglesias Evangélicas y Protestantes
    '2024-11-01',  # Día de Todos los Santos
    '2024-12-08',  # Inmaculada Concepción
    '2024-12-25',  # Navidad
    # 2025
    '2025-01-01',  # Año Nuevo
    '2025-04-18',  # Viernes Santo
    '2025-04-19',  # Sábado Santo
    '2025-05-01',  # Día del Trabajo
    '2025-05-21',  # Día de las Glorias Navales
    '2025-06-20',  # Día de los Pueblos Indígenas
    '2025-06-29',  # San Pedro y San Pablo
    '2025-07-16',  # Día de la Virgen del Carmen
    '2025-08-15',  # Asunción de la Virgen
    '2025-09-18',  # Día de la Independencia
    '2025-09-19',  # Día de las Glorias del Ejército
    '2025-10-12',  # Encuentro de Dos Mundos
    '2025-10-31',  # Día de las Iglesias Evangélicas y Protestantes
    '2025-11-01',  # Día de Todos los Santos
    '2025-12-08',  # Inmaculada Concepción
    '2025-12-25',  # Navidad
]

# =============================================================================
# CONFIGURACIÓN PARA PROCESAMIENTO BATCH
# =============================================================================

# Equipos que usan DoD extendido (En Desarrollo)
# Estos equipos utilizan DELIVERY_STATES_DEVELOPMENT en lugar de DELIVERY_STATES_PRODUCTIVE
DEVELOPMENT_TEAMS: List[str] = [
    'FIDREN',
    'FIDSIN_2_0',
    'P2W',
]

# Tamaño de equipo por defecto cuando no se especifica
DEFAULT_TEAM_SIZE: int = 5

# Configuración del procesamiento batch
BATCH_CONFIG: Dict[str, any] = {
    'file_pattern': 'Backlog_Planning_*_All_Tasks_*.xlsx',
    'team_name_regex': r'Backlog_Planning_(.+?)_All_Tasks_',
    'output_filename': 'Metricas_Consolidadas_Equipos.xlsx',
    'summary_sheet_name': 'Resumen Comparativo',
}
