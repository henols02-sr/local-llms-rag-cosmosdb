"""
Example script showing how to use the Confluence downloader
and integrate it with the existing RAG pipeline.
"""

import os
from pathlib import Path
from confluence_downloader import ConfluenceDownloader
from load_data import load_documents_from_directory  # Assuming this exists

def download_and_load_confluence_data():
    """Download Confluence data and integrate with RAG pipeline"""
    
    # Step 1: Download Confluence content
    print("Step 1: Downloading Confluence content...")
    downloader = ConfluenceDownloader(
        base_url="https://confluence.sr.se",
        space_key="ABC"
    )
    
    downloader.download_space()
    output_dir = downloader.output_dir
    print(f"Content downloaded to: {output_dir}")
    
    # Step 2: Process downloaded content for RAG
    print("Step 2: Processing content for RAG pipeline...")
    
    # Get all text files
    text_files = list(output_dir.glob("*.txt"))
    print(f"Found {len(text_files)} text files to process")
    
    # You can now use these files with your existing RAG pipeline
    # For example, if you have a function to load documents:
    # documents = load_documents_from_directory(str(output_dir))
    
    return output_dir, text_files

def integrate_with_existing_rag():
    """Example of how to integrate with existing RAG components"""
    
    # Download content
    output_dir, text_files = download_and_load_confluence_data()
    
    # Example: Load into vector store
    print("Step 3: Loading into vector store...")
    
    # This would use your existing vector store setup
    # from cosmosdb_vector_store import CosmosDBVectorStore
    # vector_store = CosmosDBVectorStore()
    
    for text_file in text_files:
        with open(text_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Process the content as needed
        # You might want to chunk it, create embeddings, etc.
        print(f"Processing: {text_file.name}")
        
        # Example: Add to vector store
        # vector_store.add_document(content, metadata={'source': text_file.name})
    
    print("Integration complete!")

if __name__ == "__main__":
    # Set environment variables if needed
    # os.environ['CONFLUENCE_API_TOKEN'] = 'your_api_token'
    
    integrate_with_existing_rag()