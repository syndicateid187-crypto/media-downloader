from http.server import BaseHTTPRequestHandler
import urllib.parse

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

        # For Vercel, we will redirect to the actual media URL to avoid timeout/size limits in serverless
        # Most modern browsers handle the download/redirect well.
        self.send_response(302)
        self.send_header('Location', url)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
