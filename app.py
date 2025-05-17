from flask import Flask, render_template, request, send_file, url_for, flash, redirect
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import tensorflow as tf
import absl.logging
import warnings

# Initialize Flask app
app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your-secret-key-here'  # Change this for production!

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Suppress TensorFlow warnings
absl.logging.set_verbosity(absl.logging.ERROR)
tf.get_logger().setLevel('ERROR')
warnings.filterwarnings('ignore')


def load_model(model_path):
    """Load and prepare TensorFlow model"""
    model = tf.keras.models.load_model(model_path)
    if not model.optimizer:
        model.compile(optimizer='adam',
                      loss='binary_crossentropy',
                      metrics=['accuracy'])
    return model


# Load ML models
try:
    age_model = load_model('models/model_age.h5')
    gender_model = load_model('models/model_gender.h5')
    pneumonia_model = load_model('models/pneumonia_model (1).h5')
except Exception as e:
    print(f"CRITICAL: Failed to load models: {e}")
    exit(1)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_xray(image_path):
    """Validate if the image is a proper X-ray"""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            return False, "Cannot read image (may be corrupted)"

        height, width = img.shape
        if height < 256 or width < 256:
            return False, f"Image too small ({width}x{height}). Min 256x256 required"

        if np.std(img) < 15:
            return False, "Image lacks sufficient detail"

        hist = cv2.calcHist([img], [0], None, [256], [0, 256])
        peak = np.argmax(hist)

        if peak > 200:
            return False, "Doesn't appear to be an X-ray"

        return True, "Valid X-ray"

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def predict_age_gender(image_path):
    """Predict age and gender from X-ray"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = 255 - img  # Invert
    img = cv2.resize(img, (128, 128))
    img = img.reshape(1, 128, 128, 1) / 255.0

    age = int(np.round(age_model.predict(img)[0][0]))
    gender_pred = gender_model.predict(img)[0][0]
    gender = 'Male' if gender_pred > 0.5 else 'Female'
    return age, gender


def predict_pneumonia(image_path):
    """Detect pneumonia from X-ray"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (150, 150))
    img = img.reshape(1, 150, 150, 1) / 255.0

    pred = pneumonia_model.predict(img)[0][0]
    label = 'PNEUMONIA' if pred > 0.5 else 'NORMAL'
    confidence = pred * 100 if pred > 0.5 else (1 - pred) * 100
    return label, confidence


def generate_report(image_path, age, gender, pneumonia, confidence):
    """Generate PDF report"""
    from fpdf import FPDF
    import datetime

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Chest X-ray Analysis Report", ln=True, align='C')
    pdf.ln(10)

    pdf.image(image_path, x=10, y=30, w=90)
    pdf.set_y(130)
    pdf.cell(200, 10, txt=f"Predicted Age: {age} years", ln=True)
    pdf.cell(200, 10, txt=f"Predicted Gender: {gender}", ln=True)
    pdf.cell(200, 10, txt=f"Pneumonia Detection: {pneumonia}", ln=True)
    pdf.cell(200, 10, txt=f"Confidence: {confidence:.2f}%", ln=True)
    pdf.cell(200, 10, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)

    report_path = os.path.join(app.config['UPLOAD_FOLDER'], "report.pdf")
    pdf.output(report_path)
    return report_path


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'POST':
        # Check if file was uploaded
        if 'xray' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['xray']

        # Check if file is selected
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        # Validate file extension
        if not allowed_file(file.filename):
            flash('Only PNG, JPG, and JPEG files are allowed', 'error')
            return redirect(request.url)

        try:
            # Generate unique filenames to prevent collisions
            import uuid
            unique_id = uuid.uuid4().hex[:8]  # First 8 characters of UUID
            base_filename = secure_filename(file.filename)
            temp_filename = f"temp_{unique_id}_{base_filename}"
            final_filename = f"processed_{unique_id}_{base_filename}"

            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            final_path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)

            # Save temporary file
            file.save(temp_path)

            # Check file size
            if os.path.getsize(temp_path) > MAX_FILE_SIZE:
                os.remove(temp_path)
                flash('File too large (max 10MB allowed)', 'error')
                return redirect(request.url)

            # Validate X-ray content
            is_valid, msg = validate_xray(temp_path)
            if not is_valid:
                os.remove(temp_path)
                flash(msg, 'error')
                return redirect(request.url)

            try:
                # Process the image
                age, gender = predict_age_gender(temp_path)
                pneumonia_label, confidence = predict_pneumonia(temp_path)

                # Ensure destination doesn't exist
                if os.path.exists(final_path):
                    os.remove(final_path)

                # Rename to final filename
                os.rename(temp_path, final_path)

                # Generate report
                report_path = generate_report(
                    final_path,
                    age,
                    gender,
                    pneumonia_label,
                    confidence
                )

                # Return results
                return render_template(
                    'analyze.html',
                    image_path=url_for('static', filename=f'uploads/{final_filename}'),
                    age=age,
                    gender=gender,
                    pneumonia=pneumonia_label,
                    confidence=confidence,
                    report_url=url_for('download_report'),
                    success=True
                )

            except Exception as processing_error:
                # Clean up temporary files if analysis fails
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                flash(f'Analysis failed: {str(processing_error)}', 'error')
                return redirect(request.url)

        except Exception as e:
            # Clean up if any error occurs during upload
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            flash(f'Upload failed: {str(e)}', 'error')
            return redirect(request.url)

    # GET request - show empty form
    return render_template('analyze.html', success=False)


@app.route('/download')
def download_report():
    report_path = os.path.join(app.config['UPLOAD_FOLDER'], 'report.pdf')
    if not os.path.exists(report_path):
        flash('No report available', 'error')
        return redirect(url_for('analyze'))
    return send_file(report_path, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)