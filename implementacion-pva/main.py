import secrets
import socket
import struct
import time
from pathlib import Path

from protocolo import (
    ABRIR, APERTURA_CONFIRMADA, DATOS, CONFIRMAR, CERRAR, CIERRE_CONFIRMADO,
    crear_paquete, leer_paquete, dividir_mensaje, reconstruir_mensaje, BYTES_POR_PARTE,
)

TIEMPO_ESPERA = 2
INTENTOS_MAXIMOS = 5
TIEMPO_SIN_AVANCE = 12
TIEMPO_CIERRE = 30


def esperar_confirmacion(conexion, destino, sesion, tipo, confirmado=0, maximo=None):
    if maximo is None:
        maximo = confirmado
    plazo_espera = time.monotonic() + TIEMPO_ESPERA
    while True:
        segundos_restantes = plazo_espera - time.monotonic()
        if segundos_restantes <= 0:
            raise TimeoutError("No llegó la confirmación en 2 segundos.")
        conexion.settimeout(segundos_restantes)
        try:
            datos, origen = conexion.recvfrom(65535)
        except ConnectionResetError:
            continue
        if origen != destino:
            continue
        try:
            paquete = leer_paquete(datos)
        except ValueError:
            continue
        if (paquete["sesion"] == sesion and paquete["tipo"] == tipo
                and confirmado <= paquete["confirmado"] <= maximo):
            return paquete["confirmado"]


def enviar_control(conexion, destino, paquete, sesion, confirmacion, confirmado=0):
    for intento in range(1, INTENTOS_MAXIMOS + 1):
        conexion.sendto(paquete, destino)
        try:
            return esperar_confirmacion(conexion, destino, sesion, confirmacion, confirmado)
        except TimeoutError:
            if intento == INTENTOS_MAXIMOS:
                raise TimeoutError("No llegó la confirmación después de cinco intentos.")
            print(f"Sin confirmación. Reintento {intento} de {INTENTOS_MAXIMOS - 1}.", flush=True)


def guardar_mensaje(sesion, partes):
    carpeta = Path(__file__).resolve().parent / "recibidos"
    carpeta.mkdir(exist_ok=True)
    archivo = carpeta / f"recibido_{sesion}.txt"
    with archivo.open("xb") as salida:
        salida.write(b"".join(partes))
    return archivo


def recibir(puerto):
    sesion = None
    cierres_recientes = {}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
        conexion.bind(("0.0.0.0", puerto))
        print(f"Espero mensajes en el puerto {puerto}...", flush=True)
        while True:
            if sesion is not None and time.monotonic() >= plazo_espera:
                print("Sesión incompleta: sin avance durante 12 segundos. Espero otro mensaje.", flush=True)
                sesion = None
            if sesion is None:
                conexion.settimeout(None)
            else:
                conexion.settimeout(max(0.001, plazo_espera - time.monotonic()))
            try:
                datos, origen = conexion.recvfrom(65535)
            except (TimeoutError, ConnectionResetError):
                continue
            try:
                paquete = leer_paquete(datos)
            except ValueError as error:
                print(f"Descarto paquete: {error}", flush=True)
                continue
            tipo = paquete["tipo"]
            ahora = time.monotonic()
            cierres_recientes = {clave: cierre for clave, cierre in cierres_recientes.items()
                                if cierre[1] > ahora}
            clave_sesion = (origen, paquete["sesion"])
            if clave_sesion in cierres_recientes:
                if tipo == CERRAR:
                    total_confirmado = cierres_recientes[clave_sesion][0]
                    conexion.sendto(crear_paquete(CIERRE_CONFIRMADO, paquete["sesion"],
                                                 confirmado=total_confirmado), origen)
                    print("CLOSE repetido. Vuelvo a confirmar sin guardar otra copia.", flush=True)
                continue
            if sesion is None:
                if tipo != ABRIR:
                    continue
                partes = []
                fin_bloque_recibido = 0
                apertura = paquete["carga"]
                total_bytes, total_partes = struct.unpack("!II", apertura)
                sesion, origen_sesion = paquete["sesion"], origen
                plazo_espera = time.monotonic() + TIEMPO_SIN_AVANCE
                print(f"OPEN: sesión {sesion}, {total_partes} partes, {total_bytes} bytes.", flush=True)
            if paquete["sesion"] != sesion or origen != origen_sesion:
                continue

            if tipo == ABRIR and paquete["carga"] == apertura:
                respuesta = crear_paquete(APERTURA_CONFIRMADA, sesion)
                print("Respondo OPEN_ACK.", flush=True)
            elif tipo == DATOS:
                numero = paquete["secuencia"]
                bytes_esperados = min(BYTES_POR_PARTE, total_bytes - numero * BYTES_POR_PARTE)
                if numero >= total_partes or len(paquete["carga"]) != bytes_esperados:
                    continue
                siguiente_parte = len(partes)
                if numero == siguiente_parte:
                    if numero >= fin_bloque_recibido:
                        fin_bloque_recibido = min(numero + paquete["ventana"], total_partes)
                        print(f"Recibo bloque: partes {numero} a {fin_bloque_recibido - 1}. Ventana: {paquete['ventana']}.", flush=True)
                    partes.append(paquete["carga"])
                    print(f"Parte {numero} recibida: {len(paquete['carga'])} bytes. ACK {len(partes)}.", flush=True)
                    if len(partes) == fin_bloque_recibido:
                        print(f"Bloque recibido hasta la parte {fin_bloque_recibido - 1}.", flush=True)
                    plazo_espera = time.monotonic() + TIEMPO_SIN_AVANCE
                else:
                    print(f"Descarto DATA {numero}: espero {siguiente_parte}.", flush=True)
                respuesta = crear_paquete(CONFIRMAR, sesion, confirmado=len(partes))
            elif tipo == CERRAR:
                if len(partes) != total_partes or sum(map(len, partes)) != total_bytes:
                    print("Descarto CLOSE: todavía faltan partes.", flush=True)
                    continue
                try:
                    texto = reconstruir_mensaje(partes)
                    archivo = guardar_mensaje(sesion, partes)
                except (UnicodeError, OSError) as error:
                    print(f"No se pudo guardar el mensaje: {error}. Espero otro mensaje.", flush=True)
                    sesion = None
                    continue
                if len(cierres_recientes) >= 100:
                    cierres_recientes.pop(next(iter(cierres_recientes)))
                cierres_recientes[clave_sesion] = (total_partes, time.monotonic() + TIEMPO_CIERRE)
                conexion.sendto(crear_paquete(CIERRE_CONFIRMADO, sesion, confirmado=total_partes), origen)
                print(f"CLOSE válido. Respondo CLOSE_ACK.\nMensaje: {texto}\nGuardado: {archivo}\nEspero otro mensaje...", flush=True)
                sesion = None
                continue
            else:
                continue
            conexion.sendto(respuesta, origen)


def enviar(ip, puerto, texto):
    partes = dividir_mensaje(texto)
    print(f"Divido el mensaje en {len(partes)} partes de hasta 256 bytes; total {sum(map(len, partes))} bytes.", flush=True)
    sesion = secrets.randbelow(2**32 - 1) + 1
    destino = (socket.gethostbyname(ip), puerto)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
        carga = struct.pack("!II", sum(map(len, partes)), len(partes))
        enviar_control(conexion, destino, crear_paquete(ABRIR, sesion, carga=carga), sesion, APERTURA_CONFIRMADA)
        print(f"OPEN_ACK recibido. Sesión {sesion}, {len(partes)} partes.", flush=True)
        primera_sin_confirmar = 0
        ventana = 2
        esperas_sin_avance = 0
        while primera_sin_confirmar < len(partes):
            fin_bloque = min(primera_sin_confirmar + ventana, len(partes))
            bloque_recuperado = False
            ultimo_enviado = primera_sin_confirmar - 1
            print(f"Inicio bloque {primera_sin_confirmar} a {fin_bloque - 1}. Ventana: {ventana}.", flush=True)
            while primera_sin_confirmar < fin_bloque:
                fin_grupo_envio = min(primera_sin_confirmar + ventana, fin_bloque)
                for numero in range(primera_sin_confirmar, fin_grupo_envio):
                    conexion.sendto(crear_paquete(DATOS, sesion, secuencia=numero, ventana=ventana, carga=partes[numero]), destino)
                    print(f"Envío parte {numero}: {len(partes[numero])} bytes.", flush=True)
                    ultimo_enviado = max(ultimo_enviado, numero)
                while primera_sin_confirmar < fin_grupo_envio:
                    try:
                        primera_sin_confirmar = esperar_confirmacion(conexion, destino, sesion, CONFIRMAR, primera_sin_confirmar + 1, ultimo_enviado + 1)
                        esperas_sin_avance = 0
                    except TimeoutError:
                        esperas_sin_avance += 1
                        if esperas_sin_avance == INTENTOS_MAXIMOS:
                            raise TimeoutError("Cinco esperas vencidas sin avance. Envío cancelado.")
                        anterior = ventana
                        ventana = max(2, ventana - 2)
                        bloque_recuperado = True
                        print(f"Sin confirmación. Ventana: {anterior} a {ventana}. Reenvío desde la parte {primera_sin_confirmar}.", flush=True)
                        break
            print(f"Bloque confirmado hasta la parte {fin_bloque - 1}.", flush=True)
            if bloque_recuperado:
                print(f"Bloque recuperado. Mantengo ventana: {ventana}.", flush=True)
            else:
                anterior = ventana
                ventana = min(8, ventana + 2)
                print(f"Bloque limpio. Ventana: {anterior} a {ventana}.", flush=True)
        try:
            enviar_control(conexion, destino, crear_paquete(CERRAR, sesion, ventana=ventana), sesion, CIERRE_CONFIRMADO, len(partes))
        except OSError as error:
            raise OSError("Cierre no confirmado; revisa si el receptor guardó el mensaje.") from error
        print(f"CLOSE_ACK recibido. Envío completado. Ventana final: {ventana}.", flush=True)
        print(f"Mensaje enviado: {texto}", flush=True)


def main():
    print("PVA: mensajes por UDP\n1. Recibir\n2. Enviar\n3. Enviar ejemplo de veinte partes")
    try:
        opcion = input("Elige 1, 2 o 3: ").strip()
        if opcion not in ("1", "2", "3"):
            raise ValueError("Elige 1, 2 o 3.")
        puerto = int(input("Puerto [5050]: ").strip() or "5050")
        if not 1 <= puerto <= 65535:
            raise ValueError("El puerto debe estar entre 1 y 65535.")
        if opcion == "1":
            recibir(puerto)
        else:
            ip = input("IP receptora [127.0.0.1]: ").strip() or "127.0.0.1"
            texto = input("Mensaje: ") if opcion == "2" else "".join(
                f"Parte {numero:02d}: ".ljust(256, ".") for numero in range(20))
            enviar(ip, puerto, texto)
    except (OSError, ValueError) as error:
        print(f"No se pudo completar: {error}. Revisa la conexión.")
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nPrueba cancelada.")
        raise SystemExit(1)
