from flask import Flask, request, jsonify, render_template
import video_processing_refactored as vp
import json
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('video_url')
    
    if not video_url:
        return jsonify({'error': 'Video URL is missing'}), 400
    
    # Download video
    video_path = vp.download_video(video_url)
    if not video_path:
        return jsonify({'error': 'Failed to download video'}), 500

    # Find and categorize scenes
    scenes = vp.find_scenes(video_path)
    scene_frames = vp.extract_frames(video_path, scenes)
    categorized_scenes = vp.classify_and_categorize_scenes(scene_frames, data.get('descriptions', []))

    # Store the best scenes information in session or another temporary storage
    best_scenes = sorted(
        (scene for scene in categorized_scenes.values() if scene['category'] == 'Action Scene'),
        key=lambda x: x['confidence'], reverse=True)[:20]  # Top 20 action scenes by confidence

    return jsonify({
        'message': 'Scenes processed successfully',
        'scenes': best_scenes
    })

@app.route('/finalize_video', methods=['POST'])
def finalize_video():
    selected_scene_indices = request.get_json().get('selected_indices', [])
    video_path = request.get_json().get('video_path', '')

    clip_paths = [vp.save_clip(video_path, scene, app.static_folder + '/videos', index)['path']
                  for index, scene in enumerate(selected_scene_indices)]
    final_video_path = vp.process_video(clip_paths, os.path.join(app.static_folder, 'videos', 'final_video.mp4'))

    return jsonify({
        'message': 'Video concatenated successfully',
        'video_filename': os.path.basename(final_video_path)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

