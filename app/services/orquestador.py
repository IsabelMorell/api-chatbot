import json

from pydantic import ValidationError

from app.schemas.chat import ChatSalida, HerramientaUsada
from app.schemas.prestamo import PrestamoEntrada
from app.services.modelo import predecir

NOMBRE_TOOL = "calcular_riesgo_impago"
MAX_VUELTAS = 4

SISTEMA = (
    "Eres un asistente de riesgo de un banco. Cuando tengas todos los datos de una solicitud de "
    "prestamo, llama a la herramienta calcular_riesgo_impago. Si falta algun dato, pidelo. "
    "Nunca inventes valores. Responde en espanol y de forma breve."
)


def leer_argumentos(texto):
    """YA HECHO: convierte el texto JSON de la tool en dict ({} si no es JSON valido)."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return {}
    if isinstance(datos, dict):
        return datos
    return {}


# definir_tool() -> dict con la definicion de la tool, sacando "parameters" de PrestamoEntrada
def definir_tool() -> dict:
    return {
        "type": "function",
        "function": {
            "name": NOMBRE_TOOL,
            "description": "Calcula el riesgo de impago de una solicitud de préstamo.",
            "parameters": PrestamoEntrada.model_json_schema()
        }
    }

# ejecutar_tool(nombre, argumentos_json) -> dict con "ok" True/False
#       (tool desconocida, JSON roto, datos invalidos o campos inventados -> ok False con el error)
def ejecutar_tool(nombre, argumentos_json) -> dict:
    if nombre != NOMBRE_TOOL:
        return {
            "ok": False,
            "error": f"Herramienta desconocida: {nombre}"
        }
        
    try:
        argumentos = json.loads(argumentos_json)
    except (json.JSONDecodeError, TypeError):
        return {
            "ok": False,
            "error": "Los argumentos no contienen un JSON válido."
        }

    try:
        entrada = PrestamoEntrada.model_validate(argumentos)
    except ValidationError as e:
        return {
            "ok": False,
            "error": str(e)
        }
    
    resultado = predecir(entrada)

    return {
        "ok": True,
        **resultado.model_dump()
    }

# TODO: responder(mensajes, llm) -> ChatSalida, con el bucle LLM -> tool -> LLM (maximo MAX_VUELTAS)
def responder(mensajes, llm) -> ChatSalida:
    historial = [
        {"role": "system", "content": SISTEMA}
    ]

    historial.extend([
        mensaje.model_dump() if hasattr(mensaje, "model_dump") else mensaje
        for mensaje in mensajes
    ])
    
    herramienta_usada = None
    for _ in range(MAX_VUELTAS):
        mensaje = llm.completar(
            historial,
            [definir_tool()]
        )

        if not mensaje.get("tool_calls"):
            return ChatSalida(
                respuesta=mensaje.get("content") or "No he podido generar una respuesta.",
                herramienta=herramienta_usada
            )

        historial.append(mensaje)
        
        for llamada in mensaje["tool_calls"]:
            nombre = llamada["function"]["name"]
            argumentos_json = llamada["function"]["arguments"]
            resultado = ejecutar_tool(nombre, argumentos_json)

            # Guardar la última herramienta utilizada
            herramienta_usada = HerramientaUsada(
                nombre=nombre,
                argumentos=leer_argumentos(argumentos_json),
                resultado=resultado
            )

            historial.append({
                "role": "tool",
                "tool_call_id": llamada["id"],
                "content": json.dumps(resultado, ensure_ascii=False)
            })
    return ChatSalida(
        respuesta="No he podido completar la solicitud. Inténtalo de nuevo.",
        herramienta=herramienta_usada
    )
