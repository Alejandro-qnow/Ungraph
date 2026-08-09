"""
Value Object: DocumentType

Tipo de documento soportado por el sistema.
Es un Enum inmutable que representa los tipos de archivos que se pueden procesar.
"""

from enum import Enum


class DocumentType(Enum):
    """Tipos de documentos soportados - Value Object inmutable"""
    MARKDOWN = "markdown"
    TXT = "txt"
    WORD = "word"
    DOCX = "docx"
    PDF = "pdf"
    HTML = "html"
    CSV = "csv"
    XLSX = "xlsx"
    
    @classmethod
    def from_filename(cls, filename: str) -> "DocumentType":
        """
        Detecta el tipo de documento basándose en la extensión del archivo.
        
        Args:
            filename: Nombre del archivo con extensión
        
        Returns:
            DocumentType correspondiente
        
        Raises:
            ValueError: Si la extensión no es reconocida
        """
        filename_lower = filename.lower()
        
        if filename_lower.endswith(('.md', '.markdown')):
            return cls.MARKDOWN
        elif filename_lower.endswith('.txt'):
            return cls.TXT
        elif filename_lower.endswith(('.doc', '.docx')):
            return cls.DOCX if filename_lower.endswith('.docx') else cls.WORD
        elif filename_lower.endswith('.pdf'):
            return cls.PDF
        elif filename_lower.endswith(('.html', '.htm')):
            return cls.HTML
        elif filename_lower.endswith('.csv'):
            return cls.CSV
        elif filename_lower.endswith(('.xlsx', '.xls')):
            return cls.XLSX
        else:
            raise ValueError(f"Tipo de archivo no reconocido: {filename}")

    @classmethod
    def is_tabular(cls, file_type: "DocumentType") -> bool:
        """Indica si el tipo corresponde a datos tabulares (CSV/XLSX)."""
        return file_type in (cls.CSV, cls.XLSX)

