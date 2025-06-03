#!/usr/bin/env python3

import os
from google.cloud import firestore

def test_firestore():
    project_id = os.environ.get("GCP_PROJECT_ID", "stylize-mcp-server")
    print(f"Testing Firestore with project ID: {project_id}")
    
    try:
        client = firestore.Client(project=project_id)
        print("Firestore client created successfully")
        
        # Test basic connectivity
        test_collection = client.collection('_test')
        docs = test_collection.limit(1).get()
        print(f"Firestore connectivity test successful. Got {len(docs)} documents")
        
        return True
    except Exception as e:
        print(f"Firestore test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_firestore()