import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Shield, TrendingUp, Users, Home, Target, DollarSign, Settings, FileText, ArrowRightLeft } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import AdminInvestments from './AdminInvestments';
import AdminExchangeRates from './AdminExchangeRates';

const AdminPanel = ({ user, onLogout }) => {
  const [stats, setStats] = useState({});
  const [users, setUsers] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [logs, setLogs] = useState([]);
  const [pendingHouses, setPendingHouses] = useState([]);
  const [currencyRates, setCurrencyRates] = useState({});
  const [loading, setLoading] = useState(false);
  
  const [balanceUpdate, setBalanceUpdate] = useState({
    user_id: '',
    currency: 'NIM',
    amount: 0,
    operation: 'add'
  });

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [statsRes, usersRes, txRes, logsRes, housesRes, ratesRes] = await Promise.all([
        axios.get(`${API}/admin/stats`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/users?limit=20`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/transactions?limit=20`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/logs?limit=50`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/houses/pending`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/currency-rates`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setStats(statsRes.data);
      setUsers(usersRes.data.users);
      setTransactions(txRes.data.transactions);
      setLogs(logsRes.data.logs);
      setPendingHouses(housesRes.data.houses);
      setCurrencyRates(ratesRes.data.rates);
    } catch (error) {
      toast.error('Failed to load admin data');
    }
  };

  const handleUpdateCurrencyRates = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/currency-rates`, currencyRates, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Currency rates updated successfully!');
      loadAdminData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update rates');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateBalance = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/user/balance`, balanceUpdate, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('User balance updated successfully!');
      loadAdminData();
      setBalanceUpdate({ user_id: '', currency: 'NIM', amount: 0, operation: 'add' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update balance');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveHouse = async (houseId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/houses/${houseId}/approve`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('House approved!');
      loadAdminData();
    } catch (error) {
      toast.error('Failed to approve house');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteHouse = async (houseId) => {
    if (!window.confirm('Are you sure you want to delete this house?')) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/houses/${houseId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('House deleted!');
      loadAdminData();
    } catch (error) {
      toast.error('Failed to delete house');
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    { title: 'Total Users', value: stats.total_users || 0, icon: Users, color: 'purple' },
    { title: 'Total Revenue', value: `$${(stats.total_revenue || 0).toFixed(2)}`, icon: DollarSign, color: 'green' },
    { title: 'Transactions', value: stats.total_transactions || 0, icon: TrendingUp, color: 'blue' },
    { title: 'Houses', value: stats.total_houses || 0, icon: Home, color: 'yellow' },
    { title: 'Pending Houses', value: stats.pending_houses || 0, icon: Home, color: 'red' },
    { title: 'Bounties', value: stats.total_bounties || 0, icon: Target, color: 'orange' },
  ];

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8 flex items-center gap-3">
          <Shield size={40} className="text-purple-400" />
          <div>
            <h1 className="text-4xl font-black">
              <span className="text-purple-400 glow-text">ADMIN CONTROL ROOM</span>
            </h1>
            <p className="text-slate-400 text-lg">Total website control & management</p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {statCards.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div key={index} className="stat-card" data-testid={`admin-stat-${stat.title.toLowerCase().replace(' ', '-')}`}>
                <div className="flex items-center justify-between mb-4">
                  <Icon size={32} className="text-purple-400" />
                  <div className="text-3xl font-black text-purple-400">{stat.value}</div>
                </div>
                <h3 className="text-slate-400 font-medium">{stat.title}</h3>
              </div>
            );
          })}
        </div>

        <Tabs defaultValue="rates" className="w-full">
          <TabsList className="grid w-full grid-cols-5 bg-slate-900/50">
            <TabsTrigger value="rates" data-testid="admin-tab-rates"><Settings size={18} className="mr-2" />Rates</TabsTrigger>
            <TabsTrigger value="users" data-testid="admin-tab-users"><Users size={18} className="mr-2" />Users</TabsTrigger>
            <TabsTrigger value="houses" data-testid="admin-tab-houses"><Home size={18} className="mr-2" />Houses</TabsTrigger>
            <TabsTrigger value="transactions" data-testid="admin-tab-transactions"><TrendingUp size={18} className="mr-2" />Transactions</TabsTrigger>
            <TabsTrigger value="logs" data-testid="admin-tab-logs"><FileText size={18} className="mr-2" />Logs</TabsTrigger>
          </TabsList>

          <TabsContent value="rates" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="glass-card border-purple-600/20">
                <CardHeader>
                  <CardTitle className="text-2xl">Update Currency Rates</CardTitle>
                  <CardDescription>Modify exchange rates (Base: 1 GRP)</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleUpdateCurrencyRates} className="space-y-4">
                    <div className="space-y-2">
                      <Label>1 GRP = X NIM</Label>
                      <Input
                        type="number"
                        step="0.00001"
                        value={currencyRates.GRP_TO_NIM || 0}
                        onChange={(e) => setCurrencyRates({ ...currencyRates, GRP_TO_NIM: parseFloat(e.target.value) })}
                        className="bg-slate-800 border-slate-700"
                        data-testid="rate-grp-nim"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>1 GRP = X VDD</Label>
                      <Input
                        type="number"
                        step="0.00001"
                        value={currencyRates.GRP_TO_VDD || 0}
                        onChange={(e) => setCurrencyRates({ ...currencyRates, GRP_TO_VDD: parseFloat(e.target.value) })}
                        className="bg-slate-800 border-slate-700"
                        data-testid="rate-grp-vdd"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>1 GRP = X KKD</Label>
                      <Input
                        type="number"
                        step="0.00001"
                        value={currencyRates.GRP_TO_KKD || 0}
                        onChange={(e) => setCurrencyRates({ ...currencyRates, GRP_TO_KKD: parseFloat(e.target.value) })}
                        className="bg-slate-800 border-slate-700"
                        data-testid="rate-grp-kkd"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>1 GRP = X USD</Label>
                      <Input
                        type="number"
                        step="0.000001"
                        value={currencyRates.GRP_TO_USD || 0}
                        onChange={(e) => setCurrencyRates({ ...currencyRates, GRP_TO_USD: parseFloat(e.target.value) })}
                        className="bg-slate-800 border-slate-700"
                        data-testid="rate-grp-usd"
                      />
                    </div>
                    <Button type="submit" disabled={loading} className="w-full btn-kapitalist" data-testid="update-rates-button">
                      {loading ? 'Updating...' : 'Update Rates'}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="glass-card border-purple-600/20">
                <CardHeader>
                  <CardTitle className="text-2xl">Update User Balance</CardTitle>
                  <CardDescription>Add or set user currency balance</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleUpdateBalance} className="space-y-4">
                    <div className="space-y-2">
                      <Label>User ID</Label>
                      <Select value={balanceUpdate.user_id} onValueChange={(value) => setBalanceUpdate({ ...balanceUpdate, user_id: value })}>
                        <SelectTrigger className="bg-slate-800 border-slate-700" data-testid="select-user">
                          <SelectValue placeholder="Select user" />
                        </SelectTrigger>
                        <SelectContent>
                          {users.map((u) => (
                            <SelectItem key={u.id} value={u.id}>
                              {u.minecraft_username} ({u.currency_type})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Currency</Label>
                      <Select value={balanceUpdate.currency} onValueChange={(value) => setBalanceUpdate({ ...balanceUpdate, currency: value })}>
                        <SelectTrigger className="bg-slate-800 border-slate-700" data-testid="select-currency">
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
                      <Label>Amount</Label>
                      <Input
                        type="number"
                        value={balanceUpdate.amount}
                        onChange={(e) => setBalanceUpdate({ ...balanceUpdate, amount: parseFloat(e.target.value) })}
                        className="bg-slate-800 border-slate-700"
                        data-testid="balance-amount"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Operation</Label>
                      <Select value={balanceUpdate.operation} onValueChange={(value) => setBalanceUpdate({ ...balanceUpdate, operation: value })}>
                        <SelectTrigger className="bg-slate-800 border-slate-700" data-testid="select-operation">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="add">Add to balance</SelectItem>
                          <SelectItem value="set">Set balance</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button type="submit" disabled={loading || !balanceUpdate.user_id} className="w-full btn-kapitalist" data-testid="update-balance-button">
                      {loading ? 'Updating...' : 'Update Balance'}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="users" className="mt-6">
            <Card className="glass-card border-purple-600/20">
              <CardHeader>
                <CardTitle className="text-2xl">All Users</CardTitle>
                <CardDescription>Manage registered users</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Username</TableHead>
                      <TableHead>Currency Type</TableHead>
                      <TableHead>NIM</TableHead>
                      <TableHead>GRP</TableHead>
                      <TableHead>VDD</TableHead>
                      <TableHead>KKD</TableHead>
                      <TableHead>Admin</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell className="font-bold">{user.minecraft_username}</TableCell>
                        <TableCell>{user.currency_type}</TableCell>
                        <TableCell>{user.balances?.NIM?.toFixed(2) || '0.00'}</TableCell>
                        <TableCell>{user.balances?.GRP?.toFixed(2) || '0.00'}</TableCell>
                        <TableCell>{user.balances?.VDD?.toFixed(2) || '0.00'}</TableCell>
                        <TableCell>{user.balances?.KKD?.toFixed(2) || '0.00'}</TableCell>
                        <TableCell>{user.is_admin ? '✅' : '❌'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="houses" className="mt-6">
            <Card className="glass-card border-purple-600/20">
              <CardHeader>
                <CardTitle className="text-2xl">Pending House Approvals</CardTitle>
                <CardDescription>Approve or reject house listings</CardDescription>
              </CardHeader>
              <CardContent>
                {pendingHouses.length === 0 ? (
                  <p className="text-slate-400 text-center py-8">No pending houses</p>
                ) : (
                  <div className="space-y-4">
                    {pendingHouses.map((house) => (
                      <div key={house.id} className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="text-lg font-bold text-purple-400">{house.name}</h3>
                            <p className="text-sm text-slate-400 mt-1">{house.description}</p>
                            <p className="text-sm text-slate-500 mt-2">Location: {house.location}</p>
                            <p className="text-sm text-slate-500">Owner: {house.owner_username}</p>
                            {house.price_usd && <p className="text-sm font-bold text-green-400 mt-1">Price: ${house.price_usd}</p>}
                          </div>
                          <div className="flex gap-2">
                            <Button
                              onClick={() => handleApproveHouse(house.id)}
                              disabled={loading}
                              className="btn-kapitalist"
                              size="sm"
                            >
                              Approve
                            </Button>
                            <Button
                              onClick={() => handleDeleteHouse(house.id)}
                              disabled={loading}
                              variant="destructive"
                              size="sm"
                            >
                              Delete
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="transactions" className="mt-6">
            <Card className="glass-card border-purple-600/20">
              <CardHeader>
                <CardTitle className="text-2xl">Recent Transactions</CardTitle>
                <CardDescription>Payment history</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>User</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {transactions.map((tx) => (
                      <TableRow key={tx.id}>
                        <TableCell className="font-bold">{tx.username}</TableCell>
                        <TableCell>${tx.amount?.toFixed(2)}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded text-xs font-bold ${
                            tx.payment_status === 'paid' ? 'bg-green-600/20 text-green-400' : 'bg-yellow-600/20 text-yellow-400'
                          }`}>
                            {tx.payment_status}
                          </span>
                        </TableCell>
                        <TableCell>{tx.metadata?.package_type}</TableCell>
                        <TableCell>{new Date(tx.created_at).toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="logs" className="mt-6">
            <Card className="glass-card border-purple-600/20">
              <CardHeader>
                <CardTitle className="text-2xl">Admin Activity Logs</CardTitle>
                <CardDescription>Track all admin actions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {logs.map((log, index) => (
                    <div key={log.id || index} className="p-3 bg-slate-800/50 rounded border border-slate-700 text-sm">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-purple-400">{log.admin_username}</span>
                        <span className="text-slate-500 text-xs">{new Date(log.timestamp).toLocaleString()}</span>
                      </div>
                      <div className="text-slate-300">
                        <span className="font-semibold text-pink-400">{log.action}</span>: {log.details}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdminPanel;
