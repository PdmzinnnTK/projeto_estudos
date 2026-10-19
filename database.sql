	
CREATE DATABASE ProEstudo;
USE ProEstudo;

#Criação da tabela Aluno

CREATE TABLE aluno (
    id_aluno INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    nivel_diagnostico VARCHAR(50) DEFAULT 'Não realizado',
    data_ultimo_acesso DATETIME
);

#Criação da tabela Professor
CREATE TABLE professor (
    id_professor INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(100) NOT NULL,
    materia_especialidade VARCHAR(80)
);

#Criação da tabela Usuário (Unificando os acessos)
CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    perfil VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Ativo',
    id_aluno INT,
    id_professor INT,
    id_administrador INT,
    FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno),
    FOREIGN KEY (id_professor) REFERENCES professor(id_professor)
);

#Criação da tabela Conteúdo
CREATE TABLE conteudo (
    id_conteudo INT AUTO_INCREMENT PRIMARY KEY,
    id_professor INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    materia VARCHAR(80) NOT NULL,
    tema VARCHAR(100) NOT NULL,
    tipo_conteudo VARCHAR(20) NOT NULL,
    descricao TEXT,
    arquivo VARCHAR(255) NOT NULL,
    link VARCHAR(255) NOT NULL,
    data_publicacao DATETIME,
    FOREIGN KEY (id_professor) REFERENCES professor(id_professor)
);

#Criação da tabela Diagnóstico
CREATE TABLE diagnostico (
    id_diagnostico INT AUTO_INCREMENT PRIMARY KEY,
    id_aluno INT NOT NULL,
    materia VARCHAR(80) NOT NULL,
    pontuacao_obtida INT NOT NULL,
    nivel_calculado VARCHAR(50) NOT NULL,
    data_realizacao DATETIME,
    FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno)
);

#Criação da tabela Progresso
CREATE TABLE progresso (
    id_progresso INT AUTO_INCREMENT PRIMARY KEY,
    id_aluno INT NOT NULL,
    id_conteudo INT NOT NULL,
    status_conclusao VARCHAR(20) DEFAULT 'EM_ANDAMENTO',
    nota_quiz DECIMAL(4,2),
    data_ultima_interacao DATETIME,
    FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno),
    FOREIGN KEY (id_conteudo) REFERENCES conteudo(id_conteudo)
);

INSERT INTO aluno (nome, nivel_diagnostico, data_ultimo_acesso) VALUES
    ('Leticia Rodrigues', 'Intermediário', '2026-10-01 14:30:10'),
    ('Paulo Ricardo', 'Intermediario', '2026-08-23 11:10:45'),
    ('Joao Pedro', 'Avancado', '2026-06-14 23:59:35'),
    ('Christian', 'Avancado', '2026-01-14 07:35:14'),
    ('Isadora', 'Básico', '2026-08-23 16:38:25');
   
INSERT INTO professor (nome, telefone, materia_especialidade) VALUES
    ('Germano', '44992658624', 'Matematica'),
    ('Talita', '44996854775', 'Portugues'),
    ('Jocel', '44985645231', 'Geografia'),
    ('Eliane', '44975843652 ', 'Historia'),
    ('Claudia', '44985746235', 'Ciencias da computação');
   
INSERT INTO usuario (email, senha, perfil, status) VALUES
    ('leticiarodrigues@gmail.com', '22022009l', 'Aluno', 'Ativo'),
    ('pauloricardo@gmail.com', 'senha456', 'Aluno', 'Ativo'),  
    ('profgermano@gmail.com', 'gmat123', 'Professor', 'Ativo'),
    ('claudia.prof@gmail.com', 'prof475', 'Professor', 'Ativo'),
    ('admin@gmail.com', 'admin123', 'Administrador', 'Ativo');
   
INSERT INTO conteudo (id_professor, titulo, materia, tema, tipo_conteudo, descricao, arquivo, link) VALUES
(1, 'Função Quadrática e Parábolas', 'Matemática', 'Álgebra', 'Vídeo', 'Explicação completa sobre vértice da parábola e raízes da função.', '', 'https://youtube.com/watch?v=exemplo1'),
(4, 'Segunda Guerra Mundial', 'História', 'História Geral', 'Resumo', 'Resumo em PDF cobrindo os principais fatores e consequências do conflito.', 'resumo_guerra.pdf', ''),
(3, 'Cartografia e Leitura de Mapas', 'Geografia', 'Geografia Geral', 'Vídeo', 'Videoaula explicativa sobre projeções cartográficas, escalas e orientação espacial.', '', 'https://youtube.com'),
(2, 'Análise Sintática: Sujeito e Predicado', 'Português', 'Gramática', 'Resumo', 'Guia prático com regras e exemplos para identificação dos tipos de sujeito e predicado.', 'resumo_analise_sintatica.pdf', ''),
(5, 'Lógica de Programação e Algoritmos', 'Ciências da Computação', 'Programação', 'Vídeo', 'Introdução às estruturas condicionais e laços de repetição em Python.', '', 'https://youtube.com/watch?v=logica_programacao');

	
INSERT INTO progresso (id_aluno, id_conteudo, status_conclusao, nota_quiz, data_ultima_interacao) VALUES
    (1, 1, 'EM ANDAMENTO', NULL, '2026-10-01 14:30:00'),
    (2, 2, 'CONCLUÍDO', 10.00, '2026-10-02 09:15:00'),
    (3, 3, 'CONCLUÍDO', 7.50, '2026-10-03 18:45:00'),
    (4, 4, 'EM ANDAMENTO', 6.00, '2026-10-04 11:20:00'),
    (5, 5, 'CANCELADO', NULL, '2026-10-05 16:00:00');

INSERT INTO diagnostico (id_aluno, materia, pontuacao_obtida, nivel_calculado, data_realizacao) VALUES
    (1, 'Matemática', 85, 'Avançado', '2026-10-01 09:00:00'),
    (2, 'Português', 45, 'Básico', '2026-10-01 10:30:00'),
    (3, 'Geografia', 70, 'Intermediário', '2026-10-02 14:15:00'),
    (4, 'História', 92, 'Avançado', '2026-10-02 16:00:00'),
    (5, 'Ciências da Computação', 60, 'Intermediário', '2026-10-03 11:00:00');


