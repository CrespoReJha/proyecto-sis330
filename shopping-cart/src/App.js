import React, { useState, useEffect, useRef, useCallback } from 'react';
import io from 'socket.io-client';
import WebcamFeed from './WebcamFeed';
import CartTable from './CartTable';
import InvoiceModal from './InvoiceModal';
import './App.css';

function App() {
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [isInvoiceOpen, setIsInvoiceOpen] = useState(false);
  const [isPaid, setIsPaid] = useState(false);
  const [invoiceProducts, setInvoiceProducts] = useState([]);
  const [invoiceTotal, setInvoiceTotal] = useState(0);
  const lastProductsRef = useRef({});

  const socketRef = useRef(null);

  useEffect(() => {
    const backendUrl = 'http://localhost:5000';
    console.log(`Connecting to backend: ${backendUrl}`);

    socketRef.current = io(backendUrl, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    socketRef.current.on('connect', () => {
      console.log('WebSocket connected');
      setConnectionStatus('Connected');
    });

    socketRef.current.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error.message, error);
      setConnectionStatus('Connection failed. Retrying...');
    });

    socketRef.current.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setConnectionStatus('Disconnected. Reconnecting...');
    });

    socketRef.current.on('reconnect', (attempt) => {
      console.log(`WebSocket reconnected after ${attempt} attempts`);
      setConnectionStatus('Connected');
    });

    socketRef.current.on('error', (data) => {
      console.error('Server error:', data.message);
      setConnectionStatus(`Error: ${data.message}`);
    });

    socketRef.current.on('update', (data) => {
      console.log('Received update:', data);
      const newProducts = data.products || [];
      const newTotal = data.total || 0;

      const updatedProducts = {};
      newProducts.forEach((item) => {
        updatedProducts[item.product_name] = { ...item, lastSeen: Date.now() };
      });

      Object.entries(lastProductsRef.current).forEach(([name, item]) => {
        if (!updatedProducts[name] && Date.now() - item.lastSeen < 5000) {
          updatedProducts[name] = { ...item, quantity: 0, subtotal: 0 };
        }
      });

      setProducts(Object.values(updatedProducts).sort((a, b) =>
        a.product_name.localeCompare(b.product_name)
      ));
      setTotal(newTotal);
      lastProductsRef.current = updatedProducts;
    });

    return () => {
      socketRef.current.disconnect();
      console.log('WebSocket disconnected on cleanup');
    };
  }, []);

  useEffect(() => {
    if (isPaid && products.length === 0) {
      setIsInvoiceOpen(false);
      setIsPaid(false);
    }
  }, [products, isPaid]);

  const sendFrame = useCallback((imageData) => {
    if (socketRef.current && socketRef.current.connected) {
      socketRef.current.emit('frame', { image: imageData });
    } else {
      console.warn('Cannot send frame: WebSocket is not connected');
    }
  }, []);

  const handleOpenInvoice = () => {
    if (products.length > 0 && total > 0) {
      setInvoiceProducts([...products.filter(item => item.quantity > 0)]);
      setInvoiceTotal(total);
      setIsInvoiceOpen(true);
    } else {
      alert('No products in the cart to pay for.');
    }
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'Connected':
        return 'text-emerald-500';
      case 'Connecting...':
        return 'text-yellow-500';
      default:
        return 'text-red-500';
    }
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'Connected':
        return '●';
      case 'Connecting...':
        return '◐';
      default:
        return '●';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white shadow-lg border-b border-slate-200">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              🛒 Carrito Inteligente
            </h1>
            <div className="flex items-center space-x-2">
              <span className={`text-lg ${getStatusColor()}`}>
                {getStatusIcon()}
              </span>
              <span className={`text-sm font-medium ${getStatusColor()}`}>
                {connectionStatus}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <WebcamFeed sendFrame={sendFrame} />
          <CartTable products={products} total={total} />
        </div>
        
        {/* Payment Button */}
        <div className="mt-8 flex justify-center">
          <button
            onClick={handleOpenInvoice}
            disabled={products.length === 0 || total === 0}
            className="group relative bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-2xl font-semibold text-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-lg"
          >
            <span className="flex items-center space-x-2">
              <span>💳</span>
              <span>Proceder al Pago</span>
              <span className="text-xl font-bold">
                ${total.toFixed(2)}
              </span>
            </span>
            <div className="absolute inset-0 bg-white opacity-20 rounded-2xl transform scale-0 group-hover:scale-100 transition-transform duration-300"></div>
          </button>
        </div>
      </div>

      <InvoiceModal
        isOpen={isInvoiceOpen}
        onClose={() => setIsInvoiceOpen(false)}
        products={invoiceProducts}
        total={invoiceTotal}
        isPaid={isPaid}
        setIsPaid={setIsPaid}
      />
    </div>
  );
}

export default App;