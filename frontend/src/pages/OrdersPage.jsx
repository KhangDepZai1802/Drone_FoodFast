import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { Package, Clock, CheckCircle, XCircle, Plane, Ban } from 'lucide-react';
import { orderApi } from '../api';

const OrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [drones, setDrones] = useState([]);
  const [showDroneModal, setShowDroneModal] = useState(false);
  const [selectedDrone, setSelectedDrone] = useState(null);

  useEffect(() => {
    fetchOrders();
    fetchDrones();
    const interval = setInterval(fetchOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchOrders = async () => {
    try {
      const res = await orderApi.get('/orders');
      setOrders(res.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDrones = async () => {
    try {
      const res = await orderApi.get('/drones');
      setDrones(res.data);
    } catch (error) {
      console.debug('No drones available');
    }
  };

  const cancelOrder = async (orderId) => {
    if (!window.confirm('Bạn có chắc muốn hủy đơn hàng này?')) return;
    
    try {
      await orderApi.put(`/orders/${orderId}/status`, { status: 'cancelled' });
      toast.success('✅ Đã hủy đơn hàng', { autoClose: 2000 });
      fetchOrders();
    } catch (error) {
      toast.error('❌ Không thể hủy đơn. ' + (error.response?.data?.detail || ''), { autoClose: 2000 });
    }
  };

  const getStatusConfig = (status) => {
    const configs = {
      waiting_confirmation: { text: 'Chờ xác nhận', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      confirmed: { text: 'Đã xác nhận', color: 'bg-blue-100 text-blue-800', icon: CheckCircle },
      preparing: { text: 'Đang chuẩn bị', color: 'bg-purple-100 text-purple-800', icon: Package },
      ready: { text: 'Sẵn sàng', color: 'bg-green-100 text-green-800', icon: CheckCircle },
      in_delivery: { text: 'Đang giao', color: 'bg-indigo-100 text-indigo-800', icon: Plane },
      delivered: { text: 'Đã giao', color: 'bg-green-100 text-green-800', icon: CheckCircle },
      cancelled: { text: 'Đã hủy', color: 'bg-red-100 text-red-800', icon: XCircle },
      rejected: { text: 'Bị từ chối', color: 'bg-red-100 text-red-800', icon: XCircle }
    };
    return configs[status] || configs.waiting_confirmation;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin text-6xl">⏳</div>
      </div>
    );
  }

  return (
    <>
    <div className="min-h-screen bg-gray-50 py-10">
      <div className="max-w-5xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8">Đơn hàng của tôi</h1>

        {orders.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <Package size={100} className="mx-auto mb-4 text-gray-300" />
            <p className="text-xl">Bạn chưa có đơn hàng nào</p>
          </div>
        ) : (
          <div className="space-y-6">
            {orders.map(order => {
              const statusConfig = getStatusConfig(order.status);
              const StatusIcon = statusConfig.icon;
              const canCancel = ['waiting_confirmation', 'confirmed'].includes(order.status);
              
              return (
                <div key={order.id} className="bg-white rounded-xl shadow-md overflow-hidden">
                  <div className="bg-gradient-to-r from-rose-500 to-orange-400 text-white p-4 flex justify-between items-center">
                    <div>
                      <h3 className="font-bold text-lg">Đơn hàng #{order.id}</h3>
                      <p className="text-sm text-white/80">
                        {new Date(order.created_at).toLocaleString('vi-VN')}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className={`px-4 py-2 rounded-full ${statusConfig.color} flex items-center gap-2`}>
                        <StatusIcon size={18} />
                        <span className="font-semibold">{statusConfig.text}</span>
                      </div>
                      {canCancel && (
                        <button
                          onClick={() => cancelOrder(order.id)}
                          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-full flex items-center gap-2 transition"
                          title="Hủy đơn hàng"
                        >
                          <Ban size={18} />
                          <span className="font-semibold">Hủy</span>
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="p-6">
                    <div className="mb-4 space-y-2">
                      {order.items?.map((item, idx) => (
                        <div key={idx} className="flex justify-between items-center py-2 border-b">
                          <div>
                            <span className="font-medium">{item.quantity}x {item.product_name}</span>
                          </div>
                          <span className="text-gray-600">
                            {new Intl.NumberFormat('vi-VN', {style: 'currency', currency: 'VND'}).format(item.price * item.quantity)}
                          </span>
                        </div>
                      ))}
                    </div>

                    <div className="flex justify-between items-center text-lg font-bold border-t-2 pt-4 mb-4">
                      <span>Tổng cộng:</span>
                      <span className="text-rose-500">
                        {new Intl.NumberFormat('vi-VN', {style: 'currency', currency: 'VND'}).format(order.total_amount)}
                      </span>
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                      <p className="text-sm text-gray-600">
                        📍 <span className="font-medium">Địa chỉ:</span> {order.delivery_address}
                      </p>
                      {order.distance_km && (
                        <p className="text-sm text-gray-600">
                          🛣️ <span className="font-medium">Khoảng cách:</span> {order.distance_km.toFixed(1)} km
                        </p>
                      )}
                      {order.estimated_delivery_time && (
                        <p className="text-sm text-gray-600">
                          ⏱️ <span className="font-medium">Dự kiến:</span> {order.estimated_delivery_time} phút
                        </p>
                      )}
                      {order.drone_id && (
                        <div className="flex items-center gap-2">
                          <p className="text-sm text-green-600 font-semibold flex items-center gap-2">
                            <Plane size={18} />
                            Drone #{order.drone_id} đang giao hàng
                          </p>
                          <button onClick={() => {
                            const d = drones.find(x => x.id === order.drone_id);
                            setSelectedDrone(d || { id: order.drone_id });
                            setShowDroneModal(true);
                          }} className="text-xs text-blue-600 hover:underline ml-2">Xem Drone</button>
                        </div>
                      )}
                      {order.rejection_reason && (
                        <p className="text-sm text-red-600 font-semibold">
                          ❌ Lý do từ chối: {order.rejection_reason}
                        </p>
                      )}
                      {order.notes && (
                        <p className="text-sm text-gray-600">
                          📝 <span className="font-medium">Ghi chú:</span> {order.notes}
                        </p>
                      )}
                      {/* Status history timeline */}
                      {order.history && order.history.length > 0 && (
                        <div className="mt-3 border-t pt-3">
                          <h4 className="text-sm font-semibold mb-2">Lịch sử trạng thái</h4>
                          <div className="space-y-2 text-sm text-gray-600">
                            {order.history.map(h => (
                              <div key={h.id} className="flex justify-between items-start">
                                <div>
                                  <div className="font-semibold">{h.status.replace('_', ' ').toUpperCase()}</div>
                                  <div className="text-xs text-gray-500">{h.role || 'system'} • {h.note || ''}</div>
                                </div>
                                <div className="text-xs text-gray-400">{new Date(h.changed_at).toLocaleString('vi-VN')}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
      {/* Drone Modal */}
      {showDroneModal && selectedDrone && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">Drone #{selectedDrone.id}</h3>
              <button onClick={() => setShowDroneModal(false)} className="text-gray-500 hover:text-gray-700">Đóng</button>
            </div>
            <div className="space-y-2 text-sm text-gray-700">
              <p><b>Tên:</b> {selectedDrone.name || '-'}</p>
              <p><b>Mô hình:</b> {selectedDrone.model || '-'}</p>
              <p><b>Trạng thái:</b> {selectedDrone.status || '-'}</p>
              <p><b>Pin:</b> {selectedDrone.battery_level ? selectedDrone.battery_level + '%' : '-'}</p>
              <p><b>Vị trí hiện tại:</b> {selectedDrone.current_lat ? `${selectedDrone.current_lat.toFixed(5)}, ${selectedDrone.current_lng.toFixed(5)}` : 'Không có'}</p>
              <p className="text-xs text-gray-400">(Thông tin drone lấy từ Order Service)</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default OrdersPage;