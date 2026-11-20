import joblib

from app.config import MODEL_PATH
from app.schemas.prestamo import PrediccionSalida

# Orden en el que el modelo espera las variables
VARIABLES = [
    "edad",
    "ingresos_mensuales",
    "importe_prestamo",
    "plazo_meses",
    "antiguedad_laboral_anios",
    "impagos_previos",
]

# cargar el modelo joblib una sola vez, al importar el modulo
modelo = joblib.load(MODEL_PATH)

# funcion decidir(probabilidad) -> "aprobar", "revisar" o "rechazar" (umbrales en el enunciado)
def decidir(probabilidad: str) -> str:
    if probabilidad < 0.2:
        decision = "aprobar"
    elif probabilidad < 0.5:
        decision = "revisar"
    else:
        decision = "rechazar"
    return decision

# funcion predecir(entrada) -> PrediccionSalida, usando VARIABLES para ordenar los valores
def predecir(entrada) -> PrediccionSalida:
    valores = [[getattr(entrada, variable) for variable in VARIABLES]]

    # Obtener la probabilidad de impago
    probabilidades = modelo.predict_proba(valores)[0]
    probabilidad = float(probabilidades[1])
    
    decision = decidir(probabilidad)
    return PrediccionSalida(
        probabilidad_impago=probabilidad,
        decision=decision
    )
