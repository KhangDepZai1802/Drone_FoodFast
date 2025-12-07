// frontend/src/components/DroneStatusTimeline.jsx

import React, { useState, useEffect } from 'react';
import { Plane, Package, CheckCircle, Clock } from 'lucide-react';

const DroneStatusTimeline = ({ order, droneId }) => {
  const [currentStage, setCurrentStage] = useState(0);
  const [statusMessage, setStatusMessage] = useState('Đang tìm drone...');

  useEffect(() => {
    if (!order || !droneId) return;

    // Giả lập timeline: mỗi stage cách nhau vài giây
    const stages = [
      { duration: 3000, message: 'Đang tìm drone khả dụng...' },
      { duration: 2000, message: `✅ Drone #${droneId} đã nhận nhiệm vụ` },
      { duration: 8000, message: '🚁 Drone đang bay đến nhà hàng...' },
      { duration: 5000, message: '📦 Drone đã đến, vui lòng chuẩn bị đơn hàng' },
      { duration: 3000, message: '🛫 Drone đang giao hàng cho khách' }
    ];

    let currentIndex = 0;
    
    const advanceStage = () => {
      if (currentIndex < stages.length) {
        setCurrentStage(currentIndex);
        setStatusMessage(stages[currentIndex].message);
        
        setTimeout(() => {
          currentIndex++;
          if (currentIndex < stages.length) {
            advanceStage();
          }
        }, stages[currentIndex].duration);
      }
    };

    advanceStage();
  }, [order, droneId]);

  const timelineSteps = [
    { icon: Clock, label: 'Tìm drone', color: 'text-yellow-600' },
    { icon: CheckCircle, label: 'Drone nhận việc', color: 'text-green-600' },
    { icon: Plane, label: 'Bay đến quán', color: 'text-blue-600' },
    { icon: Package, label: 'Lấy hàng', color: 'text-purple-600' },
    { icon: Plane, label: 'Giao hàng', color: 'text-orange-600' }
  ];

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
      <h3 className="text-lg font-bold mb-4 text-gray-800">📡 Trạng thái Drone</h3>
      
      {/* Status Message */}
      <div className="bg-white p-4 rounded-lg mb-6 border-l-4 border-blue-500 shadow-sm">
        <p className="text-base font-semibold text-gray-800">{statusMessage}</p>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Progress Line */}
        <div className="absolute top-6 left-6 w-0.5 h-[calc(100%-3rem)] bg-gray-300"></div>
        <div 
          className="absolute top-6 left-6 w-0.5 bg-blue-500 transition-all duration-1000"
          style={{ height: `${(currentStage / (timelineSteps.length - 1)) * 100}%` }}
        ></div>

        {/* Steps */}
        <div className="space-y-6">
          {timelineSteps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index <= currentStage;
            const isCurrent = index === currentStage;

            return (
              <div key={index} className="relative flex items-center gap-4">
                {/* Icon Circle */}
                <div className={`
                  relative z-10 w-12 h-12 rounded-full flex items-center justify-center
                  transition-all duration-500
                  ${isActive 
                    ? 'bg-blue-500 text-white shadow-lg scale-110' 
                    : 'bg-gray-200 text-gray-400'
                  }
                  ${isCurrent ? 'ring-4 ring-blue-200 animate-pulse' : ''}
                `}>
                  <Icon size={20} />
                </div>

                {/* Label */}
                <div className={`
                  flex-1 p-3 rounded-lg transition-all
                  ${isActive 
                    ? 'bg-white border-2 border-blue-500' 
                    : 'bg-gray-100 border border-gray-300'
                  }
                `}>
                  <p className={`
                    font-semibold text-sm
                    ${isActive ? 'text-gray-800' : 'text-gray-500'}
                  `}>
                    {step.label}
                  </p>
                  {isCurrent && (
                    <p className="text-xs text-blue-600 mt-1">Đang xử lý...</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Drone Info */}
      {droneId && currentStage >= 1 && (
        <div className="mt-6 p-4 bg-white rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500">Drone được giao</p>
              <p className="text-lg font-bold text-blue-600">Drone #{droneId}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Pin</p>
              <p className="text-lg font-bold text-green-600">🔋 85%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DroneStatusTimeline;