import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, TrendingDown, BarChart3, Activity } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const StockCharts = ({ user, onLogout }) => {
  const [investments, setInvestments] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [exchangeRates, setExchangeRates] = useState({});
  const [viewCurrency, setViewCurrency] = useState(user.currency_type);
  const [chartData, setChartData] = useState([]);
  const [currencyChartData, setCurrencyChartData] = useState([]);
  const [marketOverview, setMarketOverview] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadInvestments();
    loadExchangeRates();
    loadCurrencyHistory();
    loadMarketOverview();
  }, []);

  useEffect(() => {
    if (selectedStock) {
      generateStockChartData(selectedStock);
    }
  }, [selectedStock, viewCurrency]);

  const loadInvestments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/investments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInvestments(response.data.investments);
      if (response.data.investments.length > 0) {
        setSelectedStock(response.data.investments[0]);
      }
    } catch (error) {
      toast.error('Failed to load investments');
    }
  };

  const loadExchangeRates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/exchange-rates`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setExchangeRates(response.data.rates);
    } catch (error) {
      toast.error('Failed to load exchange rates');
    }
  };

  const convertPrice = (price, fromCurrency, toCurrency) => {
    if (fromCurrency === toCurrency) return price;
    const rateKey = `${fromCurrency}_TO_${toCurrency}`;
    const rate = exchangeRates[rateKey] || 1;
    return price * rate;
  };

  const generateStockChartData = (stock) => {
    // Generate realistic price history
    const data = [];
    const basePrice = stock.current_price;
    const now = new Date();
    
    for (let i = 30; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      // Simulate price fluctuation
      const fluctuation = (Math.random() - 0.5) * 0.1; // ±5% fluctuation
      const dayPrice = basePrice * (1 + (fluctuation * (i / 30)));
      const convertedPrice = convertPrice(dayPrice, stock.currency, viewCurrency);
      
      data.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        price: parseFloat(convertedPrice.toFixed(2)),
        volume: Math.floor(Math.random() * 10000) + 1000
      });
    }
    
    setChartData(data);
  };

  const generateCurrencyChartData = () => {
    // Generate currency exchange rate history
    const data = [];
    const now = new Date();
    
    for (let i = 30; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      data.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        NIM: 1.687 * (1 + (Math.random() - 0.5) * 0.05),
        GRP: 1,
        VDD: 2.366 * (1 + (Math.random() - 0.5) * 0.05),
        KKD: 2.614 * (1 + (Math.random() - 0.5) * 0.05)
      });
    }
    
    setCurrencyChartData(data);
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900 border border-purple-500 p-3 rounded-lg shadow-lg">
          <p className="text-slate-300 text-sm mb-1">{payload[0].payload.date}</p>
          <p className="text-purple-400 font-bold text-lg">
            {payload[0].value.toFixed(2)} {viewCurrency}
          </p>
          {payload[0].payload.volume && (
            <p className="text-slate-500 text-xs mt-1">Volume: {payload[0].payload.volume.toLocaleString()}</p>
          )}
        </div>
      );
    }
    return null;
  };

  const CurrencyTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900 border border-purple-500 p-3 rounded-lg shadow-lg">
          <p className="text-slate-300 text-sm mb-2">{payload[0].payload.date}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              <span className="font-bold">{entry.name}:</span> {entry.value.toFixed(4)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const priceChange = chartData.length > 0 ? 
    ((chartData[chartData.length - 1].price - chartData[0].price) / chartData[0].price * 100).toFixed(2) : 0;

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-4xl font-black mb-2">
            <span className="text-purple-400 glow-text">MARKET CHARTS</span>
          </h1>
          <p className="text-slate-400 text-lg">Real-time market data and price charts</p>
        </div>

        <Tabs defaultValue="stocks" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-slate-800/50 max-w-md">
            <TabsTrigger value="stocks">
              <TrendingUp size={18} className="mr-2" />
              Stock Charts
            </TabsTrigger>
            <TabsTrigger value="forex">
              <Activity size={18} className="mr-2" />
              Currency FX
            </TabsTrigger>
          </TabsList>

          <TabsContent value="stocks" className="mt-6 space-y-6">
            {/* Stock Selection and Info */}
            <Card className="glass-card border-purple-600/20">
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm text-slate-400">Select Stock</label>
                    <Select 
                      value={selectedStock?.symbol} 
                      onValueChange={(value) => {
                        const stock = investments.find(s => s.symbol === value);
                        setSelectedStock(stock);
                      }}
                    >
                      <SelectTrigger className="bg-slate-800 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {investments.map((stock) => (
                          <SelectItem key={stock.symbol} value={stock.symbol}>
                            {stock.symbol} - {stock.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-slate-400">View in Currency</label>
                    <Select value={viewCurrency} onValueChange={setViewCurrency}>
                      <SelectTrigger className="bg-slate-800 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NIM">NIM</SelectItem>
                        <SelectItem value="GRP">GRP</SelectItem>
                        <SelectItem value="VDD">VDD</SelectItem>
                        <SelectItem value="KKD">KKD</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-slate-400">30-Day Change</label>
                    <div className={`flex items-center gap-2 text-2xl font-black ${
                      parseFloat(priceChange) >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {parseFloat(priceChange) >= 0 ? (
                        <TrendingUp size={28} />
                      ) : (
                        <TrendingDown size={28} />
                      )}
                      {Math.abs(priceChange)}%
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Price Chart */}
            {selectedStock && (
              <Card className="glass-card border-purple-600/20">
                <CardHeader>
                  <CardTitle className="text-2xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <BarChart3 className="text-purple-400" size={32} />
                      <div>
                        <div className="text-2xl font-black text-purple-400">{selectedStock.symbol}</div>
                        <div className="text-sm text-slate-400 font-normal">{selectedStock.name}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-black text-white">
                        {convertPrice(selectedStock.current_price, selectedStock.currency, viewCurrency).toFixed(2)}
                      </div>
                      <div className="text-sm text-slate-500">{viewCurrency}</div>
                    </div>
                  </CardTitle>
                  <CardDescription>30-day price movement</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b45fa" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#8b45fa" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis 
                        dataKey="date" 
                        stroke="#94a3b8"
                        tick={{ fill: '#94a3b8' }}
                      />
                      <YAxis 
                        stroke="#94a3b8"
                        tick={{ fill: '#94a3b8' }}
                        domain={['dataMin - 10', 'dataMax + 10']}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Area 
                        type="monotone" 
                        dataKey="price" 
                        stroke="#8b45fa" 
                        strokeWidth={3}
                        fillOpacity={1}
                        fill="url(#colorPrice)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="forex" className="mt-6">
            <Card className="glass-card border-purple-600/20">
              <CardHeader>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <Activity className="text-purple-400" />
                  Currency Exchange Rates (Base: GRP)
                </CardTitle>
                <CardDescription>30-day currency movement relative to GRP</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={500}>
                  <LineChart data={currencyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#94a3b8"
                      tick={{ fill: '#94a3b8' }}
                    />
                    <YAxis 
                      stroke="#94a3b8"
                      tick={{ fill: '#94a3b8' }}
                    />
                    <Tooltip content={<CurrencyTooltip />} />
                    <Legend 
                      wrapperStyle={{ color: '#94a3b8' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="NIM" 
                      stroke="#10b981" 
                      strokeWidth={3}
                      dot={{ fill: '#10b981', r: 4 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="VDD" 
                      stroke="#f59e0b" 
                      strokeWidth={3}
                      dot={{ fill: '#f59e0b', r: 4 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="KKD" 
                      stroke="#ef4444" 
                      strokeWidth={3}
                      dot={{ fill: '#ef4444', r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>

                {/* Currency Stats */}
                <div className="grid grid-cols-3 gap-4 mt-6">
                  <div className="p-4 bg-green-600/10 border border-green-600/30 rounded-lg">
                    <div className="text-sm text-slate-400 mb-1">NIM/GRP</div>
                    <div className="text-2xl font-bold text-green-400">{exchangeRates.GRP_TO_NIM?.toFixed(4)}</div>
                  </div>
                  <div className="p-4 bg-amber-600/10 border border-amber-600/30 rounded-lg">
                    <div className="text-sm text-slate-400 mb-1">VDD/GRP</div>
                    <div className="text-2xl font-bold text-amber-400">{exchangeRates.GRP_TO_VDD?.toFixed(4)}</div>
                  </div>
                  <div className="p-4 bg-red-600/10 border border-red-600/30 rounded-lg">
                    <div className="text-sm text-slate-400 mb-1">KKD/GRP</div>
                    <div className="text-2xl font-bold text-red-400">{exchangeRates.GRP_TO_KKD?.toFixed(4)}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default StockCharts;
