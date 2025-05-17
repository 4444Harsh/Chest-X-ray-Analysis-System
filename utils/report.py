from fpdf import FPDF
import os
import datetime

def generate_report(img_path, age, gender, pneumonia_label, confidence):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Chest X-ray Analysis Report", ln=True, align='C')
    pdf.ln(10)

    pdf.image(img_path, x=10, y=30, w=90)
    pdf.set_y(130)
    pdf.cell(200, 10, txt=f"Predicted Age: {age} years", ln=True)
    pdf.cell(200, 10, txt=f"Predicted Gender: {gender}", ln=True)
    pdf.cell(200, 10, txt=f"Pneumonia Detection: {pneumonia_label}", ln=True)
    pdf.cell(200, 10, txt=f"Confidence: {confidence:.2f}%", ln=True)
    pdf.cell(200, 10, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)

    report_path = os.path.join("static/uploads", "report.pdf")
    pdf.output(report_path)
    return report_path
