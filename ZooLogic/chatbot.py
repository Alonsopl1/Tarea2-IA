"""Dos modos: intérprete local + Prolog, o LLM traductor + Prolog."""
from interpretacion import interpretar_local, validar
from prolog_backend import consultar
from llm_ollama import traducir_pregunta
from consulta_prolog import parsear_consulta, ConsultaNoPermitida


def nombre(animal: str) -> str:
    return animal.replace('_',' ')


def kilos(peso) -> str:
    return f'{peso:,}'.replace(',', '.') if isinstance(peso,int) else str(peso)


def representacion(plan: dict) -> str:
    i=plan.get('intencion'); a=plan.get('animal'); b=plan.get('animal2')
    if i == 'peso_de': return f'peso({a}, P)'
    if i == 'peso_es': return f'peso({a}, {plan["peso"]})'
    if i == 'animales_peso': return f'peso(X, {plan["peso"]})'
    if i == 'categoria_de': return ';'.join(f'{cat}({a})' for cat in ('diminuto','pequeno','mediano','grande','colosal'))
    if i == 'verificar_categoria': return f'{plan["categoria"]}({a})'
    if i == 'listar_categoria': return f'{plan["categoria"]}(X)'
    if i == 'comparar': return f'{plan["relacion"]}({a}, {b})'
    if i == 'listar_comparacion':
        return f'{plan["relacion"]}({a}, X)' if plan['posicion']=='primero' else f'{plan["relacion"]}(X, {a})'
    if i == 'listar_animales': return 'peso(X, P)'
    return '—'


def respuesta_natural(r: dict) -> str:
    if r.get('estado')=='no_conocido':
        return 'No tengo información suficiente de ese animal en mi base de conocimientos.'
    t=r.get('tipo')
    if t=='peso':
        return f'El {nombre(r["animal"])} pesa aproximadamente {kilos(r["peso"])} kg.'
    if t=='peso_es':
        return (f'{"Sí" if r["verdad"] else "No"}. El {nombre(r["animal"])} '
                f'pesa aproximadamente {kilos(r["peso"])} kg; se consultaron {kilos(r["solicitado"])} kg.')
    if t=='lista_peso':
        lis=r['animales']
        return (f'Los animales registrados que pesan {kilos(r["peso"])} kg son: '+', '.join(map(nombre,lis))+'.') if lis else 'No hay animales registrados con ese peso.'
    if t=='categoria':
        c=r['categoria']
        if c=='sin_categoria':
            return 'Según las reglas actuales, el animal no corresponde a ninguna categoría de peso.'
        return f'El {nombre(r["animal"])} pertenece a la categoría «{c}» ({kilos(r["peso"])} kg).'
    if t=='categoria_es':
        return (f'{"Sí" if r["verdad"] else "No"}. El {nombre(r["animal"])} '
                f'{"sí es" if r["verdad"] else "no es"} {r["categoria"]} según las reglas de peso.')
    if t=='lista_categoria':
        lis=r['animales']
        return f'Animales de categoría «{r["categoria"]}»: '+(', '.join(map(nombre,lis)) if lis else 'ninguno')+'.'
    if t=='comparacion':
        if r['relacion']=='mismo_peso' and r['animal']==r['animal2']:
            return 'No. La regla mismo_peso exige comparar dos animales distintos.'
        a,b=nombre(r['animal']), nombre(r['animal2'])
        rel={'mas_pesado_que':'pesa más que','mas_liviano_que':'pesa menos que','mismo_peso':'tiene el mismo peso que'}[r['relacion']]
        return (f'{"Sí" if r["verdad"] else "No"}. {a.capitalize()} '
                f'{"sí" if r["verdad"] else "no"} {rel} {b} según nuestras reglas '
                f'({kilos(r["peso_a"])} kg y {kilos(r["peso_b"])} kg).')
    if t=='lista_comparacion':
        lis=r['animales']
        base=nombre(r['animal']); rel=r['relacion']; pos=r['posicion']
        frase = (
            ('que pesan más que '+base) if rel=='mas_pesado_que' and pos=='segundo' else
            ('que pesan menos que '+base) if rel=='mas_liviano_que' and pos=='segundo' else
            ('más livianos que '+base) if rel=='mas_pesado_que' else
            ('más pesados que '+base) if rel=='mas_liviano_que' else
            ('con el mismo peso que '+base))
        if rel=='mismo_peso': frase='con el mismo peso que '+base
        return ('Los animales '+frase+' son: '+', '.join(map(nombre,lis))+'.') if lis else 'No hay animales registrados que cumplan esa comparación.'
    if t=='todos':
        return 'Animales disponibles: '+', '.join(nombre(x['animal']) for x in r['animales'])+'.'
    return 'No se pudo resolver la consulta.'


def corroborar_comparacion_explicita(pregunta: str, plan: dict) -> None:
    """Detecta inversiones obvias del LLM en preguntas binarias reconocibles.

    Es una validación de intención, no una evaluación de hechos: únicamente
    el motor Prolog calcula si la comparación es verdadera o falsa.
    """
    original=interpretar_local(pregunta)
    if original.get('intencion')!='comparar':
        return
    if plan.get('intencion')!='comparar':
        raise ConsultaNoPermitida('La comparación cambió de tipo')
    a,b,r=original['animal'],original['animal2'],original['relacion']
    a2,b2,r2=plan['animal'],plan['animal2'],plan['relacion']
    if (a,b,r)==(a2,b2,r2):
        return
    inversa={'mas_pesado_que':'mas_liviano_que',
             'mas_liviano_que':'mas_pesado_que',
             'mismo_peso':'mismo_peso'}
    if (b,a,inversa[r])==(a2,b2,r2):
        return
    raise ConsultaNoPermitida('El orden o la relación no corresponden a la pregunta')


def responder(pregunta: str, modo: str='prolog') -> dict:
    """En ambos modos SOLO SWI-Prolog produce la respuesta factual.

    Modo prolog: intérprete Python determinista.
    Modo llm: Llama 3.2 traduce -> consulta permitida -> Prolog.
    """
    if not isinstance(pregunta,str) or not pregunta.strip():
        return {'ok':False,'respuesta':'Escribe una pregunta antes de continuar.'}
    if modo not in ('prolog','llm'):
        return {'ok':False,'respuesta':'Modo no válido.'}
    try:
        if modo=='llm':
            consulta_llm=traducir_pregunta(pregunta)
            if consulta_llm is None:
                return {'ok':True,'respuesta':'Esa pregunta está fuera de mi base de conocimientos de pesos y categorías de animales.',
                        'modo':modo,'motor':'Llama 3.2 (traducción) · sin ejecución',
                        'consulta':'—','interpretacion':None}
            plan=parsear_consulta(consulta_llm)
            corroborar_comparacion_explicita(pregunta, plan)
            consulta=representacion(plan)
        else:
            plan=interpretar_local(pregunta)
            if plan['intencion']=='fuera_dominio':
                return {'ok':True,'respuesta':'No puedo interpretar esa pregunta con las reglas de pesos y comparaciones disponibles.',
                        'consulta':'—','interpretacion':None,'modo':'prolog','motor':'Intérprete local'}
            plan=validar(plan)
            consulta=representacion(plan)
        resultado=consultar(plan)
        return {'ok':True,'respuesta':respuesta_natural(resultado),
                'consulta':consulta,'interpretacion':plan,
                'resultado_prolog':resultado,'modo':modo,
                'motor':('Ollama → SWI-Prolog' if modo=='llm' else 'SWI-Prolog')}
    except ConsultaNoPermitida:
        return {'ok':True,'respuesta':'No pude traducir la pregunta a una consulta válida de nuestra base. Prueba con animales, pesos o comparaciones disponibles.',
                'consulta':'—','modo':modo,'motor':'Consulta rechazada antes de Prolog'}
    except (RuntimeError, ValueError, TypeError) as exc:
        # No mostrar respuestas crudas del LLM, reglas internas ni prompts al usuario.
        from llm_ollama import TraduccionInvalida, LLMNoDisponible
        if isinstance(exc,TraduccionInvalida):
            mensaje='El modelo no entregó una consulta válida. Reformula la pregunta e inténtalo de nuevo.'
        elif isinstance(exc,LLMNoDisponible):
            mensaje='Ollama no está disponible. Revisa que esté activo y que el modelo esté descargado.'
        else:
            mensaje='No fue posible ejecutar la consulta en Prolog. Revisa que SWI-Prolog esté instalado y los archivos sean correctos.'
        return {'ok':False,'respuesta':mensaje,'modo':modo}
