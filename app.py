from flask import Flask, render_template, request, send_file
from fpdf import FPDF
import os
from datetime import datetime
import barcode
from barcode.writer import ImageWriter
import re

app = Flask(__name__)

# Ensure required dependencies are installed
try:
    import barcode
except ImportError:
    raise ImportError("Please install python-barcode: pip install python-barcode")

class PDF(FPDF):
    def header(self):
        # Set margins to 0 for header to remove side spacing
        self.set_margins(0, 10, 0)
        self.set_draw_color(0, 51, 102)
        self.set_fill_color(245, 245, 245)
        self.rect(0, 10, 210, 30, 'DF')  # Full-width header rectangle

        # Load and place the logo
        logo_path = os.path.abspath(os.path.join('static', 'assets', 'logo.png'))
        try:
            if os.path.exists(logo_path):
                self.image(logo_path, x=1, y=10, w=210, h=28)
            else:
                self.set_font('Arial', 'B', 12)
                self.set_text_color(0, 51, 102)
                self.set_xy(10, 12)
                self.cell(0, 10, 'LOGO', 0, 0, 'L')
        except Exception as e:
            print(f"Logo loading error: {e}")
            self.set_font('Arial', 'B', 12)
            self.set_text_color(0, 51, 102)
            self.set_xy(10, 12)
            self.cell(0, 10, 'LOGO', 0, 0, 'L')

        # Add title below header
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 0, 0)
        self.set_xy(0, 42)  # Reduced from 45
        self.cell(210, 8, 'Medical Examination Form', 0, 1, 'C')

        # Reset margins for body
        self.set_margins(10, 10, 10)

        # Header content (Generated on, Report ID, Barcode)
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.report_id = f"MED-{datetime.now().strftime('%Y%m%d%H%M')}"
        
        self.set_xy(10, 50)  # Reduced from 55
        self.cell(95, 6, f'Generated on: {current_datetime}', 0, 0, 'L')
        self.cell(95, 6, f'Report ID: {self.report_id}', 0, 1, 'R')

        try:
            barcode_dir = os.path.abspath('static/barcodes')
            os.makedirs(barcode_dir, exist_ok=True)
            barcode_id = self.form_data.get('barcode', self.report_id)
            code128 = barcode.get('code128', barcode_id, writer=ImageWriter())
            barcode_filename = os.path.join(barcode_dir, f"barcode_{barcode_id}")
            code128.save(barcode_filename)
            self.image(f"{barcode_filename}.png", x=10, y=56, w=50, h=10)  # Adjusted y from 62
            os.remove(f"{barcode_filename}.png")
        except Exception as e:
            print(f"Barcode generation error: {e}")
            self.set_font('Arial', '', 10)
            self.set_xy(10, 56)
            self.cell(0, 10, 'Barcode Placeholder', 0, 0, 'L')

        self.ln(20)  # Reduced from 35

    def footer(self):
        self.set_y(-15)
        if self.page_no() == self.alias_nb_pages():
            self.line(130, self.get_y(), 190, self.get_y())
            self.set_font('Arial', '', 10)
            self.cell(0, 5, "Doctor's Signature", 0, 1, 'R')
        
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, f'Page {self.page_no()}/{self.alias_nb_pages()}', 0, 1, 'C')
        self.set_font('Arial', 'I', 6)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, 'CONFIDENTIAL MEDICAL INFORMATION', 0, 0, 'C')

    def create_section_title(self, title):
        self.set_draw_color(0, 51, 102)
        self.set_fill_color(240, 248, 255)
        self.set_text_color(0, 51, 102)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, title, 1, 1, 'L', True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def create_table_header(self, headers, widths):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(220, 230, 241)
        for i in range(len(headers)):
            self.cell(widths[i], 6, headers[i], 1, 0, 'C', True)
        self.ln()

    def create_table_row(self, data, widths, align=None, height=6, alternate_color=False):
        if align is None:
            align = ['L'] * len(data)
        if alternate_color:
            self.set_fill_color(245, 245, 245)
            fill = True
        else:
            fill = False
        self.set_font('Arial', '', 10)
        for i in range(len(data)):
            self.cell(widths[i], height, str(data[i])[:50], 1, 0, align[i], fill)
        self.ln()

    def calculate_bmi_category(self, bmi_value):
        try:
            bmi = float(bmi_value)
            if bmi < 18.5:
                return f"{bmi:.1f} (Underweight)"
            elif bmi < 25:
                return f"{bmi:.1f} (Normal)"
            elif bmi < 30:
                return f"{bmi:.1f} (Overweight)"
            else:
                return f"{bmi:.1f} (Obese)"
        except:
            return str(bmi_value)

    def set_form_data(self, form_data):
        self.form_data = form_data

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        # Handle checkboxes
        checkboxes = [
            'tooth_pain', 'sensitivity', 'bleeding_gums', 'previous_treatments',
            'upper_jaw_issue', 'upper_jaw_treatment', 'lower_jaw_issue', 'lower_jaw_treatment',
            'gums_issue', 'gums_treatment', 'filling', 'cleaning', 'root_canal', 'extraction',
            'diabetes', 'hypertension', 'asthma', 'heart_disease', 'tuberculosis',
            'kidney_disease', 'liver_disease', 'cancer'
        ]
        for checkbox in checkboxes:
            form_data[checkbox] = form_data.get(checkbox, '')

        pdf = PDF()
        pdf.set_form_data(form_data)
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Personal Information
        pdf.create_section_title('Patient Information')
        col_width = 95
        line_height = 6  # Reduced from 8
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(10, pdf.get_y(), 190, 30)  # Reduced height
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(40, line_height, 'Name:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(col_width - 40, line_height, form_data.get('name', '')[:50], 0, 0)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(40, line_height, 'Gender:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(col_width - 40, line_height, form_data.get('gender', '').capitalize(), 0, 1)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(40, line_height, 'Date of Birth:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(col_width - 40, line_height, form_data.get('dob', ''), 0, 0)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(40, line_height, 'Age:', 0, 0)
        age = ''
        if form_data.get('dob'):
            try:
                dob = datetime.strptime(form_data.get('dob'), '%Y-%m-%d')
                today = datetime.now()
                age = str(today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day)))
            except:
                age = ''
        pdf.set_font('Arial', '', 12)
        pdf.cell(col_width - 40, line_height, age, 0, 1)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(40, line_height, 'Marital Status:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(col_width - 40, line_height, form_data.get('married', '').capitalize(), 0, 0)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(40, line_height, 'Occupation:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(col_width - 40, line_height, form_data.get('occupation', '')[:50], 0, 1)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(40, line_height, 'Date of Exam:', 0, 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(col_width - 40, line_height, form_data.get('exam_date', ''), 0, 0)
        pdf.ln(5)  # Reduced from 10
        
        # Measurements Section
        pdf.create_section_title('Physical Measurements')
        headers = ['Measurement', 'Value', 'Reference Range']
        widths = [50, 40, 50]
        pdf.create_table_header(headers, widths)
        
        bmi_value = form_data.get('bmi', '')
        bmi_with_category = pdf.calculate_bmi_category(bmi_value)
        
        measurements = [
            ['Height', form_data.get('height', '') + ' cm', ''],
            ['Weight', form_data.get('weight', '') + ' kg', ''],
            ['BMI', bmi_with_category, '18.5-24.9'],
            ['Blood Pressure', form_data.get('bp', '') + ' mmHg', '90/60-120/80'],
            ['Chest Circumference', form_data.get('chest', '') + ' cm', ''],
            ['Waist Circumference', form_data.get('waist', '') + ' cm', ''],
            ['Pulse Rate', form_data.get('pulse', '') + ' bpm', '60-100'],
            ['Temperature', form_data.get('temp', '') + ' °C', '36.1-37.2'],
        ]
        
        row_alternate = False
        for measurement in measurements:
            pdf.create_table_row(measurement, widths, ['L', 'C', 'L'], 6, row_alternate)
            row_alternate = not row_alternate
        pdf.ln(3)  # Reduced from 5
        
        # Lifestyle Assessment
        pdf.create_section_title('Lifestyle Assessment')
        lifestyle_data = [
            ['Smoking History', form_data.get('smoking', 'Never')],
            ['Alcohol Consumption', form_data.get('alcohol', 'Never')],
            ['Current Medications', form_data.get('medication', 'None')],
            ['Surgical History', form_data.get('surgery', 'None')]
        ]
        
        lifestyle_widths = [60, 130]
        pdf.create_table_header(['Factor', 'Details'], lifestyle_widths)
        
        row_alternate = False
        for item in lifestyle_data:
            pdf.create_table_row(item, lifestyle_widths, ['L', 'L'], 6, row_alternate)
            row_alternate = not row_alternate
        pdf.ln(3)
        
        # Eye Examination
        pdf.create_section_title('Eye Examination')
        eye_headers = ['Test', 'Right Eye', 'Left Eye']
        eye_widths = [90, 50, 50]
        pdf.create_table_header(eye_headers, eye_widths)
        
        eye_tests = [
            ['Distant Vision Without Glasses', form_data.get('distant_without_right', ''), form_data.get('distant_without_left', '')],
            ['Distant Vision With Glasses', form_data.get('distant_with_right', ''), form_data.get('distant_with_left', '')],
            ['Near Vision Without Glasses', form_data.get('near_without_right', ''), form_data.get('near_without_left', '')],
            ['Near Vision With Glasses', form_data.get('near_with_right', ''), form_data.get('near_with_left', '')],
            ['Colour Vision', form_data.get('color_vision', ''), '']
        ]
        
        row_alternate = False
        for test in eye_tests:
            pdf.create_table_row(test, eye_widths, ['L', 'C', 'C'], 6, row_alternate)
            row_alternate = not row_alternate
        
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Provisional Diagnosis:', 0, 1)
        pdf.set_font('Arial', '', 10)
        diagnosis = form_data.get('eye_diagnosis', '')[:500]
        if pdf.get_y() > 240:  # Adjusted threshold
            pdf.add_page()
        pdf.multi_cell(0, 6, diagnosis)
        pdf.ln(3)
        
        # Audiometry
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.create_section_title('Audiometry (Hearing Test)')
        hearing_headers = ['Frequency', 'Right Ear (dB)', 'Left Ear (dB)', 'Assessment']
        hearing_widths = [50, 45, 45, 50]
        pdf.create_table_header(hearing_headers, hearing_widths)
        
        frequencies = ['500hz', '1000hz', '2000hz', '4000hz']
        row_alternate = False
        for freq in frequencies:
            right_value = form_data.get(f're_{freq}', '')
            left_value = form_data.get(f'le_{freq}', '')
            assessment = form_data.get(f'assessment_{freq}', '')
            pdf.create_table_row([freq.upper(), right_value, left_value, assessment], hearing_widths, ['L', 'C', 'C', 'C'], 6, row_alternate)
            row_alternate = not row_alternate
        
        pdf.ln(3)
        
        # Dental Examination
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.create_section_title('Dental Examination')
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Reported Symptoms:', 0, 1)
        
        symptoms = [
            ('Tooth Pain', 'tooth_pain'),
            ('Sensitivity to Hot/Cold', 'sensitivity'),
            ('Bleeding Gums', 'bleeding_gums'),
            ('Previous Dental Treatments', 'previous_treatments')
        ]
        
        pdf.set_font('Arial', '', 10)
        for i in range(0, len(symptoms), 2):
            pdf.cell(5, 6, '')
            pdf.cell(95, 6, f'[{"X" if form_data.get(symptoms[i][1]) else " "}] {symptoms[i][0]}')
            if i + 1 < len(symptoms):
                pdf.cell(90, 6, f'[{"X" if form_data.get(symptoms[i+1][1]) else " "}] {symptoms[i+1][0]}', 0, 1)
            else:
                pdf.ln()
        pdf.ln(3)
        
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Examination Findings:', 0, 1)
        dental_headers = ['Area Examined', 'Issue Detected', 'Treatment Needed', 'Comments']
        dental_widths = [50, 35, 35, 70]
        pdf.create_table_header(dental_headers, dental_widths)
        
        areas = [
            ('Upper Jaw', 'upper_jaw_issue', 'upper_jaw_treatment', 'upper_jaw_comments'),
            ('Lower Jaw', 'lower_jaw_issue', 'lower_jaw_treatment', 'lower_jaw_comments'),
            ('Gums', 'gums_issue', 'gums_treatment', 'gums_comments')
        ]
        
        row_alternate = False
        for area, issue, treatment, comments in areas:
            pdf.create_table_row([
                area, 
                'Yes' if form_data.get(issue) else 'No',
                'Yes' if form_data.get(treatment) else 'No',
                form_data.get(comments, '')[:50]
            ], dental_widths, ['L', 'C', 'C', 'L'], 6, row_alternate)
            row_alternate = not row_alternate
        pdf.ln(3)
        
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Recommended Treatments:', 0, 1)
        treatments = [
            ('Filling', 'filling'),
            ('Cleaning', 'cleaning'),
            ('Root Canal', 'root_canal'),
            ('Extraction', 'extraction')
        ]
        
        pdf.set_font('Arial', '', 10)
        for treatment, field in treatments:
            pdf.cell(5, 6, '')
            pdf.cell(0, 6, f'[{"X" if form_data.get(field) else " "}] {treatment}', 0, 1)
        
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Additional Dental Notes:', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, form_data.get('dental_notes', '')[:500])
        
        # General Medical History
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.create_section_title('General Medical History')
        medical_conditions = [
            ('Diabetes', 'diabetes'),
            ('Hypertension', 'hypertension'),
            ('Asthma', 'asthma'),
            ('Heart Disease', 'heart_disease'),
            ('Tuberculosis', 'tuberculosis'),
            ('Kidney Disease', 'kidney_disease'),
            ('Liver Disease', 'liver_disease'),
            ('Cancer', 'cancer')
        ]
        
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Medical Conditions:', 0, 1)
        pdf.set_font('Arial', '', 10)
        for i in range(0, len(medical_conditions), 2):
            pdf.cell(5, 6, '')
            pdf.cell(95, 6, f'[{"X" if form_data.get(medical_conditions[i][1]) else " "}] {medical_conditions[i][0]}')
            if i + 1 < len(medical_conditions):
                pdf.cell(90, 6, f'[{"X" if form_data.get(medical_conditions[i+1][1]) else " "}] {medical_conditions[i+1][0]}', 0, 1)
            else:
                pdf.ln()
        pdf.ln(3)
        
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Family Medical History:', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, form_data.get('family_history', '')[:500])
        
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Allergies:', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, form_data.get('allergies', '')[:500])
        
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Current Symptoms/Complaints:', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, form_data.get('current_symptoms', '')[:500])
        
        # Conclusion and Recommendations
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.create_section_title('Conclusion and Recommendations')
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Key Findings:', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, form_data.get('findings', '')[:500])
        
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Recommendations:', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, form_data.get('recommendations', '')[:500])
        
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 6, 'Follow-up:', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, form_data.get('follow_up', 'No'), 0, 1)
        
        # Generate PDF
        safe_name = re.sub(r'[^\w\-]', '', form_data.get('name', 'patient').replace(' ', '_'))
        filename = f"medical_exam_{safe_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_output_path = os.path.abspath(os.path.join('static', 'pdfs', filename))
        try:
            os.makedirs(os.path.dirname(pdf_output_path), exist_ok=True)
        except PermissionError as e:
            print(f"Failed to create PDF directory: {e}")
            raise
        pdf.output(pdf_output_path)
        
        return render_template('result.html', filename=filename)
    
    return render_template('form.html')

@app.route('/download/<filename>')
def download(filename):
    safe_filename = os.path.basename(filename)
    file_path = os.path.abspath(os.path.join('static', 'pdfs', safe_filename))
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    # Ensure directories are created
    for directory in ['barcodes', 'pdfs', 'signatures', 'assets']:
        try:
            os.makedirs(os.path.abspath(os.path.join('static', directory)), exist_ok=True)
        except PermissionError as e:
            print(f"Failed to create {directory} directory: {e}")
            raise
    app.run(debug=True)