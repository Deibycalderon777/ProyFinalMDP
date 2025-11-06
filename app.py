# app.py - COMPLETAMENTE LIMPIO
from flask import Flask, render_template
from flask_cors import CORS
from routes.usuario_routes import usuario_bp

app = Flask(__name__)
app.secret_key = 'utnc'  # Necesario para las sesiones
CORS(app)
# Registrar blueprint de usuario
app.register_blueprint(usuario_bp)



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

if __name__ == "__main__":
    app.run(debug=True)

#usuario: admin@example.com
# contraseña: Password123!

