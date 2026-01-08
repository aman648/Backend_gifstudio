from flask import Flask, request, send_file, abort
from flask_cors import CORS
from PIL import Image,ImageSequence
import subprocess
import os
import io
from werkzeug.utils import secure_filename


Image.MAX_IMAGE_PIXELS = 500_000_000  # Increase max pixels to handle large images
app = Flask(__name__)
CORS(app)
app.config['Max_length'] = 200*1024*1024 ## 200 MB

##Directory to save uploads
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')

def index():
    return "Editfy Working"


@app.route('/vedio_gif', methods=['POST'])
def vedio_gif():
    if 'video' not in request.files:
        abort(400, description="No video file provided. Use form field name 'video'.")
    vedio = request.files['video']
    if vedio.filename == '':
        abort(400, description="Empty filename.")
    
    width  = int(request.form.get('width', "320"))
    fps    = 10

    try:
        vedio_bytes = vedio.read()
        command = ['ffmpeg',
                   '-i', 'pipe:0',
                   '-vf', f'scale={width},fps={fps}',
                   '-f', 'gif',
                   'pipe:1'
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        gif_bytes, err = process.communicate(input=vedio_bytes)
        if process.returncode != 0:
            abort(500, description=f"FFmpeg error: {err.decode()}")

        return send_file(
            io.BytesIO(gif_bytes),
            mimetype='image/gif',
            as_attachment=True,
            download_name='output.gif'
        )

        
    except Exception as e:
        abort(500, description=f"Error converting video to GIF: {str(e)}")


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

@app.route('/resize_gif', methods=['POST'])

def resize_gif():
    if 'image' not in request.files:
        abort(400, description="No image provided. Use form field name 'image'.")
    if 'width' not in request.form or 'height' not in request.form:
        abort(400, description="Width and height must be provided as form data.")

    file = request.files['image']
    width = int(request.form['width'])
    height = int(request.form['height'])

    

    try:
        img = Image.open(file.stream)
        img = img.resize((width, height))
        output = io.BytesIO()
        img.save(output, format='GIF')
        output.seek(0)
        return send_file(
            output,
            mimetype='image/gif',
            as_attachment=True,
            download_name='resized.gif'
        )
    except Exception as e:
        abort(500, description=f"Error resizing GIF: {str(e)}")


@app.route('/crop_gif', methods=['POST'])
def crop_gif():
    if 'image' not in request.files:
        abort(400, description="No image provided. Use form field name 'image'.")

    if 'left' not in request.form or 'upper' not in request.form or 'right' not in request.form or 'lower' not in request.form:
        abort(400, description="Crop coordinates (left, upper, right, lower) must be provided as form data.")

    file = request.files['image']
    left = int(request.form['left'])
    upper = int(request.form['upper'])
    right = int(request.form['right'])
    lower = int(request.form['lower'])

    try:
        img = Image.open(file.stream)
        frames = []
        for frame in ImageSequence.Iterator(img):
            frame = frame.convert("RGBA")
            cropped = frame.crop((left, upper, right, lower))
            frames.append(cropped)

        output = io.BytesIO()
        frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            loop=img.info.get("loop", 0),
            duration=img.info.get("duration", 100),
            disposal=2
        )
    except Exception as e:
        abort(500, description=f"Error cropping GIF: {str(e)}")
        




if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=5000)
