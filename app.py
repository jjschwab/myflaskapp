from flask import Flask, request, jsonify, render_template
import video_processing_refactored as vp
import json
import os

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('video_url')
    selected_scene_indices = data.get('selected_scenes', [])
    
    if not video_url:
        return jsonify({'error': 'No video URL provided'}), 400

    # Download and process the video
    video_path = vp.download_video(video_url)
    scenes = vp.find_scenes(video_path)
    scene_frames = vp.extract_frames(video_path, scenes)
    scene_categories = vp.classify_and_categorize_scenes(scene_frames, ["Some", "Description", "Phrases"])

    # Filter for action scenes and sort by duration
    action_scenes = [scene for scene_id, scene in scene_categories.items() if scene['category'] == 'Action Scene']
    top_scenes = sorted(action_scenes, key=lambda x: x['duration'], reverse=True)[:20]
    top_longest_scenes = sorted(top_scenes, key=lambda x: x['duration'], reverse=True)[:10]

    # Select scenes based on user input
    selected_scenes = [top_longest_scenes[i] for i in selected_scene_indices if 0 <= i < len(top_longest_scenes)]
    clip_paths = [vp.save_clip(video_path, scene, vp.BASE_DIRECTORY, index)['path'] for index, scene in enumerate(selected_scenes)]

    # Concatenate selected scenes
    output_path = os.path.join(vp.BASE_DIRECTORY, "final_concatenated_clip.mp4")
    vp.process_video(clip_paths, output_path)

    return jsonify({"message": "Video processed successfully", "output_path": output_path})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
