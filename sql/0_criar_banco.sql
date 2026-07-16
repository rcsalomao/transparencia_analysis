-- ===========================================================================
-- ETAPA 0 - CRIAR O BANCO E AS TABELAS
-- ===========================================================================
-- INSTRUÇÕES:
--   1) Abra o MySQL Workbench e conecte no seu servidor (instância local).
--   2) Abra uma aba de query (SQL) em branco.
--   3) Copie TODO o conteudo deste arquivo.
--   4) Cole na aba de query do Workbench.
--   5) Clique no raio (ou aperte Ctrl+Shift+Enter) para EXECUTAR tudo.
--   6) O banco 'transparencia' e as tabelas estarão criados. Agora prosiga para a próxima etapa (python 1_extrair.py).
--
-- IMPORTANTE: Deve-se rodar este script UMA vez, ANTES dos scripts Python.
-- Os scripts python NÃO criam tabelas: eles apenas inserem/transformam os dados.
-- O nome do banco (transparencia) deve ser o MESMO do .env (variável MYSQL_DATABASE).
-- ===========================================================================
--
-- 1) BANCO DE DADOS ---------------------------------------------------------

DROP DATABASE IF EXISTS transparencia;

CREATE DATABASE IF NOT EXISTS transparencia character
SET utf8mb4 COLLATE utf8mb4_general_ci;

USE transparencia;

-- ===========================================================================
-- 2) CAMADA RAW  (replica do CSV: TODAS as colunas sao VARCHAR / texto)
--    Sem PK/FK: a Raw guarda o dado bruto, exatamente como veio do arquivo.
--    A ordem das colunas bate com a ordem do CSV (o 1_extrair.py insere "na
--    ordem", com INSERT INTO tabela VALUES (...)).
-- ===========================================================================

DROP TABLE IF EXISTS raw_viagem;

CREATE TABLE raw_viagem (
    id_viagem varchar(20),
    num_proposta varchar(20),
    situacao varchar(50),
    viagem_urgente varchar(5),
    justificativa_viagem varchar(2000),
    cod_orgao_superior varchar(20),
    nome_orgao_superior varchar(255),
    cod_orgao_solicitante varchar(100),
    nome_orgao_solicitante varchar(255),
    cpf_viajante varchar(20),
    nome_viajante varchar(255),
    cargo varchar(255),
    funcao varchar(255),
    descricao_funcao varchar(2000),
    data_inicio varchar(20),
    data_fim varchar(20),
    destinos varchar(4000),
    motivo varchar(4000),
    valor_diarias varchar(20),
    valor_passagens varchar(20),
    valor_devolucao varchar(20),
    valor_outros_gastos varchar(20)) ENGINE = InnoDB ROW_FORMAT = DYNAMIC;

DROP TABLE IF EXISTS raw_trecho;

CREATE TABLE raw_trecho (
    id_viagem varchar(20),
    num_proposta varchar(20),
    sequencia_trecho varchar(20),
    origem_data varchar(20),
    origem_pais varchar(60),
    origem_uf varchar(40),
    origem_cidade varchar(80),
    destino_data varchar(20),
    destino_pais varchar(60),
    destino_uf varchar(40),
    destino_cidade varchar(80),
    meio_transporte varchar(50),
    numero_diarias varchar(20),
    missao varchar(20)) ENGINE = InnoDB;

DROP TABLE IF EXISTS raw_passagem;

CREATE TABLE raw_passagem (
    id_viagem varchar(20),
    num_proposta varchar(20),
    meio_transporte varchar(50),
    pais_origem_ida varchar(60),
    uf_origem_ida varchar(40),
    cidade_origem_ida varchar(80),
    pais_destino_ida varchar(60),
    uf_destino_ida varchar(40),
    cidade_destino_ida varchar(80),
    pais_origem_volta varchar(60),
    uf_origem_volta varchar(40),
    cidade_origem_volta varchar(80),
    pais_destino_volta varchar(60),
    uf_destino_volta varchar(40),
    cidade_destino_volta varchar(80),
    valor_passagem varchar(20),
    taxa_servico varchar(20),
    data_emissao varchar(20),
    hora_emissao varchar(20)) ENGINE = InnoDB;

DROP TABLE IF EXISTS raw_pagamento;

CREATE TABLE raw_pagamento (
    id_viagem varchar(20),
    num_proposta varchar(20),
    cod_orgao_superior varchar(20),
    nome_orgao_superior varchar(255),
    cod_orgao_pagador varchar(20),
    nome_orgao_pagador varchar(255),
    cod_ug_pagadora varchar(20),
    nome_ug_pagadora varchar(255),
    tipo_pagamento varchar(50),
    valor varchar(20)) ENGINE = InnoDB;

-- ===========================================================================
-- 3) CAMADA SILVER  (dados tipados + integridade referencial)
--    'silver_viagem' é a tabela principal (PRIMARY KEY = id_viagem).
--    'silver_trecho', 'silver_passagem' e 'silver_pagamento' apontam para ela com FOREIGN KEY (id_viagem).
--
--    Ordem importa: por causa da FK, derrubamos as filhas (trecho, passagem e pagamento)
--    ANTES da principal (viagem), e criamos a principal ANTES da filha.
-- ===========================================================================

DROP TABLE IF EXISTS silver_pagamento;

DROP TABLE IF EXISTS silver_passagem;

DROP TABLE IF EXISTS silver_trecho;

DROP TABLE IF EXISTS silver_viagem;

CREATE TABLE silver_viagem (
    id_viagem varchar(20) NOT NULL,
    num_proposta varchar(20),
    situacao varchar(50),
    viagem_urgente varchar(5),
    cod_orgao_superior varchar(20),
    nome_orgao_superior varchar(255) NOT NULL,
    nome_viajante varchar(255),
    cargo varchar(255),
    data_inicio date,
    data_fim date,
    destinos varchar(4000),
    motivo varchar(4000),
    valor_diarias DECIMAL(10, 2),
    valor_passagens DECIMAL(10, 2),
    valor_devolucao DECIMAL(10, 2),
    valor_outros_gastos DECIMAL(10, 2),
    valor_total DECIMAL(12, 2),
    duracao_dias int,
    -- constraints --
    PRIMARY KEY (id_viagem),
    CONSTRAINT ck_sv_valor_diarias CHECK (valor_diarias >= 0)) ENGINE = InnoDB ROW_FORMAT = DYNAMIC;

CREATE TABLE silver_trecho (
    id_trecho int AUTO_INCREMENT,
    id_viagem varchar(20) NOT NULL,
    sequencia_trecho int,
    origem_data date,
    origem_uf varchar(40),
    origem_cidade varchar(80),
    destino_data date,
    destino_uf varchar(40),
    destino_cidade varchar(80),
    meio_transporte varchar(50),
    numero_diarias DECIMAL(10, 2),
    -- constraints --
    PRIMARY KEY (id_trecho),
    FOREIGN KEY (id_viagem) REFERENCES silver_viagem (id_viagem),
    UNIQUE (id_viagem, sequencia_trecho),
    CONSTRAINT ck_st_numero_diarias CHECK (numero_diarias >= 0)) ENGINE = InnoDB;

CREATE TABLE silver_passagem (
    id_passagem int AUTO_INCREMENT,
    id_viagem varchar(20) NOT NULL,
    meio_transporte varchar(50),
    pais_origem_ida varchar(60),
    uf_origem_ida varchar(40),
    cidade_origem_ida varchar(80),
    pais_destino_ida varchar(60),
    uf_destino_ida varchar(40),
    cidade_destino_ida varchar(80),
    valor_passagem DECIMAL(10, 2),
    taxa_servico DECIMAL(10, 2),
    data_emissao date,
    -- constraints --
    PRIMARY KEY (id_passagem),
    FOREIGN KEY (id_viagem) REFERENCES silver_viagem (id_viagem),
    CONSTRAINT ck_sp_valor_passagem CHECK (valor_passagem >= 0),
    CONSTRAINT ck_sp_taxa_servico CHECK (taxa_servico >= 0)) ENGINE = InnoDB;

CREATE TABLE silver_pagamento (
    id_pagamento int AUTO_INCREMENT,
    id_viagem varchar(20) NOT NULL,
    num_proposta varchar(20),
    nome_orgao_pagador varchar(255),
    nome_ug_pagadora varchar(255),
    tipo_pagamento varchar(50) NOT NULL,
    valor DECIMAL(10, 2),
    -- constraints --
    PRIMARY KEY (id_pagamento),
    FOREIGN KEY (id_viagem) REFERENCES silver_viagem (id_viagem),
    CONSTRAINT ck_sp_valor_pagamento CHECK (valor >= 0)) ENGINE = InnoDB;

