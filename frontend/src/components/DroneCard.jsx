// frontend/src/components/DroneCard.jsx

import React from 'react';
import { Plane, Battery, MapPin, Zap, AlertCircle } from 'lucide-react';

const DroneCard = ({ drone, onClick }) => {
  const getStatusColor = (status) => {
    const colors = {
      idle: 'bg-green-100 text-green-700 border-green-300',
      in_use: 'bg-blue-100 text-blue-700 border-blue-300',
      charging: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      maintenance: 'bg-red-100 text-red-700 border-red-300'
    };
    return colors[status] || 'bg-gray-100 text-gray-700 border-gray-300';
  };

  const getStatusIcon = (status) => {
    const icons = {
      idle: '✅',
      in_use: '🚁',
      charging: '🔌',
      maintenance: '🔧'
    };
    return icons[status] || '❓';
  };

  const getBatteryColor = (level) => {
    if (level >= 80) return 'text-green-600';
    if (level >= 50) return 'text-yellow-600';
    if (level >= 20) return 'text-orange-600';
    return 'text-red-600';
  };

  const getBatteryIcon = (level) => {
    if (level >= 80) return '🔋';
    if (level >= 50) return '🔋';
    if (level >= 20) return '🪫';
    return '⚠️';
  };

  return (
    <div 
      onClick={() => onClick && onClick(drone)}
      className="bg-white rounded-xl border-2 border-gray-200 hover:border-blue-400 p-5 transition-all cursor-pointer hover:shadow-xl group"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-blue-500 to-purple-600 text-white w-14 h-14 rounded-full flex items-center justify-center text-2xl shadow-lg group-hover:scale-110 transition">
            <Plane size={24} />
          </div>
          <div>
            <h3 className="font-bold text-lg text-gray-800">{drone.name}</h3>
            <p className="text-sm text-gray-500">{drone.model || 'Model DX-100'}</p>
          </div>
        </div>

        {/* Status Badge */}
        <span className={`
          px-3 py-1 rounded-full text-xs font-bold border-2 flex items-center gap-1
          ${getStatusColor(drone.status)}
        `}>
          <span>{getStatusIcon(drone.status)}</span>
          <span>{drone.status?.toUpperCase()}</span>
        </span>
      </div>

      {/* Stats */}
      <div className="space-y-3">
        {/* Battery */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Battery size={18} className={getBatteryColor(drone.battery_level)} />
            <span className="font-medium">Pin</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-24 bg-gray-200 rounded-full h-2.5 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all ${
                  drone.battery_level >= 50 ? 'bg-green-500' : 
                  drone.battery_level >= 20 ? 'bg-yellow-500' : 
                  'bg-red-500'
                }`}
                style={{ width: `${drone.battery_level}%` }}
              ></div>
            </div>
            <span className={`text-sm font-bold ${getBatteryColor(drone.battery_level)}`}>
              {drone.battery_level.toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Payload */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2 text-gray-600">
            <Zap size={18} className="text-purple-600" />
            <span className="font-medium">Tải trọng</span>
          </div>
          <span className="font-bold text-gray-800">{drone.max_payload} kg</span>
        </div>

        {/* Location */}
        {drone.current_lat && drone.current_lng && (
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-gray-600">
              <MapPin size={18} className="text-blue-600" />
              <span className="font-medium">Vị trí</span>
            </div>
            <span className="text-xs text-gray-500">
              {drone.current_lat.toFixed(4)}, {drone.current_lng.toFixed(4)}
            </span>
          </div>
        )}
      </div>

      {/* Warning */}
      {drone.battery_level < 20 && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
          <AlertCircle size={18} className="text-red-600" />
          <span className="text-xs text-red-700 font-semibold">Pin yếu - Cần sạc ngay</span>
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 pt-4 border-t flex items-center justify-between text-xs text-gray-500">
        <span>ID: #{drone.id}</span>
        <span className="text-blue-600 font-semibold group-hover:underline">
          Xem chi tiết →
        </span>
      </div>
    </div>
  );
};

export default DroneCard;