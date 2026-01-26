import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Plus, Edit2, Trash2, Power, PowerOff } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const AdminInvestments = () => {
  const [investments, setInvestments] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [newPrice, setNewPrice] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // New stock form
  const [newStock, setNewStock] = useState({
    symbol: '',
    name: '',
    currency: 'GRP',
    current_price: 0,
    type: 'stock'
  });

  useEffect(() => {
    loadInvestments();
  }, []);

  const loadInvestments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/investments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInvestments(response.data.investments || []);
    } catch (error) {
      toast.error('Failed to load investments');
    }
  };

  const handleUpdatePrice = async () => {
    if (!newPrice || parseFloat(newPrice) < 0) {
      toast.error('Please enter a valid price');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API}/admin/investment/price`,
        {
          symbol: selectedStock.symbol,
          new_price: parseFloat(newPrice)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Updated ${selectedStock.symbol} price to ${newPrice}`);
      setDialogOpen(false);
      setNewPrice('');
      loadInvestments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update price');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStock = async () => {
    if (!newStock.symbol || !newStock.name || newStock.current_price <= 0) {
      toast.error('Please fill all fields correctly');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/admin/investment/create`,
        newStock,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Created ${newStock.symbol} successfully!`);
      setCreateDialogOpen(false);
      setNewStock({ symbol: '', name: '', currency: 'GRP', current_price: 0, type: 'stock' });
      loadInvestments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create stock');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (stock) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API}/admin/investment/status`,
        {
          symbol: stock.symbol,
          disabled: !stock.disabled
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`${stock.symbol} ${stock.disabled ? 'enabled' : 'disabled'}`);
      loadInvestments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update status');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteStock = async (stock) => {
    if (!window.confirm(`Delete ${stock.symbol}? This cannot be undone.`)) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(
        `${API}/admin/investment/${stock.symbol}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Deleted ${stock.symbol}`);
      loadInvestments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete stock');
    } finally {
      setLoading(false);
    }
  };

  const groupedByCurrency = investments.reduce((acc, inv) => {
    if (!acc[inv.currency]) acc[inv.currency] = [];
    acc[inv.currency].push(inv);
    return acc;
  }, {});

  const currencies = ['GRP', 'NIM', 'VDD', 'KKD', 'EGD', 'EP'];

  return (
    <Card className="glass-card border-purple-600/20">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-2xl flex items-center gap-2">
            <TrendingUp className="text-purple-400" />
            Investment Management
          </CardTitle>
          <CardDescription>
            Create, update, and manage stocks and bonds
          </CardDescription>
        </div>
        
        {/* Create Stock Button */}
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-kapitalist">
              <Plus size={16} className="mr-2" /> Add New Stock/Bond
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-slate-900 border-purple-600/30">
            <DialogHeader>
              <DialogTitle className="text-2xl">Create New Stock/Bond</DialogTitle>
              <DialogDescription>
                Add a new investment to the marketplace
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Symbol</Label>
                  <Input
                    placeholder="e.g., GRP-NEWSTOCK"
                    value={newStock.symbol}
                    onChange={(e) => setNewStock({ ...newStock, symbol: e.target.value.toUpperCase() })}
                    className="bg-slate-800 border-slate-700"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Currency</Label>
                  <Select value={newStock.currency} onValueChange={(v) => setNewStock({ ...newStock, currency: v })}>
                    <SelectTrigger className="bg-slate-800 border-slate-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {currencies.map(c => (
                        <SelectItem key={c} value={c}>{c}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Name</Label>
                <Input
                  placeholder="e.g., New Company Stock"
                  value={newStock.name}
                  onChange={(e) => setNewStock({ ...newStock, name: e.target.value })}
                  className="bg-slate-800 border-slate-700"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Initial Price</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={newStock.current_price}
                    onChange={(e) => setNewStock({ ...newStock, current_price: parseFloat(e.target.value) || 0 })}
                    className="bg-slate-800 border-slate-700"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Type</Label>
                  <Select value={newStock.type} onValueChange={(v) => setNewStock({ ...newStock, type: v })}>
                    <SelectTrigger className="bg-slate-800 border-slate-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="stock">📈 Stock</SelectItem>
                      <SelectItem value="bond">📜 Bond (Hazine)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="p-4 bg-purple-600/10 border border-purple-600/30 rounded-lg">
                <p className="text-sm text-slate-400">Preview:</p>
                <p className="font-bold text-lg text-purple-400">
                  {newStock.type === 'bond' ? '📜' : '📈'} {newStock.symbol || 'SYMBOL'}: {newStock.name || 'Name'}
                </p>
                <p className="text-sm">
                  Price: {newStock.current_price} {newStock.currency}
                </p>
              </div>
              
              <Button
                onClick={handleCreateStock}
                disabled={loading}
                className="w-full btn-kapitalist"
              >
                {loading ? 'Creating...' : 'Create Stock/Bond'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-6">
          {currencies.map(currency => {
            const stocks = groupedByCurrency[currency] || [];
            if (stocks.length === 0) return null;
            
            return (
              <div key={currency} className="space-y-3">
                <h3 className="text-lg font-bold text-purple-400">
                  {currency} Stocks ({stocks.length})
                </h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Symbol</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Current Price</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stocks.map((stock) => (
                      <TableRow key={stock.symbol} className={stock.disabled ? 'opacity-50' : ''}>
                        <TableCell className="font-bold text-purple-400">{stock.symbol}</TableCell>
                        <TableCell>{stock.name}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={stock.type === 'bond' ? 'text-yellow-400' : 'text-green-400'}>
                            {stock.type === 'bond' ? '📜 Bond' : '📈 Stock'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-bold">
                          {stock.current_price?.toFixed(2)} {currency}
                        </TableCell>
                        <TableCell>
                          {stock.disabled ? (
                            <Badge variant="destructive">Disabled</Badge>
                          ) : (
                            <Badge className="bg-green-600">Active</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex gap-1 justify-end">
                            <Dialog open={dialogOpen && selectedStock?.symbol === stock.symbol} onOpenChange={(open) => {
                              setDialogOpen(open);
                              if (open) {
                                setSelectedStock(stock);
                                setNewPrice(stock.current_price?.toString() || '0');
                              }
                            }}>
                              <DialogTrigger asChild>
                                <Button size="sm" variant="outline">
                                  <Edit2 size={14} className="mr-1" /> Price
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="bg-slate-900 border-purple-600/30">
                                <DialogHeader>
                                  <DialogTitle className="text-2xl">Update {stock.name}</DialogTitle>
                                  <DialogDescription>
                                    Current: {stock.current_price?.toFixed(2)} {currency}
                                  </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4">
                                  <div className="space-y-2">
                                    <Label>New Price ({currency})</Label>
                                    <Input
                                      type="number"
                                      step="0.01"
                                      min="0"
                                      value={newPrice}
                                      onChange={(e) => setNewPrice(e.target.value)}
                                      className="bg-slate-800 border-slate-700"
                                    />
                                  </div>
                                  
                                  <div className="p-4 bg-purple-600/10 border border-purple-600/30 rounded-lg">
                                    <div className="flex justify-between mb-2">
                                      <span className="text-slate-400">Old Price:</span>
                                      <span className="font-bold">{stock.current_price?.toFixed(2)} {currency}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-400">New Price:</span>
                                      <span className="font-bold text-purple-400">{newPrice || '0.00'} {currency}</span>
                                    </div>
                                    <div className="flex justify-between mt-2 pt-2 border-t border-slate-700">
                                      <span className="text-slate-400">Change:</span>
                                      <span className={`font-bold ${
                                        (parseFloat(newPrice) - stock.current_price) > 0 ? 'text-green-400' : 'text-red-400'
                                      }`}>
                                        {stock.current_price > 0 ? ((parseFloat(newPrice) - stock.current_price) / stock.current_price * 100).toFixed(2) : 0}%
                                      </span>
                                    </div>
                                  </div>
                                  
                                  <Button
                                    onClick={handleUpdatePrice}
                                    disabled={loading}
                                    className="w-full btn-kapitalist"
                                  >
                                    {loading ? 'Updating...' : 'Confirm Update'}
                                  </Button>
                                </div>
                              </DialogContent>
                            </Dialog>
                            
                            <Button 
                              size="sm" 
                              variant={stock.disabled ? "default" : "secondary"}
                              onClick={() => handleToggleStatus(stock)}
                              disabled={loading}
                            >
                              {stock.disabled ? <Power size={14} /> : <PowerOff size={14} />}
                            </Button>
                            
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleDeleteStock(stock)}
                              disabled={loading}
                            >
                              <Trash2 size={14} />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            );
          })}
          
          {investments.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              No investments found. Click "Add New Stock/Bond" to create one.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default AdminInvestments;
