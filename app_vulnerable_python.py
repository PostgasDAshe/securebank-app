"""
APLICACION VULNERABLE - USO EXCLUSIVO EDUCATIVO
================================================
Módulo: Puesta en Producción Segura
Tema 5: Implantación de Sistemas Seguros de Desplegado de SW

Esta aplicación contiene vulnerabilidades INTENCIONADAS para que
los alumnos las identifiquen y propongan soluciones.

NO DESPLEGAR EN PRODUCCION NI EN REDES REALES.
"""

import sqlite3
import subprocess
import os
from flask import Flask, request, render_template_string, redirect, session

app = Flask(__name__)

# VULNERABILIDAD 1: Secret key hardcodeada en el código fuente
app.secret_key = "clave_super_secreta_123"

# VULNERABILIDAD 2: Base de datos con ruta expuesta y sin control
DATABASE = "usuarios.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            rol TEXT
        )
    """)
    # VULNERABILIDAD 3: Contraseñas en texto plano en la base de datos
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES (1, 'admin', 'admin123', 'admin')")
    conn.execute("INSERT OR IGNORE INTO usuarios VALUES (2, 'alice', 'password', 'user')")
    conn.commit()
    conn.close()


# VULNERABILIDAD 4: Inyección SQL directa por concatenación de strings
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        # ❌ SQL INJECTION: la entrada del usuario se concatena directamente
        query = "SELECT * FROM usuarios WHERE username='" + username + "' AND password='" + password + "'"
        cursor = conn.execute(query)
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["rol"] = user[3]
            return redirect("/dashboard")
        else:
            error = "Credenciales incorrectas"

    # VULNERABILIDAD 5: XSS - el error se refleja sin escapar
    html = """
    <html><body>
    <h2>Login - SecureBank App</h2>
    <form method="POST">
        Usuario: <input name="username"><br>
        Password: <input type="password" name="password"><br>
        <button type="submit">Entrar</button>
    </form>
    <p style="color:red">""" + error + """</p>
    </body></html>
    """
    return html


# VULNERABILIDAD 6: Sin control de acceso real (broken access control)
@app.route("/dashboard")
def dashboard():
    # No se verifica si hay sesión activa
    user = session.get("user", "Invitado")
    return f"<h1>Bienvenido {user}</h1><a href='/admin'>Ir al panel admin</a>"


# VULNERABILIDAD 7: Panel de admin accesible sin verificar rol
@app.route("/admin")
def admin():
    # ❌ No se verifica session["rol"] == "admin"
    return "<h1>Panel de Administración</h1><p>Usuarios del sistema: admin, alice</p>"


# VULNERABILIDAD 8: Command injection - ejecuta comandos del sistema con input del usuario
@app.route("/ping")
def ping():
    host = request.args.get("host", "localhost")
    # ❌ COMMAND INJECTION: el parámetro host se pasa directamente al sistema
    result = subprocess.getoutput("ping -c 1 " + host)
    return f"<pre>{result}</pre>"


# VULNERABILIDAD 9: Path traversal - permite leer ficheros arbitrarios del servidor
@app.route("/archivo")
def archivo():
    filename = request.args.get("nombre", "")
    # ❌ PATH TRAVERSAL: no se valida ni sanitiza el nombre de archivo
    try:
        with open("uploads/" + filename, "r") as f:
            content = f.read()
        return f"<pre>{content}</pre>"
    except:
        return "Archivo no encontrado"


# VULNERABILIDAD 10: Sin cabeceras de seguridad HTTP
# No hay X-Frame-Options, CSP, HSTS, X-Content-Type-Options, etc.

# VULNERABILIDAD 11: Debug mode activado en producción
if __name__ == "__main__":
    init_db()
    # ❌ debug=True expone el debugger interactivo de Werkzeug al exterior
    app.run(debug=True, host="0.0.0.0", port=5000)
