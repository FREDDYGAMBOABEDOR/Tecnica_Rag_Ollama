# import logging
# import sys
# import os
# from logging.handlers import RotatingFileHandler

# def setup_logger():
#     """Configura el sistema de logging"""
#     # Crear directorio de logs si no existe
#     os.makedirs("logs", exist_ok=True)
    
#     logger = logging.getLogger()
#     logger.setLevel(logging.INFO)
    
#     # Formato de logs
#     formatter = logging.Formatter(
#         "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#         datefmt="%Y-%m-%d %H:%M:%S"
#     )
    
#     # Handler para consola
#     console_handler = logging.StreamHandler(sys.stdout)
#     console_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)
    
#     # Handler para archivo
#     file_handler = RotatingFileHandler(
#         "logs/app.log",
#         maxBytes=10485760,  # 10MB
#         backupCount=5
#     )
#     file_handler.setFormatter(formatter)
#     logger.addHandler(file_handler)
    
#     return logger