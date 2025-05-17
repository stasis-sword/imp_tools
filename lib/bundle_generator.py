import os
import json
from datetime import datetime
from firebase_admin import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
import pytz

class BundleGenerator:
    def __init__(self, firebase_handler):
        self.firebase = firebase_handler
        self.db = self.firebase.db_client
        self.output_dir = os.environ.get('BUNDLE_OUTPUT_DIR', 'bundles')
        self.club_timezone = pytz.timezone('US/Eastern')

    def create_bundle_metadata(self) -> dict:
        """Create metadata for the bundle."""
        return {
            "version": 1,
            "createTime": datetime.now(self.club_timezone).isoformat(),
            "totalDocuments": 0,  # Will be updated later
            "totalBytes": 0,  # Will be updated later
        }

    def _json_default(self, obj):
        """Default handler for JSON serialization of non-standard types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, firestore.DocumentReference):
            return obj.path
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def encode_document(self, doc: DocumentSnapshot) -> dict:
        """Encode a Firestore document into bundle format."""
        fields = doc.to_dict()
        
        # Convert the document to a dict and serialize to JSON and back to 
        # handle all conversions
        doc_dict = {
            "name": doc.reference.path,
            "createTime": doc.create_time,
            "updateTime": doc.update_time,
            "fields": fields
        }

        json_str = json.dumps(doc_dict, default=self._json_default)
        return json.loads(json_str)

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
            # encoded_doc = self.encode_document(doc)
            bundle["documents"].append(doc)
            total_bytes += len(str(doc).encode('utf-8'))

        bundle["metadata"]["totalDocuments"] = len(bundle["documents"])
        bundle["metadata"]["totalBytes"] = total_bytes

        return bundle

    def save_bundle(self, bundle_data: dict, collection_path: str):
        """
        Save bundle to the specified directory.
        
        Args:
            bundle_data: The bundle data to save
            collection_path: The collection path used for naming
        
        Returns:
            The path to the saved bundle file
        """
        # Create a normalized filename
        filename = f"{collection_path.replace('/', '_')}.json"

        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Create the full filepath
        filepath = os.path.join(self.output_dir, filename)
        
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

    def generate_all_bundles(self):
        """
        Generate bundles for all imp trophy collections.
        Returns:
            Dictionary with bundle data and metadata
        """
        # Get all imp collections
        collections = self.get_all_imp_collections()
        
        print(f"Found {len(collections)} imp collections to process")
        
        generated_bundles = []
        
        for collection_path in collections:
            print(f"Generating bundle for {collection_path}")
            bundle_data = self.generate_bundle(collection_path)
            normalized_name = collection_path.replace('/', '_')
            bundle_info = {
                "name": normalized_name,
                "collection_path": collection_path,
                "size": len(str(bundle_data).encode('utf-8')),
                "document_count": bundle_data["metadata"]["totalDocuments"],
                "data": bundle_data
            }
            
            generated_bundles.append(bundle_info)
            print(f"Generated bundle with {bundle_data['metadata'][
                'totalDocuments']} documents")

        return {
            "total_bundles": len(generated_bundles),
            "bundles": generated_bundles
        } 
