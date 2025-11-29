from pipeline.classifier_gemini import classify_event_visual
import google.generativeai as genai
import os
import sys

# ----------------------------------------------------
# Configuración de API Gemini
# ----------------------------------------------------

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: Falta GEMINI_API_KEY en variables de entorno.")
    sys.exit(1)

# Configuración básica (usa modelo compatible por defecto).
genai.configure(api_key=api_key)

# ----------------------------------------------------
# Imágenes de prueba
# Crea la carpeta test_images/ y coloca tus imágenes dentro.
# ----------------------------------------------------

test_images = [
    "test_images/evento_test_1.JPG",
    "test_images/evento_test_2.JPG"
]

# Validar existencia de archivos
missing = [img for img in test_images if not os.path.exists(img)]
if missing:
    print("ERROR: Las siguientes imágenes no existen:", missing)
    sys.exit(1)

# ----------------------------------------------------
# Ejecutar clasificación visual
# ----------------------------------------------------

print("Analizando imágenes con Gemini Vision...")
result = classify_event_visual(test_images, model="gemini-2.0-flash")

print("\n--- RESULTADO ---")
print(result)
print("-----------------\n")
