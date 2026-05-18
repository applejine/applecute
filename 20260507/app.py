from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
import hashlib

app = Flask(__name__)
app.secret_key = 'super_secret_key_2026'  # 啟用 flash 訊息與 session 所需的密鑰

FIREBASE_URL = "https://chat-app16-4895c-default-rtdb.firebaseio.com"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('board'))
    return redirect(url_for('login'))

# Screen1: 登入 (必須輸入帳密，並選擇本次登入想用的頭像)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        avatar = request.form.get('avatar') # 拿前端選的頭像 URL
        
        if not username or not password:
            flash('請填寫所有欄位！', 'danger')
            return render_template('login.html')
            
        # 到 Firebase 檢查使用者是否存在
        response = requests.get(f"{FIREBASE_URL}/users/{username}.json")
        user_data = response.json()
        
        if user_data and user_data.get('password') == hash_password(password):
            # 驗證成功，寫入後端 Session
            session['user'] = username
            session['avatar'] = avatar
            return redirect(url_for('board'))
        else:
            flash('帳號或密碼錯誤！', 'danger')
            
    return render_template('login.html')

# Screen2: 留言板
@app.route('/board', methods=['GET', 'POST'])
def board():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data and data.get('content'):
            msg_data = {
                'username': session['user'],
                'avatar': session['avatar'],
                'content': data.get('content'),
                'timestamp': {'.sv': 'timestamp'},
                'reactions': {'like': 0, 'heart': 0, 'laugh': 0, 'wow': 0, 'sad': 0}
            }
            requests.post(f"{FIREBASE_URL}/messages.json", json=msg_data)
            return jsonify({"status": "success"}), 200
            
    # 載入留言
    response = requests.get(f"{FIREBASE_URL}/messages.json")
    messages_dict = response.json() or {}
    
    messages = []
    for key, val in messages_dict.items():
        val['id'] = key
        if 'reactions' not in val:
            val['reactions'] = {'like': 0, 'heart': 0, 'laugh': 0, 'wow': 0, 'sad': 0}
        messages.append(val)
        
    return render_template('board.html', username=session['user'], avatar=session['avatar'], messages=messages)

# 處理點擊心情貼圖
@app.route('/react/<msg_id>/<reaction_type>', methods=['POST'])
def react(msg_id, reaction_type):
    res = requests.get(f"{FIREBASE_URL}/messages/{msg_id}/reactions/{reaction_type}.json")
    current_count = res.json() or 0
    requests.put(f"{FIREBASE_URL}/messages/{msg_id}/reactions/{reaction_type}.json", json=current_count + 1)
    return jsonify({"status": "success", "new_count": current_count + 1}), 200

# Screen3: 註冊帳號 (真正寫入 Firebase)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('欄位不能為空！', 'danger')
            return render_template('register.html')
            
        # 檢查是否重複註冊
        check = requests.get(f"{FIREBASE_URL}/users/{username}.json")
        if check.json():
            flash('此帳號已存在，請換一個！', 'danger')
        else:
            user_data = {'password': hash_password(password)}
            requests.put(f"{FIREBASE_URL}/users/{username}.json", json=user_data)
            flash('帳號建立成功！請登入。', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/settings')
def settings():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html', username=session['user'], avatar=session['avatar'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)