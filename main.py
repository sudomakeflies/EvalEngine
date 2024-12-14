import os
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from local_storage import scan_local_folder_and_get_documents
from my_nlp import process_documents
from task_manager import create_task
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='src')

# Configure upload folder
UPLOAD_FOLDER = 'documentos'
ALLOWED_EXTENSIONS = {'txt', 'doc', 'docx', 'pdf', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    try:
        logger.info("Serving index.html")
        return send_from_directory('src', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents')
def get_documents():
    """
    Returns a list of all documents in the documents folder
    """
    try:
        logger.info("Getting list of documents")
        documents = []
        folder_path = 'documentos'  # Use hardcoded path instead of env variable
        
        # List all files in the documentos folder
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if os.path.isfile(os.path.join(folder_path, file)) and not file.startswith('.'):
                    documents.append(file)
            
            logger.info(f"Found {len(documents)} documents")
            return jsonify({"documents": documents})
        else:
            logger.warning(f"Documents folder not found: {folder_path}")
            return jsonify({"documents": []})
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """
    Handles file uploads to the documents folder
    """
    try:
        logger.info("Processing file upload request")
        if 'files' not in request.files:
            logger.warning("No files provided in request")
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        uploaded_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                logger.info(f"Saving file: {filename}")
                file.save(file_path)
                uploaded_files.append(filename)
            else:
                logger.warning(f"Invalid file type: {file.filename}")
        
        if not uploaded_files:
            return jsonify({'error': 'No valid files to upload'}), 400

        logger.info(f"Successfully uploaded {len(uploaded_files)} files")
        return jsonify({
            'message': f'Successfully uploaded {len(uploaded_files)} files',
            'files': uploaded_files
        })
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<filename>', methods=['DELETE'])
def delete_document(filename):
    """
    Deletes a specific document from the documents folder
    """
    try:
        logger.info(f"Attempting to delete file: {filename}")
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Successfully deleted file: {filename}")
            return jsonify({'message': f'Successfully deleted {filename}'})
        logger.warning(f"File not found: {filename}")
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/process', methods=['POST'])
def process_with_guidelines():
    """
    Processes documents with specific guidelines and generates drafts
    """
    try:
        logger.info("Starting document processing")
        data = request.get_json()
        if not data or 'guidelines' not in data:
            logger.warning("No guidelines provided in request")
            return jsonify({'error': 'No guidelines provided'}), 400

        folder_path = 'documentos'  # Use hardcoded path instead of env variable
        documents = scan_local_folder_and_get_documents(folder_path)
        
        if not documents:
            logger.warning("No documents found to process")
            return jsonify({'error': 'No documents found to process'}), 400
        
        # Process documents with the provided guidelines
        logger.info("Processing documents with guidelines")
        processed_data = process_documents(documents, guidelines=data['guidelines'])
        
        # Check for errors in processed data
        if 'error' in processed_data:
            logger.error(f"Error in document processing: {processed_data['error']}")
            return jsonify({'error': processed_data['error']}), 500

        # Extract Annex 2 and 5 from processed data
        logger.info("Document processing completed successfully")
        return jsonify({
            'annex2': processed_data.get('annex2', 'No content generated for Annex 2'),
            'annex5': processed_data.get('annex5', 'No content generated for Annex 5')
        })
    except Exception as e:
        logger.error(f"Error in process_with_guidelines: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/create_event', methods=['POST'])
def create_event():
    """
    Creates an event in Google Calendar.
    """
    try:
        logger.info("Creating calendar event")
        event_details = request.get_json()
        create_task(event_details)
        logger.info("Event created successfully")
        return jsonify({'message': 'Event created successfully'})
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    logger.info("Starting Flask application")
    app.run(debug=True)
