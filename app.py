from flask import Flask, request, jsonify, render_template, url_for
import video_processing_refactored as vp
import os

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('video_url')
    
    if not video_url:
        return jsonify({'error': 'Video URL is missing'}), 400
    
    video_path = vp.download_video(video_url)
    if not video_path:
        return jsonify({'error': 'Failed to download video'}), 500

    scenes = vp.find_scenes(video_path)
    if not scenes:
        return jsonify({'error': 'No scenes detected'}), 500

    scene_frames = vp.extract_frames(video_path, scenes)
    if not scene_frames:
        return jsonify({'error': 'Failed to extract frames'}), 500

    # Integrate scene categorization
    description_phrases = ["Skier jumping off a snow ramp", "Person skiing down a snowy mountain", "Close-up of skis on snow", "Skiing through a snowy forest", "Skier performing a spin",
            "Point-of-view shot from a ski helmet", "Group of skiers on a mountain", "Skier sliding on a rail", "Snow spraying from skis", "Skier in mid-air during a jump",
            "Person being interviewed after an event", "People in a crowd cheering", "Sitting inside of a vehicle", "Skaters standing around a ramp", "People standing around at an event",
            "Commercial break", "People having a conversation", "Person in a helmet talking to the camera", "person facing the camera", "People introducing the context for a video"]  # Simplified example, adjust as necessary
    scene_categories = vp.classify_and_categorize_scenes(scene_frames, description_phrases)
    if not scene_categories:
        return jsonify({'error': 'Failed to categorize scenes'}), 500

    # Assuming we use the first categorized scene for simplification
    first_scene_info = next(iter(scene_categories.values()))
    saved_clip = vp.save_clip(video_path, first_scene_info, os.path.join(app.static_folder, 'videos'), 1)
    
    if not saved_clip:
        return jsonify({'error': 'No valid clips were selected or could be saved.'}), 500
    
    video_filename = os.path.basename(saved_clip['path'])
    return jsonify({'message': 'Clip processed successfully', 'video_filename': video_filename})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

