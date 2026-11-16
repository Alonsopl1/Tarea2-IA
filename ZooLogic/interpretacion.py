"""Interprete determinista de preguntas frecuentes para la version Prolog.

No contiene hechos ni resultados precargados: extrae los animales reales de
conocimiento.pl. No pretende reemplazar la interpretacion por LLM.
"""
import re
import unicodedata
from configuracion import hechos, CATEGORIAS, RELACIONES, INTENCIONES


def normalizar(s: str) -> str:
    s = unicodedata.normalize('NFD', s.lower().replace('_', ' '))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', s)).strip()


def animales_mencionados(s: str) -> list[str]:
    texto = normalizar(s)
    hallados = []
    for animal in hechos():
        nombre = normalizar(animal)
        for match in re.finditer(r'(?<!\w)' + re.escape(nombre) + r'(?!\w)', texto):
            hallados.append((match.start(), -(match.end()-match.start()), animal))
    hallados.sort()
    return [a for _pos, _tam, a in hallados]


def interpretar_local(pregunta: str) -> dict:
    t = normalizar(pregunta)
    a = animales_mencionados(pregunta)
    if not t:
        return {'intencion': 'fuera_dominio'}
    cats = {'diminutos':'diminuto','diminutas':'diminuto','diminuta':'diminuto',
            'pequenos':'pequeno','pequenas':'pequeno','pequena':'pequeno',
            'medianos':'mediano','medianas':'mediano','mediana':'mediano',
            'grandes':'grande','colosales':'colosal'}
    cats.update({c:c for c in CATEGORIAS})
    cats_presentes = [cats[x] for x in re.findall(r'\b(?:diminutos?|diminutas?|pequenos?|pequenas?|medianos?|medianas?|grandes?|colosal(?:es)?)\b',t)]
    categoria = cats_presentes[0] if cats_presentes else None
    numero = re.search(r'\b(\d+(?:[.,]\d+)?)\s*(?:kg|kilos?|kilogramos?)\b', t)
    peso = float(numero.group(1).replace(',','.')) if numero else None
    if peso is not None and peso.is_integer():
        peso = int(peso)

    # Listados por peso exacto: peso(X, N)
    if not a and peso is not None and ('animal' in t or 'quienes' in t):
        return {'intencion':'animales_peso','peso':peso}
    if any(x in t for x in ('todos los animales','lista de animales','animales conoces')) and not categoria and not a and peso is None:
        return {'intencion':'listar_animales'}

    # Comparaciones, incluso las preguntas sobre listas con variable X.
    igual = any(x in t for x in ('mismo peso','lo mismo','pesan igual','igual peso'))
    menor = any(x in t for x in ('mas livian', 'mas liger', 'menos pesa','pesa menos',
                                 'pesan menos', 'menor peso'))
    mayor = any(x in t for x in ('mas pesad', 'pesan mas','pesa mas', 'mayor peso'))
    rel = 'mismo_peso' if igual else ('mas_liviano_que' if menor else ('mas_pesado_que' if mayor else None))
    if rel and len(a) >= 2:
        return {'intencion':'comparar','animal':a[0],'animal2':a[1],'relacion':rel}
    if rel and len(a) == 1:
        # "¿Qué animales pesan más que el tigre?" -> rel(X,tigre)
        # "¿El tigre pesa más que cuáles animales?" -> rel(tigre,X)
        primero = bool(re.match(r'^(que|cuales)\b|^lista\b|^listar\b', t))
        return {'intencion':'listar_comparacion','animal':a[0],
                'relacion':rel,'posicion':'segundo' if primero else 'primero'}

    if categoria:
        if a:
            return {'intencion':'verificar_categoria','animal':a[0],'categoria':categoria}
        return {'intencion':'listar_categoria','categoria':categoria}

    if len(a) == 1:
        if any(x in t for x in ('categoria','clasifica','clasificacion','tipo de peso','que tamano')):
            return {'intencion':'categoria_de','animal':a[0]}
        if peso is not None and ('pesa' in t or 'peso' in t):
            return {'intencion':'peso_es','animal':a[0],'peso':peso}
        if any(x in t for x in ('peso', 'pesa', 'kilos', 'kilogramos')):
            return {'intencion':'peso_de','animal':a[0]}

    return {'intencion':'fuera_dominio'}


def validar(plan: dict) -> dict:
    """Allowlist: rechaza consultas arbitrarias, animales no registrados e inyecciones."""
    if not isinstance(plan,dict):
        raise ValueError('La interpretación debe ser un objeto JSON.')
    intent = plan.get('intencion')
    if intent == 'fuera_dominio':
        return {'intencion':'fuera_dominio'}
    if intent not in INTENCIONES:
        raise ValueError('Intención no permitida. Solo se admiten las consultas definidas.')
    req = {'peso_de':('animal',), 'peso_es':('animal','peso'),
           'animales_peso':('peso',), 'categoria_de':('animal',),
           'verificar_categoria':('animal','categoria'), 'listar_categoria':('categoria',),
           'comparar':('animal','animal2','relacion'),
           'listar_comparacion':('animal','relacion','posicion'),
           'listar_animales':()}[intent]
    limpio = {'intencion':intent}
    for key in req:
        value=plan.get(key)
        if key in ('animal','animal2'):
            if not isinstance(value,str) or value not in hechos():
                raise ValueError(f'El animal «{value}» no está en los 20 animales registrados.')
        elif key=='categoria':
            if value not in CATEGORIAS:
                raise ValueError('Categoría desconocida.')
        elif key=='relacion':
            if value not in RELACIONES:
                raise ValueError('Relación no permitida.')
        elif key=='posicion':
            if value not in ('primero','segundo'):
                raise ValueError('Posición de variable no permitida.')
        elif key=='peso':
            if isinstance(value,bool) or not isinstance(value,(int,float)) or value < 0 or value > 10000000:
                raise ValueError('Peso no válido.')
        limpio[key]=value
    return limpio
