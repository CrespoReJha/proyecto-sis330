# Proyecto SIS330 - Carrito Inteligente con Detección de Productos

## Estudiante
* **Nombre:** Jhamil Crespo Rejas
* **Carrera:** Ingeniería en Ciencias de la Computación 

## Descripción del Proyecto

El proyecto SIS330 es un sistema de carrito inteligente que utiliza visión por computadora para detectar y rastrear productos en tiempo real mediante una cámara web. Este sistema está diseñado para identificar productos, gestionar su estado (visible, ocluido, detectando, etc.), y calcular un total de compra que puede ser procesado para generar una factura. Incluye un backend basado en Python con Flask y un frontend basado en React que proporciona una interfaz de usuario interactiva.

## Cómo Funciona

El sistema utiliza el modelo YOLO (You Only Look Once) para la detección de objetos, optimizado con un modelo entrenado (`best.pt`). La lógica principal, implementada en la clase `LayeredShoppingCart`, gestiona el seguimiento de productos, incluyendo la detección de oclusiones y la asignación de capas de profundidad. Los frames de video se procesan desde la cámara web, y los resultados se envían al frontend a través de WebSocket. El frontend muestra los productos detectados, su cantidad, y el total, permitiendo al usuario proceder al pago mediante un código QR.

### Características Principales

- Detección y seguimiento de múltiples productos con manejo de oclusiones.
- Asignación de capas de profundidad para productos apilados.
- Interfaz web interactiva con actualización en tiempo real.
- Generación de facturas y procesamiento de pagos simulados.
- Optimización del procesamiento de frames para mejorar el rendimiento.

## Instalación

### Requisitos Previos

- Python 3.8+
- Node.js y npm
- Cámara web

### Instalación del Backend

1. Clona el repositorio o descarga los archivos.
2. Instala las dependencias ejecutando:

   ```
   pip install -r requirements.txt
   ```
3. Asegúrate de que el archivo `best.pt` esté en la ruta especificada (`/home/jhamilcr/Documents/proyecto-sis330/detection-model/train-files/best.pt`) o actualiza `MODEL_PATH` en `app.py`.
4. Ejecuta el servidor:

   ```
   cd app
   python app.py
   ```

   El servidor estará disponible en `http://0.0.0.0:5000`.

### Instalación del Frontend

1. Navega al directorio `shoping-cart`:

   ```
   cd shoping-cart
   ```
2. Instala las dependencias:

   ```
   npm install
   ```
3. Inicia la aplicación:

   ```
   npm run start
   ```

   La interfaz estará disponible en `http://localhost:3000`.

## Descripción de los Archivos

### Directorio `app`

- `app.py`: Script principal del backend. Configura un servidor Flask con SocketIO para manejar la detección de productos en tiempo real. Utiliza OpenCV, YOLO, y SQLite para procesar video, detectar objetos, y almacenar información de productos.
- `pruebas-deteccion.ipynb`: Notebook Jupyter con pruebas de detección y lógica de seguimiento de productos, incluyendo visualización de capas y oclusiones.
- `best.pt`: Modelo entrenado de YOLO para la detección de productos específicos.

### Directorio `detection-model/train-files`

- Contiene archivos de entrenamiento del modelo, incluyendo el archivo `best.pt`.

### Directorio `shoping-cart`

- `App.js`: Componente principal de React que integra la detección de video, la tabla de productos, y el botón de pago.
- `CartTable.js`: Componente que muestra la tabla de productos detectados con detalles como cantidad y subtotal.
- `InvoiceModal.js`: Modal para mostrar la factura y procesar el pago mediante un código QR.
- `QRModal.js`: Modal que genera un código QR con información de pago.
- `WebcamFeed.js`: Componente que captura video de la cámara web y envía frames al backend.
- `App.css`: Estilos globales para la interfaz.
- `package.json`: Configuración de dependencias y scripts de npm.

### Otros Archivos

- `requirements.txt`: Lista de dependencias de Python necesarias para el backend.
- `video_demostracion`: Contiene un video que demuestra el funcionamiento del software.
- `.gitignore`: Archivos y carpetas a ignorar en el control de versiones.

## Arquitectura del Software

![Diagrama de Arquitectura del Software](/images/arquitectura.png)


## Notas Adicionales

- Asegúrate de otorgar permisos de cámara al navegador al usar el frontend.
- El video de demostración en el directorio `video_demostracion` muestra el sistema en acción.

## Contribuciones

Cualquier mejora o sugerencia es bienvenida. Por favor, abre un issue o envía un pull request.