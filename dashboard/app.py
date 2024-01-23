from flask import jsonify
from flask_login import current_user
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
app = Flask(__name__)
app.secret_key = 'kkk'  # Clé secrète pour la session

# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Création d'une base de données SQLite pour stocker les utilisateurs (simplifié)
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT ,
                  password TEXT)''')
conn.commit()
conn.close()



# Connexion à la base de données
conn = sqlite3.connect('notifications.db')
cursor = conn.cursor()

# Création de la table des notifications
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT
    )
''')

conn.commit()
conn.close()


# Création d'une base de données SQLite pour stocker les utilisateurs (simplifié)
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT ,
                  password TEXT)''')
conn.commit()
conn.close()





# Logique pour vérifier les seuils et ajouter les notifications
def check_thresholds(temperature, luminosity):
    notifications = []

    if temperature > 30:
        add_notification('Alarme activee pour la temperature')
        notifications.append('Alarme activee pour la temperature')

    if luminosity < 15:
        add_notification('LED allumee en raison de la luminosite')
        notifications.append('LED allumee en raison de la luminosite')

    return notifications

# Ajout de notification dans la base de données
def add_notification(message):
    conn = sqlite3.connect('notifications.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO notifications (message) VALUES (?)', (message,))
    conn.commit()
    conn.close()

# Modèle utilisateur pour Flask-Login
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
        
def login_required_redirect(login_route):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for(login_route))
            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator
# Fonction pour récupérer un utilisateur depuis la base de données
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    return User(user[0])

# Route pour la page de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            user_obj = User(user[0])
            login_user(user_obj)
            return redirect(url_for('dashboard'))

    return render_template('login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Vérifiez si l'utilisateur existe déjà dans la base de données
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()

        # Si l'utilisateur n'existe pas, ajoutez-le à la base de données
        if not existing_user:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))  # Redirigez l'utilisateur vers la page de connexion après l'inscription

    return render_template('register.html')


# Route pour afficher les données dans le dashboard
@app.route('/')
def dashboard():
    conn = sqlite3.connect('arduino_data.db')
    cursor = conn.cursor()
    
    # Récupérer la dernière valeur de température et de luminosité pour affichage
    cursor.execute('SELECT temperature, light_intensity FROM sensor_data ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    temperature = row[0] if row else 'N/A'
    luminosity = row[1] if row else 'N/A'
    
    # Récupérer les 10 dernières valeurs de température et de luminosité pour les graphiques
    cursor.execute('SELECT temperature, light_intensity FROM sensor_data ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    
    # Créer des listes de températures et de luminosités à partir des résultats
    temperatures = [row[0] for row in reversed(rows)] if rows else []
    luminosities = [row[1] for row in reversed(rows)] if rows else []
    
    # Récupérer les notifications
    cursor.execute('SELECT message FROM notifications ORDER BY id DESC LIMIT 10')
    notification = [row[0] for row in cursor.fetchall()]
    
    # Vérification des seuils pour obtenir les notifications
    notifications = check_thresholds(temperature, luminosity)
    # Ajout des notifications basées sur les seuils dans la base de données
    for notification in notifications:
        add_notification(notification)
    
    conn.close()
    
    return render_template('index.html', temperature=temperature, luminosity=luminosity, temperatures=json.dumps(temperatures), luminosities=json.dumps(luminosities), notifications=json.dumps(notifications), current_user=current_user)

    
@app.route('/historique')
@login_required_redirect('home')
def historique():
    conn = sqlite3.connect('arduino_data.db')
    cursor = conn.cursor()

    # Récupérer l'historique des enregistrements depuis la base de données
    cursor.execute('SELECT timestamp, temperature, light_intensity FROM sensor_data ORDER BY id DESC LIMIT 10')
    records = cursor.fetchall()
    
    # Récupérer les notifications
    cursor.execute('SELECT message FROM notifications ORDER BY id DESC LIMIT 10')
    notification = [row[0] for row in cursor.fetchall()]
    
    # Récupérer la dernière valeur de température et de luminosité pour affichage
    cursor.execute('SELECT temperature, light_intensity FROM sensor_data  ORDER BY id DESC LIMIT 10')

    row = cursor.fetchone()
    temperature = row[0] if row else 'N/A'
    luminosity = row[1] if row else 'N/A'
    
    # Vérification des seuils pour obtenir les notifications
    notifications = check_thresholds(temperature, luminosity)
    # Ajout des notifications basées sur les seuils dans la base de données
    for notification in notifications:
        add_notification(notification)

    conn.close()

    return render_template('historique.html', records=records, notifications=json.dumps(notifications))

    # Logique pour la page historique

@app.route('/controle')
@login_required_redirect('home')
def controle():
    conn = sqlite3.connect('arduino_data.db')
    cursor = conn.cursor()

    # Récupérer les valeurs actuelles de température et luminosité pour affichage
    cursor.execute('SELECT temperature, light_intensity FROM sensor_data ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    temperature = row[0] if row else 'N/A'
    luminosity = row[1] if row else 'N/A'
    
    # Récupérer les notifications
    cursor.execute('SELECT message FROM notifications ORDER BY id DESC LIMIT 10')
    notification = [row[0] for row in cursor.fetchall()]
    
    # Vérification des seuils pour obtenir les notifications
    notifications = check_thresholds(temperature, luminosity)
    # Ajout des notifications basées sur les seuils dans la base de données
    for notification in notifications:
        add_notification(notification)

    conn.close()

    return render_template('controle.html', temperature=temperature, luminosity=luminosity, notifications=json.dumps(notifications))



@app.route('/home')
def home():
    return render_template('home.html')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))





if __name__ == '__main__':
    app.run(debug=True)