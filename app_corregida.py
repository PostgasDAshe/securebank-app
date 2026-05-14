"""
APLICACION CORREGIDA - USO EXCLUSIVO EDUCATIVO
==============================================
Módulo: Puesta en Producción Segura
Tema 5: Implantación de Sistemas Seguros de Desplegado de SW
"""

import sqlite3
import subprocess
import os
from flask import Flask, request, redirect, session
from markupsafe import escape
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# CORRECCIÓN 1: Secret key cargada desde variable de entorno
app.secret_key = os.environ.get("SECRET_KEY", "clave_desarrollo_cambiar")

# CORRECCIÓN 2: Base de datos definida en una variable
DATABASE = "usuarios.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            rol TEXT
        )
    """)

    # CORRECCIÓN 3: Contraseñas almacenadas con hash
    password_admin = generate_password_hash("admin123")
    password_alice = generate_password_hash("password")

    conn.execute(
        "INSERT OR IGNORE INTO usuarios VALUES (1, 'admin', ?, 'admin')",
        (password_admin,)
    )
    conn.execute(
        "INSERT OR IGNORE INTO usuarios VALUES (2, 'alice', ?, 'user')",
        (password_alice,)
    )

    conn.commit()
    conn.close()


# CORRECCIÓN 10: Cabeceras HTTP de seguridad
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self';"
    return response


# CORRECCIÓN 4: SQL Injection corregido con consulta parametrizada
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        # Consulta parametrizada
        query = "SELECT * FROM usuarios WHERE username=?"
        cursor = conn.execute(query, (username,))
        user = cursor.fetchone()
        conn.close()

        # Comprobación de contraseña con hash
        if user and check_password_hash(user[2], password):
            session["user"] = username
            session["rol"] = user[3]
            return redirect("/dashboard")
        else:
            error = "Credenciales incorrectas"

    # CORRECCIÓN 5: XSS corregido escapando el error
    error = escape(error)

    html = """
    <html><body>
    <h2>Login - SecureBank App</h2>
    <form method="POST">
        Usuario: <input name="username"><br>
        Password: <input type="password" name="password"><br>
        <button type="submit">Entrar</button>
    </form>
    <p style="color:red">""" + str(error) + """</p>
    </body></html>
    """

    return html


# CORRECCIÓN 6: Control de acceso en dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    return f"<h1>Bienvenido {escape(user)}</h1><a href='/admin'>Ir al panel admin</a>"


# CORRECCIÓN 7: Control de rol en panel admin
@app.route("/admin")
def admin():
    if session.get("rol") != "admin":
        return "Acceso denegado"

    return "<h1>Panel de Administración</h1><p>Usuarios del sistema: admin, alice</p>"


# CORRECCIÓN 8: Command Injection corregido con validación sencilla
@app.route("/ping")
def ping():
    host = request.args.get("host", "localhost")

    if not host.replace(".", "").isalnum():
        return "Host no válido"

    result = subprocess.getoutput(f"ping -c 1 {host}")
    return f"<pre>{escape(result)}</pre>"


# CORRECCIÓN 9: Path Traversal corregido con lista blanca de archivos
@app.route("/archivo")
def archivo():
    filename = request.args.get("nombre", "")

    archivos_permitidos = ["info.txt", "manual.txt"]

    if filename not in archivos_permitidos:
        return "Archivo no permitido"

    try:
        with open("uploads/" + filename, "r") as f:
            content = f.read()
        return f"<pre>{escape(content)}</pre>"
    except Exception:
        return "Archivo no encontrado"


if __name__ == "__main__":
    init_db()

    # CORRECCIÓN 11: Debug desactivado
    app.run(debug=False, host="0.0.0.0", port=5000)
