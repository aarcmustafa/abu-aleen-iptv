import os
import re
import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)

# القوائم المحدثة: الرياضية والجزائرية فقط
PLAYLISTS = {
    'sports': 'https://iptv-org.github.io/iptv/categories/sports.m3u',
    'algeria': 'https://iptv-org.github.io/iptv/countries/dz.m3u',
}

# دالة لقراءة وتحليل ملفات M3U واستخراج القنوات
def parse_m3u(content):
    channels = []
    lines = content.splitlines()
    current_channel = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            current_channel = {}
            
            # استخراج اسم القناة
            parts = line.split(',', 1)
            if len(parts) > 1:
                current_channel['name'] = parts[1].strip()
            else:
                current_channel['name'] = 'Unknown'
            
            # استخراج شعار القناة
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            if logo_match:
                current_channel['logo'] = logo_match.group(1)
            else:
                current_channel['logo'] = ''
                
            # استخراج المجموعة (التصنيف)
            group_match = re.search(r'group-title="([^"]+)"', line)
            if group_match:
                current_channel['group'] = group_match.group(1)
            else:
                current_channel['group'] = 'عام'

        elif line.startswith('http') and current_channel:
            current_channel['url'] = line
            channels.append(current_channel)
            current_channel = {}
            
    return channels

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# مسار لجلب أسماء القوائم المتاحة (الرياضة والجزائر)
@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    return jsonify(list(PLAYLISTS.keys()))

# مسار لجلب القنوات الخاصة بقائمة معينة
@app.route('/api/channels/<playlist_name>', methods=['GET'])
def get_channels(playlist_name):
    url = PLAYLISTS.get(playlist_name)
    if not url:
        return jsonify({"error": "Playlist not found"}), 404

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        channels = parse_m3u(response.text)
        return jsonify(channels)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
