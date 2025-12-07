// frontend/src/components/DroneMap.jsx

import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { DroneSimulator, generateRoute } from '../utils/droneSimulator';

// Fix Leaflet icon issue (CRITICAL for react-leaflet 4.x)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom icons
const createIcon = (color, symbol) => {
  return L.divIcon({
    className: 'custom-icon',
    html: `<div style="
      background-color: ${color};
      width: 35px;
      height: 35px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      border: 3px solid white;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    ">${symbol}</div>`,
    iconSize: [35, 35],
    iconAnchor: [17, 17]
  });
};

const hqIcon = createIcon('#10b981', '🏢');
const restaurantIcon = createIcon('#ef4444', '🏪');
const customerIcon = createIcon('#3b82f6', '🏠');
const droneIcon = createIcon('#f59e0b', '🚁');

// Component để auto fit bounds
function AutoFitBounds({ positions }) {
  const map = useMap();
  
  useEffect(() => {
    if (positions.length > 0) {
      const bounds = L.latLngBounds(positions);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [positions, map]);
  
  return null;
}

const DroneMap = ({ order, onClose }) => {
  const [dronePosition, setDronePosition] = useState(null);
  const [currentStatus, setCurrentStatus] = useState('Chuẩn bị khởi hành');
  const simulatorRef = useRef(null);

  useEffect(() => {
    if (!order) return;

    // Tạo route (HQ → Restaurant → Customer)
    const route = generateRoute(
      order.restaurant_lat || 10.7757, 
      order.restaurant_lng || 106.7004,
      order.delivery_lat || 10.7820,
      order.delivery_lng || 106.7050
    );

    // Khởi tạo simulator
    const simulator = new DroneSimulator(order.id, route);
    simulator.start();
    simulatorRef.current = simulator;

    // Update drone position mỗi 200ms
    const interval = setInterval(() => {
      const update = simulator.update();
      if (update) {
        setDronePosition(update.position);
        setCurrentStatus(simulator.getStatus());
        
        if (update.completed) {
          clearInterval(interval);
          setCurrentStatus('✅ Giao hàng thành công!');
        }
      }
    }, 200);

    return () => clearInterval(interval);
  }, [order]);

  if (!order) return null;

  const route = generateRoute(
    order.restaurant_lat || 10.7757,
    order.restaurant_lng || 106.7004,
    order.delivery_lat || 10.7820,
    order.delivery_lng || 106.7050
  );

  const routeCoords = route.map(p => [p.lat, p.lng]);
  const allPositions = route.map(p => [p.lat, p.lng]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">🚁 Theo dõi Drone #{order.drone_id || '---'}</h2>
            <p className="text-blue-100 text-sm mt-1">Đơn hàng #{order.id}</p>
          </div>
          <button 
            onClick={onClose}
            className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-lg font-semibold transition"
          >
            ✕ Đóng
          </button>
        </div>

        {/* Status Bar */}
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 p-4 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-orange-500 text-white w-12 h-12 rounded-full flex items-center justify-center text-2xl animate-bounce">
                🚁
              </div>
              <div>
                <p className="font-semibold text-gray-800">{currentStatus}</p>
                <p className="text-sm text-gray-600">
                  {dronePosition ? 
                    `📍 ${dronePosition.lat.toFixed(5)}, ${dronePosition.lng.toFixed(5)}` : 
                    'Đang cập nhật...'
                  }
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Pin</p>
              <p className="text-lg font-bold text-green-600">🔋 85%</p>
            </div>
          </div>
        </div>

        {/* Map */}
        <div className="h-[500px] relative">
          <MapContainer
            center={[route[0].lat, route[0].lng]}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />

            <AutoFitBounds positions={allPositions} />

            {/* Route line */}
            <Polyline 
              positions={routeCoords} 
              color="#3b82f6" 
              weight={3}
              dashArray="10, 10"
            />

            {/* Markers */}
            <Marker position={[route[0].lat, route[0].lng]} icon={hqIcon}>
              <Popup>
                <strong>🏢 Trụ sở Drone</strong><br />
                Điểm xuất phát
              </Popup>
            </Marker>

            <Marker position={[route[1].lat, route[1].lng]} icon={restaurantIcon}>
              <Popup>
                <strong>🏪 Nhà hàng</strong><br />
                Lấy đơn hàng
              </Popup>
            </Marker>

            <Marker position={[route[2].lat, route[2].lng]} icon={customerIcon}>
              <Popup>
                <strong>🏠 Địa chỉ giao hàng</strong><br />
                {order.delivery_address}
              </Popup>
            </Marker>

            {/* Drone position (moving) */}
            {dronePosition && (
              <Marker position={[dronePosition.lat, dronePosition.lng]} icon={droneIcon}>
                <Popup>
                  <strong>🚁 Drone đang bay</strong><br />
                  {currentStatus}
                </Popup>
              </Marker>
            )}
          </MapContainer>
        </div>

        {/* Legend */}
        <div className="bg-gray-50 p-4 flex justify-around text-sm">
          <div className="flex items-center gap-2">
            <span>🏢</span>
            <span className="text-gray-700">Trụ sở</span>
          </div>
          <div className="flex items-center gap-2">
            <span>🏪</span>
            <span className="text-gray-700">Nhà hàng</span>
          </div>
          <div className="flex items-center gap-2">
            <span>🏠</span>
            <span className="text-gray-700">Khách hàng</span>
          </div>
          <div className="flex items-center gap-2">
            <span>🚁</span>
            <span className="text-gray-700">Drone</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DroneMap;