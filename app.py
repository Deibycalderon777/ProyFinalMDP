# app.py - Configuración principal de Flask
from flask import Flask, render_template
from flask_cors import CORS
# Asumo que usuario_routes.py existe o lo crearás.
from routes.usuario_routes import usuario_bp
from routes.roles_routes import role_bp  # Importación del Blueprint de Roles

app = Flask(__name__)
app.secret_key = 'utnc'  # Necesario para las sesiones
CORS(app)

# Registrar blueprints
# Nota: usuario_bp se asume ya definido en routes/usuario_routes.py
app.register_blueprint(usuario_bp)
app.register_blueprint(role_bp)  # Registro del Blueprint de Roles


@app.route("/")
def dashboard():
    return render_template("inicio.html")


@app.route("/dashboard")
def dashboard_fragment():
    # Plantilla parcial que se carga dentro de inicio.html (ng-view)
    return render_template("dashboard.html")

@app.route("/login")
def app_view():
    return render_template("login.html")

@app.route("/users")
def users_fragment():
    """Plantilla parcial para la gestión de usuarios"""
    return render_template("users.html")

@app.route('/roles')
def roles_template():
    """Sirve la plantilla HTML para la vista de gestión de roles."""
    # Asegúrate de que 'roles.html' exista en tu carpeta 'templates'
    return render_template('roles.html')

if __name__ == "__main__":
    app.run(debug=True)

