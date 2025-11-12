"""
Script de prueba para validar los cambios en el cálculo de Cycle Time.
"""

from datetime import datetime
import sys
sys.path.insert(0, 'metrics_analyzer')

from utils import calculate_business_days

# Prueba 1: Calcular días hábiles entre dos fechas sin fines de semana
print("=" * 60)
print("PRUEBAS DE DÍAS HÁBILES")
print("=" * 60)

# Lunes 2024-10-07 a Viernes 2024-10-11 = 5 días hábiles
start1 = datetime(2024, 10, 7)
end1 = datetime(2024, 10, 11)
result1 = calculate_business_days(start1, end1)
print(f"\nPrueba 1: {start1.strftime('%Y-%m-%d')} a {end1.strftime('%Y-%m-%d')}")
print(f"Días hábiles: {result1} (esperado: 5)")
assert result1 == 5, f"Error: esperado 5, obtenido {result1}"

# Lunes 2024-10-07 a Lunes 2024-10-14 = 6 días hábiles (excluye sáb/dom)
start2 = datetime(2024, 10, 7)
end2 = datetime(2024, 10, 14)
result2 = calculate_business_days(start2, end2)
print(f"\nPrueba 2: {start2.strftime('%Y-%m-%d')} a {end2.strftime('%Y-%m-%d')}")
print(f"Días hábiles: {result2} (esperado: 6)")
assert result2 == 6, f"Error: esperado 6, obtenido {result2}"

# Prueba con feriado: 2024-09-18 (Independencia) es feriado
start3 = datetime(2024, 9, 16)  # Lunes
end3 = datetime(2024, 9, 20)     # Viernes (también feriado)
result3 = calculate_business_days(start3, end3)
print(f"\nPrueba 3 (con feriados): {start3.strftime('%Y-%m-%d')} a {end3.strftime('%Y-%m-%d')}")
print(f"Días hábiles: {result3}")
print(f"(Excluye 18 sept = Independencia, 19 sept = Glorias, 20 sept = feriado adicional)")
print(f"Días hábiles esperados: 2 (16 y 17 sept)")
assert result3 == 2, f"Error: esperado 2, obtenido {result3}"

print("\n" + "=" * 60)
print("✓ TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
print("=" * 60)

print("\n" + "=" * 60)
print("CAMBIOS IMPLEMENTADOS")
print("=" * 60)
print("""
1. ✓ Función calculate_business_days() agregada en utils.py
   - Excluye fines de semana (sábados y domingos)
   - Excluye feriados configurados en config.py

2. ✓ Configuración de feriados en config.py
   - Feriados de Chile 2024-2025
   - Fácilmente modificable para otros países

3. ✓ _calculate_cycle_time() modificado en data_processor.py
   - Ahora usa calculate_business_days() en lugar de días calendario
   - Cycle Time = días hábiles entre Fecha Inicio y Fecha de Entrega

4. ✓ Cálculo mensual de Cycle Time modificado en metrics_calculator.py
   - Cycle Time Mensual = PROMEDIO de los promedios de cada sprint
   - Ejemplo: Sprint 3 promedio=7.5 días, Sprint 4 promedio=9.0 días
             → Cycle Time Agosto = (7.5 + 9.0) / 2 = 8.25 días
""")

print("\n" + "=" * 60)
print("EJEMPLO DE COMPARACIÓN")
print("=" * 60)
print("""
Tarea: Inicio 2024-10-07 (lunes) → Entrega 2024-10-18 (viernes)

ANTES (días calendario):
  18 - 7 = 11 días calendario

AHORA (días hábiles):
  Lun 7, Mar 8, Mié 9, Jue 10, Vie 11 = 5 días
  [Sáb 12, Dom 13 = NO CUENTAN]
  Lun 14, Mar 15, Mié 16, Jue 17, Vie 18 = 5 días
  TOTAL: 10 días hábiles

  Si hubiera un feriado en ese rango, se restaría también.
""")
