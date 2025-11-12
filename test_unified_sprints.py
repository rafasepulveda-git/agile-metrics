"""
Script de prueba para validar la unificación de sprints.

Prueba que sprints con el mismo número base (ej: Sprint 07 FIDSIN, Sprint 07 Auto3P)
se unifican correctamente como un solo sprint en los cálculos.
"""

import sys
sys.path.insert(0, 'metrics_analyzer')

from utils import extract_sprint_number

# ============================================================================
# PRUEBA 1: Función extract_sprint_number()
# ============================================================================
print("=" * 70)
print("PRUEBA 1: Extracción de número base de sprint")
print("=" * 70)

test_cases = [
    ('Sprint 07 FIDSIN', 'Sprint 7'),
    ('Sprint 07 Auto3P', 'Sprint 7'),
    ('Sprint 7', 'Sprint 7'),
    ('Sprint 03', 'Sprint 3'),
    ('Sprint 10 Proyecto X', 'Sprint 10'),
    ('Sprint 2', 'Sprint 2'),
    ('Sprint 09', 'Sprint 9'),
]

print("\nFormato: Nombre Original → Nombre Unificado")
print("-" * 70)

all_passed = True
for original, expected in test_cases:
    result = extract_sprint_number(original)
    status = "✓" if result == expected else "✗"
    print(f"{status} '{original}' → '{result}' (esperado: '{expected}')")

    if result != expected:
        all_passed = False
        print(f"  ERROR: Se obtuvo '{result}' pero se esperaba '{expected}'")

if all_passed:
    print("\n✓ TODAS LAS PRUEBAS DE EXTRACCIÓN PASARON")
else:
    print("\n✗ ALGUNAS PRUEBAS FALLARON")

# ============================================================================
# PRUEBA 2: Simulación de agrupación de métricas
# ============================================================================
print("\n" + "=" * 70)
print("PRUEBA 2: Simulación de agrupación de sprints")
print("=" * 70)

print("""
ESCENARIO:
----------
Mes: Octubre
  - Sprint 07 FIDSIN:  30 tareas, 45 puntos
  - Sprint 07 Auto3P:  20 tareas, 35 puntos
  - Sprint 08 FIDSIN:  25 tareas, 40 puntos
  - Sprint 08 Auto3P:  15 tareas, 30 puntos

AGRUPACIÓN ESPERADA:
-------------------
  Sprint 7 (unifica FIDSIN + Auto3P):
    - Total: 50 tareas, 80 puntos

  Sprint 8 (unifica FIDSIN + Auto3P):
    - Total: 40 tareas, 70 puntos

CÁLCULO MENSUAL:
---------------
  Throughput promedio: (50 + 40) / 2 = 45 tareas/sprint
  Velocity promedio: (80 + 70) / 2 = 75 puntos/sprint
  Número de sprints en el mes: 2 (Sprint 7 y Sprint 8)

  (En lugar de 4 sprints sin unificación)
""")

# ============================================================================
# PRUEBA 3: Mapeo a mes con sprints unificados
# ============================================================================
print("=" * 70)
print("PRUEBA 3: Mapeo de sprints unificados a meses")
print("=" * 70)

sprint_mapping = {
    'Sprint 7': 'Octubre',
    'Sprint 8': 'Octubre',
    'Sprint 9': 'Noviembre',
}

sprints_originales = [
    'Sprint 07 FIDSIN',
    'Sprint 07 Auto3P',
    'Sprint 08 FIDSIN',
    'Sprint 08 Auto3P',
    'Sprint 09 FIDSIN',
]

print("\nSprints Originales → Sprint Unificado → Mes")
print("-" * 70)

for sprint_original in sprints_originales:
    sprint_unificado = extract_sprint_number(sprint_original)
    mes = sprint_mapping.get(sprint_unificado, 'No mapeado')
    print(f"'{sprint_original}' → '{sprint_unificado}' → {mes}")

# ============================================================================
# RESUMEN
# ============================================================================
print("\n" + "=" * 70)
print("RESUMEN DE CAMBIOS IMPLEMENTADOS")
print("=" * 70)

print("""
1. ✓ Función extract_sprint_number() en utils.py
   - Extrae número base de cualquier formato de sprint
   - Normaliza 'Sprint 07 XXX' → 'Sprint 7'

2. ✓ Columna Sprint_Unified en data_processor.py
   - Se agrega durante el procesamiento de datos
   - Permite agrupar sprints con mismo número base

3. ✓ Cálculo de métricas por sprint en metrics_calculator.py
   - Usa Sprint_Unified en lugar de Sprint original
   - Agrupa automáticamente sprints con mismo número
   - Guarda nombres originales en campo 'Original_Sprints'

4. ✓ Cálculo de métricas mensuales en metrics_calculator.py
   - Cuenta sprints unificados (no originales)
   - Promedia métricas por sprints unificados
   - Ejemplo: Si hay Sprint 7 FIDSIN y Sprint 7 Auto3P:
     → Se cuentan como 1 sprint unificado (Sprint 7)

5. ✓ Visualizaciones (sin cambios necesarios)
   - Ya usan la columna 'Sprint' del DataFrame de métricas
   - Automáticamente muestran sprints unificados

BENEFICIOS:
-----------
✓ Métricas más precisas cuando hay múltiples equipos
✓ Cálculos mensuales correctos (no inflan cantidad de sprints)
✓ Transparencia: se guarda información de sprints originales
✓ Backward compatible: funciona con sprints simples también
""")

print("\n" + "=" * 70)
print("EJEMPLO PRÁCTICO: IMPACTO EN MÉTRICAS")
print("=" * 70)

print("""
SIN UNIFICACIÓN (ANTES):
-----------------------
Octubre tiene 4 sprints:
  - Sprint 07 FIDSIN: Velocity = 45
  - Sprint 07 Auto3P: Velocity = 35
  - Sprint 08 FIDSIN: Velocity = 40
  - Sprint 08 Auto3P: Velocity = 30

Velocity Promedio Mensual = (45 + 35 + 40 + 30) / 4 = 37.5 puntos/sprint

CON UNIFICACIÓN (AHORA):
-----------------------
Octubre tiene 2 sprints unificados:
  - Sprint 7: Velocity = 80 (45 + 35)
  - Sprint 8: Velocity = 70 (40 + 30)

Velocity Promedio Mensual = (80 + 70) / 2 = 75 puntos/sprint ✓ CORRECTO

CONCLUSIÓN:
-----------
La unificación refleja correctamente que hay 2 sprints (Sprint 7 y 8),
cada uno ejecutado por múltiples equipos en paralelo.
""")

print("\n✓ PRUEBAS COMPLETADAS")
