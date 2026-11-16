"""Evalúa ambos modos frente al mismo motor Prolog y registra resultados reales.
La comparación comprueba también si la consulta TRADUCIDA por Llama era adecuada.
"""
import argparse
import csv
import json
import time
from pathlib import Path
from configuracion import CARPETA, SWIPL
from chatbot import responder
from interpretacion import validar, interpretar_local
from pruebas.casos import PREGUNTAS
from pruebas.referencia import esperado, observado


def ejecutar(con_llm=False):
    rows=[]
    modos=('prolog','llm') if con_llm else ('prolog',)
    for num,q in enumerate(PREGUNTAS,1):
        plan=validar(interpretar_local(q)); ref=esperado(plan)
        for modo in modos:
            t0=time.perf_counter()
            r=responder(q,modo)
            d=r.get('resultado_prolog')
            if not r['ok']:
                if (not SWIPL and modo=='prolog') or 'Ollama no está disponible' in r.get('respuesta',''):
                    est='NO_EJECUTADO'
                else:
                    est='ERROR'
            elif d is not None:
                est='CORRECTO' if observado(d)==ref else 'INCORRECTO'
            else:
                est='SIN_CONSULTA' if r['ok'] else 'NO_EJECUTADO'
            rows.append({'numero':num,'pregunta':q,'modo':modo,
                         'esperado':json.dumps(ref,ensure_ascii=False),
                         'respuesta':r.get('respuesta',''),
                         'consulta':r.get('consulta',''),
                         'estado':est,'duracion_ms':round((time.perf_counter()-t0)*1000,1)})
            print(f'[{num:02d}/{len(PREGUNTAS)}] {modo:7} {est}')
    file=CARPETA/'resultados_evaluacion.csv'
    with file.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys(),delimiter=';')
        writer.writeheader();writer.writerows(rows)
    print('\nSe guardó:',file)
    print('Revisa INCORRECTO, NO_EJECUTADO y ERROR; no atribuyas resultados a motores ausentes.')
    return rows

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--con-llm',action='store_true',help='Probar además Llama como traductor hacia Prolog')
    args=parser.parse_args()
    ejecutar(args.con_llm)
