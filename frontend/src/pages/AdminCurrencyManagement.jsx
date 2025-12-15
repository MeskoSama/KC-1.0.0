import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Coins, Plus, Edit2, Trash2, RefreshCw, ArrowRightLeft } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const AdminCurrencyManagement = () => {
  const [currencies, setCurrencies] = useState([]);
  const [currencyNames, setCurrencyNames] = useState({});
  const [exchangeRates, setExchangeRates] = useState({});
  const [loading, setLoading] = useState(false);
  
  // Add currency dialog
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newCurrency, setNewCurrency] = useState({ code: '', name: '', base_rate_to_grp: 1 });
  
  // Edit currency dialog
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editCurrency, setEditCurrency] = useState({ code: '', name: '', base_rate_to_grp: 1 });
  
  // Edit rate dialog
  const [rateDialogOpen, setRateDialogOpen] = useState(false);
  const [editRate, setEditRate] = useState({ from_currency: '', to_currency: '', rate: 1 });

  useEffect(() => {
    loadCurrencyData();
  }, []);

  const loadCurrencyData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [currenciesRes, ratesRes] = await Promise.all([
        axios.get(`${API}/currencies`),
        axios.get(`${API}/currencies/rates`)
      ]);
      
      setCurrencies(currenciesRes.data.currencies || []);
      setCurrencyNames(currenciesRes.data.names || {});
      setExchangeRates(ratesRes.data.rates || {});
    } catch (error) {
      toast.error('Failed to load currency data');
    }
  };

  const handleAddCurrency = async () => {
    if (!newCurrency.code || !newCurrency.name || newCurrency.base_rate_to_grp <= 0) {
      toast.error('Please fill all fields with valid values');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/currencies`, newCurrency, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Currency ${newCurrency.code.toUpperCase()} added successfully!`);
      setAddDialogOpen(false);
      setNewCurrency({ code: '', name: '', base_rate_to_grp: 1 });
      loadCurrencyData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add currency');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateCurrency = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/currencies`, editCurrency, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Currency ${editCurrency.code} updated successfully!`);
      setEditDialogOpen(false);
      loadCurrencyData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update currency');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCurrency = async (code) => {
    if (!window.confirm(`Are you sure you want to delete ${code}?`)) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/currencies/${code}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Currency ${code} deleted successfully!`);
      loadCurrencyData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete currency');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRate = async () => {
    if (editRate.rate <= 0) {
      toast.error('Rate must be positive');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/exchange-rate/direct`, editRate, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Exchange rate updated successfully!');
      setRateDialogOpen(false);
      loadCurrencyData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update rate');
    } finally {
      setLoading(false);
    }
  };

  const handleInitialize = async () => {
    if (!window.confirm('This will reset all currencies and rates to defaults. Continue?')) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/currencies/initialize`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Currency system initialized!');
      loadCurrencyData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to initialize');
    } finally {
      setLoading(false);
    }
  };

  const handleMigrateBalances = async () => {
    if (!window.confirm('This will add EP and EGD balances (set to 0) to all users. Continue?')) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/users/migrate-balances`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Migrated ${response.data.users_updated} users!`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to migrate balances');
    } finally {
      setLoading(false);
    }
  };

  const getRate = (from, to) => {
    const key = `${from}_TO_${to}`;
    return exchangeRates[key]?.toFixed(5) || '-';
  };

  const baseCurrencies = ['NIM', 'GRP', 'VDD', 'KKD'];

  return (
    <div className="space-y-6">
      {/* Currency List */}
      <Card className="glass-card border-purple-600/20">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-2xl flex items-center gap-2">
              <Coins className="text-purple-400" />
              Currency Management
            </CardTitle>
            <CardDescription>Manage all currencies in the system</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleMigrateBalances} disabled={loading}>
              <RefreshCw size={16} className="mr-1" />
              Migrate User Balances
            </Button>
            <Button variant="outline" size="sm" onClick={handleInitialize} disabled={loading}>
              <RefreshCw size={16} className="mr-1" />
              Initialize Defaults
            </Button>
            <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
              <DialogTrigger asChild>
                <Button className="btn-kapitalist" size="sm">
                  <Plus size={16} className="mr-1" />
                  Add Currency
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-900 border-purple-600/30">
                <DialogHeader>
                  <DialogTitle>Add New Currency</DialogTitle>
                  <DialogDescription>Add a new currency to the system</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Currency Code</Label>
                    <Input
                      placeholder="e.g., USD, EUR"
                      value={newCurrency.code}
                      onChange={(e) => setNewCurrency({ ...newCurrency, code: e.target.value.toUpperCase() })}
                      className="bg-slate-800 border-slate-700"
                      maxLength={5}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Display Name</Label>
                    <Input
                      placeholder="e.g., US Dollar"
                      value={newCurrency.name}
                      onChange={(e) => setNewCurrency({ ...newCurrency, name: e.target.value })}
                      className="bg-slate-800 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>1 GRP = X {newCurrency.code || 'NEW'}</Label>
                    <Input
                      type="number"
                      step="0.00001"
                      min="0.00001"
                      value={newCurrency.base_rate_to_grp}
                      onChange={(e) => setNewCurrency({ ...newCurrency, base_rate_to_grp: parseFloat(e.target.value) || 0 })}
                      className="bg-slate-800 border-slate-700"
                    />
                    <p className="text-xs text-slate-500">How many of the new currency equals 1 GRP</p>
                  </div>
                  <Button onClick={handleAddCurrency} disabled={loading} className="w-full btn-kapitalist">
                    {loading ? 'Adding...' : 'Add Currency'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead className="text-right">1 GRP = X</TableHead>
                <TableHead className="text-right">Type</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currencies.map((code) => {
                const isBase = baseCurrencies.includes(code);
                const grpRate = exchangeRates[`GRP_TO_${code}`] || 1;
                
                return (
                  <TableRow key={code}>
                    <TableCell className="font-bold text-purple-400">{code}</TableCell>
                    <TableCell>{currencyNames[code] || code}</TableCell>
                    <TableCell className="text-right font-mono">{grpRate.toFixed(5)}</TableCell>
                    <TableCell className="text-right">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        isBase ? 'bg-blue-600/20 text-blue-400' : 'bg-green-600/20 text-green-400'
                      }`}>
                        {isBase ? 'Base' : 'Custom'}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-2 justify-end">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setEditCurrency({
                              code,
                              name: currencyNames[code] || code,
                              base_rate_to_grp: grpRate
                            });
                            setEditDialogOpen(true);
                          }}
                        >
                          <Edit2 size={14} />
                        </Button>
                        {!isBase && (
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleDeleteCurrency(code)}
                            disabled={loading}
                          >
                            <Trash2 size={14} />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Edit Currency Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="bg-slate-900 border-purple-600/30">
          <DialogHeader>
            <DialogTitle>Edit Currency: {editCurrency.code}</DialogTitle>
            <DialogDescription>Update currency name and rate</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Display Name</Label>
              <Input
                value={editCurrency.name || ''}
                onChange={(e) => setEditCurrency({ ...editCurrency, name: e.target.value })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div className="space-y-2">
              <Label>1 GRP = X {editCurrency.code}</Label>
              <Input
                type="number"
                step="0.00001"
                min="0.00001"
                value={editCurrency.base_rate_to_grp || 1}
                onChange={(e) => setEditCurrency({ ...editCurrency, base_rate_to_grp: parseFloat(e.target.value) || 0 })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <Button onClick={handleUpdateCurrency} disabled={loading} className="w-full btn-kapitalist">
              {loading ? 'Updating...' : 'Update Currency'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Exchange Rate Matrix */}
      <Card className="glass-card border-purple-600/20">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-2xl flex items-center gap-2">
              <ArrowRightLeft className="text-purple-400" />
              Exchange Rate Matrix
            </CardTitle>
            <CardDescription>View and edit all exchange rates (1 ROW = X COLUMN)</CardDescription>
          </div>
          <Dialog open={rateDialogOpen} onOpenChange={setRateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="btn-kapitalist" size="sm">
                <Edit2 size={16} className="mr-1" />
                Edit Rate
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-slate-900 border-purple-600/30">
              <DialogHeader>
                <DialogTitle>Edit Exchange Rate</DialogTitle>
                <DialogDescription>Update a specific exchange rate</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>From Currency</Label>
                  <Select value={editRate.from_currency} onValueChange={(v) => setEditRate({ ...editRate, from_currency: v })}>
                    <SelectTrigger className="bg-slate-800 border-slate-700">
                      <SelectValue placeholder="Select currency" />
                    </SelectTrigger>
                    <SelectContent>
                      {currencies.map((c) => (
                        <SelectItem key={c} value={c}>{c}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>To Currency</Label>
                  <Select value={editRate.to_currency} onValueChange={(v) => setEditRate({ ...editRate, to_currency: v })}>
                    <SelectTrigger className="bg-slate-800 border-slate-700">
                      <SelectValue placeholder="Select currency" />
                    </SelectTrigger>
                    <SelectContent>
                      {currencies.map((c) => (
                        <SelectItem key={c} value={c}>{c}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Rate (1 {editRate.from_currency || 'FROM'} = X {editRate.to_currency || 'TO'})</Label>
                  <Input
                    type="number"
                    step="0.00001"
                    min="0.00001"
                    value={editRate.rate}
                    onChange={(e) => setEditRate({ ...editRate, rate: parseFloat(e.target.value) || 0 })}
                    className="bg-slate-800 border-slate-700"
                  />
                </div>
                <Button onClick={handleUpdateRate} disabled={loading} className="w-full btn-kapitalist">
                  {loading ? 'Updating...' : 'Update Rate'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="font-bold">FROM ↓ / TO →</TableHead>
                  {currencies.map((code) => (
                    <TableHead key={code} className="text-center font-bold text-purple-400">{code}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {currencies.map((fromCode) => (
                  <TableRow key={fromCode}>
                    <TableCell className="font-bold text-purple-400">{fromCode}</TableCell>
                    {currencies.map((toCode) => (
                      <TableCell key={toCode} className="text-center font-mono text-sm">
                        {fromCode === toCode ? (
                          <span className="text-slate-500">1.00000</span>
                        ) : (
                          <span className="text-green-400">{getRate(fromCode, toCode)}</span>
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminCurrencyManagement;
