# ================================================================
# GRÁFICA 3
# DISTRIBUCIÓN CUALITATIVA DE CARGAS EN EL ELECTRÓFORO DE VOLTA
# ================================================================
#
# SECUENCIA DEL EXPERIMENTO ORIGINAL:
#
# a) Frotar paño con telgopor
# b) Alejar el paño del telgopor
# c) Acercar el electróforo de Volta al telgopor
# d) Poner en contacto el electróforo de Volta con el telgopor
# e) Tocar el electróforo de Volta
# f) Alejar la mano del electróforo de Volta
# g) Alejar el electróforo de Volta del telgopor
# h) Analizar cargas electrostáticas
#
# ================================================================
#
# HIPÓTESIS FÍSICA DEL MODELO:
#
# El telgopor queda NEGATIVAMENTE cargado por frotamiento.
# El paño queda POSITIVAMENTE cargado.
#
# El electróforo comienza NEUTRO.
#
# Al aproximar el telgopor negativo:
#
#       electrones del conductor -> se alejan
#
# por lo tanto:
#
#       cara cercana -> positiva
#       cara alejada -> negativa
#
# Al conectar el electróforo a tierra:
#
#       electrones -> abandonan el conductor
#
# Al retirar primero la conexión a tierra y después el telgopor:
#
#       queda una carga neta positiva
#       que finalmente se redistribuye.
#
# ================================================================
#
# IMPORTANTE:
#
# Los números NO representan Coulombs.
# Son valores NORMALIZADOS y CUALITATIVOS.
#
# ================================================================


# ================================================================
# 1. LIBRERÍAS
# ================================================================

import numpy as np
import matplotlib.pyplot as plt


# ================================================================
# 2. ETAPAS EXPERIMENTALES
# ================================================================

etapas = [
    "a) Frotar paño\ncon telgopor",
    "b) Alejar el paño\ndel telgopor",
    "c) Acercar el electróforo\nal telgopor",
    "d) Poner en contacto\ncon el telgopor",
    "e) Tocar el\nelectróforo",
    "f) Alejar la mano\ndel electróforo",
    "g) Alejar el electróforo\ndel telgopor",
    "h) Analizar cargas\nelectrostáticas"
]

t = np.arange(len(etapas))


# ================================================================
# 3. CARGA DEL TELGOPOR
# ================================================================
#
# En a) se produce la electrización por frotamiento.
#
# Después de la etapa a:
#
#       telgopor -> negativo
#
# El telgopor conserva su carga durante el resto del proceso.
#
# ================================================================

carga_telgopor = np.array([
    -1.0,   # a) queda cargado negativamente
    -1.0,   # b)
    -1.0,   # c)
    -1.0,   # d)
    -1.0,   # e)
    -1.0,   # f)
    -1.0,   # g)
    -1.0    # h)
])


# ================================================================
# 4. CARGA DEL PAÑO
# ================================================================
#
# El paño pierde electrones en el proceso idealizado.
#
# Por lo tanto:
#
#       paño -> positivo
#
# ================================================================

carga_pano = np.array([
     1.0,   # a) queda positivo
     1.0,   # b)
     1.0,   # c)
     1.0,   # d)
     1.0,   # e)
     1.0,   # f)
     1.0,   # g)
     1.0    # h)
])


# ================================================================
# 5. CARGA / DISTRIBUCIÓN DE LA CARA CERCANA
#    DEL ELECTRÓFORO
# ================================================================
#
# a:
#     electróforo neutro
#
# b:
#     electróforo todavía neutro
#
# c:
#     aparece la polarización.
#
# d:
#     el telgopor está en contacto físico con el electróforo,
#     pero al ser un aislante no asumimos transferencia libre
#     de electrones entre ambos.
#
# e:
#     conexión a tierra.
#     Los electrones son repelidos por el telgopor negativo
#     y salen hacia tierra.
#
# f:
#     se retira la mano.
#     queda carga neta positiva.
#
# g:
#     se aleja el telgopor.
#     desaparece la polarización externa.
#
# h:
#     carga positiva distribuida.
#
# ================================================================

cara_cercana = np.array([
    0.00,   # a) electróforo neutro
    0.00,   # b) electróforo neutro
    1.00,   # c) polarización
    1.05,   # d) polarización mantenida
    1.20,   # e) conexión a tierra
    0.90,   # f) queda carga neta positiva
    0.50,   # g) redistribución
    0.50    # h) distribución final
])


# ================================================================
# 6. CARGA / DISTRIBUCIÓN DE LA CARA ALEJADA
# ================================================================
#
# a:
#     electróforo neutro
#
# b:
#     electróforo neutro
#
# c:
#     acumulación relativa de electrones -> negativo
#
# d:
#     la polarización continúa
#
# e:
#     al conectar a tierra salen electrones.
#     desaparece el exceso negativo.
#
# f:
#     el conductor queda netamente positivo.
#
# g:
#     desaparece la polarización y la carga positiva
#     se redistribuye.
#
# h:
#     ambas regiones alcanzan un valor semejante.
#
# ================================================================

cara_alejada = np.array([
    0.00,    # a) electróforo neutro
    0.00,    # b) electróforo neutro
   -1.00,    # c) polarización
   -0.90,    # d) polarización mantenida
    0.05,    # e) desaparece el exceso negativo
    0.25,    # f) carga neta positiva
    0.50,    # g) redistribución
    0.50     # h) distribución final
])


# ================================================================
# 7. CREAR FIGURA
# ================================================================

fig, ax = plt.subplots(
    figsize=(18, 9)
)


# ================================================================
# 8. CURVA DEL TELGOPOR
# ================================================================

ax.plot(
    t,
    carga_telgopor,
    marker='o',
    markersize=8,
    linewidth=2.8,
    label='Telgopor'
)


# ================================================================
# 9. CURVA DEL PAÑO
# ================================================================

ax.plot(
    t,
    carga_pano,
    marker='s',
    markersize=8,
    linewidth=2.8,
    label='Paño'
)


# ================================================================
# 10. CARA CERCANA DEL ELECTRÓFORO
# ================================================================

ax.plot(
    t,
    cara_cercana,
    marker='^',
    markersize=8,
    linewidth=2.8,
    label='Electróforo: cara cercana'
)


# ================================================================
# 11. CARA ALEJADA DEL ELECTRÓFORO
# ================================================================

ax.plot(
    t,
    cara_alejada,
    marker='v',
    markersize=8,
    linewidth=2.8,
    label='Electróforo: cara alejada'
)


# ================================================================
# 12. REFERENCIA DE CARGA CERO
# ================================================================

ax.axhline(
    y=0,
    linewidth=1.4,
    linestyle='-'
)


# ================================================================
# 13. SEPARACIÓN VISUAL DE LAS ETAPAS
# ================================================================

for x in t:

    ax.axvline(
        x=x,
        linewidth=0.6,
        linestyle=':',
        alpha=0.30
    )


# ================================================================
# 14. EJE X
# ================================================================

ax.set_xticks(t)

ax.set_xticklabels(
    etapas,
    fontsize=9
)


# ================================================================
# 15. EJE Y
# ================================================================

ax.set_ylim(
    -1.30,
    1.50
)

ax.set_yticks([
    -1.0,
     0.0,
     1.0
])

ax.set_yticklabels([
    'Carga relativa negativa (−)',
    'Carga relativa nula (0)',
    'Carga relativa positiva (+)'
])


# ================================================================
# 16. ETIQUETA DEL EJE X
# ================================================================

ax.set_xlabel(
    'Etapa del procedimiento experimental',
    fontsize=12
)


# ================================================================
# 17. ETIQUETA DEL EJE Y
# ================================================================

ax.set_ylabel(
    'Distribución cualitativa de carga',
    fontsize=12
)


# ================================================================
# 18. TÍTULO
# ================================================================

ax.set_title(
    'Evolución cualitativa de las cargas en el electróforo de Volta',
    fontsize=15,
    fontweight='bold',
    pad=18
)


# ================================================================
# 19. ANOTACIÓN DE LA ETAPA A
# ================================================================

ax.annotate(
    'Frotamiento:\n'
    'el telgopor adquiere electrones\n'
    'y queda negativo.\n'
    'El paño queda positivo.',
    xy=(0, -1.0),
    xytext=(0.15, -0.58),
    arrowprops=dict(
        arrowstyle='->',
        linewidth=1.2
    ),
    fontsize=10
)


# ================================================================
# 20. ANOTACIÓN DE LA ETAPA B
# ================================================================

ax.annotate(
    'El paño se aleja.\n'
    'El electróforo todavía\n'
    'permanece neutro.',
    xy=(1, 0.0),
    xytext=(0.65, 0.65),
    arrowprops=dict(
        arrowstyle='->',
        linewidth=1.2
    ),
    fontsize=10
)


# ================================================================
# 21. ANOTACIÓN DE LA ETAPA C
# ================================================================

ax.annotate(
    'Polarización:\n'
    'los electrones del electróforo\n'
    'son repelidos.',
    xy=(2, 1.0),
    xytext=(1.45, 1.23),
    arrowprops=dict(
        arrowstyle='->',
        linewidth=1.2
    ),
    fontsize=10
)


# ================================================================
# 22. ANOTACIÓN DE LA ETAPA D
# ================================================================

ax.annotate(
    'Contacto con el telgopor:\n'
    'la polarización permanece\n'
    'mientras actúa el campo externo.',
    xy=(3, 1.05),
    xytext=(2.55, -0.55),
    arrowprops=dict(
        arrowstyle='->',
        linewidth=1.2
    ),
    fontsize=10
)


# ================================================================
# 23. ANOTACIÓN DE LA ETAPA E
# ================================================================

ax.annotate(
    'Conexión a tierra:\n'
    'los electrones son expulsados\n'
    'hacia la Tierra.',
    xy=(4, 1.20),
    xytext=(3.55, 0.45),
    arrowprops=dict(
        arrowstyle='->',
        linewidth=1.2
    ),
    fontsize=10
)


# ================================================================
# 24. ANOTACIÓN DE LA ETAPA F
# ================================================================

ax.annotate(
    'Se retira la mano:\n'
    'el electróforo queda aislado\n'
    'con carga neta positiva.',
    xy=(5, 0.90),
    xytext=(4.55, -0.62),
    arrowprops=dict(
        arrowstyle='->',
        linewidth=1.2
    ),
    fontsize=10
)


# ================================================================
# 25. ANOTACIÓN DE LA ETAPA G
# ================================================================

ax.annotate(
    'Se aleja el telgopor:\n'
    'desaparece la polarización,\n'
    'pero permanece la carga neta +.',
    xy=(6, 0.50),
    xytext=(5.35, 1.10),
    arrowprops=dict(
        arrowstyle='->',
        linewidth=1.2
    ),
    fontsize=10
)


# ================================================================
# 26. ANOTACIÓN DE LA ETAPA H
# ================================================================

ax.annotate(
    'Estado final:\n'
    'la carga positiva se\n'
    'redistribuye sobre el conductor.',
    xy=(7, 0.50),
    xytext=(6.35, -0.60),
    arrowprops=dict(
        arrowstyle='->',
        linewidth=1.2
    ),
    fontsize=10
)


# ================================================================
# 27. LEYENDA
# ================================================================

ax.legend(
    loc='upper left',
    fontsize=10,
    frameon=True
)


# ================================================================
# 28. CUADRÍCULA
# ================================================================

ax.grid(
    True,
    linestyle='--',
    linewidth=0.7,
    alpha=0.35
)


# ================================================================
# 29. BORDES
# ================================================================

for spine in ax.spines.values():
    spine.set_linewidth(1.1)


# ================================================================
# 30. AJUSTES DE TICKS
# ================================================================

ax.tick_params(
    axis='x',
    labelsize=9
)

ax.tick_params(
    axis='y',
    labelsize=10
)


# ================================================================
# 31. AJUSTE FINAL
# ================================================================

plt.tight_layout()


# ================================================================
# 32. GUARDAR IMAGEN
# ================================================================

plt.savefig(
    'grafica_3_electroforo_corregida_fisicamente.png',
    dpi=300,
    bbox_inches='tight'
)


# ================================================================
# 33. MOSTRAR
# ================================================================

plt.show()