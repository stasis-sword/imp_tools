import os
import logging

from flask import Flask, request, jsonify, redirect, make_response
from waitress import serve
from firebase_admin import auth
from functools import wraps
from google.auth import transport
from google.oauth2 import id_token

from lib.bundle_generator import BundleGenerator
from lib.firebase_handler import FirebaseHandler
from lib.flags import FlagHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
FLAG_HANDLER = FlagHandler()

def verify_firebase_token(f):
    """
    Verify authentication token. Accepts both:
    1. Firebase user ID tokens (for end-user authentication)
    2. Google Identity Tokens (for service-to-service authentication)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
            
        token = auth_header.split('Bearer ')[1]
        
        # First, try to verify as Firebase user token (for backward compatibility)
        try:
            decoded_token = auth.verify_id_token(token)
            request.user = decoded_token
            request.auth_type = 'firebase_user'
            return f(*args, **kwargs)
        except Exception as firebase_error:
            # If Firebase verification fails, try as Google Identity Token (service-to-service)
            try:
                # Prefer explicit audience. Fall back to current service root URL.
                host = request.host
                forwarded_proto = request.headers.get('X-Forwarded-Proto')
                # Cloud Run often terminates TLS upstream; Flask may see `http://...` even when the
                # ID token audience was minted for `https://...`. Accept both schemes.
                https_audience = f'https://{host}'
                http_audience = f'http://{host}'
                candidates = []

                explicit = os.environ.get('CLOUD_RUN_SERVICE_URL')
                if explicit:
                    candidates.append(explicit.rstrip('/'))

                if forwarded_proto:
                    candidates.append(f'{forwarded_proto}://{host}')

                candidates.extend([https_audience, http_audience])
                # De-dupe while preserving order
                candidates = list(dict.fromkeys([c.rstrip('/') for c in candidates if c]))

                decoded_token = None
                last_error = None
                logger.info(f'Identity token audience candidates: {candidates}')
                for aud in candidates:
                    try:
                        decoded_token = id_token.verify_token(
                            token,
                            transport.requests.Request(),
                            audience=aud
                        )
                        break
                    except Exception as e:
                        last_error = e
                        logger.info(f'Identity token verify failed for aud={aud}: {e}')

                if decoded_token is None:
                    raise last_error
                
                request.user = decoded_token
                request.auth_type = 'service_account'
                return f(*args, **kwargs)
            except Exception as identity_error:
                logger.warning(f"Token verification failed: Firebase error: {firebase_error}, Identity error: {identity_error}")
                return jsonify({
                    'error': 'Invalid authentication token',
                    'details': 'Token must be either a Firebase user ID token or a Google Identity Token'
                }), 401
    return decorated_function

def generate_cacheless_redirect_response(redirect_url):
    """Create redirect response with no-cache headers"""
    response = make_response(redirect(redirect_url, code=302))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

@app.route('/generate-bundle', methods=['POST'])
@verify_firebase_token
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
        
        # # Decide whether to save file or return JSON based on the request
        # if data.get('save_bundle', False):
        #     output_dir = data.get('output_dir')
        #     filepath = bundle_generator.save_bundle(bundle_data, collection_path, output_dir)
        #     return jsonify({
        #         'success': True,
        #         'message': f'Bundle saved to {filepath}',
        #         'filepath': filepath,
        #         'bundle_name': collection_path.replace('/', '_'),
        #         'size': len(str(bundle_data).encode('utf-8')),
        #         'document_count': bundle_data["metadata"]["totalDocuments"]
        #     }), 200
        # else:
        return jsonify(bundle_data), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-all-bundles', methods=['POST'])
@verify_firebase_token
def generate_all_bundles():
    """Generate bundles for all imp trophy collections and return them."""
    data = request.get_json() or {}
    output_dir = data.get('output_dir')
    
    try:
        year = data.get('year')
        firebase_handler = FirebaseHandler(year=year)
        bundle_generator = BundleGenerator(firebase_handler)
        
        result = bundle_generator.generate_all_bundles()
         
        return jsonify({
            'success': True,
            'message': f'Generated {result["total_bundles"]} bundle files',
            'result': result
        }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/images/random-flag', methods=['GET'])
def serve_random_flag():
    """
    Redirect to a random flag image URL on SA servers.
    """
    try:
        redirect_url = FLAG_HANDLER.get_random_flag_url()
        return generate_cacheless_redirect_response(redirect_url)
    except Exception as e:
        logger.error(f"Error redirecting to image: {str(e)}")
        return jsonify({'error': 'Failed to redirect to image'}), 500

@app.route('/images/random-flag-with-creator', methods=['GET'])
def serve_random_flag_with_creator():
    """
    Redirect to a random flag URL with its creator as a query parameter.
    """
    try:
        redirect_url = FLAG_HANDLER.get_random_flag_url(True)
        return generate_cacheless_redirect_response(redirect_url)
    except Exception as e:
        logger.error(f"Error redirecting to image with creator: {str(e)}")
        return jsonify({'error': 'Failed to redirect to image'}), 500

@app.route('/flags', methods=['GET'])
@verify_firebase_token
def get_flags():
    """
    Return a list of all flags with their URLs and metadata.
    """
    try:
        flags = FLAG_HANDLER.flags
        flags_with_urls = []
        
        for flag in flags:
            flag_url = FLAG_HANDLER.generate_flag_url(flag)
            flags_with_urls.append({
                'name': flag.name,
                'by': flag.by,
                'image_url': flag_url
            })
        
        return jsonify(flags_with_urls), 200
    except Exception as e:
        logger.error(f"Error retrieving flags: {str(e)}")
        return jsonify({'error': 'Failed to retrieve flags'}), 500

if __name__ == '__main__':
    # Use PORT environment variable provided by Cloud Run, default to 8080
    port = int(os.environ.get('PORT', 8080))
    serve(app, host='0.0.0.0', port=port)
