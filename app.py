from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import webbrowser
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_pro_estudos_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ProEstudo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

MATERIAS = {
    'matematica': 'Matemática',
    'portugues': 'Português',
    'historia': 'História',
    'geografia': 'Geografia',
    'computacao': 'Ciências da Computação'
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

class Professor(db.Model):
    __tablename__ = 'professor'
    id_professor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(100), default='')
    materia_especialidade = db.Column(db.String(80), default='')

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
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)

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


# --- CÁLCULO DE STREAK E PONTUAÇÃO DIÁRIA ---
def atualizar_streak_aluno(aluno):
    if not aluno:
        return
    
    hoje = datetime.utcnow().date()
    
    if aluno.data_ultimo_acesso:
        ultimo_acesso = aluno.data_ultimo_acesso.date()
        diferenca_dias = (hoje - ultimo_acesso).days

        if diferenca_dias == 1:
            aluno.sequencia_dias = (aluno.sequencia_dias or 0) + 1
            ganho = 10 + (aluno.sequencia_dias * 5)
            aluno.pontos = (aluno.pontos or 0) + ganho
            aluno.data_ultimo_acesso = datetime.utcnow()
            db.session.commit()
        elif diferenca_dias > 1:
            aluno.sequencia_dias = 1
            aluno.pontos = (aluno.pontos or 0) + 10
            aluno.data_ultimo_acesso = datetime.utcnow()
            db.session.commit()
    else:
        aluno.sequencia_dias = 1
        aluno.pontos = 10
        aluno.data_ultimo_acesso = datetime.utcnow()
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
    
    ranking_alunos = Aluno.query.order_by(Aluno.pontos.desc()).limit(10).all()

    return usuario_logado, professores, mensagens, ranking_alunos


# --- ROTAS PRINCIPAIS (TELA A TELA) ---

@app.route('/')
def index():
    usuario_logado, professores, mensagens, ranking = obter_contexto_usuario()
    return render_template('index.html', materias=MATERIAS, usuario=usuario_logado, professores=professores, mensagens=mensagens, ranking=ranking)


@app.route('/conteudos')
def conteudos():
    usuario_logado, professores, mensagens, ranking = obter_contexto_usuario()
    todos_conteudos = Conteudo.query.order_by(Conteudo.data_publicacao.desc()).all()
    return render_template('conteudos.html', materias=MATERIAS, conteudos=todos_conteudos, usuario=usuario_logado, professores=professores, mensagens=mensagens)


@app.route('/ranking')
def ver_ranking():
    usuario_logado, professores, mensagens, ranking = obter_contexto_usuario()
    return render_template('ranking.html', usuario=usuario_logado, ranking=ranking, professores=professores, mensagens=mensagens)


@app.route('/professores')
def para_professores():
    usuario_logado, professores, mensagens, ranking = obter_contexto_usuario()
    return render_template('professores.html', usuario=usuario_logado, professores=professores, mensagens=mensagens)


@app.route('/mensagens')
def mensagens():
    usuario_logado, professores, mensagens_lista, ranking = obter_contexto_usuario()
    return render_template('mensagens.html', materias=MATERIAS, usuario=usuario_logado, professores=professores, mensagens=mensagens_lista)


@app.route('/materia/<slug>')
def ver_materia(slug):
    nome_materia = MATERIAS.get(slug)
    if not nome_materia:
        return redirect(url_for('index'))

    conteudos_materia = Conteudo.query.filter(Conteudo.materia.ilike(nome_materia)).all()
    usuario_logado, professores, mensagens_lista, ranking = obter_contexto_usuario()

    return render_template('materia.html', materia_nome=nome_materia, conteudos=conteudos_materia, usuario=usuario_logado, professores=professores, mensagens=mensagens_lista)


# --- ROTAS DE AUTENTICAÇÃO E AÇÕES ---

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
            novo_prof = Professor(nome=nome, telefone='', materia_especialidade='')
            db.session.add(novo_prof)
            db.session.commit()
            novo_usuario = Usuario(email=email, senha=senha_hash, perfil='professor', status='Ativo', id_professor=novo_prof.id_professor)
        else:
            novo_aluno = Aluno(nome=nome, pontos=10, sequencia_dias=1)
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

    novo_conteudo = Conteudo(
        id_professor=id_prof,
        titulo=data.get('titulo'),
        materia=data.get('materia'),
        tema=data.get('tema'),
        tipo_conteudo=data.get('tipo_conteudo', 'PDF'),
        descricao=data.get('descricao', ''),
        link=data.get('link', '')
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
                conn.execute(db.text("ALTER TABLE aluno ADD COLUMN sequencia_dias INTEGER DEFAULT 1"))
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