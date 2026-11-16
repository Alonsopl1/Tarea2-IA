"""Configuración y datos del proyecto: sin dependencias externas."""
from pathlib import Path
import os
import re
import shutil

CARPETA = Path(__file__).resolve().parent
CONOCIMIENTO = CARPETA / 'conocimiento.pl'
MOTOR = CARPETA / 'motor_prolog.pl'
MODELO = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
SWIPL = os.environ.get('SWIPL', '') or shutil.which('swipl')


def hechos() -> dict[str, int]:
    """Lee los hechos directamente del Prolog: una sola fuente de verdad."""
    texto = CONOCIMIENTO.read_text(encoding='utf-8')
    return {nombre: int(peso) for nombre, peso in
            re.findall(r'^peso\(([a-z_]+),\s*(\d+)\)\.', texto, re.MULTILINE)}


CATEGORIAS = ('diminuto', 'pequeno', 'mediano', 'grande', 'colosal')
RELACIONES = ('mas_pesado_que', 'mas_liviano_que', 'mismo_peso')
INTENCIONES = ('peso_de', 'peso_es', 'animales_peso', 'categoria_de',
              'verificar_categoria', 'listar_categoria', 'comparar',
              'listar_comparacion', 'listar_animales')
