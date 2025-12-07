import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, LogOut, Zap, ShieldCheck, Plane } from 'lucide-react';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// --- IMPORT API (CRITICAL FIX) ---
import { authApi, userApi, getImageUrl } from './api';

// --- IMPORT CÁC TRANG TỪ THƯ MỤC PAGES ---
import RestaurantDetail from './pages/RestaurantDetail';
import CartPage from './pages/CartPage';
import OrdersPage from './pages/OrdersPage';
import AdminDashboard from './pages/AdminDashboard';
import RestaurantDashboard from './pages/RestaurantDashboard';
import HomePage from './pages/HomePage';
// ==========================================
// NAVBAR COMPONENT
// ==========================================
const Navbar = ({ user, cartCount, onLogout }) => {
  const isAdmin = user?.role === 'admin';
  const isRestaurant = user?.role === 'restaurant';
  const isCustomer = !isAdmin && !isRestaurant;

  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center cursor-pointer">
            <Link to="/" className="flex items-center gap-2">
              <span className="text-3xl">🚁</span>
              <span className="font-bold text-2xl text-transparent bg-clip-text bg-gradient-to-r from-primary to-rose-600">
                DroneFood
              </span>
            </Link>
          </div>
          <div className="flex items-center space-x-6">
            <Link to="/" className="text-gray-600 hover:text-primary font-medium">Trang chủ</Link>
            
            {isCustomer && (
              <>
                <Link to="/restaurants" className="text-gray-600 hover:text-primary font-medium">Nhà hàng</Link>
                {user && <Link to="/orders" className="text-gray-600 hover:text-primary font-medium">Đơn hàng</Link>}
              </>
            )}
            
            {user ? (
              <div className="flex items-center gap-4">
                {isAdmin && (
                   <Link to="/admin" className="text-blue-700 font-bold bg-blue-50 px-3 py-1 rounded border border-blue-200">
                     🛡️ Admin
                   </Link>
                )}
                {isRestaurant && (
                   <Link to="/restaurant-dashboard" className="text-green-700 font-bold bg-green-50 px-3 py-1 rounded border border-green-200">
                     🏪 Quản lý
                   </Link>
                )}
                
                {isCustomer && (
                  <Link to="/cart" className="relative p-2 text-gray-600 hover:text-primary transition">
                    <ShoppingCart size={24} />
                    {cartCount > 0 && (
                      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                        {cartCount}
                      </span>
                    )}
                  </Link>
                )}

                <div className="flex items-center gap-2 border-l pl-4 ml-2">
                  <div className="hidden md:flex flex-col text-right mr-1">
                    <span className="text-sm font-semibold">{user.full_name || user.username}</span>
                  </div>
                  <button onClick={onLogout} className="text-gray-400 hover:text-red-500">
                    <LogOut size={20} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex gap-3">
                <Link to="/login" className="px-4 py-2 text-primary border border-primary rounded-lg hover:bg-red-50 transition">Đăng nhập</Link>
                <Link to="/register" className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-red-600 shadow-lg shadow-red-200 transition">Đăng ký</Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

// Note: HomePage component is implemented in ./pages/HomePage.jsx and is imported at the top.
// The inline HomePage declaration was removed to avoid duplicate identifier errors.

// ==========================================
// LOGIN PAGE (FIXED)
// ==========================================
const LoginPage = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    console.log('🔐 LOGIN ATTEMPT:', { username, password: '***' });
    
    if (!username || !password) {
      toast.error('Vui lòng nhập đầy đủ thông tin');
      return;
    }

    setLoading(true);
    try {
      // ✅ FIX: Gọi đúng authApi.login() từ api.js
      console.log('📡 Calling authApi.login()...');
      const res = await authApi.login(username, password);
      
      console.log('✅ Login response:', res.data);
      
      // Lưu token và user
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      
      onLogin(res.data.user);
      toast.success('✅ Đăng nhập thành công!');
      
      // Redirect theo role
      if (res.data.user.role === 'admin') {
        navigate('/admin');
      } else if (res.data.user.role === 'restaurant') {
        navigate('/restaurant-dashboard');
      } else {
        navigate('/');
      }
    } catch (err) {
      console.error('❌ Login error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Đăng nhập thất bại';
      toast.error(`❌ ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
        <h2 className="text-3xl font-bold text-center mb-8">Đăng nhập</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <input 
            className="w-full px-4 py-3 rounded-lg border focus:ring-2 focus:ring-rose-500 outline-none" 
            placeholder="Tên đăng nhập" 
            value={username} 
            onChange={(e) => setUsername(e.target.value)} 
            disabled={loading}
            required 
          />
          <input 
            className="w-full px-4 py-3 rounded-lg border focus:ring-2 focus:ring-rose-500 outline-none" 
            type="password" 
            placeholder="Mật khẩu" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            disabled={loading}
            required 
          />
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-primary text-white py-3 rounded-lg font-bold hover:bg-rose-600 transition disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {loading ? 'Đang xử lý...' : 'Đăng nhập'}
          </button>
        </form>
        <p className="mt-4 text-center">
          Chưa có tài khoản? <Link to="/register" className="text-primary font-semibold hover:underline">Đăng ký ngay</Link>
        </p>
      </div>
    </div>
  );
};

// ==========================================
// REGISTER PAGE
// ==========================================
const RegisterPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ 
    username: '', 
    password: '', 
    email: '', 
    full_name: '', 
    phone: '', 
    address: '' 
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await userApi.post('/register', formData);
      toast.success('✅ Đăng ký thành công! Vui lòng đăng nhập.');
      navigate('/login');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Đăng ký thất bại');
    } finally {
      setLoading(false);
    }
  };
  // React-Toastify is configured once in main.jsx via <ToastContainer />
  // Avoid calling toast.configure inside components (it causes duplicate toasts and repeats on re-renders)
  return (
    <div className="min-h-[80vh] flex items-center justify-center bg-gray-100 py-10">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-lg">
        <h2 className="text-3xl font-bold text-center mb-6">Đăng ký</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
           <input className="w-full p-2 border rounded" placeholder="Họ tên" onChange={e => setFormData({...formData, full_name: e.target.value})} required />
           <input className="w-full p-2 border rounded" placeholder="Email" type="email" onChange={e => setFormData({...formData, email: e.target.value})} required />
           <input className="w-full p-2 border rounded" placeholder="Username" onChange={e => setFormData({...formData, username: e.target.value})} required />
           <input className="w-full p-2 border rounded" placeholder="Password" type="password" onChange={e => setFormData({...formData, password: e.target.value})} required />
           <input className="w-full p-2 border rounded" placeholder="SĐT" onChange={e => setFormData({...formData, phone: e.target.value})} required />
           <textarea className="w-full p-2 border rounded" placeholder="Địa chỉ" onChange={e => setFormData({...formData, address: e.target.value})} required />
           <button 
             type="submit"
             disabled={loading}
             className="w-full bg-primary text-white py-3 rounded font-bold hover:bg-rose-600 disabled:bg-gray-300"
           >
             {loading ? 'Đang xử lý...' : 'Đăng ký'}
           </button>
        </form>
      </div>
    </div>
  );
};

// ==========================================
// RESTAURANTS PAGE
// ==========================================
const RestaurantsPage = () => {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    userApi.get('/restaurants').then(res => {
      setRestaurants(res.data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="p-20 text-center">Loading...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-8">🍽️ Danh sách Nhà hàng</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {restaurants.map(res => (
          <Link to={`/restaurant/${res.id}`} key={res.id} className="block group">
            <div className="bg-white rounded-xl overflow-hidden shadow-md hover:shadow-xl transition">
              <div className="h-48 overflow-hidden">
                 <img src={getImageUrl(res.restaurant_image)} className="w-full h-full object-cover" onError={(e) => e.target.src = 'https://placehold.co/400x300'} />
              </div>
              <div className="p-4">
                <h3 className="font-bold text-lg group-hover:text-primary">{res.restaurant_name}</h3>
                <p className="text-gray-500 text-sm truncate">{res.restaurant_description}</p>
                <p className="text-xs text-gray-400 mt-2">📍 {res.city || 'TP.HCM'}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

// ==========================================
// MAIN APP COMPONENT
// ==========================================
function App() {
  const [user, setUser] = useState(null);
  const [cart, setCart] = useState([]);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) setUser(JSON.parse(storedUser));
    
    const loadCart = () => {
       const storedCart = localStorage.getItem('drone_cart');
       if (storedCart) setCart(JSON.parse(storedCart));
    };
    
    loadCart();
    window.addEventListener('cart-updated', loadCart);
    return () => window.removeEventListener('cart-updated', loadCart);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 font-sans text-slate-800">
      {/* ToastContainer is mounted in src/main.jsx to avoid duplicates */}
      <Navbar user={user} cartCount={cart.reduce((a,b) => a+b.quantity, 0)} onLogout={handleLogout} />
      
      <main className="flex-grow">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage onLogin={setUser} />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/restaurants" element={<RestaurantsPage />} />
          <Route path="/restaurant/:id" element={<RestaurantDetail />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/restaurant-dashboard" element={<RestaurantDashboard />} />
        </Routes>
      </main>

      <footer className="bg-gray-800 text-gray-400 py-8 text-center">
        <p>© 2025 Drone Food Delivery</p>
      </footer>
    </div>
  );
}

export default App;