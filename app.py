from flask import Flask, request, jsonify, render_template
import video_processing_refactored as vp
import base64
import cv2

app = Flask(__name__)

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

    results = []
    for scene_id, scene_data in scene_frames.items():
        encoded_image = base64.b64encode(cv2.imencode('.jpg', scene_data['first_frame'])[1]).decode()
        results.append({
            'scene_id': scene_id,
            'start_time': str(scene_data['start_time']),
            'end_time': str(scene_data['end_time']),
            'image': encoded_image
        })

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')