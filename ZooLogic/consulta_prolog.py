"""Convierte una consulta Prolog *muy limitada* del LLM al plan seguro existente.

Nunca se ejecuta el texto proporcionado por el LLM con call/1, read/1 o eval.
El adaptador motor_prolog.pl invoca solo los predicados originales tras validación.
"""
import re
from interpretacion import validar
from configuracion import CATEGORIAS, RELACIONES

IDENT = r'[a-z][a-z_]*'
ARG = rf'(?:{IDENT}|X|P)'
NUM = r'\d+(?:\.\d+)?'
PESO = re.compile(rf'peso\s*\(\s*({ARG})\s*,\s*({NUM}|X|P)\s*\)\Z')
CAT = re.compile(rf'({"|".join(CATEGORIAS)})\s*\(\s*({IDENT}|X)\s*\)\Z')
REL = re.compile(rf'({"|".join(RELACIONES)})\s*\(\s*({IDENT}|X)\s*,\s*({IDENT}|X)\s*\)\Z')


class ConsultaNoPermitida(ValueError):
    """El LLM no produjo una consulta válida dentro del dominio acordado."""


def parsear_consulta(texto: str) -> dict:
    if not isinstance(texto, str) or len(texto) > 320 or not texto.strip():
        raise ConsultaNoPermitida('Consulta vacía o demasiado larga')
    q = texto.strip()
    if q.startswith('?-'):
        q = q[2:].strip()
    if q.endswith('.'):
        q = q[:-1].strip()
    # Consulta compuesta de categoría de un animal: no añade predicados al KB.
    # Son exactamente las cinco reglas existentes, con el mismo argumento.
    if ';' in q:
        parts = [p.strip() for p in q.split(';')]
        found = [CAT.fullmatch(p) for p in parts]
        if len(found) != 5 or not all(found):
            raise ConsultaNoPermitida('Solo se admite la disyunción de las cinco categorías originales')
        cats = [m.group(1) for m in found]
        animales = [m.group(2) for m in found]
        if tuple(cats) != CATEGORIAS or len(set(animales)) != 1 or animales[0] == 'X':
            raise ConsultaNoPermitida('Categorías o argumentos de disyunción incorrectos')
        plan = {'intencion':'categoria_de','animal':animales[0]}
    elif match := PESO.fullmatch(q):
        animal, cantidad = match.groups()
        if animal == 'X' and cantidad in ('X','P'):
            plan={'intencion':'listar_animales'}
        elif animal == 'X':
            plan={'intencion':'animales_peso','peso':float(cantidad) if '.' in cantidad else int(cantidad)}
        elif cantidad in ('X','P'):
            plan={'intencion':'peso_de','animal':animal}
        else:
            plan={'intencion':'peso_es','animal':animal,
                  'peso':float(cantidad) if '.' in cantidad else int(cantidad)}
    elif match := CAT.fullmatch(q):
        categoria, animal = match.groups()
        plan=({'intencion':'listar_categoria','categoria':categoria} if animal=='X'
              else {'intencion':'verificar_categoria','categoria':categoria,'animal':animal})
    elif match := REL.fullmatch(q):
        rel,a,b=match.groups()
        if a=='X' and b=='X':
            raise ConsultaNoPermitida('Solo se admite una variable en una comparación')
        if a=='X':
            plan={'intencion':'listar_comparacion','relacion':rel,'animal':b,'posicion':'segundo'}
        elif b=='X':
            plan={'intencion':'listar_comparacion','relacion':rel,'animal':a,'posicion':'primero'}
        else:
            plan={'intencion':'comparar','relacion':rel,'animal':a,'animal2':b}
    else:
        raise ConsultaNoPermitida('Predicado, argumentos o sintaxis no admitidos')
    try:
        return validar(plan)
    except (ValueError, TypeError) as exc:
        raise ConsultaNoPermitida('Consulta sobre animales, parámetros o reglas no registrados') from exc
