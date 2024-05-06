from flask import Flask, request, jsonify, render_template
import video_processing_refactored as vp
import os
import json

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data['video_url']
    description_phrases = [
        "Skier jumping off a snow ramp", "Person skiing down a snowy mountain", "Close-up of skis on snow", "Skiing through a snowy forest", "Skier performing a spin",
            "Point-of-view shot from a ski helmet", "Group of skiers on a mountain", "Skier sliding on a rail", "Snow spraying from skis", "Skier in mid-air during a jump",
            "Person being interviewed after an event", "People in a crowd cheering", "Sitting inside of a vehicle", "Skaters standing around a ramp", "People standing around at an event",
            "Commercial break", "People having a conversation", "Person in a helmet talking to the camera", "person facing the camera", "People introducing the context for a video"
    ]

    video_path = vp.download_video(video_url)
    if not video_path:
        return jsonify({'error': 'Failed to download video.'}), 400

    scenes = vp.find_scenes(video_path)
    scene_frames = vp.extract_frames(video_path, scenes)
    scene_categories = vp.classify_and_categorize_scenes(scene_frames, description_phrases)

    # Filter for action scenes and sort them by confidence, then by duration
    action_scenes = [scene for scene_id, scene in scene_categories.items() if scene['category'] == 'Action Scene']
    top_scenes = sorted(action_scenes, key=lambda x: (-x['confidence'], -x['duration']))[:20]
    top_10_scenes = sorted(top_scenes, key=lambda x: -x['duration'])[:10]

    # Convert first_frame to base64 to send to front-end
    for scene in top_10_scenes:
        if 'first_frame' in scene:
            scene['first_frame'] = vp.image_to_base64(scene['first_frame'])

    return jsonify(top_10_scenes)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')