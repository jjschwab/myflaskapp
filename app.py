from flask import Flask, request, jsonify, session, render_template
import video_processing_refactored as vp
import numpy as np
import json
import base64
import cv2
import logging


app = Flask(__name__, template_folder='/home/buckschwab/myflaskapp/templates')

@app.route('/test')
def test_json():
    app.logger.info("Entered the /test route")
    data = [1, 2, 3]
    return jsonify(data.tolist())

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)  # Set host to '0.0.0.0' to listen on all network interfaces

app.secret_key = 'bt\xcd\xc5\xf1\xbf19\xed\x86\xe5\xc2Y\x01\xb3\x8eh\xff\x9a\x9b\x1c\xd3\xec\xe8l'
  # Necessary for session management


def ndarray_to_base64(ndarray):
    """Converts an ndarray to a base64 encoded string."""
    _, buffer = cv2.imencode('.jpg', ndarray)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    return jpg_as_text

@app.route('/submit_video', methods=['POST'])
def submit_video():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data received'}), 400

    video_url = data.get('video_url')
    category_choice = data.get('category_choice')
    user_descriptions = data.get('user_descriptions', [])

    if not video_url or not category_choice:
        return jsonify({'error': "Missing data: 'video_url' or 'category_choice' not provided"}), 400

    try:
        video_path = vp.download_video(video_url)
        if not video_path:
            return jsonify({'error': 'Failed to download video.'}), 400

        scenes = vp.find_scenes(video_path)
        scene_frames = vp.extract_frames(video_path, scenes)
        scene_categories = vp.classify_and_categorize_scenes(scene_frames, user_descriptions + ["Additional phrases"])

        # Ensure all data is serializable
        for scene_id, category in scene_categories.items():
            for key, value in category.items():
                if isinstance(value, np.ndarray):
                    _, buffer = cv2.imencode('.jpg', value)
                    category[key] = base64.b64encode(buffer).decode('utf-8')

        return jsonify(scene_categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500