"""
2_transformar.py  -  ETAPA 2: Transformação e Camada SILVER
----------------------------------------------------------
Pega os dados "sujos" da camada RAW e preenche as tabelas SILVER
(já criadas com PK/FK por '0_criar_banco.txt') com os dados limpos e tipados.

Execução dos comandos SQL, em ordem.
  1. Esvaziamento das tabelas SILVER (para garantir a idempotência).
  2. Cópia da camada RAW para SILVER, convertendo-se os tipos.
  3. Calculam-se as colunas derivadas (valor_total, duracao_dias).

------------------------------------------------------------------------------
CONVERSÃO DO TEXTO DA CAMADA RAW:

  - Dinheiro: "1.234,50" (texto)  ->  1234.50 (número DECIMAL)
      tira o ponto de milhar, troca a vírgula por ponto e faz CAST:
      CAST(REPLACE(REPLACE(NULLIF(TRIM(coluna), ''), '.', ''), ',', '.') AS DECIMAL(10,2))

  - Data: "30/06/2025" (texto)  ->  2025-06-30 (tipo DATE)
      STR_TO_DATE(NULLIF(TRIM(coluna), ''), '%d/%m/%Y')

  Obs.: NULLIF(coluna, '') transforma um campo vazio em NULL (vazio no banco).
------------------------------------------------------------------------------
"""

from common import banco


# 1) Esvaziar as tabelas SILVER (idempotência).
# A ordem importa por causa da FK:
# Deve-se apagar as tabelas filha (pagamento, passagem e trecho) antes da principal.
LIMPAR_SILVER = [
    "DELETE FROM silver_pagamento",
    "DELETE FROM silver_passagem",
    "DELETE FROM silver_trecho",
    "DELETE FROM silver_viagem",
]


# 2) Copiar RAW -> SILVER convertendo os tipos.
# silver_viagem é a tabela principal. Deve ser carregada primeiro.
SQL_VIAGEM = """
INSERT INTO silver_viagem (
    id_viagem,
    num_proposta,
    situacao,
    viagem_urgente,
    cod_orgao_superior,
    nome_orgao_superior,
    nome_viajante,
    cargo,
    data_inicio,
    data_fim,
    destinos,
    motivo,
    valor_diarias,
    valor_passagens,
    valor_devolucao,
    valor_outros_gastos
)
SELECT
    NULLIF(UPPER(TRIM(id_viagem)), ''),
    NULLIF(UPPER(TRIM(num_proposta)), ''),
    NULLIF(UPPER(TRIM(situacao)), ''),
    NULLIF(UPPER(TRIM(viagem_urgente)), ''),
    NULLIF(UPPER(TRIM(cod_orgao_superior)), ''),
    NULLIF(UPPER(TRIM(nome_orgao_superior)), ''),
    NULLIF(UPPER(TRIM(nome_viajante)), ''),
    NULLIF(UPPER(TRIM(cargo)), ''),
    STR_TO_DATE(NULLIF(TRIM(data_inicio),  ''), '%d/%m/%Y'),
    STR_TO_DATE(NULLIF(TRIM(data_fim), ''), '%d/%m/%Y'),
    NULLIF(UPPER(TRIM(destinos)), ''),
    NULLIF(TRIM(motivo), ''),
    CAST(REPLACE(REPLACE(NULLIF(TRIM(valor_diarias),    ''), '.', ''), ',', '.') AS DECIMAL(10,2)),
    CAST(REPLACE(REPLACE(NULLIF(TRIM(valor_passagens), ''), '.', ''), ',', '.') AS DECIMAL(10,2)),
    CAST(REPLACE(REPLACE(NULLIF(TRIM(valor_devolucao), ''), '.', ''), ',', '.') AS DECIMAL(10,2)),
    CAST(REPLACE(REPLACE(NULLIF(TRIM(valor_outros_gastos), ''), '.', ''), ',', '.') AS DECIMAL(10,2))
FROM raw_viagem;
"""

SQL_TRECHO = """
INSERT INTO silver_trecho (
    id_viagem,
    sequencia_trecho,
    origem_data,
    origem_uf,
    origem_cidade,
    destino_data,
    destino_uf,
    destino_cidade,
    meio_transporte,
    numero_diarias
)
SELECT
    NULLIF(UPPER(TRIM(id_viagem)), ''),
    CAST(TRIM(sequencia_trecho) AS UNSIGNED),
    STR_TO_DATE(NULLIF(TRIM(origem_data),  ''), '%d/%m/%Y'),
    NULLIF(UPPER(TRIM(origem_uf)), ''),
    NULLIF(UPPER(TRIM(origem_cidade)), ''),
    STR_TO_DATE(NULLIF(TRIM(destino_data),  ''), '%d/%m/%Y'),
    NULLIF(UPPER(TRIM(destino_uf)), ''),
    NULLIF(UPPER(TRIM(destino_cidade)), ''),
    NULLIF(UPPER(TRIM(meio_transporte)), ''),
    CAST(REPLACE(REPLACE(NULLIF(TRIM(numero_diarias), ''), '.', ''), ',', '.') AS DECIMAL(10,2))
FROM raw_trecho
WHERE id_viagem IN (SELECT id_viagem FROM silver_viagem);
"""

SQL_PASSAGEM = """
INSERT INTO silver_passagem (
    id_viagem,
    meio_transporte,
    pais_origem_ida,
    uf_origem_ida,
    cidade_origem_ida,
    pais_destino_ida,
    uf_destino_ida,
    cidade_destino_ida,
    valor_passagem,
    taxa_servico,
    data_emissao
)
SELECT
    NULLIF(UPPER(TRIM(id_viagem)), ''),
    NULLIF(UPPER(TRIM(meio_transporte)), ''),
    NULLIF(UPPER(TRIM(pais_origem_ida)), ''),
    NULLIF(UPPER(TRIM(uf_origem_ida)), ''),
    NULLIF(UPPER(TRIM(cidade_origem_ida)), ''),
    NULLIF(UPPER(TRIM(pais_destino_ida)), ''),
    NULLIF(UPPER(TRIM(uf_destino_ida)), ''),
    NULLIF(UPPER(TRIM(cidade_destino_ida)), ''),
    CAST(REPLACE(REPLACE(NULLIF(TRIM(valor_passagem), ''), '.', ''), ',', '.') AS DECIMAL(10,2)),
    CAST(REPLACE(REPLACE(NULLIF(TRIM(taxa_servico), ''), '.', ''), ',', '.') AS DECIMAL(10,2)),
    STR_TO_DATE(NULLIF(TRIM(data_emissao),  ''), '%d/%m/%Y')
FROM raw_passagem
WHERE id_viagem IN (SELECT id_viagem FROM silver_viagem);
"""

SQL_PAGAMENTO = """
INSERT INTO silver_pagamento (
    id_viagem,
    num_proposta,
    nome_orgao_pagador,
    nome_ug_pagadora,
    tipo_pagamento,
    valor
)
SELECT
    NULLIF(UPPER(TRIM(id_viagem)), ''),
    NULLIF(UPPER(TRIM(num_proposta)), ''),
    NULLIF(UPPER(TRIM(nome_orgao_pagador)), ''),
    NULLIF(UPPER(TRIM(nome_ug_pagadora)), ''),
    NULLIF(UPPER(TRIM(tipo_pagamento)), ''),
    CAST(REPLACE(REPLACE(NULLIF(TRIM(valor), ''), '.', ''), ',', '.') AS DECIMAL(10,2))
FROM raw_pagamento
WHERE id_viagem IN (SELECT id_viagem FROM silver_viagem);
"""


# 3) Calculando as colunas derivadas.
# Agora que os valores já são números e as datas já são DATE é possível facilmente obter os atributos derivados.
# COALESCE(coluna, 0) usa 0 quando o valor for NULL (vazio), para não quebrar a soma.
SQL_CALC_VIAGEM = """
UPDATE silver_viagem
SET valor_total = COALESCE(valor_diarias, 0) + COALESCE(valor_passagens, 0) + COALESCE(valor_outros_gastos, 0) - COALESCE(valor_devolucao, 0),
    duracao_dias  = DATEDIFF(data_fim, data_inicio)
"""


def main():
    print("=== ETAPA 2: TRANSFORMAÇÃO + CAMADA SILVER ===")
    try:
        conexao = banco.conectar()

        print("[1/3] Esvaziando as tabelas SILVER...")
        for comando in LIMPAR_SILVER:
            banco.executar(conexao, comando)

        print("[2/3] Copiando e convertendo RAW -> SILVER...")
        for sql_query, descr in [
            (SQL_VIAGEM, "silver_viagem"),
            (SQL_TRECHO, "silver_trecho"),
            (SQL_PASSAGEM, "silver_passagem"),
            (SQL_PAGAMENTO, "silver_pagamento"),
        ]:
            print(f"      transformando {descr}...")
            banco.executar(conexao, sql_query)
            print(f"      {descr} OK")

        print("[3/3] Calculando: valor_total, duracao_dias...")
        banco.executar(conexao, SQL_CALC_VIAGEM)

        conexao.close()
        print("=== Camada SILVER concluída com sucesso! ===")
    except Exception as erro:
        print("[ERRO] Algo deu errado:", erro)
        raise


if __name__ == "__main__":
    main()
