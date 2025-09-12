import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import json
import os
from flask import current_app


class QRCodeService:
    """Service for generating QR codes for campers"""
    
    def __init__(self):
        self.qr_config = {
            'version': 1,
            'error_correction': qrcode.constants.ERROR_CORRECT_L,
            'box_size': 10,
            'border': 4,
        }
    
    def generate_camper_qr_data(self, camper_id: str, camper_code: str) -> str:
        """Generate QR code data containing frontend URL for camper"""
        try:
            # Get frontend URL from environment
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173/')
            
            # Ensure frontend_url ends with /
            if not frontend_url.endswith('/'):
                frontend_url += '/'
            
            # Generate the URL: FRONTEND_URL/{camper_id}/qrcode
            qr_url = f"{frontend_url}{camper_id}/qrcode"
            
            return qr_url
            
        except Exception as e:
            current_app.logger.error(f"Error generating camper QR URL: {str(e)}")
            # Fallback to old JSON format if there's an error
            qr_data = {
                'camper_id': camper_id,
                'camper_code': camper_code,
                'type': 'camper_identification'
            }
            return json.dumps(qr_data)
    
    def generate_qr_code_png_base64(self, data: str) -> str:
        """Generate QR code as base64 encoded PNG image"""
        try:
            qr = qrcode.QRCode(**self.qr_config)
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
            
        except Exception as e:
            current_app.logger.error(f"Error generating QR code PNG: {str(e)}")
            raise Exception("Failed to generate QR code")
    
    def generate_qr_code_svg(self, data: str) -> str:
        """Generate QR code as SVG string"""
        try:
            factory = qrcode.image.svg.SvgPathImage
            qr = qrcode.QRCode(**self.qr_config, image_factory=factory)
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create SVG
            img = qr.make_image()
            
            # Convert to string
            buffer = BytesIO()
            img.save(buffer)
            svg_str = buffer.getvalue().decode('utf-8')
            
            return svg_str
            
        except Exception as e:
            current_app.logger.error(f"Error generating QR code SVG: {str(e)}")
            raise Exception("Failed to generate QR code")
    
    def generate_qr_code_html_img(self, data: str) -> str:
        """Generate QR code as HTML img tag with base64 data"""
        try:
            base64_img = self.generate_qr_code_png_base64(data)
            html = f'<img src="data:image/png;base64,{base64_img}" alt="Camper QR Code" style="max-width: 200px; height: auto;" />'
            return html
            
        except Exception as e:
            current_app.logger.error(f"Error generating QR code HTML: {str(e)}")
            raise Exception("Failed to generate QR code HTML")
    
    def generate_camper_qr_code(self, camper_id: str, camper_code: str, format_type: str = 'html') -> str:
        """
        Generate QR code for a camper
        
        Args:
            camper_id: The camper's registration ID
            camper_code: The camper's unique code
            format_type: 'html', 'base64', or 'svg'
        
        Returns:
            QR code in the requested format
        """
        try:
            qr_data = self.generate_camper_qr_data(camper_id, camper_code)
            
            if format_type == 'html':
                return self.generate_qr_code_html_img(qr_data)
            elif format_type == 'base64':
                return self.generate_qr_code_png_base64(qr_data)
            elif format_type == 'svg':
                return self.generate_qr_code_svg(qr_data)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
                
        except Exception as e:
            current_app.logger.error(f"Error generating camper QR code: {str(e)}")
            raise Exception("Failed to generate camper QR code")
    
    def decode_camper_qr_data(self, qr_data_str: str) -> dict:
        """
        Decode QR code data back to camper information
        
        Args:
            qr_data_str: The JSON string from QR code
            
        Returns:
            Dictionary containing camper information
        """
        try:
            data = json.loads(qr_data_str)
            
            # Validate required fields
            required_fields = ['camper_id', 'camper_code', 'type']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate type
            if data['type'] != 'camper_identification':
                raise ValueError("Invalid QR code type")
            
            return data
            
        except json.JSONDecodeError:
            raise ValueError("Invalid QR code data format")
        except Exception as e:
            current_app.logger.error(f"Error decoding QR code data: {str(e)}")
            raise ValueError("Failed to decode QR code data")


# Create singleton instance
qr_service = QRCodeService()
