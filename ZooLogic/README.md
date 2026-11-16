# ZooLogic CINF103 — corrección de integración según observaciones del profesor

Este es **el mismo proyecto corregido**, no una reimplementación desde cero. Conserva literalmente `conocimiento.pl` de la entrega anterior (20 hechos `peso/2`, 8 reglas) y los módulos del servidor, la web y el adaptador SWI-Prolog. No incorpora nuevos hechos ni nuevas reglas de animales.

## Dos opciones, no tres

| Opción de la interfaz | ¿Quién traduce? | ¿Quién obtiene la respuesta lógica? |
|---|---|---|
| **01 · Python + Prolog** (`prolog`) | `interpretacion.py`, con patrones acotados | SWI-Prolog (`conocimiento.pl`) |
| **02 · LLM + Python** (`llm`) | Llama 3.2 vía Ollama genera una consulta Prolog | **El mismo SWI-Prolog** |

**Nota sobre la guía:** el enunciado escrito describe dos implementaciones (Prolog y LLM); esta versión sigue la aclaración docente más reciente comunicada por el grupo: el LLM traduce y Prolog ejecuta. Se mantienen dos botones, sin tercer modo; no se simula razonamiento con texto del LLM.

## Qué se corrigió

- Antes `llm_ollama.py` leía el archivo `.pl` como texto y le pedía al LLM responder por sí mismo. Ahora **solo genera** `{"consulta":"mas_pesado_que(conejo,lobo)."}` o `{"consulta":null}`.
- `consulta_prolog.py` es un **validador estricto**: solo reconoce `peso/2`, cinco predicados de categoría y tres de comparación, más una disyunción controlada de las cinco categorías originales. No evalúa `call`, `consult`, `asserta`, `halt`, reglas inventadas, variables arbitrarias ni código libre.
- `chatbot.py` convierte la consulta aceptada al plan JSON que ya conocía `motor_prolog.pl`. **`prolog_backend.py` ejecuta `swipl` realmente**. La respuesta natural procede exclusivamente del resultado JSON de SWI-Prolog. Para preguntas binarias claras, Python también comprueba que el LLM no haya invertido accidentalmente el orden de los animales; la verdad de la comparación sigue decidiéndose en Prolog.
- Las preguntas negativas devuelven `false` de Prolog, no una respuesta fabricada por Llama. En caso de consulta inválida o fuera del dominio no se ejecuta ningún código.
- El frontend mantiene sus archivos HTML/CSS/JS y solamente se actualizó la descripción de la segunda opción.
- Las pruebas y el informe pasan a comprobar las dos rutas hasta Prolog.

## Ejemplo exacto (modo LLM)

```text
Usuario:     ¿El conejo es más pesado que el lobo?
Llama 3.2:   {"consulta":"mas_pesado_que(conejo,lobo)."}
Python:      validación estricta → {"intencion":"comparar", ...}
SWI-Prolog:  peso(conejo,2), peso(lobo,40), mas_pesado_que(conejo,lobo) → false
Chatbot:     No. Conejo no pesa más que lobo según nuestras reglas (2 kg y 40 kg).
```

Este es un **ejemplo esperado de la ejecución**, no una medición en vivo de Ollama.

## Configuración

No se necesitan cuentas ni claves de API. Todo se configura con variables de entorno opcionales; el archivo [`.env.example`](.env.example) muestra los valores por defecto.

| Variable | Por defecto | Uso |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.2:3b` | Modelo de Ollama para la opción LLM |
| `OLLAMA_URL` | `http://127.0.0.1:11434` (en Docker: `http://ollama:11434`) | Dirección de Ollama |
| `OLLAMA_TIMEOUT` | `180` | Segundos de espera al LLM |
| `ZOOLOGIC_HOST` | `127.0.0.1` | Interfaz del servidor web |
| `PORT` | `8765` | Puerto del servidor web |
| `SWIPL` | (busca `swipl` en el PATH) | Ruta a SWI-Prolog |

Con Docker Compose ya vienen configuradas en `compose.yaml`; sin Docker, define las variables en la terminal solo si necesitas cambiarlas.

## Windows (sin Docker)

1. Extrae el ZIP entero. En VS Code, **Archivo → Abrir carpeta**, selecciona la carpeta interior que contiene `servidor.py`.
2. Instala [Python](https://www.python.org/downloads/), [SWI-Prolog](https://www.swi-prolog.org/Download.html), [Ollama](https://ollama.com/download/windows).
3. Reinicia la terminal y confirma:

   ```powershell
   python --version
   swipl --version
   ollama --version
   ollama pull llama3.2:3b
   ollama list
   ```

   Si Windows no encuentra Python, prueba `py --version` y `py servidor.py`. Ollama debe permanecer ejecutándose en segundo plano; si no se inicia automáticamente, ejecuta `ollama serve` en otra terminal.
4. Desde **la carpeta que contiene `servidor.py`** ejecuta:

   ```powershell
   python servidor.py
   ```

5. Abre <http://127.0.0.1:8765>. Prueba primero el modo `Prolog`, después `LLM`. **No cierres la terminal del servidor.**
6. Para probar todas las preguntas:

   ```powershell
   python -m unittest discover -s pruebas -v
   python evaluar.py --con-llm
   ```

   El evaluador crea `resultados_evaluacion.csv`; compara el resultado obtenido por cada modo con una referencia basada en los hechos originales. `NO_EJECUTADO` o `ERROR` no equivale a aprobado.

## Docker Compose (Windows, Linux o macOS con Docker)

Docker empaqueta Python + SWI-Prolog **en el contenedor `zoologic`** y Ollama **en el contenedor `ollama`**; no hace falta instalar Python, SWI-Prolog ni Ollama por separado en el host. Se necesita Docker con soporte de Compose, conexión inicial a Internet y memoria suficiente para Llama 3.2 (~2 GB de descarga, más memoria al inferir).

En la carpeta del proyecto:

```sh
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2:3b
docker compose logs -f zoologic
```

Después abre <http://127.0.0.1:8765>. Para ejecutar las pruebas desde Docker:

```sh
docker compose exec zoologic python -m unittest discover -s pruebas -v
docker compose exec zoologic python evaluar.py --con-llm
```

Los resultados de las pruebas ejecutadas **dentro de Docker** quedan dentro del contenedor. Copia el CSV al computador con:

```sh
docker compose cp zoologic:/app/resultados_evaluacion.csv ./resultados_evaluacion.csv
```

Para detener: `docker compose down` (conserva los modelos en un volumen). El primer arranque de la opción LLM puede ser lento, especialmente sin GPU. **`compose.yaml` no garantiza rapidez ni que el modelo esté descargado antes del primer uso**: ejecuta `ollama pull` una vez.

## Qué pregunta Prolog realmente

`llm_ollama.py` → `consulta_prolog.py` → `chatbot.py` → `prolog_backend.py` → `motor_prolog.pl` → `conocimiento.pl` → resultado JSON → `chatbot.py`.

`motor_prolog.pl` ya existía en el proyecto. Por seguridad recibe un **plan JSON validado**, nunca texto Prolog sin comprobar. Dentro de SWI-Prolog ejecuta los predicados originales. Por ejemplo, si el modelo devuelve `mas_pesado_que(conejo,lobo).`, el plan es `{"intencion":"comparar","animal":"conejo","animal2":"lobo","relacion":"mas_pesado_que"}`, y Prolog comprueba esa regla con los hechos vigentes.

Para comprobar el motor sin LLM:

```powershell
'{"intencion":"comparar","animal":"conejo","animal2":"lobo","relacion":"mas_pesado_que"}' | swipl -q -g "consult(['conocimiento.pl','motor_prolog.pl'])" -g main -t halt
```

La salida debe incluir `"tipo":"comparacion"` y `"verdad":false` (el orden de claves JSON puede variar). Para probar la consulta directamente en SWI-Prolog:

```powershell
swipl -q -s conocimiento.pl -g "(mas_pesado_que(conejo,lobo)->writeln(true);writeln(false))" -t halt
```

Debe imprimir `false`. La pregunta inversa `mas_pesado_que(lobo,conejo)` devuelve `true`.

## Casos de prueba recomendados

| Pregunta | Consulta válida | Resultado esperado |
|---|---|---|
| ¿El conejo pesa más que el lobo? | `mas_pesado_que(conejo,lobo)` | No; 2 kg vs. 40 kg |
| ¿El lobo pesa más que el conejo? | `mas_pesado_que(lobo,conejo)` | Sí |
| ¿El gato es mediano? | `mediano(gato)` | No |
| ¿Cuánto pesa la jirafa? | `peso(jirafa,P)` | 1.200 kg |
| ¿Qué animales pesan más que el tigre? | `mas_pesado_que(X,tigre)` | 6 animales |
| ¿Qué animales son colosales? | `colosal(X)` | Ballena azul, elefante, rinoceronte |
| ¿Cuántos años vive el conejo? | `null` | Fuera del dominio |
| ¿Cuánto pesa un delfín? | `null` | Animal no registrado |

`pruebas/test_traduccion_llm.py` prueba el validador frente a inyección de código y a respuestas mal formadas. Las pruebas que usan mocks validan integración de software, **no la calidad real de Llama 3.2**. Para medir esta última hay que ejecutar Ollama en el PC y revisar el CSV.

## Límites honestos de esta revisión

- La base mantiene los rangos originales para animales de pesos enteros; no se alteraron las ocho reglas ni los 20 hechos.
- El LLM todavía puede **traducir mal** una frase, incluso si genera una consulta sintácticamente válida. Para eso existe el CSV de evaluación y la revisión del grupo.
- En el entorno donde se corrigió el código no estaban instalados SWI-Prolog, Ollama ni Docker, por lo que la ejecución integrada real debe hacerse en un computador con esos programas; no se fingen resultados.
- El servidor web se ejecuta en `127.0.0.1` por defecto y Docker solo expone el puerto al equipo local. No se recomienda publicarlo en Internet.
