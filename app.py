import os
import json
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Please change to a secure key

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# OpenAI API configuration - for calling ModelScope MonkeyOCR
MONKEY_OCR_API_BASE = os.getenv('MONKEY_OCR_API_BASE', 'http://localhost:8000/v1')
MONKEY_OCR_API_KEY = os.getenv('MONKEY_OCR_API_KEY', 'EMPTY')
MONKEY_OCR_MODEL = os.getenv('MONKEY_OCR_MODEL', 'MonkeyOCR')

# Initialize OpenAI client for MonkeyOCR
print("Initializing MonkeyOCR client...")
ocr_client = None
ocr_status = "Not initialized"

try:
    ocr_client = OpenAI(
        api_key=MONKEY_OCR_API_KEY,
        base_url=MONKEY_OCR_API_BASE
    )
    
    # Test connection
    try:
        models = ocr_client.models.list()
        print(f"MonkeyOCR API connection successful! Available models: {[model.id for model in models.data]}")
        ocr_status = "Connected"
    except Exception as e:
        print(f"MonkeyOCR API connection test failed: {e}")
        ocr_status = "Connection failed"
        
except Exception as e:
    print(f"MonkeyOCR client initialization failed: {e}")
    ocr_status = "Initialization failed"

# Backup OCR initialization
backup_ocr = None
try:
    import pytesseract
    backup_ocr = "tesseract"
    print("Tesseract backup OCR available")
except ImportError:
    print("Tesseract not available")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def image_to_base64(image_path):
    """Convert image to base64 encoding"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Image encoding failed: {str(e)}")

def ocr_with_monkey_api(image_path):
    """Call MonkeyOCR model using OpenAI API format"""
    try:
        if not ocr_client:
            return "MonkeyOCR client not initialized"
        
        base64_image = image_to_base64(image_path)
        
        response = ocr_client.chat.completions.create(
            model=MONKEY_OCR_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please recognize all text content in this image, including text, tables, formulas, etc. Please output in the following format:\n1. Complete recognized text content\n2. If there are tables, please maintain table structure\n3. If there are special formats (such as titles, lists, etc.), please mark them\n4. Please ensure text accuracy and completeness"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096,
            temperature=0.1
        )
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content:
                return content.strip()
            else:
                return "MonkeyOCR returned no recognition result"
        else:
            return "MonkeyOCR API response format error"
            
    except Exception as e:
        return f"MonkeyOCR API call failed: {str(e)}"

def ocr_with_tesseract(image_path):
    """Use Tesseract for OCR recognition"""
    try:
        import pytesseract
        
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        
        if text.strip():
            return text.strip()
        else:
            return "No text content recognized"
            
    except Exception as e:
        return f"Tesseract OCR recognition failed: {str(e)}"

def ocr_with_basic(image_path):
    """Basic OCR solution (returns image information only)"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            mode = img.mode
            format_name = img.format
            
        return f"Image processed successfully\nFile path: {image_path}\nImage dimensions: {width}x{height}\nColor mode: {mode}\nFile format: {format_name}\n\nNote: Currently using basic image processing mode, no text recognition performed.\nRecommend configuring MonkeyOCR API or installing Tesseract to enable text recognition."
        
    except Exception as e:
        return f"Basic image processing failed: {str(e)}"

def perform_ocr(image_path):
    """Perform OCR recognition, try different solutions by priority"""
    # Solution 1: MonkeyOCR API
    if ocr_client and ocr_status == "Connected":
        result = ocr_with_monkey_api(image_path)
        if "failed" not in result and "error" not in result:
            return result, "MonkeyOCR API"
    
    # Solution 2: Tesseract
    if backup_ocr == "tesseract":
        result = ocr_with_tesseract(image_path)
        if "failed" not in result:
            return result, "Tesseract"
    
    # Solution 3: Basic processing
    result = ocr_with_basic(image_path)
    return result, "Basic"

def save_result_to_json(filename, ocr_result, original_filename, model_used):
    """Save OCR result to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"{filename}_{timestamp}.json"
    json_path = os.path.join(OUTPUT_FOLDER, json_filename)
    
    result_data = {
        "timestamp": datetime.now().isoformat(),
        "original_filename": original_filename,
        "ocr_result": ocr_result,
        "processing_info": {
            "model": model_used,
            "status": "success" if "failed" not in ocr_result else "failed",
            "api_endpoint": MONKEY_OCR_API_BASE if model_used == "MonkeyOCR API" else "Local",
            "model_name": MONKEY_OCR_MODEL if model_used == "MonkeyOCR API" else model_used
        }
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    return json_path

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and OCR recognition"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_without_ext = os.path.splitext(filename)[0]
            file_extension = os.path.splitext(filename)[1]
            new_filename = f"{filename_without_ext}_{timestamp}{file_extension}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(file_path)
            
            ocr_result, model_used = perform_ocr(file_path)
            json_path = save_result_to_json(filename_without_ext, ocr_result, filename, model_used)
            
            return jsonify({
                'success': True,
                'message': 'OCR recognition completed',
                'ocr_result': ocr_result,
                'json_file': os.path.basename(json_path),
                'uploaded_file': new_filename,
                'model_info': model_used,
                'api_info': {
                    'endpoint': MONKEY_OCR_API_BASE if model_used == "MonkeyOCR API" else "Local",
                    'model': MONKEY_OCR_MODEL if model_used == "MonkeyOCR API" else model_used
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Processing failed: {str(e)}'
            })
    
    else:
        return jsonify({
            'success': False,
            'message': 'Unsupported file format. Please upload image files (PNG, JPG, JPEG, GIF, BMP, WEBP) or PDF files'
        })

@app.route('/results')
def list_results():
    """List all OCR result files"""
    try:
        json_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.json')]
        json_files.sort(reverse=True)
        return jsonify({
            'success': True,
            'files': json_files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get result list: {str(e)}'
        })

@app.route('/download/<filename>')
def download_file(filename):
    """Download JSON result file"""
    try:
        # 安全检查：确保文件名只包含JSON文件且在output目录中
        if not filename.endswith('.json'):
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
        
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Download failed: {str(e)}'
        }), 500

@app.route('/model-status')
def model_status():
    """Check model status"""
    return jsonify({
        'monkey_ocr': {
            'status': ocr_status,
            'api_base': MONKEY_OCR_API_BASE,
            'model': MONKEY_OCR_MODEL,
            'available': ocr_client is not None and ocr_status == "Connected"
        },
        'backup_ocr': {
            'tesseract': backup_ocr == "tesseract",
            'basic': True
        },
        'current_priority': [
            "MonkeyOCR API" if ocr_status == "Connected" else None,
            "Tesseract" if backup_ocr == "tesseract" else None,
            "Basic"
        ]
    })

if __name__ == '__main__':
    print("=" * 60)
    print("OCR Service Startup Information:")
    print(f"MonkeyOCR API: {ocr_status}")
    if ocr_status == "Connected":
        print(f"  - API Address: {MONKEY_OCR_API_BASE}")
        print(f"  - Model Name: {MONKEY_OCR_MODEL}")
    print(f"Backup OCR: {'Tesseract available' if backup_ocr == 'tesseract' else 'Basic processing only'}")
    print(f"Supported formats: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"Maximum file size: {MAX_FILE_SIZE // (1024*1024)}MB")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
