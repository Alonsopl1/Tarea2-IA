% Adaptador seguro: recibe JSON por stdin y devuelve un unico JSON por stdout.
% No evalua texto Prolog procedente del usuario ni del LLM.
:- use_module(library(http/json)).

main :-
    catch(
        ( json_read_dict(user_input, Pregunta),
          ( resolver(Pregunta, Respuesta) -> true
          ; Respuesta = _{estado:"error",mensaje:"Consulta no admitida"} ),
          json_write_dict(current_output, Respuesta), nl
        ),
        Error,
        ( message_to_string(Error, Texto),
          json_write_dict(current_output, _{estado:"error",mensaje:Texto}), nl )
    ).

texto_atomico(Dict, Campo, Atomo) :-
    get_dict(Campo, Dict, Texto),
    string(Texto),
    atom_string(Atomo, Texto).

categoria_valida(diminuto).
categoria_valida(pequeno).
categoria_valida(mediano).
categoria_valida(grande).
categoria_valida(colosal).

regla_categoria(diminuto, X) :- diminuto(X).
regla_categoria(pequeno, X) :- pequeno(X).
regla_categoria(mediano, X) :- mediano(X).
regla_categoria(grande, X) :- grande(X).
regla_categoria(colosal, X) :- colosal(X).

regla_comparacion(mas_pesado_que, X, Y) :- mas_pesado_que(X,Y).
regla_comparacion(mas_liviano_que, X, Y) :- mas_liviano_que(X,Y).
regla_comparacion(mismo_peso, X, Y) :- mismo_peso(X,Y).

resolver(D, R) :-
    get_dict(intencion, D, "listar_animales"), !,
    findall(_{animal:A,peso:P}, peso(A,P), Lista),
    R = _{estado:"ok",tipo:"todos",animales:Lista}.

resolver(D, R) :-
    get_dict(intencion, D, "peso_de"), !,
    texto_atomico(D, animal, A),
    ( peso(A, P) -> R = _{estado:"ok",tipo:"peso",animal:A,peso:P}
    ; R = _{estado:"no_conocido",animal:A} ).

resolver(D, R) :-
    get_dict(intencion, D, "peso_es"), !,
    texto_atomico(D, animal, A), get_dict(peso, D, Solicitado),
    ( peso(A, P) ->
        ( P =:= Solicitado -> Verdad = true ; Verdad = false ),
        R = _{estado:"ok",tipo:"peso_es",animal:A,peso:P,solicitado:Solicitado,verdad:Verdad}
    ; R = _{estado:"no_conocido",animal:A} ).

resolver(D, R) :-
    get_dict(intencion, D, "animales_peso"), !,
    get_dict(peso, D, Solicitado),
    findall(A, peso(A, Solicitado), Lista),
    R = _{estado:"ok",tipo:"lista_peso",peso:Solicitado,animales:Lista}.

resolver(D, R) :-
    get_dict(intencion, D, "categoria_de"), !,
    texto_atomico(D, animal, A),
    ( peso(A, P) ->
        ( once(regla_categoria(C, A)) -> atom_string(C, TextoC)
        ; TextoC = "sin_categoria" ),
        R = _{estado:"ok",tipo:"categoria",animal:A,peso:P,categoria:TextoC}
    ; R = _{estado:"no_conocido",animal:A} ).

resolver(D, R) :-
    get_dict(intencion, D, "verificar_categoria"), !,
    texto_atomico(D, animal, A), texto_atomico(D, categoria, C), categoria_valida(C),
    ( peso(A, P) ->
        ( regla_categoria(C, A) -> Verdad = true ; Verdad = false ),
        R = _{estado:"ok",tipo:"categoria_es",animal:A,peso:P,categoria:C,verdad:Verdad}
    ; R = _{estado:"no_conocido",animal:A} ).

resolver(D, R) :-
    get_dict(intencion, D, "listar_categoria"), !,
    texto_atomico(D, categoria, C), categoria_valida(C),
    findall(A, regla_categoria(C, A), Lista),
    R = _{estado:"ok",tipo:"lista_categoria",categoria:C,animales:Lista}.

resolver(D, R) :-
    get_dict(intencion, D, "comparar"), !,
    texto_atomico(D, animal, A), texto_atomico(D, animal2, B),
    texto_atomico(D, relacion, Rel),
    memberchk(Rel,[mas_pesado_que,mas_liviano_que,mismo_peso]),
    ( peso(A, PA), peso(B, PB) ->
        ( regla_comparacion(Rel,A,B) -> Verdad=true ; Verdad=false ),
        R = _{estado:"ok",tipo:"comparacion",animal:A,animal2:B,peso_a:PA,peso_b:PB,relacion:Rel,verdad:Verdad}
    ; R = _{estado:"no_conocido",mensaje:"Uno o ambos animales no estan registrados"} ).

resolver(D, R) :-
    get_dict(intencion, D, "listar_comparacion"), !,
    texto_atomico(D, animal, A), texto_atomico(D, relacion, Rel),
    texto_atomico(D, posicion, Posicion),
    memberchk(Rel,[mas_pesado_que,mas_liviano_que,mismo_peso]),
    memberchk(Posicion,[primero,segundo]),
    ( peso(A, P) ->
        ( Posicion == primero ->
            findall(X, regla_comparacion(Rel,A,X), Lista)
        ; findall(X, regla_comparacion(Rel,X,A), Lista) ),
        R = _{estado:"ok",tipo:"lista_comparacion",animal:A,peso:P,relacion:Rel,posicion:Posicion,animales:Lista}
    ; R = _{estado:"no_conocido",animal:A} ).
