from flask import Flask, request, send_file, abort
from PIL import Image
import os
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['Max_length'] = 200*1024*1024 ## 200 MB

##Directory to save uploads
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return "Editfy Working"

@app.route('/images-to-gif', methods=['POST'])
def images_to_gif():
    if 'images' not in request.files:
        abort(400, description="No images provided. Use form field name 'images'.")

    files = request.files.getlist('images')
    
    if len(files) < 2:
        abort(400, description="At least 2 images are required to create an animated GIF.")

    images = []
    for file in files:
        if file.filename == '':
            abort(400, description="Empty filename.")
        
        # Open image directly from stream
        try:
            img = Image.open(file.stream)
            # Convert to RGB if it has transparency (GIF doesn't support alpha well)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            images.append(img)
        except Exception as e:
            abort(400, description=f"Invalid image file: {file.filename} ({str(e)})")

    if not images:
        abort(400, description="No valid images uploaded.")

    # Optional parameters (you can add form fields for these)
    duration = int(request.form.get('duration', 200))  # ms per frame, default 200ms
    loop = int(request.form.get('loop', 0))  # 0 = infinite loop

    # Create GIF in memory
    output = io.BytesIO()
    try:
        images[0].save(
            output,
            format='GIF',
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=loop
        )
    except Exception as e:
        abort(500, description=f"Error creating GIF: {str(e)}")

    output.seek(0)

    return send_file(
        output,
        mimetype='image/gif',
        as_attachment=True,
        download_name='animated.gif'
    )





if __name__ == "__main__":
    app.run(debug=True)
