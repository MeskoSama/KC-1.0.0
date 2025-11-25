import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Target, Trophy, CheckCircle, Plus } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const BountyBoard = ({ user, onLogout, onUpdateUser }) => {
  const [bounties, setBounties] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newBounty, setNewBounty] = useState({
    bounty_type: 'quest',
    title: '',
    description: '',
    reward_currency: user.currency_type,
    reward_amount: 1000,
    target_player: ''
  });

  useEffect(() => {
    loadBounties();
  }, []);

  const loadBounties = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/bounties?status=active`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBounties(response.data.bounties);
    } catch (error) {
      toast.error('Failed to load bounties');
    }
  };

  const handleCreateBounty = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/bounties`, newBounty, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Bounty created successfully!');
      setCreateDialogOpen(false);
      setNewBounty({
        bounty_type: 'quest',
        title: '',
        description: '',
        reward_currency: user.currency_type,
        reward_amount: 1000,
        target_player: ''
      });
      loadBounties();
      onUpdateUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create bounty');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteBounty = async (bountyId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/bounties/${bountyId}/complete`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Bounty completed! Reward claimed.');
      loadBounties();
      onUpdateUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete bounty');
    } finally {
      setLoading(false);
    }
  };

  const pvpBounties = bounties.filter(b => b.bounty_type === 'pvp');
  const questBounties = bounties.filter(b => b.bounty_type === 'quest');

  return (
    <div className="minecraft-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black mb-2">
              <span className="text-rose-400 glow-text">BOUNTY BOARD</span>
            </h1>
            <p className="text-slate-400 text-lg">Complete bounties to earn rewards</p>
          </div>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="btn-minecraft" data-testid="create-bounty-button">
                <Plus className="mr-2" size={18} />
                Create Bounty
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-slate-900 border-emerald-600/30 max-w-2xl">
              <DialogHeader>
                <DialogTitle className="text-2xl">Create New Bounty</DialogTitle>
                <DialogDescription>Set up a bounty for other players to complete</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateBounty} className="space-y-4">
                <div className="space-y-2">
                  <Label>Bounty Type</Label>
                  <Select
                    value={newBounty.bounty_type}
                    onValueChange={(value) => setNewBounty({ ...newBounty, bounty_type: value })}
                  >
                    <SelectTrigger className="bg-slate-800 border-slate-700" data-testid="bounty-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="quest">Quest Bounty</SelectItem>
                      <SelectItem value="pvp">PvP Bounty</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bounty-title">Title</Label>
                  <Input
                    id="bounty-title"
                    data-testid="bounty-title-input"
                    value={newBounty.title}
                    onChange={(e) => setNewBounty({ ...newBounty, title: e.target.value })}
                    className="bg-slate-800 border-slate-700"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bounty-description">Description</Label>
                  <Textarea
                    id="bounty-description"
                    data-testid="bounty-description-input"
                    value={newBounty.description}
                    onChange={(e) => setNewBounty({ ...newBounty, description: e.target.value })}
                    className="bg-slate-800 border-slate-700 min-h-24"
                    required
                  />
                </div>

                {newBounty.bounty_type === 'pvp' && (
                  <div className="space-y-2">
                    <Label htmlFor="target-player">Target Player</Label>
                    <Input
                      id="target-player"
                      data-testid="target-player-input"
                      value={newBounty.target_player}
                      onChange={(e) => setNewBounty({ ...newBounty, target_player: e.target.value })}
                      className="bg-slate-800 border-slate-700"
                      required
                    />
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="reward-currency">Reward Currency</Label>
                    <Select
                      value={newBounty.reward_currency}
                      onValueChange={(value) => setNewBounty({ ...newBounty, reward_currency: value })}
                    >
                      <SelectTrigger className="bg-slate-800 border-slate-700" data-testid="reward-currency-select">
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
                    <Label htmlFor="reward-amount">Reward Amount</Label>
                    <Input
                      id="reward-amount"
                      data-testid="reward-amount-input"
                      type="number"
                      min="100"
                      value={newBounty.reward_amount}
                      onChange={(e) => setNewBounty({ ...newBounty, reward_amount: parseFloat(e.target.value) })}
                      className="bg-slate-800 border-slate-700"
                      required
                    />
                  </div>
                </div>

                <div className="p-4 bg-amber-600/10 border border-amber-600/30 rounded-lg">
                  <p className="text-sm text-amber-300">
                    ⚠️ The reward amount will be deducted from your balance immediately
                  </p>
                </div>

                <Button type="submit" disabled={loading} className="w-full btn-minecraft">
                  {loading ? 'Creating...' : 'Create Bounty'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <Tabs defaultValue="all" className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-slate-800/50 max-w-md" data-testid="bounty-tabs">
            <TabsTrigger value="all" data-testid="tab-all">All ({bounties.length})</TabsTrigger>
            <TabsTrigger value="pvp" data-testid="tab-pvp">PvP ({pvpBounties.length})</TabsTrigger>
            <TabsTrigger value="quest" data-testid="tab-quest">Quests ({questBounties.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {bounties.map((bounty) => (
                <Card key={bounty.id} className="glass-card border-rose-600/20" data-testid={`bounty-${bounty.id}`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <Badge className="mb-2" variant={bounty.bounty_type === 'pvp' ? 'destructive' : 'default'}>
                          {bounty.bounty_type === 'pvp' ? <Target size={14} className="mr-1" /> : <Trophy size={14} className="mr-1" />}
                          {bounty.bounty_type.toUpperCase()}
                        </Badge>
                        <CardTitle className="text-xl mb-2">{bounty.title}</CardTitle>
                      </div>
                    </div>
                    <CardDescription className="text-slate-400">{bounty.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {bounty.target_player && (
                      <div className="text-sm">
                        <span className="text-slate-500">Target: </span>
                        <span className="font-bold text-rose-400">{bounty.target_player}</span>
                      </div>
                    )}
                    <div className="text-sm">
                      <span className="text-slate-500">Posted by: </span>
                      <span className="font-bold text-emerald-400">{bounty.creator_username}</span>
                    </div>
                    <div className="p-3 bg-emerald-600/10 border border-emerald-600/30 rounded-lg">
                      <div className="text-sm text-slate-400 mb-1">Reward</div>
                      <div className="text-2xl font-bold text-emerald-400">
                        {bounty.reward_amount.toLocaleString()} {bounty.reward_currency}
                      </div>
                    </div>
                    {bounty.creator_id !== user.id && (
                      <Button
                        onClick={() => handleCompleteBounty(bounty.id)}
                        disabled={loading}
                        className="w-full btn-minecraft"
                        data-testid={`complete-bounty-${bounty.id}`}
                      >
                        <CheckCircle className="mr-2" size={18} />
                        Claim Bounty
                      </Button>
                    )}
                    {bounty.creator_id === user.id && (
                      <div className="w-full py-2 bg-amber-600/20 border border-amber-600 rounded-lg text-center text-sm font-bold text-amber-400">
                        YOUR BOUNTY
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
            {bounties.length === 0 && (
              <Card className="glass-card border-slate-700">
                <CardContent className="py-12 text-center">
                  <Target size={48} className="mx-auto mb-4 text-slate-600" />
                  <p className="text-slate-400 text-lg">No active bounties</p>
                  <p className="text-slate-500 text-sm mt-2">Be the first to create one!</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="pvp" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {pvpBounties.map((bounty) => (
                <Card key={bounty.id} className="glass-card border-rose-600/20">
                  <CardHeader>
                    <Badge className="mb-2 w-fit" variant="destructive">
                      <Target size={14} className="mr-1" />
                      PVP
                    </Badge>
                    <CardTitle className="text-xl mb-2">{bounty.title}</CardTitle>
                    <CardDescription>{bounty.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="text-sm">
                      <span className="text-slate-500">Target: </span>
                      <span className="font-bold text-rose-400">{bounty.target_player}</span>
                    </div>
                    <div className="text-sm">
                      <span className="text-slate-500">Posted by: </span>
                      <span className="font-bold text-emerald-400">{bounty.creator_username}</span>
                    </div>
                    <div className="p-3 bg-emerald-600/10 border border-emerald-600/30 rounded-lg">
                      <div className="text-sm text-slate-400 mb-1">Reward</div>
                      <div className="text-2xl font-bold text-emerald-400">
                        {bounty.reward_amount.toLocaleString()} {bounty.reward_currency}
                      </div>
                    </div>
                    {bounty.creator_id !== user.id && (
                      <Button onClick={() => handleCompleteBounty(bounty.id)} disabled={loading} className="w-full btn-minecraft">
                        <CheckCircle className="mr-2" size={18} />
                        Claim Bounty
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="quest" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {questBounties.map((bounty) => (
                <Card key={bounty.id} className="glass-card border-emerald-600/20">
                  <CardHeader>
                    <Badge className="mb-2 w-fit" variant="default">
                      <Trophy size={14} className="mr-1" />
                      QUEST
                    </Badge>
                    <CardTitle className="text-xl mb-2">{bounty.title}</CardTitle>
                    <CardDescription>{bounty.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="text-sm">
                      <span className="text-slate-500">Posted by: </span>
                      <span className="font-bold text-emerald-400">{bounty.creator_username}</span>
                    </div>
                    <div className="p-3 bg-emerald-600/10 border border-emerald-600/30 rounded-lg">
                      <div className="text-sm text-slate-400 mb-1">Reward</div>
                      <div className="text-2xl font-bold text-emerald-400">
                        {bounty.reward_amount.toLocaleString()} {bounty.reward_currency}
                      </div>
                    </div>
                    {bounty.creator_id !== user.id && (
                      <Button onClick={() => handleCompleteBounty(bounty.id)} disabled={loading} className="w-full btn-minecraft">
                        <CheckCircle className="mr-2" size={18} />
                        Claim Bounty
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default BountyBoard;
