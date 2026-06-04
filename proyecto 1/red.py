import pygame
import random
import csv
import os
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

pygame.init()
w, h = 800, 400
pantalla = pygame.display.set_mode((w, h))
pygame.display.set_caption("Modo Auto: Red Neuronal MLP")

jugador = pygame.Rect(50, h - 100, 32, 48)
bala = pygame.Rect(w - 50, h - 90, 16, 16)
nave = pygame.Rect(w - 100, h - 100, 64, 64)

jugador_frames = [pygame.image.load(f'assets/sprites/mono_{i}.png') for i in range(1, 5)]
bala_img = pygame.image.load('assets/sprites/baguette.png')
fondo_img = pygame.transform.scale(pygame.image.load('assets/game/fondo.png'), (w, h))
nave_img = pygame.image.load('assets/game/panadero.png')

modelo = None
scaler = None
ruta_csv = "datos_juego.csv"

def cargar_y_entrenar():
    global modelo, scaler
    X, y = [], []
    if not os.path.exists(ruta_csv):
        print("No existe el archivo de datos. Juega primero en modo manual.")
        return False
    
    with open(ruta_csv, mode='r') as archivo:
        lector = csv.reader(archivo, delimiter=',')
        next(lector)
        for fila in lector:
            try:
                if len(fila) < 5: continue
                v_bala = float(fila[0])
                dist = float(fila[1])
                alt_bala = float(fila[2])
                s_flag = int(float(fila[3]))
                a_flag = int(float(fila[4]))
                X.append([v_bala, dist, alt_bala])
                if s_flag == 1: y.append(1)
                elif a_flag == 1: y.append(2)
                else: y.append(0)
            except (ValueError, IndexError):
                continue
    
    X = np.array(X)
    y = np.array(y)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    modelo = MLPClassifier(hidden_layer_sizes=(64, 32, 16), max_iter=500, early_stopping=True, random_state=42)
    modelo.fit(X, y)
    print("Modelo Red Neuronal (MLP) entrenado con éxito.")
    return True

def decidir_accion():
    if not bala_disparada: return 0
    distancia = abs(jugador.x - bala.x)
    caract = scaler.transform(np.array([[velocidad_bala, distancia, altura_bala_nivel]]))
    return modelo.predict(caract)[0]

salto = False
salto_altura = 15
gravedad = 1
en_suelo = True
agachado = False
velocidad_bala = -12
bala_disparada = False
altura_bala_nivel = 0
fondo_x1, fondo_x2 = 0, w
current_frame, frame_speed, frame_count = 0, 10, 0

def disparar_bala():
    global bala_disparada, velocidad_bala, bala, altura_bala_nivel
    if not bala_disparada:
        velocidad_bala = random.randint(-12, -6)
        altura_bala_nivel = random.randint(0, 2)
        if altura_bala_nivel == 0:
            bala.y = h - 90
        elif altura_bala_nivel == 1:
            bala.y = h - 114
        else:
            bala.y = h - 130
        bala_disparada = True

def manejar_salto():
    global jugador, salto, salto_altura, en_suelo
    if salto:
        jugador.y -= salto_altura
        salto_altura -= gravedad
        if jugador.y >= h - 100:
            jugador.y = h - 100
            salto = False
            salto_altura = 15
            en_suelo = True

def update():
    global current_frame, frame_count, fondo_x1, fondo_x2, bala_disparada
    fondo_x1 -= 1
    fondo_x2 -= 1
    if fondo_x1 <= -w: fondo_x1 = w
    if fondo_x2 <= -w: fondo_x2 = w
    pantalla.blit(fondo_img, (fondo_x1, 0))
    pantalla.blit(fondo_img, (fondo_x2, 0))
 
    frame_count += 1
    if frame_count >= frame_speed:
        current_frame = (current_frame + 1) % len(jugador_frames)
        frame_count = 0

    img = jugador_frames[current_frame]
    if agachado: img = pygame.transform.scale(img, (32, 24))
    pantalla.blit(img, (jugador.x, jugador.y))
    pantalla.blit(nave_img, (nave.x, nave.y))

    if bala_disparada:
        bala.x += velocidad_bala
    if bala.x < 0:
        bala.x = w - 50
        bala_disparada = False
    pantalla.blit(bala_img, (bala.x, bala.y))

    if jugador.colliderect(bala):
        reiniciar_juego()

def reiniciar_juego():
    global salto, en_suelo, bala_disparada, agachado
    jugador.y = h - 100
    jugador.height = 48
    bala.x = w - 50
    bala_disparada = False
    salto = False
    en_suelo = True
    agachado = False

def main():
    global salto, en_suelo, agachado
    if not cargar_y_entrenar(): return

    reloj = pygame.time.Clock()
    correr = True

    while correr:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: correr = False

        # IA decidiendo lógica multiclase
        accion = decidir_accion()
        if accion == 1 and en_suelo and not agachado:
            salto = True
            en_suelo = False
        elif accion == 2 and en_suelo and not salto:
            agachado = True
            jugador.height = 24
            jugador.y = h - 76
        elif not salto:
            agachado = False
            jugador.height = 48
            jugador.y = h - 100

        manejar_salto()
        disparar_bala()
        update()

        pygame.display.flip()
        reloj.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()