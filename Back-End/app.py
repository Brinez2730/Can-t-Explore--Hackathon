from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "f93$1!oP#7wZ@2kLm*8rT4q%X9"


# 1. FUNÇÕES DE BANCO
def criar_banco():
    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()

    # Tabela de usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL,
        quant_publicacoes INTEGER DEFAULT 0,
        quant_favoritos INTEGER DEFAULT 0,
        quant_comentarios INTEGER DEFAULT 0,
        quant_curtidas INTEGER DEFAULT 0
    )
    """)

    # Tabela de publicações
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS publicacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_criador INTEGER NOT NULL,
        titulo TEXT NOT NULL,
        subtitulo TEXT,
        conteudo TEXT NOT NULL,
        fonte TEXT NOT NULL,
        cor_fonte TEXT DEFAULT '#000000',
        tamanho_fonte INTEGER DEFAULT 14,
        imagem TEXT,
        pdf TEXT,
        quant_caracteres INTEGER NOT NULL,
        quant_curtidas INTEGER DEFAULT 0,
        quant_favoritos INTEGER DEFAULT 0,
        quant_comentarios INTEGER DEFAULT 0,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_criador) REFERENCES usuarios (id)
    )
    """)

    conexao.commit()
    conexao.close()

def criar_tabela_interacoes():
    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS curtidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER NOT NULL,
        id_publicacao INTEGER NOT NULL,
        UNIQUE(id_usuario, id_publicacao),
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
        FOREIGN KEY (id_publicacao) REFERENCES publicacoes(id)
    )
    """)
    conexao.commit()
    conexao.close()

def criar_tabela_favoritos():
    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favoritos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER NOT NULL,
        id_publicacao INTEGER NOT NULL,
        UNIQUE(id_usuario, id_publicacao),
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
        FOREIGN KEY (id_publicacao) REFERENCES publicacoes(id)
    )
    """)
    conexao.commit()
    conexao.close()

def criar_tabela_comentarios():
    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comentarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER NOT NULL,
        id_publicacao INTEGER NOT NULL,
        conteudo TEXT NOT NULL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
        FOREIGN KEY (id_publicacao) REFERENCES publicacoes(id)
    )
    """)
    conexao.commit()
    conexao.close()

def criar_tabela_denuncias():
    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS denuncias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER NOT NULL,
        id_publicacao INTEGER NOT NULL,
        motivo TEXT NOT NULL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(id_usuario, id_publicacao),
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
        FOREIGN KEY (id_publicacao) REFERENCES publicacoes(id)
    )
    """)
    conexao.commit()
    conexao.close()

# Criar tabelas
criar_banco()
criar_tabela_interacoes()
criar_tabela_favoritos()
criar_tabela_comentarios()
criar_tabela_denuncias()

def atualizar_contador(campo, id_usuario):
    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute(f"UPDATE usuarios SET {campo} = {campo} + 1 WHERE id = ?", (id_usuario,))
    conexao.commit()
    conexao.close()

def get_db_connection():
    conexao = sqlite3.connect('banco_dados.db')
    conexao.row_factory = sqlite3.Row
    return conexao


# 2. ROTAS DE AUTENTICAÇÃO
@app.route('/')
def formulario():
    return render_template('cadastro.html')

@app.route('/salvar', methods=['POST'])
def salvar():
    nickname = request.form['nickname']
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    tipo = request.form['tipo']

    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    if cursor.fetchone():
        conexao.close()
        return f'Erro: já existe um usuário com o email {email}'

    cursor.execute("""
        INSERT INTO usuarios (nickname, nome, email, senha, tipo)
        VALUES (?, ?, ?, ?, ?)
    """, (nickname, nome, email, senha, tipo))
    conexao.commit()
    conexao.close()
    return f'Sua conta foi criada com sucesso, {nome}!'

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template("index.html")

    data = request.get_json()
    email = data.get("email")
    senha = data.get("senha")

    conexao = sqlite3.connect("banco_dados.db")
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
    usuario = cursor.fetchone()
    conexao.close()

    if usuario:
        session['usuario'] = {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "tipo": usuario["tipo"]
        }
        return jsonify({"status": "ok", "mensagem": f"Bem-vindo(a), {usuario['nome']}!"})
    else:
        return jsonify({"status": "erro", "mensagem": "E-mail ou senha incorretos!"}), 401

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login_page'))


# 3. PUBLICAÇÕES
@app.route('/publicar', methods=['GET', 'POST'])
def publicar():
    if request.method == 'POST':
        if 'usuario' not in session:
            return "Você precisa estar logado!", 403
        id_usuario = session['usuario']['id']

        titulo = request.form['titulo']
        subtitulo = request.form.get('subtitulo', '')
        conteudo = request.form['conteudo']
        fonte = request.form['fonte']
        cor_fonte = request.form.get('cor_fonte', '#000000')
        tamanho_fonte = int(request.form.get('tamanho_fonte', 14))

        conexao = get_db_connection()
        cursor = conexao.cursor()
        cursor.execute("SELECT tipo FROM usuarios WHERE id = ?", (id_usuario,))
        usuario = cursor.fetchone()

        if not usuario or usuario['tipo'] != 'criador':
            conexao.close()
            return "Apenas criadores podem publicar!", 403

        # Uploads (opcional)
        imagem = None
        if 'imagem' in request.files and request.files['imagem'].filename != '':
            img_file = request.files['imagem']
            imagem = secure_filename(img_file.filename)
            os.makedirs('static/uploads', exist_ok=True)
            img_file.save(os.path.join('static/uploads', imagem))

        pdf = None
        if 'pdf' in request.files and request.files['pdf'].filename != '':
            pdf_file = request.files['pdf']
            pdf = secure_filename(pdf_file.filename)
            os.makedirs('static/uploads', exist_ok=True)
            pdf_file.save(os.path.join('static/uploads', pdf))

        quant_caracteres = len(conteudo)
        cursor.execute("""
            INSERT INTO publicacoes (
                id_criador, titulo, subtitulo, conteudo, fonte, cor_fonte, tamanho_fonte, imagem, pdf, quant_caracteres
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_usuario, titulo, subtitulo, conteudo, fonte, cor_fonte, tamanho_fonte, imagem, pdf, quant_caracteres))

        conexao.commit()
        conexao.close()
        atualizar_contador("quant_publicacoes", id_usuario)
        return redirect(url_for('listar_publicacoes'))

    return render_template('publicar.html')

@app.route('/publicacoes')
def listar_publicacoes():
    conexao = get_db_connection()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT p.*, u.nome AS nome_criador
        FROM publicacoes p
        JOIN usuarios u ON p.id_criador = u.id
        ORDER BY data_criacao DESC
    """)
    publicacoes = cursor.fetchall()
    conexao.close()
    return render_template('publicacoes.html', publicacoes=publicacoes)


# 4. INTERAÇÕES (TODAS USANDO SESSÃO)

@app.route('/curtir/<int:id_publicacao>', methods=['POST'])
def curtir(id_publicacao):
    if 'usuario' not in session:
        return jsonify({"status": "erro", "mensagem": "Você precisa estar logado!"}), 403
    id_usuario = session['usuario']['id']

    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM curtidas WHERE id_usuario = ? AND id_publicacao = ?", (id_usuario, id_publicacao))
    if cursor.fetchone():
        conexao.close()
        return jsonify({"status": "erro", "mensagem": "Você já curtiu esta publicação!"}), 400

    cursor.execute("INSERT INTO curtidas (id_usuario, id_publicacao) VALUES (?, ?)", (id_usuario, id_publicacao))
    cursor.execute("UPDATE publicacoes SET quant_curtidas = quant_curtidas + 1 WHERE id = ?", (id_publicacao,))
    cursor.execute("""
        UPDATE usuarios SET quant_curtidas = quant_curtidas + 1
        WHERE id = (SELECT id_criador FROM publicacoes WHERE id = ?)
    """, (id_publicacao,))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "ok", "mensagem": "Curtida adicionada!"})

@app.route('/descurtir/<int:id_publicacao>', methods=['POST'])
def descurtir(id_publicacao):
    if 'usuario' not in session:
        return jsonify({"status": "erro", "mensagem": "Você precisa estar logado!"}), 403
    id_usuario = session['usuario']['id']

    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM curtidas WHERE id_usuario = ? AND id_publicacao = ?", (id_usuario, id_publicacao))
    if not cursor.fetchone():
        conexao.close()
        return jsonify({"status": "erro", "mensagem": "Você não curtiu esta publicação!"}), 400

    cursor.execute("DELETE FROM curtidas WHERE id_usuario = ? AND id_publicacao = ?", (id_usuario, id_publicacao))
    cursor.execute("UPDATE publicacoes SET quant_curtidas = quant_curtidas - 1 WHERE id = ?", (id_publicacao,))
    cursor.execute("""
        UPDATE usuarios SET quant_curtidas = quant_curtidas - 1
        WHERE id = (SELECT id_criador FROM publicacoes WHERE id = ?)
    """, (id_publicacao,))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "ok", "mensagem": "Curtida removida!"})

@app.route('/favoritar/<int:id_publicacao>', methods=['POST'])
def favoritar(id_publicacao):
    if 'usuario' not in session:
        return jsonify({"status": "erro", "mensagem": "Você precisa estar logado!"}), 403
    id_usuario = session['usuario']['id']

    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM favoritos WHERE id_usuario = ? AND id_publicacao = ?", (id_usuario, id_publicacao))
    if cursor.fetchone():
        conexao.close()
        return jsonify({"status": "erro", "mensagem": "Você já favoritou esta publicação!"}), 400

    cursor.execute("INSERT INTO favoritos (id_usuario, id_publicacao) VALUES (?, ?)", (id_usuario, id_publicacao))
    cursor.execute("UPDATE publicacoes SET quant_favoritos = quant_favoritos + 1 WHERE id = ?", (id_publicacao,))
    cursor.execute("""
        UPDATE usuarios SET quant_favoritos = quant_favoritos + 1
        WHERE id = (SELECT id_criador FROM publicacoes WHERE id = ?)
    """, (id_publicacao,))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "ok", "mensagem": "Publicação favoritada!"})

@app.route('/desfavoritar/<int:id_publicacao>', methods=['POST'])
def desfavoritar(id_publicacao):
    if 'usuario' not in session:
        return jsonify({"status": "erro", "mensagem": "Você precisa estar logado!"}), 403
    id_usuario = session['usuario']['id']

    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM favoritos WHERE id_usuario = ? AND id_publicacao = ?", (id_usuario, id_publicacao))
    if not cursor.fetchone():
        conexao.close()
        return jsonify({"status": "erro", "mensagem": "Você não favoritou esta publicação!"}), 400

    cursor.execute("DELETE FROM favoritos WHERE id_usuario = ? AND id_publicacao = ?", (id_usuario, id_publicacao))
    cursor.execute("UPDATE publicacoes SET quant_favoritos = quant_favoritos - 1 WHERE id = ?", (id_publicacao,))
    cursor.execute("""
        UPDATE usuarios SET quant_favoritos = quant_favoritos - 1
        WHERE id = (SELECT id_criador FROM publicacoes WHERE id = ?)
    """, (id_publicacao,))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "ok", "mensagem": "Favorito removido!"})

@app.route('/comentar', methods=['POST'])
def comentar():
    if 'usuario' not in session:
        return jsonify({"status": "erro", "mensagem": "Você precisa estar logado!"}), 403
    id_usuario = session['usuario']['id']

    data = request.get_json()
    id_publicacao = data.get("id_publicacao")
    conteudo = data.get("conteudo")

    if not conteudo.strip():
        return jsonify({"status": "erro", "mensagem": "O comentário não pode ser vazio!"}), 400

    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO comentarios (id_usuario, id_publicacao, conteudo) VALUES (?, ?, ?)",
                   (id_usuario, id_publicacao, conteudo))
    cursor.execute("UPDATE publicacoes SET quant_comentarios = quant_comentarios + 1 WHERE id = ?", (id_publicacao,))
    cursor.execute("""
        UPDATE usuarios SET quant_comentarios = quant_comentarios + 1
        WHERE id = (SELECT id_criador FROM publicacoes WHERE id = ?)
    """, (id_publicacao,))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "ok", "mensagem": "Comentário adicionado!"})

@app.route('/denunciar', methods=['POST'])
def denunciar():
    if 'usuario' not in session:
        return jsonify({"status": "erro", "mensagem": "Você precisa estar logado!"}), 403
    id_usuario = session['usuario']['id']

    data = request.get_json()
    id_publicacao = data.get("id_publicacao")
    motivo = data.get("motivo")

    if not motivo.strip():
        return jsonify({"status": "erro", "mensagem": "O motivo da denúncia não pode ser vazio!"}), 400

    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM denuncias WHERE id_usuario = ? AND id_publicacao = ?", (id_usuario, id_publicacao))
    if cursor.fetchone():
        conexao.close()
        return jsonify({"status": "erro", "mensagem": "Você já denunciou esta publicação!"}), 400

    cursor.execute("INSERT INTO denuncias (id_usuario, id_publicacao, motivo) VALUES (?, ?, ?)",
                   (id_usuario, id_publicacao, motivo))
    conexao.commit()
    conexao.close()
    return jsonify({"status": "ok", "mensagem": "Denúncia registrada com sucesso!"})


# 5. EXCLUIR CONTA
@app.route('/excluir_conta', methods=['DELETE'])
def excluir_conta():
    if 'usuario' not in session:
        return jsonify({"status": "erro", "mensagem": "Você precisa estar logado!"}), 403
    id_usuario = session['usuario']['id']

    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM curtidas WHERE id_usuario = ?", (id_usuario,))
    cursor.execute("DELETE FROM favoritos WHERE id_usuario = ?", (id_usuario,))
    cursor.execute("DELETE FROM comentarios WHERE id_usuario = ?", (id_usuario,))
    cursor.execute("DELETE FROM denuncias WHERE id_usuario = ?", (id_usuario,))
    cursor.execute("DELETE FROM publicacoes WHERE id_criador = ?", (id_usuario,))
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
    conexao.commit()
    conexao.close()

    session.pop('usuario', None)
    return jsonify({"status": "ok", "mensagem": "Conta excluída com sucesso!"})


if __name__ == '__main__':
    app.run(debug=True)