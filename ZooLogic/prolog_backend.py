"""Interfaz Python ↔ SWI-Prolog, usando un proceso con JSON por stdin/stdout."""
import json
import subprocess
from configuracion import SWIPL, CONOCIMIENTO, MOTOR


class MotorNoDisponible(RuntimeError):
    pass


def consultar(plan: dict) -> dict:
    if not SWIPL:
        raise MotorNoDisponible('No se encontró SWI-Prolog (swipl). Instálalo y reinicia VS Code.')
    try:
        p = subprocess.run(
            [SWIPL, '-q', '-g', f"consult(['{CONOCIMIENTO.as_posix()}','{MOTOR.as_posix()}'])",
             '-g', 'main', '-t', 'halt'],
            input=json.dumps(plan, ensure_ascii=False), text=True,
            encoding='utf-8', errors='replace', capture_output=True, timeout=12,
            cwd=str(CONOCIMIENTO.parent), check=False
        )
    except FileNotFoundError as e:
        raise MotorNoDisponible('No se pudo ejecutar SWI-Prolog. Verifica su instalación y PATH.') from e
    except subprocess.TimeoutExpired as e:
        raise MotorNoDisponible('SWI-Prolog demoró demasiado en responder.') from e
    if p.returncode:
        raise RuntimeError('Error de SWI-Prolog: ' + (p.stderr.strip() or 'salida no válida'))
    try:
        r=json.loads(p.stdout.strip())
    except json.JSONDecodeError as e:
        raise RuntimeError('SWI-Prolog no devolvió JSON: '+p.stdout[:300]+' '+p.stderr[:200]) from e
    if r.get('estado')=='error':
        raise RuntimeError(r.get('mensaje','Error en la consulta'))
    return r
