// frontend/src/contexts/DroneContext.jsx

import React, { createContext, useState, useEffect, useContext } from 'react';
import { orderApi } from '../api';

const DroneContext = createContext();

export const useDrones = () => {
  const context = useContext(DroneContext);
  if (!context) {
    throw new Error('useDrones must be used within DroneProvider');
  }
  return context;
};

export const DroneProvider = ({ children }) => {
  const [drones, setDrones] = useState([]);
  const [activeDrones, setActiveDrones] = useState({}); // {orderId: droneData}
  const [loading, setLoading] = useState(false);

  // Fetch tất cả drone từ backend
  const fetchDrones = async () => {
    try {
      setLoading(true);
      const res = await orderApi.get('/drones');
      setDrones(res.data);
    } catch (error) {
      console.error('Error fetching drones:', error);
    } finally {
      setLoading(false);
    }
  };

  // Lấy drone theo order_id
  const getDroneByOrderId = (orderId) => {
    return activeDrones[orderId] || null;
  };

  // Cập nhật trạng thái drone khi có assignment
  const assignDroneToOrder = (orderId, droneId) => {
    const drone = drones.find(d => d.id === droneId);
    if (drone) {
      setActiveDrones(prev => ({
        ...prev,
        [orderId]: {
          ...drone,
          assignedAt: new Date(),
          status: 'assigned'
        }
      }));
    }
  };

  // Polling để cập nhật drones mỗi 10s
  useEffect(() => {
    fetchDrones();
    const interval = setInterval(fetchDrones, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <DroneContext.Provider value={{
      drones,
      activeDrones,
      loading,
      fetchDrones,
      getDroneByOrderId,
      assignDroneToOrder
    }}>
      {children}
    </DroneContext.Provider>
  );
};