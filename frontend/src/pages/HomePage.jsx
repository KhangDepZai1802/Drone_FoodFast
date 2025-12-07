import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Zap, ShieldCheck, Plane, Star, TrendingUp, Award, ChevronRight } from 'lucide-react';
import { userApi, productApi, getImageUrl } from '../api';

const HomePage = () => {
  const [featuredRestaurants, setFeaturedRestaurants] = useState([]);
  const [bestsellerProducts, setBestsellerProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [restaurantsRes, productsRes] = await Promise.all([
        userApi.get('/restaurants'),
        productApi.get('/products?available_only=true&limit=8')
      ]);
      
      // Top 3 restaurants
      setFeaturedRestaurants(restaurantsRes.data.slice(0, 3));
      
      // Top 8 products
      setBestsellerProducts(productsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      {/* Hero Banner */}
      <div className="relative bg-gradient-to-br from-rose-500 via-orange-500 to-yellow-400 text-white overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="absolute top-0 right-0 w-1/2 h-full opacity-20">
          <div className="text-[400px] absolute top-[-100px] right-[-100px] animate-bounce-slow">🚁</div>
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 py-24 md:py-32">
          <div className="md:w-1/2 z-10">
            <div className="inline-block bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-semibold mb-4">
              🎉 Công nghệ giao hàng tương lai
            </div>
            <h1 className="text-5xl md:text-7xl font-extrabold leading-tight mb-6">
              Giao đồ ăn<br/>
              <span className="text-yellow-300">siêu tốc</span><br/>
              bằng Drone
            </h1>
            <p className="text-xl mb-8 text-white/90 max-w-lg">
              Trải nghiệm công nghệ giao hàng bay. Nóng hổi, an toàn và chỉ mất 15 phút.
            </p>
            <div className="flex gap-4">
              <Link 
                to="/restaurants" 
                className="px-8 py-4 bg-white text-rose-500 font-bold rounded-full shadow-xl hover:shadow-2xl hover:scale-105 transition transform flex items-center gap-2"
              >
                Đặt món ngay <ChevronRight size={20} />
              </Link>
              <Link 
                to="/restaurants" 
                className="px-8 py-4 bg-white/20 backdrop-blur-sm border-2 border-white text-white font-bold rounded-full hover:bg-white/30 transition"
              >
                Xem thực đơn
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">Tại sao chọn DroneFood?</h2>
            <p className="text-gray-600">Trải nghiệm giao hàng thế hệ mới</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div className="p-8 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl hover:shadow-xl transition text-center group">
              <div className="bg-blue-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition">
                <Zap size={32} className="text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">Siêu tốc độ</h3>
              <p className="text-gray-600">Giao hàng trong vòng 15 phút với công nghệ drone tự động</p>
            </div>
            
            <div className="p-8 bg-gradient-to-br from-green-50 to-green-100 rounded-2xl hover:shadow-xl transition text-center group">
              <div className="bg-green-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition">
                <ShieldCheck size={32} className="text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">An toàn tuyệt đối</h3>
              <p className="text-gray-600">Hệ thống AI đảm bảo an toàn và theo dõi 24/7</p>
            </div>
            
            <div className="p-8 bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl hover:shadow-xl transition text-center group">
              <div className="bg-purple-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition">
                <Plane size={32} className="text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">Công nghệ cao</h3>
              <p className="text-gray-600">Đội ngũ drone hiện đại với GPS và cảm biến thông minh</p>
            </div>
          </div>
        </div>
      </div>

      {/* Featured Restaurants */}
      {!loading && featuredRestaurants.length > 0 && (
        <div className="py-16 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-3xl font-bold mb-2 flex items-center gap-3">
                  <Award className="text-yellow-500" size={32} />
                  Nhà hàng nổi bật
                </h2>
                <p className="text-gray-600">Top nhà hàng được yêu thích nhất</p>
              </div>
              <Link 
                to="/restaurants" 
                className="text-rose-500 font-semibold hover:text-rose-600 flex items-center gap-2"
              >
                Xem tất cả <ChevronRight size={20} />
              </Link>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {featuredRestaurants.map(restaurant => (
                <Link 
                  to={`/restaurant/${restaurant.id}`} 
                  key={restaurant.id} 
                  className="block group"
                >
                  <div className="bg-white rounded-2xl overflow-hidden shadow-md hover:shadow-2xl transition transform hover:-translate-y-2">
                    <div className="h-56 overflow-hidden relative">
                      <div className="absolute top-4 right-4 bg-rose-500 text-white px-3 py-1 rounded-full text-sm font-bold z-10 flex items-center gap-1">
                        <Star size={16} className="fill-current" />
                        4.8
                      </div>
                      <img 
                        src={getImageUrl(restaurant.restaurant_image)} 
                        className="w-full h-full object-cover group-hover:scale-110 transition duration-500" 
                        onError={(e) => e.target.src = 'https://placehold.co/400x300?text=Restaurant'}
                        alt={restaurant.restaurant_name}
                      />
                    </div>
                    <div className="p-6">
                      <h3 className="font-bold text-xl mb-2 group-hover:text-rose-500 transition">
                        {restaurant.restaurant_name}
                      </h3>
                      <p className="text-gray-500 text-sm mb-3 line-clamp-2">
                        {restaurant.restaurant_description}
                      </p>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Zap size={16} className="text-yellow-500" />
                          15-20 phút
                        </span>
                        <span>📍 {restaurant.city || 'TP.HCM'}</span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Bestseller Products */}
      {!loading && bestsellerProducts.length > 0 && (
        <div className="py-16 bg-white">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-3xl font-bold mb-2 flex items-center gap-3">
                  <TrendingUp className="text-rose-500" size={32} />
                  Món ăn bán chạy
                </h2>
                <p className="text-gray-600">Top món được đặt nhiều nhất</p>
              </div>
              <Link 
                to="/restaurants" 
                className="text-rose-500 font-semibold hover:text-rose-600 flex items-center gap-2"
              >
                Xem tất cả <ChevronRight size={20} />
              </Link>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {bestsellerProducts.map(product => (
                <Link
                  key={product.id}
                  to={`/restaurant/${product.restaurant_id}`}
                  className="block bg-white rounded-xl overflow-hidden shadow-md hover:shadow-xl transition transform hover:-translate-y-1 border border-gray-100"
                >
                  <div className="h-48 overflow-hidden relative">
                    <div className="absolute top-3 left-3 bg-red-500 text-white px-2 py-1 rounded-lg text-xs font-bold">
                      🔥 HOT
                    </div>
                    <img 
                      src={getImageUrl(product.image_url)} 
                      alt={product.name}
                      className="w-full h-full object-cover hover:scale-110 transition duration-500"
                      onError={(e) => e.target.src = 'https://placehold.co/400x300?text=Food'}
                    />
                  </div>
                  <div className="p-4">
                    <h3 className="font-bold mb-2 line-clamp-1">{product.name}</h3>
                    <p className="text-gray-500 text-sm mb-3 line-clamp-2">
                      {product.description || 'Món ăn ngon tuyệt vời'}
                    </p>
                    <div className="flex justify-between items-center">
                      <span className="text-rose-500 font-bold text-lg">
                        {product.price.toLocaleString()}₫
                      </span>
                      <span className="text-xs text-gray-500">⏱️ {product.preparation_time || 15} phút</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* CTA Section */}
      <div className="py-20 bg-gradient-to-r from-rose-500 to-orange-400 text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="text-6xl mb-6 animate-bounce">🚁</div>
          <h2 className="text-4xl font-bold mb-4">Sẵn sàng trải nghiệm?</h2>
          <p className="text-xl mb-8 text-white/90">
            Đặt món ngay hôm nay và nhận ưu đãi 20% cho đơn hàng đầu tiên
          </p>
          <Link 
            to="/restaurants" 
            className="inline-block px-10 py-4 bg-white text-rose-500 font-bold rounded-full shadow-xl hover:shadow-2xl hover:scale-105 transition transform"
          >
            Khám phá ngay 🚀
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;