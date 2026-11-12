from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import webbrowser
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_pro_estudos_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ProEstudo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

MATERIAS = {
    'matematica': 'Matemática',
    'portugues': 'Português',
    'historia': 'História',
    'geografia': 'Geografia',
    'computacao': 'Ciências da Computação'
}

# Categorias de conteúdo: 'geral' (tela Conteúdos) e 'enem' (tela Conteúdos do ENEM)
CATEGORIAS_CONTEUDO = ['geral', 'enem']

PATENTES_INFO = {
    "Bronze": {"nome": "Bronze", "icone": "🥉", "cor": "#b08968", "bg": "#f5efe6", "min_pontos": 0},
    "Prata": {"nome": "Prata", "icone": "🥈", "cor": "#7f8c8d", "bg": "#f1f2f6", "min_pontos": 100},
    "Ouro": {"nome": "Ouro", "icone": "🥇", "cor": "#d4a373", "bg": "#fff8e1", "min_pontos": 200},
    "Platina": {"nome": "Platina", "icone": "💎", "cor": "#2ec4b6", "bg": "#e0f2f1", "min_pontos": 300},
    "Diamante": {"nome": "Diamante", "icone": "🔷", "cor": "#00b4d8", "bg": "#e0f7fa", "min_pontos": 400},
    "Mestre": {"nome": "Mestre", "icone": "👑", "cor": "#9c27b0", "bg": "#f3e5f5", "min_pontos": 500},
    "Desafiante": {"nome": "Desafiante", "icone": "⚡", "cor": "#e63946", "bg": "#ffe5e8", "min_pontos": 600}
}

# --- MODELOS DA BASE DE DADOS ---

class Aluno(db.Model):
    __tablename__ = 'aluno'
    id_aluno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    nivel_diagnostico = db.Column(db.String(50), default='Não realizado')
    data_ultimo_acesso = db.Column(db.DateTime, default=datetime.utcnow)
    pontos = db.Column(db.Integer, default=10)
    sequencia_dias = db.Column(db.Integer, default=1)
    foto = db.Column(db.String(255), default='default_avatar.png')
    moldura_equipada = db.Column(db.String(50), default='auto')

    @property
    def patente_info(self):
        p = self.pontos or 0
        if p >= 600: return PATENTES_INFO["Desafiante"]
        elif p >= 500: return PATENTES_INFO["Mestre"]
        elif p >= 400: return PATENTES_INFO["Diamante"]
        elif p >= 300: return PATENTES_INFO["Platina"]
        elif p >= 200: return PATENTES_INFO["Ouro"]
        elif p >= 100: return PATENTES_INFO["Prata"]
        else: return PATENTES_INFO["Bronze"]

    @property
    def moldura_ativa_info(self):
        if self.moldura_equipada and self.moldura_equipada in PATENTES_INFO:
            info = PATENTES_INFO[self.moldura_equipada]
            if (self.pontos or 0) >= info["min_pontos"]:
                return info
        return self.patente_info

    @property
    def todas_molduras_status(self):
        p = self.pontos or 0
        equipada_atual = self.moldura_ativa_info["nome"]
        
        lista = []
        for nome, info in PATENTES_INFO.items():
            desbloqueada = p >= info["min_pontos"]
            lista.append({
                "nome": nome,
                "icone": info["icone"],
                "cor": info["cor"],
                "bg": info["bg"],
                "min_pontos": info["min_pontos"],
                "desbloqueada": desbloqueada,
                "equipada": (nome == equipada_atual)
            })
        return lista

    @property
    def total_acessos_conteudos(self):
        return sum(a.qtd_acessos for a in self.acessos_materias) if self.acessos_materias else 0

    @property
    def missoes_conquistas(self):
        total = self.total_acessos_conteudos
        tabela_medalhas = [
            {"meta": 10, "titulo": "Primeiros Passos", "raridade": "Comum", "icone": "🌱", "cor": "#6c757d", "bg": "#f8f9fa"},
            {"meta": 20, "titulo": "Aprendiz Focado", "raridade": "Comum", "icone": "📖", "cor": "#6c757d", "bg": "#f8f9fa"},
            {"meta": 30, "titulo": "Buscador do Saber", "raridade": "Raro", "icone": "🔍", "cor": "#0d6efd", "bg": "#e7f1ff"},
            {"meta": 40, "titulo": "Mente Brilhante", "raridade": "Raro", "icone": "💡", "cor": "#0d6efd", "bg": "#e7f1ff"},
            {"meta": 50, "titulo": "Devorador de Aulas", "raridade": "Épico", "icone": "📚", "cor": "#6f42c1", "bg": "#f3e8ff"},
            {"meta": 60, "titulo": "Estudioso Incansável", "raridade": "Épico", "icone": "🔥", "cor": "#6f42c1", "bg": "#f3e8ff"},
            {"meta": 70, "titulo": "Mestre da Frequência", "raridade": "Lendário", "icone": "🎓", "cor": "#fd7e14", "bg": "#fff3cd"},
            {"meta": 80, "titulo": "Sábio do Conhecimento", "raridade": "Lendário", "icone": "🦉", "cor": "#fd7e14", "bg": "#fff3cd"},
            {"meta": 90, "titulo": "Guardião da Sabedoria", "raridade": "Mítico", "icone": "🛡️", "cor": "#d63384", "bg": "#f8d7da"},
            {"meta": 100, "titulo": "Centenário Acadêmico", "raridade": "Mítico", "icone": "⚡", "cor": "#d63384", "bg": "#f8d7da"},
            {"meta": 150, "titulo": "Lenda dos Estudos", "raridade": "Ancestral", "icone": "👑", "cor": "#ffc107", "bg": "#fff9db"},
            {"meta": 200, "titulo": "Mito Inalcançável", "raridade": "Ancestral", "icone": "🌟", "cor": "#ffc107", "bg": "#fff9db"},
            {"meta": 250, "titulo": "Divindade Escolar", "raridade": "Divino", "icone": "🌌", "cor": "#20c997", "bg": "#e6fffa"},
            {"meta": 300, "titulo": "Conhecimento Infinito", "raridade": "Divino", "icone": "🔮", "cor": "#20c997", "bg": "#e6fffa"},
            {"meta": 350, "titulo": "Mestre dos Elementos", "raridade": "Divino", "icone": "📜", "cor": "#20c997", "bg": "#e6fffa"},
            {"meta": 400, "titulo": "Sábio Imortal", "raridade": "Divino", "icone": "🏆", "cor": "#20c997", "bg": "#e6fffa"}
        ]

        resultado = []
        for m in tabela_medalhas:
            desbloqueado = total >= m["meta"]
            pct = min(100, int((total / m["meta"]) * 100))
            resultado.append({
                "meta": m["meta"],
                "titulo": m["titulo"],
                "raridade": m["raridade"],
                "icone": m["icone"],
                "cor": m["cor"],
                "bg": m["bg"],
                "desbloqueado": desbloqueado,
                "progresso_pct": pct
            })

        return {
            "total_acessos": total,
            "medalhas": resultado,
            "qtd_desbloqueadas": sum(1 for r in resultado if r["desbloqueado"]),
            "qtd_total": len(resultado)
        }

class Professor(db.Model):
    __tablename__ = 'professor'
    id_professor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(100), default='')
    materia_especialidade = db.Column(db.String(80), default='')
    foto = db.Column(db.String(255), default='default_avatar.png')

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Ativo')
    id_aluno = db.Column(db.Integer, db.ForeignKey('aluno.id_aluno'), nullable=True)
    id_professor = db.Column(db.Integer, db.ForeignKey('professor.id_professor'), nullable=True)

    aluno = db.relationship('Aluno', backref='usuario', uselist=False)
    professor = db.relationship('Professor', backref='usuario', uselist=False)

class Conteudo(db.Model):
    __tablename__ = 'conteudo'
    id_conteudo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_professor = db.Column(db.Integer, db.ForeignKey('professor.id_professor'), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    materia = db.Column(db.String(80), nullable=False)
    tema = db.Column(db.String(100), nullable=False)
    tipo_conteudo = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.Text)
    arquivo = db.Column(db.String(255))
    link = db.Column(db.String(255))
    categoria = db.Column(db.String(20), default='geral')
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)

    professor = db.relationship('Professor', backref='conteudos')

class Pergunta(db.Model):
    __tablename__ = 'pergunta'
    id_pergunta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_conteudo = db.Column(db.Integer, db.ForeignKey('conteudo.id_conteudo'), nullable=False)
    enunciado = db.Column(db.Text, nullable=False)
    opcao_a = db.Column(db.String(255), nullable=False)
    opcao_b = db.Column(db.String(255), nullable=False)
    opcao_c = db.Column(db.String(255), nullable=False)
    opcao_d = db.Column(db.String(255), nullable=False)
    resposta_correta = db.Column(db.String(1), nullable=False)
    pontos = db.Column(db.Integer, default=10)

    conteudo = db.relationship('Conteudo', backref='perguntas')

class ResultadoLicao(db.Model):
    __tablename__ = 'resultado_licao'
    id_resultado = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_aluno = db.Column(db.Integer, db.ForeignKey('aluno.id_aluno'), nullable=False)
    id_conteudo = db.Column(db.Integer, db.ForeignKey('conteudo.id_conteudo'), nullable=False)
    pontos_ganhos = db.Column(db.Integer, default=0)
    total_acertos = db.Column(db.Integer, default=0)
    total_perguntas = db.Column(db.Integer, default=0)
    data_conclusao = db.Column(db.DateTime, default=datetime.utcnow)

    aluno = db.relationship('Aluno', backref='resultados_licoes')
    conteudo = db.relationship('Conteudo', backref='resultados')

class Mensagem(db.Model):
    __tablename__ = 'mensagem'
    id_mensagem = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_aluno = db.Column(db.Integer, db.ForeignKey('aluno.id_aluno'), nullable=False)
    id_professor = db.Column(db.Integer, db.ForeignKey('professor.id_professor'), nullable=True)
    tipo = db.Column(db.String(20), nullable=False)
    assunto = db.Column(db.String(150), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    resposta = db.Column(db.Text, nullable=True)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)

    aluno = db.relationship('Aluno', backref='mensagens')
    professor = db.relationship('Professor', backref='mensagens')

class AcessoMateria(db.Model):
    __tablename__ = 'acesso_materia'
    id_acesso = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_aluno = db.Column(db.Integer, db.ForeignKey('aluno.id_aluno'), nullable=False)
    materia = db.Column(db.String(80), nullable=False)
    qtd_acessos = db.Column(db.Integer, default=1)

    aluno = db.relationship('Aluno', backref='acessos_materias')


# --- CÁLCULO DE STREAK E PONTUAÇÃO DIÁRIA ---
def atualizar_streak_aluno(aluno):
    if not aluno:
        return

    agora = datetime.utcnow()

    if not aluno.data_ultimo_acesso:
        aluno.sequencia_dias = 1
        aluno.pontos = (aluno.pontos or 0) + 10
        aluno.data_ultimo_acesso = agora
        db.session.commit()
        return

    data_ultimo = aluno.data_ultimo_acesso.date()
    data_atual = agora.date()
    diferenca_dias = (data_atual - data_ultimo).days

    if diferenca_dias == 1:
        aluno.sequencia_dias = (aluno.sequencia_dias or 0) + 1
        pontos_ganhos = 10 + (aluno.sequencia_dias * 5)
        aluno.pontos = (aluno.pontos or 0) + pontos_ganhos
        aluno.data_ultimo_acesso = agora
        db.session.commit()
    elif diferenca_dias > 1:
        aluno.sequencia_dias = 1
        aluno.pontos = (aluno.pontos or 0) + 10
        aluno.data_ultimo_acesso = agora
        db.session.commit()


# --- CONTEXTO GLOBAL DO USUÁRIO & RANKING ---
def obter_contexto_usuario():
    usuario_logado = None
    professores = []
    mensagens = []
    
    if 'usuario_id' in session:
        usuario_logado = Usuario.query.get(session['usuario_id'])
        if usuario_logado:
            if usuario_logado.perfil == 'aluno' and usuario_logado.aluno:
                atualizar_streak_aluno(usuario_logado.aluno)

            professores = Professor.query.all()
            if usuario_logado.perfil == 'admin':
                mensagens = Mensagem.query.order_by(Mensagem.data_envio.desc()).all()
            elif usuario_logado.perfil == 'aluno' and usuario_logado.id_aluno:
                mensagens = Mensagem.query.filter_by(id_aluno=usuario_logado.id_aluno).order_by(Mensagem.data_envio.desc()).all()
            elif usuario_logado.perfil == 'professor' and usuario_logado.id_professor:
                mensagens = Mensagem.query.filter_by(id_professor=usuario_logado.id_professor).order_by(Mensagem.data_envio.desc()).all()
    
    ranking_alunos = Aluno.query.order_by(Aluno.pontos.desc()).limit(50).all()

    return usuario_logado, professores, mensagens, ranking_alunos


def consultar_conteudos_por_categoria(categoria):
    """Retorna os conteúdos da categoria pedida ('geral' ou 'enem').
    Conteúdos antigos (categoria nula) contam como 'geral'."""
    query = Conteudo.query
    if categoria == 'enem':
        query = query.filter(Conteudo.categoria == 'enem')
    else:
        query = query.filter(or_(Conteudo.categoria == 'geral', Conteudo.categoria.is_(None)))
    return query.order_by(Conteudo.data_publicacao.desc()).all()


# --- ROTAS PRINCIPAIS ---

@app.route('/')
def index():
    usuario_logado, professores, mensagens, ranking = obter_contexto_usuario()
    return render_template('index.html', materias=MATERIAS, usuario=usuario_logado, professores=professores, mensagens=mensagens, ranking=ranking)


@app.route('/conteudos')
def conteudos():
    usuario_logado, professores, mensagens_lista, ranking = obter_contexto_usuario()
    todos_conteudos = consultar_conteudos_por_categoria('geral')
    return render_template('conteudos.html', materias=MATERIAS, conteudos=todos_conteudos, categoria='geral', usuario=usuario_logado, professores=professores, mensagens_lista=mensagens_lista, ranking=ranking)


@app.route('/conteudos/enem')
def conteudos_enem():
    usuario_logado, professores, mensagens_lista, ranking = obter_contexto_usuario()
    conteudos_enem_lista = consultar_conteudos_por_categoria('enem')
    return render_template('conteudos.html', materias=MATERIAS, conteudos=conteudos_enem_lista, categoria='enem', usuario=usuario_logado, professores=professores, mensagens_lista=mensagens_lista, ranking=ranking)


@app.route('/ranking')
def ranking():
    usuario_logado, professores, mensagens_lista, ranking_alunos = obter_contexto_usuario()
    return render_template('ranking.html', materias=MATERIAS, usuario=usuario_logado, professores=professores, mensagens_lista=mensagens_lista, ranking=ranking_alunos)


@app.route('/professores')
def professores():
    if session.get('usuario_perfil') == 'aluno':
        return redirect(url_for('index'))

    usuario_logado, professores_lista, mensagens_lista, ranking = obter_contexto_usuario()
    return render_template('professores.html', materias=MATERIAS, usuario=usuario_logado, professores=professores_lista, mensagens=mensagens_lista, ranking=ranking)


@app.route('/conquistas')
def conquistas():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    usuario_logado, professores, mensagens_lista, ranking = obter_contexto_usuario()
    return render_template('conquistas.html', materias=MATERIAS, usuario=usuario_logado, professores=professores, mensagens_lista=mensagens_lista)


@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    usuario_logado, professores, mensagens_lista, ranking = obter_contexto_usuario()

    if request.method == 'POST':
        novo_nome = request.form.get('nome', '').strip()
        
        nome_arquivo = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '':
                extensao = file.filename.rsplit('.', 1)[-1].lower()
                if extensao in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    nome_arquivo = secure_filename(f"avatar_{usuario_logado.id_usuario}_{int(datetime.utcnow().timestamp())}.{extensao}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))

        if usuario_logado.aluno:
            if novo_nome:
                usuario_logado.aluno.nome = novo_nome
            if nome_arquivo:
                usuario_logado.aluno.foto = nome_arquivo

            moldura_escolhida = request.form.get('moldura_equipada')
            if moldura_escolhida in PATENTES_INFO:
                if (usuario_logado.aluno.pontos or 0) >= PATENTES_INFO[moldura_escolhida]["min_pontos"]:
                    usuario_logado.aluno.moldura_equipada = moldura_escolhida

        elif usuario_logado.professor:
            if novo_nome:
                usuario_logado.professor.nome = novo_nome
            if nome_arquivo:
                usuario_logado.professor.foto = nome_arquivo

        db.session.commit()
        return redirect(url_for('perfil'))

    return render_template('perfil.html', materias=MATERIAS, usuario=usuario_logado, professores=professores, mensagens=mensagens_lista)


# --- ROTAS DE GERENCIAMENTO E EDIÇÃO DE LIÇÕES ---

@app.route('/api/conteudo/<int:id_conteudo>/perguntas')
def listar_perguntas_conteudo(id_conteudo):
    if 'usuario_id' not in session or session.get('usuario_perfil') not in ['professor', 'admin']:
        return jsonify([]), 403

    perguntas = Pergunta.query.filter_by(id_conteudo=id_conteudo).all()
    lista = [{
        'id_pergunta': p.id_pergunta,
        'enunciado': p.enunciado,
        'opcao_a': p.opcao_a,
        'opcao_b': p.opcao_b,
        'opcao_c': p.opcao_c,
        'opcao_d': p.opcao_d,
        'resposta_correta': p.resposta_correta,
        'pontos': p.pontos
    } for p in perguntas]

    return jsonify(lista)


@app.route('/professor/conteudo/<int:id_conteudo>/pergunta/nova', methods=['POST'])
def adicionar_pergunta(id_conteudo):
    if 'usuario_id' not in session or session.get('usuario_perfil') not in ['professor', 'admin']:
        return jsonify({"status": "error", "message": "Acesso não autorizado."}), 403

    conteudo = Conteudo.query.get_or_404(id_conteudo)
    data = request.get_json() if request.is_json else request.form

    enunciado = data.get('enunciado', '').strip()
    opcao_a = data.get('opcao_a', '').strip()
    opcao_b = data.get('opcao_b', '').strip()
    opcao_c = data.get('opcao_c', '').strip()
    opcao_d = data.get('opcao_d', '').strip()
    resposta_correta = data.get('resposta_correta', '').strip().upper()
    pontos = int(data.get('pontos', 10))

    if not all([enunciado, opcao_a, opcao_b, opcao_c, opcao_d, resposta_correta]):
        return jsonify({"status": "error", "message": "Preencha todos os campos da pergunta."}), 400

    nova_pergunta = Pergunta(
        id_conteudo=id_conteudo,
        enunciado=enunciado,
        opcao_a=opcao_a,
        opcao_b=opcao_b,
        opcao_c=opcao_c,
        opcao_d=opcao_d,
        resposta_correta=resposta_correta,
        pontos=pontos
    )
    db.session.add(nova_pergunta)
    db.session.commit()

    return jsonify({"status": "success", "message": "Pergunta adicionada com sucesso!"})


@app.route('/professor/pergunta/editar/<int:id_pergunta>', methods=['POST'])
def editar_pergunta(id_pergunta):
    if 'usuario_id' not in session or session.get('usuario_perfil') not in ['professor', 'admin']:
        return jsonify({"status": "error", "message": "Acesso não autorizado."}), 403

    pergunta = Pergunta.query.get_or_404(id_pergunta)
    data = request.get_json() if request.is_json else request.form

    enunciado = data.get('enunciado', '').strip()
    opcao_a = data.get('opcao_a', '').strip()
    opcao_b = data.get('opcao_b', '').strip()
    opcao_c = data.get('opcao_c', '').strip()
    opcao_d = data.get('opcao_d', '').strip()
    resposta_correta = data.get('resposta_correta', '').strip().upper()
    pontos = int(data.get('pontos', 10))

    if not all([enunciado, opcao_a, opcao_b, opcao_c, opcao_d, resposta_correta]):
        return jsonify({"status": "error", "message": "Preencha todos os campos da pergunta."}), 400

    pergunta.enunciado = enunciado
    pergunta.opcao_a = opcao_a
    pergunta.opcao_b = opcao_b
    pergunta.opcao_c = opcao_c
    pergunta.opcao_d = opcao_d
    pergunta.resposta_correta = resposta_correta
    pergunta.pontos = pontos

    db.session.commit()

    return jsonify({"status": "success", "message": "Pergunta editada e atualizada com sucesso!"})


@app.route('/professor/pergunta/excluir/<int:id_pergunta>', methods=['POST'])
def excluir_pergunta(id_pergunta):
    if 'usuario_id' not in session or session.get('usuario_perfil') not in ['professor', 'admin']:
        return jsonify({"status": "error", "message": "Acesso não autorizado."}), 403

    pergunta = Pergunta.query.get_or_404(id_pergunta)
    db.session.delete(pergunta)
    db.session.commit()

    return jsonify({"status": "success", "message": "Pergunta excluída com sucesso!"})


@app.route('/licao/<int:id_conteudo>')
def fazer_licao(id_conteudo):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    usuario_logado, professores, mensagens, ranking = obter_contexto_usuario()

    if usuario_logado and usuario_logado.perfil in ['professor', 'admin']:
        return redirect(url_for('conteudos'))

    conteudo = Conteudo.query.get_or_404(id_conteudo)
    perguntas = Pergunta.query.filter_by(id_conteudo=id_conteudo).all()

    if not perguntas:
        return redirect(url_for('conteudos'))

    return render_template('licao.html', materias=MATERIAS, usuario=usuario_logado, conteudo=conteudo, perguntas=perguntas, resultado=None)


@app.route('/licao/submeter/<int:id_conteudo>', methods=['POST'])
def submeter_licao(id_conteudo):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    usuario_logado, professores, mensagens, ranking = obter_contexto_usuario()
    if usuario_logado.perfil != 'aluno' or not usuario_logado.aluno:
        return redirect(url_for('conteudos'))

    conteudo = Conteudo.query.get_or_404(id_conteudo)
    perguntas = Pergunta.query.filter_by(id_conteudo=id_conteudo).all()

    total_acertos = 0
    pontos_ganhos = 0
    detalhes_respostas = []

    for idx, p in enumerate(perguntas, 1):
        campo_resposta = f"pergunta_{p.id_pergunta}"
        resposta_usuario = request.form.get(campo_resposta, '').upper()
        acertou = (resposta_usuario == p.resposta_correta)

        if acertou:
            total_acertos += 1
            pontos_ganhos += p.pontos

        detalhes_respostas.append({
            "numero": idx,
            "enunciado": p.enunciado,
            "opcao_a": p.opcao_a,
            "opcao_b": p.opcao_b,
            "opcao_c": p.opcao_c,
            "opcao_d": p.opcao_d,
            "resposta_correta": p.resposta_correta,
            "resposta_usuario": resposta_usuario,
            "acertou": acertou,
            "pontos": p.pontos if acertou else 0
        })

    usuario_logado.aluno.pontos = (usuario_logado.aluno.pontos or 0) + pontos_ganhos

    resultado_reg = ResultadoLicao(
        id_aluno=usuario_logado.aluno.id_aluno,
        id_conteudo=id_conteudo,
        pontos_ganhos=pontos_ganhos,
        total_acertos=total_acertos,
        total_perguntas=len(perguntas)
    )
    db.session.add(resultado_reg)
    db.session.commit()

    resultado_resumo = {
        "total_perguntas": len(perguntas),
        "total_acertos": total_acertos,
        "total_erros": len(perguntas) - total_acertos,
        "pontos_ganhos": pontos_ganhos,
        "aproveitamento_pct": int((total_acertos / len(perguntas)) * 100) if perguntas else 0,
        "detalhes": detalhes_respostas
    }

    return render_template('licao.html', materias=MATERIAS, usuario=usuario_logado, conteudo=conteudo, perguntas=perguntas, resultado=resultado_resumo)


@app.route('/admin/usuarios')
def listar_usuarios():
    if 'usuario_id' not in session or session.get('usuario_perfil') != 'admin':
        return redirect(url_for('index'))

    usuario_logado, professores, mensagens_lista, ranking = obter_contexto_usuario()
    todos_usuarios = Usuario.query.order_by(Usuario.id_usuario.asc()).all()

    return render_template('usuarios.html', materias=MATERIAS, usuario=usuario_logado, professores=professores, mensagens_lista=mensagens_lista, usuarios_lista=todos_usuarios)


@app.route('/diagnostico')
@app.route('/diagnostico/<int:id_aluno>')
def diagnostico(id_aluno=None):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    usuario_logado, professores, mensagens_lista, ranking = obter_contexto_usuario()

    if usuario_logado.perfil == 'aluno':
        if not usuario_logado.aluno:
            return redirect(url_for('index'))
        aluno_alvo = usuario_logado.aluno
    else:
        if id_aluno:
            aluno_alvo = Aluno.query.get(id_aluno)
        else:
            aluno_alvo = Aluno.query.first()

    if not aluno_alvo:
        return render_template('diagnostico.html', materias=MATERIAS, usuario=usuario_logado, aluno_alvo=None, todos_alunos=[], labels=[], valores=[])

    todos_alunos = Aluno.query.order_by(Aluno.nome.asc()).all() if usuario_logado.perfil in ['professor', 'admin'] else []

    acessos = AcessoMateria.query.filter_by(id_aluno=aluno_alvo.id_aluno).all()
    dados_map = {a.materia: a.qtd_acessos for a in acessos}

    labels = list(MATERIAS.values())
    valores = [dados_map.get(m, 0) for m in labels]

    return render_template(
        'diagnostico.html',
        materias=MATERIAS,
        usuario=usuario_logado,
        aluno_alvo=aluno_alvo,
        todos_alunos=todos_alunos,
        labels=labels,
        valores=valores
    )


@app.route('/admin/reset_diagnostico/<int:id_aluno>', methods=['POST'])
@app.route('/diagnostico/reset/<int:id_aluno>', methods=['POST'])
def reset_diagnostico_aluno(id_aluno):
    if 'usuario_id' not in session:
        return jsonify({"status": "error", "message": "Acesso não autorizado."}), 403

    usuario = Usuario.query.get(session['usuario_id'])
    is_admin = usuario.perfil == 'admin'
    is_proprio_aluno = usuario.perfil == 'aluno' and usuario.id_aluno == id_aluno

    if not (is_admin or is_proprio_aluno):
        return jsonify({"status": "error", "message": "Permissão negada."}), 403

    AcessoMateria.query.filter_by(id_aluno=id_aluno).delete()
    db.session.commit()

    return jsonify({"status": "success", "message": "Gráfico de diagnóstico resetado com sucesso!"})


@app.route('/diagnostico/reset_materia/<int:id_aluno>', methods=['POST'])
def reset_materia_diagnostico(id_aluno):
    if 'usuario_id' not in session:
        return jsonify({"status": "error", "message": "Acesso não autorizado."}), 403

    usuario = Usuario.query.get(session['usuario_id'])
    is_admin = usuario.perfil == 'admin'
    is_proprio_aluno = usuario.perfil == 'aluno' and usuario.id_aluno == id_aluno

    if not (is_admin or is_proprio_aluno):
        return jsonify({"status": "error", "message": "Permissão negada."}), 403

    data = request.get_json() if request.is_json else request.form
    nome_materia = data.get('materia')

    if not nome_materia:
        return jsonify({"status": "error", "message": "Matéria não selecionada."}), 400

    AcessoMateria.query.filter_by(id_aluno=id_aluno, materia=nome_materia).delete()
    db.session.commit()

    return jsonify({"status": "success", "message": f"Acessos da matéria '{nome_materia}' foram resetados!"})


@app.route('/conteudo/acessar/<int:id_conteudo>')
def acessar_conteudo(id_conteudo):
    conteudo = Conteudo.query.get_or_404(id_conteudo)

    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        if usuario and usuario.perfil == 'aluno' and usuario.aluno:
            acesso = AcessoMateria.query.filter_by(
                id_aluno=usuario.aluno.id_aluno,
                materia=conteudo.materia
            ).first()
            if acesso:
                acesso.qtd_acessos += 1
            else:
                acesso = AcessoMateria(
                    id_aluno=usuario.aluno.id_aluno,
                    materia=conteudo.materia,
                    qtd_acessos=1
                )
                db.session.add(acesso)
            db.session.commit()

    if conteudo.link:
        return redirect(conteudo.link)
    elif conteudo.arquivo:
        return redirect(url_for('static', filename='uploads/' + conteudo.arquivo))

    return redirect(url_for('conteudos'))


@app.route('/materia/<slug>')
def ver_materia(slug):
    nome_materia = MATERIAS.get(slug)
    if not nome_materia:
        return redirect(url_for('index'))

    usuario_logado, professores, mensagens, ranking = obter_contexto_usuario()
    conteudos_materia = Conteudo.query.filter(
        Conteudo.materia.ilike(nome_materia),
        or_(Conteudo.categoria == 'geral', Conteudo.categoria.is_(None))
    ).order_by(Conteudo.data_publicacao.desc()).all()

    return render_template('materia.html', materia_nome=nome_materia, conteudos=conteudos_materia, usuario=usuario_logado, professores=professores, mensagens=mensagens, ranking=ranking)


@app.route('/mensagens')
def mensagens():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    
    usuario_logado, professores, mensagens_lista, ranking = obter_contexto_usuario()
    return render_template('mensagens.html', materias=MATERIAS, usuario=usuario_logado, professores=professores, mensagens=mensagens_lista)


@app.route('/cadastro', methods=['GET', 'POST'])
@app.route('/cadastrar', methods=['POST'])
def cadastro():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        nome = data.get('nome', '').strip()
        email = data.get('email', '').strip()
        senha = data.get('senha', '')
        perfil = data.get('perfil', 'aluno')

        if not email or not senha or not nome:
            msg = "Preencha todos os campos obrigatórios."
            return jsonify({"status": "error", "message": msg}), 400 if request.is_json else render_template('index.html', erro_cadastro=msg, materias=MATERIAS)

        if Usuario.query.filter_by(email=email).first():
            msg = "Este e-mail já está cadastrado."
            return jsonify({"status": "error", "message": msg}), 400 if request.is_json else render_template('index.html', erro_cadastro=msg, materias=MATERIAS)

        senha_hash = generate_password_hash(senha)

        if perfil == 'professor':
            novo_prof = Professor(nome=nome, telefone='', materia_especialidade='', foto='default_avatar.png')
            db.session.add(novo_prof)
            db.session.commit()
            novo_usuario = Usuario(email=email, senha=senha_hash, perfil='professor', status='Ativo', id_professor=novo_prof.id_professor)
        else:
            novo_aluno = Aluno(nome=nome, pontos=10, sequencia_dias=1, data_ultimo_acesso=datetime.utcnow(), foto='default_avatar.png', moldura_equipada='auto')
            db.session.add(novo_aluno)
            db.session.commit()
            novo_usuario = Usuario(email=email, senha=senha_hash, perfil='aluno', status='Ativo', id_aluno=novo_aluno.id_aluno)

        db.session.add(novo_usuario)
        db.session.commit()

        session['usuario_id'] = novo_usuario.id_usuario
        session['usuario_perfil'] = novo_usuario.perfil

        if request.is_json:
            return jsonify({"status": "success", "message": "Conta criada com sucesso!"})
        return redirect(url_for('index'))

    return render_template('index.html', materias=MATERIAS)


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() if request.is_json else request.form
    email = data.get('email', '').strip()
    senha = data.get('senha', '')

    usuario = Usuario.query.filter_by(email=email).first()

    if usuario and (check_password_hash(usuario.senha, senha) or usuario.senha == senha):
        session['usuario_id'] = usuario.id_usuario
        session['usuario_perfil'] = usuario.perfil
        
        if request.is_json:
            return jsonify({"status": "success", "message": "Login realizado com sucesso!", "perfil": usuario.perfil})
        return redirect(url_for('index'))

    if request.is_json:
        return jsonify({"status": "error", "message": "E-mail ou senha incorretos."}), 401
    return render_template('index.html', erro_login="E-mail ou senha incorretos.", materias=MATERIAS)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/enviar_mensagem', methods=['POST'])
def enviar_mensagem():
    if 'usuario_id' not in session:
        return jsonify({"status": "error", "message": "Acesso não autorizado."}), 403

    usuario = Usuario.query.get(session['usuario_id'])
    data = request.get_json() if request.is_json else request.form

    id_prof = data.get('id_professor')
    id_aluno_envio = usuario.id_aluno if usuario.id_aluno else 1

    nova_msg = Mensagem(
        id_aluno=id_aluno_envio,
        id_professor=int(id_prof) if id_prof else None,
        tipo=data.get('tipo', 'duvida'),
        assunto=data.get('assunto', '').strip(),
        conteudo=data.get('conteudo', '').strip()
    )
    db.session.add(nova_msg)

    if usuario.aluno:
        usuario.aluno.pontos = (usuario.aluno.pontos or 0) + 5

    db.session.commit()

    return jsonify({"status": "success", "message": "Mensagem enviada com sucesso! Você ganhou +5 pontos."})


@app.route('/professor/responder_mensagem/<int:id_mensagem>', methods=['POST'])
def responder_mensagem(id_mensagem):
    if 'usuario_id' not in session or session.get('usuario_perfil') not in ['professor', 'admin']:
        return jsonify({"status": "error", "message": "Acesso não autorizado."}), 403

    data = request.get_json() if request.is_json else request.form
    msg = Mensagem.query.get_or_404(id_mensagem)
    msg.resposta = data.get('resposta', '').strip()
    db.session.commit()

    return jsonify({"status": "success", "message": "Resposta enviada!"})


@app.route('/mensagem/excluir/<int:id_mensagem>', methods=['POST'])
def excluir_mensagem(id_mensagem):
    if 'usuario_id' not in session:
        return jsonify({"status": "error", "message": "Acesso negado."}), 403

    usuario = Usuario.query.get(session['usuario_id'])
    msg = Mensagem.query.get_or_404(id_mensagem)

    is_admin = usuario.perfil == 'admin'
    is_aluno_autor = usuario.perfil == 'aluno' and usuario.id_aluno == msg.id_aluno
    is_prof_destinatario = usuario.perfil == 'professor' and usuario.id_professor == msg.id_professor

    if not (is_admin or is_aluno_autor or is_prof_destinatario):
        return jsonify({"status": "error", "message": "Permissão negada."}), 403

    db.session.delete(msg)
    db.session.commit()

    return jsonify({"status": "success", "message": "Mensagem excluída!"})


@app.route('/professor/conteudo/novo', methods=['POST'])
def criar_conteudo():
    if 'usuario_id' not in session or session.get('usuario_perfil') not in ['professor', 'admin']:
        return jsonify({"status": "error", "message": "Acesso não autorizado."}), 403

    usuario = Usuario.query.get(session['usuario_id'])
    data = request.get_json() if request.is_json else request.form

    id_prof = usuario.id_professor
    if usuario.perfil == 'admin':
        id_prof = data.get('id_professor')
        if not id_prof:
            primeiro_prof = Professor.query.first()
            id_prof = primeiro_prof.id_professor if primeiro_prof else None

    if not id_prof:
        return jsonify({"status": "error", "message": "Nenhum professor disponível."}), 400

    categoria = data.get('categoria', 'geral')
    if categoria not in CATEGORIAS_CONTEUDO:
        categoria = 'geral'

    novo_conteudo = Conteudo(
        id_professor=id_prof,
        titulo=data.get('titulo'),
        materia=data.get('materia'),
        tema=data.get('tema'),
        tipo_conteudo=data.get('tipo_conteudo', 'PDF'),
        descricao=data.get('descricao', ''),
        link=data.get('link', ''),
        categoria=categoria
    )
    db.session.add(novo_conteudo)
    db.session.commit()

    return jsonify({"status": "success", "message": "Material publicado!"})


def abrir_navegador():
    webbrowser.open_new('http://127.0.0.1:5000/')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE aluno ADD COLUMN pontos INTEGER DEFAULT 10"))
                conn.commit()
        except Exception:
            pass

        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE aluno ADD COLUMN sequencia_dias INTEGER DEFAULT 1"))
                conn.commit()
        except Exception:
            pass

        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE aluno ADD COLUMN foto VARCHAR(255) DEFAULT 'default_avatar.png'"))
                conn.commit()
        except Exception:
            pass

        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE aluno ADD COLUMN moldura_equipada VARCHAR(50) DEFAULT 'auto'"))
                conn.commit()
        except Exception:
            pass

        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE professor ADD COLUMN foto VARCHAR(255) DEFAULT 'default_avatar.png'"))
                conn.commit()
        except Exception:
            pass

        # Nova coluna: separa conteúdos gerais dos conteúdos do ENEM
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE conteudo ADD COLUMN categoria VARCHAR(20) DEFAULT 'geral'"))
                conn.commit()
        except Exception:
            pass

        if not Usuario.query.filter_by(perfil='admin').first():
            db.session.add(Usuario(
                email='admin@proestudos.com',
                senha=generate_password_hash('admin123'),
                perfil='admin',
                status='Ativo'
            ))
            db.session.commit()


    threading.Timer(1.5, abrir_navegador).start()
    app.run(debug=True)