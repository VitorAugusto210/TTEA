import cv2

def listar_cameras():
    print("Verificando câmeras disponíveis...")
    # Testa os primeiros 5 índices (0 a 4)
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) # Testando com DirectShow (mesmo do seu código)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"[SUCESSO] Câmera encontrada no índice: {i}")
                # Mostra o que a câmera está vendo para você confirmar qual é
                cv2.imshow(f'Camera {i}', frame)
                cv2.waitKey(1000) # Mostra por 1 segundo
                cv2.destroyAllWindows()
            else:
                print(f"[FALHA] Índice {i} abre mas não retorna imagem.")
            cap.release()
        else:
            print(f"[VAZIO] Nenhuma câmera no índice: {i}")

if __name__ == "__main__":
    listar_cameras()