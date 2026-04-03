import os
import secrets
import urllib.parse
import re
from flask import Flask, render_template, session, redirect, url_for, request
from oath_client import SimpleOAuth2Client
from dotenv import load_dotenv

load_dotenv() 

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

MEMBER_EMAILS = [
    "nezzaluna10@gmail.com",
    "hillyelizabeth06@gmail.com",
    "deldildolly@gmail.com",
    "zakiaraihanauni@gmail.com",
    "qonitavidia@gmail.com"
]

TEAM_MEMBERS = [
    {"id": 1, "nama": "Nezzaluna Azzahra", "npm": "2406495741", "jurusan": "Ilmu Komputer", "angkatan": "2024", "foto": "https://media.licdn.com/dms/image/v2/D5603AQGEvhdWtlK4Zg/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1723943775447?e=1776902400&v=beta&t=t1mV623KAqTj97ZLndU7R2rZ9UNBnY0FJh5cCO61xH8"},
    {"id": 2, "nama": "Hillary Elizabeth Clara Pasaribu", "npm": "2406407266", "jurusan": "Sistem Informasi", "angkatan": "2024", "foto": "https://media.licdn.com/dms/image/v2/D5603AQEHiDpqhf9zxw/profile-displayphoto-shrink_400_400/B56ZxmbYCvKkAg-/0/1771244980074?e=1776902400&v=beta&t=aSgsLJn4j68q7Yg4Whj2VMsfdAsomk6BwKgQFfugT6o"},
    {"id": 3, "nama": "Cristian Dillon Philbert", "npm": "2406495956", "jurusan": "Sistem Informasi", "angkatan": "2024", "foto": "https://lh3.googleusercontent.com/d/1TBSyG-gij9eFnxA559AGe4xIwIA18qs4"},
    {"id": 4, "nama": "Raihana Auni Zakia", "npm": "2406495760", "jurusan": "Ilmu Komputer", "angkatan": "2024", "foto": "https://media.licdn.com/dms/image/v2/D5603AQFeua4cK7xnXg/profile-displayphoto-scale_400_400/B56ZjWK6_hH8Ag-/0/1755939846437?e=1776902400&v=beta&t=TDNazc9HhZy_GnkyFXVy29m6QHUkEQFgqpneaxqn4oE"},
    {"id": 5, "nama": "Vidia Qonita Ahmad", "npm": "2406345381", "jurusan": "Ilmu Komputer", "angkatan": "2024", "foto": "https://media.licdn.com/dms/image/v2/D5603AQEXU1uuaXGVbQ/profile-displayphoto-crop_800_800/B56Z1TlYlDKEAI-/0/1775223805609?e=1776902400&v=beta&t=MpADci-M6RPRopU6GZEgJwPAu9CDgXxQ4tqUPuKX8zY"}
]

DISPLAY_STYLE = {
    "color": "#f4f4f9",
    "font": "sans-serif"
}

ALLOWED_FONTS = {"sans-serif", "serif", "monospace"}


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def mix_with_black(hex_color, amount):
    r, g, b = hex_to_rgb(hex_color)
    r = max(0, min(255, int(r * (1 - amount))))
    g = max(0, min(255, int(g * (1 - amount))))
    b = max(0, min(255, int(b * (1 - amount))))
    return rgb_to_hex((r, g, b))


def get_text_color_for_bg(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return "#111111" if luminance > 160 else "#ffffff"


def get_ui_palette(bg_color):
    button_color = mix_with_black(bg_color, 0.25)
    button_hover = mix_with_black(bg_color, 0.4)
    button_text = get_text_color_for_bg(button_color)
    return {
        "button_color": button_color,
        "button_hover": button_hover,
        "button_text": button_text,
    }

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
    palette = get_ui_palette(DISPLAY_STYLE['color'])
    return render_template('index.html', 
                           user=session.get('user'), 
                           is_member=session.get('is_member'),
                           style=DISPLAY_STYLE,
                           palette=palette,
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
    session['is_member'] = user_info['email'] in MEMBER_EMAILS
    return redirect(url_for('index'))

@app.route('/update-style', methods=['POST'])
def update_style():
    if session.get('is_member'):
        color = (request.form.get('color') or '').strip()
        font = (request.form.get('font') or '').strip()

        if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            DISPLAY_STYLE['color'] = color
        if font in ALLOWED_FONTS:
            DISPLAY_STYLE['font'] = font
    return redirect(url_for('index'))


@app.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
def edit_member(member_id):
    if not session.get('is_member'):
        return "Hanya anggota kelompok yang boleh mengedit data.", 403

    member = get_member_by_id(member_id)
    if not member:
        return "Data anggota tidak ditemukan.", 404

    error_message = None 

    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        npm = request.form.get('npm', '').strip()
        jurusan = request.form.get('jurusan', '').strip()
        angkatan = request.form.get('angkatan', '').strip()
        foto = request.form.get('foto', '').strip()

        if not npm.isdigit():
            error_message = "Input tidak valid. NPM harus berupa angka."
        elif len(npm) != 10:
            error_message = "Input tidak valid. Panjang NPM harus tepat 10 digit."
        else:
            member['nama'] = nama
            member['npm'] = npm
            member['jurusan'] = jurusan
            member['angkatan'] = angkatan
            member['foto'] = foto
            return redirect(url_for('index'))

    return render_template('edit_member.html', member=member, error=error_message)

@app.route('/logout')
def logout():
    session.pop('oauth_state', None)
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(port=8000, debug=True, use_reloader=False)