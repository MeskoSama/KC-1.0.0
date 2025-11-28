import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TrendingUp, TrendingDown, BarChart3, ShoppingCart, DollarSign } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const Investments = ({ user, onLogout, onUpdateUser }) => {
  const [investments, setInvestments] = useState([]);
  const [filteredInvestments, setFilteredInvestments] = useState([]);
  const [selectedCurrency, setSelectedCurrency] = useState('ALL');
  const [viewCurrency, setViewCurrency] = useState(user.currency_type);
  const [exchangeRates, setExchangeRates] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [buyDialogOpen, setBuyDialogOpen] = useState(false);
  const [sellDialogOpen, setSellDialogOpen] = useState(false);
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    loadInvestments();
    loadExchangeRates();
  }, []);

  useEffect(() => {
    filterInvestments();
  }, [selectedCurrency, investments]);

  const loadInvestments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/investments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInvestments(response.data.investments);
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

  const filterInvestments = () => {
    if (selectedCurrency === 'ALL') {
      setFilteredInvestments(investments);
    } else {
      setFilteredInvestments(investments.filter(inv => inv.currency === selectedCurrency));
    }
  };

  const convertPrice = (price, fromCurrency) => {
    if (fromCurrency === viewCurrency) return price;
    
    const rateKey = `${fromCurrency}_TO_${viewCurrency}`;
    const rate = exchangeRates[rateKey] || 1;
    return price * rate;
  };

  const handleBuy = async () => {
    if (!quantity || quantity <= 0) {
      toast.error('Please enter a valid quantity');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/investments/buy`,
        {
          symbol: selectedStock.symbol,
          quantity: parseFloat(quantity)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Bought ${quantity} shares of ${selectedStock.name}`);
      setBuyDialogOpen(false);
      setQuantity(1);
      loadInvestments();
      onUpdateUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Purchase failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSell = async () => {
    if (!quantity || quantity <= 0) {
      toast.error('Please enter a valid quantity');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/investments/sell`,
        {
          symbol: selectedStock.symbol,
          quantity: parseFloat(quantity)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Sold ${quantity} shares of ${selectedStock.name}`);
      setSellDialogOpen(false);
      setQuantity(1);
      loadInvestments();
      onUpdateUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Sale failed');
    } finally {
      setLoading(false);
    }
  };

  const getPortfolioQuantity = (symbol) => {
    return user.portfolio?.[symbol] || 0;
  };

  const calculateTotal = (price, qty) => {
    const total = price * qty;
    const commission = total * 0.00001; // 0.001%
    return { total, commission, final: total + commission };
  };

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black mb-2">
              <span className="text-purple-400 glow-text">INVESTMENT MARKET</span>
            </h1>
            <p className="text-slate-400 text-lg">Trade stocks and treasury bonds</p>
          </div>
          <div className="flex gap-4">
            <Select value={selectedCurrency} onValueChange={setSelectedCurrency}>
              <SelectTrigger className="w-32 bg-slate-800 border-slate-700">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All</SelectItem>
                <SelectItem value="NIM">NIM</SelectItem>
                <SelectItem value="GRP">GRP</SelectItem>
                <SelectItem value="VDD">VDD</SelectItem>
                <SelectItem value="KKD">KKD</SelectItem>
              </SelectContent>
            </Select>
            <Select value={viewCurrency} onValueChange={setViewCurrency}>
              <SelectTrigger className="w-40 bg-slate-800 border-slate-700">
                <SelectValue placeholder="View in" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="NIM">View in NIM</SelectItem>
                <SelectItem value="GRP">View in GRP</SelectItem>
                <SelectItem value="VDD">View in VDD</SelectItem>
                <SelectItem value="KKD">View in KKD</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <Card className="glass-card border-purple-600/20">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center gap-2">
              <BarChart3 className="text-purple-400" />
              Stock Market Chart
            </CardTitle>
            <CardDescription>
              Live prices • Commission: 0.001% (Buy/Sell) • 0.01% (Transfer)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">#</TableHead>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Currency</TableHead>
                    <TableHead className="text-right">Price</TableHead>
                    <TableHead className="text-right">Price in {viewCurrency}</TableHead>
                    <TableHead className="text-right">Owned</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredInvestments.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center text-slate-500 py-8">
                        No investments available
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredInvestments.map((stock, index) => {
                      const convertedPrice = convertPrice(stock.current_price, stock.currency);
                      const owned = getPortfolioQuantity(stock.symbol);
                      
                      return (
                        <TableRow key={stock.symbol} className="hover:bg-purple-900/10">
                          <TableCell className="font-medium">{index + 1}</TableCell>
                          <TableCell>
                            <span className="font-bold text-purple-400">{stock.symbol}</span>
                          </TableCell>
                          <TableCell className="font-medium text-red-500">{stock.name}</TableCell>
                          <TableCell>
                            <span className="px-2 py-1 bg-slate-700 rounded text-xs font-bold">
                              {stock.currency}
                            </span>
                          </TableCell>
                          <TableCell className="text-right font-bold">
                            {stock.current_price.toFixed(2)} {stock.currency}
                          </TableCell>
                          <TableCell className="text-right font-bold text-purple-400">
                            {convertedPrice.toFixed(2)} {viewCurrency}
                          </TableCell>
                          <TableCell className="text-right">
                            <span className={`font-bold ${owned > 0 ? 'text-green-400' : 'text-slate-500'}`}>
                              {owned.toFixed(2)}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex gap-2 justify-end">
                              <Dialog open={buyDialogOpen && selectedStock?.symbol === stock.symbol} onOpenChange={(open) => {
                                setBuyDialogOpen(open);
                                if (open) setSelectedStock(stock);
                              }}>
                                <DialogTrigger asChild>
                                  <Button
                                    size="sm"
                                    className="bg-green-600 hover:bg-green-700"
                                    onClick={() => setSelectedStock(stock)}
                                  >
                                    Buy
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="bg-slate-900 border-purple-600/30">
                                  <DialogHeader>
                                    <DialogTitle className="text-2xl">Buy {stock.name}</DialogTitle>
                                    <DialogDescription>
                                      Current price: {stock.current_price.toFixed(2)} {stock.currency}
                                    </DialogDescription>
                                  </DialogHeader>
                                  <div className="space-y-4">
                                    <div className="space-y-2">
                                      <Label>Quantity</Label>
                                      <Input
                                        type="number"
                                        min="0.01"
                                        step="0.01"
                                        value={quantity}
                                        onChange={(e) => setQuantity(e.target.value)}
                                        className="bg-slate-800 border-slate-700"
                                      />
                                    </div>
                                    
                                    {quantity > 0 && (
                                      <div className="p-4 bg-purple-600/10 border border-purple-600/30 rounded-lg space-y-2">
                                        <div className="flex justify-between text-sm">
                                          <span className="text-slate-400">Subtotal:</span>
                                          <span className="font-bold">
                                            {(stock.current_price * quantity).toFixed(2)} {stock.currency}
                                          </span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                          <span className="text-slate-400">Commission (0.001%):</span>
                                          <span className="font-bold">
                                            {(stock.current_price * quantity * 0.00001).toFixed(4)} {stock.currency}
                                          </span>
                                        </div>
                                        <div className="flex justify-between text-lg border-t border-slate-700 pt-2">
                                          <span className="text-white font-bold">Total:</span>
                                          <span className="font-black text-purple-400">
                                            {(stock.current_price * quantity * 1.00001).toFixed(2)} {stock.currency}
                                          </span>
                                        </div>
                                        <div className="text-xs text-slate-500 text-center mt-2">
                                          Your balance: {user.balances[stock.currency]?.toFixed(2)} {stock.currency}
                                        </div>
                                      </div>
                                    )}
                                    
                                    <Button
                                      onClick={handleBuy}
                                      disabled={loading || !quantity || quantity <= 0}
                                      className="w-full btn-kapitalist"
                                    >
                                      {loading ? 'Processing...' : 'Confirm Purchase'}
                                    </Button>
                                  </div>
                                </DialogContent>
                              </Dialog>

                              <Dialog open={sellDialogOpen && selectedStock?.symbol === stock.symbol} onOpenChange={(open) => {
                                setSellDialogOpen(open);
                                if (open) setSelectedStock(stock);
                              }}>
                                <DialogTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="border-red-600 text-red-400 hover:bg-red-950"
                                    disabled={owned === 0}
                                    onClick={() => setSelectedStock(stock)}
                                  >
                                    Sell
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="bg-slate-900 border-purple-600/30">
                                  <DialogHeader>
                                    <DialogTitle className="text-2xl">Sell {stock.name}</DialogTitle>
                                    <DialogDescription>
                                      You own: {owned.toFixed(2)} shares
                                    </DialogDescription>
                                  </DialogHeader>
                                  <div className="space-y-4">
                                    <div className="space-y-2">
                                      <Label>Quantity</Label>
                                      <Input
                                        type="number"
                                        min="0.01"
                                        step="0.01"
                                        max={owned}
                                        value={quantity}
                                        onChange={(e) => setQuantity(e.target.value)}
                                        className="bg-slate-800 border-slate-700"
                                      />
                                    </div>
                                    
                                    {quantity > 0 && (
                                      <div className="p-4 bg-green-600/10 border border-green-600/30 rounded-lg space-y-2">
                                        <div className="flex justify-between text-sm">
                                          <span className="text-slate-400">Subtotal:</span>
                                          <span className="font-bold">
                                            {(stock.current_price * quantity).toFixed(2)} {stock.currency}
                                          </span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                          <span className="text-slate-400">Commission (0.001%):</span>
                                          <span className="font-bold">
                                            {(stock.current_price * quantity * 0.00001).toFixed(4)} {stock.currency}
                                          </span>
                                        </div>
                                        <div className="flex justify-between text-lg border-t border-slate-700 pt-2">
                                          <span className="text-white font-bold">You'll receive:</span>
                                          <span className="font-black text-green-400">
                                            {(stock.current_price * quantity * 0.99999).toFixed(2)} {stock.currency}
                                          </span>
                                        </div>
                                      </div>
                                    )}
                                    
                                    <Button
                                      onClick={handleSell}
                                      disabled={loading || !quantity || quantity <= 0 || quantity > owned}
                                      className="w-full bg-red-600 hover:bg-red-700"
                                    >
                                      {loading ? 'Processing...' : 'Confirm Sale'}
                                    </Button>
                                  </div>
                                </DialogContent>
                              </Dialog>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Investments;
