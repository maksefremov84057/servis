import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import random
from flask import Flask, render_template, request, flash, session

app = Flask(__name__)
app.secret_key = 'simple-secret-key-123'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def generate_captcha():
    # CAPTCHA только из цифр
    captcha_text = ''.join(random.choices('0123456789', k=4))
    
    # Создаем изображение
    image = Image.new('RGB', (120, 50), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Простой текст
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Рисуем текст
    if font:
        draw.text((30, 15), captcha_text, font=font, fill=(0, 0, 0))
    else:
        draw.text((30, 15), captcha_text, fill=(0, 0, 0))
    
    # Сохраняем в base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    captcha_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return captcha_text, captcha_base64

def process_image_color_reorder(image_path, color_order):
    img = Image.open(image_path)
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    img_array = np.array(img)
    
    r = img_array[:, :, 0]
    g = img_array[:, :, 1]
    b = img_array[:, :, 2]
    
    channels = {'r': r, 'g': g, 'b': b}
    new_order = [channels[channel] for channel in color_order.lower()]
    processed_array = np.stack(new_order, axis=2)
    
    processed_img = Image.fromarray(processed_array.astype('uint8'))
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed.png')
    processed_img.save(output_path)
    
    return 'uploads/processed.png', img_array, processed_array

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        captcha_text, captcha_base64 = generate_captcha()
        session['captcha_text'] = captcha_text
        return render_template('index.html', captcha_image=captcha_base64)
    
    if request.method == 'POST':
        # Проверяем CAPTCHA
        user_captcha = request.form.get('captcha', '')
        stored_captcha = session.get('captcha_text', '')
        
        print(f"Введено: '{user_captcha}', Ожидается: '{stored_captcha}'")
        
        if user_captcha != stored_captcha:
            flash('Неверная CAPTCHA! Введите 4 цифры, которые видите на картинке.')
            captcha_text, captcha_base64 = generate_captcha()
            session['captcha_text'] = captcha_text
            return render_template('index.html', captcha_image=captcha_base64)
        
        # Проверяем файл
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Выберите файл!')
            captcha_text, captcha_base64 = generate_captcha()
            session['captcha_text'] = captcha_text
            return render_template('index.html', captcha_image=captcha_base64)
        
        if not allowed_file(file.filename):
            flash('Неподдерживаемый формат файла! Используйте PNG, JPG, JPEG, GIF или BMP.')
            captcha_text, captcha_base64 = generate_captcha()
            session['captcha_text'] = captcha_text
            return render_template('index.html', captcha_image=captcha_base64)
        
        # Сохраняем и обрабатываем файл
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'original.png')
            file.save(file_path)
            
            color_order = request.form.get('color_order', 'rgb')
            processed_path, original_array, processed_array = process_image_color_reorder(file_path, color_order)
            
            # Генерируем новую CAPTCHA для следующего использования
            new_captcha_text, new_captcha_base64 = generate_captcha()
            session['captcha_text'] = new_captcha_text
            
            return render_template('result.html',
                                original_image='uploads/original.png',
                                processed_image=processed_path,
                                color_order=color_order.upper())
            
        except Exception as e:
            flash(f'Ошибка обработки: {str(e)}')
            captcha_text, captcha_base64 = generate_captcha()
            session['captcha_text'] = captcha_text
            return render_template('index.html', captcha_image=captcha_base64)

@app.route('/refresh-captcha')
def refresh_captcha():
    captcha_text, captcha_base64 = generate_captcha()
    session['captcha_text'] = captcha_text
    return {'captcha_image': captcha_base64}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9500)
