import os
import json
from datetime import datetime
from flask import Flask, request, render_template, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 请更改为安全的密钥

# 配置
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# 创建必要的目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# 初始化OCR模型
print("正在初始化OCR模型...")
ocr_pipeline = None

try:
    # 尝试使用ModelScope的pipeline接口
    from modelscope import pipeline
    
    # 使用文档理解pipeline
    ocr_pipeline = pipeline(
        task='document-understanding',
        model='damo/cv_convnextTiny_ocr-recognition-document_damo',
        model_revision='v1.0.0'
    )
    print("ModelScope OCR模型加载成功！")
    
except Exception as e:
    print(f"ModelScope模型加载失败: {e}")
    print("尝试使用备用OCR方案...")
    
    try:
        # 备用方案：使用pytesseract
        import pytesseract
        print("Tesseract OCR可用")
        ocr_pipeline = "tesseract"
    except ImportError:
        print("Tesseract不可用，将使用基础图像处理")
        ocr_pipeline = None

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ocr_with_modelscope(image_path):
    """使用ModelScope进行OCR识别"""
    try:
        if ocr_pipeline and hasattr(ocr_pipeline, '__call__'):
            # 使用ModelScope pipeline
            result = ocr_pipeline(image_path)
            
            # 处理结果
            if isinstance(result, dict):
                if 'text' in result:
                    return result['text']
                elif 'output' in result:
                    return str(result['output'])
                else:
                    return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return str(result)
        else:
            return "ModelScope OCR模型未正确加载"
            
    except Exception as e:
        return f"ModelScope OCR识别失败: {str(e)}"

def ocr_with_tesseract(image_path):
    """使用Tesseract进行OCR识别"""
    try:
        import pytesseract
        from PIL import Image
        
        # 打开图像
        image = Image.open(image_path)
        
        # 进行OCR识别，支持中英文
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        
        if text.strip():
            return text.strip()
        else:
            return "未识别到文字内容"
            
    except Exception as e:
        return f"Tesseract OCR识别失败: {str(e)}"

def ocr_with_basic(image_path):
    """基础OCR方案（仅返回图像信息）"""
    try:
        from PIL import Image
        
        # 获取图像基本信息
        with Image.open(image_path) as img:
            width, height = img.size
            mode = img.mode
            format_name = img.format
            
        return f"图像已成功处理\n文件路径: {image_path}\n图像尺寸: {width}x{height}\n颜色模式: {mode}\n文件格式: {format_name}\n\n注意: 当前使用基础图像处理模式，未进行文字识别。\n建议安装OCR依赖包以启用文字识别功能。"
        
    except Exception as e:
        return f"图像处理失败: {str(e)}"

def perform_ocr(image_path):
    """执行OCR识别，按优先级尝试不同方案"""
    # 方案1: ModelScope
    if ocr_pipeline and hasattr(ocr_pipeline, '__call__'):
        result = ocr_with_modelscope(image_path)
        if "失败" not in result:
            return result, "ModelScope"
    
    # 方案2: Tesseract
    if ocr_pipeline == "tesseract":
        result = ocr_with_tesseract(image_path)
        if "失败" not in result:
            return result, "Tesseract"
    
    # 方案3: 基础处理
    result = ocr_with_basic(image_path)
    return result, "Basic"

def save_result_to_json(filename, ocr_result, original_filename, model_used):
    """将OCR结果保存为JSON文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"{filename}_{timestamp}.json"
    json_path = os.path.join(OUTPUT_FOLDER, json_filename)
    
    result_data = {
        "timestamp": datetime.now().isoformat(),
        "original_filename": original_filename,
        "ocr_result": ocr_result,
        "processing_info": {
            "model": model_used,
            "status": "success" if "失败" not in ocr_result else "failed",
            "model_source": "ModelScope" if model_used == "ModelScope" else "Local"
        }
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    return json_path

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传和OCR识别"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    if file and allowed_file(file.filename):
        try:
            # 保存上传的文件
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_without_ext = os.path.splitext(filename)[0]
            file_extension = os.path.splitext(filename)[1]
            new_filename = f"{filename_without_ext}_{timestamp}{file_extension}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(file_path)
            
            # 进行OCR识别
            ocr_result, model_used = perform_ocr(file_path)
            
            # 保存结果到JSON文件
            json_path = save_result_to_json(filename_without_ext, ocr_result, filename, model_used)
            
            return jsonify({
                'success': True,
                'message': 'OCR识别完成',
                'ocr_result': ocr_result,
                'json_file': os.path.basename(json_path),
                'uploaded_file': new_filename,
                'model_info': model_used
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'处理失败: {str(e)}'
            })
    
    else:
        return jsonify({
            'success': False,
            'message': '不支持的文件格式，请上传图片文件（PNG, JPG, JPEG, GIF, BMP, WEBP）或PDF文件'
        })

@app.route('/results')
def list_results():
    """列出所有OCR结果文件"""
    try:
        json_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.json')]
        json_files.sort(reverse=True)  # 按时间倒序排列
        return jsonify({
            'success': True,
            'files': json_files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取结果列表失败: {str(e)}'
        })

@app.route('/model-status')
def model_status():
    """检查模型状态"""
    if ocr_pipeline and hasattr(ocr_pipeline, '__call__'):
        status = "ModelScope OCR已加载"
        model_name = "ModelScope Document Understanding"
    elif ocr_pipeline == "tesseract":
        status = "Tesseract OCR可用"
        model_name = "Tesseract OCR"
    else:
        status = "使用基础图像处理"
        model_name = "Basic Image Processing"
    
    return jsonify({
        'model_loaded': ocr_pipeline is not None,
        'model_name': model_name,
        'model_source': status,
        'available_models': {
            'modelscope': ocr_pipeline and hasattr(ocr_pipeline, '__call__'),
            'tesseract': ocr_pipeline == "tesseract",
            'basic': True
        }
    })

if __name__ == '__main__':
    print("=" * 50)
    print("OCR服务启动信息:")
    if ocr_pipeline and hasattr(ocr_pipeline, '__call__'):
        print("✅ ModelScope OCR模型已加载")
    elif ocr_pipeline == "tesseract":
        print("✅ Tesseract OCR可用")
    else:
        print("⚠️  使用基础图像处理模式")
    print(f"支持格式: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"最大文件大小: {MAX_FILE_SIZE // (1024*1024)}MB")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
