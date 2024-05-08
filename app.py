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
    description_phrases = ["Action scene", "Quiet moment", "Intense moment"]  # Example set of phrases
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

    return jsonify(results)


@app.route('/concatenate_clips', methods=['POST'])
def concatenate_clips():
    data = request.get_json()
    selected_indices = data.get('selected_indices')
    video_path = data.get('video_path')

    clips_info = [scene for i, scene in enumerate(best_clips) if i in selected_indices]
    clip_paths = [vp.save_clip(video_path, scene, os.path.join(app.static_folder, 'videos'), i)['path'] for i, scene in enumerate(clips_info)]

    final_video_info = vp.process_video(clip_paths, os.path.join(app.static_folder, 'videos', 'final_video.mp4'))
    if 'path' not in final_video_info:
        return jsonify({'error': 'Failed to process final video'}), 500

    return jsonify({'message': 'Video processed successfully', 'video_filename': os.path.basename(final_video_info['path'])})

@app.route('/downloads/<path:filename>', methods=['GET'])
def download(filename):
    return send_from_directory(app.static_folder, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)




