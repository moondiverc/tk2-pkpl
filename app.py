import os
import secrets
import urllib.parse
from flask import Flask, render_template, session, redirect, url_for, request
from oath_client import SimpleOAuth2Client
from dotenv import load_dotenv

# mengambil data dari file .env
load_dotenv() 

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# list email anggota kelompok (Otorisasi: hanya email ini yang bisa login dan mengedit data anggota)
MEMBER_EMAILS = [
    "nezzaluna10@gmail.com",
    "hillyelizabeth06@gmail.com",
    "deldildolly@gmail.com",
    "zakiaraihanauni@gmail.com",
    "qonitavidia@gmail.com"
]

# data anggota kelompok (bisa diedit oleh anggota yang login)
TEAM_MEMBERS = [
    {"id": 1, "nama": "Nezzaluna Azzahra", "npm": "2406495741", "jurusan": "Ilmu Komputer", "angkatan": "2024"},
    {"id": 2, "nama": "Hillary Elizabeth Clara Pasaribu", "npm": "2406407266", "jurusan": "Sistem Informasi", "angkatan": "2024"},
    {"id": 3, "nama": "Cristian Dillon Philbert", "npm": "2406495956", "jurusan": "Sistem Informasi", "angkatan": "2024"},
    {"id": 4, "nama": "Raihana Auni Zakia", "npm": "2406495760", "jurusan": "Ilmu Komputer", "angkatan": "2024"},
    {"id": 5, "nama": "Vidia Qonita Ahmad", "npm": "2406345381", "jurusan": "Ilmu Komputer", "angkatan": "2024"}
]

# init OAuth Client
oauth = SimpleOAuth2Client(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    auth_url="https://accounts.google.com/o/oauth2/auth",
    token_url="https://oauth2.googleapis.com/token",
    redirect_uri="http://localhost:8000/callback",
    scope="profile email"
)


def get_member_by_id(member_id):
    for member in TEAM_MEMBERS:
        if member["id"] == member_id:
            return member
    return None

@app.route('/')
def index():
    # mengambil data gaya dari session (default : biru & sans-serif)
    current_style = {
        'color': session.get('bg_color', '#f4f4f9'),
        'font': session.get('font_family', 'sans-serif')
    }
    return render_template('index.html', 
                           user=session.get('user'), 
                           is_member=session.get('is_member'),
                           style=current_style,
                           members=TEAM_MEMBERS)

@app.route('/login')
def login():
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state

    params = {
        'client_id': oauth.client_id,
        'redirect_uri': oauth.redirect_uri,
        'scope': oauth.scope,
        'response_type': 'code',
        'state': state,
        'prompt': 'select_account consent',
        'access_type': 'offline',
        'include_granted_scopes': 'true'
    }
    auth_request_url = f"{oauth.auth_url}?{urllib.parse.urlencode(params)}"
    return redirect(auth_request_url)

@app.route('/callback')
def callback():
    returned_state = request.args.get('state')
    expected_state = session.get('oauth_state')
    if not returned_state or returned_state != expected_state:
        return "OAuth state tidak valid.", 400

    code = request.args.get('code')
    if not code:
        return "Authorization code tidak ditemukan.", 400

    oauth.get_token(code=code)
    user_info = oauth.make_api_request("https://www.googleapis.com/oauth2/v2/userinfo").json()
    
    session['user'] = user_info
    # Mekanisme Otorisasi: cek apakah email user ada di daftar anggota
    session['is_member'] = user_info['email'] in MEMBER_EMAILS
    return redirect(url_for('index'))

@app.route('/update-style', methods=['POST'])
def update_style():
    # Proteksi Otorisasi tambahan di server-side
    if session.get('is_member'):
        session['bg_color'] = request.form.get('color')
        session['font_family'] = request.form.get('font')
    return redirect(url_for('index'))


@app.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
def edit_member(member_id):
    if not session.get('is_member'):
        return "Hanya anggota kelompok yang boleh mengedit data.", 403

    member = get_member_by_id(member_id)
    if not member:
        return "Data anggota tidak ditemukan.", 404

    if request.method == 'POST':
        #Validasi input dan update data anggota
        try:
            member['nama'] = str(request.form.get('nama', member['nama']).strip())
            member['npm'] = int(request.form.get('npm', member.get('npm', '')).strip())
            member['jurusan'] = int(request.form.get('jurusan', member['jurusan']).strip())
            member['angkatan'] = str(request.form.get('angkatan', member['angkatan']).strip())
        except ValueError:
            return "Input tidak valid. Pastikan npm dan jurusan adalah angka.", 400
        return redirect(url_for('index'))

    return render_template('edit_member.html', member=member)

@app.route('/logout')
def logout():
    session.pop('oauth_state', None)
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(port=8000, debug=True, use_reloader=False)