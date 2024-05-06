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
    description_phrases = ["Mountain biker doing a downhill run", "Rider jumping over an obstacle", "Cyclist on a rocky trail", "Biking through forest trails", "MTB stunt on a dirt path",
            "Close-up of a mountain bike wheel", "Mountain biker navigating a sharp turn", "First-person view of a bike ride", "Mountain biker doing a trick jump", "Biking fast down a steep incline",
            "Biker with a helmet on talking to the camera", "People standing around", "a person facing and talking to the camera", "Introducing the context for a video", "a zoomed out scene of nature without any people in it",
            "Scene showing a mountain biking terrain park", "Biker taking it easy going down a hill", "mountain Biker falling and crashing", "People walking outside", "Context scene with mountain bikers not performing any tricks"]  # Example set of phrases
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')