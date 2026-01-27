

# Proyecto de Práctica RAG con Ollama

Este proyecto es una práctica de la técnica **RAG (Retrieval Augmented Generation)** usando **Ollama** como motor de IA.  
El objetivo es combinar un modelo de lenguaje con una base de conocimiento propia para obtener respuestas más precisas y basadas en información real.

## ¿Qué es RAG?
RAG es una técnica que:
1. Busca información relevante en una base de datos o documentos.
2. Usa esa información como contexto.
3. Se la pasa al modelo de IA para generar una respuesta más exacta.

En vez de que la IA “invente”, primero **recupera datos reales** y luego responde.

## Tecnologías usadas
- **Ollama** – Para ejecutar modelos LLM localmente.
- **Python** – Lenguaje principal del proyecto.
- Documentos locales (PDF, TXT, etc.) como base de conocimiento.
-  Librerías típicas:
  - `langchain` o similar (si la usaste)
  - `faiss` / `chromadb` (si usaste vectores)
  - `sentence-transformers` (para embeddings)


