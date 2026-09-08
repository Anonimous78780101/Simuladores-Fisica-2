# -*- coding: utf-8 -*-
"""
LABORATORIO VIRTUAL DE CAPACITORES
==================================

Simulador educativo profesional de un capacitor de placas paralelas.

Características
---------------
* Capacitor de placas paralelas dibujado con Tkinter.
* Batería conectable/desconectable.
* Dieléctrico arrastrable horizontalmente.
* Fracción de inserción calculada a partir de la posición real del dieléctrico.
* Materiales dieléctricos predefinidos y material personalizado.
* Cambio de:
    - tensión de la batería
    - área de las placas
    - separación entre placas
    - constante dieléctrica relativa
    - espesor del dieléctrico
    - ancho/tamaño lateral del dieléctrico
    - fracción de área insertada
    - carga conservada cuando la batería está desconectada
* El espesor del dieléctrico puede ser exactamente igual a d o menor que d.
  En este último caso se representan explícitamente los espacios de aire.
* Multímetro virtual con modos:
    - tensión
    - capacitancia
    - carga
    - energía
    - campo eléctrico
* Detector de campo eléctrico con sonda desplazable.
* Visualización de cargas en las placas.
* Visualización de líneas de campo.
* Medición de campo dentro/fuera del dieléctrico.
* Cálculo energético y eléctrico consistente con el estado conectado/
  desconectado de la batería.
* Panel de ecuaciones y magnitudes físicas.
* Registro de eventos.
* Reinicio completo.
* Cada parámetro puede modificarse tanto con el deslizador como
  escribiendo directamente un valor numérico exacto y pulsando
  "Aplicar" o Enter.

Modelo físico
-------------

Para una región sin dieléctrico:

    C_aire = eps0 A / d

Si el dieléctrico de espesor t ocupa una fracción f del área activa
lateralmente, el área se divide en dos regiones eléctricamente en
paralelo:

    C = C_aire(1-f) + C_region f

Aquí f es el solapamiento real del bloque con el área de las placas.
El ancho del bloque puede ser menor, igual o mayor que el ancho de
las placas.

La región que contiene un dieléctrico de espesor t < d tiene una
geometría de capas en serie:

    C_region = eps0 A / (d - t + t/eps_r)

Por tanto:

    C = eps0 A/d * (1-f)
        + eps0 A/(d - t + t/eps_r) * f

Para t = d:

    C = eps0 A/d * [1 + f(eps_r - 1)]

Cuando la batería está conectada:

    V = V_bateria
    Q = C V
    U = 1/2 C V^2

Cuando la batería está desconectada:

    Q = constante
    V = Q/C
    U = Q^2/(2C)

Campo medio del capacitor:

    E_aire = V/d

En una región parcialmente ocupada por un dieléctrico de espesor t:

    E_dielectrico = V / (d - t + t/eps_r)

    E_aire_en_serie = E_dielectrico/eps_r

El modelo supone placas ideales, campo aproximadamente uniforme,
efectos de borde despreciables y dieléctrico lineal, homogéneo e
isótropo. No representa descarga, ruptura dieléctrica, pérdidas ni
efectos fringing de forma exacta.
"""

import math
import time
import tkinter as tk
from tkinter import ttk, messagebox


# ============================================================================
# CONSTANTES FÍSICAS
# ============================================================================

EPS0 = 8.8541878128e-12       # F/m
K_E = 8.9875517923e9          # N m²/C²
E_CHARGE = 1.602176634e-19    # C
C_LIGHT = 299792458.0         # m/s


# ============================================================================
# UTILIDADES NUMÉRICAS Y FORMATO
# ============================================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def fmt_si(value, unit="", digits=4):
    """Formato científico con prefijos SI básicos."""
    if not math.isfinite(value):
        return "—"

    av = abs(value)

    prefixes = [
        (1e12, "T"),
        (1e9, "G"),
        (1e6, "M"),
        (1e3, "k"),
        (1.0, ""),
        (1e-3, "m"),
        (1e-6, "µ"),
        (1e-9, "n"),
        (1e-12, "p"),
        (1e-15, "f"),
    ]

    for scale, prefix in prefixes:
        if av >= scale:
            return f"{value / scale:.{digits}g} {prefix}{unit}"

    return f"{value / 1e-15:.{digits}g} f{unit}"


def fmt_number(value, digits=5):
    if not math.isfinite(value):
        return "—"
    return f"{value:.{digits}g}"


def safe_float(text, default):
    try:
        return float(str(text).replace(",", "."))
    except (TypeError, ValueError):
        return default


# ============================================================================
# MODELO FÍSICO
# ============================================================================

class CapacitorPhysics:
    """
    Modelo de capacitor de placas paralelas con inserción lateral
    de un dieléctrico.

    Todas las magnitudes internas se almacenan en unidades SI.
    """

    MATERIALS = {
        "Vacío": 1.0000,
        "Aire": 1.0006,
        "Papel": 3.5,
        "Vidrio": 5.0,
        "Mica": 5.4,
        "Cerámica": 7.0,
        "Teflón": 2.1,
        "Polietileno": 2.25,
        "Agua": 80.0,
    }

    def __init__(self):
        self.reset()

    def reset(self):
        self.V_battery = 1.5
        self.area = 100e-4       # 100 cm² = 0.01 m²
        self.distance = 10e-3    # 10 mm
        self.eps_r = 5.0
        self.dielectric_thickness = self.distance
        # Fracción máxima de ancho del dieléctrico respecto del ancho de
        # las placas. 100 % significa que el bloque tiene el mismo ancho
        # que la región activa; >100 % significa un bloque más grande.
        self.dielectric_width_ratio = 1.00
        # Fracción efectiva del área de la placa ocupada por el dieléctrico
        # en la dirección lateral. Se obtiene de la geometría/arrastre.
        self.insertion = 0.0

        self.battery_connected = True
        self.fixed_charge = None

        self.update()

    def set_parameters(self, V=None, area=None, distance=None,
                       eps_r=None, thickness=None, insertion=None,
                       dielectric_width_ratio=None):
        old_C = getattr(self, "C", None)
        old_Q = getattr(self, "Q", 0.0)

        if V is not None:
            self.V_battery = max(0.0, float(V))
        if area is not None:
            self.area = max(1e-8, float(area))
        if distance is not None:
            self.distance = max(1e-6, float(distance))
        if eps_r is not None:
            self.eps_r = max(1.0, float(eps_r))
        if thickness is not None:
            self.dielectric_thickness = clamp(
                float(thickness), 0.0, self.distance
            )
        if insertion is not None:
            self.insertion = clamp(float(insertion), 0.0, 1.0)
        if dielectric_width_ratio is not None:
            self.dielectric_width_ratio = clamp(
                float(dielectric_width_ratio), 0.10, 2.50
            )

        # Si la separación cambia, el espesor no puede excederla.
        self.dielectric_thickness = clamp(
            self.dielectric_thickness, 0.0, self.distance
        )

        # Si se estaba operando como capacitor aislado, se conserva Q.
        if not self.battery_connected and self.fixed_charge is None:
            self.fixed_charge = old_Q

        self.update()

    def dielectric_area_fraction(self):
        """
        Fracción efectiva del área de las placas ocupada por el
        dieléctrico en la dirección lateral.

        self.insertion ya representa el solapamiento efectivo 0...1.
        El ancho físico del bloque queda almacenado para la geometría
        gráfica y para limitar el arrastre cuando sea menor que el ancho
        de la placa.
        """
        return clamp(self.insertion, 0.0, 1.0)

    def capacitance(self):
        A = self.area
        d = self.distance
        er = self.eps_r
        t = self.dielectric_thickness
        f = self.dielectric_area_fraction()

        # Zona sin dieléctrico: campo aproximadamente uniforme en aire.
        C_air = EPS0 * A / d

        # Zona que contiene un slab de espesor t. Hay dos capas de aire
        # (si corresponde) y una de dieléctrico en serie en la dirección
        # del campo.
        denominator = d - t + t / er
        denominator = max(denominator, 1e-15)

        # Solo la parte de área f*A tiene esa trayectoria.
        C_dielectric_region = EPS0 * (A * f) / denominator
        C_air_region = EPS0 * (A * (1.0 - f)) / d

        return C_air_region + C_dielectric_region

    def update(self):
        self.C = self.capacitance()

        if self.battery_connected:
            self.V = self.V_battery
            self.Q = self.C * self.V
            self.fixed_charge = self.Q
        else:
            if self.fixed_charge is None:
                self.fixed_charge = self.Q if hasattr(self, "Q") else 0.0
            self.Q = self.fixed_charge
            self.V = self.Q / self.C if self.C > 0 else 0.0

        self.U = 0.5 * self.C * self.V ** 2

        self.E_average = self.V / self.distance

        # Descomposición del campo eléctrico medio.
        # Campo equivalente en vacío para la misma carga libre:
        #     E_vacío = sigma_f/eps0 = Q/(eps0*A)
        # Campo inducido por las cargas ligadas del dieléctrico:
        #     E_inducido = E_resultante - E_vacío
        self.E_vacuum = (
            self.Q / (EPS0 * self.area)
            if self.area > 0.0 else 0.0
        )
        self.E_resultant = self.E_average
        self.E_induced = self.E_resultant - self.E_vacuum

        d = self.distance
        t = self.dielectric_thickness
        er = self.eps_r

        denominator = d - t + t / er
        denominator = max(denominator, 1e-15)

        self.E_dielectric = self.V / denominator
        self.E_air_series = self.E_dielectric / er

        # Campo aproximado según posición lateral.
        if self.insertion > 0.5:
            self.E_probe_default = self.E_dielectric
        else:
            self.E_probe_default = self.E_average

        self.surface_charge_density = self.Q / self.area

        # Energía por unidad de volumen aproximada para una región dieléctrica.
        self.energy_density_air = 0.5 * EPS0 * self.E_average ** 2
        self.energy_density_dielectric = (
            0.5 * EPS0 * er * self.E_dielectric ** 2
        )

    def connect_battery(self):
        # Al conectar la batería se impone V.
        self.battery_connected = True
        self.fixed_charge = None
        self.update()

    def disconnect_battery(self):
        # Al desconectar se conserva la carga instantánea.
        self.fixed_charge = self.Q
        self.battery_connected = False
        self.update()

    def toggle_battery(self):
        if self.battery_connected:
            self.disconnect_battery()
        else:
            self.connect_battery()

    def insert_percent(self):
        return 100.0 * self.insertion

    def effective_relative_capacitance(self):
        C0 = EPS0 * self.area / self.distance
        return self.C / C0 if C0 else float("nan")

    def charge_in_electrons(self):
        return self.Q / E_CHARGE

    @property
    def electric_field_vacuum(self):
        return self.E_vacuum

    @property
    def electric_field_induced(self):
        return self.E_induced

    @property
    def electric_field_resultant(self):
        return self.E_resultant

    def dielectric_polarization(self):
        # P = eps0 (er - 1) E
        return EPS0 * (self.eps_r - 1.0) * self.E_dielectric

    def voltage_energy_state(self):
        return (
            "BATERÍA CONECTADA: V fijada por la fuente"
            if self.battery_connected
            else "CAPACITOR AISLADO: Q conservada"
        )


# ============================================================================
# MULTÍMETRO VIRTUAL
# ============================================================================

class Multimeter(tk.Toplevel):
    """Multímetro virtual independiente."""

    MODES = {
        "Tensión (V)": "V",
        "Capacitancia (C)": "C",
        "Carga (Q)": "Q",
        "Energía (U)": "U",
        "Campo eléctrico (E)": "E",
    }

    def __init__(self, parent, simulator):
        super().__init__(parent)
        self.simulator = simulator
        self.title("Multímetro virtual")
        self.geometry("390x470")
        self.resizable(False, False)
        self.configure(bg="#20252b")
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.mode_var = tk.StringVar(value="Tensión (V)")
        self.auto_range = tk.BooleanVar(value=True)
        self.power_var = tk.BooleanVar(value=True)
        self.display_var = tk.StringVar(value="0.000 V")

        self._build()
        self.update_meter()

    def _build(self):
        top = tk.Frame(self, bg="#30363d", bd=2, relief="raised")
        top.pack(fill="x", padx=12, pady=12)

        tk.Label(
            top, text="MULTÍMETRO DIGITAL",
            bg="#30363d", fg="#f0f0f0",
            font=("Segoe UI", 15, "bold")
        ).pack(pady=(10, 2))

        tk.Label(
            top, text="Instrumento virtual",
            bg="#30363d", fg="#aeb6bf",
            font=("Segoe UI", 9)
        ).pack(pady=(0, 10))

        display = tk.Frame(
            self, bg="#0b0e10", bd=5, relief="sunken",
            height=100
        )
        display.pack(fill="x", padx=20, pady=8)
        display.pack_propagate(False)

        tk.Label(
            display, textvariable=self.display_var,
            bg="#0b0e10", fg="#d9ffb8",
            font=("Consolas", 24, "bold")
        ).pack(expand=True)

        control = ttk.LabelFrame(self, text="Magnitud medida")
        control.pack(fill="x", padx=20, pady=12)

        combo = ttk.Combobox(
            control, textvariable=self.mode_var,
            values=list(self.MODES.keys()),
            state="readonly"
        )
        combo.pack(fill="x", padx=10, pady=10)
        combo.bind("<<ComboboxSelected>>",
                   lambda e: self.update_meter())

        ttk.Checkbutton(
            control, text="Rango automático",
            variable=self.auto_range
        ).pack(anchor="w", padx=10, pady=4)

        ttk.Checkbutton(
            control, text="Instrumento encendido",
            variable=self.power_var,
            command=self.update_meter
        ).pack(anchor="w", padx=10, pady=4)

        self.status = tk.StringVar(value="Listo")
        tk.Label(
            self, textvariable=self.status,
            bg="#20252b", fg="#cbd5df",
            font=("Segoe UI", 9)
        ).pack(pady=5)

        ttk.Button(
            self, text="Actualizar lectura",
            command=self.update_meter
        ).pack(pady=8)

    def update_meter(self):
        if not self.power_var.get():
            self.display_var.set("----")
            self.status.set("Multímetro apagado")
            return

        p = self.simulator.physics
        mode = self.MODES[self.mode_var.get()]

        if mode == "V":
            value = p.V
            text = fmt_si(value, "V")
        elif mode == "C":
            value = p.C
            text = fmt_si(value, "F")
        elif mode == "Q":
            value = p.Q
            text = fmt_si(value, "C")
        elif mode == "U":
            value = p.U
            text = fmt_si(value, "J")
        else:
            value = self.simulator.probe_field
            text = fmt_si(value, "V/m")

        self.display_var.set(text)
        self.status.set(
            f"{p.voltage_energy_state()} | {time.strftime('%H:%M:%S')}"
        )


# ============================================================================
# DETECTOR DE CAMPO
# ============================================================================

class FieldDetector(tk.Toplevel):
    """Detector de campo eléctrico con sonda desplazable."""

    def __init__(self, parent, simulator):
        super().__init__(parent)
        self.simulator = simulator
        self.title("Detector de campo eléctrico")
        self.geometry("430x520")
        self.resizable(False, False)

        self.field_var = tk.StringVar(value="0 V/m")
        self.position_var = tk.StringVar(value="Posición: 0.0 %")
        self.region_var = tk.StringVar(value="Región: aire")

        self._build()
        self.update_detector()

    def _build(self):
        title = ttk.Label(
            self, text="DETECTOR DE CAMPO ELÉCTRICO",
            font=("Segoe UI", 14, "bold")
        )
        title.pack(pady=12)

        self.canvas = tk.Canvas(
            self, width=380, height=220,
            bg="#d8f2ff", highlightthickness=1
        )
        self.canvas.pack(pady=8)

        self.field_label = ttk.Label(
            self, textvariable=self.field_var,
            font=("Consolas", 20, "bold")
        )
        self.field_label.pack(pady=8)

        ttk.Label(
            self, textvariable=self.region_var
        ).pack()

        ttk.Label(
            self, textvariable=self.position_var
        ).pack(pady=4)

        frame = ttk.LabelFrame(self, text="Sonda")
        frame.pack(fill="x", padx=20, pady=12)

        self.probe_scale = ttk.Scale(
            frame, from_=0, to=100,
            command=self._move_probe
        )
        self.probe_scale.set(self.simulator.probe_x_percent)
        self.probe_scale.pack(fill="x", padx=12, pady=12)

        ttk.Button(
            self, text="Centrar sonda",
            command=self.center_probe
        ).pack(pady=5)

        note = (
            "El detector usa el campo local del modelo ideal.\n"
            "Los efectos de borde y fringing no se representan."
        )
        ttk.Label(
            self, text=note, justify="center",
            foreground="#555"
        ).pack(pady=12)

    def _move_probe(self, value):
        self.simulator.probe_x_percent = float(value)
        self.update_detector()

    def center_probe(self):
        self.probe_scale.set(50)
        self.simulator.probe_x_percent = 50
        self.update_detector()

    def update_detector(self):
        p = self.simulator.physics

        # Interpretación de la sonda:
        # 0% corresponde al lado sin dieléctrico y 100% al extremo
        # que coincide con la zona de inserción.
        x = self.simulator.probe_x_percent / 100.0

        # Si x cae dentro de la zona lateral ocupada por dieléctrico:
        if p.insertion > 0 and x <= p.insertion:
            E = p.E_dielectric
            region = "dieléctrico / región en serie"
        else:
            E = p.E_average
            region = "aire"

        self.simulator.probe_field = E
        self.field_var.set(fmt_si(E, "V/m"))
        self.position_var.set(
            f"Posición de la sonda: {self.simulator.probe_x_percent:.1f} %"
        )
        self.region_var.set(f"Región: {region}")

        self.canvas.delete("all")

        # Placas esquemáticas.
        self.canvas.create_rectangle(
            55, 35, 75, 185, fill="#b8b8b8", outline="#555"
        )
        self.canvas.create_rectangle(
            305, 35, 325, 185, fill="#b8b8b8", outline="#555"
        )

        # Líneas de campo verticales entre las placas.
        for xx in range(105, 300, 38):
            self.canvas.create_line(
                xx, 60, xx, 160,
                arrow=tk.LAST,
                width=2
            )

        px = 95 + 220 * x
        self.canvas.create_line(
            px, 45, px, 175,
            fill="#333", width=3
        )
        self.canvas.create_oval(
            px - 7, 103, px + 7, 117,
            fill="#ffffff", outline="#111", width=2
        )

        self.canvas.create_text(
            190, 207,
            text="placa (+) superior     •     placa (-) inferior",
            font=("Segoe UI", 9)
        )


# ============================================================================
# APLICACIÓN PRINCIPAL
# ============================================================================

class CapacitorLab(tk.Tk):

    BG = "#dff3fb"
    PANEL = "#f4f4f4"
    BLUE = "#2e74b5"
    DARK = "#24313d"

    def __init__(self):
        super().__init__()

        self.title("Laboratorio Virtual de Capacitores — Física y Electromagnetismo")
        self.geometry("1450x900")
        self.minsize(1180, 760)

        self.physics = CapacitorPhysics()

        # Estado gráfico del dieléctrico.
        self.dielectric_dragging = False
        self.drag_offset = 0.0

        # Estado de la sonda.
        self.probe_x_percent = 50.0
        self.probe_field = self.physics.E_average

        self.multimeter = None
        self.detector = None

        # Variables de interfaz.
        self.var_V = tk.DoubleVar(value=1.5)
        self.var_area_cm2 = tk.DoubleVar(value=100.0)
        self.var_d_mm = tk.DoubleVar(value=10.0)
        self.var_eps = tk.DoubleVar(value=5.0)
        self.var_t_mm = tk.DoubleVar(value=10.0)
        self.var_insert = tk.DoubleVar(value=0.0)
        self.var_dielectric_width = tk.DoubleVar(value=100.0)

        self.var_material = tk.StringVar(value="Vidrio")
        self.var_battery = tk.BooleanVar(value=True)

        # Variables de los cuadros de entrada manual.
        # La clave coincide con el identificador del parámetro.
        self.manual_entry_vars = {}
        self.manual_entries = {}

        self.show_charges = tk.BooleanVar(value=True)
        self.show_field_lines = tk.BooleanVar(value=True)
        self.show_values = tk.BooleanVar(value=True)

        self.status_var = tk.StringVar(value="Sistema listo.")
        self.measurement_var = tk.StringVar()

        self._configure_style()
        self._build_menu()
        self._build_header()
        self._build_layout()
        self._bind_events()

        self._sync_controls_from_physics()
        self.update_simulation()

        self.after(100, self._periodic_update)

    # ---------------------------------------------------------------------
    # ESTILO
    # ---------------------------------------------------------------------

    def _configure_style(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 18, "bold")
        )
        style.configure(
            "Section.TLabelframe.Label",
            font=("Segoe UI", 10, "bold")
        )
        style.configure(
            "Value.TLabel",
            font=("Consolas", 10, "bold")
        )
        style.configure(
            "Small.TLabel",
            font=("Segoe UI", 9)
        )

    # ---------------------------------------------------------------------
    # MENÚ
    # ---------------------------------------------------------------------

    def _build_menu(self):
        menu = tk.Menu(self)

        archivo = tk.Menu(menu, tearoff=False)
        archivo.add_command(label="Reiniciar todo",
                            command=self.reset_all)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self.destroy)

        instrumentos = tk.Menu(menu, tearoff=False)
        instrumentos.add_command(
            label="Abrir multímetro",
            command=self.open_multimeter
        )
        instrumentos.add_command(
            label="Abrir detector de campo",
            command=self.open_detector
        )

        ayuda = tk.Menu(menu, tearoff=False)
        ayuda.add_command(
            label="Modelo físico",
            command=self.show_physics
        )
        ayuda.add_command(
            label="Acerca del simulador",
            command=self.show_about
        )

        menu.add_cascade(label="Archivo", menu=archivo)
        menu.add_cascade(label="Instrumentos", menu=instrumentos)
        menu.add_cascade(label="Ayuda", menu=ayuda)

        self.config(menu=menu)

    # ---------------------------------------------------------------------
    # CABECERA
    # ---------------------------------------------------------------------

    def _build_header(self):
        header = tk.Frame(self, bg=self.BLUE, height=62)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="LABORATORIO VIRTUAL DE CAPACITORES",
            bg=self.BLUE,
            fg="white",
            font=("Segoe UI", 17, "bold")
        ).pack(side="left", padx=20)

        tk.Label(
            header,
            text="Placas paralelas • Dieléctricos • Instrumentación",
            bg=self.BLUE,
            fg="#e5f3ff",
            font=("Segoe UI", 9)
        ).pack(side="right", padx=20)

    # ---------------------------------------------------------------------
    # LAYOUT
    # ---------------------------------------------------------------------

    def _build_layout(self):
        root = tk.Frame(self, bg=self.BG)
        root.pack(fill="both", expand=True)

        # Panel izquierdo: controles.
        self.left_panel = ttk.Frame(root, width=305)
        self.left_panel.pack(side="left", fill="y", padx=8, pady=8)
        self.left_panel.pack_propagate(False)

        # Centro: simulación.
        center = tk.Frame(root, bg=self.BG)
        center.pack(side="left", fill="both", expand=True,
                   padx=4, pady=8)

        # Derecha: medidas.
        self.right_panel = ttk.Frame(root, width=330)
        self.right_panel.pack(side="right", fill="y", padx=8, pady=8)
        self.right_panel.pack_propagate(False)

        self._build_controls(self.left_panel)
        self._build_simulation(center)
        self._build_measurements(self.right_panel)

        status = tk.Label(
            self, textvariable=self.status_var,
            anchor="w", bg="#e8e8e8", fg="#333",
            relief="sunken", bd=1,
            font=("Segoe UI", 9)
        )
        status.pack(fill="x", side="bottom")

    # ---------------------------------------------------------------------
    # CONTROLES
    # ---------------------------------------------------------------------

    def _build_controls(self, parent):
        # Todos los parámetros numéricos disponen de dos métodos:
        # 1) deslizador para exploración continua,
        # 2) entrada manual para valores exactos.

        # Fuente.
        source = ttk.LabelFrame(
            parent, text="Fuente y estado",
            style="Section.TLabelframe"
        )
        source.pack(fill="x", pady=(0, 8))

        self.battery_button = ttk.Button(
            source, text="Desconectar batería",
            command=self.toggle_battery
        )
        self.battery_button.pack(fill="x", padx=10, pady=8)

        self.battery_state_label = ttk.Label(
            source, text="● Batería conectada"
        )
        self.battery_state_label.pack(pady=(0, 8))

        self._add_slider(
            source, "Tensión de batería V (V)",
            self.var_V, 0.0, 50.0,
            self._on_parameter_change
        )

        # Geometría.
        geom = ttk.LabelFrame(
            parent, text="Geometría del capacitor",
            style="Section.TLabelframe"
        )
        geom.pack(fill="x", pady=8)

        self._add_slider(
            geom, "Área A (cm²)",
            self.var_area_cm2, 1.0, 500.0,
            self._on_parameter_change
        )

        self._add_slider(
            geom, "Separación d (mm)",
            self.var_d_mm, 1.0, 50.0,
            self._on_parameter_change
        )

        self._add_slider(
            geom, "Espesor t (mm)",
            self.var_t_mm, 0.0, 50.0,
            self._on_parameter_change
        )

        self._add_slider(
            geom, "Ancho del dieléctrico / placa (%)",
            self.var_dielectric_width, 10.0, 250.0,
            self._on_parameter_change
        )

        # Dieléctrico.
        diel = ttk.LabelFrame(
            parent, text="Dieléctrico",
            style="Section.TLabelframe"
        )
        diel.pack(fill="x", pady=8)

        ttk.Label(diel, text="Material:").pack(
            anchor="w", padx=10, pady=(8, 2)
        )

        material_combo = ttk.Combobox(
            diel,
            textvariable=self.var_material,
            values=list(CapacitorPhysics.MATERIALS.keys())
                   + ["Personalizado"],
            state="readonly"
        )
        material_combo.pack(fill="x", padx=10, pady=4)
        material_combo.bind(
            "<<ComboboxSelected>>",
            self._material_changed
        )

        self._add_slider(
            diel, "εr",
            self.var_eps, 1.0, 100.0,
            self._on_parameter_change
        )

        self._add_slider(
            diel, "Inserción (%)",
            self.var_insert, 0.0, 100.0,
            self._on_parameter_change
        )

        ttk.Label(
            diel,
            text="Escriba valores exactos en las cajas y pulse Aplicar.\n"
                 "También puede arrastrar el bloque con el mouse.",
            justify="center",
            foreground="#555"
        ).pack(pady=7)

        # Visualización.
        view = ttk.LabelFrame(
            parent, text="Visualización",
            style="Section.TLabelframe"
        )
        view.pack(fill="x", pady=8)

        ttk.Checkbutton(
            view, text="Cargas de las placas",
            variable=self.show_charges,
            command=self.update_simulation
        ).pack(anchor="w", padx=10, pady=3)

        ttk.Checkbutton(
            view, text="Líneas de campo eléctrico",
            variable=self.show_field_lines,
            command=self.update_simulation
        ).pack(anchor="w", padx=10, pady=3)

        ttk.Checkbutton(
            view, text="Valores sobre la escena",
            variable=self.show_values,
            command=self.update_simulation
        ).pack(anchor="w", padx=10, pady=3)

        # Instrumentos.
        instruments = ttk.LabelFrame(
            parent, text="Instrumentos",
            style="Section.TLabelframe"
        )
        instruments.pack(fill="x", pady=8)

        ttk.Button(
            instruments,
            text="Abrir multímetro digital",
            command=self.open_multimeter
        ).pack(fill="x", padx=10, pady=5)

        ttk.Button(
            instruments,
            text="Abrir detector de campo",
            command=self.open_detector
        ).pack(fill="x", padx=10, pady=5)

        ttk.Button(
            instruments,
            text="Reiniciar todo",
            command=self.reset_all
        ).pack(fill="x", padx=10, pady=(5, 10))

    def _add_slider(self, parent, text, variable,
                    low, high, command):
        """
        Crea un control híbrido: deslizador + entrada numérica manual.

        El deslizador permite exploración rápida y el Entry permite
        introducir valores exactos. Enter y el botón "Aplicar" ejecutan
        exactamente la misma actualización física que el deslizador.
        """
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=8, pady=4)

        # ----------------------------
        # Encabezado del parámetro.
        # ----------------------------
        header = ttk.Frame(row)
        header.pack(fill="x")

        ttk.Label(
            header, text=text,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        range_label = ttk.Label(
            header,
            text=f"[{fmt_number(low, 5)} … {fmt_number(high, 5)}]",
            foreground="#666",
            font=("Segoe UI", 8)
        )
        range_label.pack(side="right")

        # ----------------------------
        # Deslizador + entrada exacta.
        # ----------------------------
        controls = ttk.Frame(row)
        controls.pack(fill="x", pady=(2, 0))

        scale = ttk.Scale(
            controls,
            from_=low, to=high,
            variable=variable,
            command=lambda value: command()
        )
        scale.pack(side="left", fill="x", expand=True, padx=(0, 6))

        # StringVar independiente para no obligar al usuario a escribir
        # un número completo mientras está editando.
        entry_var = tk.StringVar(value=fmt_number(variable.get(), 8))
        self.manual_entry_vars[text] = entry_var

        entry = ttk.Entry(
            controls,
            textvariable=entry_var,
            width=11,
            justify="right"
        )
        entry.pack(side="left", padx=(0, 4))
        self.manual_entries[text] = entry

        apply_button = ttk.Button(
            controls,
            text="Aplicar",
            width=8,
            command=lambda: apply_manual()
        )
        apply_button.pack(side="left")

        # ----------------------------
        # Estado y unidad visible.
        # ----------------------------
        info = ttk.Frame(row)
        info.pack(fill="x")

        value_label = ttk.Label(
            info,
            text="",
            foreground="#455a64",
            font=("Consolas", 8)
        )
        value_label.pack(side="right", pady=(1, 0))

        def mark_entry(valid, message=""):
            # ttk.Entry no garantiza background uniforme entre temas,
            # por eso se utiliza un estilo dinámico para el estado de error.
            try:
                if valid:
                    entry.configure(foreground="#222")
                else:
                    entry.configure(foreground="#b00020")
            except tk.TclError:
                pass

        def apply_manual(event=None):
            raw = entry_var.get().strip().replace(",", ".")

            try:
                value = float(raw)
            except ValueError:
                mark_entry(False)
                self._set_status(
                    f"Valor no válido para {text}: {raw!r}. "
                    "Introduzca un número."
                )
                entry.focus_set()
                entry.selection_range(0, tk.END)
                return "break"

            if not math.isfinite(value):
                mark_entry(False)
                self._set_status(
                    f"El valor de {text} debe ser un número finito."
                )
                entry.focus_set()
                entry.selection_range(0, tk.END)
                return "break"

            # Si está fuera del rango del deslizador, se limita al
            # extremo correspondiente y se informa al usuario.
            original = value
            value = clamp(value, low, high)

            variable.set(value)
            command()
            entry_var.set(fmt_number(variable.get(), 10))
            mark_entry(True)

            if original != value:
                self._set_status(
                    f"{text}: el valor solicitado estaba fuera del rango. "
                    f"Se aplicó {fmt_number(value, 10)}."
                )
            else:
                self._set_status(
                    f"{text} actualizado manualmente a "
                    f"{fmt_number(value, 10)}."
                )

            entry.icursor(tk.END)
            return "break"

        entry.bind("<Return>", apply_manual)
        entry.bind("<KP_Enter>", apply_manual)
        entry.bind("<FocusIn>",
                   lambda e: entry.selection_range(0, tk.END))

        def refresh(*_):
            current = variable.get()
            value_label.config(text=f"Actual: {fmt_number(current, 8)}")
            # El texto de la caja se actualiza únicamente cuando el campo
            # no tiene el foco. De ese modo el usuario puede escribir
            # 1.234 sin que la interfaz lo reemplace a mitad de edición.
            try:
                if self.focus_get() is not entry:
                    entry_var.set(fmt_number(current, 10))
                    mark_entry(True)
            except tk.TclError:
                entry_var.set(fmt_number(current, 10))

        variable.trace_add("write", refresh)
        refresh()

    # ---------------------------------------------------------------------
    # ESCENA
    # ---------------------------------------------------------------------

    def _build_simulation(self, parent):
        title = ttk.Label(
            parent,
            text="Capacitor de placas paralelas",
            style="Title.TLabel"
        )
        title.pack(pady=(2, 5))

        subtitle = ttk.Label(
            parent,
            text="Arrastre el dieléctrico horizontalmente para modificar "
                 "la fracción de área ocupada."
        )
        subtitle.pack(pady=(0, 7))

        self.canvas = tk.Canvas(
            parent,
            bg="#bde7f6",
            highlightthickness=1,
            highlightbackground="#7199aa"
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Configure>",
                         lambda e: self.update_simulation())

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self._canvas_press)
        self.canvas.bind("<B1-Motion>", self._canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._canvas_release)

    # ---------------------------------------------------------------------
    # MEDICIONES
    # ---------------------------------------------------------------------

    def _build_measurements(self, parent):
        measures = ttk.LabelFrame(
            parent, text="Mediciones",
            style="Section.TLabelframe"
        )
        measures.pack(fill="x", pady=(0, 8))

        self.measure_labels = {}

        fields = [
            ("Capacitancia", "C", "F"),
            ("Carga de la placa", "Q", "C"),
            ("Tensión", "V", "V"),
            ("Energía almacenada", "U", "J"),
            ("Campo eléctrico resultante", "E", "V/m"),
            ("Campo eléctrico en el vacío", "E_vac", "V/m"),
            ("Campo eléctrico inducido", "E_ind", "V/m"),
            ("Densidad superficial de carga", "sigma", "C/m²"),
            ("Polarización", "P", "C/m²"),
        ]

        for name, key, unit in fields:
            row = ttk.Frame(measures)
            row.pack(fill="x", padx=10, pady=4)

            ttk.Label(
                row, text=name
            ).pack(side="left")

            label = ttk.Label(
                row, text="—",
                style="Value.TLabel"
            )
            label.pack(side="right")

            self.measure_labels[key] = (label, unit)

        # Estado.
        state = ttk.LabelFrame(
            parent, text="Estado físico",
            style="Section.TLabelframe"
        )
        state.pack(fill="x", pady=8)

        self.state_text = tk.Text(
            state, height=7, width=36,
            wrap="word", font=("Consolas", 9),
            bg="#fafafa", relief="flat"
        )
        self.state_text.pack(fill="both", padx=8, pady=8)
        self.state_text.configure(state="disabled")

        # Ecuaciones.
        equations = ttk.LabelFrame(
            parent, text="Ecuaciones del modelo",
            style="Section.TLabelframe"
        )
        equations.pack(fill="both", expand=True, pady=8)

        self.eq_text = tk.Text(
            equations, height=14, width=36,
            wrap="word", font=("Consolas", 9),
            bg="#fafafa", relief="flat"
        )
        self.eq_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.eq_text.configure(state="disabled")

    # ---------------------------------------------------------------------
    # SINCRONIZACIÓN
    # ---------------------------------------------------------------------

    def _sync_controls_from_physics(self):
        p = self.physics
        self.var_V.set(p.V_battery)
        self.var_area_cm2.set(p.area * 1e4)
        self.var_d_mm.set(p.distance * 1e3)
        self.var_eps.set(p.eps_r)
        self.var_t_mm.set(p.dielectric_thickness * 1e3)
        self.var_insert.set(p.insertion * 100)
        self.var_dielectric_width.set(p.dielectric_width_ratio * 100)

    def _on_parameter_change(self):
        p = self.physics

        old_eps = p.eps_r

        p.set_parameters(
            V=self.var_V.get(),
            area=self.var_area_cm2.get() * 1e-4,
            distance=self.var_d_mm.get() * 1e-3,
            eps_r=self.var_eps.get(),
            thickness=self.var_t_mm.get() * 1e-3,
            insertion=self.var_insert.get() / 100.0,
            dielectric_width_ratio=self.var_dielectric_width.get() / 100.0
        )

        # Ajuste automático del espesor visual si d disminuyó.
        if p.dielectric_thickness * 1e3 != self.var_t_mm.get():
            self.var_t_mm.set(p.dielectric_thickness * 1e3)

        if old_eps != p.eps_r:
            self._set_status("Constante dieléctrica actualizada.")

        self.update_simulation()

    def _material_changed(self, event=None):
        material = self.var_material.get()

        if material in CapacitorPhysics.MATERIALS:
            self.var_eps.set(
                CapacitorPhysics.MATERIALS[material]
            )

        self._on_parameter_change()

    # ---------------------------------------------------------------------
    # BATERÍA
    # ---------------------------------------------------------------------

    def toggle_battery(self):
        self.physics.toggle_battery()
        self.var_battery.set(self.physics.battery_connected)

        if self.physics.battery_connected:
            self.battery_button.config(text="Desconectar batería")
            self.battery_state_label.config(
                text="● Batería conectada"
            )
            self._set_status(
                "Batería conectada: la tensión queda fijada por la fuente."
            )
        else:
            self.battery_button.config(text="Conectar batería")
            self.battery_state_label.config(
                text="○ Batería desconectada — capacitor aislado"
            )
            self._set_status(
                "Batería desconectada: se conserva la carga del capacitor."
            )

        self.update_simulation()

    # ---------------------------------------------------------------------
    # ARRASTRE DEL DIELÉCTRICO
    # ---------------------------------------------------------------------

    def _scene_geometry(self):
        """
        Vista de sección frontal:

              PLACA (+)
        =====================
             espacio d
              dieléctrico
        =====================
              PLACA (-)

        La coordenada horizontal representa la extensión lateral de la
        placa. La coordenada vertical representa la separación d.
        """
        w = max(600, self.canvas.winfo_width())
        h = max(450, self.canvas.winfo_height())

        plate_left = 0.22 * w
        plate_right = 0.82 * w

        top_plate_y = 0.29 * h
        bottom_plate_y = 0.71 * h

        plate_thickness = max(14.0, 0.022 * h)

        gap_top = top_plate_y + plate_thickness / 2
        gap_bottom = bottom_plate_y - plate_thickness / 2

        return (
            plate_left, plate_right,
            top_plate_y, bottom_plate_y,
            gap_top, gap_bottom,
            plate_thickness
        )

    def _dielectric_geometry(self):
        """
        Geometría gráfica coherente con:
          - espesor t en dirección del campo;
          - ancho lateral independiente;
          - solapamiento lateral independiente.

        La posición se determina a partir de la fracción efectiva de
        área ocupada (insertion). Para un bloque más ancho que la placa,
        puede sobresalir por ambos extremos cuando insertion=100 %.
        """
        (
            left_x, right_x,
            top_plate_y, bottom_plate_y,
            gap_top, gap_bottom,
            plate_thickness
        ) = self._scene_geometry()

        plate_width = right_x - left_x
        block_width = clamp(
            plate_width * self.physics.dielectric_width_ratio,
            24.0,
            2.50 * plate_width
        )

        # insertion = anchura de solapamiento / anchura de placa.
        overlap = self.physics.insertion * plate_width

        # El borde derecho se coloca de forma que el solapamiento con
        # la placa sea exactamente 'overlap'. Esto mantiene coherencia
        # visual incluso cuando el bloque es mayor o menor que la placa.
        x_right = left_x + overlap
        x_left = x_right - block_width

        # Espesor t/d: 1 => contacto con ambas placas; <1 => aire arriba
        # y abajo.
        d_ratio = clamp(
            self.physics.dielectric_thickness /
            max(self.physics.distance, 1e-15),
            0.0, 1.0
        )

        gap_height = max(20.0, gap_bottom - gap_top)
        block_height = d_ratio * gap_height

        y_center = 0.5 * (gap_top + gap_bottom)
        y1 = y_center - block_height / 2
        y2 = y_center + block_height / 2

        return x_left, x_right, y1, y2

    def _canvas_press(self, event):
        x1, x2, y1, y2 = self._dielectric_geometry()

        if x1 <= event.x <= x2 and y1 <= event.y <= y2:
            self.dielectric_dragging = True
            self.drag_offset = event.x - x2
            self.canvas.configure(cursor="hand2")
            return

        if abs(event.x - x2) < 18 and y1 - 15 <= event.y <= y2 + 15:
            self.dielectric_dragging = True
            self.drag_offset = event.x - x2
            self.canvas.configure(cursor="hand2")

    def _canvas_drag(self, event):
        if not self.dielectric_dragging:
            return

        (
            left_x, right_x,
            top_plate_y, bottom_plate_y,
            gap_top, gap_bottom,
            plate_thickness
        ) = self._scene_geometry()

        plate_width = right_x - left_x
        block_width = clamp(
            plate_width * self.physics.dielectric_width_ratio,
            24.0,
            2.50 * plate_width
        )

        target_right = event.x - self.drag_offset

        # Solapamiento real del bloque con la región activa de las placas.
        block_left = target_right - block_width
        overlap_px = max(
            0.0,
            min(target_right, right_x) -
            max(block_left, left_x)
        )

        f = clamp(overlap_px / plate_width, 0.0, 1.0)

        self.var_insert.set(100.0 * f)
        self.physics.set_parameters(insertion=f)

        self.update_simulation()

    def _canvas_release(self, event):
        self.dielectric_dragging = False
        self.canvas.configure(cursor="")

    # ---------------------------------------------------------------------
    # DIBUJO PRINCIPAL
    # ---------------------------------------------------------------------

    def update_simulation(self):
        if not hasattr(self, "canvas"):
            return

        p = self.physics
        self.canvas.delete("all")

        w = max(600, self.canvas.winfo_width())
        h = max(450, self.canvas.winfo_height())

        (
            left_x, right_x,
            top_plate_y, bottom_plate_y,
            gap_top, gap_bottom,
            plate_thickness
        ) = self._scene_geometry()
        top = top_plate_y
        bottom = bottom_plate_y

        # -----------------------------------------------------------------
        # Título de escena.
        # -----------------------------------------------------------------

        self.canvas.create_text(
            w / 2, 25,
            text="CAPACITOR DE PLACAS PARALELAS",
            font=("Segoe UI", 13, "bold"),
            fill="#20323d"
        )

        # -----------------------------------------------------------------
        # Batería.
        # -----------------------------------------------------------------

        bx = 0.08 * w
        by = 0.50 * h

        self._draw_battery(
            bx, by, p.V,
            connected=p.battery_connected
        )

        # -----------------------------------------------------------------
        # Cables.
        # -----------------------------------------------------------------

        wire = "#39444b"
        width = 5

        # La batería alimenta las dos placas horizontales.
        self.canvas.create_line(
            bx + 30, by - 48,
            bx + 30, top_plate_y,
            left_x, top_plate_y,
            fill=wire, width=width
        )
        self.canvas.create_line(
            bx + 30, by + 48,
            bx + 30, bottom_plate_y,
            left_x, bottom_plate_y,
            fill=wire, width=width
        )

        # -----------------------------------------------------------------
        # Placas paralelas.
        # -----------------------------------------------------------------

        plate_y1 = top_plate_y - plate_thickness / 2
        plate_y2 = bottom_plate_y - plate_thickness / 2

        self.canvas.create_rectangle(
            left_x, plate_y1,
            right_x, top_plate_y + plate_thickness / 2,
            fill="#aeb6bd", outline="#4d555b", width=2
        )

        self.canvas.create_rectangle(
            left_x, bottom_plate_y - plate_thickness / 2,
            right_x, bottom_plate_y + plate_thickness / 2,
            fill="#aeb6bd", outline="#4d555b", width=2
        )

        self.canvas.create_text(
            right_x + 35, top_plate_y,
            text="+",
            font=("Segoe UI", 15, "bold"),
            fill="#b33131"
        )
        self.canvas.create_text(
            right_x + 35, bottom_plate_y,
            text="−",
            font=("Segoe UI", 15, "bold"),
            fill="#315fa1"
        )

        # -----------------------------------------------------------------
        # Dieléctrico.
        # -----------------------------------------------------------------

        dx1, dx2, dy1, dy2 = self._dielectric_geometry()

        # Color aproximado según epsilon.
        er = p.eps_r

        if er < 2:
            diel_fill = "#d8d8d8"
        elif er < 4:
            diel_fill = "#ead8aa"
        elif er < 7:
            diel_fill = "#cfcf6a"
        elif er < 20:
            diel_fill = "#d4a6cf"
        else:
            diel_fill = "#9bb7dc"

        self.canvas.create_rectangle(
            dx1, dy1, dx2, dy2,
            fill=diel_fill,
            outline="#5a5a45",
            width=2,
            tags=("dielectric",)
        )

        # Etiqueta del dieléctrico.
        if self.show_values.get() and (dx2 - dx1) > 55:
            self.canvas.create_text(
                (dx1 + dx2) / 2,
                (dy1 + dy2) / 2,
                text=f"εr = {p.eps_r:.3g}\n"
                     f"{self.var_material.get()}",
                font=("Segoe UI", 9, "bold"),
                fill="#333",
                tags=("dielectric",)
            )

        # -----------------------------------------------------------------
        # Líneas de campo.
        # -----------------------------------------------------------------

        if self.show_field_lines.get():
            self._draw_field_lines(left_x, right_x, top, bottom)

        # -----------------------------------------------------------------
        # Cargas.
        # -----------------------------------------------------------------

        if self.show_charges.get():
            self._draw_charges(left_x, right_x, top, bottom)

        # -----------------------------------------------------------------
        # Cotas.
        # -----------------------------------------------------------------

        # Cota de separación d: se dibuja verticalmente.
        dim_x = right_x + 85
        self.canvas.create_line(
            dim_x, top_plate_y,
            dim_x, bottom_plate_y,
            fill="#3e4e56", width=1,
            arrow=tk.BOTH
        )
        self.canvas.create_text(
            dim_x + 8, (top_plate_y + bottom_plate_y) / 2,
            text=f"d = {p.distance * 1e3:.3g} mm",
            anchor="w",
            font=("Segoe UI", 9, "bold"),
            fill="#3e4e56"
        )

        # Cota del espesor t.
        dx1, dx2, dy1, dy2 = self._dielectric_geometry()
        self.canvas.create_line(
            dx2 + 20, dy1,
            dx2 + 20, dy2,
            fill="#5d6b72", width=1,
            arrow=tk.BOTH
        )
        self.canvas.create_text(
            dx2 + 28, (dy1 + dy2) / 2,
            text=f"t = {p.dielectric_thickness * 1e3:.3g} mm",
            anchor="w",
            font=("Segoe UI", 9),
            fill="#4c5960"
        )

        overlap_px = (right_x - left_x) * p.insertion
        self._draw_dimension(
            left_x, left_x + overlap_px,
            bottom_plate_y + 55,
            f"área ocupada = {p.insertion * 100:.1f}%"
        )

        self.canvas.create_text(
            (left_x + right_x) / 2,
            bottom_plate_y + 88,
            text=f"A = {p.area * 1e4:.3g} cm²    |    "
                 f"ancho dieléctrico = {p.dielectric_width_ratio * 100:.1f}% "
                 f"del ancho de placa",
            font=("Segoe UI", 10),
            fill="#354650"
        )

        # -----------------------------------------------------------------
        # Caja de información.
        # -----------------------------------------------------------------

        if self.show_values.get():
            self._draw_scene_info(w, h)

            holgura = p.distance - p.dielectric_thickness
            label = (
                "DIELÉCTRICO AJUSTADO A LAS PLACAS"
                if abs(holgura) < max(1e-12, 1e-4 * p.distance)
                else f"ESPACIO DE AIRE TOTAL = {holgura * 1e3:.3g} mm"
            )
            self.canvas.create_text(
                (left_x + right_x) / 2,
                0.92 * h,
                text=label,
                font=("Segoe UI", 9, "bold"),
                fill="#385563"
            )

        self._update_measurements()
        self._update_external_instruments()

    def _draw_battery(self, x, y, voltage, connected=True):
        # Cuerpo.
        self.canvas.create_rectangle(
            x - 30, y - 55,
            x + 30, y + 55,
            fill="#e6a13c",
            outline="#7a5520",
            width=2
        )

        # Terminales.
        self.canvas.create_rectangle(
            x - 9, y - 70,
            x + 9, y - 55,
            fill="#b7b7b7",
            outline="#555"
        )

        self.canvas.create_rectangle(
            x - 9, y + 55,
            x + 9, y + 70,
            fill="#b7b7b7",
            outline="#555"
        )

        self.canvas.create_text(
            x, y,
            text=f"{voltage:.3g} V",
            font=("Segoe UI", 10, "bold"),
            fill="#222"
        )

        self.canvas.create_text(
            x, y - 31,
            text="+",
            font=("Segoe UI", 12, "bold")
        )
        self.canvas.create_text(
            x, y + 31,
            text="−",
            font=("Segoe UI", 12, "bold")
        )

        if not connected:
            # Símbolo de circuito abierto.
            self.canvas.create_line(
                x + 30, y - 48,
                x + 55, y - 48,
                fill="#39444b", width=5
            )
            self.canvas.create_line(
                x + 30, y + 48,
                x + 55, y + 48,
                fill="#39444b", width=5
            )
            self.canvas.create_text(
                x + 75, y,
                text="AISLADO",
                font=("Segoe UI", 8, "bold"),
                fill="#9a2d2d"
            )

    def _draw_field_lines(self, lx, rx, top, bottom):
        p = self.physics

        # Dirección de E para Q>0: de la placa positiva superior a la
        # negativa inferior.
        direction = tk.LAST if p.Q >= 0 else tk.FIRST

        xs = [
            lx + 40 + i * ((rx - lx - 80) / 6)
            for i in range(7)
        ]

        for x in xs:
            self.canvas.create_line(
                x, top + 18,
                x, bottom - 18,
                fill="#4782a3",
                width=1.5,
                arrow=direction
            )

        self.canvas.create_text(
            lx + 24,
            (top + bottom) / 2,
            text="E",
            font=("Segoe UI", 11, "bold"),
            fill="#315c75"
        )

    def _draw_charges(self, lx, rx, top, bottom):
        p = self.physics

        n = int(clamp(
            abs(p.Q) / max(EPS0 * p.area * 1e5, 1e-20),
            6, 28
        ))

        xs = [
            lx + 25 + i * ((rx - lx - 50) / max(n - 1, 1))
            for i in range(n)
        ]

        top_sign = "+" if p.Q >= 0 else "−"
        bottom_sign = "−" if p.Q >= 0 else "+"

        for x in xs:
            self.canvas.create_text(
                x, top + 2,
                text=top_sign,
                font=("Segoe UI", 10, "bold"),
                fill="#b33131"
            )
            self.canvas.create_text(
                x, bottom - 2,
                text=bottom_sign,
                font=("Segoe UI", 10, "bold"),
                fill="#315fa1"
            )

    def _draw_dimension(self, x1, x2, y, text):
        if abs(x2 - x1) < 4:
            return

        self.canvas.create_line(
            x1, y, x2, y,
            fill="#3e4e56", width=1,
            arrow=tk.BOTH
        )

        self.canvas.create_text(
            (x1 + x2) / 2,
            y - 10,
            text=text,
            font=("Segoe UI", 9, "bold"),
            fill="#3e4e56"
        )

    def _draw_scene_info(self, w, h):
        p = self.physics

        x1 = 0.04 * w
        y1 = 0.80 * h
        x2 = 0.44 * w
        y2 = min(h - 18, y1 + 138)

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#eef8fc",
            outline="#7aa3b5"
        )

        info = (
            f"C = {fmt_si(p.C, 'F')}\n"
            f"Q = {fmt_si(p.Q, 'C')}\n"
            f"U = {fmt_si(p.U, 'J')}\n"
            f"E_resultante = {fmt_si(p.E_resultant, 'V/m')}\n"
            f"E_vacío = {fmt_si(p.E_vacuum, 'V/m')}\n"
            f"E_inducido = {fmt_si(p.E_induced, 'V/m')}\n"
            f"f_área = {p.insertion * 100:.1f}%"
        )

        self.canvas.create_text(
            x1 + 12, y1 + 10,
            text=info,
            anchor="nw",
            font=("Consolas", 10),
            fill="#23323b"
        )

        state = "CONECTADA" if p.battery_connected else "AISLADO"
        self.canvas.create_text(
            x2 - 10, y2 - 12,
            text=state,
            anchor="se",
            font=("Segoe UI", 9, "bold"),
            fill="#2c5368"
        )

    # ---------------------------------------------------------------------
    # MEDICIONES Y TEXTO
    # ---------------------------------------------------------------------

    def _update_measurements(self):
        p = self.physics

        values = {
            "C": p.C,
            "Q": p.Q,
            "V": p.V,
            "U": p.U,
            "E": p.E_resultant,
            "E_vac": p.E_vacuum,
            "E_ind": p.E_induced,
            "sigma": p.surface_charge_density,
            "P": p.dielectric_polarization(),
        }

        for key, value in values.items():
            label, unit = self.measure_labels[key]
            label.config(text=fmt_si(value, unit))

        self._set_text(
            self.state_text,
            (
                f"{p.voltage_energy_state()}\n\n"
                f"Área ocupada por el dieléctrico: {p.insertion * 100:.2f} %\n"
                f"Ancho del bloque: {p.dielectric_width_ratio * 100:.2f} % de la placa\n"
                f"Constante relativa: εr = {p.eps_r:.5g}\n"
                f"Espesor: t = {p.dielectric_thickness * 1e3:.5g} mm\n"
                f"Holgura total: {(p.distance - p.dielectric_thickness) * 1e3:.5g} mm\n"
                f"Factor C/C0 = {p.effective_relative_capacitance():.5g}\n"
                f"Campo en vacío = {fmt_si(p.E_vacuum, 'V/m')}\n"
                f"Campo inducido = {fmt_si(p.E_induced, 'V/m')}\n"
                f"Campo resultante = {fmt_si(p.E_resultant, 'V/m')}\n"
                f"Carga equivalente en electrones:\n"
                f"    N = {p.charge_in_electrons():.5g}\n"
            )
        )

        eq = (
            "C0 = ε0 A / d\n\n"
            "f = área ocupada / área de placa\n"
            "C = C0(1−f) + Creg f\n\n"
            "Creg = ε0 A /\n"
            "      (d−t+t/εr)\n\n"
            "Con batería:\n"
            "    Q = CV\n"
            "    U = ½CV²\n\n"
            "Aislado:\n"
            "    Q = cte.\n"
            "    V = Q/C\n"
            "    U = Q²/(2C)\n\n"
            "E_resultante = V/d\n"
            "E_vacío = Q/(ε0 A)\n"
            "E_inducido = E_resultante − E_vacío\n"
            "E_diel = V/(d−t+t/εr)\n\n"
            "Holgura = d−t\n"
            "t=d: contacto con ambas placas\n"
            "t<d: espacios de aire\n"
        )

        self._set_text(self.eq_text, eq)

    def _set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    # ---------------------------------------------------------------------
    # INSTRUMENTOS
    # ---------------------------------------------------------------------

    def open_multimeter(self):
        if self.multimeter is not None:
            try:
                if self.multimeter.winfo_exists():
                    self.multimeter.lift()
                    return
            except tk.TclError:
                pass

        self.multimeter = Multimeter(self, self)

    def open_detector(self):
        if self.detector is not None:
            try:
                if self.detector.winfo_exists():
                    self.detector.lift()
                    return
            except tk.TclError:
                pass

        self.detector = FieldDetector(self, self)

    def _update_external_instruments(self):
        if self.multimeter is not None:
            try:
                if self.multimeter.winfo_exists():
                    self.multimeter.update_meter()
            except tk.TclError:
                self.multimeter = None

        if self.detector is not None:
            try:
                if self.detector.winfo_exists():
                    self.detector.update_detector()
            except tk.TclError:
                self.detector = None

    # ---------------------------------------------------------------------
    # REINICIO
    # ---------------------------------------------------------------------

    def reset_all(self):
        if not messagebox.askyesno(
            "Reiniciar",
            "¿Desea restablecer todos los parámetros?"
        ):
            return

        self.physics.reset()
        self._sync_controls_from_physics()

        self.var_material.set("Vidrio")
        self.probe_x_percent = 50.0
        self.probe_field = self.physics.E_average

        self.battery_button.config(text="Desconectar batería")
        self.battery_state_label.config(
            text="● Batería conectada"
        )

        self._set_status("Todos los parámetros fueron restablecidos.")
        self.update_simulation()

    # ---------------------------------------------------------------------
    # AYUDA
    # ---------------------------------------------------------------------

    def show_physics(self):
        text = (
            "MODELO FÍSICO\n\n"
            "El capacitor se trata como un sistema de placas paralelas "
            "ideales.\n\n"
            "Para la zona sin dieléctrico:\n"
            "    C_aire = ε0 A/d\n\n"
            "Para la zona con dieléctrico de espesor t:\n"
            "    C_reg = ε0 A/(d−t+t/εr)\n\n"
            "Si f es la fracción de área lateral ocupada:\n"
            "    C = C_aire(1−f) + C_reg f\n\n"
            "Batería conectada:\n"
            "    V = constante\n"
            "    Q = CV\n\n"
            "Batería desconectada:\n"
            "    Q = constante\n"
            "    V = Q/C\n\n"
            "Energía:\n"
            "    U = 1/2 CV² = Q²/(2C)\n\n"
            "Campo eléctrico medio:\n"
            "    E_resultante = V/d\n"
            "    E_vacío = Q/(ε0 A)\n"
            "    E_inducido = E_resultante − E_vacío\n"
            "La contribución inducida corresponde al campo de las cargas "
            "ligadas y, en este modelo, se opone al campo equivalente en vacío.\n\n"
            "Suposiciones: campo cuasiuniforme, dieléctrico lineal, "
            "homogéneo e isótropo y fringing despreciable."
        )
        messagebox.showinfo("Modelo físico", text)

    def show_about(self):
        messagebox.showinfo(
            "Acerca del simulador",
            "Laboratorio Virtual de Capacitores\n\n"
            "Aplicación educativa desarrollada con Python + Tkinter.\n"
            "No requiere pygame ni librerías externas.\n\n"
            "Incluye modelado de capacitancia, carga, energía, "
            "campo eléctrico y dieléctricos parcialmente insertados, "
            "con espesor ajustable y tamaño lateral variable."
        )

    # ---------------------------------------------------------------------
    # ESTADO
    # ---------------------------------------------------------------------

    def _set_status(self, text):
        self.status_var.set(text)

    def _periodic_update(self):
        if self.winfo_exists():
            self.update_simulation()
            self.after(250, self._periodic_update)


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    app = CapacitorLab()
    app.mainloop()


if __name__ == "__main__":
    main()
