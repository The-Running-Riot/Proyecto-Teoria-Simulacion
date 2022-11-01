from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.window import Window
import matplotlib.pyplot as plt
from kivy.uix.boxlayout import BoxLayout
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

import random
import math
import simpy
import time
import numpy as np

# CONSTANTES Y VARIABLES
MILISECONDS = int(round(time.time()*1000))
SEMILLA = MILISECONDS
EMPLEADOS_VENTANILLA = 2  # Agregar Valor en interfaz
TIEMPO_DE_ATENCION_MIN = 15
TIEMPO_DE_ATENCION_MAX = 20
TIEMPO_LLEGADAS = 20  # Promedio de Clientes por minuto
TIEMPO_SIMULACION = 480
PASAJEROS_BUS_MAX = 20  # Agregar Valor en interfaz

TIEMPO_ESPERA_TOTAL = 0.0
DURACION_SERVICIO_TOTAL = 0.0
TIEMPO_FINALIZACION = 0.0
PASAJEROS = 0

DIAS = 7
DIAS_SEMANA = ["LUNES", "MARTES", "MIERCOLES",
               "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
DESTINO = ["NORTE", "OCCIDENTE", "SUR"]
SELECCION_DESTINO = []
CONTEO_PASAJEROS = []
CONTEO_DIAS = []

TIEMPO_ESPERA = []

PROM_COLA = []
PROM_TIEMPO_ESPERA = []
PROM_INSTALACIONES = []

INDICADORES = []
COLOR = ['yellow', 'cyan', 'blue']


def crearenv():
    env = simpy.Environment()  # Crea el objeto entorno de simulacion
    return env

# PROCEDIMIENTO


def atender(env, cliente, DatosAtencionMax, DatosAtencionMin):
    global DURACION_SERVICIO_TOTAL
    R = random.random()  # Obtencion de numero aleatorio y guardado en R
    tiempo = DatosAtencionMax - DatosAtencionMin
    tiempo_atencion = DatosAtencionMin + (tiempo*R)
    yield env.timeout(tiempo_atencion)
    print(" \o/ Transaccion de ticket completa por %s en %.2f minutos" %
          (cliente, tiempo_atencion))
    DURACION_SERVICIO_TOTAL = DURACION_SERVICIO_TOTAL + tiempo_atencion


def cliente(env, nombre, personal, DatosAtencionMax, DatosAtencionMin):
    global TIEMPO_ESPERA_TOTAL
    global TIEMPO_FINALIZACION
    llega = env.now  # Guarda el minuto de llegada

    # Obtencion aleatoria de una de las 3 rutas del bus
    bus = random.randint(1, 3)

    print("---> %s llego  en el minuto %.2f" % (nombre, llega))

    with personal.request() as request:  # Espera turno
        yield request
        pasa = env.now  # Guarda el minuto en que es atendido
        espera = pasa - llega  # Calcula el tiempo que espero
        TIEMPO_ESPERA.append(espera)
        TIEMPO_ESPERA_TOTAL = TIEMPO_ESPERA_TOTAL + espera

        print("**** %s pasa a Ventanilla en minuto %.2f habiendo esperado %.2f" %
              (nombre, pasa, espera))
        # Invoca el proceso atender
        yield env.process(atender(env, nombre, DatosAtencionMax, DatosAtencionMin))
        se_va = env.now  # Guarda el minuto en que dejo de atender
        SELECCION_DESTINO.append(bus)
        print("<--- %s dejo de ser atendido en el minuto %.2f y selecciono la ruta %s" %
              (nombre, se_va, bus))
        TIEMPO_FINALIZACION = se_va


def principal(env, personal, DatosAtencionMax, DatosAtencionMin):
    llegada = 0
    global PASAJEROS
    while True:
        R = random.random()
        llegada = -TIEMPO_LLEGADAS * math.log(R)  # Distribucion exponencial
        # Deja transcurrir un tiempo entre uno y otro
        yield env.timeout(llegada)
        PASAJEROS += 1
        CONTEO_PASAJEROS.append(PASAJEROS)
        env.process(cliente(env, 'Cliente %d' % PASAJEROS,
                    personal, DatosAtencionMax, DatosAtencionMin))


# SIMULACION
def empezarSimul(Datosempleados, DatosAtencionMax, DatosAtencionMin):
    print("------------------- SIMULACION BUSES ------------------")
    random.seed(SEMILLA)
    for i in range(DIAS):
        global PASAJEROS
        PASAJEROS = 0
        env = crearenv()
        random.seed(random.random()*100)  # Cualquier valor
        print(random.random())
        env = simpy.Environment()  # Crea el objeto entorno de simulacion
        # Crea los recursos (Empleados)
        personal = simpy.Resource(env, Datosempleados)
        # Invoca el proceso principal
        env.process(principal(env, personal,
                    DatosAtencionMax, DatosAtencionMin))
        env.run(until=TIEMPO_SIMULACION)  # Inicia la simulacion
        i += 1
        print("Dia : %s" % (i))
        # INDICADORES
        print("\n---------------------------------------------------------------------")
        print("\nIndicadores obtenidos: ")

        lpc = TIEMPO_ESPERA_TOTAL / TIEMPO_FINALIZACION
        print("\nLongitud promedio de la cola: %.2f" % lpc)
        tep = TIEMPO_ESPERA_TOTAL / PASAJEROS
        print("Tiempo de espera promedio = %.2f" % tep)
        upi = (DURACION_SERVICIO_TOTAL / TIEMPO_FINALIZACION) / \
            EMPLEADOS_VENTANILLA
        print("Uso promedio de la instalacion = %.2f" % upi)
        print("\n---------------------------------------------------------------------")

        NORTE = SELECCION_DESTINO.count(1)
        OCCIDENTE = SELECCION_DESTINO.count(2)
        SUR = SELECCION_DESTINO.count(3)

        CONTEO_DESTINO = [NORTE, OCCIDENTE, SUR]

        CONTEO_DIAS.append(PASAJEROS)

        PROM_COLA.append(lpc)
        PROM_TIEMPO_ESPERA.append(tep)
        PROM_INSTALACIONES.append(upi)

        print(CONTEO_DIAS)

    plot1 = plt.subplot(1, 3, 1)
    plot2 = plt.subplot(1, 3, 2)
    plot3 = plt.subplot(1, 3, 3)

    # GRAFICA  PROMEDIO DE VIAJE A ZONA

    plot1.bar(DESTINO, CONTEO_DESTINO)
    plot1.set_title('Promedio de personas que viajan a cada zona')
    # plt.show()

    # GRAFICA  PROMEDIO DE VIAJE A ZONA
    x_axis = np.arange(len(DIAS_SEMANA))
    plot2.bar(x_axis + 0.20, PROM_COLA, width=0.4,
              label='Promedio Cola', color='y')

    plot2.bar(x_axis + 0.20*2, PROM_TIEMPO_ESPERA, width=0.4,
              label='Promedio Tiempo Espera', color='g')

    plot2.bar(x_axis + 0.20*3, PROM_INSTALACIONES, width=0.4,
              label='Uso Promedio Instalaciones', color='b')
    plot2.legend()
    plot2.set_title('INDICADORES POR DIA')
    # plt.show()

    # GRAFICA  CONTEO DE PERSONAS POR DIA
    plot3.bar(DIAS_SEMANA, CONTEO_DIAS)
    plot3.set_title('Personas por dia')
    # plt.show()

    plt.tight_layout()


class KivyApp(App):
    def build(self):
        self.title = "Simulador de Buses"
        Window.size = (1000, 800)
        Window.clearcolor = ("#1e81b0")
        pass
        layout1 = GridLayout(cols=2, padding=20,
                             spacing=10, row_force_default=True, row_default_height=200)
        layout = GridLayout(cols=4, rows=2, padding=10,
                            spacing=10,  row_force_default=True, row_default_height=30)
        layout2 = GridLayout(cols=3, rows=1, padding=10,
                             spacing=10)

        self.empleadosVen = TextInput(text='1')
        self.TiempoAtencionMax = TextInput(text='1')
        self.TiempoAtencionMin = TextInput(text='1')

        box = BoxLayout(orientation='horizontal', size=(
            500, 500), size_hint=(5, 6))
        box = FigureCanvasKivyAgg(plt.gcf())
        Titulolbl = Label(
            text="Simulador de Centro de Autobuses", width=100, font_size='40sp', color=(1, 1, 1, 1))
        empleadosVenlbl = Label(
            text="Empleados por ventanilla", width=100, font_size='20sp')
        tiempoAtencionMaxlbl = Label(
            text="Tiempo de atencion Min",  width=100, font_size='20sp')
        tiempoAtencionMinlbl = Label(
            text="Tiempo de atencion Max", width=100, font_size='20sp')

        Simular = Button(text="Simular")
        Simular.bind(on_press=lambda x: empezarSimul(int(self.empleadosVen.text),
                                                     int(self.TiempoAtencionMax.text), int(self.TiempoAtencionMin.text)))

        layout1.add_widget(Titulolbl)
        layout1.add_widget(
            Image(source="logo.png", size_hint_x=0.4, allow_stretch=True))
        layout.add_widget(empleadosVenlbl)
        layout.add_widget(tiempoAtencionMaxlbl)
        layout.add_widget(tiempoAtencionMinlbl)
        layout.add_widget(Simular)
        layout.add_widget(self.empleadosVen)
        layout.add_widget(self.TiempoAtencionMax)
        layout.add_widget(self.TiempoAtencionMin)
        layout2.add_widget(box)

        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        main_layout.add_widget(layout1)
        main_layout.add_widget(layout)
        main_layout.add_widget(layout2)

        return main_layout


if __name__ == '__main__':
    app = KivyApp()
    app.run()
