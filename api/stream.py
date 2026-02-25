import requests
from http.server import BaseHTTPRequestHandler
import urllib.parse
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        url = params.get('url', [None])[0]
        filename = params.get('filename', ['download.mp4'])[0]

        if not url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"URL is required")
            return

        try:
            # We stream the request to the target URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.pinterest.com/'
            }
            # Increased timeout for large files on Vercel
            resp = requests.get(url, stream=True, timeout=20, headers=headers)
            
            if resp.status_code != 200:
                self.send_response(resp.status_code)
                self.end_headers()
                return

            self.send_response(200)
            # Filter and pass along relevant headers
            content_type = resp.headers.get('Content-Type', 'application/octet-stream')
            self.send_header('Content-Type', content_type)
            # This is the key header to force a download
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Access-Control-Allow-Origin', '*')
            
            # Pass along Content-Length if available
            if 'Content-Length' in resp.headers:
                self.send_header('Content-Length', resp.headers['Content-Length'])
                
            self.end_headers()

            # Stream chunks of data back to the client
            for chunk in resp.iter_content(chunk_size=1024*64):
                if chunk:
                    self.wfile.write(chunk)
                    
        except Exception as e:
            # Fallback to redirect if proxying fails or takes too long
            # (Though Vercel might have already cut the connection)
            self.send_response(302)
            self.send_header('Location', url)
            self.end_headers()

