import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { Users, Store, Package, Plane, ShieldCheck, Ban, CheckCircle, Trash2, X, Eye } from 'lucide-react';
import { userApi, orderApi } from '../api';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  
  const [users, setUsers] = useState([]);
  const [restaurants, setRestaurants] = useState([]);
  const [orders, setOrders] = useState([]);
  const [drones, setDrones] = useState([]);
  
  const [showModal, setShowModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [modalType, setModalType] = useState('');

  const fetchAllData = async () => {
    try {
      setLoading(true);
      const [usersRes, restaurantsRes, ordersRes, dronesRes] = await Promise.all([
        userApi.get('/users').catch(() => ({ data: [] })),
        userApi.get('/restaurants').catch(() => ({ data: [] })),
        orderApi.get('/orders').catch(() => ({ data: [] })),
        orderApi.get('/drones').catch(() => ({ data: [] }))
      ]);

      setUsers(usersRes.data);
      setRestaurants(restaurantsRes.data);
      setOrders(ordersRes.data);
      setDrones(dronesRes.data);
    } catch (error) {
      console.error("Error loading data:", error);
      toast.error('Không thể tải dữ liệu', { autoClose: 2000 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, []);

  // User Management
  const toggleUserStatus = async (userId, currentStatus) => {
    try {
      await userApi.put(`/users/${userId}`, { is_active: !currentStatus });
      toast.success('✅ Đã cập nhật trạng thái user', { autoClose: 2000 });
      fetchAllData();
    } catch (error) {
      toast.error('❌ Lỗi cập nhật', { autoClose: 2000 });
    }
  };

  const deleteUser = async (userId) => {
    if (!window.confirm('Xác nhận xóa user này?')) return;
    try {
      await userApi.delete(`/users/${userId}`);
      toast.success('✅ Đã xóa user', { autoClose: 2000 });
      fetchAllData();
    } catch (error) {
      toast.error('❌ Lỗi xóa user', { autoClose: 2000 });
    }
  };

  // Restaurant Management
  const toggleRestaurantStatus = async (restaurantId, currentStatus) => {
    try {
      await userApi.put(`/users/${restaurantId}`, { 
        status: currentStatus === 'active' ? 'inactive' : 'active' 
      });
      toast.success('✅ Đã cập nhật trạng thái nhà hàng', { autoClose: 2000 });
      fetchAllData();
    } catch (error) {
      toast.error('❌ Lỗi cập nhật', { autoClose: 2000 });
    }
  };

  // Drone Management
  const chargeDrone = async (droneId) => {
    try {
      await orderApi.post(`/drones/${droneId}/charge`);
      toast.success('✅ Đã sạc pin drone', { autoClose: 2000 });
      fetchAllData();
    } catch (error) {
      toast.error('❌ Lỗi sạc drone', { autoClose: 2000 });
    }
  };

  const updateDroneStatus = async (droneId, newStatus) => {
    try {
      await orderApi.put(`/drones/${droneId}`, { status: newStatus });
      toast.success('✅ Đã cập nhật trạng thái drone', { autoClose: 2000 });
      fetchAllData();
    } catch (error) {
      toast.error('❌ Lỗi cập nhật', { autoClose: 2000 });
    }
  };

  // Stats
  const stats = {
    totalUsers: users.length,
    activeUsers: users.filter(u => u.is_active).length,
    totalRestaurants: restaurants.length,
    activeRestaurants: restaurants.filter(r => r.status === 'active').length,
    totalOrders: orders.length,
    completedOrders: orders.filter(o => o.status === 'delivered').length,
    totalDrones: drones.length,
    activeDrones: drones.filter(d => d.status === 'in_use').length,
    totalRevenue: orders.filter(o => o.status === 'delivered').reduce((sum, o) => sum + o.total_amount, 0),
    platformRevenue: orders.filter(o => o.status === 'delivered').reduce((sum, o) => sum + (o.total_amount * 0.15), 0)
  };

  const getRoleBadge = (role) => {
    const colors = { 
      admin: 'bg-red-100 text-red-800', 
      restaurant: 'bg-orange-100 text-orange-800', 
      customer: 'bg-green-100 text-green-800' 
    };
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${colors[role] || 'bg-gray-100'}`}>
        {role?.toUpperCase() || 'N/A'}
      </span>
    );
  };

  const getStatusBadge = (status) => {
    const colors = { 
      idle: 'bg-green-100 text-green-800', 
      in_use: 'bg-blue-100 text-blue-800', 
      charging: 'bg-yellow-100 text-yellow-800', 
      maintenance: 'bg-red-100 text-red-800' 
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-bold ${colors[status] || 'bg-gray-100'}`}>
        {status}
      </span>
    );
  };

  const openModal = (type, item) => {
    setModalType(type);
    setSelectedItem(item);
    setShowModal(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-500">Đang tải dữ liệu hệ thống...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-800 to-indigo-700 text-white py-10 shadow-lg">
        <div className="max-w-7xl mx-auto px-4">
          <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
            <ShieldCheck size={40} /> Admin Dashboard
          </h1>
          <p className="opacity-90">Hệ thống quản trị trung tâm DroneFood</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="max-w-7xl mx-auto px-4 -mt-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-blue-500">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-gray-500 text-sm font-bold uppercase">Users</p>
                <p className="text-3xl font-bold text-gray-800">{stats.totalUsers}</p>
                <p className="text-xs text-green-600">Active: {stats.activeUsers}</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-full text-blue-600">
                <Users size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-orange-500">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-gray-500 text-sm font-bold uppercase">Nhà hàng</p>
                <p className="text-3xl font-bold text-gray-800">{stats.totalRestaurants}</p>
                <p className="text-xs text-green-600">Active: {stats.activeRestaurants}</p>
              </div>
              <div className="bg-orange-100 p-3 rounded-full text-orange-600">
                <Store size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-green-500">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-gray-500 text-sm font-bold uppercase">Đơn hàng</p>
                <p className="text-3xl font-bold text-gray-800">{stats.totalOrders}</p>
                <p className="text-xs text-green-600">Hoàn thành: {stats.completedOrders}</p>
              </div>
              <div className="bg-green-100 p-3 rounded-full text-green-600">
                <Package size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-purple-500">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-gray-500 text-sm font-bold uppercase">Doanh thu</p>
                <p className="text-2xl font-bold text-green-600">
                  {stats.platformRevenue.toLocaleString()}₫
                </p>
                <p className="text-xs text-gray-500">Phí nền tảng (15%)</p>
              </div>
              <div className="bg-purple-100 p-3 rounded-full text-purple-600">
                <Plane size={24} />
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="flex border-b overflow-x-auto">
            {['overview', 'users', 'restaurants', 'orders', 'drones'].map(tab => (
              <button 
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-4 font-bold text-sm uppercase tracking-wide transition whitespace-nowrap ${
                  activeTab === tab ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:bg-gray-50'
                }`}
              >
                {tab === 'overview' && 'Tổng quan'}
                {tab === 'users' && 'Người dùng'}
                {tab === 'restaurants' && 'Nhà hàng'}
                {tab === 'orders' && 'Đơn hàng'}
                {tab === 'drones' && 'Drones'}
              </button>
            ))}
          </div>

          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-purple-500 to-pink-600 text-white p-8 rounded-xl">
                  <h2 className="text-2xl font-bold mb-4">Tổng quan hệ thống</h2>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <p className="text-purple-100 mb-2">Tổng doanh thu</p>
                      <p className="text-3xl font-bold">{stats.totalRevenue.toLocaleString()}₫</p>
                    </div>
                    <div>
                      <p className="text-purple-100 mb-2">Doanh thu nền tảng</p>
                      <p className="text-3xl font-bold">{stats.platformRevenue.toLocaleString()}₫</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div className="border rounded-lg p-6">
                    <h3 className="font-bold text-lg mb-4">Top 5 Nhà hàng</h3>
                    {restaurants.slice(0, 5).map(r => (
                      <div key={r.id} className="flex justify-between items-center py-2 border-b">
                        <span className="font-medium">{r.restaurant_name}</span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          r.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {r.status}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="border rounded-lg p-6">
                    <h3 className="font-bold text-lg mb-4">Drone Status</h3>
                    {drones.slice(0, 5).map(d => (
                      <div key={d.id} className="flex justify-between items-center py-2 border-b">
                        <span className="font-medium">{d.name}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{d.battery_level}%</span>
                          {getStatusBadge(d.status)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <>
                {users.length === 0 ? (
                  <p className="text-center text-gray-500 py-10">Không có dữ liệu người dùng</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="text-gray-500 border-b">
                          <th className="py-3">ID</th>
                          <th className="py-3">Họ tên</th>
                          <th className="py-3">Email</th>
                          <th className="py-3">Vai trò</th>
                          <th className="py-3">Trạng thái</th>
                          <th className="py-3">Hành động</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map(u => (
                          <tr key={u.id} className="border-b hover:bg-gray-50">
                            <td className="py-3 font-bold">#{u.id}</td>
                            <td className="py-3 font-medium">{u.full_name || u.username}</td>
                            <td className="py-3 text-gray-600">{u.email}</td>
                            <td className="py-3">{getRoleBadge(u.role)}</td>
                            <td className="py-3">
                              <span className={`px-2 py-1 rounded text-xs font-bold ${
                                u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                              }`}>
                                {u.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="py-3">
                              <div className="flex gap-2">
                                <button
                                  onClick={() => openModal('user', u)}
                                  className="text-blue-600 hover:text-blue-800"
                                  title="Xem chi tiết"
                                >
                                  <Eye size={18} />
                                </button>
                                <button
                                  onClick={() => toggleUserStatus(u.id, u.is_active)}
                                  className={`${u.is_active ? 'text-red-600' : 'text-green-600'} hover:opacity-70`}
                                  title={u.is_active ? 'Vô hiệu hóa' : 'Kích hoạt'}
                                >
                                  {u.is_active ? <Ban size={18} /> : <CheckCircle size={18} />}
                                </button>
                                {u.role !== 'admin' && (
                                  <button
                                    onClick={() => deleteUser(u.id)}
                                    className="text-red-600 hover:text-red-800"
                                    title="Xóa"
                                  >
                                    <Trash2 size={18} />
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}

            {/* Restaurants Tab */}
            {activeTab === 'restaurants' && (
              <>
                {restaurants.length === 0 ? (
                  <p className="text-center text-gray-500 py-10">Chưa có nhà hàng nào</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {restaurants.map(r => (
                      <div key={r.id} className="border rounded-lg p-4 hover:shadow-md transition">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="font-bold text-lg">{r.restaurant_name}</h3>
                            <p className="text-gray-500 text-sm">📍 {r.city || 'N/A'}</p>
                          </div>
                          <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                            r.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {r.status === 'active' ? 'Hoạt động' : 'Đóng cửa'}
                          </div>
                        </div>
                        <p className="text-gray-400 text-xs mb-3 line-clamp-2">
                          {r.restaurant_description}
                        </p>
                        <div className="flex gap-2">
                          <button
                            onClick={() => openModal('restaurant', r)}
                            className="flex-1 bg-blue-500 text-white px-3 py-2 rounded hover:bg-blue-600 flex items-center justify-center gap-2"
                          >
                            <Eye size={16} /> Xem
                          </button>
                          <button
                            onClick={() => toggleRestaurantStatus(r.id, r.status)}
                            className={`flex-1 ${
                              r.status === 'active' ? 'bg-red-500' : 'bg-green-500'
                            } text-white px-3 py-2 rounded hover:opacity-80 flex items-center justify-center gap-2`}
                          >
                            {r.status === 'active' ? <><Ban size={16} /> Khóa</> : <><CheckCircle size={16} /> Mở</>}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* Orders Tab */}
            {activeTab === 'orders' && (
              <>
                {orders.length === 0 ? (
                  <p className="text-center text-gray-500 py-10">Chưa có đơn hàng nào</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="text-gray-500 border-b">
                          <th className="py-3">Mã đơn</th>
                          <th className="py-3">User ID</th>
                          <th className="py-3">Tổng tiền</th>
                          <th className="py-3">Phí (15%)</th>
                          <th className="py-3">Trạng thái</th>
                          <th className="py-3">Ngày đặt</th>
                          <th className="py-3">Hành động</th>
                        </tr>
                      </thead>
                      <tbody>
                        {orders.map(o => (
                          <tr key={o.id} className="border-b hover:bg-gray-50">
                            <td className="py-3 font-bold">#{o.id}</td>
                            <td className="py-3">User #{o.user_id}</td>
                            <td className="py-3 font-bold text-rose-600">
                              {parseInt(o.total_amount).toLocaleString()}₫
                            </td>
                            <td className="py-3 text-green-600 font-semibold">
                              {parseInt(o.total_amount * 0.15).toLocaleString()}₫
                            </td>
                            <td className="py-3">
                              <span className={`px-2 py-1 rounded text-xs uppercase font-bold ${
                                o.status === 'delivered' ? 'bg-green-100 text-green-700' : 
                                o.status === 'in_delivery' ? 'bg-blue-100 text-blue-700' : 
                                'bg-yellow-100 text-yellow-700'
                              }`}>
                                {o.status}
                              </span>
                            </td>
                            <td className="py-3 text-sm text-gray-500">
                              {new Date(o.created_at).toLocaleDateString('vi-VN')}
                            </td>
                            <td className="py-3">
                              <button
                                onClick={() => openModal('order', o)}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                <Eye size={18} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}

            {/* Drones Tab */}
            {activeTab === 'drones' && (
              <>
                {drones.length === 0 ? (
                  <p className="text-center text-gray-500 py-10">Chưa có drone nào</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {drones.map(d => (
                      <div key={d.id} className="border rounded-xl p-5 hover:shadow-lg transition relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4">
                          <div className="bg-indigo-50 p-3 rounded-lg">
                            <Plane className="text-indigo-600" size={24} />
                          </div>
                          {getStatusBadge(d.status)}
                        </div>
                        <h3 className="font-bold text-lg">{d.name}</h3>
                        <p className="text-gray-500 text-sm mb-4">{d.model}</p>
                        
                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-gray-500">Pin</span>
                              <span className="font-bold">{d.battery_level}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full ${
                                  d.battery_level > 50 ? 'bg-green-500' : 
                                  d.battery_level > 20 ? 'bg-yellow-500' : 
                                  'bg-red-500'
                                }`} 
                                style={{width: `${d.battery_level}%`}}
                              ></div>
                            </div>
                          </div>
                          <div className="flex justify-between text-sm pt-2 border-t">
                            <span className="text-gray-500">Tải trọng:</span>
                            <span className="font-bold">{d.max_payload} kg</span>
                          </div>
                        </div>

                        <div className="flex gap-2 mt-4">
                          {d.battery_level < 20 && (
                            <button
                              onClick={() => chargeDrone(d.id)}
                              className="flex-1 bg-yellow-500 text-white px-3 py-2 rounded hover:bg-yellow-600"
                            >
                              ⚡ Sạc
                            </button>
                          )}
                          <select
                            value={d.status}
                            onChange={(e) => updateDroneStatus(d.id, e.target.value)}
                            className="flex-1 border rounded px-2 py-2 text-sm"
                          >
                            <option value="idle">Idle</option>
                            <option value="in_use">In Use</option>
                            <option value="charging">Charging</option>
                            <option value="maintenance">Maintenance</option>
                          </select>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && selectedItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-2xl font-bold">Chi tiết {modalType}</h2>
              <button onClick={() => setShowModal(false)}>
                <X size={24} />
              </button>
            </div>
            <div className="p-6">
              {modalType === 'order' ? (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="font-bold">Đơn #{selectedItem.id}</h3>
                    <span className={`px-2 py-1 rounded text-xs font-bold ${selectedItem.status === 'delivered' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                      {selectedItem.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    <p>Khách hàng: User #{selectedItem.user_id}</p>
                    <p>Nhà hàng: #{selectedItem.restaurant_id}</p>
                    <p>Địa chỉ: {selectedItem.delivery_address}</p>
                    <p>Tổng: {parseInt(selectedItem.total_amount).toLocaleString()}₫</p>
                  </div>

                  <div className="border-t pt-4">
                    <h4 className="font-semibold mb-2">Món trong đơn</h4>
                    {selectedItem.items?.map(it => (
                      <div key={it.id} className="flex justify-between text-sm py-1 border-b">
                        <div>{it.quantity}x {it.product_name}</div>
                        <div>{(it.price * it.quantity).toLocaleString()}₫</div>
                      </div>
                    ))}
                  </div>

                  {selectedItem.history && selectedItem.history.length > 0 && (
                    <div className="border-t pt-4">
                      <h4 className="font-semibold mb-2">Lịch sử trạng thái</h4>
                      <div className="space-y-2 text-sm text-gray-600">
                        {selectedItem.history.map(h => (
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

                  <div className="border-t pt-4 flex gap-2">
                    <select defaultValue={selectedItem.status} onChange={async (e) => {
                      try {
                        await orderApi.put(`/orders/${selectedItem.id}/status`, { status: e.target.value });
                        toast.success('Đã cập nhật trạng thái');
                        fetchAllData();
                        setShowModal(false);
                      } catch (err) {
                        toast.error('Lỗi cập nhật');
                      }
                    }} className="border rounded px-3 py-2">
                      <option value="waiting_confirmation">waiting_confirmation</option>
                      <option value="confirmed">confirmed</option>
                      <option value="preparing">preparing</option>
                      <option value="ready">ready</option>
                      <option value="in_delivery">in_delivery</option>
                      <option value="delivered">delivered</option>
                      <option value="cancelled">cancelled</option>
                      <option value="rejected">rejected</option>
                    </select>
                    <button onClick={() => setShowModal(false)} className="bg-gray-100 px-4 py-2 rounded">Đóng</button>
                  </div>
                </div>
              ) : (
                <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm">{JSON.stringify(selectedItem, null, 2)}</pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;