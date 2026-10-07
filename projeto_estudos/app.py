from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = "projeto_estudos"

def conectar():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/")
def index():
    if "id_usuario" not in session:
        return redirect("/login")
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        
        return render_template(
            "index.html",
            
        )
    except Exception as erro:
        flash(f"Erro ao carregar página inicial: {erro}", "erro")
        return render_template(
            "index.html",
            total_alunos=0,
            total_livros=0,
            total_disponiveis=0,
            total_emprestimos=0
        )

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login/autenticar", methods=["POST"])
def autenticar():
    login_usuario = request.form["email"]
    senha = request.form["senha"]
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        sql = """
            SELECT *
            FROM usuario
            WHERE email = %s
              AND senha = %s
              AND status = 'Ativo'
        """
        cursor.execute(sql, (login_usuario, senha))
        usuario = cursor.fetchone()
        cursor.close()
        conexao.close()
        
        if usuario:
            session["id_usuario"] = usuario["id_usuario"]
            session["nome"] = usuario["nome"]
            session["perfil"] = usuario["perfil"]
            flash("Login realizado com sucesso!", "sucesso")
            return redirect("/")
        else:
            flash("Login ou senha inválidos.", "erro")
            return redirect("/login")
    except Exception as erro:
        flash(f"Erro ao realizar login: {erro}", "erro")
        return redirect("/login")

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "sucesso")
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)