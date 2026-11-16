"""Servidor web local sin dependencias Python adicionales.

Arranque: python servidor.py
Visita: http://127.0.0.1:8765
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
import os
import mimetypes
from urllib.parse import urlparse
from chatbot import responder
from configuracion import CARPETA, hechos, SWIPL, MODELO

PUBLIC = CARPETA / 'web'
PORT = int(os.environ.get('PORT', '8765'))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print('[WEB]', format % args)

    def json(self, data, status=200):
        payload=json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/health':
            return self.json({'ok':True,'prolog_instalado':bool(SWIPL),
                              'modelo_ollama':MODELO,'version':'dos_versiones'})
        if path=='/api/animales':
            return self.json({'animales':[{'animal':a,'peso':p} for a,p in hechos().items()]})
        if path=='/':
            archivo=PUBLIC/'index.html'
        elif path in ('/style.css','/script.js'):
            archivo=PUBLIC/path.lstrip('/')
        else:
            return self.json({'error':'Ruta no encontrada'},404)
        if not archivo.is_file():
            return self.json({'error':'Falta archivo de interfaz'},500)
        body=archivo.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type',mimetypes.guess_type(str(archivo))[0]+'; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != '/api/chat':
            return self.json({'error':'Ruta no encontrada'},404)
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<1 or n>8192:
                return self.json({'ok':False,'respuesta':'Solicitud demasiado grande.'},413)
            data=json.loads(self.rfile.read(n).decode('utf-8'))
            if not isinstance(data,dict):
                raise ValueError('El cuerpo debe ser JSON')
            pregunta=data.get('pregunta','')
            modo=data.get('modo','prolog')
            if not isinstance(modo,str) or modo not in ('prolog','llm'):
                return self.json({'ok':False,'respuesta':'Modo no válido.'},400)
            if not isinstance(pregunta,str) or len(pregunta)>1000:
                return self.json({'ok':False,'respuesta':'La pregunta debe ser texto (máximo 1000 caracteres).'},400)
            return self.json(responder(pregunta,modo))
        except (ValueError,UnicodeDecodeError,json.JSONDecodeError) as e:
            return self.json({'ok':False,'respuesta':'Error de formato: '+str(e)},400)
        except Exception as e:
            return self.json({'ok':False,'respuesta':'Error interno del servidor. Revisa la terminal.'},500)


def iniciar(host=None, port=PORT):
    host = host or os.environ.get('ZOOLOGIC_HOST', '127.0.0.1')
    httpd=ThreadingHTTPServer((host,port),Handler)
    print('\nZooLogic · CINF103 · Proyecto 2')
    print(f'Abre en tu navegador: http://{host}:{httpd.server_address[1]}')
    print('Ctrl+C para detener el servidor.')
    return httpd


if __name__=='__main__':
    try:
        iniciar().serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')
