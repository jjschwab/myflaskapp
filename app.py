from flask import Flask, request, jsonify, render_template, send_from_directory, session
import video_processing_refactored as vp
import json
import os
import cv2
import base64

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('video_url')
    category_choice = data.get('category_choice')
    custom_phrases = [data.get(f'customPhrase{i+1}', None) for i in range(5)]  # Fetch up to five custom phrases

    if not video_url:
        return jsonify({'error': 'No video URL provided'}), 400
    
    video_path = vp.download_video(video_url)
    if not video_path:
        return jsonify({'error': 'Failed to download video'}), 500

    scenes = vp.find_scenes(video_path)
    scene_frames = vp.extract_frames(video_path, scenes)
    
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
    }[category_choice]

    # Replace the first few phrases with custom phrases if provided
    for i, phrase in enumerate(custom_phrases):
        if phrase:  # Only replace if a custom phrase was actually provided
            description_phrases[i] = phrase
    
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
            'image': encoded_image,  # For display

        })

    # Store top action scenes in session
    top_action_scenes = sorted([scene for scene in results if scene['category'] == 'Action Scene'], key=lambda x: x['confidence'], reverse=True)[:10]
 

    return jsonify({'all_scenes': results, 'top_action_scenes': top_action_scenes})

@app.route('/concatenate_clips', methods=['POST'])
def concatenate_clips():
    data = request.get_json()
    video_url = data['video_url']
    selected_indices = data['selected_indices']
    caption_text = data.get('caption_text', '')  # Optional caption text
    audio_url = data.get('audio_url', None)  # Optional audio URL

    video_path = session['video_path']
    
    audio_path = None  # Initialize audio_path
    if audio_url:
        audio_path = vp.download_video(audio_url)  # Download the audio file if URL is provided

    if audio_url and not audio_path:
        return jsonify({'error': 'Failed to download audio'}), 400
    
    if 'top_action_scenes' not in session:
        return jsonify({'error': 'No processed video data available'}), 400

    top_action_scenes = session['top_action_scenes']
    
    try:
        clip_paths = []
        for index in selected_indices:
            index = int(index)  # Ensure index is an integer
            if index < 0 or index >= len(top_action_scenes):
                return jsonify({'error': f'Index {index} out of range'}), 400
            scene_info = top_action_scenes[index]
            clip_info = vp.save_clip(video_path, scene_info, os.path.join(app.static_folder, 'videos'), index)
            if clip_info is None:
                return jsonify({'error': 'Failed to save some clips'}), 500
            clip_paths.append(clip_info['path'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

    # Assuming video_path and clip_paths are determined earlier in your code
    final_video_info = vp.process_video(clip_paths, os.path.join(app.static_folder, 'videos', 'final_video.mp4'), caption=caption_text, audio_path=audio_path)
    if 'path' not in final_video_info:
        return jsonify({'error': 'Failed to process final video'}), 500

    return jsonify({'message': 'Video processed successfully', 'video_filename': os.path.basename(final_video_info['path'])})

@app.route('/downloads/<path:filename>', methods=['GET'])
def download(filename):
    return send_from_directory(app.static_folder, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
