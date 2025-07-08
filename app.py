import os
import json
import zipfile
import shutil
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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf', 'zip'}
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
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

def is_image_file(filename):
    """Check if file is an image"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS

def extract_zip_file(zip_path, extract_to):
    """Extract ZIP file and return list of image files"""
    try:
        image_files = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of files in ZIP
            file_list = zip_ref.namelist()
            
            # Filter image files
            for file_name in file_list:
                if is_image_file(file_name) and not file_name.startswith('__MACOSX/'):
                    # Extract file
                    zip_ref.extract(file_name, extract_to)
                    extracted_path = os.path.join(extract_to, file_name)
                    image_files.append(extracted_path)
        
        return image_files, None
    except Exception as e:
        return [], f"ZIP extraction failed: {str(e)}"

def process_zip_batch(zip_path, zip_filename, output_format='json'):
    """Process all images in a ZIP file"""
    try:
        # Create temporary extraction directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_extract_dir = os.path.join(UPLOAD_FOLDER, f"temp_{timestamp}")
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        # Extract ZIP file
        image_files, error = extract_zip_file(zip_path, temp_extract_dir)
        if error:
            return None, error
        
        if not image_files:
            return None, "No image files found in ZIP archive"
        
        # Create output directory for this ZIP
        zip_name_without_ext = os.path.splitext(zip_filename)[0]
        output_dir = os.path.join(OUTPUT_FOLDER, f"{zip_name_without_ext}_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process each image
        results = []
        for image_path in image_files:
            try:
                # Get relative filename for JSON naming
                rel_path = os.path.relpath(image_path, temp_extract_dir)
                filename_without_ext = os.path.splitext(os.path.basename(rel_path))[0]
                
                # Perform OCR
                ocr_result, model_used = perform_ocr(image_path)
                
                # Save result to specified format in the ZIP-specific output directory
                # Temporarily change OUTPUT_FOLDER to the ZIP-specific directory
                original_output_folder = OUTPUT_FOLDER
                globals()['OUTPUT_FOLDER'] = output_dir
                
                try:
                    result_path = save_result_to_file(filename_without_ext, ocr_result, rel_path, model_used, output_format)
                    result_filename = os.path.basename(result_path)
                finally:
                    # Restore original OUTPUT_FOLDER
                    globals()['OUTPUT_FOLDER'] = original_output_folder
                
                results.append({
                    "image_file": rel_path,
                    "result_file": result_filename,
                    "output_format": output_format,
                    "ocr_result": ocr_result,
                    "model_used": model_used,
                    "status": "success" if "failed" not in ocr_result else "failed"
                })
                
            except Exception as e:
                results.append({
                    "image_file": os.path.relpath(image_path, temp_extract_dir),
                    "result_file": None,
                    "output_format": output_format,
                    "ocr_result": f"Processing failed: {str(e)}",
                    "model_used": "None",
                    "status": "failed"
                })
        
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_extract_dir)
        except:
            pass
        
        return {
            "output_directory": os.path.basename(output_dir),
            "total_images": len(image_files),
            "processed_results": results,
            "success_count": len([r for r in results if r["status"] == "success"]),
            "failed_count": len([r for r in results if r["status"] == "failed"])
        }, None
        
    except Exception as e:
        # Clean up on error
        try:
            if 'temp_extract_dir' in locals():
                shutil.rmtree(temp_extract_dir)
        except:
            pass
        return None, f"ZIP processing failed: {str(e)}"

def image_to_base64(image_path):
    """Convert image to base64 encoding"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Image encoding failed: {str(e)}")

def ocr_with_monkey_api(image_path, image_type='document'):
    """Call MonkeyOCR model using OpenAI API format"""
    try:
        if not ocr_client:
            return "MonkeyOCR client not initialized"
        
        base64_image = image_to_base64(image_path)
        
        # Choose prompt based on image type
        if image_type == 'table':
            prompt_text = "Please recognize all content in this table image and output it in a structured table format. Requirements:\n1. Identify all table headers, rows, and columns accurately\n2. Preserve the exact table structure and cell relationships\n3. Use consistent spacing or tab characters to align columns\n4. Maintain the original row order and column sequence\n5. Include all cell content including numbers, text, and symbols\n6. For merged cells, indicate the span appropriately\n7. Preserve any table formatting like borders or separators using text characters (|, -, +)\n8. Output should be readable as a plain text table that maintains the original structure\n9. Include table headers if present\n10. Ensure the output can be easily converted to CSV or Excel format"
        else:  # document type
            prompt_text = "Please recognize all text content in this image and output it exactly as it appears in the original image layout. Requirements:\n1. Preserve the exact spatial layout and formatting of the original image\n2. Maintain all spacing, indentation, line breaks, and alignment as shown\n3. For tables: preserve column alignment and row structure using spaces or tabs\n4. For multi-column text: maintain the column layout and reading order\n5. For titles, headings, and special formatting: preserve their visual hierarchy and positioning\n6. Keep all original punctuation, symbols, and special characters\n7. Do not add any explanatory text or formatting markers - output only the recognized content in its original layout\n8. If text appears in different sizes or styles, maintain the relative positioning but output as plain text\n9. Preserve any mathematical formulas or equations in their original format\n10. Ensure the output can be directly used to recreate the visual layout of the original document"
        
        response = ocr_client.chat.completions.create(
            model=MONKEY_OCR_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
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

def perform_ocr(image_path, image_type='document'):
    """Perform OCR recognition, try different solutions by priority"""
    # Solution 1: MonkeyOCR API
    if ocr_client and ocr_status == "Connected":
        result = ocr_with_monkey_api(image_path, image_type)
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

def save_result_to_file(filename, ocr_result, original_filename, model_used, output_format='json'):
    """Save OCR result to specified format file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if output_format == 'json':
        result_filename = f"{filename}_{timestamp}.json"
        result_path = os.path.join(OUTPUT_FOLDER, result_filename)
        
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
        
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
            
    elif output_format == 'txt':
        result_filename = f"{filename}_{timestamp}.txt"
        result_path = os.path.join(OUTPUT_FOLDER, result_filename)
        
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(f"Recognition Time: {datetime.now().isoformat()}\n")
            f.write(f"Original Filename: {original_filename}\n")
            f.write(f"Recognition Model: {model_used}\n")
            f.write(f"Processing Status: {'Success' if 'failed' not in ocr_result else 'Failed'}\n")
            f.write("\n")
            f.write("Recognition Result:\n")
            f.write(ocr_result)
            
    elif output_format == 'xlsx':
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment
            
            result_filename = f"{filename}_{timestamp}.xlsx"
            result_path = os.path.join(OUTPUT_FOLDER, result_filename)
            
            wb = Workbook()
            ws = wb.active
            ws.title = "OCR Recognition Result"
            
            # Set title style
            title_font = Font(bold=True, size=12)
            
            # Add headers and data
            ws['A1'] = "Item"
            ws['B1'] = "Content"
            ws['A1'].font = title_font
            ws['B1'].font = title_font
            
            ws['A2'] = "Recognition Time"
            ws['B2'] = datetime.now().isoformat()
            
            ws['A3'] = "Original Filename"
            ws['B3'] = original_filename
            
            ws['A4'] = "Recognition Model"
            ws['B4'] = model_used
            
            ws['A5'] = "Processing Status"
            ws['B5'] = "Success" if "failed" not in ocr_result else "Failed"
            
            ws['A6'] = "Recognition Result"
            ws['B6'] = ocr_result
            
            # Set column width
            ws.column_dimensions['A'].width = 15
            ws.column_dimensions['B'].width = 50
            
            # Set text wrapping
            for row in ws.iter_rows(min_row=2, max_row=6, min_col=2, max_col=2):
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
            
            wb.save(result_path)
            
        except ImportError:
            # If openpyxl is not installed, fallback to JSON format
            return save_result_to_file(filename, ocr_result, original_filename, model_used, 'json')
    
    return result_path

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
            file_extension = os.path.splitext(filename)[1].lower()
            new_filename = f"{filename_without_ext}_{timestamp}{file_extension}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(file_path)
            
            # Check if uploaded file is a ZIP
            if file_extension == '.zip':
                # Get output format from form data
                output_format = request.form.get('output_format', 'json')
                
                # Process ZIP file
                batch_result, error = process_zip_batch(file_path, filename, output_format)
                
                if error:
                    return jsonify({
                        'success': False,
                        'message': f'ZIP processing failed: {error}'
                    })
                
                return jsonify({
                    'success': True,
                    'message': f'ZIP file processed successfully in {output_format.upper()} format. {batch_result["success_count"]} images processed, {batch_result["failed_count"]} failed.',
                    'file_type': 'zip',
                    'output_format': output_format,
                    'uploaded_file': new_filename,
                    'output_directory': batch_result['output_directory'],
                    'batch_results': {
                        'total_images': batch_result['total_images'],
                        'success_count': batch_result['success_count'],
                        'failed_count': batch_result['failed_count'],
                        'processed_results': batch_result['processed_results']
                    }
                })
            else:
                # Get output format and image type from form data
                output_format = request.form.get('output_format', 'json')
                image_type = request.form.get('image_type', 'document')
                
                # Process single image file
                ocr_result, model_used = perform_ocr(file_path, image_type)
                result_path = save_result_to_file(filename_without_ext, ocr_result, filename, model_used, output_format)
                
                return jsonify({
                    'success': True,
                    'message': f'OCR recognition completed, saved as {output_format.upper()} format',
                    'file_type': 'image',
                    'ocr_result': ocr_result,
                    'result_file': os.path.basename(result_path),
                    'output_format': output_format,
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
    """List all OCR result files and batch processing directories"""
    try:
        results = {
            'single_files': [],
            'batch_directories': []
        }
        
        # Scan output directory
        for item in os.listdir(OUTPUT_FOLDER):
            item_path = os.path.join(OUTPUT_FOLDER, item)
            
            if os.path.isfile(item_path) and (item.endswith('.json') or item.endswith('.txt') or item.endswith('.xlsx')):
                # Single result files (JSON, TXT, XLSX)
                results['single_files'].append(item)
            elif os.path.isdir(item_path):
                # Batch processing directories
                dir_info = {
                    'name': item,
                    'files': [],
                    'created_time': os.path.getctime(item_path)
                }
                
                # List result files in the directory (JSON, TXT, XLSX)
                try:
                    for file in os.listdir(item_path):
                        if file.endswith('.json') or file.endswith('.txt') or file.endswith('.xlsx'):
                            file_path = os.path.join(item_path, file)
                            dir_info['files'].append({
                                'name': file,
                                'size': os.path.getsize(file_path),
                                'modified_time': os.path.getmtime(file_path)
                            })
                    
                    # Sort files by modification time (newest first)
                    dir_info['files'].sort(key=lambda x: x['modified_time'], reverse=True)
                    results['batch_directories'].append(dir_info)
                except Exception as e:
                    print(f"Error reading directory {item}: {e}")
        
        # Sort single files and directories by creation time (newest first)
        results['single_files'].sort(reverse=True)
        results['batch_directories'].sort(key=lambda x: x['created_time'], reverse=True)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get result list: {str(e)}'
        })

@app.route('/download/<filename>')
def download_file(filename):
    """Download result file from root output directory"""
    try:
        # Security check: ensure filename contains only supported file formats
        if not (filename.endswith('.json') or filename.endswith('.txt') or filename.endswith('.xlsx')):
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
        
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        # Set MIME type based on file type
        if filename.endswith('.json'):
            mimetype = 'application/json'
        elif filename.endswith('.txt'):
            mimetype = 'text/plain'
        elif filename.endswith('.xlsx'):
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Download failed: {str(e)}'
        }), 500

@app.route('/download/<directory>/<filename>')
def download_batch_file(directory, filename):
    """Download result file from batch processing directory"""
    try:
        # Security check: ensure filename contains only supported file formats
        if not (filename.endswith('.json') or filename.endswith('.txt') or filename.endswith('.xlsx')):
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
        
        # Security check: prevent path traversal attacks
        if '..' in directory or '/' in directory or '\\' in directory:
            return jsonify({'success': False, 'message': 'Invalid directory name'}), 400
        
        # Build file path
        dir_path = os.path.join(OUTPUT_FOLDER, directory)
        file_path = os.path.join(dir_path, filename)
        
        # Check if directory exists
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            return jsonify({'success': False, 'message': 'Directory not found'}), 404
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        # Set MIME type based on file type
        if filename.endswith('.json'):
            mimetype = 'application/json'
        elif filename.endswith('.txt'):
            mimetype = 'text/plain'
        elif filename.endswith('.xlsx'):
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
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
