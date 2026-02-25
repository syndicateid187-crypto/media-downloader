from http.server import BaseHTTPRequestHandler
import json
import yt_dlp
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
        except:
            data = {}
            
        url = data.get('url')

        if not url:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "URL is required"}).encode())
            return

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                formats = []
                raw_formats = info.get('formats', [])
                
                for f in raw_formats:
                    # Aggressively filter out streaming manifests
                    protocol = (f.get('protocol') or '').lower()
                    url_val = (f.get('url') or '').lower()
                    
                    if 'm3u8' in protocol or 'm3u8' in url_val or 'dash' in protocol or 'dash' in url_val:
                        # Special case for Pinterest: attempt to find direct MP4 from HLS URL
                        if 'pinimg.com' in url_val and '.m3u8' in url_val:
                            # Try to convert: /hls/.../_v2_720w.m3u8 -> /720p/...mp4
                            # This is a common pattern for Pinterest
                            potential_mp4 = url_val.replace('/hls/', '/720p/').replace('_v2_720w.m3u8', '.mp4').replace('_v2.m3u8', '.mp4')
                            if potential_mp4 not in [fmt['url'] for fmt in formats]:
                                formats.append({
                                    "formatId": f.get('format_id') + "-mp4-fixed",
                                    "ext": "mp4",
                                    "resolution": f.get('resolution') or f"{f.get('width', 0)}x{f.get('height', 0)}",
                                    "filesize": None,
                                    "url": potential_mp4,
                                    "note": "Direct MP4 (Fixed)",
                                    "width": f.get('width', 0),
                                    "height": f.get('height', 0)
                                })
                        continue
                        
                    if f.get('url') and (f.get('vcodec') != 'none' or f.get('acodec') != 'none'):
                        formats.append({
                            "formatId": f.get('format_id'),
                            "ext": f.get('ext'),
                            "resolution": f.get('resolution') or f"{f.get('width', 0)}x{f.get('height', 0)}",
                            "filesize": f.get('filesize') or f.get('filesize_approx'),
                            "url": f.get('url'),
                            "note": f.get('format_note', ''),
                            "width": f.get('width', 0),
                            "height": f.get('height', 0)
                        })
                
                # Sort by resolution (height) descending
                formats.sort(key=lambda x: x.get('height', 0) if x.get('height') else 0, reverse=True)

                response_data = {
                    "type": info.get('extractor', 'generic'),
                    "title": info.get('title'),
                    "thumbnail": info.get('thumbnail'),
                    "formats": formats,
                    "originalUrl": info.get('original_url') or url
                }

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
