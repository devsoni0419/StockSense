import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

const SocketContext = createContext();

export const SocketProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/dashboard/`;

    const connectWebSocket = () => {
      try {
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
          console.log('⚡ Connected to StockSense Real-Time WebSocket');
          setIsConnected(true);
        };

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLastMessage(data);

            if (data.message) {
              setToastMessage(data.message);
              setTimeout(() => setToastMessage(null), 5000);
            }
          } catch (e) {
            console.error('Error parsing WS message:', e);
          }
        };

        socket.onclose = () => {
          console.log('Disconnected from StockSense WebSocket, attempting reconnect...');
          setIsConnected(false);
          setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = (err) => {
          console.warn('WebSocket error:', err);
          socket.close();
        };

        socketRef.current = socket;
      } catch (err) {
        console.error('Failed to initiate WebSocket:', err);
      }
    };

    connectWebSocket();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  return (
    <SocketContext.Provider value={{ isConnected, lastMessage, toastMessage, setToastMessage }}>
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = () => useContext(SocketContext);
