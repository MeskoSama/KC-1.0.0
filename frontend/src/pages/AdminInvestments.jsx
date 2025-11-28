import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { TrendingUp } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const AdminInvestments = () => {
  const [investments, setInvestments] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [newPrice, setNewPrice] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadInvestments();
  }, []);

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

  const groupedByurrency = investments.reduce((acc, inv) => {
    if (!acc[inv.currency]) acc[inv.currency] = [];
    acc[inv.currency].push(inv);
    return acc;
  }, {});

  return (
    <Card className="glass-card border-purple-600/20">
      <CardHeader>
        <CardTitle className="text-2xl flex items-center gap-2">
          <TrendingUp className="text-purple-400" />
          Investment Price Management
        </CardTitle>
        <CardDescription>
          Update stock and bond prices - changes reflect immediately on charts
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {Object.entries(groupedByCurrency).map(([currency, stocks]) => (
            <div key={currency} className="space-y-3">
              <h3 className="text-lg font-bold text-purple-400">{currency} Stocks</h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead className="text-right">Current Price</TableHead>
                    <TableHead className="text-right">Last Updated</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stocks.map((stock) => (
                    <TableRow key={stock.symbol}>
                      <TableCell className="font-bold text-purple-400">{stock.symbol}</TableCell>
                      <TableCell>{stock.name}</TableCell>
                      <TableCell className="text-right font-bold">
                        {stock.current_price.toFixed(2)} {currency}
                      </TableCell>
                      <TableCell className="text-right text-sm text-slate-500">
                        {stock.last_updated ? new Date(stock.last_updated).toLocaleString() : 'N/A'}
                      </TableCell>
                      <TableCell className="text-right">
                        <Dialog open={dialogOpen && selectedStock?.symbol === stock.symbol} onOpenChange={(open) => {
                          setDialogOpen(open);
                          if (open) {
                            setSelectedStock(stock);
                            setNewPrice(stock.current_price.toString());
                          }
                        }}>
                          <DialogTrigger asChild>
                            <Button size="sm" className="btn-kapitalist">
                              Update Price
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="bg-slate-900 border-purple-600/30">
                            <DialogHeader>
                              <DialogTitle className="text-2xl">Update {stock.name}</DialogTitle>
                              <DialogDescription>
                                Current: {stock.current_price.toFixed(2)} {currency}
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
                                  <span className="font-bold">{stock.current_price.toFixed(2)} {currency}</span>
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
                                    {((parseFloat(newPrice) - stock.current_price) / stock.current_price * 100).toFixed(2)}%
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
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default AdminInvestments;
