from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
random_key = os.urandom(24).hex()
app.config['SECRET_KEY'] = random_key
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "studyroom.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Availability(db.Model):
    __tablename__ = 'Availability'
    id = db.Column(db.Integer, primary_key=True)
    center_name = db.Column(db.Text, db.ForeignKey('BasicInfo.name'), nullable=False)
    day = db.Column(db.Text, nullable=False)
    start_time = db.Column(db.Text, nullable=False)
    end_time = db.Column(db.Text, nullable=False)
    __table_args__ = (db.UniqueConstraint('center_name', 'day', 'start_time', 'end_time'),)
    basic_info = db.relationship('BasicInfo', back_populates='availabilities')

class BasicInfo(db.Model):
    __tablename__ = 'BasicInfo'
    name = db.Column(db.Text, primary_key=True)
    serial_number = db.Column(db.Float)
    division = db.Column(db.Text)
    address = db.Column(db.Text)
    availability = db.Column(db.Text)
    contacts = db.Column(db.Text)
    additional_info = db.Column(db.Text)
    postal_code = db.Column(db.Text)
    region = db.Column(db.Text)

    availabilities = db.relationship('Availability', back_populates='basic_info')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    regions = db.session.query(BasicInfo.division).distinct().order_by(BasicInfo.division).all()
    regions = [r[0] for r in regions if r[0]]  # Remove any None values
    return render_template('index.html', regions=regions)


@app.route('/search', methods=['POST'])
def search():
    region = request.form['region']
    current_time = datetime.now().strftime('%H:%M')
    current_day = datetime.now().strftime('%A')
    
    results = db.session.query(BasicInfo, Availability).join(Availability)\
        .filter(BasicInfo.division == region)\
        .filter(Availability.day == current_day)\
        .all()
    
    # Group results by RC
    grouped_results = {}
    for basic, avail in results:
        if basic.name not in grouped_results:
            grouped_results[basic.name] = {
                'info': basic,
                'hours': []
            }
        grouped_results[basic.name]['hours'].append(avail)
    
    return render_template('results.html', results=grouped_results, current_time=current_time)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/add_entry', methods=['POST'])
@login_required
def add_entry():
    data = request.json
    new_entry = BasicInfo(**data)
    db.session.add(new_entry)
    db.session.commit()
    return jsonify({"message": "Entry added successfully"})

@app.route('/upload_excel', methods=['POST'])
@login_required
def upload_excel():
    if 'excel_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['excel_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        table_name = request.form['table_name']
        
        try:
            df = pd.read_excel(file_path)
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            os.remove(file_path)  # Remove the file after processing
            return jsonify({"message": f"Table '{table_name}' created successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid file type"}), 400

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

@app.route('/get_entries')
@login_required
def get_entries():
    entries = BasicInfo.query.all()
    return jsonify([{
        'name': entry.name,
        'address': entry.address,
        'postal_code': entry.postal_code
    } for entry in entries])

@app.route('/timetable')
def timetable_select():
    regions = db.session.query(BasicInfo.division).distinct().order_by(BasicInfo.division).all()
    regions = [r[0] for r in regions if r[0]]
    return render_template('timetable_select.html', regions=regions)

@app.route('/timetable_view')
def timetable_view():
    region = request.args.get('region')
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return render_template('timetable_view.html', region=region, days=days)

@app.route('/api/timetable')
def api_timetable():
    region = request.args.get('region')
    day = request.args.get('day')
    
    results = db.session.query(BasicInfo, Availability).join(Availability)\
        .filter(BasicInfo.division == region)\
        .filter(Availability.day == day)\
        .order_by(BasicInfo.name)\
        .all()

    timetable_data = []
    for basic, avail in results:
        start_hour = int(avail.start_time.split(':')[0])
        end_hour = int(avail.end_time.split(':')[0])
        timetable_data.append({
            'name': basic.name,
            'start': start_hour,
            'end': end_hour,
            'address': basic.address,
            'postal_code': basic.postal_code
        })

    return jsonify(timetable_data)

if __name__ == '__main__':
    app.run(debug=True)