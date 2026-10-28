import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from protocolo import dividir_mensaje


class Ventana(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('PVA · Mensajes en red')
        self.geometry('780x700')
        self.minsize(620, 560)
        self.configure(background='#eef3f7')
        estilo = ttk.Style(self)
        estilo.theme_use('clam')
        estilo.configure('TFrame', background='#eef3f7')
        estilo.configure('TLabel', background='#eef3f7', foreground='#243d50', font=('Segoe UI', 10))
        estilo.configure('Titulo.TLabel', font=('Segoe UI', 22, 'bold'))
        estilo.configure('TButton', padding=10, font=('Segoe UI', 10))
        self.proceso = None
        self.eventos = queue.Queue()
        self.estado = tk.StringVar(value='Listo')
        self.puerto = tk.StringVar(value='5050')
        self.ip = tk.StringVar(value='127.0.0.1')
        try:
            imagen = tk.PhotoImage(master=self, file=str(Path(__file__).resolve().parent / 'imagenes' / 'logo.png'))
            self.logo = tk.PhotoImage(master=self)
            self.logo.tk.call(self.logo, 'copy', imagen, '-from', 0, 250, 1254, 1000, '-subsample', 4, 4)
        except tk.TclError:
            self.logo = None
        self.contenido = ttk.Frame(self, padding=24)
        self.contenido.pack(fill='both', expand=True)
        self.protocol('WM_DELETE_WINDOW', self.cerrar)
        self.inicio()
        self.after(80, self.actualizar)

    def limpiar(self):
        for elemento in self.contenido.winfo_children():
            elemento.destroy()

    def inicio(self):
        self.limpiar()
        if self.logo:
            ttk.Label(self.contenido, image=self.logo).pack(pady=(20, 8))
        else:
            ttk.Label(self.contenido, text='Ventana Adaptativa', style='Titulo.TLabel').pack(pady=(70, 8))
        ttk.Label(self.contenido, text='¿Qué hará este equipo?').pack(pady=(15, 16))
        ttk.Button(self.contenido, text='Enviar un mensaje', command=lambda: self.pagina('emisor')).pack(fill='x', padx=90, pady=8)
        ttk.Button(self.contenido, text='Recibir un mensaje', command=lambda: self.pagina('receptor')).pack(fill='x', padx=90, pady=8)
        ttk.Label(self.contenido, text='Usa la misma red y el mismo puerto en ambas PCs.').pack(pady=30)

    def pagina(self, rol):
        self.rol = rol
        self.limpiar()
        self.volver = ttk.Button(self.contenido, text='← Inicio', command=self.inicio)
        self.volver.pack(anchor='w')
        ttk.Label(self.contenido, text='Enviar mensaje' if rol == 'emisor' else 'Recibir mensaje', style='Titulo.TLabel').pack(anchor='w', pady=(15, 8))
        campos = ttk.Frame(self.contenido)
        campos.pack(fill='x')
        if rol == 'emisor':
            ttk.Label(campos, text='IP del receptor').pack(side='left')
            ttk.Entry(campos, textvariable=self.ip, width=22).pack(side='left', padx=(8, 20))
        ttk.Label(campos, text='Puerto UDP').pack(side='left')
        ttk.Entry(campos, textvariable=self.puerto, width=8).pack(side='left', padx=8)
        if rol == 'emisor':
            ttk.Label(self.contenido, text='Mensaje').pack(anchor='w', pady=(15, 5))
            self.mensaje = ScrolledText(self.contenido, height=5, font=('Segoe UI', 11), wrap='word', relief='solid', borderwidth=1)
            self.mensaje.pack(fill='x')
        acciones = ttk.Frame(self.contenido)
        acciones.pack(fill='x', pady=15)
        self.boton_iniciar = ttk.Button(acciones, text='Enviar' if rol == 'emisor' else 'Iniciar recepción', command=self.iniciar)
        self.boton_iniciar.pack(side='left')
        self.boton_detener = ttk.Button(acciones, text='Detener', command=self.detener, state='disabled')
        self.estado.set('Listo para enviar.' if rol == 'emisor' else 'Listo para recibir.')
        ttk.Label(self.contenido, textvariable=self.estado).pack(anchor='w')
        ttk.Label(self.contenido, text='Mensaje y bloques').pack(anchor='w', pady=(15, 5))
        self.actividad = ScrolledText(self.contenido, font=('Consolas', 10), wrap='word', state='disabled', height=12, relief='solid', borderwidth=1)
        self.actividad.pack(fill='both', expand=True)

    def iniciar(self):
        if self.proceso is not None:
            return
        try:
            puerto = int(self.puerto.get())
            if not 1 <= puerto <= 65535:
                raise ValueError('El puerto debe estar entre 1 y 65535.')
            datos = b''
            if self.rol == 'emisor':
                if not self.ip.get().strip():
                    raise ValueError('Escribe la IP del receptor.')
                texto = self.mensaje.get('1.0', 'end-1c')
                dividir_mensaje(texto)
                datos = texto.encode('utf-8')
                argumentos = [self.ip.get().strip(), str(puerto)]
                llamada = 'main.enviar(sys.argv[1], int(sys.argv[2]), sys.stdin.read())'
            else:
                argumentos = [str(puerto)]
                llamada = 'main.recibir(int(sys.argv[1]))'
            codigo = 'import main, sys\ntry:\n    ' + llamada + '\nexcept (OSError, ValueError) as error:\n    print("No se completó:", error, flush=True)\n    sys.exit(1)'
            self.proceso = subprocess.Popen([sys.executable, '-B', '-u', '-X', 'utf8', '-c', codigo, *argumentos], cwd=Path(__file__).resolve().parent, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except (ValueError, OSError) as error:
            messagebox.showerror('Revisa los datos', str(error), parent=self)
            return
        self.cancelado = False
        self.actividad.configure(state='normal')
        self.actividad.delete('1.0', 'end')
        self.actividad.configure(state='disabled')
        self.boton_iniciar.configure(state='disabled')
        self.volver.configure(state='disabled')
        self.boton_detener.pack(side='left', padx=8)
        self.boton_detener.configure(state='normal')
        self.estado.set('Enviando…' if self.rol == 'emisor' else 'Esperando mensajes…')
        threading.Thread(target=self.comunicar, args=(self.proceso, datos), daemon=True).start()

    def comunicar(self, proceso, datos):
        try:
            proceso.stdin.write(datos)
            proceso.stdin.close()
            for linea in iter(proceso.stdout.readline, b''):
                self.eventos.put(('texto', linea.decode('utf-8', errors='replace')))
        except OSError as error:
            self.eventos.put(('texto', f'Comunicación interrumpida: {error}\n'))
        finally:
            proceso.stdout.close()
            self.eventos.put(('fin', proceso.wait()))

    def actualizar(self):
        for _ in range(200):
            try:
                tipo, valor = self.eventos.get_nowait()
            except queue.Empty:
                break
            if tipo == 'texto':
                if self.rol == 'receptor' and 'Espero otro mensaje' in valor:
                    self.estado.set('Esperando el siguiente mensaje…')
                self.actividad.configure(state='normal')
                self.actividad.insert('end', valor)
                self.actividad.see('end')
                self.actividad.configure(state='disabled')
            else:
                self.proceso = None
                self.boton_iniciar.configure(state='normal')
                self.volver.configure(state='normal')
                self.boton_detener.pack_forget()
                self.estado.set('Operación detenida.' if self.cancelado else 'Mensaje completado.' if valor == 0 else 'No se completó. Revisa el recorrido y la conexión.')
        self.after(80, self.actualizar)

    def detener(self):
        if self.proceso is not None:
            self.cancelado = True
            self.proceso.kill()

    def cerrar(self):
        if self.proceso is not None:
            self.proceso.kill()
        self.destroy()


def main():
    Ventana().mainloop()


if __name__ == '__main__':
    main()
