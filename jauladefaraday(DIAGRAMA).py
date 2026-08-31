"""
===============================================================
        SIMULADOR 2D — JAULA DE FARADAY
===============================================================

Autor: Simulador educativo de Física
Tema: Electrostática / Conductores / Jaula de Faraday

Descripción:
------------
Este programa genera una representación 2D de una jaula de
Faraday sometida a un campo eléctrico externo.

Se muestran:

    1. Campo eléctrico externo.
    2. Dirección del campo mediante flechas.
    3. Conductor de la jaula.
    4. Cargas inducidas en la superficie.
    5. Región interior protegida.
    6. Campo eléctrico aproximadamente nulo dentro.
    7. Carga de prueba interior.
    8. Animación del campo externo.
    9. Intensidad del campo modificable.
    10. Apertura/cierre de la jaula.
    11. Visualización de líneas de campo.
    12. Panel informativo físico.

Modelo físico:
--------------

En equilibrio electrostático, para un conductor ideal:

                    E = 0

en el interior del material conductor y, para una cavidad
cerrada sin cargas internas, el campo producido por una fuente
externa no penetra idealmente en la cavidad.

La presencia del campo externo produce redistribución de
cargas en la superficie:

                    sigma = sigma(x,y)

La superficie del conductor se convierte en una superficie
equipotencial:

                    V = constante

y el campo es perpendicular a la superficie:

                    E_t = 0

En una representación idealizada de una jaula cerrada:

                    E_interior ≈ 0

IMPORTANTE:
------------
El dibujo representa el fenómeno electrostático idealizado.
Una jaula real puede presentar pequeñas penetraciones de campo
debido a:

    - aperturas,
    - geometría,
    - frecuencia,
    - espesor,
    - conductividad finita,
    - efectos de borde.

===============================================================
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button


# ===============================================================
# 1. CONSTANTES Y PARÁMETROS DEL MODELO
# ===============================================================

LIMITE_X = 12
LIMITE_Y = 7

# Centro de la jaula
CX = 0.0
CY = 0.0

# Dimensiones de la jaula
ANCHO_JAULA = 5.0
ALTO_JAULA = 4.0

# Espesor visual del conductor
ESPESOR_JAULA = 0.22

# Intensidad inicial del campo
E0_INICIAL = 1.0

# Número de flechas del campo
N_FLECHAS_X = 16
N_FLECHAS_Y = 10

# Radio visual de las cargas inducidas
RADIO_CARGA = 0.085

# Número de cargas sobre la superficie
N_CARGAS = 38


# ===============================================================
# 2. CONFIGURACIÓN DE LA FIGURA
# ===============================================================

plt.close("all")

fig, ax = plt.subplots(figsize=(15, 8))

plt.subplots_adjust(
    left=0.05,
    right=0.78,
    bottom=0.16,
    top=0.93
)

ax.set_xlim(-LIMITE_X, LIMITE_X)
ax.set_ylim(-LIMITE_Y, LIMITE_Y)

ax.set_aspect("equal")

ax.set_title(
    "JAULA DE FARADAY — BLINDAJE ELECTROSTÁTICO",
    fontsize=18,
    fontweight="bold",
    pad=15
)

ax.set_xlabel(
    "x",
    fontsize=12
)

ax.set_ylabel(
    "y",
    fontsize=12
)

ax.grid(
    True,
    alpha=0.15
)


# ===============================================================
# 3. ESTADO DEL SISTEMA
# ===============================================================

campo_intensidad = E0_INICIAL

jaula_cerrada = True

mostrar_cargas = True

mostrar_lineas = True

mostrar_campo_interior = False

fase_animacion = 0.0


# ===============================================================
# 4. GEOMETRÍA DE LA JAULA
# ===============================================================

x_izq = CX - ANCHO_JAULA / 2
x_der = CX + ANCHO_JAULA / 2

y_inf = CY - ALTO_JAULA / 2
y_sup = CY + ALTO_JAULA / 2


# ===============================================================
# 5. FUNCIONES FÍSICAS
# ===============================================================

def dentro_de_jaula(x, y):
    """
    Determina si un punto se encuentra dentro de la cavidad.
    """

    return (
        (x > x_izq + ESPESOR_JAULA) &
        (x < x_der - ESPESOR_JAULA) &
        (y > y_inf + ESPESOR_JAULA) &
        (y < y_sup - ESPESOR_JAULA)
    )


def campo_externo(x, y):
    """
    Campo eléctrico externo uniforme.

    El campo apunta inicialmente en dirección +x.

            E = (E0, 0)

    """

    Ex = np.ones_like(x) * campo_intensidad
    Ey = np.zeros_like(y)

    return Ex, Ey


def campo_fisico(x, y):
    """
    Campo eléctrico total idealizado.

    Exterior:
        E = E0

    Interior:
        E ≈ 0

    Esto representa el blindaje electrostático ideal
    proporcionado por una jaula conductora cerrada.
    """

    Ex, Ey = campo_externo(x, y)

    if jaula_cerrada:

        interior = dentro_de_jaula(x, y)

        Ex = np.where(interior, 0.0, Ex)
        Ey = np.where(interior, 0.0, Ey)

    return Ex, Ey


# ===============================================================
# 6. CARGAS INDUCIDAS
# ===============================================================

def generar_cargas_superficie():
    """
    Distribuye cargas inducidas sobre la superficie.

    Para un campo externo dirigido hacia +x:

        lado izquierdo  -> carga negativa
        lado derecho     -> carga positiva

    La distribución real depende de la geometría y del campo.
    Esta es una representación educativa simplificada.
    """

    cargas = []

    # -----------------------------------------------------------
    # Lado izquierdo
    # -----------------------------------------------------------

    ys = np.linspace(
        y_inf + 0.35,
        y_sup - 0.35,
        N_CARGAS // 2
    )

    for y in ys:

        x = x_izq

        cargas.append(
            (x, y, -1)
        )

    # -----------------------------------------------------------
    # Lado derecho
    # -----------------------------------------------------------

    ys = np.linspace(
        y_inf + 0.35,
        y_sup - 0.35,
        N_CARGAS // 2
    )

    for y in ys:

        x = x_der

        cargas.append(
            (x, y, +1)
        )

    return cargas


cargas_superficie = generar_cargas_superficie()


# ===============================================================
# 7. DIBUJAR CAMPO ELÉCTRICO
# ===============================================================

def crear_malla():

    x = np.linspace(
        -LIMITE_X,
        LIMITE_X,
        45
    )

    y = np.linspace(
        -LIMITE_Y,
        LIMITE_Y,
        28
    )

    X, Y = np.meshgrid(x, y)

    return X, Y


X, Y = crear_malla()


# ===============================================================
# 8. DIBUJAR VECTORES DEL CAMPO
# ===============================================================

def dibujar_campo():

    Ex, Ey = campo_fisico(X, Y)

    magnitud = np.sqrt(
        Ex**2 + Ey**2
    )

    # Evitamos división por cero
    magnitud_segura = np.where(
        magnitud == 0,
        1,
        magnitud
    )

    # -----------------------------------------------------------
    # Quiver
    # -----------------------------------------------------------

    ax.quiver(
        X,
        Y,
        Ex / magnitud_segura,
        Ey / magnitud_segura,
        magnitud,
        cmap="plasma",
        scale=18,
        width=0.0025,
        alpha=0.75,
        pivot="mid"
    )


# ===============================================================
# 9. LÍNEAS DE CAMPO
# ===============================================================

def dibujar_lineas_campo():

    if not mostrar_lineas:
        return

    # Campo uniforme exterior
    x = np.linspace(
        -LIMITE_X,
        LIMITE_X,
        25
    )

    y = np.linspace(
        -LIMITE_Y + 0.3,
        LIMITE_Y - 0.3,
        17
    )

    for yy in y:

        if jaula_cerrada:

            # Segmento izquierdo
            ax.plot(
                [x[0], x_izq - 0.15],
                [yy, yy],
                linewidth=1.2,
                alpha=0.35
            )

            # Segmento derecho
            ax.plot(
                [x_der + 0.15, x[-1]],
                [yy, yy],
                linewidth=1.2,
                alpha=0.35
            )

        else:

            ax.plot(
                x,
                np.ones_like(x) * yy,
                linewidth=1.2,
                alpha=0.35
            )


# ===============================================================
# 10. DIBUJAR JAULA
# ===============================================================

def dibujar_jaula():

    if jaula_cerrada:

        # -------------------------------------------------------
        # Cuerpo conductor
        # -------------------------------------------------------

        rect_exterior = Rectangle(
            (
                x_izq,
                y_inf
            ),
            ANCHO_JAULA,
            ALTO_JAULA,
            fill=False,
            linewidth=9,
            zorder=10
        )

        ax.add_patch(rect_exterior)

        # -------------------------------------------------------
        # Línea interna
        # -------------------------------------------------------

        rect_interior = Rectangle(
            (
                x_izq + ESPESOR_JAULA,
                y_inf + ESPESOR_JAULA
            ),
            ANCHO_JAULA - 2 * ESPESOR_JAULA,
            ALTO_JAULA - 2 * ESPESOR_JAULA,
            fill=False,
            linewidth=2,
            linestyle="--",
            alpha=0.5,
            zorder=11
        )

        ax.add_patch(rect_interior)

        # -------------------------------------------------------
        # Región protegida
        # -------------------------------------------------------

        ax.fill_between(
            [
                x_izq + ESPESOR_JAULA,
                x_der - ESPESOR_JAULA
            ],
            y_inf + ESPESOR_JAULA,
            y_sup - ESPESOR_JAULA,
            alpha=0.08,
            zorder=1
        )

        # -------------------------------------------------------
        # Etiqueta
        # -------------------------------------------------------

        ax.text(
            CX,
            y_sup + 0.55,
            "CONDUCTOR METÁLICO",
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold"
        )

        ax.text(
            CX,
            CY,
            "REGIÓN\nPROTEGIDA",
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            alpha=0.75
        )

    else:

        # Jaula abierta visualmente
        rect = Rectangle(
            (
                x_izq,
                y_inf
            ),
            ANCHO_JAULA,
            ALTO_JAULA,
            fill=False,
            linewidth=7,
            linestyle="--",
            alpha=0.5
        )

        ax.add_patch(rect)

        ax.text(
            CX,
            y_sup + 0.55,
            "JAULA ABIERTA",
            ha="center",
            fontsize=12,
            fontweight="bold"
        )


# ===============================================================
# 11. DIBUJAR CARGAS INDUCIDAS
# ===============================================================

def dibujar_cargas():

    if not mostrar_cargas:
        return

    if not jaula_cerrada:
        return

    for x, y, signo in cargas_superficie:

        if signo > 0:

            etiqueta = "+"

        else:

            etiqueta = "−"

        circ = Circle(
            (
                x,
                y
            ),
            RADIO_CARGA,
            alpha=0.9,
            zorder=20
        )

        ax.add_patch(circ)

        ax.text(
            x,
            y,
            etiqueta,
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            zorder=21
        )


# ===============================================================
# 12. CARGA DE PRUEBA INTERIOR
# ===============================================================

def dibujar_carga_prueba():

    # Posición fija dentro de la cavidad
    x = CX
    y = CY - 0.2

    # Partícula
    carga = Circle(
        (
            x,
            y
        ),
        0.20,
        alpha=0.9,
        zorder=30
    )

    ax.add_patch(carga)

    ax.text(
        x,
        y,
        "+",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        zorder=31
    )

    # -----------------------------------------------------------
    # Vector E interior
    # -----------------------------------------------------------

    if mostrar_campo_interior:

        ax.arrow(
            x,
            y,
            1.3,
            0,
            head_width=0.18,
            head_length=0.25,
            linewidth=2
        )

        ax.text(
            x + 0.7,
            y + 0.35,
            "E ≠ 0",
            fontsize=11,
            fontweight="bold"
        )

    else:

        ax.text(
            x,
            y - 0.65,
            "E ≈ 0",
            ha="center",
            fontsize=13,
            fontweight="bold"
        )


# ===============================================================
# 13. FUENTE EXTERNA
# ===============================================================

def dibujar_fuente():

    # -----------------------------------------------------------
    # Flecha indicando el campo externo
    # -----------------------------------------------------------

    ax.annotate(
        "CAMPO ELÉCTRICO EXTERNO",
        xy=(-8.5, 5.3),
        xytext=(-10.5, 5.3),
        arrowprops=dict(
            arrowstyle="->",
            linewidth=2
        ),
        fontsize=11,
        fontweight="bold"
    )

    # -----------------------------------------------------------
    # Texto de dirección
    # -----------------------------------------------------------

    ax.text(
        -9.5,
        4.5,
        r"$\vec{E}_{ext}$",
        fontsize=18,
        fontweight="bold"
    )


# ===============================================================
# 14. INFORMACIÓN FÍSICA
# ===============================================================

def dibujar_panel_informacion():

    texto = (
        "PRINCIPIO FÍSICO\n"
        "────────────────────────\n\n"
        "En equilibrio electrostático:\n\n"
        "E = 0  en el interior\n\n"
        "V = constante en el conductor\n\n"
        "Eₜ = 0 en la superficie\n\n"
        "Las cargas libres se redistribuyen\n"
        "sobre la superficie del conductor.\n\n"
        "Campo externo:\n"
        f"E₀ = {campo_intensidad:.2f} unidades\n\n"
        "Campo interior ideal:\n"
        "Eint ≈ 0\n\n"
        "────────────────────────\n"
        "Blindaje electrostático"
    )

    ax.text(
        1.03,
        0.50,
        texto,
        transform=ax.transAxes,
        fontsize=11,
        va="center",
        ha="left",
        bbox=dict(
            boxstyle="round,pad=0.7",
            alpha=0.12
        )
    )


# ===============================================================
# 15. LEYENDA
# ===============================================================

def dibujar_leyenda():

    ax.text(
        -11.5,
        -6.3,
        "→ Dirección del campo eléctrico",
        fontsize=10
    )

    ax.text(
        -11.5,
        -6.7,
        "−  Carga inducida negativa",
        fontsize=10
    )

    ax.text(
        3.5,
        -6.3,
        "+  Carga inducida positiva",
        fontsize=10
    )

    ax.text(
        3.5,
        -6.7,
        "Interior: E ≈ 0",
        fontsize=10,
        fontweight="bold"
    )


# ===============================================================
# 16. REDIBUJAR TODO
# ===============================================================

def redibujar():

    ax.clear()

    ax.set_xlim(
        -LIMITE_X,
        LIMITE_X
    )

    ax.set_ylim(
        -LIMITE_Y,
        LIMITE_Y
    )

    ax.set_aspect("equal")

    ax.set_xlabel(
        "x",
        fontsize=12
    )

    ax.set_ylabel(
        "y",
        fontsize=12
    )

    ax.set_title(
        "JAULA DE FARADAY — BLINDAJE ELECTROSTÁTICO",
        fontsize=18,
        fontweight="bold",
        pad=15
    )

    ax.grid(
        True,
        alpha=0.15
    )

    dibujar_lineas_campo()

    dibujar_campo()

    dibujar_jaula()

    dibujar_cargas()

    dibujar_carga_prueba()

    dibujar_fuente()

    dibujar_leyenda()

    dibujar_panel_informacion()


# ===============================================================
# 17. SLIDER DE INTENSIDAD DEL CAMPO
# ===============================================================

ax_slider = plt.axes(
    [0.18, 0.07, 0.45, 0.035]
)

slider_campo = Slider(
    ax_slider,
    "Intensidad E₀",
    0.0,
    5.0,
    valinit=E0_INICIAL,
    valstep=0.05
)


def actualizar_campo(valor):

    global campo_intensidad

    campo_intensidad = slider_campo.val

    redibujar()

    fig.canvas.draw_idle()


slider_campo.on_changed(
    actualizar_campo
)


# ===============================================================
# 18. BOTÓN ABRIR/CERRAR JAULA
# ===============================================================

ax_boton_jaula = plt.axes(
    [0.67, 0.07, 0.10, 0.045]
)

boton_jaula = Button(
    ax_boton_jaula,
    "Abrir/Cerrar"
)


def cambiar_jaula(event):

    global jaula_cerrada

    jaula_cerrada = not jaula_cerrada

    redibujar()

    fig.canvas.draw_idle()


boton_jaula.on_clicked(
    cambiar_jaula
)


# ===============================================================
# 19. BOTÓN CARGAS
# ===============================================================

ax_boton_cargas = plt.axes(
    [0.54, 0.01, 0.10, 0.045]
)

boton_cargas = Button(
    ax_boton_cargas,
    "Cargas"
)


def cambiar_cargas(event):

    global mostrar_cargas

    mostrar_cargas = not mostrar_cargas

    redibujar()

    fig.canvas.draw_idle()


boton_cargas.on_clicked(
    cambiar_cargas
)


# ===============================================================
# 20. BOTÓN LÍNEAS DE CAMPO
# ===============================================================

ax_boton_lineas = plt.axes(
    [0.42, 0.01, 0.10, 0.045]
)

boton_lineas = Button(
    ax_boton_lineas,
    "Líneas E"
)


def cambiar_lineas(event):

    global mostrar_lineas

    mostrar_lineas = not mostrar_lineas

    redibujar()

    fig.canvas.draw_idle()


boton_lineas.on_clicked(
    cambiar_lineas
)


# ===============================================================
# 21. BOTÓN CAMPO INTERIOR
# ===============================================================

ax_boton_interior = plt.axes(
    [0.30, 0.01, 0.10, 0.045]
)

boton_interior = Button(
    ax_boton_interior,
    "Campo interior"
)


def cambiar_campo_interior(event):

    global mostrar_campo_interior

    mostrar_campo_interior = not mostrar_campo_interior

    redibujar()

    fig.canvas.draw_idle()


boton_interior.on_clicked(
    cambiar_campo_interior
)


# ===============================================================
# 22. ANIMACIÓN
# ===============================================================

def animar(frame):

    global fase_animacion

    fase_animacion += 0.08

    # La animación modifica ligeramente la posición visual
    # de las líneas de campo para representar flujo dinámico.

    redibujar()

    return []


# ===============================================================
# 23. INICIALIZACIÓN
# ===============================================================

redibujar()


# ===============================================================
# 24. EJECUTAR ANIMACIÓN
# ===============================================================

animacion = FuncAnimation(
    fig,
    animar,
    frames=300,
    interval=70,
    blit=False,
    cache_frame_data=False
)


# ===============================================================
# 25. MOSTRAR
# ===============================================================

plt.show()