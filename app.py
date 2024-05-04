from flask import Flask, request, jsonify, session, render_template
import video_processing_refactored as vp

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)  # Set host to '0.0.0.0' to listen on all network interfaces

app.secret_key = 'bt\xcd\xc5\xf1\xbf19\xed\x86\xe5\xc2Y\x01\xb3\x8eh\xff\x9a\x9b\x1c\xd3\xec\xe8l'
  # Necessary for session management

@app.route('/submit_video', methods=['POST'])
def submit_video():
    # Attempt to get JSON data from request
    data = request.get_json()
    if not data:
        app.logger.error("No data received")
        return jsonify({'error': 'No data received'}), 400

    video_url = data.get('video_url')
    category_choice = data.get('category_choice')
    user_descriptions = data.get('user_descriptions', [])

    # Check for required fields
    if not video_url or not category_choice:
        app.logger.error("Missing data: 'video_url' or 'category_choice' not provided")
        return jsonify({'error': "Missing data: 'video_url' or 'category_choice' not provided"}), 400

    # Define default categories and merge them with user descriptions
    category_phrases = {
        "1": [
            "Mountain biker doing a downhill run", "Rider jumping over an obstacle",
            "Cyclist on a rocky trail", "Biking through forest trails", "MTB stunt on a dirt path"
        ],
        "2": [
            "Skier jumping off a snow ramp", "Person skiing down a snowy mountain",
            "Close-up of skis on snow", "Skiing through a snowy forest", "Skier performing a spin"
        ],
        "3": [
            "Surfer riding a big wave", "Close-up of a surfboard on water",
            "Surfer performing a cutback", "Wave curling over a surfer", "Aerial view of a surf competition"
        ]
    }

    chosen_category_phrases = category_phrases.get(category_choice, category_phrases["1"])
    description_texts = user_descriptions + chosen_category_phrases[len(user_descriptions):]

    # Process the video
    try:
        video_path = vp.download_video(video_url)
        if not video_path:
            app.logger.error("Failed to download video from URL: " + video_url)
            return jsonify({'error': 'Failed to download video.'}), 400

        scenes = vp.find_scenes(video_path)
        scene_frames = vp.extract_frames(video_path, scenes)
        scene_categories = vp.classify_and_categorize_scenes(scene_frames, description_texts)

        # Return the processed data
        return jsonify(scene_categories)
    except Exception as e:
        app.logger.error(f"Error processing video: {str(e)}")
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
@app.route('/process_video', methods=['GET'])
def process_video():
    video_path = session.get('video_path')
    descriptions = session.get('descriptions', [])
    categories = session.get('categories', {}).get(session.get('category_choice', '1'), [])
    
    if not video_path:
        return jsonify({"error": "Video not found. Please upload first."}), 404

    scenes = vp.find_scenes(video_path)
    scene_frames = vp.extract_frames(video_path, scenes)
    scene_categories = vp.classify_and_categorize_scenes(scene_frames, descriptions + categories)
    
    session['scenes'] = scene_categories  # Store scenes for review or further processing
    return jsonify({"message": "Video processed successfully", "scenes": scene_categories}), 200

@app.route('/select_scenes', methods=['POST'])
def select_scenes():
    selected_indices = request.json.get('selected_indices', [])
    scenes = session.get('scenes', {})
    selected_scenes = {index: scenes[index] for index in selected_indices if index in scenes}
    
    session['selected_scenes'] = selected_scenes
    return jsonify({"message": "Scenes selected successfully", "selected_scenes": selected_scenes}), 200

@app.route('/finalize_video', methods=['POST'])
def finalize_video():
    caption = request.json.get('caption', "")
    audio_url = request.json.get('audio_url', "")
    
    selected_scenes = session.get('selected_scenes', {})
    clip_paths = [vp.save_clip(session['video_path'], scene, vp.BASE_DIRECTORY, index)['path'] for index, scene in selected_scenes.items()]
    
    audio_path = vp.download_video(audio_url) if audio_url else None
    output_path = os.path.join(vp.BASE_DIRECTORY, "final_concatenated_clip.mp4")
    
    vp.process_video(clip_paths, output_path, caption, audio_path)
    return jsonify({"message": "Video finalized successfully", "output_path": output_path}), 200

