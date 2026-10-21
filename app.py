from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_pro_estudos_2026'

# Para usar MySQL: 'mysql+pymysql://usuario:senha@localhost/ProEstudo'
# Para usar SQLite com o arquivo do seu banco:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ProEstudo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Mapeamento com URLs amigáveis
MATERIAS = {
    'matematica': 'Matemática',
    'portugues': 'Português',
    'historia': 'História',
    'geografia': 'Geografia',
    'computacao': 'Ciências da Computação'
}

# --- MODELOS REFLETINDO SEU DATABASE.SQL ---

class Aluno(db.Model):
    __tablename__ = 'aluno'
    id_aluno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    nivel_diagnostico = db.Column(db.String(50), default='Não realizado')
    data_ultimo_acesso = db.Column(db.DateTime)

class Professor(db.Model):
    __tablename__ = 'professor'
    id_professor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(100), nullable=False)
    materia_especialidade = db.Column(db.String(80))

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Ativo')
    id_aluno = db.Column(db.Integer, db.ForeignKey('aluno.id_aluno'))
    id_professor = db.Column(db.Integer, db.ForeignKey('professor.id_professor'))

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


# --- ROTAS ---

@app.route('/')
def index():
    usuario_logado = None
    if 'usuario_id' in session:
        usuario_logado = Usuario.query.get(session['usuario_id'])

    return render_template('index.html', materias=MATERIAS, usuario=usuario_logado)


@app.route('/materia/<slug>')
def ver_materia(slug):
    nome_materia = MATERIAS.get(slug)
    if not nome_materia:
        return redirect(url_for('index'))

    # Filtra os conteúdos pela coluna 'materia' do seu SQL
    conteudos = Conteudo.query.filter(Conteudo.materia.ilike(nome_materia)).all()

    usuario_logado = None
    if 'usuario_id' in session:
        usuario_logado = Usuario.query.get(session['usuario_id'])

    return render_template('materia.html', materia_nome=nome_materia, conteudos=conteudos, usuario=usuario_logado)


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    senha = data.get('senha', '')

    usuario = Usuario.query.filter_by(email=email, senha=senha).first()

    if usuario:
        session['usuario_id'] = usuario.id_usuario
        session['usuario_perfil'] = usuario.perfil
        return jsonify({"status": "success", "message": "Login realizado com sucesso!"})

    return jsonify({"status": "error", "message": "E-mail ou senha incorretos."}), 401


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria automaticamente todas as tabelas caso não existam
    app.run(debug=True)