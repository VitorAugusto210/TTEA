import csv
import cv2
import mediapipe as mp
import numpy as np
import pygame
import time
from pygame import mixer
import datetime
import arquivo
import os 

pygame.init()

# --- CONFIGURAÇÃO DE JANELA (MÓVEL E CENTRALIZADA) ---
# 1. Centraliza a janela no monitor
os.environ['SDL_VIDEO_CENTERED'] = '1'

# 2. Descobre o tamanho do seu monitor e usa 90% dele
info_tela = pygame.display.Info()
LARGURA = int(info_tela.current_w * 0.90)
ALTURA = int(info_tela.current_h * 0.90)
# -----------------------------------------------------

#CONFIGURAÇÃO INICIAL

azul = 0, 0, 255
verde = 0, 255, 0
vermelho = 255, 0, 0
amarelo = 255, 255, 0
branco = 255, 255, 255
preto = 0, 0, 0
font = pygame.font.SysFont('Sans', 30)

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pontos_calibracao = np.zeros((4, 2), int)
contador = 4 
gameExit = False
figura_selecionada = False 
hud_switch = True
som_switch = True

# Leitura do Jogador
try:
    jogador_nome = arquivo.get_Player()
    jogador_config = 'Jogadores/' + jogador_nome + '_RepeTEA_config.csv'
    pontos_calibracao_repetea = arquivo.lerCalibracao()
except:
    jogador_nome = "Teste"
    jogador_config = ""
    pontos_calibracao_repetea = []

# Leitura da Configuração (Cores, Sons, Câmera)
# Nota: Removemos a leitura de LARGURA/ALTURA daqui para usar a automática calculada acima
try:
    with open(jogador_config, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader) # Pula header
        linha = next(reader)        
        
        # Ignoramos a resolução do arquivo para usar a da tela automática
        # LARGURA = int(linha[13]) 
        # ALTURA = int(linha[14])
        
        # Tela de controle (webcam)
        LARGURA_CAM = int(linha[15]) 
        ALTURA_CAM = int(linha[16])
        
        paleta_cores = str(linha[17])
        paleta_sons = str(linha[18])
except:
    print("Erro na config. Usando padrões.")
    # Se der erro na leitura, mantemos a LARGURA/ALTURA de 90% calculada no início
    LARGURA_CAM, ALTURA_CAM = 640, 480
    paleta_cores = "padrao"
    paleta_sons = "padrao"

# Ajustar a calibração da câmera para a tela do projetor
relacao_w = LARGURA / LARGURA_CAM
relacao_h = ALTURA / ALTURA_CAM

# Inicializa Webcam
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW) # Tenta camera padrão

#CARREGAMENTO E AJUSTE DE IMAGENS

# Funçao para carregar
def carregar_imagem(nome):
    caminho = f'Assets/Repetea_Figuras/{paleta_cores}/{nome}'
    try:
        img = pygame.image.load(caminho)
        # Redimensiona para ocupar a tela inteira (LARGURA x ALTURA)
        img = pygame.transform.scale(img, (LARGURA, ALTURA))
        return img
    except Exception as e:
        print(f"Erro ao carregar imagem {nome}: {e}")
        # Cria um quadrado colorido se falhar
        surf = pygame.Surface((LARGURA, ALTURA))
        surf.fill(preto)
        return surf

# Carrega as imagens já ajustadas
img_base_vazia = carregar_imagem('silhueta_perto.png')
img_base_verde = carregar_imagem('base_com_pe_verde.png')
img_triangulo = carregar_imagem('triangulo_selecionado_perto.png')
img_retangulo = carregar_imagem('retangulo_selecionado_perto.png')
img_circulo = carregar_imagem('circulo_selecionado_perto.png')
img_quadrado = carregar_imagem('quadrado_selecionado_perto.png')

icone = pygame.image.load(f'Assets/Repetea_Figuras/{paleta_cores}/icone.png')

#SONS
mixer.init()
path_snd = f'Assets/Repetea_Sons/{paleta_sons}/'
try:
    snd_triangulo = mixer.Sound(path_snd + '1_triangulo.wav')
    snd_retangulo = mixer.Sound(path_snd + '2_retangulo.wav')
    snd_circulo = mixer.Sound(path_snd + '3_circulo.wav')
    snd_quadrado = mixer.Sound(path_snd + '4_quadrado.wav')
except:
    print("Erro ao carregar sons.")

#FUNÇÕES DE POSICIONAMENTO

def calcular_posicao_pe(landmarks):
    # Pega a média entre pé esquerdo e direito
    x = (landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].x + 
         landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x) / 2
    y = (landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].y + 
         landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y) / 2
    return x, y

def transformar_perspectiva(x_pose, y_pose):
    # Converte coordenadas normalizadas do MediaPipe para pixels da tela de controle
    p_cam = (int(x_pose * LARGURA_CAM), int(y_pose * ALTURA_CAM))
    
    # Aplica a calibração
    pts_calib = np.float32(pontos_calibracao_repetea)
    pts_tela = np.float32([[0, 0], [LARGURA_CAM, 0], [0, ALTURA_CAM], [LARGURA_CAM, ALTURA_CAM]])
    
    try:
        matrix = cv2.getPerspectiveTransform(pts_calib, pts_tela)
        
        # Matemática da perspectiva
        px = (matrix[0][0]*p_cam[0] + matrix[0][1]*p_cam[1] + matrix[0][2]) / \
             (matrix[2][0]*p_cam[0] + matrix[2][1]*p_cam[1] + matrix[2][2])
        py = (matrix[1][0]*p_cam[0] + matrix[1][1]*p_cam[1] + matrix[1][2]) / \
             (matrix[2][0]*p_cam[0] + matrix[2][1]*p_cam[1] + matrix[2][2])
             
        # Escala para o tamanho do Projetor
        return int(px * relacao_w), int(py * relacao_h)
    except:
        return 0, 0

def desenhar_hud(display):
    txt_jog = font.render(f'Jogador: {jogador_nome}', True, branco)
    txt_mod = font.render('Modo Livre', True, branco)
    display.blit(txt_jog, (LARGURA * 0.05, ALTURA * 0.9))
    display.blit(txt_mod, (LARGURA * 0.80, ALTURA * 0.9))

# LOOP DO JOGO

# 3. MUDANÇA AQUI: Adicionado pygame.RESIZABLE para permitir mover a janela
screen = pygame.display.set_mode((LARGURA, ALTURA), pygame.RESIZABLE)
pygame.display.set_caption('Beat & Hit')
pygame.display.set_icon(icone)

while not gameExit:
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while camera.isOpened():
            
            #Leitura da Câmera
            ret, frame = camera.read()
            if not ret: break
            frame = cv2.flip(frame, 1) 
            
            # Processamento MediaPipe
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_rgb.flags.writeable = False
            results = pose.process(img_rgb)
            
            # Visualização Debug (Tela pequena)
            img_debug = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(img_debug, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # Se tiver calibração, processa o jogo
                if len(pontos_calibracao_repetea) == 4:
                    
                    # 1. calcula pé
                    x_norm, y_norm = calcular_posicao_pe(results.pose_landmarks.landmark)
                    px, py = transformar_perspectiva(x_norm, y_norm)
                    
                    # 2. desenhar Fundo
                    screen.fill(branco)
                    screen.blit(img_base_vazia, (0, 0)) # Imagem já está esticada
                    
                    # 3. Verificar Colisões (USANDO PORCENTAGENS DA TELA)
                    # Isso garante que funciona em qualquer resolução
                    colidiu = False
                    
                    # Definição das zonas (baseado na proporção original 800x600)
                    # Triângulo (Esquerda Baixo): X < 22%, Y entre 50% e 66%
                    if (0 < px < LARGURA * 0.22) and (ALTURA * 0.50 < py < ALTURA * 0.66):
                        screen.blit(img_triangulo, (0, 0))
                        if not figura_selecionada and som_switch: snd_triangulo.play()
                        colidiu = True
                        
                    # Retângulo (Meio Esquerda Alto): X 22%-50%, Y 30%-50%
                    elif (LARGURA * 0.22 < px < LARGURA * 0.50) and (ALTURA * 0.30 < py < ALTURA * 0.50):
                        screen.blit(img_retangulo, (0, 0))
                        if not figura_selecionada and som_switch: snd_retangulo.play()
                        colidiu = True
                        
                    # Círculo (Meio Direita Alto): X 50%-78%, Y 30%-50%
                    elif (LARGURA * 0.50 < px < LARGURA * 0.78) and (ALTURA * 0.30 < py < ALTURA * 0.50):
                        screen.blit(img_circulo, (0, 0))
                        if not figura_selecionada and som_switch: snd_circulo.play()
                        colidiu = True
                        
                    # Quadrado (Direita Baixo): X > 78%, Y 50%-66%
                    elif (LARGURA * 0.78 < px < LARGURA) and (ALTURA * 0.50 < py < ALTURA * 0.66):
                        screen.blit(img_quadrado, (0, 0))
                        if not figura_selecionada and som_switch: snd_quadrado.play()
                        colidiu = True

                    # Lógica de Reset
                    if colidiu:
                        figura_selecionada = True
                    else:
                        figura_selecionada = False
                        screen.blit(img_base_verde, (0, 0)) # Mostra base livre

                    # Feedback Visual do Pé
                    pygame.draw.circle(screen, amarelo, (px, py), 15)
                    
                    if hud_switch: desenhar_hud(screen)
                    
                    pygame.display.update()
            
            # Mostra janela da câmera para debug
            cv2.imshow("Calibracao / Camera", img_debug)
            
            # Inputs
            for event in pygame.event.get():
                if event.type == pygame.QUIT: gameExit = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q: gameExit = True
                    if event.key == pygame.K_s: som_switch = not som_switch
                    if event.key == pygame.K_h: hud_switch = not hud_switch
            
            if cv2.waitKey(1) & 0xFF == ord('q') or gameExit:
                break
        
        if gameExit: break

cv2.destroyAllWindows()
pygame.quit()
camera.release()
exit()