import pygame
import random
import csv
import os
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np

pygame.init()

w, h = 800, 400
pantalla = pygame.display.set_mode((w, h))
pygame.display.set_caption("Juego: Disparo de Bala, Salto, Nave y Menú")

BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)

jugador = None
bala = None
fondo = None
nave = None
menu = None
ultimo_movimiento = "quieto"

modelo_decision_tree = None
modelo_red_neuronal = None
modelo_actual = None
scaler = None
modo_auto = False

salto = False
salto_altura = 15
gravedad = 1
en_suelo = True

pausa = False
fuente = pygame.font.SysFont('Arial', 24)
menu_activo = True
modo_auto = False

movimiento_horizontal = False
direccion_movimiento = None
contador_movimiento = 0
posicion_central = 30
velocidad_retorno = 2.5

datos_modelo = []
datos_csv = []

ruta_csv = "datos_juego.csv"

jugador_frames = [
    pygame.image.load('assets/sprites/mono_1.png'),
    pygame.image.load('assets/sprites/mono_2.png'),
    pygame.image.load('assets/sprites/mono_3.png'),
    pygame.image.load('assets/sprites/mono_4.png')
]

bala_img = pygame.image.load('assets/sprites/baguette.png')
fondo_img = pygame.image.load('assets/game/fondo.png')
nave_img = pygame.image.load('assets/game/panadero.png')
menu_img = pygame.image.load('assets/game/menu.png')

fondo_img = pygame.transform.scale(fondo_img, (w, h))

jugador = pygame.Rect(50, h - 100, 32, 48)
bala = pygame.Rect(w - 50, h - 90, 16, 16)
nave = pygame.Rect(w - 100, h - 100, 64, 64)
menu_rect = pygame.Rect(w // 2 - 135, h // 2 - 90, 270, 180)

current_frame = 0
frame_speed = 10
frame_count = 0

velocidad_bala = -10
bala_disparada = False

fondo_x1 = 0
fondo_x2 = w

def cargar_datos_entrenamiento():
    global scaler
    X = []
    y = []
    
    if not os.path.exists(ruta_csv):
        return None, None
    
    with open(ruta_csv, mode='r') as archivo:
        lector = csv.reader(archivo, delimiter=';')
        next(lector)
        for fila in lector:
            if len(fila) < 4:
                continue
                
            jugador_x = float(fila[0])
            jugador_y = float(fila[1])
            bala1_x = float(fila[2])
            bala1_y = float(fila[3])
            salto = int(fila[4])
            
            distancia_bala1 = abs(jugador_x - bala1_x)
            velocidad_bala1 = -5
            
            X.append([distancia_bala1, velocidad_bala1])
            
            if salto == 1:
                y.append(1)
            else:
                y.append(0)
    
    if not X:
        return None, None
    
    X = np.array(X)
    y = np.array(y)
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    return X, y

def entrenar_modelos():
    global modelo_decision_tree, modelo_red_neuronal
    
    X, y = cargar_datos_entrenamiento()
    if X is None or y is None:
        print("No hay datos suficientes para entrenar los modelos. Juega en modo manual primero.")
        return False
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    modelo_decision_tree = DecisionTreeClassifier(max_depth=5)
    modelo_decision_tree.fit(X_train, y_train)
    print(f"Decision Tree - Precisión: {modelo_decision_tree.score(X_test, y_test):.2f}")
    
    modelo_red_neuronal = MLPClassifier(hidden_layer_sizes=(10, 10), max_iter=1000)
    modelo_red_neuronal.fit(X_train, y_train)
    print(f"Red Neuronal - Precisión: {modelo_red_neuronal.score(X_test, y_test):.2f}")
    
    return True

def decidir_accion(modelo):
    global jugador, bala, scaler

    distancia_bala1 = abs(jugador.x - bala.x)
    velocidad_bala1 = velocidad_bala

    caracteristicas = np.array([[distancia_bala1, velocidad_bala1]])

    if scaler:
        caracteristicas = scaler.transform(caracteristicas)

    accion = modelo.predict(caracteristicas)[0]

    return accion

def disparar_bala():
    global bala_disparada, velocidad_bala
    if not bala_disparada:
        velocidad_bala = random.randint(-8, -3)
        bala_disparada = True

def reset_bala():
    global bala, bala_disparada
    bala.x = w - 50
    bala_disparada = False

def manejar_salto():
    global jugador, salto, salto_altura, gravedad, en_suelo
    if salto:
        jugador.y -= salto_altura
        salto_altura -= gravedad
        if jugador.y >= h - 100:
            jugador.y = h - 100
            salto = False
            salto_altura = 15
            en_suelo = True

def guardar_datos_csv():
    archivo_existe = os.path.exists(ruta_csv)
    with open(ruta_csv, mode='a', newline='') as archivo:
        escritor = csv.writer(archivo, delimiter=';')
        if not archivo_existe:
            escritor.writerow(['jugador_x', 'jugador_y', 'bala1_x', 'bala1_y', 'salto'])
        for fila in datos_csv:
            escritor.writerow(fila)
    datos_csv.clear()

def guardar_datos():
    if not modo_auto:
        distancia = abs(jugador.x - bala.x)
        salto_hecho = 1 if salto else 0
        datos_modelo.append((velocidad_bala, distancia, salto_hecho))
        datos_csv.append((jugador.x, jugador.y, bala.x, bala.y, salto_hecho))

def update():
    global bala, velocidad_bala, current_frame, frame_count, fondo_x1, fondo_x2
    global movimiento_horizontal, direccion_movimiento

    fondo_x1 -= 1
    fondo_x2 -= 1
    if fondo_x1 <= -w:
        fondo_x1 = w
    if fondo_x2 <= -w:
        fondo_x2 = w
    pantalla.blit(fondo_img, (fondo_x1, 0))
    pantalla.blit(fondo_img, (fondo_x2, 0))

    frame_count += 1
    if frame_count >= frame_speed:
        current_frame = (current_frame + 1) % len(jugador_frames)
        frame_count = 0
    pantalla.blit(jugador_frames[current_frame], (jugador.x, jugador.y))

    pantalla.blit(nave_img, (nave.x, nave.y))
    if bala_disparada:
        bala.x += velocidad_bala
    if bala.x < 0:
        reset_bala()
    pantalla.blit(bala_img, (bala.x, bala.y))

    if jugador.colliderect(bala):
        print("¡Colisión detectada!")
        reiniciar_juego()

def pausa_juego():
    global pausa
    pausa = not pausa
    if pausa:
        print("Juego pausado. Datos registrados hasta ahora:", datos_modelo)
    else:
        print("Juego reanudado.")

def mostrar_menu():
    global menu_activo, modo_auto
    pantalla.fill(NEGRO)
    texto = fuente.render("Presiona 'A' para Auto, 'M' para Manual, o 'Q' para Salir", True, BLANCO)
    pantalla.blit(texto, (w // 4, h // 2))
    pygame.display.flip()

    while menu_activo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_a:
                    mostrar_menu_automatico()
                    modo_auto = True
                    menu_activo = False
                elif evento.key == pygame.K_m:
                    modo_auto = False
                    menu_activo = False
                elif evento.key == pygame.K_q:
                    guardar_datos_csv()
                    pygame.quit()
                    exit()

def mostrar_menu_automatico():
    global modelo_actual, modo_auto
    
    if not entrenar_modelos():
        modo_auto = False
        return
    
    pantalla.fill(NEGRO)
    opciones = ["1 - Decision Trees", "2 - Redes neuronales", "3 - Volver"]
    for i, opcion in enumerate(opciones):
        texto = fuente.render(opcion, True, BLANCO)
        pantalla.blit(texto, (w // 4, h // 2 + i * 30))
    pygame.display.flip()
    
    esperando = True
    while esperando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_1: # --- INICIO SELECCIÓN: ÁRBOLES DE DECISIÓN ---
                    modelo_actual = modelo_decision_tree
                    esperando = False
                elif evento.key == pygame.K_2:
                    modelo_actual = modelo_red_neuronal
                    esperando = False
                elif evento.key == pygame.K_3:
                    modo_auto = False
                    esperando = False

def reiniciar_juego():
    global jugador, bala, nave
    global bala_disparada, salto, en_suelo, menu_activo
    jugador.x, jugador.y = 50, h - 100
    bala.x = w - 50
    nave.x, nave.y = w - 100, h - 100
    bala_disparada = False
    salto = False
    en_suelo = True
    guardar_datos_csv()
    print("Datos recopilados guardados en CSV.")
    menu_activo = True
    mostrar_menu()

def main():
    global salto, en_suelo, bala_disparada, ultimo_movimiento, modelo_actual, modo_auto
    global movimiento_horizontal, direccion_movimiento

    if 'modo_auto' not in globals():
        modo_auto = False

    reloj = pygame.time.Clock()
    mostrar_menu()
    correr = True

    while correr:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                guardar_datos_csv()
                correr = False
            if evento.type == pygame.KEYDOWN:
                tecla = evento.key

                if evento.key == pygame.K_SPACE and en_suelo and not pausa and not modo_auto:
                    salto = True
                    en_suelo = False
                if evento.key == pygame.K_p:
                    pausa_juego()
                if evento.key == pygame.K_q:
                    guardar_datos_csv()
                    pygame.quit()
                    exit()
                if evento.key == pygame.K_m:
                    modo_auto = False
                if evento.key == pygame.K_a:
                    mostrar_menu_automatico()

        if modo_auto and modelo_actual and not pausa:
            # --- INICIO LÓGICA DE PREDICCIÓN (Aquí actúa el Árbol de Decisión si fue seleccionado) ---
            accion = decidir_accion(modelo_actual)

            if accion == 1 and en_suelo:
                salto = True
                en_suelo = False
                ultimo_movimiento = "salto"
            else:
                ultimo_movimiento = "quieto"
            # --- FIN LÓGICA DE PREDICCIÓN ---

        if not pausa:
            if salto:
                manejar_salto()
            if not modo_auto:
                guardar_datos()
            if not bala_disparada:
                disparar_bala()
            update()

            if bala.x == 372 and bala.y == 310:
                pygame.draw.circle(pantalla, (255, 0, 0), (bala.x, bala.y), 5)

        pygame.display.flip()
        reloj.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()