from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

class PDFService:
    def generate_medical_report(self, analysis_data):
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        

        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, "Rural AI Doctor - Medical Report")
        

        p.setFont("Helvetica", 12)
        p.drawString(100, 730, f"Image Type: {analysis_data.image_type.replace('_', ' ').title()}")
        p.drawString(100, 715, f"Severity: {analysis_data.severity.upper()}")
        
     
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, 680, "Key Clinical Findings:")
        p.setFont("Helvetica", 10)
        y_pos = 660
        for finding in analysis_data.findings.split('\n'):
            p.drawString(110, y_pos, f"• {finding}")
            y_pos -= 15
            
       
        p.setFont("Helvetica-Oblique", 8)
        p.drawString(100, 100, "Disclaimer: This AI analysis is for informational purposes only.")
        
        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer

pdf_service = PDFService()