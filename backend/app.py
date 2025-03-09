from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import subprocess
import tempfile
import shutil

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'stl', 'obj', 'step', 'stp', 'iges', 'igs', 'gltf', 'glb'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Generate a unique filename to prevent collisions
        original_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{original_ext}"

        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)

        # Add metadata extraction if appropriate
        metadata = extract_model_metadata(file_path, original_ext)

        return jsonify({
            'success': True,
            'filename': unique_filename,
            'originalName': file.filename,
            'fileType': original_ext,
            'metadata': metadata
        })

    return jsonify({'error': 'File type not allowed'}), 400

def extract_model_metadata(file_path, file_ext):
    """Extract basic metadata from the 3D model file"""
    metadata = {}
    
    # For future expansion, you could add more sophisticated metadata extraction
    # This could include using libraries like numpy-stl for STL files
    # or other parsers for different formats
    
    # For now, return file size as basic metadata
    try:
        file_size = os.path.getsize(file_path)
        metadata['fileSize'] = file_size
        metadata['fileSizeFormatted'] = format_file_size(file_size)
    except Exception:
        pass
    
    return metadata

def format_file_size(size_in_bytes):
    """Format file size in a human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

@app.route('/api/files', methods=['GET'])
def list_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # Get file metadata
            file_size = os.path.getsize(file_path)
            file_type = filename.rsplit('.', 1)[1].lower()
            
            files.append({
                'filename': filename,
                'fileType': file_type,
                'fileSize': file_size,
                'fileSizeFormatted': format_file_size(file_size),
                'dateModified': os.path.getmtime(file_path)
            })
    
    # Sort files by date modified (newest first)
    files.sort(key=lambda x: x['dateModified'], reverse=True)
    
    # Remove the dateModified field as it's only used for sorting
    for file in files:
        del file['dateModified']
        
    return jsonify(files)

@app.route('/api/files/<filename>', methods=['GET'])
def get_file(filename):
    # Ensure the file path is correct by using the absolute path
    return send_from_directory(os.path.abspath(UPLOAD_FOLDER), filename)

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True})
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert', methods=['POST'])
def convert_file():
    """Convert a CAD file from one format to another"""
    data = request.json
    if not data or 'filename' not in data or 'targetFormat' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    source_filename = data['filename']
    target_format = data['targetFormat'].lower()
    
    if target_format not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Unsupported target format: {target_format}'}), 400
    
    try:
        source_path = os.path.join(UPLOAD_FOLDER, source_filename)
        if not os.path.exists(source_path):
            return jsonify({'error': 'Source file not found'}), 404
        
        # Generate target filename
        source_name = source_filename.rsplit('.', 1)[0]
        target_filename = f"{source_name}_converted_{uuid.uuid4().hex[:8]}.{target_format}"
        target_path = os.path.join(UPLOAD_FOLDER, target_filename)
        
        # Perform the conversion
        # This is a simplified example. For a production app, you would:
        # 1. Use a dedicated CAD conversion library or tool (e.g., FreeCAD Python API)
        # 2. Implement proper error handling and progress tracking
        # 3. Support a wider range of conversion paths
        
        # For this example, we'll just implement a basic STL<->OBJ conversion
        # using simple file copying (in a real app, use actual conversion libraries)
        source_ext = source_filename.rsplit('.', 1)[1].lower()
        
        if (source_ext == 'stl' and target_format == 'obj') or (source_ext == 'obj' and target_format == 'stl'):
            # Simulate a conversion by copying the file
            # In a real app, you would use proper conversion libraries
            shutil.copy(source_path, target_path)
            
            return jsonify({
                'success': True,
                'originalFilename': source_filename,
                'convertedFilename': target_filename,
                'targetFormat': target_format
            })
        else:
            return jsonify({'error': f'Conversion from {source_ext} to {target_format} is not supported'}), 400
        
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)