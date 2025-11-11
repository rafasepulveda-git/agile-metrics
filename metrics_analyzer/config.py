"""
Configuración por defecto para el analizador de métricas ágiles.

Este módulo contiene todas las constantes, mapeos y umbrales utilizados
en el análisis de métricas de performance ágil.
"""

from typing import Dict, List


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
    'Sprint Completed?'
]

# Columnas opcionales (deseables pero no críticas)
OPTIONAL_COLUMNS: List[str] = [
    'Estado QA',
    'Estado UAT',
    'Puntos Logrados',
    'Fecha Ready for Production',
    'Fecha paso a Producción',
    'Ciclos UAT',
    'Carry over'
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
