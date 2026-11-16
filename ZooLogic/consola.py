"""Interfaz de consola para comparar Prolog y LLM traductor a Prolog."""
from chatbot import responder


def main():
    print('ZooLogic | 20 animales | Prolog / LLM')
    print('Elige modo: 1 = Prolog, 2 = LLM traductor a Prolog')
    opcion=input('Modo (1/2): ').strip()
    modo={'1':'prolog','2':'llm'}.get(opcion,'prolog')
    print('Escribe «salir» para terminar.\n')
    while True:
        try:
            pregunta=input('Tú: ').strip()
        except (EOFError,KeyboardInterrupt):
            break
        if pregunta.lower()=='salir':
            break
        r=responder(pregunta,modo)
        print('Chatbot:',r['respuesta'])
        if r.get('consulta') not in (None,'—'):
            print('Consulta Prolog:',r['consulta'])
        print()


if __name__=='__main__':
    main()
