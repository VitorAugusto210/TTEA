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
import datetime

pygame.init()

# --- CONFIGURAÇÃO DE JANELA ---
os.environ['SDL_VIDEO_CENTERED'] = '1'
info_tela = pygame.display.Info()
LARGURA = int(info_tela.current_w * 0.90)
ALTURA = int(info_tela.current_h * 0.90)

# --- CORES ---
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
CINZA_ESCURO = (30, 30, 30)
CINZA_CLARO = (100, 100, 100)
VERDE = (0, 255, 0)
VERDE_CLARO = (100, 255, 100)
VERMELHO = (255, 0, 0)
VERMELHO_CLARO = (255, 100, 100)
AZUL = (0, 0, 255)
AZUL_NEON = (0, 255, 255)
AMARELO = (255, 255, 0)
ROXO = (128, 0, 128)

# Cores OpenCV
CV_VERDE = (0, 255, 0)
CV_AZUL = (255, 0, 0)

# --- FONTES ---
font_titulo = pygame.font.SysFont('Arial', 80, bold=True)
font_btn = pygame.font.SysFont('Arial', 30, bold=True)
font_placar = pygame.font.SysFont('Arial', 50)
font_info = pygame.font.SysFont('Arial', 30)
font_aviso = pygame.font.SysFont('Arial', 40, bold=True)

# --- GLOBAIS ---
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
gameExit = False
hud_switch = True
estado_jogo = "MENU" # Estados: MENU, JOGANDO, GAMEOVER

# Configuração Visual Padrão
tipo_piso = "ESCURO" 
COR_RAQUETE = AZUL_NEON
COR_BOLA = VERDE
COR_TEXTO = BRANCO

# --- LEITURA DE DADOS ---
try:
    jogador_nome = arquivo.get_Player()
    arquivo_dados_pong = f'Jogadores/{jogador_nome}_Pong_Dados.csv'
    jogador_config = f'Jogadores/{jogador_nome}_RepeTEA_config.csv'
    pontos_calibracao_repetea = arquivo.lerCalibracao()
    
    with open(jogador_config, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader) 
        linha = next(reader)
        LARGURA_CAM = int(linha[15])
        ALTURA_CAM = int(linha[16])
        paleta_sons = str(linha[18])
        
    if not os.path.exists(arquivo_dados_pong):
        with open(arquivo_dados_pong, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Data", "Hora", "Pontuacao", "Lado_Queda_Bola"])
except:
    jogador_nome = "Visitante"
    arquivo_dados_pong = "Jogadores/Visitante_Pong_Dados.csv"
    LARGURA_CAM, ALTURA_CAM = 640, 480
    paleta_sons = "padrao"
    pontos_calibracao_repetea = []

relacao_w = LARGURA / LARGURA_CAM
relacao_h = ALTURA / ALTURA_CAM

# --- SONS ---
mixer.init()
try:
    path_snd = f'Assets/Repetea_Sons/{paleta_sons}/'
    snd_batida = mixer.Sound(path_snd + '1_triangulo.wav') 
    snd_ponto = mixer.Sound(path_snd + '5_feliz.wav')
    snd_erro = mixer.Sound(path_snd + '6_triste.wav')
except:
    pass

# --- OBJETOS ---
raquete_w, raquete_h = LARGURA * 0.20, 20
raquete_y = ALTURA - 50 
raquete_x = (LARGURA / 2) - (raquete_w / 2)
bola_tam = 20
bola_x, bola_y = LARGURA / 2, ALTURA / 2

VELOCIDADE_INICIAL = 10 
bola_vel_x = VELOCIDADE_INICIAL  
bola_vel_y = VELOCIDADE_INICIAL  
score = 0
vidas = 3
px_jogador = LARGURA / 2 

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW) 

# --- FUNÇÕES ---

def definir_cores_piso(tipo):
    global COR_RAQUETE, COR_BOLA, COR_TEXTO, tipo_piso
    tipo_piso = tipo
    if tipo == "ESCURO":
        COR_RAQUETE = AZUL_NEON
        COR_BOLA = VERDE
        COR_TEXTO = BRANCO
    else:
        COR_RAQUETE = AZUL
        COR_BOLA = VERMELHO
        COR_TEXTO = AMARELO 

def desenhar_botao_estetico(texto, x, y, w, h, cor_base, cor_hover, mouse_pos, selecionado=False):
    rect = pygame.Rect(x, y, w, h)
    em_cima = rect.collidepoint(mouse_pos)
    
    # Sombra
    sombra_rect = pygame.Rect(x + 5, y + 5, w, h)
    pygame.draw.rect(screen, (20, 20, 20), sombra_rect, border_radius=15)

    # Cor
    if selecionado:
        cor_final = cor_hover
        borda_cor = BRANCO
        borda_tam = 3
    else:
        if em_cima:
            cor_final = cor_base
            borda_cor = cor_hover
            borda_tam = 2
        else:
            cor_final = CINZA_ESCURO
            borda_cor = cor_base
            borda_tam = 1

    # Desenho
    pygame.draw.rect(screen, cor_final, rect, border_radius=15)
    pygame.draw.rect(screen, borda_cor, rect, borda_tam, border_radius=15)
    
    # Texto
    txt_surf = font_btn.render(texto, True, BRANCO if not selecionado else PRETO)
    margem = 20
    if txt_surf.get_width() > (w - margem):
        escala = (w - margem) / txt_surf.get_width()
        novo_w = int(txt_surf.get_width() * escala)
        novo_h = int(txt_surf.get_height() * escala)
        txt_surf = pygame.transform.smoothscale(txt_surf, (novo_w, novo_h))

    txt_rect = txt_surf.get_rect(center=rect.center)
    screen.blit(txt_surf, txt_rect)
    return rect

def desenhar_modal_confirmacao(mouse_pos):
   
    # Fundo escurecido
    overlay = pygame.Surface((LARGURA, ALTURA))
    overlay.set_alpha(150)
    overlay.fill(PRETO)
    screen.blit(overlay, (0,0))
    
    # Caixa Modal
    largura_box, altura_box = 500, 300
    x_box = (LARGURA - largura_box) // 2
    y_box = (ALTURA - altura_box) // 2
    
    rect_box = pygame.Rect(x_box, y_box, largura_box, altura_box)
    pygame.draw.rect(screen, CINZA_ESCURO, rect_box, border_radius=20)
    pygame.draw.rect(screen, BRANCO, rect_box, 3, border_radius=20)
    
    # Texto
    txt_pergunta = font_aviso.render("VOLTAR AO MENU?", True, BRANCO)
    txt_aviso = font_info.render("O progresso atual será perdido.", True, CINZA_CLARO)
    
    screen.blit(txt_pergunta, (x_box + (largura_box - txt_pergunta.get_width())//2, y_box + 50))
    screen.blit(txt_aviso, (x_box + (largura_box - txt_aviso.get_width())//2, y_box + 100))
    
    # Botões
    w_btn = 150
    h_btn = 60
    y_btn = y_box + 180
    gap = 40
    
    rect_sim = desenhar_botao_estetico("SIM", x_box + (largura_box//2) - w_btn - (gap//2), y_btn, w_btn, h_btn, VERDE_CLARO, VERDE, mouse_pos)
    rect_nao = desenhar_botao_estetico("NÃO", x_box + (largura_box//2) + (gap//2), y_btn, w_btn, h_btn, VERMELHO_CLARO, VERMELHO, mouse_pos)
    
    return rect_sim, rect_nao

def salvar_dados_fase(pontuacao_atual, bola_x_pos):
    try:
        data_hoje = datetime.date.today()
        hora_agora = datetime.datetime.now().time().strftime("%H:%M:%S")
        lado = "Esquerda" if bola_x_pos < (LARGURA / 2) else "Direita"
        with open(arquivo_dados_pong, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([data_hoje, hora_agora, pontuacao_atual, lado])
    except:
        pass

def calcular_posicao_pe(landmarks):
    x = (landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].x + 
         landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x) / 2
    y = (landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].y + 
         landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y) / 2
    return x, y

def transformar_perspectiva(x_pose, y_pose):
    if len(pontos_calibracao_repetea) != 4:
        return int(x_pose * LARGURA) 
    p_cam = (int(x_pose * LARGURA_CAM), int(y_pose * ALTURA_CAM))
    pts_calib = np.float32(pontos_calibracao_repetea)
    pts_tela = np.float32([[0, 0], [LARGURA_CAM, 0], [0, ALTURA_CAM], [LARGURA_CAM, ALTURA_CAM]])
    try:
        matrix = cv2.getPerspectiveTransform(pts_calib, pts_tela)
        px = (matrix[0][0]*p_cam[0] + matrix[0][1]*p_cam[1] + matrix[0][2]) / \
             (matrix[2][0]*p_cam[0] + matrix[2][1]*p_cam[1] + matrix[2][2])
        return int(px * relacao_w)
    except:
        return int(x_pose * LARGURA)

def reset_bola(hard_reset=False):
    global bola_x, bola_y, bola_vel_y, bola_vel_x
    bola_x, bola_y = LARGURA / 2, ALTURA / 3
    velocidade = VELOCIDADE_INICIAL if hard_reset else abs(bola_vel_y)
    bola_vel_y = -velocidade 
    bola_vel_x = velocidade * random.choice([-1, 1])
    time.sleep(1)

def reiniciar_jogo():
    global score, vidas
    score = 0
    vidas = 3
    reset_bola(hard_reset=True)

# --- LOOP PRINCIPAL ---

screen = pygame.display.set_mode((LARGURA, ALTURA), pygame.RESIZABLE) 
pygame.display.set_caption(f'Pong Humano - Jogador: {jogador_nome}')
clock = pygame.time.Clock()

definir_cores_piso("ESCURO") 
pausa_confirmacao = False # Controla se a caixa de "Deseja sair?" está aberta

while not gameExit:
    
    mouse_pos = pygame.mouse.get_pos()
    clique = False
    
    # Tratamento de Eventos Global
    for event in pygame.event.get():
        if event.type == pygame.QUIT: gameExit = True
        if event.type == pygame.MOUSEBUTTONDOWN: clique = True
        if event.type == pygame.KEYDOWN:
            # No Menu, Q sai. No jogo, Q sai.
            if estado_jogo == "MENU" and event.key == pygame.K_q: gameExit = True
            
            # Lógica do ESCAPE no jogo
            if estado_jogo == "JOGANDO" and event.key == pygame.K_ESCAPE:
                pausa_confirmacao = not pausa_confirmacao # Alterna a pausa

    # =========================================================================
    # ESTADO: MENU INICIAL
    # =========================================================================
    if estado_jogo == "MENU":
        screen.fill(PRETO)
        
        titulo_sombra = font_titulo.render("PONG HUMANO", True, CINZA_ESCURO)
        screen.blit(titulo_sombra, (LARGURA//2 - titulo_sombra.get_width()//2 + 5, ALTURA//5 + 5))
        titulo = font_titulo.render("PONG HUMANO", True, COR_RAQUETE)
        screen.blit(titulo, (LARGURA//2 - titulo.get_width()//2, ALTURA//5))
        
        subtitulo = font_info.render(f"Jogador: {jogador_nome}", True, BRANCO)
        screen.blit(subtitulo, (LARGURA//2 - subtitulo.get_width()//2, ALTURA//5 + 100))
        
        lbl_piso = font_info.render("Selecione o contraste do chão:", True, BRANCO)
        screen.blit(lbl_piso, (LARGURA//2 - lbl_piso.get_width()//2, ALTURA//2 - 60))
        
        largura_btn = 260
        gap = 40
        x_centro = LARGURA // 2
        
        btn_escuro = desenhar_botao_estetico("PISO ESCURO", x_centro - largura_btn - (gap//2), ALTURA//2, largura_btn, 60, CINZA_CLARO, AZUL_NEON, mouse_pos, selecionado=(tipo_piso=="ESCURO"))
        btn_claro = desenhar_botao_estetico("PISO CLARO", x_centro + (gap//2), ALTURA//2, largura_btn, 60, CINZA_CLARO, AMARELO, mouse_pos, selecionado=(tipo_piso=="CLARO"))
        
        if clique:
            if btn_escuro.collidepoint(mouse_pos): defining_cores_piso = definir_cores_piso("ESCURO")
            if btn_claro.collidepoint(mouse_pos): defining_cores_piso = definir_cores_piso("CLARO")

        btn_jogar = desenhar_botao_estetico("INICIAR JOGO", LARGURA//2 - 150, ALTURA//2 + 120, 300, 80, VERDE_CLARO, VERDE, mouse_pos)
        
        if clique and btn_jogar.collidepoint(mouse_pos):
            reiniciar_jogo()
            pausa_confirmacao = False
            estado_jogo = "JOGANDO"

        if camera.isOpened(): ret, _ = camera.read()

    # =========================================================================
    # ESTADO: JOGANDO
    # =========================================================================
    elif estado_jogo == "JOGANDO":
        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            while camera.isOpened() and estado_jogo == "JOGANDO":
                
                # --- VISÃO COMPUTACIONAL ---
                ret, frame = camera.read()
                if not ret: break
                frame = cv2.flip(frame, 1) 
                
                # Só processa se não estiver pausado (economia de recursos)
                # ou processa sempre para mostrar feedback visual mesmo pausado
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_rgb.flags.writeable = False
                results = pose.process(img_rgb)
                img_debug = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
                
                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(img_debug, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                    if len(pontos_calibracao_repetea) == 4:
                        pts = pontos_calibracao_repetea
                        cv2.line(img_debug, tuple(pts[0]), tuple(pts[1]), CV_VERDE, 2)
                        cv2.line(img_debug, tuple(pts[1]), tuple(pts[3]), CV_VERDE, 2)
                        cv2.line(img_debug, tuple(pts[2]), tuple(pts[0]), CV_VERDE, 2)
                        cv2.line(img_debug, tuple(pts[2]), tuple(pts[3]), CV_VERDE, 2)
                        for p in pts: cv2.circle(img_debug, tuple(p), 5, CV_AZUL, 3)
                        x_norm, y_norm = calcular_posicao_pe(results.pose_landmarks.landmark)
                        
                        # Se estiver pausado, não atualiza a posição do jogador (congela)
                        if not pausa_confirmacao:
                            px_jogador = transformar_perspectiva(x_norm, y_norm)

                # --- LÓGICA DO JOGO (Só roda se NÃO estiver pausado) ---
                if not pausa_confirmacao:
                    raquete_x = px_jogador - (raquete_w / 2)
                    if raquete_x < 0: raquete_x = 0
                    if raquete_x + raquete_w > LARGURA: raquete_x = LARGURA - raquete_w

                    bola_x += bola_vel_x
                    bola_y += bola_vel_y

                    if bola_x <= 0 or bola_x + bola_tam >= LARGURA: bola_vel_x *= -1 
                    if bola_y <= 0: bola_vel_y *= -1 
                    
                    rect_bola = pygame.Rect(bola_x, bola_y, bola_tam, bola_tam)
                    rect_raquete = pygame.Rect(raquete_x, raquete_y, raquete_w, raquete_h)
                    
                    if rect_bola.colliderect(rect_raquete) and bola_vel_y > 0:
                        bola_vel_y *= -1 
                        snd_batida.play()
                        score += 10
                        if score > 0 and score % 20 == 0:
                            bola_vel_x *= 1.1
                            bola_vel_y *= 1.1

                    if bola_y > ALTURA:
                        snd_erro.play()
                        salvar_dados_fase(score, bola_x)
                        vidas -= 1
                        if vidas == 0:
                            estado_jogo = "GAMEOVER"
                        else:
                            reset_bola(hard_reset=False)

                # --- DESENHO ---
                screen.fill(PRETO)
                pygame.draw.rect(screen, COR_RAQUETE, (raquete_x, raquete_y, raquete_w, raquete_h))
                pygame.draw.ellipse(screen, COR_BOLA, (bola_x, bola_y, bola_tam, bola_tam))
                pygame.draw.line(screen, VERMELHO, (0, ALTURA-2), (LARGURA, ALTURA-2), 5)
                
                if hud_switch:
                    txt_score = font_placar.render(f'{score}', True, COR_TEXTO)
                    txt_vidas = font_placar.render(f'Vidas: {vidas}', True, VERMELHO)
                    screen.blit(txt_score, (LARGURA/2 - 20, 50))
                    screen.blit(txt_vidas, (LARGURA - 220, 50))

                # --- BOTÃO MENU NO CANTO (Só se não estiver pausado) ---
                if not pausa_confirmacao:
                    # Botão pequeno no canto superior direito
                    rect_menu = desenhar_botao_estetico("MENU", LARGURA - 120, 10, 100, 40, CINZA_CLARO, CINZA_CLARO, pygame.mouse.get_pos())
                
                # --- MODAL DE CONFIRMAÇÃO ---
                if pausa_confirmacao:
                    rect_sim, rect_nao = desenhar_modal_confirmacao(pygame.mouse.get_pos())

                pygame.display.update()
                clock.tick(60) 
                
                cv2.imshow("Tela de Controle (Pong)", img_debug)
                
                # --- EVENTOS INTERNOS DO LOOP ---
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: 
                        gameExit = True
                        estado_jogo = "SAIR"
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            pausa_confirmacao = not pausa_confirmacao
                    
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        
                        if pausa_confirmacao:
                            # Se estiver na tela de confirmação, checa SIM ou NÃO
                            rect_sim, rect_nao = desenhar_modal_confirmacao(mouse_pos) # Recalcula rects
                            if rect_sim.collidepoint(mouse_pos):
                                estado_jogo = "MENU"
                                pausa_confirmacao = False
                            if rect_nao.collidepoint(mouse_pos):
                                pausa_confirmacao = False
                        else:
                            # Se estiver jogando, checa o botão MENU no canto
                            rect_menu = pygame.Rect(LARGURA - 120, 10, 100, 40)
                            if rect_menu.collidepoint(mouse_pos):
                                pausa_confirmacao = True

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    estado_jogo = "MENU"
                    break

    # =========================================================================
    # ESTADO: GAME OVER
    # =========================================================================
    elif estado_jogo == "GAMEOVER":
        screen.fill(PRETO)
        
        msg_fim = font_titulo.render("FIM DE JOGO", True, VERMELHO)
        msg_score = font_placar.render(f"Pontuação Final: {score}", True, BRANCO)
        
        screen.blit(msg_fim, (LARGURA//2 - msg_fim.get_width()//2, ALTURA//4))
        screen.blit(msg_score, (LARGURA//2 - msg_score.get_width()//2, ALTURA//4 + 100))
        
        btn_restart = desenhar_botao_estetico("REINICIAR", LARGURA//2 - 220, ALTURA//2 + 50, 200, 80, CINZA_CLARO, VERDE, mouse_pos)
        btn_sair = desenhar_botao_estetico("MENU", LARGURA//2 + 20, ALTURA//2 + 50, 200, 80, CINZA_CLARO, VERMELHO, mouse_pos)
        
        if clique:
            if btn_restart.collidepoint(mouse_pos):
                reiniciar_jogo()
                estado_jogo = "JOGANDO"
                pausa_confirmacao = False
            if btn_sair.collidepoint(mouse_pos):
                estado_jogo = "MENU"

        if camera.isOpened(): ret, _ = camera.read()

    pygame.display.update()

cv2.destroyAllWindows()
pygame.quit()
camera.release()
exit()