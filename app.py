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

    description_phrases = {
        "1": ["Mountain biker doing a downhill run", "Rider jumping over an obstacle", "Cyclist on a rocky trail", "Biking through forest trails", "MTB stunt on a dirt path",
            "Close-up of a mountain bike wheel", "Mountain biker navigating a sharp turn", "First-person view of a bike ride", "Mountain biker doing a trick jump", "Biking fast down a steep incline",
            "Biker with a helmet on talking to the camera", "People standing around", "a person facing and talking to the camera", "Introducing the context for a video", "a zoomed-out scene of nature without any people in it",
            "Scene showing a mountain biking terrain park", "Biker taking it easy going down a hill", "mountain Biker falling and crashing", "People walking outside", "Context scene with mountain bikers not performing any tricks"],  # Example phrases for categories
        "2": ["Skier jumping off a snow ramp", "Person skiing down a snowy mountain", "Close-up of skis on snow", "Skiing through a snowy forest", "Skier performing a spin",
            "Point-of-view shot from a ski helmet", "Group of skiers on a mountain", "Skier sliding on a rail", "Snow spraying from skis", "Skier in mid-air during a jump",
            "Person being interviewed after an event", "People in a crowd cheering", "Sitting inside of a vehicle", "Skaters standing around a ramp", "People standing around at an event",
            "Commercial break", "People having a conversation", "Person in a helmet talking to the camera", "person facing the camera", "People introducing the context for a video",],
        "3": ["Surfer riding a big wave", "Close-up of a surfboard on water", "Surfer performing a cutback", "Wave curling over a surfer", "Aerial view of a surf competition",
            "Surfer paddling on a board", "Surfboard leaving a trail in the water", "Surfer in a tube wave", "Surfer wiping out on a wave", "Longboard surfer cruising a wave",
            "Surfers lounging on the beach", "Paddling to catch a wave", "a surfer surveying the waves sitting on their surfboard", "People standing holding their surfboards",
            "Standing on the beach", "Interviewing a surfer after their performance", "multiple faces in the frame", "Surfer paddling out to get ready for a wave",
            "Surfer in the water sitting on their surfboard", "Beginner surfer struggling to stand on their board"]
    }

    categorized_scenes = vp.classify_and_categorize_scenes(scene_frames, description_phrases[category_choice])
    action_scenes = [scene for scene in categorized_scenes.values() if scene['category'] == 'Action Scene']
    top_action_scenes = sorted(action_scenes, key=lambda x: x['confidence'], reverse=True)[:20]
    best_clips = sorted(top_action_scenes, key=lambda x: x['duration'], reverse=True)[:10]

    scene_details = [{
        'scene_number': list(categorized_scenes.keys())[list(categorized_scenes.values()).index(scene)] + 1,
        'duration': scene['duration'],
        'start_time': scene['start_time'],
        'end_time': scene['end_time'],
        'description': scene['best_description'],
        'first_frame': base64.b64encode(cv2.imencode('.jpg', scene['first_frame'])[1]).decode()
    } for scene in best_clips]

    return jsonify({'clips': scene_details})

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




