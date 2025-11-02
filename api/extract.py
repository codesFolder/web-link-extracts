from http.server import BaseHTTPRequestHandler
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Read request body
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        try:
            url = data.get('url', '').strip()
            keyword = data.get('keyword', '').strip()
            
            if not url:
                raise ValueError("URL is required")
            
            # Fetch and parse the webpage
            all_links = self.get_all_links(url)
            
            if not all_links:
                response_data = {
                    'success': True,
                    'all_links': [],
                    'filtered_links': [],
                    'message': 'No links found on this page'
                }
            else:
                # Filter by keyword if provided
                if keyword:
                    filtered_links = [
                        link for link in all_links 
                        if keyword.lower() in link['text'].lower()
                    ]
                else:
                    filtered_links = all_links
                
                response_data = {
                    'success': True,
                    'all_links': all_links,
                    'filtered_links': filtered_links,
                    'total_count': len(all_links),
                    'filtered_count': len(filtered_links)
                }
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except requests.RequestException as e:
            # Network/request errors
            error_response = {
                'success': False,
                'error': f'Failed to fetch URL: {str(e)}'
            }
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
            
        except Exception as e:
            # Other errors
            error_response = {
                'success': False,
                'error': str(e)
            }
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
    
    def get_all_links(self, url):
        """Fetches all hyperlink URLs and their text from a webpage."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href and not href.startswith(('javascript:', 'mailto:', '#')):
                absolute_url = urljoin(url, href)
                link_text = a_tag.get_text(strip=True)
                links.append({
                    'text': link_text if link_text else '(No text)',
                    'url': absolute_url
                })
        
        return links
    
    def do_GET(self):
        # Simple test endpoint
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {'message': 'Link Extractor API is working! Use POST to /api/extract'}
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()