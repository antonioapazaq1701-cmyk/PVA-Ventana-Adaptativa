import struct
import zlib

CABECERA = struct.Struct("!BBIIIBHI")  
BYTES_POR_PARTE = 256
VENTANAS_PERMITIDAS = (2, 4, 6, 8)
LIMITE_MENSAJE = 1024 * 1024
ABRIR, APERTURA_CONFIRMADA, DATOS, CONFIRMAR, CERRAR, CIERRE_CONFIRMADO, ERROR = range(1, 8)


def dividir_mensaje(texto):
    datos = texto.encode("utf-8")
    if not 1 <= len(datos) <= LIMITE_MENSAJE:
        raise ValueError("El mensaje debe ocupar entre 1 byte y 1 MiB.")
    return [datos[inicio:inicio + BYTES_POR_PARTE] for inicio in range(0, len(datos), BYTES_POR_PARTE)]


def reconstruir_mensaje(partes):
    return b"".join(partes).decode("utf-8")


def crear_paquete(tipo, sesion, secuencia=0, confirmado=0, ventana=2, carga=b""):
    try:
        cabecera = CABECERA.pack(1, tipo, sesion, secuencia, confirmado, ventana, len(carga), 0)
    except struct.error as error:
        raise ValueError("Los campos deben ser enteros dentro del rango de la cabecera.") from error
    crc_paquete = zlib.crc32(cabecera + carga)
    paquete = cabecera[:CABECERA.size - 4] + struct.pack("!I", crc_paquete) + carga
    leer_paquete(paquete) 
    return paquete


def leer_paquete(datos):
    if len(datos) < CABECERA.size:
        raise ValueError("Cabecera incompleta: se necesitan 21 bytes.")
    version, tipo, sesion, secuencia, confirmado, ventana, longitud, crc_paquete = CABECERA.unpack(datos[:CABECERA.size])
    carga = datos[CABECERA.size:]
    if version != 1 or tipo not in range(1, 8) or sesion == 0:
        raise ValueError("Versión, tipo o sesión inválidos.")
    if ventana not in VENTANAS_PERMITIDAS:
        raise ValueError("La ventana debe ser 2, 4, 6 u 8.")
    if longitud != len(carga) or longitud > BYTES_POR_PARTE:
        raise ValueError("Longitud de carga incorrecta.")
    cabecera_sin_crc = datos[:CABECERA.size - 4] + b"\0\0\0\0"
    if zlib.crc32(cabecera_sin_crc + carga) != crc_paquete:
        raise ValueError("CRC incorrecto: el paquete está alterado.")
    if tipo != DATOS and secuencia != 0:
        raise ValueError("Solo DATOS puede tener una secuencia distinta de cero.")
    if tipo not in (CONFIRMAR, CIERRE_CONFIRMADO) and confirmado != 0:
        raise ValueError("Solo las confirmaciones pueden usar el campo confirmado.")

    if tipo == DATOS:
        if not 1 <= longitud <= BYTES_POR_PARTE:
            raise ValueError("DATOS necesita entre 1 y 256 bytes.")
    else:
        bytes_esperados = {ABRIR: 8, ERROR: 2}.get(tipo, 0)
        if longitud != bytes_esperados:
            raise ValueError("La carga no corresponde al tipo de paquete.")
    if tipo == ABRIR:
        total_bytes, total_partes = struct.unpack("!II", carga)
        if not 1 <= total_bytes <= LIMITE_MENSAJE or total_partes != (total_bytes + BYTES_POR_PARTE - 1) // BYTES_POR_PARTE:
            raise ValueError("Los totales de la apertura son incorrectos.")

    return {
        "tipo": tipo, "sesion": sesion, "secuencia": secuencia,
        "confirmado": confirmado, "ventana": ventana, "carga": carga,
    }
