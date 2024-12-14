import os
import fitz  # PyMuPDF
from docx import Document
import io

def get_document_content(filepath):
    """
    Obtiene el contenido de un documento local.

    Args:
        filepath: La ruta al archivo.

    Returns:
        El contenido del documento como una cadena de texto.
        O un mensaje de error si falla
    """
    try:
        if filepath.lower().endswith('.pdf'):
            doc = fitz.open(filepath)
            content = ""
            for page in doc:
                content += page.get_text()
            return content
        elif filepath.lower().endswith('.docx'):
            doc = Document(filepath)
            content = ""
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
            return content
        elif filepath.lower().endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        else:
            return "Formato de archivo no soportado."

    except Exception as e:
        print(f"Error al procesar el archivo {filepath}: {e}")
        return f"Error al procesar el archivo {filepath}: {e}"

def scan_local_folder_and_get_documents(folder_path):
    """
    Escanea una carpeta local y devuelve el contenido de los documentos encontrados.

    Args:
        folder_path: La ruta a la carpeta.

    Returns:
        Una lista de diccionarios, donde cada diccionario representa un documento y contiene:
        - path: La ruta completa al documento.
        - name: El nombre del documento.
        - content: El contenido del documento como texto plano.
    """
    documents = []
    try:
        for root, dirs, files in os.walk(folder_path):
            # Ignorar la carpeta 'resultados' si existe
            if 'resultados' in dirs:
                dirs.remove('resultados')
                
            for file in files:
                filepath = os.path.join(root, file)
                print(f"Procesando: {file}")
                content = get_document_content(filepath)
                if not content.startswith("Error"):
                    
                    # Crear la carpeta de resultados si no existe
                    results_folder = os.path.join(folder_path, "resultados")
                    if not os.path.exists(results_folder):
                        os.makedirs(results_folder)

                    # Crear una carpeta para el documento actual dentro de resultados
                    doc_folder = os.path.join(results_folder, os.path.splitext(file)[0])
                    if not os.path.exists(doc_folder):
                        os.makedirs(doc_folder)

                    # Copiar el archivo original a la carpeta de resultados
                    destination_path = os.path.join(doc_folder, file)
                    if not os.path.exists(destination_path):
                        with open(filepath, "rb") as source_file, open(destination_path, "wb") as dest_file:
                          dest_file.write(source_file.read())

                    documents.append({'path': filepath, 'name': file, 'content': content})

        return documents

    except Exception as e:
        print(f"Error al escanear la carpeta: {e}")
        return []