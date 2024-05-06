from flask import Flask, request, jsonify, session, render_template
import video_processing_refactored as vp
import numpy as np
import json
import base64
import cv2
import logging


app = Flask(__name__, template_folder='/home/buckschwab/myflaskapp/templates')

@app.route('/test')
def test_json():
    app.logger.info("Entered the /test route")
    data = [1, 2, 3]
    return jsonify(data.tolist())

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)  # Set host to '0.0.0.0' to listen on all network interfaces

app.secret_key = 'bt\xcd\xc5\xf1\xbf19\xed\x86\xe5\xc2Y\x01\xb3\x8eh\xff\x9a\x9b\x1c\xd3\xec\xe8l'
  # Necessary for session management


def ndarray_to_base64(ndarray):
    """Converts an ndarray to a base64 encoded string."""
    _, buffer = cv2.imencode('.jpg', ndarray)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    return jpg_as_text

@app.route('/submit_video', methods=['POST'])
def submit_video():
    data = request.get_json()
    if not data:
        app.logger.error("No data received")
        return jsonify({'error': 'No data received'}), 400

    # Dummy data processing function that simulates processing that returns ndarrays
    def process_video():
        # Simulating an ndarray that might be returned from a video processing function
        return {'frames': np.zeros((100, 100, 3), dtype=np.uint8)}

    try:
        result = process_video()

        # Checking and converting all ndarray objects in the result
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, np.ndarray):
                    result[key] = ndarray_to_base64(value)
                    app.logger.info(f"Converted {key} to base64 string.")
                else:
                    app.logger.info(f"No conversion needed for {key}.")

        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error processing video: {str(e)}")
        return jsonify({'error': str(e)}), 500