from flask import Flask, request, jsonify, send_file
import os
import json
import tempfile
from lib.bundle_generator import BundleGenerator
from lib.firebase_handler import FirebaseHandler

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

@app.route('/generate-bundle', methods=['POST'])
def generate_bundle():
    """Generate a bundle for a specific collection path."""
    data = request.get_json()
    collection_path = data.get('collection_path')
    
    if not collection_path:
        return jsonify({'error': 'collection_path is required'}), 400
    
    try:
        firebase_handler = FirebaseHandler()
        bundle_generator = BundleGenerator(firebase_handler)
        
        bundle_data = bundle_generator.generate_bundle(collection_path)
        
        # Decide whether to save file or return JSON based on the request
        if data.get('save_bundle', False):
            output_dir = data.get('output_dir')
            filepath = bundle_generator.save_bundle(bundle_data, collection_path, output_dir)
            return jsonify({
                'success': True,
                'message': f'Bundle saved to {filepath}',
                'filepath': filepath
            }), 200
        else:
            return jsonify(bundle_data), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-bundle', methods=['POST'])
def download_bundle():
    """Generate a bundle for a specific collection and return it as a downloadable file."""
    data = request.get_json()
    collection_path = data.get('collection_path')
    
    if not collection_path:
        return jsonify({'error': 'collection_path is required'}), 400
    
    try:
        firebase_handler = FirebaseHandler()
        bundle_generator = BundleGenerator(firebase_handler)
        
        bundle_data = bundle_generator.generate_bundle(collection_path)
        
        # Create a temporary file to serve
        temp_dir = tempfile.gettempdir()
        filename = f"{collection_path.replace('/', '_')}.json"
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(bundle_data, f, ensure_ascii=False, indent=2)
        
        return send_file(
            filepath,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-all-bundles', methods=['POST'])
def generate_all_bundles():
    """Generate bundles for all imp trophy collections."""
    data = request.get_json() or {}
    output_dir = data.get('output_dir')
    
    try:
        year = data.get('year')
        firebase_handler = FirebaseHandler(year=year)
        bundle_generator = BundleGenerator(firebase_handler)
        
        filepaths = bundle_generator.generate_all_bundles(output_dir)
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(filepaths)} bundle files',
            'filepaths': filepaths
        }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use PORT environment variable provided by Cloud Run, default to 8080
    port = int(os.environ.get('PORT', 8080))
    # Run on all interfaces and specified port
    app.run(host='0.0.0.0', port=port)
