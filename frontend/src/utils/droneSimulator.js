// frontend/src/utils/droneSimulator.js

/**
 * Giả lập di chuyển drone giữa các điểm
 * Tính toán vị trí trung gian (interpolation)
 */

export const calculateDistance = (lat1, lng1, lat2, lng2) => {
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};

export const interpolatePosition = (start, end, progress) => {
  return {
    lat: start.lat + (end.lat - start.lat) * progress,
    lng: start.lng + (end.lng - start.lng) * progress
  };
};

export class DroneSimulator {
  constructor(orderId, route) {
    this.orderId = orderId;
    this.route = route; // [{lat, lng, name}, ...]
    this.currentSegment = 0;
    this.progress = 0;
    this.speed = 0.01; // 1% per update (adjust for faster/slower)
    this.status = 'idle';
  }

  start() {
    this.status = 'moving';
    this.currentSegment = 0;
    this.progress = 0;
  }

  update() {
    if (this.status !== 'moving') return null;

    this.progress += this.speed;

    if (this.progress >= 1) {
      this.progress = 0;
      this.currentSegment++;

      if (this.currentSegment >= this.route.length - 1) {
        this.status = 'completed';
        return {
          position: this.route[this.route.length - 1],
          segment: this.currentSegment,
          completed: true
        };
      }
    }

    const start = this.route[this.currentSegment];
    const end = this.route[this.currentSegment + 1];
    const position = interpolatePosition(start, end, this.progress);

    return {
      position,
      segment: this.currentSegment,
      progress: this.progress,
      completed: false
    };
  }

  getCurrentPosition() {
    if (this.currentSegment >= this.route.length) {
      return this.route[this.route.length - 1];
    }
    const start = this.route[this.currentSegment];
    const end = this.route[this.currentSegment + 1] || start;
    return interpolatePosition(start, end, this.progress);
  }

  getStatus() {
    const stages = [
      'Đang bay đến nhà hàng',
      'Đang lấy hàng tại nhà hàng',
      'Đang giao hàng cho khách'
    ];
    return stages[this.currentSegment] || 'Hoàn thành';
  }
}

// Tạo route mẫu (HQ → Restaurant → Customer)
export const generateRoute = (restaurantLat, restaurantLng, customerLat, customerLng) => {
  const HQ_LAT = 10.762622; // Trụ sở drone mặc định (HCM)
  const HQ_LNG = 106.660172;

  return [
    { lat: HQ_LAT, lng: HQ_LNG, name: 'Trụ sở Drone' },
    { lat: restaurantLat, lng: restaurantLng, name: 'Nhà hàng' },
    { lat: customerLat, lng: customerLng, name: 'Khách hàng' }
  ];
};