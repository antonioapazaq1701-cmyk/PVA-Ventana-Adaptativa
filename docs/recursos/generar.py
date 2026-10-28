import ast
import io
import json
import keyword
import token
import tokenize
from pathlib import Path

from explicaciones_lineas import NOTAS

CARPETA = Path(__file__).resolve().parents[1]
PROGRAMA = CARPETA.parent / 'implementacion-pva'
NOTAS_USADAS = set()


def colores_python(fuente):
    lineas = fuente.splitlines()
    marcas = [[] for _ in lineas]
    integradas = {'print', 'len', 'range', 'min', 'max', 'int', 'str', 'bytes',
                  'sum', 'map', 'iter', 'next', 'open', 'enumerate', 'super',
                  'ValueError', 'TimeoutError', 'OSError', 'ConnectionResetError'}
    for pieza in tokenize.generate_tokens(io.StringIO(fuente).readline):
        tipo = token.tok_name[pieza.type]
        if tipo == 'NAME':
            clase = ('palabra' if keyword.iskeyword(pieza.string) else
                     'integrada' if pieza.string in integradas else
                     'constante' if pieza.string.isupper() else
                     'propia' if pieza.string == 'self' else 'nombre')
        elif tipo == 'NUMBER':
            clase = 'numero-python'
        elif tipo == 'STRING' or tipo.startswith('FSTRING'):
            clase = 'cadena'
        elif tipo == 'COMMENT':
            clase = 'comentario'
        elif tipo == 'OP':
            clase = 'operador'
        else:
            continue
        for fila in range(pieza.start[0], pieza.end[0] + 1):
            if fila > len(lineas):
                continue
            inicio = pieza.start[1] if fila == pieza.start[0] else 0
            fin = pieza.end[1] if fila == pieza.end[0] else len(lineas[fila - 1])
            if fin > inicio:
                marcas[fila - 1].append((inicio, fin, clase))

    resultado = []
    for texto, partes in zip(lineas, marcas):
        trozos = []
        posicion = 0
        for inicio, fin, clase in sorted(partes):
            if inicio < posicion:
                continue
            if inicio > posicion:
                trozos.append([texto[posicion:inicio], ''])
            trozos.append([texto[inicio:fin], clase])
            posicion = fin
        if posicion < len(texto):
            trozos.append([texto[posicion:], ''])
        if ''.join(parte[0] for parte in trozos) != texto:
            raise ValueError('Los colores no coinciden con el texto original.')
        resultado.append(trozos)
    return resultado


def notas_de_bloque(archivo, funcion, lineas, inicio):
    notas = {}
    if (archivo, funcion) in NOTAS:
        NOTAS_USADAS.add((archivo, funcion))
    for comienzo, explicacion in NOTAS.get((archivo, funcion), {}).items():
        coincidencias = [inicio + i for i, linea in enumerate(lineas)
                         if linea.strip().startswith(comienzo)]
        if not coincidencias:
            raise ValueError(f'La línea explicada ya no existe: {archivo} · {funcion} · {comienzo}')
        for numero in coincidencias:
            if numero in notas:
                raise ValueError(f'Dos explicaciones apuntan a la línea {numero} de {archivo}')
            notas[numero] = explicacion
    return notas

def pagina(titulo, cuerpo, script):
    return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+titulo+'</title><link rel="icon" href="data:,"><link rel="stylesheet" href="recursos/estilos.css"></head><body><header><div><strong>PVA · Ventana Adaptativa</strong><small>Guía de la implementación educativa</small></div><nav><a href="index.html">Cómo usar</a><a href="Codigo_explicado.html">Entender el código</a><button id="tema">Cambiar tema</button><button id="pantalla" aria-label="Pantalla completa">⛶</button></nav></header>'+cuerpo+'<script src="recursos/comun.js"></script><script src="recursos/'+script+'"></script></body></html>'

laminas = [
('Empezar','Un mensaje, dos computadoras.','''<div class="columnas"><div><p class="intro-portada">Una PC divide el texto. La otra recibe las partes y vuelve a unirlas.</p><p>Aprende a usar el programa y sigue el código real, bloque a bloque.</p><pre><code>python interfaz.py</code></pre><p class="nota">Ejecuta el comando desde la carpeta implementacion-pva. Tkinter viene con la instalación habitual de Python para Windows.</p></div><div class="escena-portada"><span class="etiqueta">UN MENSAJE · DOS EQUIPOS</span><div class="red"><div class="pc">Emisor<small>Divide y envía</small></div><span class="flecha">⇄</span><div class="pc">Receptor<small>Confirma y une</small></div></div><div class="pista-portada"><span>DATA 0</span><span>DATA 1</span><span>ACK 2</span></div><p>Una confirmación indica qué parte se espera a continuación.</p></div></div>'''),
('Preparar','La misma red. El mismo puerto.','''<div class="pasos"><article><span>1</span><h3>Copia el programa</h3><p>En ambas PCs: <code>interfaz.py</code>, <code>main.py</code>, <code>protocolo.py</code> y <code>imagenes/logo.png</code>. Necesitas Python con Tcl/Tk.</p></article><article><span>2</span><h3>Conecta las PCs</h3><p>Al mismo router mediante Wi-Fi o cable. La red debe permitir comunicar sus equipos.</p></article><article><span>3</span><h3>Busca la IPv4</h3><p>En la receptora ejecuta <code>ipconfig</code>. Anota la IPv4 de su conexión activa.</p></article></div><p class="destacado">Para probar dos ventanas en una PC, usa 127.0.0.1. Para dos PCs, escribe la IPv4 real del receptor.</p>'''),
('Recibir','Primero, prepara el receptor.','''<div class="columnas"><ol><li>Abre <code>python interfaz.py</code>.</li><li>Elige <strong>Recibir un mensaje</strong>.</li><li>Deja el puerto <strong>5050</strong>.</li><li>Pulsa <strong>Iniciar recepción</strong>.</li></ol><div class="ayuda-ventana"><h3>Recibir mensaje</h3><div class="campo">Puerto UDP &nbsp; 5050</div><button class="principal" disabled>Iniciar recepción</button><p>Esperando un mensaje…</p><p class="nota">Esquema de los controles; no conecta a la red desde esta página.</p></div></div><p class="destacado">Deja esta ventana abierta mientras envías desde la otra PC.</p>'''),
('Enviar','Ahora, escribe y envía.','''<div class="columnas"><ol><li>En la otra PC elige <strong>Enviar un mensaje</strong>.</li><li>Escribe la IPv4 del receptor y el mismo puerto.</li><li>Escribe el mensaje y pulsa <strong>Enviar</strong>.</li></ol><div class="ayuda-ventana"><h3>Enviar mensaje</h3><div class="campo">IP del receptor &nbsp; 192.168.1.20</div><div class="campo">Puerto UDP &nbsp; 5050</div><div class="campo">Hola, este mensaje viaja por partes.</div><button class="principal" disabled>Enviar</button><p class="nota">La dirección es un ejemplo: reemplázala por la de tu receptora.</p></div></div>'''),
('Observar','Cada bloque tiene varias partes.','''<p>El texto se convierte a UTF-8 y se divide en partes de hasta <strong>256 bytes</strong>. Una ventana de 2 permite enviar dos partes antes de esperar sus confirmaciones.</p><div class="sobres"><div class="sobre">0</div><div class="sobre">1</div><span class="flecha">→</span><div class="pc">Receptor</div></div><p><strong>ACK 2</strong> significa: «ya tengo 0 y 1; ahora espero la parte 2».</p><div class="laboratorio"><label for="texto-demo">Prueba la división con tu texto</label><div class="mensaje-demo"><input id="texto-demo" maxlength="1024" value="Hola, mensaje PVA 🌎" aria-describedby="resultado-fragmentos"><button id="texto-ejemplo">Cargar mensaje largo</button></div><div id="fragmentos-demo" class="fragmentos-demo"></div><p id="resultado-fragmentos" role="status"></p><p class="nota">Vista didáctica local: cortar UTF-8 puede separar un carácter. El programa une los bytes antes de leerlos.</p></div><p class="destacado">En «Mensaje y bloques» verás las partes y el mensaje completo. Los números empiezan en 0.</p>'''),
('Ventana adaptativa','De dos partes a ocho.','''<div class="ventanas"><b>2</b><span>→</span><b>4</b><span>→</span><b>6</b><span>→</span><b>8</b></div><p>Después de confirmar un bloque sin recuperación, la ventana aumenta en dos. Si vence la espera, disminuye en dos y se reenvía desde la primera parte pendiente.</p><div class="controles"><button id="paso-bloque" class="principal">Confirmar siguiente bloque</button><button id="reiniciar-bloque">Reiniciar</button></div><div class="sobres" id="sobres-demo"></div><p id="detalle-demo" role="status"></p><p class="nota">Demostración didáctica de veinte partes (5120 bytes); no es tráfico de red real ni provoca errores en el programa.</p>'''),
('Finalizar','Comprueba el mensaje completo.','''<ol><li>El emisor muestra <strong>Envío completado</strong> después de recibir la confirmación del cierre.</li><li>El receptor muestra el texto unido y la ruta <code>recibidos/recibido_SESION.txt</code>.</li><li>Para otro mensaje, deja el receptor esperando y vuelve a enviar.</li></ol><p>El receptor procesa un mensaje a la vez y permanece abierto hasta que pulses <strong>Detener</strong>. Después puedes volver a <strong>Inicio</strong> para cambiar de rol.</p><p class="destacado">Si el emisor dice «Cierre no confirmado», comprueba los recibidos: el receptor pudo guardar el texto aunque la respuesta no llegara.</p>'''),
('Si no llega','Revisa cuatro cosas.','''<table><thead><tr><th>Lo que ocurre</th><th>Qué hacer</th></tr></thead><tbody><tr><td>No hay respuesta</td><td>Inicia el receptor antes de enviar.</td></tr><tr><td>No llega a la otra PC</td><td>Comprueba su IPv4 y que ambas usen el mismo puerto.</td></tr><tr><td>Solo funciona en una PC</td><td>Permite Python en el firewall privado y evita redes de invitados.</td></tr><tr><td>Puerto ocupado</td><td>Cierra otro receptor o elige otro puerto en ambas PCs.</td></tr></tbody></table><p class="nota">No necesitas desactivar el firewall. Detener una transferencia incompleta no entrega el texto como si hubiera llegado completo.</p>'''),
('Cómo funciona','Tres archivos, tareas distintas.','''<div class="capas"><div><strong>interfaz.py</strong> · Recoge los datos y muestra la actividad. Un hilo lee la salida del programa y una cola la lleva a Tkinter.</div><div><strong>main.py</strong> · Abre el socket, envía bloques, espera ACK, recibe partes y guarda el mensaje.</div><div><strong>protocolo.py</strong> · Define la cabecera de 21 bytes, divide y une el texto, y valida los paquetes con CRC.</div></div><p>PVA organiza la mensajería sobre <strong>UDP/IP</strong>, dentro de la familia TCP/IP. Las confirmaciones y la ventana pertenecen a PVA; el transporte utilizado es UDP.</p><p><a href="Codigo_explicado.html">Abrir el código explicado por bloques</a></p>'''),
('Lo que sigue','Un envío que puede repetirse.','''<p>La versión actual transmite texto UTF-8 de hasta 1 MiB, verifica CRC y recupera datos ante esperas vencidas. OPEN y CLOSE se reintentan hasta cinco veces. El receptor sigue escuchando varios mensajes.</p><ol><li><strong>Comprobar en dos PCs:</strong> texto corto, largo y con emojis; comparar el archivo guardado.</li><li><strong>Mostrar un resumen:</strong> partes, reenvíos y tiempo de cada envío.</li><li><strong>Mejorar la recuperación:</strong> informar mejor las sesiones incompletas y revisar qué hacer si se reinicia el receptor.</li></ol><p class="nota">El receptor recuerda hasta 100 cierres durante 30 segundos mientras permanece abierto. Si se reinicia, esa memoria se pierde.</p><details><summary>Referencias e inspiración</summary><div class="fuentes"><p><a href="https://ventana-adaptativa.netlify.app/">Ventana Adaptativa</a>: sobres, ACK, ventanas 2/4/6/8 y recuperación. La presentación de referencia describe objetivos más amplios que esta implementación.</p><p>Ayuda local de AzCode: navegación de presentación y explorador de código.</p><p>Esta guía explica los archivos educativos actuales; no corresponde a PVA-Extreme.</p></div></details>''')
]
contenido='<main class="pagina">'+''.join('<section class="lamina"'+(' hidden' if i else '')+'><span class="etiqueta">'+str(i+1).zfill(2)+' / '+str(len(laminas))+' · '+titulo+'</span><h1>'+encabezado+'</h1>'+cuerpo+'</section>' for i,(titulo,encabezado,cuerpo) in enumerate(laminas))+'</main><footer class="pie"><button id="anterior">← Anterior</button><select id="indice" aria-label="Ir a una sección">'+''.join(f'<option value="{i}">{i+1}. {titulo}</option>' for i,(titulo,_,_) in enumerate(laminas))+'</select><span id="contador"></span><button id="siguiente">Siguiente →</button></footer>'
(CARPETA/'index.html').write_text(pagina('PVA · Cómo usar el programa',contenido,'presentacion.js'),encoding='utf-8')

explicaciones={
'dividir_mensaje':('Del texto a las partes','Convierte el texto a bytes UTF-8. Comprueba que ocupe entre 1 byte y 1 MiB. La comprensión de listas recorre los bytes de 256 en 256 y devuelve cada tramo; no divide por cantidad de letras.'),
'reconstruir_mensaje':('Unir antes de decodificar','join une todas las partes en un solo conjunto de bytes. decode convierte ese resultado a texto UTF-8. El orden importa: un emoji puede quedar cortado entre dos partes y solo es válido después de unirlas.'),
'crear_paquete':('Escribir un paquete','pack organiza versión, tipo, sesión, secuencia, confirmación, ventana, longitud y CRC. Primero pone el CRC en cero, calcula CRC-32 de cabecera y carga y reemplaza esos cuatro bytes. leer_paquete valida el resultado antes de devolverlo.'),
'leer_paquete':('Validar y leer','Comprueba la cabecera mínima antes de desempaquetar. Revisa versión, tipo, sesión, ventana, longitud y CRC. Después valida los campos según el tipo de paquete y los totales de OPEN. Si algo no coincide lanza ValueError; si todo coincide devuelve un diccionario con los campos.'),
'esperar_confirmacion':('Esperar sin aceptar cualquier respuesta','Fija un plazo de dos segundos usando un reloj monotónico. Cada lectura espera solo el tiempo restante. Ignora otros orígenes, paquetes inválidos, sesiones y tipos distintos. Solo devuelve un ACK dentro del rango solicitado; el tráfico irrelevante no reinicia el plazo.'),
'enviar_control':('Reintentar apertura y cierre','Envía el control y espera su respuesta. Si vence la espera, vuelve a enviarlo, hasta un máximo de cinco intentos en total. Si ninguno recibe confirmación, informa el fallo. Se usa tanto para OPEN como para CLOSE.'),
'guardar_mensaje':('Guardar una entrega','Crea recibidos junto a main.py si no existe. Usa la sesión para formar el nombre y abre con xb: crea un archivo nuevo y falla si ya existe. Escribe las partes unidas como bytes y devuelve la ruta.'),
'recibir':('Escuchar, confirmar y reconstruir','bind escucha en todas las interfaces IPv4 dentro de un while True. Cada OPEN válido fija origen, sesión y totales; una apertura repetida se vuelve a confirmar. Solo acepta la siguiente parte esperada y responde con ACK acumulativos. En CLOSE exige todos los bytes, reconstruye y guarda el texto, recuerda el cierre durante 30 segundos y responde CLOSE_ACK. Si llega un cierre repetido vuelve a confirmar sin guardar otra copia. Después sigue escuchando; una sesión sin avance también se descarta sin cerrar la escucha.'),
'enviar':('Coordinar la ventana adaptativa','Divide el texto y genera una sesión aleatoria no nula. enviar_control reintenta OPEN si es necesario. Cada bloque fija su límite con la ventana actual; los ACK adelantan primera_sin_confirmar. Una espera vencida reduce la ventana y reenvía lo pendiente, con cinco esperas sin avance como límite. Un bloque recuperado no aumenta la ventana. Al acabar reintenta CLOSE y solo anuncia éxito si llega CLOSE_ACK.'),
'limpiar':('Cambiar de página','Destruye los controles de la página actual. Los datos compartidos, como IP y puerto, permanecen en variables de la ventana.'),
'inicio':('Elegir el rol','Construye la portada con dos acciones. Los comandos de los botones abren pagina con emisor o receptor. No inicia todavía una conexión de red.'),
'pagina':('Mostrar lo necesario','Crea el botón Inicio, los campos y las acciones del rol. La IP y el cuadro del mensaje solo aparecen para el emisor. Ambos roles tienen puerto, estado y actividad. Detener se crea aquí pero solo se muestra durante la operación.'),
'iniciar':('Validar y arrancar el trabajo','Rechaza puertos fuera de rango, IP vacía o texto inválido. Construye una llamada fija a main y pasa IP y puerto como argumentos; el mensaje entra por stdin, no como código Python. Popen inicia otro proceso para que Tkinter siga respondiendo. Deshabilita iniciar e inicio, muestra Detener y arranca un hilo para leer la salida.'),
'comunicar':('Leer fuera del hilo gráfico','Escribe el mensaje en stdin y cierra ese canal. Lee la salida UTF-8 línea a línea y coloca eventos en la cola. No modifica widgets desde el hilo secundario. Al terminar cierra la salida y publica el código de finalización.'),
'actualizar':('Llevar los eventos a la pantalla','Cada 80 milisegundos procesa hasta 200 eventos pendientes. Agrega el texto a la actividad o, si terminó el proceso, restaura los controles y el estado. La cola separa el hilo lector del hilo de Tkinter.'),
'detener':('Cancelar la operación','Si hay un proceso activo lo marca como cancelado y lo termina. El evento de finalización permitirá actualizar los controles. Esta versión no envía un paquete de cancelación al otro equipo; ese extremo puede agotar su propia espera.'),
'cerrar':('Salir de la ventana','Termina el proceso de comunicación si sigue activo y destruye la ventana. El hilo lector es daemon, por lo que no mantiene abierta la aplicación.'),
'__init__':('Preparar la ventana','Configura tamaño, colores y controles ttk. Crea la cola de eventos y las variables de estado, puerto e IP. Carga el logo de imagenes/logo.png con Tkinter; si falta, muestra el nombre del programa. Registra el cierre, abre la portada y programa el primer ciclo de actualización.'),
}
bloques=[]

def agregar_bloque(archivo, nombre, clave, titulo, detalle, inicio, lineas, colores):
    bloques.append({'archivo': archivo, 'nombre': nombre, 'titulo': titulo, 'detalle': detalle,
                    'inicio': inicio, 'codigo': lineas,
                    'colores': colores[inicio - 1:inicio - 1 + len(lineas)],
                    'notas': notas_de_bloque(archivo, clave, lineas, inicio)})

for nombre in ('protocolo.py','main.py','interfaz.py'):
    fuente=(PROGRAMA/nombre).read_text(encoding='utf-8-sig'); lineas=fuente.splitlines(); arbol=ast.parse(fuente)
    colores=colores_python(fuente)
    funciones=[]
    for nodo in arbol.body:
        if isinstance(nodo,ast.FunctionDef): funciones.append(nodo)
        if isinstance(nodo,ast.ClassDef): funciones.extend(n for n in nodo.body if isinstance(n,ast.FunctionDef))
    primero=min(n.lineno for n in funciones)
    agregar_bloque(nombre, 'Preparación del archivo', 'Preparación del archivo', 'Bibliotecas y datos compartidos', ('struct fija la cabecera binaria de 21 bytes en orden de red. zlib calcula CRC-32. Las constantes fijan 256 bytes por parte, ventanas 2/4/6/8 y hasta 1 MiB de texto. Los tipos numéricos distinguen los controles de los datos.' if nombre=='protocolo.py' else 'Las importaciones hacen disponibles las herramientas utilizadas abajo. main usa sockets, un reloj monotónico y el formato del protocolo. La interfaz usa Tkinter, una cola, un hilo lector y un subproceso para mantener la ventana disponible.'), 1, lineas[:primero-1], colores)
    for nodo in funciones:
        titulo,detalle=explicaciones.get(nodo.name,('Entrada del programa','En main.py muestra el menú de consola, valida la opción y llama a enviar o recibir. En interfaz.py crea la ventana y ejecuta el bucle de eventos de Tkinter. Los bloques finales con __name__ permiten ejecutar el archivo directamente sin abrir el programa al importarlo.'))
        agregar_bloque(nombre, nodo.name+'()', nodo.name, titulo, detalle, nodo.lineno, lineas[nodo.lineno-1:nodo.end_lineno], colores)
    ultimo=max(n.end_lineno for n in funciones)
    if any(l.strip() for l in lineas[ultimo:]):
        agregar_bloque(nombre, 'Ejecución directa', 'Ejecución directa', 'Iniciar solo al ejecutar este archivo', 'La condición __name__ == "__main__" llama a main solo al ejecutar el archivo directamente. El menú de consola también captura la interrupción del usuario y la falta de entrada. Importar el módulo no arranca el menú ni abre una ventana.', ultimo+1, lineas[ultimo:], colores)
if set(NOTAS) != NOTAS_USADAS:
    raise ValueError(f'Hay explicaciones para bloques que ya no existen: {set(NOTAS) - NOTAS_USADAS}')
datos=json.dumps(bloques,ensure_ascii=False).replace('</','<\\/')
cuerpo='<div class="explorador"><aside><div class="cabecera-archivos"><span>EXPLORADOR</span><strong>El programa por dentro</strong><p>Elige una función para ver su código y las líneas explicadas.</p></div><label for="buscar">Buscar en los bloques</label><input id="buscar" placeholder="Ej. ACK, recibir, CRC"><div id="lista-bloques"></div><p id="sin-resultados" class="nota" hidden>No hay bloques para esa búsqueda.</p></aside><main class="leccion"><span id="ubicacion" class="etiqueta"></span><h1 id="titulo-bloque" aria-live="polite"></h1><p id="explicacion" class="explicacion"></p><div class="controles navegacion-codigo"><button id="bloque-anterior">← Anterior</button><button id="bloque-siguiente">Siguiente bloque →</button><span id="contador-notas" class="contador-notas" aria-live="polite"></span></div><section class="editor" aria-label="Código fuente explicado"><div class="editor-barra"><div class="puntos-editor" aria-hidden="true"><i></i><i></i><i></i></div><span class="archivo-editor" id="archivo-editor"></span><span id="rango-editor"></span><div class="editor-acciones"><button id="notas-visibles" aria-pressed="true">Ocultar explicaciones</button><button id="ajustar-lineas" aria-pressed="true">Sin ajuste</button></div></div><div id="codigo" class="lineas ajustadas" aria-label="Código con números de línea y explicaciones"></div></section><div class="leyenda-codigo"><span><i class="muestra-palabra"></i>Palabra reservada</span><span><i class="muestra-cadena"></i>Texto</span><span><i class="muestra-numero"></i>Número</span><span><i class="muestra-nota"></i>Línea explicada</span></div><p class="nota sincronizacion">Esta vista contiene el código real de los archivos. Para actualizarla después de cambiar el programa, ejecuta <code>python docs/recursos/generar.py</code> desde la raíz del repositorio.</p></main></div><script id="datos-codigo" type="application/json">'+datos+'</script>'
(CARPETA/'Codigo_explicado.html').write_text(pagina('PVA · Código explicado',cuerpo,'codigo.js'),encoding='utf-8')
print(f'Generadas {len(laminas)} secciones y {len(bloques)} bloques de código.')
