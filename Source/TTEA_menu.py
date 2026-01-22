import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import arquivo
from settings import * # Importa as variáveis globais do settings
import cv2
import numpy as np
import settings
import pygame
import subprocess
import csv # Necessário para ler a configuração
from importlib import reload # Necessário para reiniciar os jogos sem fechar o menu

from tkinter import messagebox

# Configuração da Janela Principal
root = tk.Tk()

def center_window_on_screen(width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cord = int((screen_width/2) - (width/2))
    y_cord = int((screen_height/2) - (height/2))
    root.geometry("{}x{}+{}+{}".format(width, height, x_cord, y_cord))

def show_menu():
    root.title('Menu TTEA')
    arr_Jogadores = ler_nome_jogadores()
    jogador_cb['values'] = arr_Jogadores

    width, height = 400, 600
    center_window_on_screen(width, height)
    menu_frame.pack()
    cad_frame.forget()
    
    # Reseta os campos
    game_cb['state'] = 'readonly'
    game_cb.set('')
    jogador_cb['state'] = 'disabled'
    jogador_cb.set('')
    fase_cb['state'] = 'disabled'
    fase_cb.set('')
    nivel_cb['state'] = 'disabled'
    nivel_cb.set('')

def show_cad():
    root.title('Cadastro TTEA')
    width, height = 300, 150
    center_window_on_screen(width, height)
    cad_frame.pack()
    menu_frame.forget()

# Configuração da Raiz
root.resizable(False, False)
root.title('Menu TTEA')
width, height = 400, 600
center_window_on_screen(width, height)

# Frames
menu_frame = tk.Frame(root)
cad_frame = tk.Frame(root)

# --- LOGO ---
try:
    image = Image.open("Assets/TTEA Logo.png")
    photo = ImageTk.PhotoImage(image)
    imagem = tk.Label(menu_frame, text = "TTEA Logo", image = photo)
    imagem.image = photo
    imagem.pack()
except:
    pass

# --- BOTÃO CALIBRAR ---
def CalibrarCallback():
    import calibracao
    reload(calibracao)

B = tk.Button(menu_frame, text ="Calibrar", command = CalibrarCallback)
B.pack()

# --- SELEÇÃO DE JOGO ---
label = ttk.Label(menu_frame, text="Jogos:")
label.pack(fill=tk.X, padx=100, pady=5)

selected_game = tk.StringVar()
game_cb = ttk.Combobox(menu_frame, textvariable=selected_game)
game = ''

# Adicionado BEATHIT na lista
game_cb['values'] = ['KARTEA', 'REPETEA', 'BEATHIT', 'PONG']
game_cb['state'] = 'readonly'
game_cb.pack(fill=tk.X, padx=100, pady=5)

def game_changed(event):
    global game
    game = selected_game.get()
    jogador_cb['state'] = 'readonly'
    jogador_cb.set('')
    
    if game == 'KARTEA':
        fase_cb['values'] = ['1', '2', '3']
        nivel_cb['values'] = ['1', '2', '3', '4', '5', '6']
    elif game == 'BEATHIT' or game == 'PONG':
        # BeatHit é jogo livre
        fase_cb['values'] = ['1'] 
        nivel_cb['values'] = ['1']
    else:
        # RepeTEA
        fase_cb['values'] = ['1', '2', '3','4','5','6','7','8','9','10']
        nivel_cb['values'] = ['1', '2', '3', '4', '5']

    fase_cb['state'] = 'disabled'
    fase_cb.set('')
    nivel_cb['state'] = 'disabled'
    nivel_cb.set('')

game_cb.bind('<<ComboboxSelected>>', game_changed)

# --- SELEÇÃO DE JOGADOR ---
label = ttk.Label(menu_frame, text="Jogador:")
label.pack(fill=tk.X, padx=100, pady=5)

selected_jogador = tk.StringVar()
jogador_cb = ttk.Combobox(menu_frame, textvariable=selected_jogador)

def ler_nome_jogadores():
    path = os.getcwd() + "\Jogadores"
    if not os.path.exists(path):
        os.makedirs(path) 
    Jogadores = os.listdir(path)

    arr = []
    b = ''
    for a in Jogadores:
        # Limpa os sufixos para pegar apenas o nome
        a = a.replace('_KarTEA_sessao.csv','')
        a = a.replace('_KarTEA_config.csv','')
        a = a.replace('_KarTEA_detalhado.csv','')
        a = a.replace('_RepeTEA.csv','')
        a = a.replace('_RepeTEA_config.csv','')
        a = a.replace('_RepeTEA_detalhado.csv','')
        if a != b:
            arr.append(a)
        b = a
    return arr

arr_Jogadores = ler_nome_jogadores()
jogador_cb['values'] = arr_Jogadores
jogador_cb['state'] = 'disabled'
jogador_cb.pack(fill=tk.X, padx=100, pady=5)

# Variáveis Globais de Controle
jogador = ''
FASE = 0
NIVEL = 0
PLAYER_ARQ_CONFIG = ''

def jogador_changed(event):
    global jogador, PLAYER_ARQ_CONFIG
    jogador = selected_jogador.get()
    PLAYER = "Jogadores/" + jogador
    
    # Define quais arquivos carregar baseado no jogo
    if game == 'KARTEA':
        PLAYER_ARQ = PLAYER + "_KarTEA_sessao.csv"
        PLAYER_ARQ_CONFIG = PLAYER + "_KarTEA_config.csv"
        PLAYER_ARQ_DET = PLAYER + "_KarTEA_detalhado.csv"
    elif game == 'REPETEA' or game == 'BEATHIT':
        # BEATHIT usa a calibração do REPETEA
        PLAYER_ARQ = PLAYER + "_RepeTEA_sessao.csv"
        PLAYER_ARQ_CONFIG = PLAYER + "_RepeTEA_config.csv"
        PLAYER_ARQ_DET = PLAYER + "_RepeTEA_detalhado.csv"

    global FASE, NIVEL
    try:
        FASE = arquivo.get_K_FASE(PLAYER_ARQ_CONFIG)
        NIVEL = arquivo.get_K_NIVEL(PLAYER_ARQ_CONFIG)
        
        fase_cb['state'] = 'readonly'
        if FASE > 0: fase_cb.current(FASE-1)
        
        nivel_cb['state'] = 'readonly'
        if NIVEL > 0: nivel_cb.current(NIVEL-1)
    except:
        print("Erro ao ler configuração do jogador ou arquivo novo.")
        fase_cb['state'] = 'readonly'
        nivel_cb['state'] = 'readonly'

jogador_cb.bind('<<ComboboxSelected>>', jogador_changed)

# --- BOTÃO CADASTRO ---
def cadastrarCallback():
    show_cad()

B = tk.Button(menu_frame, text ="Cadastrar Novo Jogador", command = cadastrarCallback)
B.pack(fill=tk.X, padx=100, pady=10)

# --- SELEÇÃO DE FASE ---
label = ttk.Label(menu_frame, text="Fase:")
label.pack(fill=tk.X, padx=100, pady=5)

selected_fase = tk.StringVar()
fase_cb = ttk.Combobox(menu_frame, textvariable=selected_fase)
fase_cb['state'] = 'disabled'
fase_cb.pack(fill=tk.X, padx=100, pady=5)

def fase_changed(event):
    if PLAYER_ARQ_CONFIG:
        arquivo.set_K_FASE(PLAYER_ARQ_CONFIG, int(selected_fase.get()))

fase_cb.bind('<<ComboboxSelected>>', fase_changed)

# --- SELEÇÃO DE NÍVEL ---
label = ttk.Label(menu_frame, text="Nível:")
label.pack(fill=tk.X, padx=100, pady=5)

selected_nivel = tk.StringVar()
nivel_cb = ttk.Combobox(menu_frame, textvariable=selected_nivel)
nivel_cb['values'] = ['1', '2', '3', '4', '5', '6']
nivel_cb['state'] = 'disabled'
nivel_cb.pack(fill=tk.X, padx=100, pady=5)

def nivel_changed(event):
    if PLAYER_ARQ_CONFIG:
        arquivo.set_K_NIVEL(PLAYER_ARQ_CONFIG, int(selected_nivel.get()))

nivel_cb.bind('<<ComboboxSelected>>', nivel_changed)

# =========================================================================
# FUNÇÃO JOGAR (CORRIGIDA E ROBUSTA)
# =========================================================================
def JogarCallback():
    if not jogador:
        tk.messagebox.showwarning("Aviso", "Selecione um jogador!")
        return

    arquivo.set_Player(jogador)
    
    # 1. LEITURA INTELIGENTE DA RESOLUÇÃO (Evita erro de coluna trocada)
    largura_projetor = 800 # Valor de segurança padrão
    
    try:
        if PLAYER_ARQ_CONFIG:
            with open(PLAYER_ARQ_CONFIG, 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                next(csv_reader) # Pula cabeçalho
                linha = next(csv_reader) # Lê a linha de dados
                
                # Tenta achar um número que pareça uma resolução (>600) na linha
                encontrou = False
                for item in linha:
                    try:
                        valor = int(item)
                        if 600 <= valor <= 4000: # Faixa aceitável de resolução
                            largura_projetor = valor
                            encontrou = True
                            break
                    except:
                        continue
                
                if not encontrou:
                    print("Aviso: Resolução não encontrada no CSV. Usando 800.")

    except Exception as e:
        print(f"Erro ao ler arquivo de config: {e}. Usando padrão 800.")

    # 2. Define Fase e Nível no Arquivo Global
    try:
        arquivo.set_Fase(arquivo.get_K_FASE(PLAYER_ARQ_CONFIG))
        arquivo.set_Nivel(arquivo.get_K_NIVEL(PLAYER_ARQ_CONFIG))
    except:
        arquivo.set_Fase(1)
        arquivo.set_Nivel(1)

    print(f"Iniciando... Jogador: {arquivo.get_Player()} | Resolução: {largura_projetor}")
    
    # 3. Carrega Calibração
    settings.pontos_calibracao = arquivo.lerCalibracao()
    if len(settings.pontos_calibracao) < 4:
        print("AVISO: Calibração incompleta ou inexistente.")

    # 4. Atualiza as variáveis globais de settings com a resolução correta
    settings.div0_pista = 0
    settings.div1_pista = (largura_projetor // 3)
    settings.div2_pista = (2 * (largura_projetor // 3))
    settings.div3_pista = largura_projetor
    
    print(f"Divisões de Pista configuradas: {settings.div1_pista}, {settings.div2_pista}")

    # 5. Inicia o Jogo
    if game == 'KARTEA':
        import KarTEA
        reload(KarTEA)
        KarTEA.main()
        
    elif game == 'BEATHIT':
        import BeatHit
        reload(BeatHit)
        # BeatHit roda direto no import, não tem main()
    
    elif game == 'PONG':
        import Pong
        from importlib import reload
        reload(Pong)
        
    else:
        # RepeTEA
        import RepeTEA
        reload(RepeTEA)
        # RepeTEA não tem main() encapsulado, roda no import

B = tk.Button(menu_frame, text ="Jogar", command = JogarCallback)
B.pack()

menu_frame.pack()

# --- TELA DE CADASTRO ---
arr_Jogadores = ler_nome_jogadores()

NomeString = tk.StringVar(cad_frame)
DataString = tk.StringVar(cad_frame)
ObsString = tk.StringVar(cad_frame)

LNome = tk.Label(cad_frame, text="Nome: ")
LNome.grid(column=0, row=0, sticky=tk.W)
Nome = tk.Entry(cad_frame, width=20, textvariable=NomeString)
Nome.grid(column=1, row=0, padx=10)

LData = tk.Label(cad_frame, text="Data de Nasc.: ")
LData.grid(column=0, row=1, sticky=tk.W)
Data = tk.Entry(cad_frame, width=20, textvariable=DataString)
Data.grid(column=1, row=1, padx=10)

LObs = tk.Label(cad_frame, text="Observação: ")
LObs.grid(column=0, row=2, sticky=tk.W)
Obs = tk.Entry(cad_frame, width=20, textvariable=ObsString)
Obs.grid(column=1, row=2, padx=10)

def cadastrarcallback():
    SNome = NomeString.get()
    SData = DataString.get()
    SObs = ObsString.get()

    if SNome not in arr_Jogadores:
        arquivo.CadastrarJogador(SNome, SData, SObs)
        arr_Jogadores.append(SNome)
        res = tk.messagebox.askquestion (title='Jogador cadastrado!', message='Sucesso!\nDeseja cadastrar outro?')
        if res == 'no':
            show_menu()
    else:
        tk.messagebox.showerror(title='Erro!', message='Nome já cadastrado!')

B = tk.Button(cad_frame, text="Cadastrar Novo Jogador", command=cadastrarcallback)
B.grid(column=0, row=3, padx=10, pady=10, sticky=tk.W)

def cancelarcallback():
    show_menu()

B = tk.Button(cad_frame, text="Cancelar", command=cancelarcallback)
B.grid(column=1, row=3, padx=10, pady=10, sticky=tk.W)

root.mainloop()