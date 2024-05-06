from flask import Flask, request, jsonify
import os
import video_processing_refactored as vp

app = Flask(__name__, static_folder='static')

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('video_url')
    selected_indices = data.get('selected_indices', [])

    try:
        video_path = vp.download_video(video_url)
        if not video_path:
            return jsonify({'error': 'Failed to download video.'}), 400

        scenes = vp.find_scenes(video_path)
        scene_frames = vp.extract_frames(video_path, scenes)
        scene_categories = vp.classify_and_categorize_scenes(scene_frames, ["Skier jumping off a snow ramp", "Person skiing down a snowy mountain", "Close-up of skis on snow", "Skiing through a snowy forest", "Skier performing a spin",
            "Point-of-view shot from a ski helmet", "Group of skiers on a mountain", "Skier sliding on a rail", "Snow spraying from skis", "Skier in mid-air during a jump",
            "Person being interviewed after an event", "People in a crowd cheering", "Sitting inside of a vehicle", "Skaters standing around a ramp", "People standing around at an event",
            "Commercial break", "People having a conversation", "Person in a helmet talking to the camera", "person facing the camera", "People introducing the context for a video"])

        # Filter scenes selected by the user and ensure they exist
        clip_paths = [
            vp.save_clip(video_path, scene_categories[idx], 'static/videos', idx)['path']
            for idx in selected_indices
            if idx in scene_categories
        ]

        if not clip_paths:
            return jsonify({'error': 'No valid clips selected or clips could not be saved.'}), 404

        output_path = os.path.join('static/videos', 'final_concatenated_clip.mp4')
        vp.process_video(clip_paths, output_path)

        return jsonify({'message': 'Video processed successfully', 'video_filename': 'final_concatenated_clip.mp4'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
