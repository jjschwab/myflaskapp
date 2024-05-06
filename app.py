from flask import Flask, request, jsonify, render_template
import video_processing_refactored as vp

app = Flask(__name__)

@app.route('/')
def index():
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

    scene_list = vp.find_scenes(video_path)
    # Convert scene_list to a JSON serializable format
    scenes_data = [{'start_time': str(scene[0]), 'end_time': str(scene[1])} for scene in scene_list]
    
    return jsonify(scenes_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')