# Confluence Content Downloader

This script downloads all content from a specified Atlassian Confluence space using the Confluence REST API. It's designed to work with the existing RAG application setup in this repository.

## Features

- Downloads all pages from a Confluence space
- Converts HTML content to plain text for better processing
- Preserves page hierarchy and metadata
- Saves content in multiple formats (JSON and text)
- Includes comprehensive logging
- Rate limiting to respect API limits
- Error handling and retry logic
- SSL certificate verification bypass for corporate environments

## Prerequisites

1. **Confluence API Access**: You need access to the Confluence instance at `https://confluence.sr.se`
2. **API Token**: Generate an API token from your Confluence account settings
3. **Python Dependencies**: Install the required packages

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Set up authentication (optional):

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
CONFLUENCE_API_TOKEN=your_bearer_token
```

## Usage

### Basic Usage

Run the script directly to download content from the "ABC" space:

```bash
python confluence_downloader.py
```

The script will:

1. Prompt for credentials if not set in environment variables
2. Connect to the Confluence instance
3. Download all pages from the "ABC" space
4. Save content to a timestamped directory

### Programmatic Usage

```python
from confluence_downloader import ConfluenceDownloader

# Create downloader instance
downloader = ConfluenceDownloader(
    base_url="https://confluence.sr.se",
    space_key="ABC",
    api_token="your_bearer_token"    # Optional
)

# Download all content
downloader.download_space()
```

### Integration with RAG Pipeline

See `confluence_integration_example.py` for examples of how to integrate the downloaded content with your existing RAG application.

## Output Structure

The downloader creates a timestamped directory with the following structure:

```
confluence_export_ABC_20241017_143022/
├── space_metadata.json          # Space information and metadata
├── download_summary.json        # Summary of download results
├── confluence_download.log      # Detailed log file
├── 12345_Page_Title.json        # Page data in JSON format
├── 12345_Page_Title.txt         # Page content in plain text
├── 67890_Another_Page.json
├── 67890_Another_Page.txt
└── ...
```

### File Formats

#### JSON Files

Each page is saved as a JSON file containing:

- Page metadata (ID, title, hierarchy, author, etc.)
- Original HTML content (storage format)
- Converted plain text
- Labels and categories
- Version information

#### Text Files

Plain text versions for easy processing, including:

- Page header with metadata
- Clean text content suitable for RAG processing

## Configuration

### Environment Variables

- `CONFLUENCE_API_TOKEN`: Your Bearer API token
- `CONFLUENCE_BASE_URL`: Base URL (default: <https://confluence.sr.se>)
- `CONFLUENCE_SPACE_KEY`: Space key (default: ABC)

### Authentication

You have several options for authentication:

1. **Environment Variables**: Set `CONFLUENCE_API_TOKEN`
2. **Interactive Prompts**: The script will prompt if the token is not found
3. **Direct Parameters**: Pass the token directly to the ConfluenceDownloader constructor

### API Token Generation

To generate an API token:

1. Go to your Confluence profile settings
2. Navigate to "Security" → "API tokens"
3. Click "Create and manage API tokens"
4. Create a new token with appropriate permissions
5. Use this token for Bearer authentication

## Security Notice

**SSL Certificate Verification**: This script disables SSL certificate verification to avoid SSL: CERTIFICATE_VERIFY_FAILED errors commonly encountered in corporate environments with self-signed certificates or corporate proxies.

⚠️ **Warning**: Disabling SSL certificate verification reduces security by making the connection vulnerable to man-in-the-middle attacks. Only use this script in trusted network environments.

## Error Handling

The script includes comprehensive error handling:

- **Network Issues**: Automatic retry with exponential backoff
- **Authentication Errors**: Clear error messages and guidance
- **Rate Limiting**: Respects API rate limits with configurable delays
- **Partial Failures**: Continues processing even if individual pages fail
- **Logging**: Detailed logs for troubleshooting

## Rate Limiting

The downloader implements rate limiting to be respectful of the Confluence API:

- Default delay of 0 seconds between requests (no delay)
- Configurable via the `REQUEST_DELAY` environment variable (integer seconds)
- Set `REQUEST_DELAY=1` to add 1 second delay, or any other integer value
- Monitors API response headers for rate limit information

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your API token is correct and not expired
   - Check if your account has access to the space
   - Ensure the API token has appropriate permissions

2. **Space Not Found**
   - Verify the space key is correct
   - Check if you have read access to the space

3. **SSL Certificate Errors**
   - SSL certificate verification is automatically disabled
   - If you still encounter SSL issues, check your network configuration
   - Contact your IT department about corporate proxy or firewall settings

4. **Network Errors**
   - Check your internet connection
   - Verify the Confluence URL is accessible
   - Check if there are any firewall restrictions

### Logging

Check the `confluence_download.log` file for detailed information about:

- API requests and responses
- Processing progress
- Error details
- Performance metrics

## Integration with Existing RAG Application

This downloader is designed to work seamlessly with the existing RAG application in this repository. The downloaded content can be:

1. **Loaded into Azure Cosmos DB**: Use the existing vector store setup
2. **Processed with LangChain**: Leverage the existing document processing pipeline
3. **Embedded with Ollama**: Use the local LLM setup for embeddings
4. **Queried via RAG**: Integrate with the existing query system

See the main README.md for more information about the RAG application setup.

## License

This script is part of the local-llms-rag-cosmosdb project and follows the same licensing terms.