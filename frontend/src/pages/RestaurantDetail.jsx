import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { ShoppingCart, Clock, Star, MapPin } from 'lucide-react';
import { userApi, productApi, getImageUrl } from '../api';

const RestaurantDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [restaurant, setRestaurant] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRestaurantAndProducts();
  }, [id]);

  const fetchRestaurantAndProducts = async () => {
    try {
      const [resRes, prodRes] = await Promise.all([
        userApi.get(`/restaurants/${id}`),
        productApi.get(`/products/restaurant/${id}`)
      ]);
      setRestaurant(resRes.data);
      setProducts(prodRes.data);
    } catch (error) {
      toast.error('Không thể tải thông tin nhà hàng');
      navigate('/restaurants');
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (product) => {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user || user.role !== 'customer') {
      toast.warning('Vui lòng đăng nhập với tài khoản khách hàng');
      navigate('/login');
      return;
    }

    const cart = JSON.parse(localStorage.getItem('drone_cart')) || [];
    const existing = cart.find(item => item.product_id === product.id);
    
    if (existing) {
      existing.quantity++;
    } else {
      cart.push({
        product_id: product.id,
        product_name: product.name,
        price: product.price,
        quantity: 1,
        restaurant_id: parseInt(id)
      });
    }
    
    localStorage.setItem('drone_cart', JSON.stringify(cart));
    toast.success(`Đã thêm ${product.name}`);
    window.dispatchEvent(new Event('cart-updated'));
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
      <div className="bg-gradient-to-r from-rose-500 to-orange-400 text-white">
        <div className="max-w-7xl mx-auto px-4 py-12">
          <div className="flex items-start gap-6">
            <div className="w-32 h-32 bg-white rounded-2xl shadow-xl overflow-hidden">
              <img 
                src={getImageUrl(restaurant?.restaurant_image)} 
                alt={restaurant?.restaurant_name}
                className="w-full h-full object-cover"
                onError={(e) => e.target.src = 'https://placehold.co/200x200?text=Restaurant'}
              />
            </div>
            <div className="flex-1">
              <h1 className="text-4xl font-bold mb-2">{restaurant?.restaurant_name}</h1>
              <p className="text-white/90 mb-4">{restaurant?.restaurant_description}</p>
              <div className="flex gap-6 text-sm">
                <span className="flex items-center gap-2">
                  <Star className="fill-yellow-300 text-yellow-300" size={20} />
                  <span>4.5</span>
                </span>
                <span className="flex items-center gap-2">
                  <Clock size={20} />
                  <span>20-30 phút</span>
                </span>
                <span className="flex items-center gap-2">
                  <MapPin size={20} />
                  <span>{restaurant?.city || 'TP.HCM'}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Products */}
      <div className="max-w-7xl mx-auto px-4 py-10">
        <h2 className="text-2xl font-bold mb-6">Thực đơn</h2>
        
        {products.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <p className="text-6xl mb-4">🍽️</p>
            <p>Nhà hàng chưa có món ăn nào</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map(product => (
              <div key={product.id} className="bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                <div className="h-48 bg-gray-200 overflow-hidden">
                  <img 
                    src={getImageUrl(product.image_url)} 
                    alt={product.name}
                    className="w-full h-full object-cover hover:scale-110 transition duration-500"
                    onError={(e) => e.target.src = 'https://placehold.co/400x300?text=Food'}
                  />
                </div>
                <div className="p-4">
                  <h3 className="font-bold text-lg mb-2">{product.name}</h3>
                  <p className="text-gray-500 text-sm mb-3 line-clamp-2">{product.description}</p>
                  <div className="flex justify-between items-center">
                    <span className="text-rose-500 font-bold text-xl">
                      {new Intl.NumberFormat('vi-VN', {style: 'currency', currency: 'VND'}).format(product.price)}
                    </span>
                    {product.is_available && product.stock_quantity > 0 ? (
                      <button 
                        onClick={() => addToCart(product)}
                        className="bg-rose-500 text-white px-4 py-2 rounded-lg hover:bg-rose-600 transition flex items-center gap-2"
                      >
                        <ShoppingCart size={18} />
                        Thêm
                      </button>
                    ) : (
                      <span className="text-gray-400 text-sm">Hết hàng</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RestaurantDetail;