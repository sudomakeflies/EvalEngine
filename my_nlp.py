from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_summary(text):
    """
    Genera un resumen de un texto utilizando la API de GPT-4 si el texto supera un límite de 500 palabras.
    Si el texto ya está resumido (500 palabras o menos), se retorna directamente como el resultado.
    """
    MAX_WORDS = 500  # Número máximo de palabras para considerar que el texto ya está resumido
    
    try:
        # Contar palabras en el texto
        word_count = len(text.split())
        logger.info(f"Procesando texto con {word_count} palabras")
        
        if word_count <= MAX_WORDS:
            # Si el texto tiene 500 palabras o menos, se considera resumido
            logger.info("Texto dentro del límite de palabras, retornando sin resumir")
            results = text.strip()
        else:
            # Si el texto excede 500 palabras, se envía al modelo GPT-4 para resumir
            logger.info("Generando resumen con GPT-4")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides concise summaries."},
                    {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
                ]
            )
            results = response.choices[0].message.content.strip()
            logger.info("Resumen generado exitosamente")
        
        return results
    except Exception as e:
        logger.error(f"Error al generar el resumen: {str(e)}", exc_info=True)
        return f"Error al generar el resumen: {str(e)}"

def process_documents(documents, guidelines=None):
    """
    Procesa una lista de documentos, generando resúmenes y borradores de Anexo 5 y Anexo 2.

    Args:
        documents: Una lista de diccionarios, donde cada diccionario representa un documento (path, name, content).
        guidelines: Directrices específicas para el procesamiento de documentos y generación de anexos (opcional).

    Returns:
        Un diccionario que contiene:
        - annex2: El borrador del Anexo 2
        - annex5: El borrador del Anexo 5
    """
    try:
        logger.info(f"Iniciando procesamiento de {len(documents)} documentos")
        results = []
        all_summaries = []  # Lista para almacenar todos los resúmenes

        for doc in documents:
            logger.info(f"Procesando documento: {doc['name']} ({doc['path']})")
            
            # Verificar que el contenido sea texto válido
            if not isinstance(doc['content'], str):
                logger.error(f"Contenido inválido en documento {doc['name']}: {type(doc['content'])}")
                raise ValueError(f"Contenido inválido en documento {doc['name']}")
                
            summary = generate_summary(doc['content'])
            
            results.append({
                'path': doc['path'],
                'name': doc['name'],
                'summary': summary,
            })

            all_summaries.append(f"Documento: {doc['name']}\nResumen:\n{summary}\n")

        # Guardar todos los resúmenes en un solo archivo plano
        doc_folder = os.path.join(os.path.dirname(documents[0]['path']), "resultados")
        os.makedirs(doc_folder, exist_ok=True)
        
        contexto_path = os.path.join(doc_folder, "contexto_ie.txt")
        logger.info(f"Guardando resúmenes en {contexto_path}")
        
        with open(contexto_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(all_summaries))

        # Leer directamente el archivo consolidado para generar los anexos
        with open(contexto_path, "r", encoding="utf-8") as f:
            consolidated_text = f.read()

        # Si hay directrices específicas, agregarlas al contexto
        if guidelines:
            logger.info("Agregando directrices específicas al contexto")
            consolidated_text = f"Directrices específicas:\n{guidelines}\n\nContexto de la IE:\n{consolidated_text}"

        logger.info("Generando borrador del Anexo 5")
        annex5_draft = generate_annex_draft(consolidated_text, "Anexo 5")
        
        logger.info("Generando borrador del Anexo 2")
        annex2_draft = generate_annex_draft(annex5_draft, "Anexo 2")

        # Guardar borradores
        with open(os.path.join(doc_folder, "anexo5_borrador.txt"), "w", encoding="utf-8") as f:
            f.write(annex5_draft)

        with open(os.path.join(doc_folder, "anexo2_borrador.txt"), "w", encoding="utf-8") as f:
            f.write(annex2_draft)
            
        logger.info("Procesamiento de documentos completado exitosamente")
        return {
            'annex2': annex2_draft,
            'annex5': annex5_draft
        }
    except Exception as e:
        logger.error(f"Error en process_documents: {str(e)}", exc_info=True)
        return {
            'error': f"Error processing documents: {str(e)}"
        }

def generate_annex_draft(text, annex_type):
    """
    Genera un borrador de anexo  basado en el contexto de la IE y tipo de anexo

    Args:
        text: El texto de contexto de la IE necesario para el generar el borrador.
        annex_type: El tipo de anexo a generar ("Anexo 5" o "Anexo 2").

    Returns:
        El borrador del anexo generado.
    """
    try:
        logger.info(f"Generando borrador para {annex_type}")
        
        if annex_type == "Anexo 5":
            prompt = f"""Considerando que este es un documento de evaluación de desempeño docente, genera un borrador para el Anexo 5 basado en el siguiente texto:

                Instrucciones para la generación del documento:

                1. **Estructura del documento**:
                - Seguir el formato oficial del Ministerio de Educación Nacional de Colombia.
                - Incluir las áreas de gestión: Académica, Administrativa y Comunitaria.
                - Cubrir competencias funcionales y comportamentales.

                2. **Elementos clave a incluir**:
                - Nombre completo del docente: Diego Estiben Beltrán Calderón.
                - Número de identificación: 80213550 de Bogotá.
                - Área de desempeño.
                - Competencias específicas evaluadas organizadas por áreas de gestión:
                    **Académica:**
                    1. Dominio Curricular
                    2. Planeación y Organización
                    3. Pedagogía y Didáctica
                    4. Evaluación y Aprendizaje
                    **Administrativa:**
                    5. Uso de Recursos
                    6. Seguimiento de Procesos
                    **Comunitaria:**
                    7. Comunicación Institucional
                    8. Comunidad y Entorno
                    **Competencias Comportamentales:**
                    9. Liderazgo
                    10. Trabajo en Equipo
                    11. Iniciativa
                - Contribuciones individuales para cada competencia que incluyan los siguientes elementos:
                    - **Verbo:** Acción observable y verificable (por ejemplo: implementar, diseñar, documentar, presentar).
                    - **Objeto:** Resultado específico que el docente busca lograr (por ejemplo: un informe, base de datos, proyecto).
                    - **Condición de calidad:** Características específicas de calidad del resultado esperado.
                - Criterios de evaluación (mínimo 3 por contribución).
                - Evidencias documentales (mínimo 1 por cada criterio de evaluación).

                3. **Directrices específicas**:
                - Usar lenguaje oficial y técnico de evaluación docente.
                - Describir contribuciones medibles y verificables.
                - Alinear objetivos con el Proyecto Educativo Institucional (PEI) y el contexto de la IE.
                - **Incluir contribuciones para todas las competencias listadas, distribuyendo correctamente:**
                    - **Gestión Académica:** Dominio Curricular, Planeación y Organización, Pedagogía y Didáctica, Evaluación y Aprendizaje.
                    - **Gestión Administrativa:** Uso de Recursos, Seguimiento de Procesos.
                    - **Gestión Comunitaria:** Comunicación Institucional, Comunidad y Entorno.
                    - **Competencias Comportamentales:** Liderazgo, Trabajo en Equipo, Iniciativa.

                4. **Generalmente las evidencias usadas son**:
                - Informes y reportes.
                - Copia de correos electrónicos.
                - Actas de reuniones.
                - Copia del cuaderno de novedades.
                - Fotografías.
                - Pantallazos (calendario, plataformas como Teams o correos).
                - Plan de clase.
                - Encuadre pedagógico.

                5. **Ejemplo de tablas de evaluación completa**:

                **Tabla de Competencias Funcionales:**

                | Área de Gestión | Competencia | Contribución Individual | Criterios de Evaluación | Evidencias Primera Evaluación | Evidencias Segunda Evaluación |
                |----------------|-------------|------------------------|------------------------|-------------------------------|-------------------------------|
                | Académica | Dominio Curricular | Diseñar e implementar un programa curricular integrado para estudiantes de educación técnica, orientado al proyecto "Producción de Polvo de Limón", garantizando un aprendizaje significativo y contextualizado. | • Elaboración del programa curricular <br> • Evaluación de la relevancia de los contenidos <br> • Impacto en los resultados académicos | • Borrador del programa curricular <br> • Encuestas iniciales a estudiantes <br> • Informe preliminar de impacto | • Versión final del programa curricular <br> • Resultados finales de evaluación académica <br> • Informe completo del impacto |
                | Académica | Pedagogía y Didáctica | Crear y aplicar estrategias didácticas basadas en TIC para promover la participación activa y colaborativa en el proyecto "Producción de Polvo de Limón". | • Diseño de recursos TIC <br> • Evaluación del uso de TIC <br> • Integración de estrategias colaborativas | • Recursos digitales preliminares <br> • Encuesta inicial sobre uso de TIC <br> • Informe preliminar de colaboración | • Recursos digitales finales <br> • Evaluación final del impacto de TIC <br> • Informe final de estrategias colaborativas |
                | Administrativa | Uso de Recursos | Diseñar un plan integral para optimizar el uso de recursos humanos y materiales en el proyecto, minimizando costos y maximizando eficiencia. | • Identificación de recursos críticos <br> • Diseño del plan de optimización <br> • Monitoreo de la implementación | • Registro inicial de recursos <br> • Borrador del plan <br> • Informe preliminar de monitoreo | • Registro final de recursos <br> • Plan definitivo optimizado <br> • Informe final de eficiencia |
                | Comunitaria | Comunicación Institucional | Difundir y mantener una comunicación institucional efectiva en el proyecto "Producción de Polvo de Limón", asegurando un intercambio claro y constante de información entre los diferentes miembros del equipo y las partes interesadas involucradas. | • Evaluación de los canales existentes <br> • Implementación de nuevas herramientas de comunicación <br> • Monitoreo del flujo de información | • Análisis inicial de los canales de comunicación <br> • Propuesta de herramientas <br> • Informe preliminar de monitoreo | • Evaluación final de los canales <br> • Implementación de herramientas efectivas <br> • Informe detallado del flujo de información |

                **Tabla de Competencias Comportamentales:**

                | Competencia | Contribución Individual | Criterios de Evaluación | Evidencias Primera Evaluación | Evidencias Segunda Evaluación |
                |-------------|------------------------|------------------------|-------------------------------|-------------------------------|
                | Liderazgo | Diseñar y ejecutar estrategias de liderazgo para inspirar y motivar a los equipos en el proyecto, fomentando un entorno inclusivo y colaborativo. | • Planificación de actividades de liderazgo <br> • Impacto en la cohesión del equipo <br> • Evaluación del entorno laboral | • Plan de liderazgo preliminar <br> • Encuestas iniciales sobre cohesión <br> • Informe de diagnóstico | • Plan final de liderazgo <br> • Encuestas finales de impacto <br> • Informe completo del entorno laboral |
                | Trabajo en Equipo | Implementar dinámicas de colaboración interdisciplinaria para lograr los objetivos del proyecto "Producción de Polvo de Limón" de manera eficiente y armónica. | • Diseño de dinámicas de colaboración <br> • Participación activa de los miembros <br> • Evaluación del cumplimiento de objetivos | • Documentación preliminar de dinámicas <br> • Registros iniciales de participación <br> • Informe preliminar de resultados | • Documentación final de dinámicas <br> • Registros finales de participación <br> • Informe completo de objetivos cumplidos |
                | Iniciativa | Diseñar y ejecutar propuestas innovadoras que contribuyan a la mejora continua del proyecto "Producción de Polvo de Limón". | • Número y calidad de propuestas <br> • Implementación de innovaciones <br> • Evaluación del impacto | • Registro inicial de propuestas <br> • Evaluación preliminar de viabilidad <br> • Informe inicial de impacto | • Registro final de propuestas ejecutadas <br> • Evaluación de resultados <br> • Informe detallado del impacto |

                6. **Consideraciones adicionales**:
                - Usar el Decreto Ley 1278 de 2002 como marco normativo.
                - Reflejar compromiso con la calidad educativa.
                - Documentar impacto en aprendizaje estudiantil.
                - Mostrar desarrollo profesional continuo.
                - Tener en cuenta el contexto de la IE pasado como texto base.

                Texto base (contexto de la IE):
                {text}"""
            
        elif annex_type == "Anexo 2":
            prompt = f"""You are a professional assistant helping to create a Performance Evaluation Document for educational professionals in Colombia, following the official Ministry of National Education guidelines. The Anexo 2 should be directly derived from the content of Anexo 5, maintaining a direct, one-to-one relationship between the documents. Each piece of evidence in Anexo 2 will directly correspond to a specific element or activity described in Anexo 5.

                Instructions for generating Anexo 2:

                1. **Structure**:
                - Follow the official format provided by the Ministry of National Education.
                - Use a table summarizing all evidences, including:
                    - Sequential number.
                    - Page/folio.
                    - Date of inclusion.
                    - Type of evidence (D: Documental; T: Testimonial).
                    - Name of the evidence.
                    - Competencies supported by the evidence.
                    - Signature fields.
                    - Detailed description of each evidence.

                2. **Alignment**:
                - Ensure each evidence relates directly to contributions, criteria, and competencies from Anexo 5.
                - Maintain consistent language and terminology between both documents.

                3. **Example of Evidence Table**:

                | No. | Folio | Date of Inclusion | Type of Evidence | Evidence Name | Supported Competencies | Signature | Description |
                |-----|-------|-------------------|------------------|---------------|-----------------------|-----------|-------------|
                | 1 | 06/06/2024 | D | Plan de lecciones | Dominio Curricular | - | Document detailing the lesson plan including specific objectives, proposed activities, and required resources. |
                | 2 | 06/06/2024 | D | Plan de difusión y comercialización | Planeación y Organización | - | Document designed by the teacher to commercialize the product obtained in the project, providing students opportunities to learn about marketing and business management. |

                4. **Final Considerations**:
                - Ensure evidence names are descriptive and align with Anexo 5.
                - Use realistic future dates (e.g., June 6, September 13, November 20).
                - Highlight educational practices and outcomes in the evidence descriptions.

                Base Text (Anexo 5 draft):
                {text}"""        

        logger.info(f"Enviando prompt a GPT-4 para generar {annex_type}")
        response = client.chat.completions.create(
            model="gpt-4o",  # Corregido el nombre del modelo
            messages=[
                {"role": "system", "content": f"""Eres un asistente especializado en la generación de documentos pedagógicos y administrativos, enfocado en la evaluación del desempeño docente en Colombia según el Decreto Ley 1278 de 2002. 
                                                Tu objetivo es producir borradores claros, precisos y consistentes en español, siguiendo estas directrices:
                                                1. Usa lenguaje técnico y profesional alineado con las normativas educativas.
                                                2. Asegúrate de estructurar los textos de acuerdo con las instrucciones provistas y los formatos oficiales.
                                                3. Mantén correspondencia estricta entre criterios, competencias y evidencias.
                                                4. Asegura que las tablas incluyan todas las columnas y datos especificados en los ejemplos.
                                                5. Los borradores deben alinearse con el Proyecto Educativo Institucional (PEI) y el contexto de la institución educativa.
                                                Proporciona respuestas detalladas y consistentes, asegurando la inclusión de todos los elementos solicitados. Evita omisiones y refuerza la claridad en las instrucciones para las tablas y los textos narrativos."""},
                {"role": "user", "content": prompt}
            ]
        )
        draft = response.choices[0].message.content
        logger.info(f"Borrador de {annex_type} generado exitosamente")
        return draft.strip()
    except Exception as e:
        logger.error(f"Error al generar el borrador de {annex_type}: {str(e)}", exc_info=True)
        return f"Error al generar el borrador de {annex_type}: {str(e)}"
