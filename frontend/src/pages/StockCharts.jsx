import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Brush, ReferenceLine } from 'recharts';
import { TrendingUp, TrendingDown, BarChart3, Activity, ZoomIn, ZoomOut, RefreshCw, Calendar } from 'lucide-react';
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
  
  // Zoom and range state
  const [timeRange, setTimeRange] = useState(30); // days
  const [zoomLevel, setZoomLevel] = useState(100); // percentage
  const [chartType, setChartType] = useState('area'); // area, line, candlestick

  useEffect(() => {
    loadInvestments();
    loadExchangeRates();
    loadCurrencyHistory();
    loadMarketOverview();
  }, []);

  useEffect(() => {
    if (selectedStock) {
      loadStockHistory(selectedStock.symbol);
    }
  }, [selectedStock, viewCurrency, timeRange]);

  const loadInvestments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/investments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInvestments(response.data.investments || []);
      if (response.data.investments?.length > 0) {
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
      setExchangeRates(response.data.rates || {});
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

  const loadStockHistory = async (symbol) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/stocks/${symbol}/history?days=${timeRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const history = response.data.history || [];
      const stockCurrency = response.data.currency;
      
      // If no history, generate sample data points
      if (history.length < 2) {
        const currentPrice = selectedStock?.current_price || 100;
        const sampleData = generateSampleHistory(currentPrice, timeRange, stockCurrency);
        setChartData(sampleData);
        return;
      }
      
      // Transform data for chart
      const transformedData = history.map((point, idx) => {
        const date = new Date(point.timestamp);
        const convertedPrice = convertPrice(point.price, stockCurrency, viewCurrency);
        
        // Calculate moving average
        let ma5 = convertedPrice;
        let ma20 = convertedPrice;
        if (idx >= 4) {
          ma5 = history.slice(idx - 4, idx + 1).reduce((sum, p) => sum + convertPrice(p.price, stockCurrency, viewCurrency), 0) / 5;
        }
        if (idx >= 19) {
          ma20 = history.slice(idx - 19, idx + 1).reduce((sum, p) => sum + convertPrice(p.price, stockCurrency, viewCurrency), 0) / 20;
        }
        
        return {
          date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          fullDate: date.toISOString(),
          price: parseFloat(convertedPrice.toFixed(4)),
          originalPrice: point.price,
          change: point.change || 0,
          ma5: parseFloat(ma5.toFixed(4)),
          ma20: parseFloat(ma20.toFixed(4)),
          volume: Math.floor(Math.random() * 100000) + 10000 // Simulated volume
        };
      });
      
      setChartData(transformedData);
    } catch (error) {
      console.error('Failed to load stock history:', error);
      // Generate sample data on error
      const currentPrice = selectedStock?.current_price || 100;
      const sampleData = generateSampleHistory(currentPrice, timeRange, selectedStock?.currency || 'GRP');
      setChartData(sampleData);
    } finally {
      setLoading(false);
    }
  };

  const generateSampleHistory = (currentPrice, days, currency) => {
    const data = [];
    let price = currentPrice * 0.95; // Start slightly lower
    
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      // Create realistic price movement
      const volatility = 0.02; // 2% daily volatility
      const trend = (Math.random() - 0.48) * volatility; // Slight upward bias
      const noise = (Math.random() - 0.5) * volatility * 0.5;
      
      price = price * (1 + trend + noise);
      price = Math.max(price, 0.01); // Prevent negative
      
      const convertedPrice = convertPrice(price, currency, viewCurrency);
      
      data.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        fullDate: date.toISOString(),
        price: parseFloat(convertedPrice.toFixed(4)),
        originalPrice: price,
        change: trend * 100,
        volume: Math.floor(Math.random() * 100000) + 10000
      });
    }
    
    return data;
  };

  const loadCurrencyHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/currency/history?days=${timeRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const history = response.data.history || [];
      
      const transformedData = history.map(point => {
        const date = new Date(point.timestamp);
        const rates = point.rates || {};
        
        return {
          date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          NIM: rates.GRP_TO_NIM || 1,
          VDD: rates.GRP_TO_VDD || 1,
          KKD: rates.GRP_TO_KKD || 1,
          EGD: rates.GRP_TO_EGD || 1,
          EP: rates.GRP_TO_EP || 1,
          GRP: 1
        };
      });
      
      setCurrencyChartData(transformedData);
    } catch (error) {
      console.error('Failed to load currency history:', error);
    }
  };

  const loadMarketOverview = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/market/overview`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMarketOverview(response.data);
    } catch (error) {
      console.error('Failed to load market overview:', error);
    }
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900/95 border border-purple-500 p-4 rounded-lg shadow-xl backdrop-blur">
          <p className="text-slate-300 text-sm mb-2 font-medium">{data.date}</p>
          <div className="space-y-1">
            <p className="text-purple-400 font-bold text-xl">
              {payload[0].value?.toFixed(4)} {viewCurrency}
            </p>
            {data.originalPrice && viewCurrency !== selectedStock?.currency && (
              <p className="text-slate-500 text-xs">
                Original: {data.originalPrice?.toFixed(4)} {selectedStock?.currency}
              </p>
            )}
            {data.change !== undefined && (
              <p className={`text-sm font-medium ${data.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {data.change >= 0 ? '▲' : '▼'} {Math.abs(data.change).toFixed(2)}%
              </p>
            )}
            {data.volume && (
              <p className="text-slate-500 text-xs mt-2">
                Volume: {data.volume.toLocaleString()}
              </p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  const CurrencyTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900/95 border border-purple-500 p-4 rounded-lg shadow-xl backdrop-blur">
          <p className="text-slate-300 text-sm mb-2 font-medium">{payload[0].payload.date}</p>
          <div className="space-y-1">
            {payload.map((entry, index) => (
              <p key={index} className="text-sm flex justify-between gap-4" style={{ color: entry.color }}>
                <span className="font-medium">{entry.name}:</span>
                <span>{entry.value?.toFixed(4)}</span>
              </p>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  const priceChange = chartData.length > 1 ? 
    ((chartData[chartData.length - 1].price - chartData[0].price) / chartData[0].price * 100) : 0;

  const minPrice = chartData.length > 0 ? Math.min(...chartData.map(d => d.price)) * 0.98 : 0;
  const maxPrice = chartData.length > 0 ? Math.max(...chartData.map(d => d.price)) * 1.02 : 100;

  // Get visible data based on zoom
  const visibleDataCount = Math.max(Math.floor(chartData.length * (zoomLevel / 100)), 5);
  const visibleData = chartData.slice(-visibleDataCount);

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-6">
          <h1 className="text-4xl font-black mb-2">
            <span className="text-purple-400 glow-text">MARKET CHARTS</span>
          </h1>
          <p className="text-slate-400 text-lg">Real-time market data and price charts</p>
        </div>

        {/* Market Overview */}
        {marketOverview && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Top Gainers */}
            <Card className="glass-card border-green-600/20">
              <CardHeader className="py-3">
                <CardTitle className="text-lg flex items-center gap-2 text-green-400">
                  <TrendingUp size={20} />
                  Top Gainers
                </CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <div className="space-y-2">
                  {(marketOverview.top_gainers || []).slice(0, 5).map((stock) => (
                    <div 
                      key={stock.symbol} 
                      className="flex items-center justify-between p-2 bg-green-600/5 border border-green-600/20 rounded-lg cursor-pointer hover:bg-green-600/10"
                      onClick={() => {
                        const found = investments.find(i => i.symbol === stock.symbol);
                        if (found) setSelectedStock(found);
                      }}
                    >
                      <div>
                        <div className="font-bold text-white text-sm">{stock.symbol}</div>
                        <div className="text-xs text-slate-500">{stock.name}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-green-400">+{stock.change_percent?.toFixed(2)}%</div>
                        <div className="text-xs text-slate-400">{stock.current_price?.toFixed(2)} {stock.currency}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Top Losers */}
            <Card className="glass-card border-red-600/20">
              <CardHeader className="py-3">
                <CardTitle className="text-lg flex items-center gap-2 text-red-400">
                  <TrendingDown size={20} />
                  Top Losers
                </CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <div className="space-y-2">
                  {(marketOverview.top_losers || []).slice(0, 5).map((stock) => (
                    <div 
                      key={stock.symbol} 
                      className="flex items-center justify-between p-2 bg-red-600/5 border border-red-600/20 rounded-lg cursor-pointer hover:bg-red-600/10"
                      onClick={() => {
                        const found = investments.find(i => i.symbol === stock.symbol);
                        if (found) setSelectedStock(found);
                      }}
                    >
                      <div>
                        <div className="font-bold text-white text-sm">{stock.symbol}</div>
                        <div className="text-xs text-slate-500">{stock.name}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-red-400">{stock.change_percent?.toFixed(2)}%</div>
                        <div className="text-xs text-slate-400">{stock.current_price?.toFixed(2)} {stock.currency}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <Tabs defaultValue="stocks" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-slate-800/50 max-w-md mb-6">
            <TabsTrigger value="stocks">
              <TrendingUp size={18} className="mr-2" />
              Stock Charts
            </TabsTrigger>
            <TabsTrigger value="currency">
              <Activity size={18} className="mr-2" />
              Currency Rates
            </TabsTrigger>
          </TabsList>

          <TabsContent value="stocks">
            <Card className="glass-card border-purple-600/20">
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <Select 
                      value={selectedStock?.symbol || ''} 
                      onValueChange={(v) => setSelectedStock(investments.find(i => i.symbol === v))}
                    >
                      <SelectTrigger className="w-60 bg-slate-800/50 border-slate-700">
                        <SelectValue placeholder="Select stock" />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-700 max-h-80">
                        {['GRP', 'NIM', 'VDD', 'KKD', 'EGD', 'EP'].map(currency => {
                          const currencyStocks = investments.filter(i => i.currency === currency);
                          if (currencyStocks.length === 0) return null;
                          return (
                            <React.Fragment key={currency}>
                              <div className="px-2 py-1 text-xs font-bold text-purple-400 bg-slate-800">{currency} Stocks</div>
                              {currencyStocks.map(stock => (
                                <SelectItem key={stock.symbol} value={stock.symbol}>
                                  {stock.symbol} - {stock.name}
                                </SelectItem>
                              ))}
                            </React.Fragment>
                          );
                        })}
                      </SelectContent>
                    </Select>
                    
                    {selectedStock && (
                      <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold text-white">
                          {selectedStock.current_price?.toFixed(2)}
                        </span>
                        <span className="text-slate-400">{selectedStock.currency}</span>
                        <Badge className={priceChange >= 0 ? 'bg-green-600' : 'bg-red-600'}>
                          {priceChange >= 0 ? '▲' : '▼'} {Math.abs(priceChange).toFixed(2)}%
                        </Badge>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-4">
                    {/* Time Range Selector */}
                    <div className="flex items-center gap-2">
                      <Calendar size={16} className="text-slate-400" />
                      <Select value={timeRange.toString()} onValueChange={(v) => setTimeRange(parseInt(v))}>
                        <SelectTrigger className="w-28 bg-slate-800/50 border-slate-700">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-900 border-slate-700">
                          <SelectItem value="7">7 Days</SelectItem>
                          <SelectItem value="14">14 Days</SelectItem>
                          <SelectItem value="30">30 Days</SelectItem>
                          <SelectItem value="60">60 Days</SelectItem>
                          <SelectItem value="90">90 Days</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    {/* View Currency */}
                    <Select value={viewCurrency} onValueChange={setViewCurrency}>
                      <SelectTrigger className="w-24 bg-slate-800/50 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-700">
                        {['GRP', 'NIM', 'VDD', 'KKD', 'EGD', 'EP'].map(c => (
                          <SelectItem key={c} value={c}>{c}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    {/* Chart Type */}
                    <Select value={chartType} onValueChange={setChartType}>
                      <SelectTrigger className="w-28 bg-slate-800/50 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-700">
                        <SelectItem value="area">Area</SelectItem>
                        <SelectItem value="line">Line</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Button variant="outline" size="icon" onClick={() => loadStockHistory(selectedStock?.symbol)}>
                      <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                    </Button>
                  </div>
                </div>
                
                {/* Zoom Control */}
                <div className="flex items-center gap-4 mt-4 pt-4 border-t border-slate-700">
                  <ZoomOut size={16} className="text-slate-400" />
                  <Slider
                    value={[zoomLevel]}
                    onValueChange={(v) => setZoomLevel(v[0])}
                    min={20}
                    max={100}
                    step={5}
                    className="w-48"
                  />
                  <ZoomIn size={16} className="text-slate-400" />
                  <span className="text-sm text-slate-400 min-w-16">{zoomLevel}% view</span>
                  
                  <div className="flex gap-2 ml-auto">
                    <Button size="sm" variant={zoomLevel === 100 ? "default" : "outline"} onClick={() => setZoomLevel(100)}>All</Button>
                    <Button size="sm" variant={zoomLevel === 50 ? "default" : "outline"} onClick={() => setZoomLevel(50)}>50%</Button>
                    <Button size="sm" variant={zoomLevel === 25 ? "default" : "outline"} onClick={() => setZoomLevel(25)}>25%</Button>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                {loading ? (
                  <div className="h-96 flex items-center justify-center">
                    <RefreshCw className="animate-spin text-purple-400" size={32} />
                  </div>
                ) : (
                  <div className="h-96">
                    <ResponsiveContainer width="100%" height="100%">
                      {chartType === 'area' ? (
                        <AreaChart data={visibleData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                          <defs>
                            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#9333ea" stopOpacity={0.4}/>
                              <stop offset="95%" stopColor="#9333ea" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                          <XAxis 
                            dataKey="date" 
                            stroke="#64748b" 
                            tick={{ fill: '#94a3b8', fontSize: 11 }}
                            tickLine={{ stroke: '#475569' }}
                          />
                          <YAxis 
                            stroke="#64748b" 
                            tick={{ fill: '#94a3b8', fontSize: 11 }}
                            tickLine={{ stroke: '#475569' }}
                            domain={[minPrice, maxPrice]}
                            tickFormatter={(v) => v.toFixed(2)}
                          />
                          <Tooltip content={<CustomTooltip />} />
                          <ReferenceLine y={chartData[0]?.price} stroke="#6366f1" strokeDasharray="3 3" label={{ value: 'Start', fill: '#6366f1', fontSize: 10 }} />
                          <Area 
                            type="monotone" 
                            dataKey="price" 
                            stroke="#9333ea" 
                            strokeWidth={2}
                            fillOpacity={1} 
                            fill="url(#colorPrice)" 
                            dot={visibleData.length < 30}
                            activeDot={{ r: 6, fill: '#9333ea', stroke: '#fff', strokeWidth: 2 }}
                          />
                        </AreaChart>
                      ) : (
                        <LineChart data={visibleData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                          <XAxis 
                            dataKey="date" 
                            stroke="#64748b" 
                            tick={{ fill: '#94a3b8', fontSize: 11 }}
                          />
                          <YAxis 
                            stroke="#64748b" 
                            tick={{ fill: '#94a3b8', fontSize: 11 }}
                            domain={[minPrice, maxPrice]}
                            tickFormatter={(v) => v.toFixed(2)}
                          />
                          <Tooltip content={<CustomTooltip />} />
                          <ReferenceLine y={chartData[0]?.price} stroke="#6366f1" strokeDasharray="3 3" />
                          <Line 
                            type="monotone" 
                            dataKey="price" 
                            stroke="#9333ea" 
                            strokeWidth={2}
                            dot={visibleData.length < 30}
                            activeDot={{ r: 6, fill: '#9333ea', stroke: '#fff', strokeWidth: 2 }}
                          />
                        </LineChart>
                      )}
                    </ResponsiveContainer>
                  </div>
                )}
                
                {/* Price Statistics */}
                {chartData.length > 0 && (
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6 pt-6 border-t border-slate-700">
                    <div className="p-3 bg-slate-800/30 rounded-lg">
                      <p className="text-slate-400 text-xs">Current</p>
                      <p className="text-white font-bold">{chartData[chartData.length - 1]?.price.toFixed(4)} {viewCurrency}</p>
                    </div>
                    <div className="p-3 bg-slate-800/30 rounded-lg">
                      <p className="text-slate-400 text-xs">Period High</p>
                      <p className="text-green-400 font-bold">{Math.max(...chartData.map(d => d.price)).toFixed(4)} {viewCurrency}</p>
                    </div>
                    <div className="p-3 bg-slate-800/30 rounded-lg">
                      <p className="text-slate-400 text-xs">Period Low</p>
                      <p className="text-red-400 font-bold">{Math.min(...chartData.map(d => d.price)).toFixed(4)} {viewCurrency}</p>
                    </div>
                    <div className="p-3 bg-slate-800/30 rounded-lg">
                      <p className="text-slate-400 text-xs">Average</p>
                      <p className="text-purple-400 font-bold">{(chartData.reduce((s, d) => s + d.price, 0) / chartData.length).toFixed(4)} {viewCurrency}</p>
                    </div>
                    <div className="p-3 bg-slate-800/30 rounded-lg">
                      <p className="text-slate-400 text-xs">Change ({timeRange}d)</p>
                      <p className={`font-bold ${priceChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="currency">
            <Card className="glass-card border-purple-600/20">
              <CardHeader>
                <CardTitle className="text-xl flex items-center gap-2">
                  <Activity className="text-purple-400" />
                  Currency Exchange Rates (vs GRP)
                </CardTitle>
                <CardDescription>Historical currency exchange rates over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-96">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={currencyChartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="date" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <Tooltip content={<CurrencyTooltip />} />
                      <Legend />
                      <Line type="monotone" dataKey="NIM" stroke="#ef4444" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="VDD" stroke="#22c55e" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="KKD" stroke="#3b82f6" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="EGD" stroke="#f59e0b" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="EP" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
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
