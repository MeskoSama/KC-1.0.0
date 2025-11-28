import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ArrowRightLeft } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const AdminExchangeRates = () => {
  const [rates, setRates] = useState({});
  const [selectedRate, setSelectedRate] = useState(null);
  const [newRate, setNewRate] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRates();
  }, []);

  const loadRates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/exchange-rates`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRates(response.data.rates);
    } catch (error) {
      toast.error('Failed to load exchange rates');
    }
  };

  const handleUpdateRate = async () => {
    if (!newRate || parseFloat(newRate) <= 0) {
      toast.error('Please enter a valid rate');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API}/admin/exchange-rate`,
        {
          rate_key: selectedRate.key,
          new_rate: parseFloat(newRate)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Updated ${selectedRate.key} to ${newRate}`);
      setDialogOpen(false);
      setNewRate('');
      loadRates();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update rate');
    } finally {
      setLoading(false);
    }
  };

  const formatRateKey = (key) => {
    const parts = key.split('_TO_');
    return `${parts[0]} → ${parts[1]}`;
  };

  const rateEntries = Object.entries(rates).filter(([key]) => !key.includes('USD'));
  const usdRates = Object.entries(rates).filter(([key]) => key.includes('USD'));

  return (
    <Card className="glass-card border-purple-600/20">
      <CardHeader>
        <CardTitle className="text-2xl flex items-center gap-2">
          <ArrowRightLeft className="text-purple-400" />
          Exchange Rate Management
        </CardTitle>
        <CardDescription>
          Manage currency exchange rates - changes affect all conversions immediately
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Currency to Currency Rates */}
        <div>
          <h3 className="text-lg font-bold text-purple-400 mb-3">Currency Exchange Rates</h3>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Exchange Pair</TableHead>
                <TableHead className="text-right">Current Rate</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rateEntries.map(([key, value]) => (
                <TableRow key={key}>
                  <TableCell className="font-bold">{formatRateKey(key)}</TableCell>
                  <TableCell className="text-right font-bold text-purple-400">
                    {value.toFixed(6)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Dialog open={dialogOpen && selectedRate?.key === key} onOpenChange={(open) => {
                      setDialogOpen(open);
                      if (open) {
                        setSelectedRate({ key, value });
                        setNewRate(value.toString());
                      }
                    }}>
                      <DialogTrigger asChild>
                        <Button size="sm" className="btn-kapitalist">
                          Edit Rate
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="bg-slate-900 border-purple-600/30">
                        <DialogHeader>
                          <DialogTitle className="text-2xl">Update {formatRateKey(key)}</DialogTitle>
                          <DialogDescription>
                            Current rate: {value.toFixed(6)}
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div className="space-y-2">
                            <Label>New Rate</Label>
                            <Input
                              type="number"
                              step="0.000001"
                              min="0"
                              value={newRate}
                              onChange={(e) => setNewRate(e.target.value)}
                              className="bg-slate-800 border-slate-700"
                            />
                          </div>
                          
                          <div className="p-4 bg-purple-600/10 border border-purple-600/30 rounded-lg">
                            <div className="flex justify-between mb-2">
                              <span className="text-slate-400">Old Rate:</span>
                              <span className="font-bold">{value.toFixed(6)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-400">New Rate:</span>
                              <span className="font-bold text-purple-400">{newRate || '0.000000'}</span>
                            </div>
                            <div className="flex justify-between mt-2 pt-2 border-t border-slate-700">
                              <span className="text-slate-400">Change:</span>
                              <span className={`font-bold ${
                                (parseFloat(newRate) - value) > 0 ? 'text-green-400' : 'text-red-400'
                              }`}>
                                {((parseFloat(newRate) - value) / value * 100).toFixed(2)}%
                              </span>
                            </div>
                          </div>
                          
                          <Button
                            onClick={handleUpdateRate}
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

        {/* USD Conversion Rates */}
        <div>
          <h3 className="text-lg font-bold text-purple-400 mb-3">USD Conversion Rates</h3>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Exchange Pair</TableHead>
                <TableHead className="text-right">Current Rate</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {usdRates.map(([key, value]) => (
                <TableRow key={key}>
                  <TableCell className="font-bold">{formatRateKey(key)}</TableCell>
                  <TableCell className="text-right font-bold text-green-400">
                    {value.toFixed(8)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Dialog open={dialogOpen && selectedRate?.key === key} onOpenChange={(open) => {
                      setDialogOpen(open);
                      if (open) {
                        setSelectedRate({ key, value });
                        setNewRate(value.toString());
                      }
                    }}>
                      <DialogTrigger asChild>
                        <Button size="sm" className="btn-kapitalist">
                          Edit Rate
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="bg-slate-900 border-purple-600/30">
                        <DialogHeader>
                          <DialogTitle className="text-2xl">Update {formatRateKey(key)}</DialogTitle>
                          <DialogDescription>
                            Current rate: {value.toFixed(8)}
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div className="space-y-2">
                            <Label>New Rate</Label>
                            <Input
                              type="number"
                              step="0.00000001"
                              min="0"
                              value={newRate}
                              onChange={(e) => setNewRate(e.target.value)}
                              className="bg-slate-800 border-slate-700"
                            />
                          </div>
                          
                          <Button
                            onClick={handleUpdateRate}
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
      </CardContent>
    </Card>
  );
};

export default AdminExchangeRates;
