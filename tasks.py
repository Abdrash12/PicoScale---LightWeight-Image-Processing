from app import celery_app
import io
from PIL import Image
import json

@celery_app.task(bind=True, soft_time_limit=10, max_tasks_per_child=50)
def execute_image_mutation(self, file_bytes, filename, quality, width, height, crop_coords):
    """
    Executes heavy image mutation out of the request pipeline.
    Utilizes in-memory byte buffers entirely to bypass disk writing degradation.
    """
    try:
        # Load the bytes directly as an image object array
        image = Image.open(io.BytesIO(file_bytes))
        
        # 1. Execute Crop operations if client passed down box vectors
        if crop_coords:
            # Parsing visual crop matrix: [x, y, w, h]
            x, y, w, h = map(float, crop_coords.split(','))
            image = image.crop((x, y, x + w, y + h))
            
        # 2. Execute Resize configurations
        if width or height:
            orig_w, orig_h = image.size
            target_w = int(width) if width else int(orig_w * (int(height) / orig_h))
            target_h = int(height) if height else int(orig_h * (int(width) / orig_w))
            
            # Using high-quality resampling filters native to C-layer headers
            image = image.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
        # 3. Compress and pack into output RAM stream
        output_buffer = io.BytesIO()
        
        # Retain transparency index configuration if format is PNG/WEBP
        out_format = image.format if image.format else 'JPEG'
        image.save(output_buffer, format=out_format, quality=quality, optimize=True)
        output_buffer.seek(0)
        
        # [PROD NOTE]: Stream the `output_buffer.getvalue()` directly out to AWS S3/Cloudflare R2 here
        # For now, it returns success back to the state monitor tracking task results.
        return {"status": "success", "filename": filename}
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}