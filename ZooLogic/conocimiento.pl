% Fundamentos de Inteligencia Artificial
% NRC: 8328
% Tema: Animales (categorías por peso y comparaciones)


% --------
% HECHOS
% --------


% peso(Animal, Kilos): peso promedio aproximado de un animal adulto, en kilogramos.
peso(ballena_azul,150000). % Se declara que el peso de la ballena azul es de 150000 kg.
peso(elefante,6000). % Se declara que el peso del elefante es de 6000 kg.
peso(rinoceronte,2300). % Se declara que el peso del rinoceronte es de 2300 kg.
peso(hipopotamo,1500). % Se declara que el peso del hipopótamo es de 1500 kg.
peso(jirafa,1200). % Se declara que el peso de la jirafa es de 1200 kg.
peso(oso_polar,450). % Se declara que el peso del oso polar es de 450 kg.
peso(tigre,220). % Se declara que el peso del tigre es de 220 kg.
peso(leon,190). % Se declara que el peso del león es de 190 kg.
peso(gorila,160). % Se declara que el peso del gorila es de 160 kg.
peso(jaguar,100). % Se declara que el peso del jaguar es de 100 kg.
peso(puma,100). % Se declara que el peso del puma es de 100 kg.
peso(lobo,40). % Se declara que el peso del lobo es de 40 kg.
peso(pinguino,30). % Se declara que el peso del pingüino emperador es de 30 kg.
peso(zorro,8). % Se declara que el peso del zorro es de 8 kg.
peso(gato,4). % Se declara que el peso del gato es de 4 kg.
peso(aguila,4). % Se declara que el peso del águila calva es de 4 kg.
peso(conejo,2). % Se declara que el peso del conejo es de 2 kg.
peso(loro,1). % Se declara que el peso del loro es de 1 kg.
peso(hamster,1). % Se declara que el peso del hámster es de 1 kg.
peso(ardilla,1). % Se declara que el peso de la ardilla es de 1 kg.

% --------
% REGLAS
% --------

% ----- Categorías de peso -----

% Determina si un animal es diminuto.
% Debe pesar 2 kg o menos.
diminuto(X):- peso(X,Y), Y=<2.

% Determina si un animal es pequeño.
% Debe pesar entre 3 y 50 kg inclusive.
pequeno(X):- peso(X,Y), Y>=3, Y=<50.

% Determina si un animal es mediano.
% Debe pesar entre 51 y 300 kg inclusive.
mediano(X):- peso(X,Y), Y>=51, Y=<300.

% Determina si un animal es grande.
% Debe pesar entre 301 y 2000 kg inclusive.
grande(X):- peso(X,Y), Y>=301, Y=<2000.

% Determina si un animal es colosal.
% Debe pesar más de 2000 kg.
colosal(X):- peso(X,Y), Y>2000.

% ----- Mayores, menores e iguales -----

% Verifica si el animal X pesa más que el animal Y.
% Obtiene los pesos de ambos animales y compara si PX es mayor que PY.
mas_pesado_que(X,Y):- peso(X,PX), peso(Y,PY), PX>PY.

% Verifica si el animal X pesa menos que el animal Y.
% Obtiene los pesos de ambos animales y compara si PX es menor que PY.
mas_liviano_que(X,Y):- peso(X,PX), peso(Y,PY), PX<PY.

% Verifica si los animales X e Y tienen el mismo peso.
% Además, comprueba que X e Y no sean el mismo animal.
mismo_peso(X,Y):- peso(X,PX), peso(Y,PY), PX=:=PY, X \= Y.
