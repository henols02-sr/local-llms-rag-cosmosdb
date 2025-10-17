"""
Confluence Space Content Downloader

This script downloads all content from a specified Atlassian Confluence space
using the Confluence REST API. It saves the content in a structured format
that can be used for RAG applications.
"""

import os
import json
import requests
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin
import logging
from datetime import datetime
import html2text
from pathlib import Path
import urllib3

# Disable SSL warnings when certificate verification is disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging with UTF-8 encoding to handle Unicode characters
# Set console to use UTF-8 encoding on Windows
import sys
if sys.platform == "win32":
    # Try to set console to UTF-8 mode
    try:
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True, check=False)
    except Exception:
        # If setting console encoding fails, continue anyway
        pass

try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('confluence_download.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
except Exception:
    # Fallback logging configuration if UTF-8 setup fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)


def safe_log_title(title: str) -> str:
    """Safely encode page title for logging to avoid Unicode errors"""
    try:
        # Replace problematic Unicode characters with safe ASCII equivalents
        # This approach is more aggressive but ensures compatibility
        safe_title = title.encode('ascii', 'replace').decode('ascii')
        return safe_title
    except Exception:
        # Ultimate fallback: keep only basic ASCII characters
        return ''.join(c if ord(c) < 128 and c.isprintable() else '?' for c in str(title))


class ConfluenceDownloader:
    """Downloads content from Confluence space using REST API"""
    
    def __init__(self, base_url: str, space_key: str, api_token: str = None):
        """
        Initialize Confluence downloader
        
        Args:
            base_url: Base URL of Confluence instance (e.g., 'https://confluence.sr.se')
            space_key: Space key to download (e.g., 'ABC')
            api_token: API token for Bearer authentication (optional, will prompt if needed)
        """
        self.base_url = base_url.rstrip('/')
        self.space_key = space_key
        self.api_base = f"{self.base_url}/rest/api/"
        self.session = requests.Session()
        
        # Disable SSL certificate verification to avoid SSL: CERTIFICATE_VERIFY_FAILED errors
        # WARNING: This reduces security - only use in trusted environments
        self.session.verify = False
        
        # Setup authentication
        self._setup_authentication(api_token)
        
        # Create output directory
        #self.output_dir = Path(f"confluence_export_{space_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.output_dir = Path(f"confluence_export/{space_key}")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # HTML to text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        
    def _setup_authentication(self, api_token: str = None):
        """Setup Bearer token authentication for Confluence API"""
        if not api_token:
            api_token = os.getenv('CONFLUENCE_API_TOKEN')
            if not api_token:
                api_token = input("Enter Confluence API token: ")
        
        # Set up Bearer token authentication
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        })
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Confluence API"""
        url = urljoin(self.api_base, endpoint)
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
            
    def get_space_info(self) -> Dict:
        """Get information about the space"""
        logger.info(f"Getting space information for '{self.space_key}'")
        endpoint = f"space/{self.space_key}"
        params = {
            'expand': 'description,homepage'
        }
        return self._make_request(endpoint, params)
    
    def get_all_pages(self) -> List[Dict]:
        """Get all pages from the space"""
        logger.info(f"Fetching all pages from space '{self.space_key}'")
        
        all_pages = []
        start = 0
        limit = 50
        request_delay = int(os.getenv("REQUEST_DELAY", "0"))
        
        while True:
            endpoint = "content"
            params = {
                'spaceKey': self.space_key,
                'type': 'page',
                'status': 'current',
                'expand': 'body.storage,ancestors,children,version,space',
                'start': start,
                'limit': limit
            }
            
            response = self._make_request(endpoint, params)
            pages = response.get('results', [])
            
            if not pages:
                break
                
            all_pages.extend(pages)
            logger.info(f"Retrieved {len(pages)} pages (total: {len(all_pages)})")
            
            # Check if there are more pages
            if len(pages) < limit:
                break
                
            start += limit
            if request_delay > 0:
                time.sleep(request_delay)  # Rate limiting

        logger.info(f"Total pages retrieved: {len(all_pages)}")
        return all_pages
    
    def download_page_content(self, page: Dict) -> Dict:
        """Download and process individual page content"""
        page_id = page['id']
        title = page['title']
        safe_title = safe_log_title(title)
        
        logger.info(f"Processing page: {safe_title} (ID: {page_id})")
        
        # Get full page content
        endpoint = f"content/{page_id}"
        params = {
            'expand': 'body.storage,body.view,ancestors,children,version,space,metadata.labels'
        }
        
        full_page = self._make_request(endpoint, params)
        
        # Extract content
        storage_body = full_page.get('body', {}).get('storage', {}).get('value', '')
        
        # Convert HTML to plain text
        plain_text = self.html_converter.handle(storage_body) if storage_body else ''
        
        # Build page hierarchy path
        ancestors = full_page.get('ancestors', [])
        hierarchy_path = ' > '.join([ancestor['title'] for ancestor in ancestors] + [title])
        
        page_data = {
            'id': page_id,
            'title': title,
            'space_key': self.space_key,
            'url': f"{self.base_url}/pages/viewpage.action?pageId={page_id}",
            'hierarchy_path': hierarchy_path,
            'created_date': full_page.get('version', {}).get('when'),
            'modified_date': full_page.get('version', {}).get('when'),
            'version': full_page.get('version', {}).get('number'),
            'author': full_page.get('version', {}).get('by', {}).get('displayName'),
            'labels': [label['name'] for label in full_page.get('metadata', {}).get('labels', {}).get('results', [])],
            'ancestors': [{'id': a['id'], 'title': a['title']} for a in ancestors],
            'storage_format': storage_body,
            'plain_text': plain_text,
            'content_length': len(plain_text),
            'downloaded_at': datetime.now().isoformat()
        }
        
        return page_data
    
    def save_page_data(self, page_data: Dict):
        """Save page data to files"""
        page_id = page_data['id']
        title = page_data['title']
        
        # Create safe filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:100]  # Limit length
        
        # Save as JSON
        json_file = self.output_dir / f"{page_id}_{safe_title}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)
        
        # Save plain text content
        txt_file = self.output_dir / f"{page_id}_{safe_title}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write(f"Space: {page_data['space_key']}\n")
            f.write(f"URL: {page_data['url']}\n")
            f.write(f"Hierarchy: {page_data['hierarchy_path']}\n")
            f.write(f"Author: {page_data['author']}\n")
            f.write(f"Modified: {page_data['modified_date']}\n")
            f.write(f"Labels: {', '.join(page_data['labels'])}\n")
            f.write("="*80 + "\n\n")
            f.write(page_data['plain_text'])
    
    def download_space(self):
        """Download all content from the space"""
        logger.info(f"Starting download of Confluence space '{self.space_key}'")
        logger.warning("SSL certificate verification is disabled for this connection. Use only in trusted environments.")
        
        try:
            # Get space information
            space_info = self.get_space_info()
            logger.info(f"Space name: {space_info.get('name', 'Unknown')}")
            
            # Save space metadata
            space_metadata = {
                'space_info': space_info,
                'download_started': datetime.now().isoformat(),
                'base_url': self.base_url,
                'space_key': self.space_key
            }
            
            with open(self.output_dir / 'space_metadata.json', 'w', encoding='utf-8') as f:
                json.dump(space_metadata, f, indent=2, ensure_ascii=False)
            
            # Get all pages
            pages = self.get_all_pages()
            
            if not pages:
                logger.warning("No pages found in the space")
                return
            
            # Download each page
            downloaded_pages = []
            failed_pages = []
            request_delay = int(os.getenv("REQUEST_DELAY", "0"))
            
            for i, page in enumerate(pages, 1):
                try:
                    safe_title = safe_log_title(page['title'])
                    logger.info(f"Processing page {i}/{len(pages)}: {safe_title}")
                    page_data = self.download_page_content(page)
                    self.save_page_data(page_data)
                    downloaded_pages.append(page_data)
                    
                except Exception as e:
                    safe_title = safe_log_title(page['title'])
                    logger.error(f"Failed to process page '{safe_title}': {e}")
                    failed_pages.append({'page': page, 'error': str(e)})
                
                # Rate limiting
                if request_delay > 0:
                    time.sleep(request_delay)
            
            # Save summary
            summary = {
                'total_pages': len(pages),
                'downloaded_pages': len(downloaded_pages),
                'failed_pages': len(failed_pages),
                'download_completed': datetime.now().isoformat(),
                'output_directory': str(self.output_dir),
                'failed_page_details': failed_pages
            }
            
            with open(self.output_dir / 'download_summary.json', 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Download completed!")
            logger.info(f"Downloaded: {len(downloaded_pages)} pages")
            logger.info(f"Failed: {len(failed_pages)} pages")
            logger.info(f"Output directory: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise


def main():
    """Main function to run the Confluence downloader"""
    # Configuration
    BASE_URL = "https://confluence.sr.se"
    SPACE_KEY = "ABC"
    
    print("Confluence Space Content Downloader")
    print("===================================")
    print(f"Base URL: {BASE_URL}")
    print(f"Space Key: {SPACE_KEY}")
    print()
    
    try:
        # Create downloader instance
        downloader = ConfluenceDownloader(BASE_URL, SPACE_KEY)
        
        # Start download
        downloader.download_space()
        
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()