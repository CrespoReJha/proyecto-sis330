import React, { useEffect, useRef, memo, useState } from 'react';

function WebcamFeed({ sendFrame }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let interval;

    const startWebcam = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        if (!streamRef.current) {
          const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
              width: { ideal: 1280 },
              height: { ideal: 720 },
              facingMode: 'environment'
            } 
          });
          streamRef.current = stream;
          
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.onloadedmetadata = () => {
              videoRef.current.play()
                .then(() => setIsLoading(false))
                .catch((err) => {
                  console.error('Error playing video:', err);
                  setError('Error al reproducir el video');
                  setIsLoading(false);
                });
            };
          }
        }
      } catch (err) {
        console.error('Error accessing webcam:', err);
        setError('No se pudo acceder a la cámara');
        setIsLoading(false);
      }
    };

    startWebcam();

    interval = setInterval(() => {
      if (videoRef.current && canvasRef.current && videoRef.current.readyState === 4) {
        const canvas = canvasRef.current;
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        canvas.getContext('2d').drawImage(videoRef.current, 0, 0);
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        sendFrame(imageData);
      }
    }, 50);

    return () => {
      clearInterval(interval);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, [sendFrame]);

  return (
    <div className="w-full">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-50 to-slate-100 px-6 py-4 border-b border-slate-200">
          <h2 className="text-2xl font-bold text-slate-800 flex items-center">
            <span className="mr-3 text-3xl"></span>
            Detección de Productos
          </h2>
        </div>

        {/* Video Container */}
        <div className="relative">
          {isLoading && (
            <div className="absolute inset-0 bg-slate-100 flex items-center justify-center z-10">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                <p className="text-slate-600 font-medium">Iniciando cámara...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 bg-red-50 flex items-center justify-center z-10">
              <div className="text-center p-6">
                <div className="text-6xl mb-4">📷</div>
                <p className="text-red-600 font-medium mb-2">{error}</p>
                <p className="text-red-500 text-sm">
                  Verifica que hayas dado permisos de cámara
                </p>
              </div>
            </div>
          )}

          <div className="relative aspect-video bg-slate-900">
            <video 
              ref={videoRef} 
              className="w-full h-full object-cover"
              autoPlay 
              muted
              playsInline
            />
            
            {/* Overlay for scanning effect */}
            <div className="absolute inset-0 pointer-events-none">
              {/* Scanning line animation */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-400 to-transparent opacity-70 animate-pulse"></div>
              
              {/* Corner indicators */}
              <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-white opacity-60"></div>
              <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-white opacity-60"></div>
              <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-white opacity-60"></div>
              <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-white opacity-60"></div>
              
              {/* Status indicator */}
              <div className="absolute top-4 left-1/2 transform -translate-x-1/2">
                <div className="bg-black/50 backdrop-blur-sm text-white px-3 py-1 rounded-full text-sm font-medium flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span>Escaneando productos...</span>
                </div>
              </div>
            </div>
          </div>

          {/* Instructions */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-4">
            <div className="flex items-center space-x-3 text-sm">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-bold">💡</span>
                </div>
              </div>
              <div>
                <p className="text-slate-700 font-medium">
                  Coloca los productos claramente frente a la cámara
                </p>
                <p className="text-slate-500 text-xs">
                  Los productos se detectarán automáticamente y se agregarán al carrito
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}

export default memo(WebcamFeed);