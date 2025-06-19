import React, { useState } from 'react';
import QRModal from './QRModal';

function InvoiceModal({ isOpen, onClose, products, total, isPaid, setIsPaid }) {
  const [isQRModalOpen, setIsQRModalOpen] = useState(false);

  if (!isOpen) return null;

  const currentDate = new Date();
  const invoiceNumber = `INV-${currentDate.getFullYear()}${String(currentDate.getMonth() + 1).padStart(2, '0')}${String(currentDate.getDate()).padStart(2, '0')}-${String(currentDate.getHours()).padStart(2, '0')}${String(currentDate.getMinutes()).padStart(2, '0')}`;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold">Factura de Compra</h2>
              <p className="text-blue-100 mt-1">#{invoiceNumber}</p>
            </div>
            <div className="text-right">
              <p className="text-blue-100 text-sm">Fecha</p>
              <p className="font-semibold">{currentDate.toLocaleDateString()}</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-8">
          {/* Company Info */}
          <div className="mb-8 p-6 bg-slate-50 rounded-2xl">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white text-2xl">
                🛒
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-800">Smart Shopping Cart</h3>
                <p className="text-slate-600">Sistema de Compras Inteligente</p>
              </div>
            </div>
          </div>

          {/* Products Table */}
          <div className="mb-8 overflow-hidden rounded-2xl border border-slate-200">
            <table className="w-full">
              <thead>
                <tr className="bg-gradient-to-r from-slate-100 to-slate-50">
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 uppercase tracking-wider">
                    Producto
                  </th>
                  <th className="px-4 py-4 text-center text-sm font-semibold text-slate-700 uppercase tracking-wider">
                    Cant.
                  </th>
                  <th className="px-4 py-4 text-right text-sm font-semibold text-slate-700 uppercase tracking-wider">
                    Precio
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-slate-700 uppercase tracking-wider">
                    Subtotal
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {products.map((item, index) => (
                  <tr key={item.product_name} className={index % 2 === 0 ? 'bg-white' : 'bg-slate-25'}>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
                        <span className="font-medium text-slate-800">{item.product_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <span className="inline-flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-800 rounded-full text-sm font-bold">
                        {item.quantity}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-right text-slate-600 font-medium">
                      ${item.unit_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-right font-bold text-green-600">
                      ${item.subtotal.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Total Section */}
          <div className="bg-gradient-to-r from-slate-800 to-slate-700 rounded-2xl p-6 mb-8">
            <div className="flex items-center justify-between text-white">
              <div>
                <p className="text-slate-300 text-sm">Total de productos</p>
                <p className="text-xl font-semibold">{products.length} artículo(s)</p>
              </div>
              <div className="text-right">
                <p className="text-slate-300 text-sm">Total a Pagar</p>
                <p className="text-4xl font-bold">${total.toFixed(2)}</p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-4">
            <button
              onClick={onClose}
              className="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold py-4 px-6 rounded-2xl transition-all duration-300 transform hover:scale-105"
            >
              ← Cancelar
            </button>
            <button
              onClick={() => setIsQRModalOpen(true)}
              className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold py-4 px-6 rounded-2xl transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl"
            >
              Continuar al Pago →
            </button>
          </div>
        </div>
      </div>
      
      <QRModal
        isOpen={isQRModalOpen}
        onClose={() => setIsQRModalOpen(false)}
        total={total}
        products={products}
        isPaid={isPaid}
        setIsPaid={setIsPaid}
      />
    </div>
  );
}

export default InvoiceModal;