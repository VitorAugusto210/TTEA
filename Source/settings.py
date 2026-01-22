import pygame
import numpy as np

pygame.init()
pygame.font.init()

# --- HARDWARE ---
CAMERA = 0  # Índice da câmera

# --- DIMENSÕES DA TELA PADRÃO ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# --- CORES BÁSICAS ---
branco = (255, 255, 255)
preto = (0, 0, 0)
verde = (0, 255, 0)
azul = (0, 0, 255)
vermelho = (255, 0, 0)
amarelo = (255, 255, 0)

# --- CORES DA INTERFACE (UI) ---
COLORS = {
    "buttons": {
        "default": (70, 130, 180),  # Azul Aço
        "second": (100, 149, 237),  # Azul Cornflower (Hover)
        "shadow": (30, 30, 30),     # Sombra
        "text": branco              # Texto
    }
}

# --- FONTES ---
# Tenta carregar fonte padrão do sistema
try:
    font_name = pygame.font.match_font('arial')
except:
    font_name = None

FONTS = {
    "small": pygame.font.SysFont(font_name, 20),
    "medium": pygame.font.SysFont(font_name, 30),
    "large": pygame.font.SysFont(font_name, 50)
}

# --- BOTÕES ---
BUTTONS_SIZES = (200, 50)

# --- CALIBRAÇÃO (Variável Global) ---
pontos_calibracao = np.zeros((4, 2), int)