from flask import Flask, request, jsonify
from config import Config
from flask import render_template 
from celery import Celery
import psutil

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Celery
celery_app = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery_app.conf.update(result_backend=app.config['CELERY_RESULT_BACKEND'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """Emergency Circuit Breaker endpoint tracking hardware health."""
    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    
    status = "healthy"
    # Trigger circuit breaker if system is failing
    if cpu_usage > 85 or memory.percent > 85:
        status = "overloaded"
        
    return jsonify({
        "status": status,
        "cpu": f"{cpu_usage}%",
        "memory": f"{memory.percent}%"
    }), 200 if status == "healthy" else 503

@app.route('/api/process', methods=['POST'])
def submit_images():
    # Emergency check before handling payload
    _, status_code = health_check()
    if status_code == 503:
        return jsonify({"error": "Server is under high load. Please try again shortly."}), 503

    if 'images' not in request.files:
        return jsonify({"error": "No image payload detected."}), 400
        
    files = request.files.getlist('images')
    
    # Strict Limit Guard
    if len(files) > Config.MAX_BATCH_FILES:
        return jsonify({"error": f"Max limit exceeded. You can only upload up to {Config.MAX_BATCH_FILES} images."}), 400
        
    task_ids = []
    
    for file in files:
        if file.filename == '':
            continue
            
        if not allowed_file(file.filename):
            return jsonify({"error": f"Unsupported format for file: {file.filename}"}), 422
            
        # Optimization: Read file explicitly as bytes directly into memory buffer (No Disk I/O)
        file_bytes = file.read()
        
        # Dispatch processing to the Celery worker pool
        from tasks import execute_image_mutation
        task = execute_image_mutation.delay(
            file_bytes, 
            file.filename,
            quality=int(request.form.get('quality', 85)),
            width=request.form.get('width', None),
            height=request.form.get('height', None),
            crop_coords=request.form.get('crop', None) # Expected format string: "x,y,w,h"
        )
        task_ids.append({"filename": file.filename, "task_id": task.id})
        
    return jsonify({"message": "Batch queued successfully", "tasks": task_ids}), 202
 

@app.route('/', methods=['GET'])
def index():
    """Serves the central user workspace utility."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)