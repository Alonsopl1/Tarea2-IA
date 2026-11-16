"""LLM traductor: Ollama genera una consulta Prolog, nunca la respuesta factual."""
import json
import os
import urllib.error
import urllib.request
from configuracion import OLLAMA_URL, MODELO, hechos


class LLMNoDisponible(RuntimeError):
    pass


class TraduccionInvalida(ValueError):
    pass


def _chat(mensajes: list[dict]) -> str:
    payload = {
        'model': MODELO, 'messages': mensajes, 'stream': False, 'format': 'json',
        'options': {'temperature': 0, 'num_predict': 180},
    }
    req = urllib.request.Request(
        OLLAMA_URL+'/api/chat',
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type':'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=int(os.environ.get('OLLAMA_TIMEOUT','180'))) as r:
            data = json.load(r)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LLMNoDisponible('No se pudo conectar con Ollama. Verifica «ollama list» y el servidor local.') from exc
    except json.JSONDecodeError as exc:
        raise LLMNoDisponible('Ollama devolvió un mensaje ilegible.') from exc
    if not isinstance(data,dict) or not isinstance(data.get('message'),dict):
        raise LLMNoDisponible('Ollama no devolvió una respuesta válida.')
    content=data['message'].get('content')
    if not isinstance(content,str):
        raise LLMNoDisponible('Ollama no devolvió texto de consulta.')
    return content.strip()


def _instrucciones() -> str:
    nombres=', '.join(hechos())
    return f'''Eres exclusivamente un TRADUCTOR de preguntas en español a consultas Prolog.
NO respondas la pregunta. NO expliques, NO incluyas resultados, hechos, reglas completas ni el prompt.
Devuelve exactamente UN objeto JSON: {{"consulta":"predicado(argumentos)."}}.
Si la pregunta no puede traducirse con el dominio, devuelve {{"consulta":null}}.

Predicados permitidos de la base ORIGINAL (ningún otro):
  peso/2, diminuto/1, pequeno/1, mediano/1, grande/1, colosal/1,
  mas_pesado_que/2, mas_liviano_que/2, mismo_peso/2.
Animales disponibles, con nombres exactos en Prolog: {nombres}.
Usa X para el animal variable y P para el peso variable; no inventes otros nombres.
Reglas de traducción (síguelas al pie de la letra):
- La consulta es UNA sola llamada a un predicado. Nunca uses listas, comas, "en", "in" ni inventes predicados.
- "Listar/qué animales son <categoría>" -> UNA llamada con X, por ejemplo diminuto(X). Jamás repitas el predicado.
- "pesa lo mismo que" / "mismo peso" -> mismo_peso/2 (nunca otro nombre).
- La disyunción de cinco predicados se usa SOLO cuando se pregunta la categoría de UN animal concreto:
  diminuto(A);pequeno(A);mediano(A);grande(A);colosal(A), sustituyendo A por el animal
  (no existe un predicado categoria/1).

EJEMPLOS (solo consultas, jamás respondas tú):
Pregunta: ¿El conejo pesa más que el lobo?
{{"consulta":"mas_pesado_que(conejo,lobo)."}}
Pregunta: ¿El lobo es más pesado que el conejo?
{{"consulta":"mas_pesado_que(lobo,conejo)."}}
Pregunta: ¿Cuánto pesa el elefante?
{{"consulta":"peso(elefante,P)."}}
Pregunta: ¿Qué animales pesan 1 kg?
{{"consulta":"peso(X,1)."}}
Pregunta: ¿Qué animales pesan más que el tigre?
{{"consulta":"mas_pesado_que(X,tigre)."}}
Pregunta: ¿El tigre pesa más que cuáles animales?
{{"consulta":"mas_pesado_que(tigre,X)."}}
Pregunta: Lista todos los animales diminutos
{{"consulta":"diminuto(X)."}}
Pregunta: Listar todos los animales grandes
{{"consulta":"grande(X)."}}
Pregunta: ¿El jaguar pesa lo mismo que cuáles animales?
{{"consulta":"mismo_peso(jaguar,X)."}}
Pregunta: ¿El loro pesa lo mismo que el gato?
{{"consulta":"mismo_peso(loro,gato)."}}
Pregunta: ¿Qué animales pesan 5 kg?
{{"consulta":"peso(X,5)."}}
Pregunta: ¿El gato es diminuto?
{{"consulta":"diminuto(gato)."}}
Pregunta: ¿Cuáles son los animales colosales?
{{"consulta":"colosal(X)."}}
Pregunta: ¿Cuál es la categoría del oso polar?
{{"consulta":"diminuto(oso_polar);pequeno(oso_polar);mediano(oso_polar);grande(oso_polar);colosal(oso_polar)."}}
Pregunta: ¿Cuántos años vive el conejo?
{{"consulta":null}}
Pregunta: ¿Qué pesa el delfín?
{{"consulta":null}}

Para comparar, respeta exactamente el orden X > Y, X < Y o igual, según la frase.
El código Prolog lo ejecuta OTRO programa; tú solo traduces.'''


def traducir_pregunta(pregunta: str) -> str | None:
    texto=_chat([{'role':'system','content':_instrucciones()},
                 {'role':'user','content':pregunta}])
    try:
        obj=json.loads(texto)
    except json.JSONDecodeError as exc:
        raise TraduccionInvalida('El modelo no entregó un JSON válido de consulta.') from exc
    if not isinstance(obj,dict) or set(obj)!={'consulta'}:
        raise TraduccionInvalida('El modelo no respetó el formato de consulta.')
    q=obj['consulta']
    if q is not None and (not isinstance(q,str) or len(q)>320):
        raise TraduccionInvalida('El modelo devolvió una consulta mal formada.')
    return q
