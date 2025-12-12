from flask import Flask, render_template, request, redirect
import sqlite3, os, socket

app = Flask(__name__)

# База данных
def init_db():
    if not os.path.exists('grades.db'):
        conn = sqlite3.connect('grades.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE grades
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT, subject TEXT, grade INTEGER)''')
        conn.commit()
        conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    # Добавление
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        grade = request.form.get('grade')
        
        if name and subject and grade:
            conn = sqlite3.connect('grades.db')
            c = conn.cursor()
            c.execute("INSERT INTO grades (name, subject, grade) VALUES (?, ?, ?)",
                     (name, subject, grade))
            conn.commit()
            conn.close()
        return redirect('/')
    
    # Показать все
    conn = sqlite3.connect('grades.db')
    c = conn.cursor()
    c.execute("SELECT * FROM grades")
    grades = c.fetchall()
    conn.close()
    
    return render_template('index.html', grades=grades)

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('grades.db')
    c = conn.cursor()
    c.execute("DELETE FROM grades WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if __name__ == '__main__':
    init_db()
    port = 9000
    
    # Проверка порта
    if is_port_in_use(port):
        print(f"Порт {port} занят! Пробую порт 9001...")
        port = 9001
    
    try:
        print(f"Сервер запущен: http://localhost:{port}")
        app.run(debug=True, port=port, use_reloader=False)  # use_reloader=False убирает перезагрузку
    except OSError as e:
        print(f"Ошибка порта: {e}")
        print("Пробую другой порт...")
        app.run(debug=True, port=9002, use_reloader=False)
