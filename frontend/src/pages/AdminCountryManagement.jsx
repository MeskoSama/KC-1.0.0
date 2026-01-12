import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Landmark, Plus, Edit2, Trash2, RefreshCw, TrendingUp, TrendingDown, PieChart, Palette } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const AdminCountryManagement = () => {
  const [countries, setCountries] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [independenceStatuses, setIndependenceStatuses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState(null);
  
  // Dialog states
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [incomeDialogOpen, setIncomeDialogOpen] = useState(false);
  const [expenseDialogOpen, setExpenseDialogOpen] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  
  // Form states
  const [newCountry, setNewCountry] = useState({
    id: '', name: '', currency: 'GRP', independence_status: 'independent country',
    treasury: 0, color: '#9333ea'
  });
  const [editData, setEditData] = useState({});
  const [incomeItems, setIncomeItems] = useState([]);
  const [expenseItems, setExpenseItems] = useState([]);
  const [economicShare, setEconomicShare] = useState({ bank_flow: 0, trade: 0, global_reserves: 0 });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [countriesRes, currenciesRes, statusesRes] = await Promise.all([
        axios.get(`${API}/countries`),
        axios.get(`${API}/currencies`),
        axios.get(`${API}/admin/countries/independence-statuses`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      setCountries(countriesRes.data.countries || []);
      setCurrencies(currenciesRes.data.currencies || []);
      setIndependenceStatuses(statusesRes.data.statuses || []);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load data');
    }
  };

  const formatNumber = (num) => {
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    return num.toLocaleString();
  };

  const handleAddCountry = async () => {
    if (!newCountry.id || !newCountry.name) {
      toast.error('Please fill in ID and Name');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/countries`, newCountry, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Country added successfully!');
      setAddDialogOpen(false);
      setNewCountry({ id: '', name: '', currency: 'GRP', independence_status: 'independent country', treasury: 0, color: '#9333ea' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add country');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateCountry = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/countries/${selectedCountry.id}`, editData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Country updated successfully!');
      setEditDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update country');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCountry = async (countryId) => {
    if (!window.confirm('Are you sure you want to delete this country?')) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/countries/${countryId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Country deleted successfully!');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete country');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateIncomeExpenses = async (type) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const items = type === 'income' ? incomeItems : expenseItems;
      await axios.put(`${API}/admin/countries/${selectedCountry.id}/income-expenses`, {
        country_id: selectedCountry.id,
        type,
        items
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`${type} updated successfully!`);
      if (type === 'income') setIncomeDialogOpen(false);
      else setExpenseDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || `Failed to update ${type}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateEconomicShare = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/countries/${selectedCountry.id}/economic-share`, {
        country_id: selectedCountry.id,
        ...economicShare
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Economic share updated successfully!');
      setShareDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update economic share');
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerTreasuryUpdate = async () => {
    if (!window.confirm('This will update all country treasuries based on weekly net income. Continue?')) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/countries/treasury-update`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(response.data.message);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update treasuries');
    } finally {
      setLoading(false);
    }
  };

  const handleInitializeCountries = async () => {
    if (!window.confirm('This will RESET all countries to defaults. Continue?')) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/countries/initialize`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(response.data.message);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to initialize countries');
    } finally {
      setLoading(false);
    }
  };

  const addIncomeItem = () => setIncomeItems([...incomeItems, { name: '', amount: 0 }]);
  const removeIncomeItem = (idx) => setIncomeItems(incomeItems.filter((_, i) => i !== idx));
  const updateIncomeItem = (idx, field, value) => {
    const updated = [...incomeItems];
    updated[idx][field] = field === 'amount' ? parseFloat(value) || 0 : value;
    setIncomeItems(updated);
  };

  const addExpenseItem = () => setExpenseItems([...expenseItems, { name: '', amount: 0 }]);
  const removeExpenseItem = (idx) => setExpenseItems(expenseItems.filter((_, i) => i !== idx));
  const updateExpenseItem = (idx, field, value) => {
    const updated = [...expenseItems];
    updated[idx][field] = field === 'amount' ? parseFloat(value) || 0 : value;
    setExpenseItems(updated);
  };

  const openEditDialog = (country) => {
    setSelectedCountry(country);
    setEditData({
      name: country.name,
      currency: country.currency,
      independence_status: country.independence_status,
      treasury: country.treasury,
      color: country.color
    });
    setEditDialogOpen(true);
  };

  const openIncomeDialog = (country) => {
    setSelectedCountry(country);
    setIncomeItems(country.income || []);
    setIncomeDialogOpen(true);
  };

  const openExpenseDialog = (country) => {
    setSelectedCountry(country);
    setExpenseItems(country.expenses || []);
    setExpenseDialogOpen(true);
  };

  const openShareDialog = (country) => {
    setSelectedCountry(country);
    setEconomicShare(country.economic_share || { bank_flow: 0, trade: 0, global_reserves: 0 });
    setShareDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <Card className="glass-card border-purple-600/20">
        <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-4">
          <div>
            <CardTitle className="text-2xl flex items-center gap-2">
              <Landmark className="text-purple-400" />
              Country Management
            </CardTitle>
            <CardDescription>Manage countries, treasuries, income/expenses, and economic shares</CardDescription>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button variant="outline" size="sm" onClick={handleTriggerTreasuryUpdate} disabled={loading}>
              <RefreshCw size={16} className="mr-1" />
              Update Treasuries
            </Button>
            <Button variant="outline" size="sm" onClick={handleInitializeCountries} disabled={loading}>
              <RefreshCw size={16} className="mr-1" />
              Reset to Defaults
            </Button>
            <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
              <DialogTrigger asChild>
                <Button className="btn-kapitalist" size="sm">
                  <Plus size={16} className="mr-1" />
                  Add Country
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-900 border-purple-600/30 max-w-md">
                <DialogHeader>
                  <DialogTitle>Add New Country</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>ID (unique)</Label>
                      <Input
                        placeholder="e.g., new_nation"
                        value={newCountry.id}
                        onChange={(e) => setNewCountry({ ...newCountry, id: e.target.value.toLowerCase().replace(/\s/g, '_') })}
                        className="bg-slate-800 border-slate-700"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Name</Label>
                      <Input
                        placeholder="e.g., New Nation"
                        value={newCountry.name}
                        onChange={(e) => setNewCountry({ ...newCountry, name: e.target.value })}
                        className="bg-slate-800 border-slate-700"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Currency</Label>
                      <Select value={newCountry.currency} onValueChange={(v) => setNewCountry({ ...newCountry, currency: v })}>
                        <SelectTrigger className="bg-slate-800 border-slate-700">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {currencies.map((c) => (
                            <SelectItem key={c} value={c}>{c}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Color</Label>
                      <div className="flex gap-2">
                        <Input
                          type="color"
                          value={newCountry.color}
                          onChange={(e) => setNewCountry({ ...newCountry, color: e.target.value })}
                          className="w-12 h-10 p-1 bg-slate-800 border-slate-700"
                        />
                        <Input
                          value={newCountry.color}
                          onChange={(e) => setNewCountry({ ...newCountry, color: e.target.value })}
                          className="bg-slate-800 border-slate-700 font-mono"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Independence Status</Label>
                    <Select value={newCountry.independence_status} onValueChange={(v) => setNewCountry({ ...newCountry, independence_status: v })}>
                      <SelectTrigger className="bg-slate-800 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {independenceStatuses.map((s) => (
                          <SelectItem key={s} value={s}>{s}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Initial Treasury</Label>
                    <Input
                      type="number"
                      value={newCountry.treasury}
                      onChange={(e) => setNewCountry({ ...newCountry, treasury: parseFloat(e.target.value) || 0 })}
                      className="bg-slate-800 border-slate-700"
                    />
                  </div>
                  <Button onClick={handleAddCountry} disabled={loading} className="w-full btn-kapitalist">
                    {loading ? 'Adding...' : 'Add Country'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
      </Card>

      {/* Countries Table */}
      <Card className="glass-card border-purple-600/20">
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Country</TableHead>
                <TableHead>Currency</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Treasury</TableHead>
                <TableHead className="text-right">Weekly Net</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {countries.map((country) => (
                <TableRow key={country.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: country.color }} />
                      <span className="font-bold">{country.name}</span>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-purple-400">{country.currency}</TableCell>
                  <TableCell className="text-xs">{country.independence_status}</TableCell>
                  <TableCell className="text-right font-mono text-green-400">
                    {formatNumber(country.treasury)}
                  </TableCell>
                  <TableCell className={`text-right font-mono ${(country.weekly_net || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {(country.weekly_net || 0) >= 0 ? '+' : ''}{formatNumber(country.weekly_net || 0)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex gap-1 justify-end flex-wrap">
                      <Button size="sm" variant="outline" onClick={() => openEditDialog(country)} title="Edit Basic Info">
                        <Edit2 size={14} />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => openIncomeDialog(country)} title="Edit Income" className="text-green-400 border-green-600/30">
                        <TrendingUp size={14} />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => openExpenseDialog(country)} title="Edit Expenses" className="text-red-400 border-red-600/30">
                        <TrendingDown size={14} />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => openShareDialog(country)} title="Edit Economic Share" className="text-blue-400 border-blue-600/30">
                        <PieChart size={14} />
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => handleDeleteCountry(country.id)} disabled={loading}>
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Edit Country Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="bg-slate-900 border-purple-600/30">
          <DialogHeader>
            <DialogTitle>Edit Country: {selectedCountry?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input
                value={editData.name || ''}
                onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Currency</Label>
                <Select value={editData.currency} onValueChange={(v) => setEditData({ ...editData, currency: v })}>
                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {currencies.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Color</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={editData.color || '#9333ea'}
                    onChange={(e) => setEditData({ ...editData, color: e.target.value })}
                    className="w-12 h-10 p-1 bg-slate-800 border-slate-700"
                  />
                  <Input
                    value={editData.color || ''}
                    onChange={(e) => setEditData({ ...editData, color: e.target.value })}
                    className="bg-slate-800 border-slate-700 font-mono"
                  />
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Independence Status</Label>
              <Select value={editData.independence_status} onValueChange={(v) => setEditData({ ...editData, independence_status: v })}>
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {independenceStatuses.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Treasury</Label>
              <Input
                type="number"
                value={editData.treasury || 0}
                onChange={(e) => setEditData({ ...editData, treasury: parseFloat(e.target.value) || 0 })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <Button onClick={handleUpdateCountry} disabled={loading} className="w-full btn-kapitalist">
              {loading ? 'Updating...' : 'Update Country'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Income Dialog */}
      <Dialog open={incomeDialogOpen} onOpenChange={setIncomeDialogOpen}>
        <DialogContent className="bg-slate-900 border-purple-600/30 max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-green-400">Edit Income: {selectedCountry?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {incomeItems.map((item, idx) => (
              <div key={idx} className="flex gap-2 items-center">
                <Input
                  placeholder="Income name"
                  value={item.name}
                  onChange={(e) => updateIncomeItem(idx, 'name', e.target.value)}
                  className="bg-slate-800 border-slate-700 flex-1"
                />
                <Input
                  type="number"
                  placeholder="Amount"
                  value={item.amount}
                  onChange={(e) => updateIncomeItem(idx, 'amount', e.target.value)}
                  className="bg-slate-800 border-slate-700 w-40"
                />
                <Button variant="destructive" size="sm" onClick={() => removeIncomeItem(idx)}>
                  <Trash2 size={14} />
                </Button>
              </div>
            ))}
            <Button variant="outline" onClick={addIncomeItem} className="w-full">
              <Plus size={16} className="mr-1" /> Add Income Item
            </Button>
            <Button onClick={() => handleUpdateIncomeExpenses('income')} disabled={loading} className="w-full btn-kapitalist">
              {loading ? 'Saving...' : 'Save Income'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Expenses Dialog */}
      <Dialog open={expenseDialogOpen} onOpenChange={setExpenseDialogOpen}>
        <DialogContent className="bg-slate-900 border-purple-600/30 max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-red-400">Edit Expenses: {selectedCountry?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {expenseItems.map((item, idx) => (
              <div key={idx} className="flex gap-2 items-center">
                <Input
                  placeholder="Expense name"
                  value={item.name}
                  onChange={(e) => updateExpenseItem(idx, 'name', e.target.value)}
                  className="bg-slate-800 border-slate-700 flex-1"
                />
                <Input
                  type="number"
                  placeholder="Amount"
                  value={item.amount}
                  onChange={(e) => updateExpenseItem(idx, 'amount', e.target.value)}
                  className="bg-slate-800 border-slate-700 w-40"
                />
                <Button variant="destructive" size="sm" onClick={() => removeExpenseItem(idx)}>
                  <Trash2 size={14} />
                </Button>
              </div>
            ))}
            <Button variant="outline" onClick={addExpenseItem} className="w-full">
              <Plus size={16} className="mr-1" /> Add Expense Item
            </Button>
            <Button onClick={() => handleUpdateIncomeExpenses('expenses')} disabled={loading} className="w-full btn-kapitalist">
              {loading ? 'Saving...' : 'Save Expenses'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Economic Share Dialog */}
      <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
        <DialogContent className="bg-slate-900 border-purple-600/30">
          <DialogHeader>
            <DialogTitle className="text-blue-400">Edit Economic Share: {selectedCountry?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Bank Account Flow Share (%)</Label>
              <Input
                type="number"
                step="0.01"
                value={economicShare.bank_flow}
                onChange={(e) => setEconomicShare({ ...economicShare, bank_flow: parseFloat(e.target.value) || 0 })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div className="space-y-2">
              <Label>Trade Share (%)</Label>
              <Input
                type="number"
                step="0.01"
                value={economicShare.trade}
                onChange={(e) => setEconomicShare({ ...economicShare, trade: parseFloat(e.target.value) || 0 })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div className="space-y-2">
              <Label>Global Reserves Share (%)</Label>
              <Input
                type="number"
                step="0.01"
                value={economicShare.global_reserves}
                onChange={(e) => setEconomicShare({ ...economicShare, global_reserves: parseFloat(e.target.value) || 0 })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <Button onClick={handleUpdateEconomicShare} disabled={loading} className="w-full btn-kapitalist">
              {loading ? 'Saving...' : 'Save Economic Share'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminCountryManagement;
