import os
import json
from datetime import datetime
from firebase_admin import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
from google.protobuf.timestamp_pb2 import Timestamp
from pathlib import Path

class BundleGenerator:
    def __init__(self, firebase_handler=None):
        """
        Initialize the bundle generator.
        
        Args:
            firebase_handler: Optional FirebaseHandler instance. If not provided, 
                              will create one.
        """
        if firebase_handler:
            self.firebase = firebase_handler
        else:
            # Import here to avoid circular imports
            from .firebase_handler import FirebaseHandler
            self.firebase = FirebaseHandler()
            
        self.db = self.firebase.db_client
        self.output_dir = os.environ.get('BUNDLE_OUTPUT_DIR', 'bundles')

    def create_bundle_metadata(self) -> dict:
        """Create metadata for the bundle."""
        return {
            "version": 1,
            "createTime": datetime.utcnow().isoformat(),
            "totalDocuments": 0,  # Will be updated later
            "totalBytes": 0,  # Will be updated later
        }

    def encode_document(self, doc: DocumentSnapshot) -> dict:
        """Encode a Firestore document into bundle format."""
        def convert_timestamp(timestamp):
            if isinstance(timestamp, datetime):
                return timestamp.isoformat()
            elif isinstance(timestamp, Timestamp):
                return datetime.fromtimestamp(timestamp.seconds + timestamp.nanos/1e9).isoformat()
            return timestamp

        def convert_value(value):
            if isinstance(value, (datetime, Timestamp)):
                return convert_timestamp(value)
            elif isinstance(value, firestore.DocumentReference):
                return value.path
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_value(v) for v in value]
            return value

        fields = doc.to_dict()
        fields = convert_value(fields)

        return {
            "name": doc.reference.path,
            "createTime": convert_timestamp(doc.create_time),
            "updateTime": convert_timestamp(doc.update_time),
            "fields": fields
        }

    def generate_bundle(self, collection_path: str) -> dict:
        """Generate a Firestore bundle from a collection path."""
        bundle = {
            "metadata": self.create_bundle_metadata(),
            "namedQueries": {},
            "documents": []
        }
        
        total_bytes = 0
        collection_ref = self.db.collection(collection_path)
        docs = collection_ref.stream()
        
        for doc in docs:
            encoded_doc = self.encode_document(doc)
            bundle["documents"].append(encoded_doc)
            total_bytes += len(str(encoded_doc).encode('utf-8'))
        
        bundle["metadata"]["totalDocuments"] = len(bundle["documents"])
        bundle["metadata"]["totalBytes"] = total_bytes
        
        return bundle

    def save_bundle(self, bundle_data: dict, collection_path: str, output_dir=None):
        """
        Save bundle to the specified directory.
        
        Args:
            bundle_data: The bundle data to save
            collection_path: The collection path used for naming
            output_dir: Optional custom output directory, defaults to self.output_dir
        
        Returns:
            The path to the saved bundle file
        """
        # Create a normalized filename
        filename = f"{collection_path.replace('/', '_')}.json"
        
        # Determine output directory
        if output_dir is None:
            output_dir = self.output_dir
            
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Create the full filepath
        filepath = os.path.join(output_dir, filename)
        
        # Save the bundle
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(bundle_data, f, ensure_ascii=False, indent=2)
        
        print(f"Saved bundle to {filepath}")
        return filepath

    def get_all_imp_collections(self) -> list:
        """Get all imp trophy collections for the current year."""
        collections = []
        imps_ref = self.db.collection('imps')
        
        for imp_doc in imps_ref.stream():
            imp_name = imp_doc.id
            collection_path = f"imps/{imp_name}/trophies{self.firebase.year}"
            collections.append(collection_path)
        
        return collections

    def generate_all_bundles(self, output_dir=None):
        """
        Generate bundles for all imp trophy collections.
        
        Args:
            output_dir: Optional custom output directory
        
        Returns:
            List of generated bundle filepaths
        """
        # Get all imp collections
        collections = self.get_all_imp_collections()
        
        print(f"Found {len(collections)} imp collections to process")
        
        generated_files = []
        
        for collection_path in collections:
            print(f"Generating bundle for {collection_path}")
            bundle_data = self.generate_bundle(collection_path)
            filepath = self.save_bundle(bundle_data, collection_path, output_dir)
            generated_files.append(filepath)
            print(f"Generated bundle with {bundle_data['metadata']['totalDocuments']} documents")
        
        return generated_files 
