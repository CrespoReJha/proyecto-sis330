import React from 'react';

function CartTable({ products, total }) {
  const hasProducts = products.some(item => item.quantity > 0);

  return (
    <div className="w-full">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-50 to-slate-100 px-6 py-4 border-b border-slate-200">
          <h2 className="text-2xl font-bold text-slate-800 flex items-center">
            <span className="mr-3 text-3xl">🛍️</span>
            Contenido del Carrito
          </h2>
        </div>

        {/* Table Container */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gradient-to-r from-slate-100 to-slate-50 border-b border-slate-200">
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700 uppercase tracking-wider">
                  Producto
                </th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-slate-700 uppercase tracking-wider">
                  Cantidad
                </th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-slate-700 uppercase tracking-wider">
                  Precio Unit.
                </th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-slate-700 uppercase tracking-wider">
                  Subtotal
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {products.length > 0 ? (
                products.map((item, index) => (
                  <tr
                    key={item.product_name}
                    className={`transition-all duration-500 ease-in-out hover:bg-slate-50 ${
                      item.quantity > 0 
                        ? 'opacity-100 transform translate-x-0' 
                        : 'opacity-40 transform translate-x-1'
                    } ${index % 2 === 0 ? 'bg-white' : 'bg-slate-25'}`}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className={`w-3 h-3 rounded-full mr-3 ${
                          item.quantity > 0 ? 'bg-green-400' : 'bg-gray-300'
                        }`}></div>
                        <span className="font-medium text-slate-800">
                          {item.product_name}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                        item.quantity > 0 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-gray-100 text-gray-500'
                      }`}>
                        {item.quantity}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-medium text-slate-600">
                      ${item.unit_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className={`font-bold ${
                        item.quantity > 0 ? 'text-green-600' : 'text-gray-400'
                      }`}>
                        ${item.subtotal.toFixed(2)}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center justify-center space-y-3">
                      <div className="text-6xl opacity-20">🛒</div>
                      <p className="text-slate-500 text-lg font-medium">
                        No se han detectado productos
                      </p>
                      <p className="text-slate-400 text-sm">
                        Coloca productos frente a la cámara para comenzar
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Total Section */}
        {hasProducts && (
          <div className="bg-gradient-to-r from-slate-800 to-slate-700 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-white text-lg font-medium">Total a Pagar:</span>
                <div className="bg-white/20 px-3 py-1 rounded-full">
                  <span className="text-white text-sm font-medium">
                    {products.filter(item => item.quantity > 0).length} producto(s)
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-white">
                  ${total.toFixed(2)}
                </div>
                <div className="text-green-300 text-sm">
                  
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CartTable;