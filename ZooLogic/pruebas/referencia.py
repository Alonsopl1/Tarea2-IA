"""Oráculo de resultados esperados para contrastar salidas; NO es el chatbot.

Implementación separada, usada solamente por los tests y el informe; los datos
se leen de conocimiento.pl y NO se utilizan para responder al usuario.
"""
from configuracion import hechos


def categoria(p: int) -> str | None:
    if p<=2: return 'diminuto'
    if 3<=p<=50: return 'pequeno'
    if 51<=p<=300: return 'mediano'
    if 301<=p<=2000: return 'grande'
    if p>2000: return 'colosal'
    return None


def relacion(rel: str, a: str, b: str, data: dict) -> bool:
    if rel == 'mas_pesado_que': return data[a] > data[b]
    if rel == 'mas_liviano_que': return data[a] < data[b]
    return a!=b and data[a] == data[b]


def esperado(plan: dict):
    d=hechos(); i=plan['intencion']; a=plan.get('animal'); b=plan.get('animal2')
    if i=='peso_de':return d[a]
    if i=='peso_es':return d[a] == plan['peso']
    if i=='animales_peso':return [x for x,p in d.items() if p==plan['peso']]
    if i=='categoria_de':return categoria(d[a])
    if i=='verificar_categoria':return categoria(d[a])==plan['categoria']
    if i=='listar_categoria':return [x for x,p in d.items() if categoria(p)==plan['categoria']]
    if i=='comparar':return relacion(plan['relacion'], a, b, d)
    if i=='listar_comparacion':
        return [x for x in d if (relacion(plan['relacion'],a,x,d) if plan['posicion']=='primero'
                                else relacion(plan['relacion'],x,a,d))]
    if i=='listar_animales':return [{'animal':x,'peso':p} for x,p in d.items()]
    raise ValueError('Sin referencia')


def observado(prolog_resultado):
    t=prolog_resultado['tipo']
    if t=='peso':return prolog_resultado['peso']
    if t in ('peso_es','categoria_es','comparacion'):return prolog_resultado['verdad']
    if t in ('lista_peso','lista_categoria','lista_comparacion'):return prolog_resultado['animales']
    if t=='categoria':return None if prolog_resultado['categoria']=='sin_categoria' else prolog_resultado['categoria']
    if t=='todos':return prolog_resultado['animales']
    raise ValueError('Respuesta inesperada')
