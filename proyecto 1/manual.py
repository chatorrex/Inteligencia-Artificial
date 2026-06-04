import pygame
import random
import csv
import os

pygame.init()

w, h = 800, 400
pantalla = pygame.display.set_mode((w, h))
pygame.display.set_caption("Modo Manual: Recolección de Datos")

BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)

jugador = pygame.Rect(50, h - 100, 32, 48)
bala = pygame.Rect(w - 50, h - 90, 16, 16)
nave = pygame.Rect(w - 100, h - 100, 64, 64)

jugador_frames = [
    pygame.image.load('assets/sprites/mono_1.png'),
    pygame.image.load('assets/sprites/mono_2.png'),
    pygame.image.load('assets/sprites/mono_3.png'),
    pygame.image.load('assets/sprites/mono_4.png')
]
bala_img = pygame.image.load('assets/sprites/baguette.png')
fondo_img = pygame.image.load('assets/game/fondo.png')
nave_img = pygame.image.load('assets/game/panadero.png')
fondo_img = pygame.transform.scale(fondo_img, (w, h))

salto = False
salto_altura = 15
gravedad = 1
en_suelo = True
agachado = False
pausa = False
velocidad_bala = -12
bala_disparada = False
altura_bala_nivel = 0
fondo_x1, fondo_x2 = 0, w
current_frame, frame_speed, frame_count = 0, 10, 0

datos_csv = []
ruta_csv = "datos_juego.csv"

# Inicializar el archivo CSV: se abre en modo 'w' para borrar el contenido previo y escribir los encabezados.
with open(ruta_csv, mode='w', newline='') as archivo:
    escritor = csv.writer(archivo, delimiter=',')
    escritor.writerow(['velocidad_bala', 'distancia', 'altura_bala', 'salto', 'agachado'])

def disparar_bala():
    global bala_disparada, velocidad_bala, bala, altura_bala_nivel
    if not bala_disparada:
        velocidad_bala = random.randint(-12, -6)
        altura_bala_nivel = random.randint(0, 2)
        if altura_bala_nivel == 0: # Suelo
            bala.y = h - 90
        elif altura_bala_nivel == 1: # Cintura
            bala.y = h - 114
        else: # Cabeza
            bala.y = h - 130
        bala_disparada = True

def reset_bala():
    global bala, bala_disparada
    bala.x = w - 50
    bala_disparada = False

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

def guardar_datos_csv():
    with open(ruta_csv, mode='a', newline='') as archivo:
        escritor = csv.writer(archivo, delimiter=',')
        for fila in datos_csv:
            escritor.writerow(fila)
    datos_csv.clear()
 
def registrar_datos():
    if not bala_disparada:
        return
    distancia = abs(jugador.x - bala.x)
    salto_label = 1 if not en_suelo else 0
    agachado_label = 1 if agachado else 0
    datos_csv.append((velocidad_bala, distancia, altura_bala_nivel, salto_label, agachado_label))

def update():
    global current_frame, frame_count, fondo_x1, fondo_x2
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
        reset_bala()
    pantalla.blit(bala_img, (bala.x, bala.y))

    if jugador.colliderect(bala):
        print("¡Colisión! Guardando datos...")
        guardar_datos_csv()
        reiniciar_posiciones()

def reiniciar_posiciones():
    global salto, en_suelo, bala_disparada, agachado
    jugador.y = h - 100
    jugador.height = 48
    reset_bala()
    salto = False
    en_suelo = True
    agachado = False

def main():
    global salto, en_suelo, pausa, agachado
    reloj = pygame.time.Clock()
    correr = True

    while correr:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                guardar_datos_csv()
                correr = False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE and en_suelo and not pausa:
                    salto = True
                    en_suelo = False
                if evento.key == pygame.K_p:
                    pausa = not pausa
                if evento.key == pygame.K_q:
                    guardar_datos_csv()
                    correr = False

        if not pausa:
            keys = pygame.key.get_pressed()
            if en_suelo and keys[pygame.K_DOWN]:
                agachado = True
                jugador.height = 24
                jugador.y = h - 76
            else:
                agachado = False
                jugador.height = 48
                if not salto: jugador.y = h - 100

            disparar_bala()
            manejar_salto()
            registrar_datos()
            update()

        pygame.display.flip()
        reloj.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()