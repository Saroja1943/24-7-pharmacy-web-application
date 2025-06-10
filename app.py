from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret-key'

# Upload folder for prescriptions (not used in home.html but required for prescription uploads)
UPLOAD_FOLDER = 'static/prescriptions'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory storage (can be replaced with DB logic)
cart_items = []  # Temporary global cart (better to use per user in production)
prescriptions = []

DATABASE = 'users.db'

# ------------------ User Model ------------------
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    con.close()
    return User(*row) if row else None

# ------------------ Routes ------------------

@app.route('/')
def home():
    return render_template('home.html', cart_items=cart_items)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/prescription', methods=['GET', 'POST'])
@login_required
def prescription():
    if request.method == 'POST':
        name = request.form['name']
        medicine = request.form['medicine']
        prescriptions.append({'name': name, 'medicine': medicine})
        return redirect(url_for('home'))
    return render_template('prescription.html')

@app.route('/cart')
@login_required
def cart():
    return render_template('cart.html', items=cart_items)

@app.route('/add_to_cart/<item>')
@login_required
def add_to_cart(item):
    cart_items.append(item)
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    return render_template('checkout.html', items=cart_items)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    return render_template('admin_dashboard.html', prescriptions=prescriptions)

@app.route('/pharmacist_dashboard')
@login_required
def pharmacist_dashboard():
    if current_user.role != 'pharmacist':
        return "Unauthorized", 403
    return render_template('pharmacist_dashboard.html', prescriptions=prescriptions)

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        con.commit()
        con.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        cur.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        con.close()
        if user and user[2] == password:
            user_obj = User(user[0], user[1], user[3])
            login_user(user_obj)
            if user[3] == 'admin':
                return redirect('/admin_dashboard')
            elif user[3] == 'pharmacist':
                return redirect('/pharmacist_dashboard')
            else:
                return redirect('/user_dashboard')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# ------------------ Run ------------------

if __name__ == '__main__':
    app.run(debug=True)
