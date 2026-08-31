import tkinter as tk
from tkinter import ttk
import math
import random
import time


# ==============================================================
#       SIMULADOR DINÁMICO DE ELECTROSCOPIO DE HOJAS
# ==============================================================
#
# CONTROLES:
#
# 1. Seleccionar carga de referencia.
# 2. Presionar "CARGAR POR CONTACTO".
# 3. Seleccionar la carga del objeto desconocido.
# 4. Arrastrar el objeto con el mouse.
# 5. Observar cómo cambian dinámicamente las hojas.
#
#
# MODELO MECÁNICO SIMPLIFICADO:
#
#       I θ'' + b θ' + k(θ - θeq) = 0
#
# donde:
#
#       θ      = ángulo de apertura
#       I      = inercia efectiva
#       b      = amortiguamiento
#       k      = constante restauradora
#       θeq    = ángulo de equilibrio electrostático
#
#
# MODELO DE INDUCCIÓN SIMPLIFICADO:
#
#       E_inducción ∝ Qx / d²
#
#
# La posición del objeto modifica continuamente θeq.
#
# ==============================================================


# ==============================================================
# CONFIGURACIÓN GENERAL
# ==============================================================

ANCHO = 1400
ALTO = 850

BG = "#0B1117"
PANEL = "#15232D"
PANEL2 = "#1D303D"

TEXTO = "#F2F5F7"
SECUNDARIO = "#AAB8C2"

POSITIVO = "#FF5252"
NEGATIVO = "#42A5F5"
NEUTRO = "#B0BEC5"

METAL = "#C2CDD2"
METAL_OSCURO = "#64747D"

VERDE = "#66BB6A"
AMARILLO = "#FFD54F"

LINEA_GRAFICO = "#FFFFFF"


# ==============================================================
# FUNCIONES AUXILIARES
# ==============================================================

def signo(x):

    if x > 0:
        return 1

    if x < 0:
        return -1

    return 0


def limitar(x, minimo, maximo):

    return max(minimo, min(maximo, x))


def color_carga(q):

    if q > 0:
        return POSITIVO

    elif q < 0:
        return NEGATIVO

    return NEUTRO


# ==============================================================
# CLASE DE PARTÍCULAS DE CARGA
# ==============================================================

class ParticulaCarga:

    def __init__(self, x, y, signo_particula):

        self.x = x
        self.y = y

        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.3, 0.3)

        self.signo = signo_particula

        self.fase = random.uniform(0, math.pi * 2)

    def actualizar(self, dt, objetivo_x, objetivo_y):

        # Movimiento oscilatorio suave.

        self.fase += dt * random.uniform(1.0, 2.0)

        dx = objetivo_x - self.x
        dy = objetivo_y - self.y

        # Atracción hacia la región objetivo.

        self.vx += dx * 0.001
        self.vy += dy * 0.001

        # Pequeña oscilación.

        self.vx += math.sin(self.fase) * 0.02
        self.vy += math.cos(self.fase) * 0.02

        # Amortiguamiento.

        self.vx *= 0.94
        self.vy *= 0.94

        self.x += self.vx
        self.y += self.vy


# ==============================================================
# CLASE PRINCIPAL
# ==============================================================

class SimuladorElectroscopio:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Electroscopio Dinámico - Simulador Interactivo"
        )

        self.root.geometry(
            f"{ANCHO}x{ALTO}"
        )

        self.root.configure(
            bg=BG
        )

        # ------------------------------------------------------
        # VARIABLES FÍSICAS
        # ------------------------------------------------------

        self.q_referencia = 10.0
        self.q_objeto = -10.0

        self.q_electroscopio = 0.0

        # Posición del objeto.

        self.objeto_x = 250
        self.objeto_y = 280

        self.arrastrando = False

        # ------------------------------------------------------
        # SISTEMA MECÁNICO
        # ------------------------------------------------------

        self.theta = 0.0
        self.omega = 0.0

        self.theta_equilibrio = 0.0

        # Parámetros.

        self.k = 12.0
        self.b = 3.5
        self.I = 1.0

        # ------------------------------------------------------
        # HISTORIAL PARA GRÁFICO
        # ------------------------------------------------------

        self.historial_theta = []

        self.max_historial = 180

        # ------------------------------------------------------
        # TIEMPO
        # ------------------------------------------------------

        self.t_anterior = time.time()

        # ------------------------------------------------------
        # PARTÍCULAS
        # ------------------------------------------------------

        self.particulas = []

        # ------------------------------------------------------
        # ESTADO
        # ------------------------------------------------------

        self.cargado = False

        self.mostrar_campo = True
        self.mostrar_cargas = True

        # ------------------------------------------------------
        # INTERFAZ
        # ------------------------------------------------------

        self.crear_interfaz()

        self.crear_particulas()

        # ------------------------------------------------------
        # EVENTOS
        # ------------------------------------------------------

        self.canvas.bind(
            "<ButtonPress-1>",
            self.mouse_presionado
        )

        self.canvas.bind(
            "<B1-Motion>",
            self.mouse_movido
        )

        self.canvas.bind(
            "<ButtonRelease-1>",
            self.mouse_liberado
        )

        # ------------------------------------------------------
        # INICIAR
        # ------------------------------------------------------

        self.animar()


    # ==========================================================
    # INTERFAZ
    # ==========================================================

    def crear_interfaz(self):

        titulo = tk.Label(
            self.root,
            text="ELECTROSCOPIO DINÁMICO E INTERACTIVO",
            font=("Segoe UI", 22, "bold"),
            bg=BG,
            fg=TEXTO
        )

        titulo.pack(
            pady=(10, 0)
        )

        subtitulo = tk.Label(
            self.root,
            text=(
                "Arrastra el objeto cargado y observa "
                "la respuesta del electroscopio en tiempo real"
            ),
            font=("Segoe UI", 11),
            bg=BG,
            fg=SECUNDARIO
        )

        subtitulo.pack(
            pady=(0, 10)
        )

        principal = tk.Frame(
            self.root,
            bg=BG
        )

        principal.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=8
        )

        # ------------------------------------------------------
        # PANEL DE CONTROLES
        # ------------------------------------------------------

        controles = tk.Frame(
            principal,
            bg=PANEL,
            width=300
        )

        controles.pack(
            side="left",
            fill="y",
            padx=(0, 8)
        )

        controles.pack_propagate(False)

        # ------------------------------------------------------
        # PANEL DE SIMULACIÓN
        # ------------------------------------------------------

        simulacion = tk.Frame(
            principal,
            bg=PANEL
        )

        simulacion.pack(
            side="left",
            fill="both",
            expand=True
        )

        # ======================================================
        # CONTROLES
        # ======================================================

        tk.Label(
            controles,
            text="CONTROLES",
            font=("Segoe UI", 15, "bold"),
            bg=PANEL,
            fg=TEXTO
        ).pack(
            pady=(15, 15)
        )

        # ------------------------------------------------------
        # REFERENCIA
        # ------------------------------------------------------

        tk.Label(
            controles,
            text="Carga de referencia",
            font=("Segoe UI", 10, "bold"),
            bg=PANEL,
            fg=TEXTO
        ).pack()

        self.var_ref = tk.DoubleVar(
            value=10
        )

        tk.Scale(
            controles,
            from_=-20,
            to=20,
            resolution=1,
            orient="horizontal",
            variable=self.var_ref,
            command=self.actualizar_valores,
            length=250,
            bg=PANEL,
            fg=TEXTO,
            troughcolor=PANEL2,
            highlightthickness=0
        ).pack()

        self.label_ref = tk.Label(
            controles,
            text="",
            bg=PANEL,
            fg=POSITIVO,
            font=("Consolas", 11, "bold")
        )

        self.label_ref.pack(
            pady=(0, 15)
        )

        # ------------------------------------------------------
        # OBJETO
        # ------------------------------------------------------

        tk.Label(
            controles,
            text="Carga del objeto desconocido",
            font=("Segoe UI", 10, "bold"),
            bg=PANEL,
            fg=TEXTO
        ).pack()

        self.var_objeto = tk.DoubleVar(
            value=-10
        )

        tk.Scale(
            controles,
            from_=-20,
            to=20,
            resolution=1,
            orient="horizontal",
            variable=self.var_objeto,
            command=self.actualizar_valores,
            length=250,
            bg=PANEL,
            fg=TEXTO,
            troughcolor=PANEL2,
            highlightthickness=0
        ).pack()

        self.label_objeto = tk.Label(
            controles,
            text="",
            bg=PANEL,
            fg=NEGATIVO,
            font=("Consolas", 11, "bold")
        )

        self.label_objeto.pack(
            pady=(0, 15)
        )

        # ------------------------------------------------------
        # BOTÓN CARGAR
        # ------------------------------------------------------

        tk.Button(
            controles,
            text="⚡ CARGAR POR CONTACTO",
            command=self.cargar_contacto,
            font=("Segoe UI", 10, "bold"),
            bg=PANEL2,
            fg=TEXTO,
            relief="flat",
            pady=10
        ).pack(
            fill="x",
            padx=20,
            pady=5
        )

        # ------------------------------------------------------
        # DESCARGAR
        # ------------------------------------------------------

        tk.Button(
            controles,
            text="DESCARGAR ELECTROSCOPIO",
            command=self.descargar,
            font=("Segoe UI", 10, "bold"),
            bg="#343434",
            fg=TEXTO,
            relief="flat",
            pady=8
        ).pack(
            fill="x",
            padx=20,
            pady=5
        )

        # ------------------------------------------------------
        # REINICIAR
        # ------------------------------------------------------

        tk.Button(
            controles,
            text="REINICIAR POSICIÓN",
            command=self.reiniciar,
            font=("Segoe UI", 10, "bold"),
            bg="#343434",
            fg=TEXTO,
            relief="flat",
            pady=8
        ).pack(
            fill="x",
            padx=20,
            pady=5
        )

        # ------------------------------------------------------
        # OPCIONES
        # ------------------------------------------------------

        tk.Label(
            controles,
            text="VISUALIZACIÓN",
            font=("Segoe UI", 11, "bold"),
            bg=PANEL,
            fg=TEXTO
        ).pack(
            pady=(20, 5)
        )

        self.var_campo = tk.BooleanVar(
            value=True
        )

        tk.Checkbutton(
            controles,
            text="Mostrar líneas de campo",
            variable=self.var_campo,
            bg=PANEL,
            fg=TEXTO,
            selectcolor=PANEL2,
            activebackground=PANEL
        ).pack(
            anchor="w",
            padx=25
        )

        self.var_cargas = tk.BooleanVar(
            value=True
        )

        tk.Checkbutton(
            controles,
            text="Mostrar cargas móviles",
            variable=self.var_cargas,
            bg=PANEL,
            fg=TEXTO,
            selectcolor=PANEL2,
            activebackground=PANEL
        ).pack(
            anchor="w",
            padx=25
        )

        # ------------------------------------------------------
        # ESTADO
        # ------------------------------------------------------

        self.estado = tk.Label(
            controles,
            text="Electroscopio neutro",
            font=("Segoe UI", 10, "bold"),
            bg=PANEL,
            fg=AMARILLO,
            wraplength=260,
            justify="center"
        )

        self.estado.pack(
            pady=(25, 5)
        )

        # ======================================================
        # CANVAS
        # ======================================================

        self.canvas = tk.Canvas(
            simulacion,
            bg="#080D11",
            highlightthickness=0
        )

        self.canvas.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        # ------------------------------------------------------
        # INFORMACIÓN
        # ------------------------------------------------------

        self.info = tk.Label(
            simulacion,
            text="",
            bg=PANEL,
            fg=SECUNDARIO,
            font=("Consolas", 10),
            justify="left",
            anchor="w"
        )

        self.info.pack(
            fill="x",
            padx=8,
            pady=(0, 8)
        )


    # ==========================================================
    # CREAR PARTÍCULAS
    # ==========================================================

    def crear_particulas(self):

        self.particulas = []

        for _ in range(22):

            x = random.uniform(
                650,
                760
            )

            y = random.uniform(
                250,
                520
            )

            p = ParticulaCarga(
                x,
                y,
                1
            )

            self.particulas.append(
                p
            )


    # ==========================================================
    # ACTUALIZAR VALORES
    # ==========================================================

    def actualizar_valores(self, event=None):

        self.q_referencia = (
            self.var_ref.get()
        )

        self.q_objeto = (
            self.var_objeto.get()
        )

        self.label_ref.config(
            text=f"Qref = {self.q_referencia:+.0f} uC",
            fg=color_carga(self.q_referencia)
        )

        self.label_objeto.config(
            text=f"Qx = {self.q_objeto:+.0f} uC",
            fg=color_carga(self.q_objeto)
        )


    # ==========================================================
    # CARGAR POR CONTACTO
    # ==========================================================

    def cargar_contacto(self):

        if self.q_referencia == 0:

            self.estado.config(
                text="La carga de referencia es cero.",
                fg=AMARILLO
            )

            return

        self.q_electroscopio = (
            self.q_referencia
        )

        self.cargado = True

        self.estado.config(
            text=(
                "Electroscopio cargado por contacto.\n"
                "Ahora tiene el mismo signo que "
                "la carga de referencia."
            ),
            fg=VERDE
        )

        self.crear_particulas()


    # ==========================================================
    # DESCARGAR
    # ==========================================================

    def descargar(self):

        self.q_electroscopio = 0.0

        self.cargado = False

        self.theta_equilibrio = 0

        self.estado.config(
            text="Electroscopio descargado.",
            fg=AMARILLO
        )


    # ==========================================================
    # REINICIAR
    # ==========================================================

    def reiniciar(self):

        self.objeto_x = 200
        self.objeto_y = 280

        self.theta = 0
        self.omega = 0

        self.historial_theta.clear()


    # ==========================================================
    # POSICIÓN DEL ELECTROSCOPIO
    # ==========================================================

    def centro_electroscopio(self):

        ancho = self.canvas.winfo_width()
        alto = self.canvas.winfo_height()

        if ancho < 100:
            ancho = 1000

        if alto < 100:
            alto = 600

        return ancho * 0.65, alto * 0.33


    # ==========================================================
    # CALCULAR DISTANCIA
    # ==========================================================

    def calcular_distancia(self):

        cx, cy = self.centro_electroscopio()

        dx = self.objeto_x - cx
        dy = self.objeto_y - cy

        d = math.sqrt(
            dx * dx +
            dy * dy
        )

        return max(d, 40)


    # ==========================================================
    # CALCULAR ÁNGULO DE EQUILIBRIO
    # ==========================================================

    def calcular_equilibrio(self):

        # Si el electroscopio está descargado.

        if abs(self.q_electroscopio) < 0.01:

            return 0.0

        # Apertura inicial.

        q_e = abs(
            self.q_electroscopio
        )

        theta_base = (
            8 +
            32 *
            (
                1 -
                math.exp(-q_e / 8)
            )
        )

        # Distancia.

        d = self.calcular_distancia()

        # Efecto relativo.

        efecto = (
            abs(self.q_objeto) /
            max(d / 100, 1) ** 2
        )

        # Comparación de signos.

        producto = (
            self.q_electroscopio *
            self.q_objeto
        )

        # ------------------------------------------------------
        # MISMO SIGNO
        # ------------------------------------------------------

        if producto > 0:

            cambio = (
                25 *
                (
                    1 -
                    math.exp(-efecto)
                )
            )

            theta = theta_base + cambio

        # ------------------------------------------------------
        # SIGNO OPUESTO
        # ------------------------------------------------------

        elif producto < 0:

            cambio = (
                40 *
                (
                    1 -
                    math.exp(-efecto)
                )
            )

            theta = theta_base - cambio

        else:

            theta = theta_base

        return limitar(
            theta,
            0,
            65
        )


    # ==========================================================
    # ACTUALIZAR DINÁMICA MECÁNICA
    # ==========================================================

    def actualizar_dinamica(self, dt):

        self.theta_equilibrio = (
            self.calcular_equilibrio()
        )

        # Convertimos a radianes internamente.

        theta_rad = math.radians(
            self.theta
        )

        theta_eq_rad = math.radians(
            self.theta_equilibrio
        )

        # ------------------------------------------------------
        # ECUACIÓN:
        #
        # I θ'' + b θ' + k(θ - θeq) = 0
        #
        # θ'' =
        #
        # -b/I θ'
        #
        # -k/I (θ - θeq)
        #
        # ------------------------------------------------------

        aceleracion = (
            -self.b / self.I *
            self.omega
            -
            self.k / self.I *
            (
                theta_rad -
                theta_eq_rad
            )
        )

        self.omega += (
            aceleracion * dt
        )

        theta_rad += (
            self.omega * dt
        )

        self.theta = math.degrees(
            theta_rad
        )

        self.theta = limitar(
            self.theta,
            0,
            70
        )


    # ==========================================================
    # ACTUALIZAR PARTÍCULAS
    # ==========================================================

    def actualizar_particulas(self, dt):

        if not self.cargado:

            return

        cx, cy = self.centro_electroscopio()

        d = self.calcular_distancia()

        # Dirección del objeto respecto al electroscopio.

        dx = self.objeto_x - cx
        dy = self.objeto_y - cy

        norma = math.sqrt(
            dx * dx +
            dy * dy
        )

        if norma < 1:
            norma = 1

        ux = dx / norma
        uy = dy / norma

        # Intensidad de inducción.

        intensidad = (
            abs(self.q_objeto) /
            max(d / 100, 1) ** 2
        )

        # Redistribución visual.

        desplazamiento = limitar(
            intensidad * 35,
            0,
            55
        )

        # Signos iguales y opuestos generan
        # una redistribución visual diferente.

        mismo_signo = (
            signo(self.q_electroscopio) ==
            signo(self.q_objeto)
        )

        for i, p in enumerate(
            self.particulas
        ):

            # Algunas cargas hacia la esfera.

            if i < 8:

                factor = -1 if mismo_signo else 1

                objetivo_x = (
                    cx +
                    ux *
                    desplazamiento *
                    factor
                )

                objetivo_y = (
                    cy +
                    uy *
                    desplazamiento *
                    factor
                )

            # Otras hacia las hojas.

            else:

                lado = (
                    -1
                    if i % 2 == 0
                    else 1
                )

                angulo = math.radians(
                    self.theta
                )

                objetivo_x = (
                    cx +
                    lado *
                    70 *
                    math.sin(angulo)
                )

                objetivo_y = (
                    cy +
                    230
                )

            p.actualizar(
                dt,
                objetivo_x,
                objetivo_y
            )


    # ==========================================================
    # MOUSE
    # ==========================================================

    def mouse_presionado(self, event):

        dx = (
            event.x -
            self.objeto_x
        )

        dy = (
            event.y -
            self.objeto_y
        )

        distancia = math.sqrt(
            dx * dx +
            dy * dy
        )

        if distancia < 60:

            self.arrastrando = True


    def mouse_movido(self, event):

        if self.arrastrando:

            self.objeto_x = event.x
            self.objeto_y = event.y


    def mouse_liberado(self, event):

        self.arrastrando = False


    # ==========================================================
    # DIBUJAR CAMPO
    # ==========================================================

    def dibujar_campo(self):

        if not self.var_campo.get():

            return

        if not self.cargado:

            return

        cx, cy = self.centro_electroscopio()

        dx = cx - self.objeto_x
        dy = cy - self.objeto_y

        distancia = math.sqrt(
            dx * dx +
            dy * dy
        )

        if distancia > 500:

            return

        for offset in range(-100, 101, 25):

            x1 = self.objeto_x
            y1 = self.objeto_y + offset

            x2 = cx
            y2 = cy + offset * 0.35

            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="#3A5566",
                dash=(5, 5),
                width=1
            )


    # ==========================================================
    # DIBUJAR ELECTROSCOPIO
    # ==========================================================

    def dibujar_electroscopio(self):

        cx, cy = self.centro_electroscopio()

        # ------------------------------------------------------
        # ESFERA
        # ------------------------------------------------------

        r = 38

        self.canvas.create_oval(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            fill=METAL,
            outline="#FFFFFF",
            width=2
        )

        # ------------------------------------------------------
        # BARRA
        # ------------------------------------------------------

        self.canvas.create_line(
            cx,
            cy + r,
            cx,
            cy + 240,
            fill=METAL,
            width=8
        )

        # ------------------------------------------------------
        # HOJAS
        # ------------------------------------------------------

        origen_y = cy + 240

        longitud = 145

        angulo = math.radians(
            self.theta
        )

        # Izquierda.

        x_izq = (
            cx -
            longitud *
            math.sin(angulo)
        )

        y_izq = (
            origen_y +
            longitud *
            math.cos(angulo)
        )

        # Derecha.

        x_der = (
            cx +
            longitud *
            math.sin(angulo)
        )

        y_der = (
            origen_y +
            longitud *
            math.cos(angulo)
        )

        self.canvas.create_line(
            cx,
            origen_y,
            x_izq,
            y_izq,
            fill=METAL,
            width=9
        )

        self.canvas.create_line(
            cx,
            origen_y,
            x_der,
            y_der,
            fill=METAL,
            width=9
        )

        # ------------------------------------------------------
        # BASE
        # ------------------------------------------------------

        base_y = cy + 420

        self.canvas.create_rectangle(
            cx - 100,
            base_y,
            cx + 100,
            base_y + 22,
            fill=METAL_OSCURO,
            outline=""
        )

        # ------------------------------------------------------
        # TEXTO
        # ------------------------------------------------------

        self.canvas.create_text(
            cx,
            base_y + 55,
            text="ELECTROSCOPIO",
            fill=TEXTO,
            font=("Segoe UI", 11, "bold")
        )

        self.canvas.create_text(
            cx,
            base_y + 75,
            text=(
                f"Q = "
                f"{self.q_electroscopio:+.1f} uC"
            ),
            fill=color_carga(
                self.q_electroscopio
            ),
            font=("Consolas", 10, "bold")
        )


    # ==========================================================
    # DIBUJAR OBJETO
    # ==========================================================

    def dibujar_objeto(self):

        r = 45

        color = color_carga(
            self.q_objeto
        )

        self.canvas.create_oval(
            self.objeto_x - r,
            self.objeto_y - r,
            self.objeto_x + r,
            self.objeto_y + r,
            fill=color,
            outline="#FFFFFF",
            width=2
        )

        # Símbolos de carga.

        if self.q_objeto > 0:

            simbolo = "+"

        elif self.q_objeto < 0:

            simbolo = "-"

        else:

            simbolo = "0"

        for angulo in range(
            0,
            360,
            45
        ):

            rad = math.radians(
                angulo
            )

            x = (
                self.objeto_x +
                24 *
                math.cos(rad)
            )

            y = (
                self.objeto_y +
                24 *
                math.sin(rad)
            )

            self.canvas.create_text(
                x,
                y,
                text=simbolo,
                fill="white",
                font=("Arial", 12, "bold")
            )

        self.canvas.create_text(
            self.objeto_x,
            self.objeto_y + 70,
            text="ARRÁSTRAME",
            fill=TEXTO,
            font=("Segoe UI", 10, "bold")
        )

        self.canvas.create_text(
            self.objeto_x,
            self.objeto_y + 90,
            text=(
                f"Qx = "
                f"{self.q_objeto:+.0f} uC"
            ),
            fill=color,
            font=("Consolas", 10, "bold")
        )


    # ==========================================================
    # DIBUJAR PARTÍCULAS
    # ==========================================================

    def dibujar_particulas(self):

        if not self.var_cargas.get():

            return

        if not self.cargado:

            return

        simbolo = (
            "+"
            if self.q_electroscopio > 0
            else "-"
        )

        color = color_carga(
            self.q_electroscopio
        )

        for p in self.particulas:

            self.canvas.create_text(
                p.x,
                p.y,
                text=simbolo,
                fill=color,
                font=("Arial", 12, "bold")
            )


    # ==========================================================
    # GRÁFICO DEL ÁNGULO
    # ==========================================================

    def dibujar_grafico(self):

        ancho = self.canvas.winfo_width()

        x0 = 20
        y0 = 20

        w = 280
        h = 150

        # Fondo.

        self.canvas.create_rectangle(
            x0,
            y0,
            x0 + w,
            y0 + h,
            outline="#40505A",
            width=1
        )

        self.canvas.create_text(
            x0 + w / 2,
            y0 + 15,
            text="ÁNGULO DE APERTURA θ(t)",
            fill=TEXTO,
            font=("Segoe UI", 9, "bold")
        )

        # Ejes.

        self.canvas.create_line(
            x0 + 25,
            y0 + h - 20,
            x0 + w - 10,
            y0 + h - 20,
            fill="#55636C"
        )

        self.canvas.create_line(
            x0 + 25,
            y0 + 30,
            x0 + 25,
            y0 + h - 20,
            fill="#55636C"
        )

        if len(self.historial_theta) < 2:

            return

        max_theta = 70

        puntos = []

        for i, theta in enumerate(
            self.historial_theta
        ):

            x = (
                x0 + 25 +
                i *
                (
                    w - 40
                ) /
                max(
                    len(self.historial_theta) - 1,
                    1
                )
            )

            y = (
                y0 +
                h -
                20 -
                theta /
                max_theta *
                (
                    h - 50
                )
            )

            puntos.append(
                (x, y)
            )

        for i in range(
            len(puntos) - 1
        ):

            self.canvas.create_line(
                puntos[i][0],
                puntos[i][1],
                puntos[i + 1][0],
                puntos[i + 1][1],
                fill=LINEA_GRAFICO,
                width=2
            )

        self.canvas.create_text(
            x0 + 40,
            y0 + 38,
            text="70°",
            fill=SECUNDARIO,
            font=("Consolas", 8)
        )

        self.canvas.create_text(
            x0 + 40,
            y0 + h - 28,
            text="0°",
            fill=SECUNDARIO,
            font=("Consolas", 8)
        )


    # ==========================================================
    # DIBUJAR INTERFAZ COMPLETA
    # ==========================================================

    def dibujar(self):

        self.canvas.delete("all")

        self.dibujar_campo()

        self.dibujar_electroscopio()

        self.dibujar_objeto()

        self.dibujar_particulas()

        self.dibujar_grafico()

        self.actualizar_informacion()


    # ==========================================================
    # INFORMACIÓN
    # ==========================================================

    def actualizar_informacion(self):

        d = self.calcular_distancia()

        producto = (
            self.q_electroscopio *
            self.q_objeto
        )

        if not self.cargado:

            conclusion = (
                "Primero carga el electroscopio "
                "por contacto."
            )

        elif self.q_objeto == 0:

            conclusion = (
                "Objeto neutro."
            )

        elif producto > 0:

            conclusion = (
                "Qe · Qx > 0  → MISMO SIGNO "
                "→ θ aumenta"
            )

        else:

            conclusion = (
                "Qe · Qx < 0  → SIGNO OPUESTO "
                "→ θ disminuye"
            )

        texto = (
            f"Distancia objeto-electroscopio: "
            f"{d:.1f} px\n"
            f"Ángulo actual: θ = "
            f"{self.theta:.2f} grados\n"
            f"Ángulo de equilibrio: θeq = "
            f"{self.theta_equilibrio:.2f} grados\n"
            f"{conclusion}"
        )

        self.info.config(
            text=texto
        )


    # ==========================================================
    # BUCLE PRINCIPAL DE ANIMACIÓN
    # ==========================================================

    def animar(self):

        ahora = time.time()

        dt = (
            ahora -
            self.t_anterior
        )

        self.t_anterior = ahora

        # Evitar saltos grandes.

        dt = limitar(
            dt,
            0.001,
            0.05
        )

        # ------------------------------------------------------
        # ACTUALIZAR FÍSICA
        # ------------------------------------------------------

        self.actualizar_dinamica(
            dt
        )

        self.actualizar_particulas(
            dt
        )

        # ------------------------------------------------------
        # GUARDAR HISTORIAL
        # ------------------------------------------------------

        self.historial_theta.append(
            self.theta
        )

        if len(
            self.historial_theta
        ) > self.max_historial:

            self.historial_theta.pop(0)

        # ------------------------------------------------------
        # DIBUJAR
        # ------------------------------------------------------

        self.dibujar()

        # ------------------------------------------------------
        # SIGUIENTE FRAME
        # ------------------------------------------------------

        self.root.after(
            16,
            self.animar
        )


# ==============================================================
# PROGRAMA PRINCIPAL
# ==============================================================

def main():

    root = tk.Tk()

    app = SimuladorElectroscopio(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    main()