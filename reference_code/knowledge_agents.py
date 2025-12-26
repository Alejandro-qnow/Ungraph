"""
Este módulo sirve como interfaz entre diferentes propuestas para crear grafos de conocimiento, 
validación de ontologías y procedimientos relacionados con la ingeniería de conocimiento.

Classes:
    KnowledgeGraphCreatorAgent: Agente principal para la creación y gestión de grafos de conocimiento.


El proceso base debe ser no determinista visto desdel el punto de vista de la instrucción  de extraer entidades para modelar un conocimiento determinado. 








"""

# Importaciones estándar
import os
import logging
import json
import re
from typing import Optional, List, Dict, Any, Generator, Tuple

# Importaciones de terceros
import toml
import spacy
import pandas as pd
from langdetect import detect
from pydantic import BaseModel

# Importaciones de LangChain
# from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship

# Importaciones locales
#from utilities.environ_tools import load_environment_variables

class KnowledgeGraphCreatorAgent:
    """
    Agente para crear y gestionar grafos de conocimiento usando modelos de lenguaje.
    
    Esta clase proporciona funcionalidades para:
    - Crear grafos de conocimiento a partir de texto
    - Procesar documentos en lotes
    - Detectar esquemas de conocimiento
    - Resolver entidades y sus contextos
    - Guardar y cargar esquemas en formato TOML
    
    Attributes:
        llm: Modelo de lenguaje configurado para el procesamiento
        language (str): Código ISO del idioma de trabajo
        prompt (PromptTemplate): Plantilla para las instrucciones al modelo
        transformer (LLMGraphTransformer): Transformador para crear grafos
        logger (logging.Logger): Logger para registro de eventos
    """

    def __init__(self, 
                 api_key: str, 
                 model: str = "llama-3.1-70b-versatile",
                 language: str = "spa",
                 model_config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el agente creador de grafos de conocimiento.
        
        Args:
            api_key (str): API key para el servicio Groq
            model (str): Nombre del modelo a utilizar
            language (str): Código ISO del idioma (e.g., 'spa', 'eng')
            model_config (Optional[Dict[str, Any]]): Configuración adicional del modelo
        
        Raises:
            ValueError: Si el api_key está vacío o el idioma no es válido
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key no puede estar vacío")
            
        if not self._is_valid_language_code(language):
            raise ValueError(f"Código de idioma '{language}' no válido")
            
        # Configuración base del modelo
        default_config = {
            "temperature": 0,
            "api_key": api_key,
            "model": model
        }
        
        # Combinar con configuración adicional si existe
        if model_config:
            default_config.update(model_config)
            
        self.llm = ChatGroq(**default_config)
        self.language = language.lower()
        self.prompt = self._create_prompt()
        self.transformer = None
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
    @staticmethod
    def _is_valid_language_code(code: str) -> bool:
        """Valida el código de idioma (implementación básica)"""
        valid_codes = {'spa', 'eng', 'fra', 'por'}  # Expandir según necesidad
        return code.lower() in valid_codes
    
    # Crear el prompt para el grafo de conocimiento y los procesos.
    # Esto peude ser algo que reciba la clase para crear el objeto.
    def _create_prompt(self) -> PromptTemplate:
        # Aquí encontrar la forma de cargar esto desde un archivo que facilite la gestión de los prompts.
        return PromptTemplate.from_template(
            """
            "# Instrucciones del Grafo de Conocimiento para Lama3.1\n"
            "## 1. Descripción General\n"
            "Eres un algoritmo de primer nivel diseñado para extraer información en formatos estructurados "
            "para construir un grafo de conocimiento.\n"
            "Intenta capturar tanta información del texto como sea posible sin "
            "sacrificar precisión. No añadas ninguna información que no esté explícitamente "
            "mencionada en el texto.\n"
            "- **Nodos** representan entidades y conceptos.\n"
            "- El objetivo es lograr simplicidad y claridad en el grafo de conocimiento, haciéndolo\n"
            "accesible para una amplia audiencia.\n"
            "## 2. Etiquetado de Nodos\n"
            "- **Consistencia**: Asegúrate de usar los tipos disponibles para las etiquetas de los nodos.\n"
            "Asegúrate de usar tipos básicos o elementales para las etiquetas de los nodos.\n"
            "- Por ejemplo, cuando identifiques una entidad que representa a una persona, "
            "siempre etiquétala como **'persona'**. Evita usar términos más específicos "
            "como 'matemático' o 'científico'."
            "- **IDs de Nodos**: Nunca utilices enteros como IDs de nodos. Los IDs de nodos deben ser "
            "nombres o identificadores legibles por humanos que se encuentren en el texto.\n"
            "- **Relaciones** representan conexiones entre entidades o conceptos.\n"
            "Asegúrate de la consistencia y generalidad en los tipos de relaciones al construir "
            "grafos de conocimiento. En lugar de usar tipos específicos y momentáneos "
            "como 'SE_CONVIRTIÓ_EN_PROFESOR', usa tipos de relaciones más generales y atemporales "
            "como 'PROFESOR'. ¡Asegúrate de usar tipos de relaciones generales y atemporales!\n"
            "## 3. Resolución de Correferencias\n"
            "- **Mantén la Consistencia de Entidades**: Al extraer entidades, es vital "
            "asegurar la consistencia.\n"
            'Si una entidad, como "John Doe", se menciona múltiples veces en el texto '
            'pero se refiere con diferentes nombres o pronombres (por ejemplo, "Joe", "él"),'
            "siempre usa el identificador más completo para esa entidad a lo largo del "
            'grafo de conocimiento. En este ejemplo, usa "John Doe" como el ID de la entidad.\n'
            "Recuerda, el grafo de conocimiento debe ser coherente y fácilmente comprensible, "
            "por lo que mantener la consistencia en las referencias de entidades es crucial.\n"

            El esquema debe ser escalable, coherente, y permitir inferencias lógicas 
            entre las entidades. Texto:
            
            <{text}>
            """
        )
    
    # Configurar el transformador con los nodos y relaciones permitidos.
    def setup_transformer(self, nodes: List[str], relations: List[str]) -> None:
        """
        Configura el transformador con los nodos y relaciones permitidos.
        
        Args:
            nodes (List[str]): Lista de tipos de nodos permitidos
            relations (List[str]): Lista de tipos de relaciones permitidas
        """
        # A esto le falta más parámetros para que sea más robusto.
        # Por ejemplo, el prompt que se le da al modelo para que haga el parsing del grafo.
        # También, se puede agregar un esquema de nodos y relaciones que se le pueda dar al modelo.
        # Se puede agregar más de los argumentos de la función para que sea más flexible.
        # ¿Cómo funciona el graph transformer con diferentes prompts?
        self.transformer = LLMGraphTransformer(
            llm=self.llm,
            allowed_nodes=nodes,
            allowed_relationships=relations
        )
        return self.transformer
    
    # Procesar un documento y retornar el grafo resultante.
    # 1 Documento.
    # Corregir la firma del método process_text
    def process_text(self, document: Document) -> Any:  # Eliminado parámetro transformer innecesario
        try:
            print("========== Graph Document created ==========")
            graph_documents = self.transformer.process_response(document)
            
            print(f"NODES: {graph_documents.nodes}")
            print(f"RELATIONSHIPS: {graph_documents.relationships}")
            return graph_documents
        except KeyError as e:
            print(f"KeyError: {e}")
        except TypeError as e:
            print(f"TypeError: {e}")
        return None  # Añadido: retornar None en caso de error


    def batch_process(self, documents: List[Document], batch_size: int = 5) -> Generator[GraphDocument, None, None]:
        """
        Procesa documentos en lotes y genera GraphDocuments.
        
        Args:
            documents (List[Document]): Lista de documentos a procesar
            batch_size (int): Tamaño del lote para procesamiento
            
        Yields:
            Generator[GraphDocument, None, None]: Generador de GraphDocuments procesados
        """
        def process_batch(batch: List[Document]) -> List[GraphDocument]:
            graph_documents = []
            for doc in batch:
                try:
                    # Procesar el documento usando el transformer
                    processed_doc = self.process_text(doc)
                    if processed_doc:
                        # Validar que el resultado sea un GraphDocument válido
                        if (hasattr(processed_doc, 'nodes') and 
                            hasattr(processed_doc, 'relationships') and 
                            hasattr(processed_doc, 'source')):
                            graph_documents.append(processed_doc)
                        else:
                            print(f"Warning: Invalid GraphDocument structure for document {doc.metadata.get('chunk_id', 'unknown')}")
                except Exception as e:
                    print(f"Error processing document {doc.metadata.get('chunk_id', 'unknown')}: {str(e)}")
                    continue
            
            return graph_documents

        # Procesar documentos en lotes 
        # 
        current_batch = []
        for idx, doc in enumerate(documents):
            current_batch.append(doc)
            
            if len(current_batch) >= batch_size:
                for graph_doc in process_batch(current_batch):
                    yield graph_doc
                current_batch = []
                print(f"Processed batch {idx // batch_size + 1}")
        
        # Procesar el último lote si existe
        if current_batch:
            for graph_doc in process_batch(current_batch):
                yield graph_doc
            print("Processed final batch")

    # Este .TOML se puede guardar dentro de la carpeta de metadata que se tiene del document data.
    def save_schema_to_toml(self, schema: Dict, file_path: str = "knowledge_schema.toml"):
        """Guarda el esquema en formato TOML"""
        toml_data = {
            "schema": {
                "nodes": schema["nodes"],
                "relations": schema["relations"]
            }
        }
        with open(file_path, "w") as f:
            toml.dump(toml_data, f)


    # Queryar el grafo de conocimiento.
    def query_graph(self, query: str) -> Optional[Dict[str, Any]]:
        pass

    # Validar el grafo de conocimiento.
    def validate_graph(self, graph: Dict[str, Any]) -> bool:
        pass    

    # Resolver entidades.
    def entity_resolution(self, query: str) -> Optional[Dict[str, Any]]:
        # Sería preguntar por __Entity__ en el grafo.
        # Considerar el Score de una entidad, que podemos gaurdar en el graphdocument.
        # Sería las técncias tradicionales de resolver entidades.
        # KNN, SVM, QSVM.
        # QLambert
        # QKNN
        # Al ser palabras por Similitud de espacio vectorial.
        pass

    # entity_context_resolution
    def entity_context_resolution(self, query: str) -> Optional[Dict[str, Any]]:
        # Resolver entidades según el contexto.
        # Usando al LLM para resolver entidades según el contexto de la entidad.
        pass

    # Guardar el grafo de conocimiento en un archivo CSV
    def save_graph_document(self, graph: Dict[str, Any]) -> None:
        # Guardar el grafo de conocimiento en un archivo CSV para serializarlo
        # como un grafo de sujeto, verbo, objeto.
        # La idea es valerse del dataframe para aplicar agloritmos tradicionales de entity resolution.
        # Con esto tener un Score de confianza en la resolución de entidades.
        pass


    # Cargamos modelo de spacy para detectar el idioma.
    def load_spacy_model(self, lang: str) -> spacy.language.Language:
        """Carga el modelo de spaCy apropiado según el idioma"""
        lang_models = {
            'es': 'es_core_news_lg',
            'en': 'en_core_web_lg',
        }
        
        model_name = lang_models.get(lang, 'en_core_web_lg')
        try:
            return spacy.load(model_name)
        except OSError:
            spacy.cli.download(model_name)
            return spacy.load(model_name)
        
    # Generar esquema con LLM
    def generate_schema_with_llm(self, text: str, entities: Dict, llm) -> Dict:
        """Genera el esquema usando el modelo de lenguaje"""
        prompt = PromptTemplate.from_template("""
        Analiza el siguiente texto y las entidades detectadas para generar un esquema de grafo de conocimiento.
        
        Texto: {text}
        
        Entidades detectadas: {entities}
        
        Genera una lista de tipos de nodos y relaciones posibles. Responde SOLO con un diccionario JSON válido que contenga:
        {{"nodes": ["TIPO_NODO_1", "TIPO_NODO_2"], "relations": ["RELACION_1", "RELACION_2"]}}
        """)
        
        # Get response from LLM
        response = llm.invoke(prompt.format(text=text, entities=entities))
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        try:
            import re
            import json
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                schema = json.loads(json_match.group())
                if "nodes" in schema and "relations" in schema:
                    return schema
        except:
            pass
        
        # Return default schema if parsing fails
        return {
            "nodes": ["Entity", "Document"],
            "relations": ["RELATED_TO"]
        }
    
    # Detector de esquemas:
    def knowledge_schema_detector(self, text: str, llm) -> Tuple[List[str], List[str]]:
        """
        Detecta y genera un esquema de conocimiento basado en el texto proporcionado.
        
        Args:
            text: Texto a analizar
            llm: Modelo de lenguaje a utilizar
        
        Returns:
            Tuple[List[str], List[str]]: Lista de nodos y relaciones permitidas
        """
        # 1. Detectar idioma
        lang = detect(text)
        
        # 2. Cargar modelo spaCy apropiado
        nlp = self.load_spacy_model(lang)
        
        # 3. Extraer entidades con spaCy
        doc = nlp(text)
        entities = {ent.label_: ent.text for ent in doc.ents}
        
        # 4. Generar esquema con LLM
        schema = self.generate_schema_with_llm(text, entities, llm)
      
        return schema['nodes'], schema['relations']