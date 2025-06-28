# proxy_server.py
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route("/video")
def fetch_video():
    query = request.args.get("q")
    source = request.args.get("source", "redtube")

    if not query:
        return jsonify({"error": "Missing 'q' param"}), 400

    if source == "redtube":
        api_url = f"https://api.redtube.com/?data=redtube.Videos.searchVideos&search={query}&output=json"
        r = requests.get(api_url)
        if r.status_code != 200:
            return jsonify({"error": "Source failed"}), 502
        try:
            videos = r.json().get("video", [])
            if not videos:
                return jsonify({"error": "No videos found"}), 404
            video = videos[0]
            return jsonify({
                "title": video.get("title"),
                "url": video.get("url"),
                "thumbnail": video.get("thumb")
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Unsupported source"}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
