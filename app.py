import os
import io
import uuid
from flask import Flask, request, jsonify, render_template
from celery import Celery
from PIL import Image
from flask import send_file
import cv2
import numpy as np
import psutil

# 1. Core Application Framework Setup
app = Flask(__name__)

# Ensure runtime paths exist for template matching
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.template_folder = os.path.join(BASE_DIR, 'templates')

# Fallback Configuration Values for Memory & Payload Protection
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB Absolute Threshold
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# 2. Hardwired Environment Evaluation for Celery
# Directly checks Render/OS environment strings to force execution bypass
is_eager = os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'False').lower() in ['true', '1', 'yes']

# Initialize Celery app instance
celery_app = Celery(app.name)

# Hardwire configurations directly onto Celery's core configuration object
celery_app.conf.update(
    broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    task_always_eager=is_eager,       # True forces completely local in-memory execution
    task_eager_propagates=True,        # Hands exceptions directly back to Flask thread
    worker_pool='solo'                 # Ensures stability across Windows & single-core containers
)

def allowed_file(filename):
    """Utility validator ensuring only valid visual matrices are ingested."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 3. Asynchronous Task Definition (Executes synchronously when Eager Mode is active)
@celery_app.task(name='tasks.execute_image_mutation')
def execute_image_mutation(file_bytes, filename, quality=85, width=None, height=None, crop_coords=None, target_format='original'):
    """Performs in-memory structural transformation on image arrays using Pillow & OpenCV."""
    try:
        # Load raw binary stream into a mutable Pillow Image sequence
        img = Image.open(io.BytesIO(file_bytes))
        
        # Phase A: Dynamic Spatial Cropping Matrix (via Cropper.js variables)
        if crop_coords:
            x, y, w, h = map(int, map(float, crop_coords.split(',')))
            img = img.crop((x, y, x + w, y + h))
            
        # Phase B: Resizing Matrix Resampling (Lanczos anti-aliasing interpolation)
        if width or height:
            orig_w, orig_h = img.size
            target_w = int(width) if width else int(orig_w * (int(height) / orig_h))
            target_h = int(height) if height else int(orig_h * (int(width) / orig_w))
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
        # Phase C: Format Determination Matrix
        orig_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpeg'
        if target_format == 'original':
            save_format = 'JPEG' if orig_ext in ['jpg', 'jpeg'] else orig_ext.upper()
        else:
            save_format = target_format.upper()
            
        if save_format == 'JPG':
            save_format = 'JPEG'

        # Convert back to standard RGB channels if migrating away from transparent layers
        if save_format == 'JPEG' and img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background

        # Phase D: Save to an in-memory memory stream to bypass disk latency
        output_buffer = io.BytesIO()
        img.save(output_buffer, format=save_format, quality=int(quality))
        mutated_bytes = output_buffer.getvalue()
        
        return {
            "status": "success",
            "filename": f"mutated_{uuid.uuid4().hex[:8]}.{save_format.lower()}",
            "original_name": filename,
            "bytes_length": len(mutated_bytes)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# 4. HTTP Route Matrix Controllers
@app.route('/', methods=['GET'])
def index():
    """Renders the workspace user interface."""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def system_health():
    """Monitors live hardware capacity inside the container boundary."""
    return jsonify({
        "status": "healthy",
        "cpu": f"{psutil.cpu_percent()}%",
        "memory": f"{psutil.virtual_memory().percent}%"
    })

@app.route('/api/process', methods=['POST'])
def submit_images():
    """Ingests image arrays, triggers mutation, and directly streams the resulting binary file download."""
    if 'images' not in request.files:
        return jsonify({"error": "No image array payload detected inside transaction headers."}), 400
        
    uploaded_files = request.files.getlist('images')
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({"error": "Null index parameter references inside file list."}), 400
        
    if len(uploaded_files) > 4:
        return jsonify({"error": "Batch threshold exceeded. Maximum slice limit is 4 items."}), 400

    quality = int(request.form.get('quality', 85))
    width = request.form.get('width') or None
    height = request.form.get('height') or None
    crop = request.form.get('crop') or None
    target_format = request.form.get('format', 'original')

    # For standard processing on a single-core web thread, take the first/active file
    file = uploaded_files[0]
    if file and allowed_file(file.filename):
        file_bytes = file.read()
        
        # Fire structural matrix calculation task (Synchronous in Eager Mode)
        task_result = execute_image_mutation(
            file_bytes, 
            file.filename,
            quality=quality,
            width=width,
            height=height,
            crop_coords=crop,
            target_format=target_format
        )
        
        if task_result.get("status") == "success":
            # Re-fetch the mutated raw byte arrays directly from memory
            # We must re-run the file loop directly inside our stream memory container
            img = Image.open(io.BytesIO(file_bytes))
            if crop:
                x, y, w, h = map(int, map(float, crop.split(',')))
                img = img.crop((x, y, x + w, y + h))
            if width or height:
                orig_w, orig_h = img.size
                target_w = int(width) if width else int(orig_w * (int(height) / orig_h))
                target_h = int(height) if height else int(orig_h * (int(width) / orig_w))
                img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                
            orig_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpeg'
            save_format = orig_ext.upper() if target_format == 'original' else target_format.upper()
            if save_format == 'JPG': save_format = 'JPEG'
            
            if save_format == 'JPEG' and img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background

            out_io = io.BytesIO()
            img.save(out_io, format=save_format, quality=quality)
            out_io.seek(0)
            
            # STREAM THE BINARY STRAIGHT BACK TO CLIENT AS A DOWNLOAD ATTACHMENT
            return send_file(
                out_io,
                mimetype=f"image/{save_format.lower()}",
                as_attachment=True,
                download_name=task_result["filename"]
            )
        else:
            return jsonify({"error": task_result.get("error", "Processing error")}), 500
            
    return jsonify({"error": "Invalid file selection parameter."}), 400
    
    if __name__ == '__main__':
        
        app.run(host='127.0.0.1', port=5000, debug=True)
