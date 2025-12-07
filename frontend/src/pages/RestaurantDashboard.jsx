import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { Package, DollarSign, Clock, CheckCircle, XCircle, Edit, Trash2, Upload, X } from 'lucide-react';
import { productApi, orderApi, getImageUrl } from '../api';

const RestaurantDashboard = () => {
  const [activeTab, setActiveTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [selectedOrderDrone, setSelectedOrderDrone] = useState(null);
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const user = JSON.parse(localStorage.getItem('user'));

  const [productForm, setProductForm] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    preparation_time: 15,
    stock_quantity: 999,
    weight: 0.5,
    image: null
  });

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      await Promise.all([fetchProducts(), fetchOrders()]);
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const res = await productApi.get(`/products/restaurant/${user.id}`);
      setProducts(res.data);
    } catch (error) {
      console.error('Error fetching products');
    }
  };

  const fetchOrders = async () => {
    try {
      const res = await orderApi.get('/orders');
      setOrders(res.data);
    } catch (error) {
      console.error('Error fetching orders');
    }
  };

  const handleCreateProduct = async () => {
    const formData = new FormData();
    Object.keys(productForm).forEach(key => {
      if (productForm[key] !== null) {
        formData.append(key, productForm[key]);
      }
    });

    try {
      await productApi.post('/products', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('✅ Đã thêm món mới!', { autoClose: 2000 });
      setShowProductModal(false);
      resetProductForm();
      fetchProducts();
    } catch (error) {
      toast.error('❌ ' + (error.response?.data?.detail || 'Lỗi thêm món'), { autoClose: 2000 });
    }
  };

  const handleUpdateProduct = async () => {
    try {
      await productApi.put(`/products/${editingProduct.id}`, {
        name: productForm.name,
        description: productForm.description,
        price: parseFloat(productForm.price),
        category: productForm.category,
        preparation_time: parseInt(productForm.preparation_time),
        stock_quantity: parseInt(productForm.stock_quantity),
        weight: parseFloat(productForm.weight)
      });
      toast.success('✅ Đã cập nhật món!', { autoClose: 2000 });
      setShowProductModal(false);
      setEditingProduct(null);
      resetProductForm();
      fetchProducts();
    } catch (error) {
      toast.error('❌ ' + (error.response?.data?.detail || 'Lỗi cập nhật'), { autoClose: 2000 });
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Xác nhận xóa món này?')) return;
    try {
      await productApi.delete(`/products/${productId}`);
      toast.success('✅ Đã xóa món!', { autoClose: 2000 });
      fetchProducts();
    } catch (error) {
      toast.error('❌ Lỗi xóa món', { autoClose: 2000 });
    }
  };

  const resetProductForm = () => {
    setProductForm({
      name: '',
      description: '',
      price: '',
      category: '',
      preparation_time: 15,
      stock_quantity: 999,
      weight: 0.5,
      image: null
    });
  };

  const openEditModal = (product) => {
    setEditingProduct(product);
    setProductForm({
      name: product.name,
      description: product.description || '',
      price: product.price,
      category: product.category || '',
      preparation_time: product.preparation_time || 15,
      stock_quantity: product.stock_quantity || 999,
      weight: product.weight || 0.5,
      image: null
    });
    setShowProductModal(true);
  };

  // When opening an order modal, fetch drone details if assigned
  useEffect(() => {
    if (showOrderModal && selectedOrder && selectedOrder.drone_id) {
      (async () => {
        try {
          const res = await orderApi.get('/drones');
          const d = res.data.find(x => x.id === selectedOrder.drone_id);
          setSelectedOrderDrone(d || null);
        } catch (e) {
          setSelectedOrderDrone(null);
        }
      })();
    } else {
      setSelectedOrderDrone(null);
    }
  }, [showOrderModal, selectedOrder]);

  const toggleProductAvailability = async (productId, currentStatus) => {
    try {
      await productApi.put(`/products/${productId}`, {
        is_available: !currentStatus
      });
      toast.success('✅ Đã cập nhật trạng thái', { autoClose: 2000 });
      fetchProducts();
    } catch (error) {
      toast.error('❌ Lỗi cập nhật', { autoClose: 2000 });
    }
  };

  const acceptOrder = async (orderId) => {
    try {
      await orderApi.post(`/orders/${orderId}/accept`);
      toast.success('✅ Đã nhận đơn hàng', { autoClose: 2000 });
      fetchOrders();
    } catch (error) {
      toast.error('❌ Lỗi nhận đơn', { autoClose: 2000 });
    }
  };

  const rejectOrder = async (orderId) => {
    const reason = prompt('Lý do từ chối:', 'Hết nguyên liệu');
    if (!reason) return;
    
    try {
      await orderApi.post(`/orders/${orderId}/reject`, { reason });
      toast.success('✅ Đã từ chối đơn hàng', { autoClose: 2000 });
      fetchOrders();
    } catch (error) {
      toast.error('❌ Lỗi từ chối đơn', { autoClose: 2000 });
    }
  };

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      const res = await orderApi.put(`/orders/${orderId}/status`, { status: newStatus });
      toast.success('✅ Đã cập nhật trạng thái đơn hàng', { autoClose: 2000 });
      // Update orders list and selected order with returned payload
      await fetchOrders();
      if (selectedOrder?.id === orderId) {
        setSelectedOrder(res.data);
      }
    } catch (error) {
      toast.error('❌ Lỗi cập nhật trạng thái', { autoClose: 2000 });
    }
  };

  const stats = {
    totalProducts: products.length,
    availableProducts: products.filter(p => p.is_available).length,
    totalOrders: orders.length,
    pendingOrders: orders.filter(o => o.status === 'waiting_confirmation').length,
    completedOrders: orders.filter(o => o.status === 'delivered').length,
    totalRevenue: orders
      .filter(o => o.status === 'delivered')
      .reduce((sum, o) => sum + o.total_amount, 0),
    platformFee: orders
      .filter(o => o.status === 'delivered')
      .reduce((sum, o) => sum + (o.total_amount * 0.15), 0)
  };

  const netRevenue = stats.totalRevenue - stats.platformFee;

  const getStatusBadge = (status) => {
    const statusMap = {
      waiting_confirmation: { text: 'Chờ xác nhận', color: 'bg-yellow-100 text-yellow-800' },
      confirmed: { text: 'Đã xác nhận', color: 'bg-blue-100 text-blue-800' },
      preparing: { text: 'Đang làm món', color: 'bg-purple-100 text-purple-800' },
      ready: { text: 'Sẵn sàng giao', color: 'bg-green-100 text-green-800' },
      in_delivery: { text: 'Đang giao', color: 'bg-indigo-100 text-indigo-800' },
      delivered: { text: 'Hoàn thành', color: 'bg-green-100 text-green-800' },
      rejected: { text: 'Đã từ chối', color: 'bg-red-100 text-red-800' }
    };
    const config = statusMap[status] || statusMap.waiting_confirmation;
    return <span className={`px-3 py-1 rounded-full text-xs font-bold ${config.color}`}>{config.text}</span>;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin text-6xl">⏳</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-rose-500 to-orange-400 text-white py-8">
        <div className="max-w-7xl mx-auto px-4">
          <h1 className="text-3xl font-bold mb-2">{user.restaurant_name}</h1>
          <p>{user.restaurant_description}</p>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-md">
            <div className="flex items-center gap-3 mb-2">
              <Package className="text-blue-600" size={24} />
              <span className="text-gray-500">Tổng món</span>
            </div>
            <p className="text-3xl font-bold">{stats.totalProducts}</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md">
            <div className="flex items-center gap-3 mb-2">
              <Clock className="text-orange-600" size={24} />
              <span className="text-gray-500">Chờ xử lý</span>
            </div>
            <p className="text-3xl font-bold">{stats.pendingOrders}</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md">
            <div className="flex items-center gap-3 mb-2">
              <CheckCircle className="text-green-600" size={24} />
              <span className="text-gray-500">Hoàn thành</span>
            </div>
            <p className="text-3xl font-bold">{stats.completedOrders}</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md">
            <div className="flex items-center gap-3 mb-2">
              <DollarSign className="text-purple-600" size={24} />
              <span className="text-gray-500">Doanh thu ròng</span>
            </div>
            <p className="text-2xl font-bold text-green-600">
              {netRevenue.toLocaleString()}₫
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Phí nền tảng: {stats.platformFee.toLocaleString()}₫
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="flex border-b">
            {['products', 'orders', 'revenue'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-4 font-semibold transition ${
                  activeTab === tab ? 'bg-rose-500 text-white' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {tab === 'products' && 'Sản phẩm'}
                {tab === 'orders' && 'Đơn hàng'}
                {tab === 'revenue' && 'Doanh thu'}
              </button>
            ))}
          </div>

          <div className="p-6">
            {/* Products Tab */}
            {activeTab === 'products' && (
              <>
                <button
                  onClick={() => {
                    setEditingProduct(null);
                    resetProductForm();
                    setShowProductModal(true);
                  }}
                  className="mb-6 bg-rose-500 text-white px-6 py-3 rounded-lg hover:bg-rose-600 font-semibold"
                >
                  + Thêm món mới
                </button>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {products.map(product => (
                    <div key={product.id} className="border rounded-lg overflow-hidden hover:shadow-lg transition">
                      <div className="h-40 bg-gray-200">
                        <img 
                          src={getImageUrl(product.image_url)} 
                          alt={product.name}
                          className="w-full h-full object-cover"
                          onError={(e) => e.target.src = 'https://placehold.co/400x300?text=Food'}
                        />
                      </div>
                      <div className="p-4">
                        <h3 className="font-bold mb-1">{product.name}</h3>
                        <p className="text-rose-500 font-semibold mb-2">
                          {product.price.toLocaleString()}₫
                        </p>
                        <div className="flex items-center justify-between mb-3">
                          <span className={`text-sm ${product.is_available ? 'text-green-600' : 'text-red-600'}`}>
                            {product.is_available ? '✓ Đang bán' : '✗ Hết hàng'}
                          </span>
                          <button
                            onClick={() => toggleProductAvailability(product.id, product.is_available)}
                            className="text-sm text-blue-600 hover:underline"
                          >
                            {product.is_available ? 'Tắt' : 'Bật'}
                          </button>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => openEditModal(product)}
                            className="flex-1 bg-blue-500 text-white px-3 py-2 rounded hover:bg-blue-600 flex items-center justify-center gap-2"
                          >
                            <Edit size={16} /> Sửa
                          </button>
                          <button
                            onClick={() => handleDeleteProduct(product.id)}
                            className="flex-1 bg-red-500 text-white px-3 py-2 rounded hover:bg-red-600 flex items-center justify-center gap-2"
                          >
                            <Trash2 size={16} /> Xóa
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Orders Tab */}
            {activeTab === 'orders' && (
              <div className="space-y-4">
                {orders.map(order => (
                  <div key={order.id} className="border rounded-lg p-4 hover:shadow-md transition">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-bold text-lg">Đơn #{order.id}</h3>
                        <p className="text-sm text-gray-500">
                          {new Date(order.created_at).toLocaleString('vi-VN')}
                        </p>
                      </div>
                      <div className="flex gap-2 items-center">
                        {getStatusBadge(order.status)}
                        <button
                          onClick={() => {
                            setSelectedOrder(order);
                            setShowOrderModal(true);
                          }}
                          className="text-blue-600 hover:underline text-sm"
                        >
                          Chi tiết
                        </button>
                      </div>
                    </div>

                    {order.status === 'waiting_confirmation' && (
                      <div className="flex gap-2 mb-3">
                        <button
                          onClick={() => acceptOrder(order.id)}
                          className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 flex items-center gap-2"
                        >
                          <CheckCircle size={18} /> Nhận đơn
                        </button>
                        <button
                          onClick={() => rejectOrder(order.id)}
                          className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 flex items-center gap-2"
                        >
                          <XCircle size={18} /> Từ chối
                        </button>
                      </div>
                    )}

                    {['confirmed', 'preparing', 'ready'].includes(order.status) && (
                      <select
                        value={order.status}
                        onChange={(e) => updateOrderStatus(order.id, e.target.value)}
                        className="border rounded-lg px-4 py-2 mb-3"
                      >
                        <option value="confirmed">Đã xác nhận</option>
                        <option value="preparing">Đang làm món</option>
                        <option value="ready">Sẵn sàng giao</option>
                      </select>
                    )}

                    <div className="flex justify-between items-center border-t pt-3">
                      <span className="font-bold">Tổng:</span>
                      <span className="text-xl font-bold text-rose-500">
                        {order.total_amount.toLocaleString()}₫
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Revenue Tab */}
            {activeTab === 'revenue' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white p-8 rounded-xl">
                  <h2 className="text-2xl font-bold mb-4">Tổng quan doanh thu</h2>
                  <div className="grid grid-cols-3 gap-6">
                    <div>
                      <p className="text-green-100 mb-2">Tổng doanh thu</p>
                      <p className="text-3xl font-bold">{stats.totalRevenue.toLocaleString()}₫</p>
                    </div>
                    <div>
                      <p className="text-green-100 mb-2">Phí nền tảng (15%)</p>
                      <p className="text-3xl font-bold">-{stats.platformFee.toLocaleString()}₫</p>
                    </div>
                    <div>
                      <p className="text-green-100 mb-2">Doanh thu ròng</p>
                      <p className="text-4xl font-bold">{netRevenue.toLocaleString()}₫</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white border rounded-lg p-6">
                  <h3 className="font-bold text-lg mb-4">Chi tiết đơn hàng đã hoàn thành</h3>
                  <table className="w-full">
                    <thead className="border-b">
                      <tr className="text-left text-gray-500">
                        <th className="py-2">Mã đơn</th>
                        <th>Ngày</th>
                        <th>Tổng tiền</th>
                        <th>Phí (15%)</th>
                        <th>Thực nhận</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orders.filter(o => o.status === 'delivered').map(order => (
                        <tr key={order.id} className="border-b">
                          <td className="py-3 font-bold">#{order.id}</td>
                          <td>{new Date(order.created_at).toLocaleDateString('vi-VN')}</td>
                          <td className="font-semibold">{order.total_amount.toLocaleString()}₫</td>
                          <td className="text-red-600">-{(order.total_amount * 0.15).toLocaleString()}₫</td>
                          <td className="text-green-600 font-bold">{(order.total_amount * 0.85).toLocaleString()}₫</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Product Modal */}
      {showProductModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-2xl font-bold">
                {editingProduct ? 'Chỉnh sửa món ăn' : 'Thêm món mới'}
              </h2>
              <button onClick={() => setShowProductModal(false)}>
                <X size={24} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <input
                type="text"
                placeholder="Tên món *"
                value={productForm.name}
                onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                className="w-full px-4 py-2 border rounded-lg"
              />
              <textarea
                placeholder="Mô tả"
                value={productForm.description}
                onChange={(e) => setProductForm({...productForm, description: e.target.value})}
                className="w-full px-4 py-2 border rounded-lg"
                rows="3"
              />
              <div className="grid grid-cols-2 gap-4">
                <input
                  type="number"
                  placeholder="Giá (VNĐ) *"
                  value={productForm.price}
                  onChange={(e) => setProductForm({...productForm, price: e.target.value})}
                  className="px-4 py-2 border rounded-lg"
                />
                <input
                  type="text"
                  placeholder="Danh mục"
                  value={productForm.category}
                  onChange={(e) => setProductForm({...productForm, category: e.target.value})}
                  className="px-4 py-2 border rounded-lg"
                />
                <input
                  type="number"
                  placeholder="Thời gian chuẩn bị (phút)"
                  value={productForm.preparation_time}
                  onChange={(e) => setProductForm({...productForm, preparation_time: e.target.value})}
                  className="px-4 py-2 border rounded-lg"
                />
                <input
                  type="number"
                  placeholder="Số lượng"
                  value={productForm.stock_quantity}
                  onChange={(e) => setProductForm({...productForm, stock_quantity: e.target.value})}
                  className="px-4 py-2 border rounded-lg"
                />
              </div>
              {!editingProduct && (
                <div className="border-2 border-dashed rounded-lg p-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <Upload size={20} />
                    <span>Chọn ảnh món ăn</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setProductForm({...productForm, image: e.target.files[0]})}
                      className="hidden"
                    />
                  </label>
                  {productForm.image && (
                    <p className="text-sm text-green-600 mt-2">✓ {productForm.image.name}</p>
                  )}
                </div>
              )}
              <button
                onClick={editingProduct ? handleUpdateProduct : handleCreateProduct}
                className="w-full bg-rose-500 text-white py-3 rounded-lg font-bold hover:bg-rose-600"
              >
                {editingProduct ? 'Cập nhật' : 'Thêm món'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Order Detail Modal */}
      {showOrderModal && selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-2xl font-bold">Chi tiết đơn hàng #{selectedOrder.id}</h2>
              <button onClick={() => setShowOrderModal(false)}>
                <X size={24} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Trạng thái hiện tại:</span>
                {getStatusBadge(selectedOrder.status)}
              </div>
              
              {['confirmed', 'preparing', 'ready'].includes(selectedOrder.status) && (
                <div>
                  <label className="block text-sm font-medium mb-2">Cập nhật trạng thái:</label>
                  <select
                    value={selectedOrder.status}
                    onChange={(e) => updateOrderStatus(selectedOrder.id, e.target.value)}
                    className="w-full border rounded-lg px-4 py-2"
                  >
                    <option value="confirmed">Đã xác nhận</option>
                    <option value="preparing">Đang làm món</option>
                    <option value="ready">Sẵn sàng giao</option>
                  </select>
                </div>
              )}

              <div className="border-t pt-4">
                <h3 className="font-bold mb-2">Món ăn:</h3>
                {selectedOrder.items?.map((item, idx) => (
                  <div key={idx} className="flex justify-between py-2">
                    <span>{item.quantity}x {item.product_name}</span>
                    <span>{(item.price * item.quantity).toLocaleString()}₫</span>
                  </div>
                ))}
              </div>

              {/* Status history */}
              {selectedOrder.history && selectedOrder.history.length > 0 && (
                <div className="border-t pt-4">
                  <h3 className="font-bold mb-2">Lịch sử trạng thái</h3>
                  <div className="space-y-2 text-sm text-gray-600">
                    {selectedOrder.history.map(h => (
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

              <div className="border-t pt-4">
                <div className="flex justify-between text-lg font-bold">
                  <span>Tổng cộng:</span>
                  <span className="text-rose-500">{selectedOrder.total_amount.toLocaleString()}₫</span>
                </div>
              </div>

              <div className="border-t pt-4 text-sm text-gray-600">
                <p>📍 Địa chỉ: {selectedOrder.delivery_address}</p>
                <p>📅 Ngày đặt: {new Date(selectedOrder.created_at).toLocaleString('vi-VN')}</p>
                {selectedOrder.notes && <p>📝 Ghi chú: {selectedOrder.notes}</p>}
              </div>
              {selectedOrder.drone_id && (
                <div className="border-t pt-4 text-sm text-gray-600">
                  <p className="font-semibold">🚁 Drone được phân công: #{selectedOrder.drone_id}</p>
                  {selectedOrderDrone ? (
                    <div className="text-xs text-gray-500 mt-1">
                      <div>Tên: {selectedOrderDrone.name}</div>
                      <div>Trạng thái: {selectedOrderDrone.status}</div>
                      <div>Pin: {selectedOrderDrone.battery_level}%</div>
                    </div>
                  ) : (
                    <div className="text-xs text-gray-400">Thông tin drone đang tải...</div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RestaurantDashboard;