import PyPDF2
from docx import Document
import io

class FileParser:
    @staticmethod
    def parse_file(file_content: bytes, filename: str) -> str:
        """Parse uploaded file and return text content"""
        
        file_extension = filename.split('.')[-1].lower()
        
        try:
            if file_extension == 'pdf':
                return FileParser._parse_pdf(file_content)
            elif file_extension == 'docx':
                return FileParser._parse_docx(file_content)
            elif file_extension == 'txt':
                return file_content.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            raise ValueError(f"Error parsing file: {str(e)}")
    
    @staticmethod
    def _parse_pdf(file_content: bytes) -> str:
        """Extract text from PDF"""
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    
    @staticmethod
    def _parse_docx(file_content: bytes) -> str:
        """Extract text from DOCX"""
        doc_file = io.BytesIO(file_content)
        document = Document(doc_file)
        
        text = ""
        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()