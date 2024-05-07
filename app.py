from flask import Flask, request, jsonify, render_template, send_from_directory
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
    category_choice = data.get('category_choice')
    
    if not video_url or not category_choice:
        return jsonify({'error': 'Video URL or category is missing'}), 400
    
    video_path = vp.download_video(video_url)
    if not video_path:
        return jsonify({'error': 'Failed to download video'}), 500

    scenes = vp.find_scenes(video_path)
    if not scenes:
        return jsonify({'error': 'No scenes detected'}), 500

    scene_frames = vp.extract_frames(video_path, scenes)
    if not scene_frames:
        return jsonify({'error': 'Failed to extract frames'}), 500

    # Mock descriptions based on category choice for demo
    description_phrases = {
        "1": [""Skier jumping off a snow ramp", "Person skiing down a snowy mountain", "Close-up of skis on snow", "Skiing through a snowy forest", "Skier performing a spin",
            "Point-of-view shot from a ski helmet", "Group of skiers on a mountain", "Skier sliding on a rail", "Snow spraying from skis", "Skier in mid-air during a jump",
            "Person being interviewed after an event", "People in a crowd cheering", "Sitting inside of a vehicle", "Skaters standing around a ramp", "People standing around at an event",
            "Commercial break", "People having a conversation", "Person in a helmet talking to the camera", "person facing the camera", "People introducing the context for a video""],  # Example phrases for categories
        "2": ["Dramatic scene description"],
        "3": ["Calm scene description"]
    }

    categorized_scenes = vp.classify_and_categorize_scenes(scene_frames, description_phrases[category_choice])
    top_scenes = sorted(categorized_scenes.values(), key=lambda x: x['duration'], reverse=True)[:10]  # Get top 10 longest scenes
    
    clip_paths = [vp.save_clip(video_path, scene, os.path.join(app.static_folder, 'videos'), index)['path'] for index, scene in enumerate(top_scenes)]
    final_video_info = vp.process_video(clip_paths, os.path.join(app.static_folder, 'videos', 'final_video.mp4'))

    if 'path' not in final_video_info:
        return jsonify({'error': 'Failed to process final video'}), 500

    return jsonify({'message': 'Video processed successfully', 'video_filename': os.path.basename(final_video_info['path'])})
@app.route('/downloads/<path:filename>', methods=['GET'])
def download(filename):
    return send_from_directory(app.static_folder, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
