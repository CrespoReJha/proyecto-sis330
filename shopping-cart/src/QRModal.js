import React, { useState, useEffect } from 'react';
import { QRCodeCanvas } from 'qrcode.react';

function QRModal({ isOpen, onClose, total, products, isPaid, setIsPaid }) {
  const [fixedPaymentInfo, setFixedPaymentInfo] = useState(null);

  // Generar información de pago fija solo cuando se abre el modal
  useEffect(() => {
    if (isOpen && !fixedPaymentInfo) {
      const paymentInfo = {
        total: total.toFixed(2),
        products: products.map(item => ({
          name: item.product_name,
          quantity: item.quantity,
          subtotal: item.subtotal.toFixed(2),
        })),
        timestamp: new Date().toISOString(),
        invoiceId: `PAY-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      };
      setFixedPaymentInfo(paymentInfo);
    }
  }, [isOpen, total, products, fixedPaymentInfo]);

  // Limpiar información fija cuando se cierra el modal
  useEffect(() => {
    if (!isOpen && !isPaid) {
      setFixedPaymentInfo(null);
    }
  }, [isOpen, isPaid]);

  if (!isOpen && !isPaid) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-60 p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden">
        {isPaid ? (
          // Success State
          <div className="text-center p-8">
            {/* Success Animation */}
            <div className="mb-6">
              <div className="mx-auto w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mb-4 animate-bounce">
                <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-4xl">✓</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="w-32 h-1 bg-green-200 rounded-full mx-auto overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full animate-pulse"></div>
                </div>
              </div>
            </div>

            {/* Success Message */}
            <h2 className="text-3xl font-bold mb-2 bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
              ¡Pago Exitoso!
            </h2>
            <p className="text-slate-600 mb-6 text-lg">
              Gracias por tu compra
            </p>

            {/* Purchase Summary */}
            <div className="bg-green-50 border border-green-200 rounded-2xl p-6 mb-6">
              <div className="flex items-center justify-center space-x-4 mb-4">
                <span className="text-2xl">🛍️</span>
                <div>
                  <p className="text-green-800 font-semibold">Total Pagado</p>
                  <p className="text-2xl font-bold text-green-600">${total.toFixed(2)}</p>
                </div>
              </div>
              <div className="text-center">
                <p className="text-green-700 font-medium">
                  Por favor, retira los productos del carrito
                </p>
                <p className="text-green-600 text-sm mt-1">
                  {products.length} producto(s) comprado(s)
                </p>
              </div>
            </div>

            {/* Decorative elements */}
            <div className="flex justify-center space-x-2 mb-4">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-ping"></div>
              <div className="w-2 h-2 bg-green-400 rounded-full animate-ping" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-2 h-2 bg-green-400 rounded-full animate-ping" style={{ animationDelay: '0.4s' }}></div>
            </div>
          </div>
        ) : (
          // Payment State
          <>
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-6 text-white">
              <h2 className="text-2xl font-bold text-center flex items-center justify-center">
                <span className="mr-2">📱</span>
                Escanea para Pagar
              </h2>
            </div>

            {/* QR Code Section */}
            <div className="p-8 text-center">
              {/* QR Code Container */}
              <div className="relative mb-6">
                <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-3xl shadow-inner">
                  <div className="bg-white p-4 rounded-2xl shadow-lg inline-block">
                    {fixedPaymentInfo ? (
                      <QRCodeCanvas
                        value={JSON.stringify(fixedPaymentInfo)}
                        size={200}
                        level="H"
                        includeMargin={true}
                        className="rounded-lg"
                      />
                    ) : (
                      <div className="w-[200px] h-[200px] flex items-center justify-center bg-slate-100 rounded-lg">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Animated scanning lines */}
                <div className="absolute inset-0 pointer-events-none">
                  <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-blue-400 opacity-60 animate-pulse"></div>
                </div>
              </div>

              {/* Payment Info */}
              <div className="bg-slate-50 rounded-2xl p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-slate-600 font-medium">Total a Pagar:</span>
                  <span className="text-3xl font-bold text-slate-800">
                    ${fixedPaymentInfo?.total || total.toFixed(2)}
                  </span>
                </div>
                <div className="text-sm text-slate-500">
                  {fixedPaymentInfo?.products?.length || products.length} producto(s) • {fixedPaymentInfo ? new Date(fixedPaymentInfo.timestamp).toLocaleString() : new Date().toLocaleString()}
                </div>
                {fixedPaymentInfo?.invoiceId && (
                  <div className="text-xs text-slate-400 mt-2 font-mono">
                    ID: {fixedPaymentInfo.invoiceId}
                  </div>
                )}
              </div>

              {/* Instructions */}
              <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 mb-6">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 text-lg">💡</span>
                  </div>
                  <div className="text-left">
                    <p className="text-blue-800 font-medium text-sm">
                      Instrucciones de Pago:
                    </p>
                    <ol className="text-blue-700 text-xs mt-1 space-y-1">
                      <li>1. Abre tu app de pagos móviles</li>
                      <li>2. Escanea el código QR</li>
                      <li>3. Confirma el pago</li>
                    </ol>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                <button
                  onClick={() => setIsPaid(true)}
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold py-4 px-6 rounded-2xl transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl"
                >
                  ✓ Confirmar Pago Realizado
                </button>
                
                <button
                  onClick={onClose}
                  className="w-full text-slate-500 hover:text-slate-700 font-medium py-2 transition-colors duration-200"
                >
                  ← Volver
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default QRModal;