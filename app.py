from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_pro_estudos_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pro_estudos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo do Usuário no Banco de Dados
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    perfil = db.Column(db.String(20), nullable=False) # 'aluno' ou 'professor'

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

# Cria o banco de dados e as tabelas ao iniciar
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    materias = [
        "Matemática", "Língua Portuguesa", "História", "Geografia",
        "Biologia", "Física", "Química", "Redação",
        "Inglês e Espanhol", "Informática Básica", "Cursos Livres"
    ]
    
    usuario_logado = None
    if 'usuario_id' in session:
        usuario_logado = Usuario.query.get(session['usuario_id'])

    return render_template('index.html', materias=materias, usuario=usuario_logado)

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    data = request.get_json()
    nome = data.get('nome', '').strip()
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '')
    perfil = data.get('perfil', 'aluno')

    if not nome or not email or not senha:
        return jsonify({"status": "error", "message": "Preencha todos os campos obrigatórios."}), 400

    if Usuario.query.filter_by(email=email).first():
        return jsonify({"status": "error", "message": "E-mail já cadastrado."}), 400

    novo_usuario = Usuario(nome=nome, email=email, perfil=perfil)
    novo_usuario.set_senha(senha)
    
    db.session.add(novo_usuario)
    db.session.commit()

    # Loga automaticamente após cadastrar
    session['usuario_id'] = novo_usuario.id
    session['usuario_nome'] = novo_usuario.nome

    return jsonify({
        "status": "success",
        "message": f"Conta criada com sucesso! Bem-vindo(a), {novo_usuario.nome}."
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '')

    usuario = Usuario.query.filter_by(email=email).first()

    if usuario and usuario.checar_senha(senha):
        session['usuario_id'] = usuario.id
        session['usuario_nome'] = usuario.nome
        session['usuario_perfil'] = usuario.perfil
        return jsonify({"status": "success", "message": f"Bem-vindo(a) de volta, {usuario.nome}!"})

    return jsonify({"status": "error", "message": "E-mail ou senha incorretos."}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)