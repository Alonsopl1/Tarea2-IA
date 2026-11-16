import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from configuracion import hechos, CONOCIMIENTO, SWIPL
from interpretacion import interpretar_local, validar
from chatbot import responder, representacion
from prolog_backend import consultar
from pruebas.casos import PREGUNTAS
from pruebas.referencia import esperado, observado


class TestBase(unittest.TestCase):
    def test_20_hechos_originales(self):
        d=hechos()
        self.assertEqual(len(d),20)
        self.assertEqual(d['ballena_azul'],150000)
        self.assertEqual(d['elefante'],6000)
        self.assertEqual(d['loro'],1)
        self.assertEqual(d['jaguar'],d['puma'])

    def test_ocho_reglas(self):
        texto=CONOCIMIENTO.read_text(encoding='utf8')
        for regla in ('diminuto','pequeno','mediano','grande','colosal',
                      'mas_pesado_que','mas_liviano_que','mismo_peso'):
            self.assertIn(regla+'(X',texto)
        self.assertNotIn('?- ',texto)

    def test_20_intenciones(self):
        self.assertEqual(len(PREGUNTAS),20)
        for q in PREGUNTAS:
            with self.subTest(pregunta=q):
                plan=validar(interpretar_local(q))
                self.assertNotEqual(plan['intencion'],'fuera_dominio')
                self.assertIsNotNone(esperado(plan))

    def test_orientacion_de_listas(self):
        p1=validar(interpretar_local('¿Qué animales pesan más que el tigre?'))
        p2=validar(interpretar_local('¿El tigre pesa más que cuáles animales?'))
        self.assertEqual(p1['posicion'],'segundo')
        self.assertEqual(p2['posicion'],'primero')
        self.assertEqual(len(esperado(p1)),6)
        self.assertEqual(len(esperado(p2)),13)

    def test_variantes_sin_pregunta_literal(self):
        for q in ('¿Me puedes decir cuánto pesa el elefante?',
                  'Dime el peso del elefante',
                  '¿CUÁNTO PESA EL ELEFANTE?'):
            self.assertEqual(interpretar_local(q)['intencion'],'peso_de')

    def test_fuera_de_dominio(self):
        self.assertEqual(interpretar_local('¿Cuántos años vive el león?')['intencion'],'fuera_dominio')

    def test_inyeccion_rechazada(self):
        with self.assertRaises(ValueError):
            validar({'intencion':'comparar','animal':'elefante);halt.','animal2':'leon','relacion':'mas_pesado_que'})
        with self.assertRaises(ValueError):
            validar({'intencion':'consultar_prolog_libre','query':'halt.'})
        with self.assertRaises(ValueError):
            validar({'intencion':'listar_categoria','categoria':'asserta(peso(foo,1))'})

    def test_consulta_de_cada_predicado(self):
        for q in PREGUNTAS:
            plan=validar(interpretar_local(q))
            self.assertTrue(representacion(plan))

    def test_esperados(self):
        self.assertEqual(esperado(validar(interpretar_local('¿Qué animales son colosales?'))),
                         ['ballena_azul','elefante','rinoceronte'])
        self.assertEqual(esperado(validar(interpretar_local('¿Qué animales pesan 1 kg?'))),
                         ['loro','hamster','ardilla'])
        self.assertEqual(esperado(validar(interpretar_local('¿El gato es un animal mediano?'))),False)

    def test_llm_traductor_llama_prolog(self):
        # Prueba simulada del enrutamiento; no se presenta como llamada real a Ollama.
        fake={'estado':'ok','tipo':'peso','animal':'elefante','peso':6000}
        with patch('chatbot.traducir_pregunta',return_value='peso(elefante,P).') as llm, \
             patch('chatbot.consultar',return_value=fake) as prolog:
            r=responder('¿Cuánto pesa el elefante?','llm')
        llm.assert_called_once()
        prolog.assert_called_once()
        self.assertTrue(r['ok']);self.assertEqual(r['consulta'],'peso(elefante, P)')
        self.assertIn('6.000',r['respuesta'])

    def test_modo_no_permitido(self):
        self.assertFalse(responder('¿Cuánto pesa el elefante?', 'cualquier_otro')['ok'])

    def test_transporte_json_a_swi_prolog_simulado(self):
        # Prueba solo el transporte Python; NO reemplaza la ejecución real en SWI.
        from unittest.mock import MagicMock
        with patch('prolog_backend.SWIPL', 'swipl'), patch('prolog_backend.subprocess.run') as run:
            run.return_value=MagicMock(returncode=0, stdout='{"estado":"ok","tipo":"peso","animal":"elefante","peso":6000}', stderr='')
            salida=consultar({'intencion':'peso_de','animal':'elefante'})
            self.assertEqual(salida['peso'], 6000)
            self.assertIn('"peso_de"',run.call_args.kwargs['input'])
            self.assertFalse(run.call_args.kwargs['check'])

    def test_cadena_prolog_simulada(self):
        # Prueba de la orquestación; la conexión SWI-Prolog real se prueba abajo.
        with patch('chatbot.consultar',return_value={'estado':'ok','tipo':'peso','animal':'elefante','peso':6000}):
            r=responder('¿Me puedes decir cuánto pesa el elefante?', 'prolog')
            self.assertTrue(r['ok'])
            self.assertEqual(r['consulta'],'peso(elefante, P)')
            self.assertIn('6.000',r['respuesta'])

    @unittest.skipUnless(SWIPL,'SWI-Prolog no está instalado: la prueba end-to-end se ejecutará en Windows al instalarlo.')
    def test_20_en_swi_prolog(self):
        for q in PREGUNTAS:
            with self.subTest(pregunta=q):
                plan=validar(interpretar_local(q))
                r=consultar(plan)
                self.assertEqual(observado(r),esperado(plan))

    @unittest.skipUnless(SWIPL,'SWI-Prolog no está instalado.')
    def test_servidor_respondedor_real(self):
        r=responder('¿Cuánto pesa el elefante?', 'prolog')
        self.assertTrue(r['ok'],r)
        self.assertIn('6.000',r['respuesta'])

if __name__ == '__main__': unittest.main()
