import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { 
  Users, Plus, Edit2, Trash2, CreditCard, Building2, DollarSign, 
  RefreshCw, Palette, Zap, Wallet, TrendingUp
} from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const AdminAccountsManagement = () => {
  const [accounts, setAccounts] = useState([]);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Dialog states
  const [addAccountOpen, setAddAccountOpen] = useState(false);
  const [addBankOpen, setAddBankOpen] = useState(false);
  const [addCardOpen, setAddCardOpen] = useState(false);
  const [editBalanceOpen, setEditBalanceOpen] = useState(false);
  const [editColorsOpen, setEditColorsOpen] = useState(false);
  
  // Selected items
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [selectedBank, setSelectedBank] = useState(null);
  const [selectedCard, setSelectedCard] = useState(null);
  
  // Form states
  const [newAccount, setNewAccount] = useState({ username: '' });
  const [newBank, setNewBank] = useState({ bank_id: '' });
  const [newCard, setNewCard] = useState({ card_type: 'debit' });
  const [balanceEdit, setBalanceEdit] = useState({
    bank_id: '',
    card_type: '',
    currency: 'GRP',
    amount: 0,
    operation: 'set'
  });
  const [rankingColors, setRankingColors] = useState({
    rank_1: '#FFFF00',
    rank_2: '#C0C0C0',
    rank_3: '#B87333'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accountsRes, configRes] = await Promise.all([
        axios.get(`${API}/accounts`),
        axios.get(`${API}/accounts/config`)
      ]);
      
      setAccounts(accountsRes.data.accounts || []);
      setConfig(configRes.data);
      if (configRes.data?.ranking_colors) {
        setRankingColors({
          rank_1: configRes.data.ranking_colors["1"] || '#FFFF00',
          rank_2: configRes.data.ranking_colors["2"] || '#C0C0C0',
          rank_3: configRes.data.ranking_colors["3"] || '#B87333'
        });
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load accounts');
    }
  };

  const handleInitializeSamples = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/accounts/initialize`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(response.data.message);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to initialize');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAccount = async () => {
    if (!newAccount.username.trim()) {
      toast.error('Please enter a username');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/accounts`, {
        username: newAccount.username,
        bank_accounts: []
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Account created!');
      setAddAccountOpen(false);
      setNewAccount({ username: '' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async (accountId, username) => {
    if (!window.confirm(`Delete account "${username}" and all their data?`)) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/accounts/${accountId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Account deleted');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    } finally {
      setLoading(false);
    }
  };

  const handleAddBank = async () => {
    if (!selectedAccount || !newBank.bank_id) {
      toast.error('Please select a bank');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/accounts/${selectedAccount.id}/bank`, {
        bank_id: newBank.bank_id,
        cards: []
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Bank account added!');
      setAddBankOpen(false);
      setNewBank({ bank_id: '' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add bank');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveBank = async (accountId, bankId) => {
    if (!window.confirm('Remove this bank account and all cards?')) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/accounts/${accountId}/bank/${bankId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Bank removed');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to remove bank');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCard = async () => {
    if (!selectedAccount || !selectedBank || !newCard.card_type) {
      toast.error('Please select card type');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/accounts/${selectedAccount.id}/card?bank_id=${selectedBank}`, {
        card_type: newCard.card_type,
        balances: { GRP: 0, NIM: 0, VDD: 0, KKD: 0, EGD: 0, EP: 0 },
        debt: { GRP: 0, NIM: 0, VDD: 0, KKD: 0, EGD: 0, EP: 0 },
        foreign_currencies_opened: []
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Card added!');
      setAddCardOpen(false);
      setNewCard({ card_type: 'debit' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add card');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveCard = async (accountId, bankId, cardId) => {
    if (!window.confirm('Remove this card?')) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/accounts/${accountId}/card/${bankId}/${cardId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Card removed');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to remove card');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateBalance = async () => {
    if (!selectedAccount || !balanceEdit.bank_id || !balanceEdit.card_type) {
      toast.error('Missing required fields');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/accounts/${selectedAccount.id}/balance`, balanceEdit, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Balance updated!');
      setEditBalanceOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update balance');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleForeignCurrency = async (accountId, bankId, cardType, currency, currentlyOpened) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/accounts/${accountId}/foreign-currency`, {
        bank_id: bankId,
        card_type: cardType,
        currency: currency,
        open: !currentlyOpened
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Foreign currency ${!currentlyOpened ? 'opened' : 'closed'}`);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to toggle');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRankingColors = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/accounts/config/ranking-colors`, rankingColors, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Ranking colors updated!');
      setEditColorsOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update colors');
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (amount) => {
    if (amount >= 1e6) return (amount / 1e6).toFixed(1) + 'M';
    if (amount >= 1e3) return (amount / 1e3).toFixed(1) + 'K';
    return amount?.toLocaleString() || '0';
  };

  const getCardIcon = (cardType) => {
    const icons = { credit: '💳', debit: '🏦', government: '🏛️', platinum: '💎', gold: '🥇', investor: '📈' };
    return icons[cardType] || '💳';
  };

  return (
    <div className="space-y-6">
      {/* Quick Actions */}
      <Card className="glass-card border-green-600/20">
        <CardHeader className="py-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Zap className="text-green-400" size={16} />
            Quick Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="py-2 flex gap-2 flex-wrap">
          <Button onClick={handleInitializeSamples} disabled={loading} variant="outline">
            <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
            Initialize Sample Accounts (bot1, bot2, bot3)
          </Button>
          <Dialog open={editColorsOpen} onOpenChange={setEditColorsOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Palette size={16} className="mr-2" /> Edit Ranking Colors
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-slate-900 border-purple-600/30">
              <DialogHeader>
                <DialogTitle>Edit Ranking Colors</DialogTitle>
                <DialogDescription>Set neon colors for top 3 rankings</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>1st Place Color</Label>
                  <div className="flex gap-2">
                    <Input
                      type="color"
                      value={rankingColors.rank_1}
                      onChange={(e) => setRankingColors({ ...rankingColors, rank_1: e.target.value })}
                      className="w-12 h-10"
                    />
                    <Input
                      value={rankingColors.rank_1}
                      onChange={(e) => setRankingColors({ ...rankingColors, rank_1: e.target.value })}
                      className="bg-slate-800 border-slate-700"
                    />
                    <div className="px-4 py-2 rounded" style={{ backgroundColor: rankingColors.rank_1 + '30', color: rankingColors.rank_1, textShadow: `0 0 10px ${rankingColors.rank_1}` }}>
                      Preview
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>2nd Place Color</Label>
                  <div className="flex gap-2">
                    <Input
                      type="color"
                      value={rankingColors.rank_2}
                      onChange={(e) => setRankingColors({ ...rankingColors, rank_2: e.target.value })}
                      className="w-12 h-10"
                    />
                    <Input
                      value={rankingColors.rank_2}
                      onChange={(e) => setRankingColors({ ...rankingColors, rank_2: e.target.value })}
                      className="bg-slate-800 border-slate-700"
                    />
                    <div className="px-4 py-2 rounded" style={{ backgroundColor: rankingColors.rank_2 + '30', color: rankingColors.rank_2, textShadow: `0 0 10px ${rankingColors.rank_2}` }}>
                      Preview
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>3rd Place Color</Label>
                  <div className="flex gap-2">
                    <Input
                      type="color"
                      value={rankingColors.rank_3}
                      onChange={(e) => setRankingColors({ ...rankingColors, rank_3: e.target.value })}
                      className="w-12 h-10"
                    />
                    <Input
                      value={rankingColors.rank_3}
                      onChange={(e) => setRankingColors({ ...rankingColors, rank_3: e.target.value })}
                      className="bg-slate-800 border-slate-700"
                    />
                    <div className="px-4 py-2 rounded" style={{ backgroundColor: rankingColors.rank_3 + '30', color: rankingColors.rank_3, textShadow: `0 0 10px ${rankingColors.rank_3}` }}>
                      Preview
                    </div>
                  </div>
                </div>
                <Button onClick={handleUpdateRankingColors} disabled={loading} className="w-full btn-kapitalist">
                  {loading ? 'Updating...' : 'Update Colors'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>

      {/* Accounts Table */}
      <Card className="glass-card border-yellow-600/20">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="text-yellow-400" />
              Server Accounts Management
            </CardTitle>
            <CardDescription>Manage bank accounts, cards, and balances</CardDescription>
          </div>
          <Dialog open={addAccountOpen} onOpenChange={setAddAccountOpen}>
            <DialogTrigger asChild>
              <Button className="btn-kapitalist" size="sm">
                <Plus size={16} className="mr-1" /> Add Account
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-slate-900 border-yellow-600/30">
              <DialogHeader>
                <DialogTitle>Create New Account</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Username</Label>
                  <Input
                    placeholder="Enter username"
                    value={newAccount.username}
                    onChange={(e) => setNewAccount({ ...newAccount, username: e.target.value })}
                    className="bg-slate-800 border-slate-700"
                  />
                </div>
                <Button onClick={handleCreateAccount} disabled={loading} className="w-full btn-kapitalist">
                  {loading ? 'Creating...' : 'Create Account'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {accounts.length === 0 ? (
              <p className="text-center text-slate-500 py-8">
                No accounts yet. Click "Initialize Sample Accounts" to create test data.
              </p>
            ) : (
              accounts.map((account, idx) => (
                <Card key={account.id} className="bg-slate-800/30 border-slate-700/30">
                  <CardHeader className="py-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge className={idx < 3 ? 'bg-yellow-600' : 'bg-slate-600'}>
                          #{account.rank}
                        </Badge>
                        <CardTitle className="text-lg">{account.username}</CardTitle>
                        <Badge variant="outline" className="text-green-400">
                          {formatMoney(account.total_wealth)} GRP
                        </Badge>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedAccount(account);
                            setAddBankOpen(true);
                          }}
                        >
                          <Building2 size={14} className="mr-1" /> Add Bank
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedAccount(account);
                            setEditBalanceOpen(true);
                          }}
                        >
                          <DollarSign size={14} className="mr-1" /> Edit Balance
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDeleteAccount(account.id, account.username)}
                          disabled={loading}
                        >
                          <Trash2 size={14} />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="py-2">
                    {account.bank_accounts?.length === 0 ? (
                      <p className="text-slate-500 text-sm">No bank accounts</p>
                    ) : (
                      <div className="space-y-3">
                        {account.bank_accounts.map((bankAcc, bankIdx) => (
                          <div key={bankIdx} className="p-3 bg-slate-900/50 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <Building2 size={16} className="text-blue-400" />
                                <span className="font-semibold text-blue-300">
                                  {config?.banks?.[bankAcc.bank_id]?.name || bankAcc.bank_id}
                                </span>
                                <Badge variant="outline" className="text-xs">
                                  Home: {config?.banks?.[bankAcc.bank_id]?.home_currency}
                                </Badge>
                              </div>
                              <div className="flex gap-1">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => {
                                    setSelectedAccount(account);
                                    setSelectedBank(bankAcc.bank_id);
                                    setAddCardOpen(true);
                                  }}
                                >
                                  <CreditCard size={14} className="mr-1" /> Add Card
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="text-red-400"
                                  onClick={() => handleRemoveBank(account.id, bankAcc.bank_id)}
                                >
                                  <Trash2 size={14} />
                                </Button>
                              </div>
                            </div>
                            
                            {/* Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 mt-2">
                              {bankAcc.cards?.map((card, cardIdx) => (
                                <div 
                                  key={cardIdx} 
                                  className="p-2 rounded bg-slate-800/50"
                                  style={{ borderLeft: `3px solid ${config?.banks?.[bankAcc.bank_id]?.card_colors?.[card.card_type] || '#666'}` }}
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="flex items-center gap-1 text-sm font-medium">
                                      {getCardIcon(card.card_type)} {card.card_type}
                                    </span>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      className="h-6 w-6 p-0 text-red-400"
                                      onClick={() => handleRemoveCard(account.id, bankAcc.bank_id, card.id)}
                                    >
                                      <Trash2 size={12} />
                                    </Button>
                                  </div>
                                  
                                  {/* Foreign Currency Toggles */}
                                  <div className="text-xs text-slate-400 mt-1">
                                    Foreign currencies:
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {config?.currencies?.filter(c => c !== config?.banks?.[bankAcc.bank_id]?.home_currency).map(currency => {
                                        const isOpened = card.foreign_currencies_opened?.includes(currency);
                                        return (
                                          <Badge 
                                            key={currency}
                                            variant={isOpened ? "default" : "outline"}
                                            className={`cursor-pointer text-xs ${isOpened ? 'bg-green-600' : 'text-slate-500'}`}
                                            onClick={() => handleToggleForeignCurrency(
                                              account.id, 
                                              bankAcc.bank_id, 
                                              card.card_type, 
                                              currency, 
                                              isOpened
                                            )}
                                          >
                                            {currency}
                                          </Badge>
                                        );
                                      })}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Add Bank Dialog */}
      <Dialog open={addBankOpen} onOpenChange={setAddBankOpen}>
        <DialogContent className="bg-slate-900 border-blue-600/30">
          <DialogHeader>
            <DialogTitle>Add Bank to {selectedAccount?.username}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Select Bank</Label>
              <Select value={newBank.bank_id} onValueChange={(v) => setNewBank({ ...newBank, bank_id: v })}>
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue placeholder="Choose a bank" />
                </SelectTrigger>
                <SelectContent>
                  {config?.banks && Object.entries(config.banks).map(([bankId, bank]) => (
                    <SelectItem key={bankId} value={bankId}>
                      {bank.name} (Home: {bank.home_currency})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleAddBank} disabled={loading} className="w-full btn-kapitalist">
              {loading ? 'Adding...' : 'Add Bank Account'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Add Card Dialog */}
      <Dialog open={addCardOpen} onOpenChange={setAddCardOpen}>
        <DialogContent className="bg-slate-900 border-purple-600/30">
          <DialogHeader>
            <DialogTitle>Add Card to {selectedAccount?.username}</DialogTitle>
            <DialogDescription>Bank: {config?.banks?.[selectedBank]?.name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Card Type</Label>
              <Select value={newCard.card_type} onValueChange={(v) => setNewCard({ ...newCard, card_type: v })}>
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {config?.card_types?.map(cardType => (
                    <SelectItem key={cardType} value={cardType}>
                      {getCardIcon(cardType)} {cardType}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleAddCard} disabled={loading} className="w-full btn-kapitalist">
              {loading ? 'Adding...' : 'Add Card'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Balance Dialog */}
      <Dialog open={editBalanceOpen} onOpenChange={setEditBalanceOpen}>
        <DialogContent className="bg-slate-900 border-green-600/30">
          <DialogHeader>
            <DialogTitle>Edit Balance for {selectedAccount?.username}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Bank</Label>
              <Select value={balanceEdit.bank_id} onValueChange={(v) => setBalanceEdit({ ...balanceEdit, bank_id: v })}>
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue placeholder="Select bank" />
                </SelectTrigger>
                <SelectContent>
                  {selectedAccount?.bank_accounts?.map(ba => (
                    <SelectItem key={ba.bank_id} value={ba.bank_id}>
                      {config?.banks?.[ba.bank_id]?.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Card Type</Label>
              <Select value={balanceEdit.card_type} onValueChange={(v) => setBalanceEdit({ ...balanceEdit, card_type: v })}>
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue placeholder="Select card" />
                </SelectTrigger>
                <SelectContent>
                  {selectedAccount?.bank_accounts
                    ?.find(ba => ba.bank_id === balanceEdit.bank_id)
                    ?.cards?.map(card => (
                      <SelectItem key={card.card_type} value={card.card_type}>
                        {getCardIcon(card.card_type)} {card.card_type}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Currency</Label>
                <Select value={balanceEdit.currency} onValueChange={(v) => setBalanceEdit({ ...balanceEdit, currency: v })}>
                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {config?.currencies?.map(currency => (
                      <SelectItem key={currency} value={currency}>{currency}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Operation</Label>
                <Select value={balanceEdit.operation} onValueChange={(v) => setBalanceEdit({ ...balanceEdit, operation: v })}>
                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="set">Set (Replace)</SelectItem>
                    <SelectItem value="add">Add</SelectItem>
                    <SelectItem value="subtract">Subtract</SelectItem>
                    <SelectItem value="reset">Reset to 0</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Amount</Label>
              <Input
                type="number"
                value={balanceEdit.amount}
                onChange={(e) => setBalanceEdit({ ...balanceEdit, amount: parseFloat(e.target.value) || 0 })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <Button onClick={handleUpdateBalance} disabled={loading} className="w-full btn-kapitalist">
              {loading ? 'Updating...' : 'Update Balance'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminAccountsManagement;
