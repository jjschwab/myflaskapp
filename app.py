from flask import Flask, request, jsonify, render_template, send_from_directory
import video_processing_refactored as vp
import json
import os
import cv2
import base64

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('video_url')
    
    if not video_url:
        return jsonify({'error': 'No video URL provided'}), 400
    
    video_path = vp.download_video(video_url)
    if not video_path:
        return jsonify({'error': 'Failed to download video'}), 500

    scenes = vp.find_scenes(video_path)
    scene_frames = vp.extract_frames(video_path, scenes)
    description_phrases = ["Skier jumping off a snow ramp", "Person skiing down a snowy mountain", ...]  # Your set of phrases
    scene_categories = vp.classify_and_categorize_scenes(scene_frames, description_phrases)

    results = []
    for scene_id, scene_info in scene_categories.items():
        encoded_image = base64.b64encode(cv2.imencode('.jpg', scene_info['first_frame'])[1]).decode()
        results.append({
            'scene_id': scene_id,
            'category': scene_info['category'],
            'confidence': scene_info['confidence'],
            'start_time': scene_info['start_time'],
            'end_time': scene_info['end_time'],
            'duration': scene_info['duration'],
            'best_description': scene_info['best_description'],
            'image': encoded_image
        })

    # Selecting top action scenes
    action_scenes = [scene for scene in results if scene['category'] == 'Action Scene']
    top_action_scenes = sorted(action_scenes, key=lambda x: x['confidence'], reverse=True)[:10]

    return jsonify({'all_scenes': results, 'top_action_scenes': top_action_scenes})

@app.route('/downloads/<path:filename>', methods=['GET'])
def download(filename):
    return send_from_directory(app.static_folder, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)




