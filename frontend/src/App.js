import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// User Context
const UserContext = React.createContext();

const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, [token]);

  const login = (userData, authToken) => {
    setUser(userData);
    setToken(authToken);
    localStorage.setItem('token', authToken);
    axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <UserContext.Provider value={{ user, token, login, logout }}>
      {children}
    </UserContext.Provider>
  );
};

// Components
const Navbar = () => {
  const { user, logout } = React.useContext(UserContext);

  return (
    <nav className="bg-red-600 text-white p-4 shadow-lg">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-2xl font-bold">🍕 FoodDelivery</h1>
        {user && (
          <div className="flex items-center space-x-4">
            <span>Welcome, {user.name} ({user.user_type})</span>
            <button
              onClick={logout}
              className="bg-red-700 px-4 py-2 rounded hover:bg-red-800"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

const LoginRegister = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    phone: '',
    user_type: 'customer',
    address: '',
    location: { lat: 40.7128, lng: -74.0060 } // Default to NYC
  });
  const [loading, setLoading] = useState(false);
  const { login } = React.useContext(UserContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const payload = isLogin 
        ? { email: formData.email, user_type: formData.user_type }
        : formData;
      
      const response = await axios.post(`${API}${endpoint}`, payload);
      login(response.data.user, response.data.token);
    } catch (error) {
      alert(error.response?.data?.detail || 'An error occurred');
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <div className="text-center mb-6">
          <h2 className="text-3xl font-bold text-gray-800">
            {isLogin ? 'Login' : 'Register'}
          </h2>
          <p className="text-gray-600">Choose your account type</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">User Type</label>
            <select
              value={formData.user_type}
              onChange={(e) => setFormData({...formData, user_type: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-red-500 focus:border-red-500"
            >
              <option value="customer">🛒 Customer</option>
              <option value="driver">🚗 Driver</option>
              <option value="restaurant">🏪 Restaurant Owner</option>
              <option value="admin">👑 Admin</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-red-500 focus:border-red-500"
              required
            />
          </div>

          {!isLogin && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-red-500 focus:border-red-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Phone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-red-500 focus:border-red-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Address</label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-red-500 focus:border-red-500"
                />
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {loading ? 'Loading...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-red-600 hover:text-red-800"
          >
            {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
          </button>
        </div>
      </div>
    </div>
  );
};

const CustomerDashboard = () => {
  const [restaurants, setRestaurants] = useState([]);
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [menu, setMenu] = useState([]);
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([]);
  const [ws, setWs] = useState(null);
  const { user } = React.useContext(UserContext);

  useEffect(() => {
    fetchRestaurants();
    fetchOrders();
    setupWebSocket();
  }, []);

  const setupWebSocket = () => {
    const wsUrl = `${BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/ws/customer_${user.id}`;
    const websocket = new WebSocket(wsUrl);
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'order_status_update') {
        fetchOrders(); // Refresh orders when status updates
        alert(`Order ${data.order_id} status updated to: ${data.status}`);
      } else if (data.type === 'driver_assigned') {
        alert(`Driver assigned to your order: ${data.driver.name}`);
        fetchOrders();
      } else if (data.type === 'driver_location_update') {
        console.log('Driver location updated:', data.location);
      }
    };
    
    setWs(websocket);
    
    return () => websocket.close();
  };

  const fetchRestaurants = async () => {
    try {
      const response = await axios.get(`${API}/restaurants`);
      setRestaurants(response.data);
    } catch (error) {
      console.error('Error fetching restaurants:', error);
    }
  };

  const fetchMenu = async (restaurantId) => {
    try {
      const response = await axios.get(`${API}/restaurants/${restaurantId}/menu`);
      setMenu(response.data);
    } catch (error) {
      console.error('Error fetching menu:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const addToCart = (item) => {
    const existingItem = cart.find(cartItem => cartItem.menu_item_id === item.id);
    if (existingItem) {
      setCart(cart.map(cartItem => 
        cartItem.menu_item_id === item.id 
          ? {...cartItem, quantity: cartItem.quantity + 1}
          : cartItem
      ));
    } else {
      setCart([...cart, { menu_item_id: item.id, quantity: 1, name: item.name, price: item.price }]);
    }
  };

  const placeOrder = async () => {
    if (cart.length === 0) {
      alert('Cart is empty');
      return;
    }

    try {
      const orderData = {
        restaurant_id: selectedRestaurant.id,
        items: cart.map(item => ({
          menu_item_id: item.menu_item_id,
          quantity: item.quantity
        })),
        delivery_address: user.address || "123 Main St, City, State",
        delivery_location: user.location || { lat: 40.7128, lng: -74.0060 }
      };

      const response = await axios.post(`${API}/orders`, orderData);
      alert('Order placed successfully!');
      setCart([]);
      fetchOrders();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error placing order');
    }
  };

  if (selectedRestaurant) {
    return (
      <div className="container mx-auto p-4">
        <button
          onClick={() => {setSelectedRestaurant(null); setMenu([]);}}
          className="mb-4 bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
        >
          ← Back to Restaurants
        </button>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2">
            <h2 className="text-2xl font-bold mb-4">{selectedRestaurant.name}</h2>
            <div className="grid gap-4">
              {menu.map(item => (
                <div key={item.id} className="bg-white p-4 rounded-lg shadow border">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="font-semibold">{item.name}</h3>
                      <p className="text-gray-600 text-sm">{item.description}</p>
                      <p className="text-green-600 font-bold">${item.price}</p>
                    </div>
                    <button
                      onClick={() => addToCart(item)}
                      className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
                    >
                      Add to Cart
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-xl font-bold mb-4">Cart ({cart.length})</h3>
            {cart.map((item, index) => (
              <div key={index} className="flex justify-between items-center mb-2">
                <span>{item.name} x{item.quantity}</span>
                <span>${(item.price * item.quantity).toFixed(2)}</span>
              </div>
            ))}
            {cart.length > 0 && (
              <div className="border-t pt-2 mt-2">
                <div className="flex justify-between font-bold">
                  <span>Total: ${cart.reduce((sum, item) => sum + (item.price * item.quantity), 0).toFixed(2)}</span>
                </div>
                <button
                  onClick={placeOrder}
                  className="w-full bg-green-600 text-white py-2 px-4 rounded mt-2 hover:bg-green-700"
                >
                  Place Order
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">My Orders</h2>
        <div className="grid gap-4">
          {orders.map(order => (
            <div key={order.id} className="bg-white p-4 rounded-lg shadow border">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-semibold">Order #{order.id.slice(0, 8)}</p>
                  <p className="text-gray-600">Status: <span className={`font-semibold ${order.status === 'delivered' ? 'text-green-600' : 'text-orange-600'}`}>{order.status}</span></p>
                  <p className="text-gray-600">Total: ${order.total}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">{new Date(order.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <h2 className="text-2xl font-bold mb-4">Restaurants</h2>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {restaurants.map(restaurant => (
          <div
            key={restaurant.id}
            onClick={() => {setSelectedRestaurant(restaurant); fetchMenu(restaurant.id);}}
            className="bg-white p-6 rounded-lg shadow-lg cursor-pointer hover:shadow-xl transition-shadow"
          >
            <div className="mb-4">
              <h3 className="text-xl font-bold text-gray-800">{restaurant.name}</h3>
              <p className="text-gray-600">{restaurant.cuisine_type}</p>
              <p className="text-sm text-gray-500">{restaurant.description}</p>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-green-600 font-semibold">⭐ {restaurant.rating}</span>
              <span className="text-gray-600">{restaurant.estimated_delivery_time} min</span>
              <span className="text-gray-600">${restaurant.delivery_fee} delivery</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const DriverDashboard = () => {
  const [orders, setOrders] = useState([]);
  const [availableOrders, setAvailableOrders] = useState([]);
  const [ws, setWs] = useState(null);
  const { user } = React.useContext(UserContext);

  useEffect(() => {
    fetchOrders();
    setupWebSocket();
    // Start location tracking
    if (navigator.geolocation) {
      const watchId = navigator.geolocation.watchPosition(updateLocation);
      return () => navigator.geolocation.clearWatch(watchId);
    }
  }, []);

  const setupWebSocket = () => {
    const wsUrl = `${BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/ws/driver_${user.id}`;
    const websocket = new WebSocket(wsUrl);
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'new_order') {
        setAvailableOrders(prev => [...prev, data.order]);
        alert('New order available!');
      }
    };
    
    setWs(websocket);
    return () => websocket.close();
  };

  const updateLocation = async (position) => {
    const location = {
      lat: position.coords.latitude,
      lng: position.coords.longitude
    };

    try {
      await axios.post(`${API}/drivers/location`, location);
    } catch (error) {
      console.error('Error updating location:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const acceptOrder = async (orderId) => {
    try {
      await axios.post(`${API}/orders/${orderId}/assign-driver`);
      setAvailableOrders(prev => prev.filter(order => order.id !== orderId));
      fetchOrders();
      alert('Order accepted!');
    } catch (error) {
      alert(error.response?.data?.detail || 'Error accepting order');
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.put(`${API}/orders/${orderId}/status?status=${status}`);
      fetchOrders();
      alert(`Order marked as ${status}`);
    } catch (error) {
      alert(error.response?.data?.detail || 'Error updating order status');
    }
  };

  return (
    <div className="container mx-auto p-4">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Available Orders</h2>
        <div className="grid gap-4">
          {availableOrders.map(order => (
            <div key={order.id} className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-semibold">New Order #{order.id.slice(0, 8)}</p>
                  <p className="text-gray-600">Delivery to: {order.delivery_address}</p>
                  <p className="text-green-600 font-bold">Earnings: ${order.total}</p>
                </div>
                <button
                  onClick={() => acceptOrder(order.id)}
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                >
                  Accept Order
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <h2 className="text-2xl font-bold mb-4">My Active Orders</h2>
      <div className="grid gap-4">
        {orders.map(order => (
          <div key={order.id} className="bg-white p-4 rounded-lg shadow border">
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold">Order #{order.id.slice(0, 8)}</p>
                <p className="text-gray-600">Status: {order.status}</p>
                <p className="text-gray-600">Delivery to: {order.delivery_address}</p>
                <p className="text-green-600 font-bold">Total: ${order.total}</p>
              </div>
              <div className="space-x-2">
                {order.status === 'confirmed' && (
                  <button
                    onClick={() => updateOrderStatus(order.id, 'picked_up')}
                    className="bg-orange-600 text-white px-3 py-1 rounded hover:bg-orange-700"
                  >
                    Mark Picked Up
                  </button>
                )}
                {order.status === 'picked_up' && (
                  <button
                    onClick={() => updateOrderStatus(order.id, 'delivered')}
                    className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700"
                  >
                    Mark Delivered
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const RestaurantDashboard = () => {
  const [restaurant, setRestaurant] = useState(null);
  const [menu, setMenu] = useState([]);
  const [orders, setOrders] = useState([]);
  const [newMenuItem, setNewMenuItem] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    preparation_time: 15
  });
  const { user } = React.useContext(UserContext);

  useEffect(() => {
    fetchOrders();
  }, []);

  const createRestaurant = async (e) => {
    e.preventDefault();
    const restaurantData = {
      name: "My Restaurant",
      description: "Delicious food delivered fast",
      address: "123 Restaurant St, City, State",
      location: { lat: 40.7128, lng: -74.0060 },
      cuisine_type: "American",
      phone: "+1234567890"
    };

    try {
      const response = await axios.post(`${API}/restaurants`, restaurantData);
      setRestaurant(response.data);
      alert('Restaurant created successfully!');
    } catch (error) {
      alert(error.response?.data?.detail || 'Error creating restaurant');
    }
  };

  const addMenuItem = async (e) => {
    e.preventDefault();
    if (!restaurant) {
      alert('Please create a restaurant first');
      return;
    }

    try {
      const response = await axios.post(`${API}/restaurants/${restaurant.id}/menu`, {
        ...newMenuItem,
        price: parseFloat(newMenuItem.price)
      });
      setMenu([...menu, response.data]);
      setNewMenuItem({
        name: '',
        description: '',
        price: '',
        category: '',
        preparation_time: 15
      });
      alert('Menu item added successfully!');
    } catch (error) {
      alert(error.response?.data?.detail || 'Error adding menu item');
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.put(`${API}/orders/${orderId}/status?status=${status}`);
      fetchOrders();
      alert(`Order marked as ${status}`);
    } catch (error) {
      alert(error.response?.data?.detail || 'Error updating order status');
    }
  };

  return (
    <div className="container mx-auto p-4">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Restaurant Management</h2>
        
        {!restaurant && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Create Your Restaurant</h3>
            <button
              onClick={createRestaurant}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Create Restaurant
            </button>
          </div>
        )}

        {restaurant && (
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h3 className="text-lg font-semibold mb-4">Add Menu Item</h3>
            <form onSubmit={addMenuItem} className="grid md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Item Name"
                value={newMenuItem.name}
                onChange={(e) => setNewMenuItem({...newMenuItem, name: e.target.value})}
                className="border border-gray-300 rounded px-3 py-2"
                required
              />
              <input
                type="text"
                placeholder="Category"
                value={newMenuItem.category}
                onChange={(e) => setNewMenuItem({...newMenuItem, category: e.target.value})}
                className="border border-gray-300 rounded px-3 py-2"
                required
              />
              <input
                type="number"
                step="0.01"
                placeholder="Price"
                value={newMenuItem.price}
                onChange={(e) => setNewMenuItem({...newMenuItem, price: e.target.value})}
                className="border border-gray-300 rounded px-3 py-2"
                required
              />
              <input
                type="number"
                placeholder="Prep Time (minutes)"
                value={newMenuItem.preparation_time}
                onChange={(e) => setNewMenuItem({...newMenuItem, preparation_time: parseInt(e.target.value)})}
                className="border border-gray-300 rounded px-3 py-2"
              />
              <textarea
                placeholder="Description"
                value={newMenuItem.description}
                onChange={(e) => setNewMenuItem({...newMenuItem, description: e.target.value})}
                className="border border-gray-300 rounded px-3 py-2 md:col-span-2"
                required
              />
              <button
                type="submit"
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 md:col-span-2"
              >
                Add Menu Item
              </button>
            </form>
          </div>
        )}
      </div>

      <div className="mb-8">
        <h3 className="text-xl font-bold mb-4">Menu Items</h3>
        <div className="grid gap-4">
          {menu.map(item => (
            <div key={item.id} className="bg-white p-4 rounded-lg shadow border">
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="font-semibold">{item.name}</h4>
                  <p className="text-gray-600">{item.description}</p>
                  <p className="text-green-600 font-bold">${item.price}</p>
                </div>
                <span className="text-sm text-gray-500">{item.category}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xl font-bold mb-4">Incoming Orders</h3>
        <div className="grid gap-4">
          {orders.map(order => (
            <div key={order.id} className="bg-white p-4 rounded-lg shadow border">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-semibold">Order #{order.id.slice(0, 8)}</p>
                  <p className="text-gray-600">Status: {order.status}</p>
                  <p className="text-gray-600">Total: ${order.total}</p>
                  <p className="text-gray-600">Items: {order.items.length}</p>
                </div>
                <div className="space-x-2">
                  {order.status === 'pending' && (
                    <button
                      onClick={() => updateOrderStatus(order.id, 'confirmed')}
                      className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
                    >
                      Confirm
                    </button>
                  )}
                  {order.status === 'confirmed' && (
                    <button
                      onClick={() => updateOrderStatus(order.id, 'preparing')}
                      className="bg-orange-600 text-white px-3 py-1 rounded hover:bg-orange-700"
                    >
                      Start Preparing
                    </button>
                  )}
                  {order.status === 'preparing' && (
                    <button
                      onClick={() => updateOrderStatus(order.id, 'ready')}
                      className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700"
                    >
                      Ready for Pickup
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const AdminDashboard = () => {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  if (!analytics) {
    return <div className="container mx-auto p-4">Loading analytics...</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h2 className="text-2xl font-bold mb-6">Admin Dashboard</h2>
      
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-blue-500 text-white p-6 rounded-lg">
          <h3 className="text-lg font-semibold">Total Orders</h3>
          <p className="text-3xl font-bold">{analytics.total_orders}</p>
        </div>
        <div className="bg-green-500 text-white p-6 rounded-lg">
          <h3 className="text-lg font-semibold">Total Users</h3>
          <p className="text-3xl font-bold">{analytics.total_users}</p>
        </div>
        <div className="bg-purple-500 text-white p-6 rounded-lg">
          <h3 className="text-lg font-semibold">Restaurants</h3>
          <p className="text-3xl font-bold">{analytics.total_restaurants}</p>
        </div>
        <div className="bg-red-500 text-white p-6 rounded-lg">
          <h3 className="text-lg font-semibold">Revenue</h3>
          <p className="text-3xl font-bold">${analytics.total_revenue.toFixed(2)}</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Platform Overview</h3>
        <p>Completed Orders: {analytics.completed_orders}</p>
        <p>Average Order Value: ${analytics.total_orders > 0 ? (analytics.total_revenue / analytics.completed_orders).toFixed(2) : '0.00'}</p>
      </div>
    </div>
  );
};

const App = () => {
  const { user } = React.useContext(UserContext);

  const renderDashboard = () => {
    if (!user) return <LoginRegister />;

    switch (user.user_type) {
      case 'customer':
        return <CustomerDashboard />;
      case 'driver':
        return <DriverDashboard />;
      case 'restaurant':
        return <RestaurantDashboard />;
      case 'admin':
        return <AdminDashboard />;
      default:
        return <div>Unknown user type</div>;
    }
  };

  return (
    <UserProvider>
      <div className="min-h-screen bg-gray-100">
        <Navbar />
        {renderDashboard()}
      </div>
    </UserProvider>
  );
};

export default App;
