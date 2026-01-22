import csv
import cv2
import mediapipe as mp
import numpy as np
import pygame
from pygame import mixer
import arquivo
import os
import random
import time

pygame.init()

# --- CONFIGURAÇÃO DE TELA (SEM BORDA) ---
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,0)

# Cores
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERDE = (0, 255, 0)
VERMELHO = (255, 0, 0)
AZUL_NEON = (0, 255, 255)

font = pygame.font.SysFont('Arial', 40)
font_score = pygame.font.SysFont('Arial', 60)

# Variáveis Globais
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
gameExit = False
hud_switch = True

#LEITURA DE CONFIGURAÇÃO
try:
    jogador_nome = arquivo.get_Player()
    jogador_config = 'Jogadores/' + jogador_nome + '_RepeTEA_config.csv'
    pontos_calibracao_repetea = arquivo.lerCalibracao()
    
    with open(jogador_config, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader) 
        linha = next(reader)
        LARGURA = int(linha[13]) 
        ALTURA = int(linha[14])
        LARGURA_CAM = int(linha[15])
        ALTURA_CAM = int(linha[16])
        paleta_sons = str(linha[18])
except:
    print("Usando padrão 800x600.")
    LARGURA, ALTURA = 800, 600
    LARGURA_CAM, ALTURA_CAM = 640, 480
    paleta_sons = "padrao"

relacao_w = LARGURA / LARGURA_CAM
relacao_h = ALTURA / ALTURA_CAM

# SONS
mixer.init()
try:
    path_snd = f'Assets/Repetea_Sons/{paleta_sons}/'    
    snd_batida = mixer.Sound(path_snd + '1_triangulo.wav') 
    snd_ponto = mixer.Sound(path_snd + '5_feliz.wav')
    snd_erro = mixer.Sound(path_snd + '6_triste.wav')
except:
    print("Erro sons.")

# Raquete
raquete_w = LARGURA * 0.20
raquete_h = 20
raquete_y = ALTURA - 50
raquete_x = (LARGURA / 2) - (raquete_w / 2)

#Bola
bola_tam = 20
bola_x = LARGURA / 2
bola_y = ALTURA / 2
bola_vel_x = 10
bola_vel_y = 10

score = 0
vidas = 3

# Inicializa Webcam
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW) 

# FUNÇÕES DE POSICIONAMENTO


def calcular_posicao_pe(landmarks):
    # Média dos pés
    x = (landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].x + 
         landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x) / 2
    y = (landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].y + 
         landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y) / 2
    return x, y

def transformar_perspectiva(x_pose, y_pose):
    p_cam = (int(x_pose * LARGURA_CAM), int(y_pose * ALTURA_CAM))
    pts_calib = np.float32(pontos_calibracao_repetea)
    pts_tela = np.float32([[0, 0], [LARGURA_CAM, 0], [0, ALTURA_CAM], [LARGURA_CAM, ALTURA_CAM]])
    try:
        matrix = cv2.getPerspectiveTransform(pts_calib, pts_tela)
        px = (matrix[0][0]*p_cam[0] + matrix[0][1]*p_cam[1] + matrix[0][2]) / \
             (matrix[2][0]*p_cam[0] + matrix[2][1]*p_cam[1] + matrix[2][2])
        # X ajustado para o Pong
        return int(px * relacao_w)
    except:
        return 0

def reset_bola():
    global bola_x, bola_y, bola_vel_y, bola_vel_x
    bola_x = LARGURA / 2
    bola_y = ALTURA / 3
    bola_vel_y = -10 # Começa subindo
    bola_vel_x = random.choice([-10, 10]) # Direção aleatória
    time.sleep(1)

# LOOP DO JOGO


screen = pygame.display.set_mode((LARGURA, ALTURA), pygame.NOFRAME) 
pygame.display.set_caption('Pong Humano')

clock = pygame.time.Clock()

while not gameExit:
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while camera.isOpened():
            
            # 1. Leitura e Visão Computacional
            ret, frame = camera.read()
            if not ret: break
            frame = cv2.flip(frame, 1) # Espelho
            
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_rgb.flags.writeable = False
            results = pose.process(img_rgb)
            img_debug = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            
            px_jogador = LARGURA / 2 # Padrão se não detectar

            if results.pose_landmarks and len(pontos_calibracao_repetea) == 4:
                mp_drawing.draw_landmarks(img_debug, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # Pega a posição do jogador
                x_norm, y_norm = calcular_posicao_pe(results.pose_landmarks.landmark)
                px_jogador = transformar_perspectiva(x_norm, y_norm)

            # 2. Lógica do Jogo (Física)
            
            # Atualiza posição da Raquete baseada no jogador
            # Centraliza a raquete no pé do jogador
            raquete_x = px_jogador - (raquete_w / 2)
            
            # Limites da raquete (não sair da tela)
            if raquete_x < 0: raquete_x = 0
            if raquete_x + raquete_w > LARGURA: raquete_x = LARGURA - raquete_w

            # Movimento da Bola
            bola_x += bola_vel_x
            bola_y += bola_vel_y

            # Colisão Paredes (Esquerda e Direita)
            if bola_x <= 0 or bola_x + bola_tam >= LARGURA:
                bola_vel_x *= -1 # Inverte direção horizontal
                
            # Colisão Teto
            if bola_y <= 0:
                bola_vel_y *= -1 # Inverte direção vertical
            
            # Colisão Raquete (A parte mais divertida!)
            # Cria retângulos invisíveis para checar colisão
            rect_bola = pygame.Rect(bola_x, bola_y, bola_tam, bola_tam)
            rect_raquete = pygame.Rect(raquete_x, raquete_y, raquete_w, raquete_h)
            
            if rect_bola.colliderect(rect_raquete) and bola_vel_y > 0:
                bola_vel_y *= -1 # Rebate para cima
                snd_batida.play()
                score += 10
                
                # Aumenta dificuldade a cada 50 pontos
                if score % 50 == 0:
                    bola_vel_x = bola_vel_x * 1.1
                    bola_vel_y = bola_vel_y * 1.1

            # Perdeu vida (Bola caiu no chão)
            if bola_y > ALTURA:
                snd_erro.play()
                vidas -= 1
                if vidas == 0:
                    # Game Over simples (reseta tudo)
                    vidas = 3
                    score = 0
                    bola_vel_x, bola_vel_y = 10, 10
                reset_bola()

            # 3. Desenho na Tela
            screen.fill(PRETO)
            
            # Desenha Raquete (Controlada pelo Jogador)
            pygame.draw.rect(screen, AZUL_NEON, (raquete_x, raquete_y, raquete_w, raquete_h))
            
            # Desenha Bola
            pygame.draw.ellipse(screen, VERDE, (bola_x, bola_y, bola_tam, bola_tam))
            
            # Desenha HUD (Placar)
            if hud_switch:
                txt_score = font_score.render(f'{score}', True, BRANCO)
                txt_vidas = font.render(f'Vidas: {vidas}', True, VERMELHO)
                screen.blit(txt_score, (LARGURA/2 - 20, 50))
                screen.blit(txt_vidas, (LARGURA - 200, 50))

            # Desenha linha de chão (zona de perigo)
            pygame.draw.line(screen, VERMELHO, (0, ALTURA-2), (LARGURA, ALTURA-2), 5)

            pygame.display.update()
            clock.tick(60) # Trava em 60 FPS para a bola não voar rápido demais
            
            # 4. Controle
            cv2.imshow("Calibracao / Camera", img_debug)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: gameExit = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q: gameExit = True
                    if event.key == pygame.K_r: reset_bola() # Reset manual
            
            if cv2.waitKey(1) & 0xFF == ord('q') or gameExit:
                break
        if gameExit: break

cv2.destroyAllWindows()
pygame.quit()
camera.release()
exit()