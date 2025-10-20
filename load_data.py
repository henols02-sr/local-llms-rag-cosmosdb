import json
from pathlib import Path
from langchain_text_splitters import HTMLSemanticPreservingSplitter, MarkdownTextSplitter
from langchain_community.document_loaders import WebBaseLoader
import cosmosdb_vector_store
import logging
import os
from typing import List

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def load(create_container: bool = True) -> None:
    """Load documents from files into Azure Cosmos DB vector store."""

    print("Uploading documents to Azure Cosmos DB")

    try:
        # # Load documents from web
        # loader = WebBaseLoader(
        #     web_paths=urls,
        #     header_template=headers
        # )
        # documents = loader.load()

        # Split documents into chunks
        # markdown_splitter = MarkdownTextSplitter(chunk_size=1500, chunk_overlap=200)
        # split_docs = markdown_splitter.split_documents(documents)

        # Load storage_format property from JSON files and split into chunks
        split_docs = []
        splitter = HTMLSemanticPreservingSplitter(headers_to_split_on=["h1", "h2", "h3", "h4"], max_chunk_size=1500, chunk_overlap=200)
        files = list(Path("confluence_export").rglob("*.json"))

        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                print(f"Processing file: {file}")
                data = json.load(f)
                storage_format = data.get("storage_format")
                if storage_format:
                    split_docs.extend(splitter.split_text(storage_format))
                else:
                    print("No storage_format found")

        # Get vector store instance and add documents
        print(
            f"Loading {len(split_docs)} document chunks from {len(files)} documents"
        )
        store = cosmosdb_vector_store.get_instance(create_container)
        store.add_documents(split_docs)

        print("Data loaded into Azure Cosmos DB")

    except Exception as e:
        logger.error(f"Error during data loading: {str(e)}")
        raise


if __name__ == "__main__":
    load()
