"""
1_extrair.py  -  ETAPA 1: Extração e Camada RAW
----------------------------------------------
Passo a passo:
  1. Localiza ou realiza o download do arquivo 'viagens.zip' do google drive para o diretório 'data/'.
  2. Lê os 4 CSVs de dentro do .zip (viagem, passagem, trecho, pagamento).
  3. Insere os dados, SEM nenhuma alteração, nas 4 tabelas RAW do MySQL.

ANTES DE RODAR: A variável 'DRIVE_FILE_ID' do módulo 'config.py'
                já deve ter sido preenchida com o id correto.

A camada RAW é uma cópia fiel do CSV: todas as colunas são do tipo VARCHAR.
As tabelas já devem ter sido criadas pelo script '0_criar_banco.txt'.
"""

import zipfile

import gdown
import pandas as pd

from common import config, banco


# ---------------------------------------------------------------------------
# Passo 1 - Localizar o arquivo .zip na pasta data/
# ---------------------------------------------------------------------------
def obter_zip():
    """
    Aponta para o 'viagens.zip' caso já esteja na pasta 'data/'.
    Do contrário, realiza o download do arquivo do google drive.
    """
    config.PASTA_DADOS.mkdir(exist_ok=True)
    destino = config.PASTA_DADOS / "viagens.zip"
    if destino.exists():
        print("[1/3] Usando o arquivo local:", destino.resolve())
        return destino
    else:
        print(
            "[1/3] Realizando o download do google drive para:",
            destino.resolve().parent,
        )
        try:
            gdown.download(id=config.DRIVE_FILE_ID, output=str(destino))
        except Exception as erro:
            print("[ERRO] Algo deu errado:", erro)
            raise


# ---------------------------------------------------------------------------
# Passo 2 - Carregar um CSV dentro da sua tabela RAW
# ---------------------------------------------------------------------------
def carregar_csv(conexao, zip_aberto, nome_csv, tabela):
    """
    Lê um CSV de dentro do zip e insere todas as linhas na tabela do MySQL.

    As colunas do CSV estão na MESMA ordem das colunas da tabela
    (definidas no '0_criar_banco.txt') para que seja possível a inserção "na ordem",
    sem precisar escrever o nome de cada coluna.
    """
    print("      Carregando", tabela, "...")

    # esvazia a tabela antes de carregar (assim, rodar de novo não duplica dados)
    banco.executar(conexao, f"TRUNCATE TABLE {tabela}")

    total = 0
    with zip_aberto.open(nome_csv) as arquivo:
        # lẽ o CSV em pedaços, para não encher a memória do PC em bases grandes
        pedacos = pd.read_csv(
            arquivo,
            sep=config.CSV_SEPARADOR,  # colunas separadas por ponto-e-virgula
            encoding=config.CSV_ENCODING,  # acentuação em latin-1
            dtype=str,  # tudo como texto (camada RAW)
            keep_default_na=False,  # campo vazio continua "" (não vira "NaN")
            chunksize=config.TAMANHO_BLOCO,
        )
        for pedaco in pedacos:
            linhas = pedaco.values.tolist()
            # um "%s" para cada coluna do CSV
            marcadores = ", ".join(["%s"] * len(pedaco.columns))
            comando = f"INSERT INTO {tabela} VALUES ({marcadores})"
            banco.inserir_em_lote(conexao, comando, linhas)
            total += len(linhas)

    print("      ->", total, "linhas em", tabela)


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    print("=== FASE 1: EXTRAÇÃO + CAMADA RAW ===")
    try:
        conexao = banco.conectar()

        caminho_zip = obter_zip()
        print("[2/3] Abrindo o arquivo zip...")
        print("[3/3] Carregando as 4 tabelas RAW...")
        with zipfile.ZipFile(caminho_zip) as zip_aberto:
            for arquivo in config.ARQUIVOS.values():
                carregar_csv(conexao, zip_aberto, arquivo["csv"], arquivo["tabela_raw"])

        conexao.close()
        print("=== Camada RAW concluída com sucesso! ===")
    except Exception as erro:
        print("[ERRO] Algo deu errado:", erro)
        raise


if __name__ == "__main__":
    main()
