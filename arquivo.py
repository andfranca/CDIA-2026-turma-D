import pandas as pd
def ler_arquivo_csv(caminho_arquivo):
    df = pd.read_csv(caminho_arquivo)
    return df