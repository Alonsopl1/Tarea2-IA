# Guion de defensa — ZooLogic corregido

**Qué desarrollamos:** los 20 hechos y ocho reglas de Prolog originales; un chatbot en Python con dos opciones y una interfaz web. No creamos ni reentrenamos Llama 3.2. Ollama lo ejecuta localmente.

**Opción Prolog:** Python identifica intención y argumentos de preguntas comunes; el motor SWI-Prolog resuelve usando las reglas.

**Opción LLM:** Llama 3.2 **solo traduce** una pregunta en español a una consulta Prolog; Python valida predicado, argumentos y animales; el mismo motor SWI-Prolog la ejecuta. No hay tercer modo.

**Demostración clave:**
1. Mostrar `conocimiento.pl` (no se cambió ningún hecho ni regla).
2. Elegir Prolog; preguntar «¿El conejo pesa más que el lobo?». Mostrar `mas_pesado_que(conejo,lobo)`, respuesta «No», pesos 2 kg y 40 kg.
3. Elegir LLM; repetir con «¿Podrías comprobar si un conejo supera en peso a un lobo?». Revisar la consulta traducida y el resultado Prolog (la traducción puede fallar y debe comprobarse en vivo).
4. Comprobar el caso inverso «¿El lobo pesa más que el conejo?».
5. Preguntar «¿Qué animales pesan más que el tigre?» y contrastar con «¿El tigre pesa más que cuáles animales?»; Prolog diferencia las posiciones de `X`.
6. Preguntar «¿Cuántos años vive el león?» y mostrar que no se inventa información.

**¿Dónde está el LLM?** `llm_ollama.py` usa la API HTTP local `POST /api/chat` de Ollama y solicita JSON con `consulta`. No pide respuestas sobre animales.

**¿Cómo se protege Prolog?** `consulta_prolog.py` acepta solo las nueve formas de consulta permitidas (el hecho `peso/2` más las ocho reglas originales). El programa nunca ejecuta cadenas del LLM como código sin validar: Python transforma esa consulta en un plan JSON seguro y `motor_prolog.pl` invoca únicamente predicados conocidos.

**¿Cómo se sabe que no responde Llama por su cuenta?** En `chatbot.py`, el modo `llm` llama a `traducir_pregunta`, luego a `parsear_consulta` y finalmente a `consultar(plan)`. La respuesta se crea usando exclusivamente el JSON devuelto por SWI-Prolog. Sin SWI-Prolog instalado se muestra un error, no se inventa una respuesta.

**¿Para qué Docker?** `Dockerfile` instala Python + SWI-Prolog; `compose.yaml` inicia un servicio Ollama separado. Se descarga `llama3.2:3b` una sola vez en el volumen. La lógica y reglas del chatbot no se cambian.

**Evaluación:** `python evaluar.py --con-llm` registra consultas, respuestas y estados para 20 preguntas; también deben ensayar casos negativos, desconocidos y formulaciones distintas para demostrar calidad del traductor.
