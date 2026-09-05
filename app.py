from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = 'clave_secreta_local_reparacion'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    conn = sqlite3.connect('equipos.db')
    c = conn.cursor()
    # Tabla usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        contraseña TEXT NOT NULL
    )''')
    # Tabla equipos (con nuevas columnas)
    c.execute('''CREATE TABLE IF NOT EXISTS equipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_hora TEXT,
        cliente TEXT,
        telefono TEXT,
        equipo TEXT,
        pantalla TEXT,
        camara TEXT,
        bateria TEXT,
        chasis TEXT,
        accesorios TEXT,
        detalles_extra TEXT,
        foto TEXT
    )''')
    # Agregar columnas faltantes si la tabla ya existía
    columns = ['camara', 'bateria', 'chasis', 'accesorios', 'foto']
    for col in columns:
        try:
            c.execute(f'ALTER TABLE equipos ADD COLUMN {col} TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass
    # Usuario admin por defecto
    c.execute('SELECT COUNT(*) FROM usuarios')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO usuarios (usuario, contraseña) VALUES (?, ?)', ('admin', '1234'))
        conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Debes iniciar sesión para acceder.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']
        conn = sqlite3.connect('equipos.db')
        c = conn.cursor()
        c.execute('SELECT * FROM usuarios WHERE usuario=? AND contraseña=?', (usuario, contraseña))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = usuario
            flash('Bienvenido, ' + usuario, 'success')
            return redirect(url_for('inicio'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Sesión cerrada', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def inicio():
    q = request.args.get('q', '')
    conn = sqlite3.connect('equipos.db')
    c = conn.cursor()
    if q:
        c.execute('''SELECT * FROM equipos WHERE cliente LIKE ? OR equipo LIKE ? OR telefono LIKE ? ORDER BY fecha_hora DESC''',
                  ('%'+q+'%', '%'+q+'%', '%'+q+'%'))
    else:
        c.execute('SELECT * FROM equipos ORDER BY fecha_hora DESC')
    equipos = c.fetchall()
    conn.close()
    return render_template('index.html', equipos=equipos, q=q)

@app.route('/agregar', methods=['GET', 'POST'])
@login_required
def agregar():
    if request.method == 'POST':
        cliente = request.form['cliente']
        telefono = request.form['telefono']
        equipo = request.form['equipo']
        pantalla = request.form['pantalla']
        camara = request.form['camara']
        bateria = request.form['bateria']
        chasis = request.form['chasis']
        accesorios = request.form['accesorios']
        detalles = request.form['detalles_extra']
        foto = request.files['foto']
        foto_filename = None
        if foto and foto.filename != '':
            filename = secure_filename(foto.filename)
            nombre, ext = os.path.splitext(filename)
            nuevo_nombre = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nombre}{ext}"
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nuevo_nombre))
            foto_filename = nuevo_nombre
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect('equipos.db')
        c = conn.cursor()
        c.execute('''INSERT INTO equipos 
                     (fecha_hora, cliente, telefono, equipo, pantalla, camara, bateria, chasis, accesorios, detalles_extra, foto)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (fecha_hora, cliente, telefono, equipo, pantalla, camara, bateria, chasis, accesorios, detalles, foto_filename))
        conn.commit()
        conn.close()
        flash('Equipo registrado correctamente', 'success')
        return redirect(url_for('inicio'))
    return render_template('agregar.html')

@app.route('/ver/<int:id>')
@login_required
def ver_equipo(id):
    conn = sqlite3.connect('equipos.db')
    c = conn.cursor()
    c.execute('SELECT * FROM equipos WHERE id=?', (id,))
    equipo = c.fetchone()
    conn.close()
    if not equipo:
        return redirect(url_for('inicio'))
    return render_template('ver_equipo.html', equipo=equipo)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
