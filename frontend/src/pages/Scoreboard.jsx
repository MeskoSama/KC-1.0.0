import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Trophy, TrendingUp, Home, Crown } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const Scoreboard = ({ user, onLogout }) => {
  const [richest, setRichest] = useState([]);
  const [topTraders, setTopTraders] = useState([]);
  const [houseOwners, setHouseOwners] = useState([]);
  const [selectedCurrency, setSelectedCurrency] = useState('NIM');

  useEffect(() => {
    loadLeaderboards();
  }, [selectedCurrency]);

  const loadLeaderboards = async () => {
    try {
      const token = localStorage.getItem('token');
      const [richestRes, tradersRes, ownersRes] = await Promise.all([
        axios.get(`${API}/leaderboard/richest?currency=${selectedCurrency}&limit=10`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/leaderboard/traders?limit=10`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/leaderboard/house-owners?limit=10`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setRichest(richestRes.data.leaderboard);
      setTopTraders(tradersRes.data.leaderboard);
      setHouseOwners(ownersRes.data.leaderboard);
    } catch (error) {
      toast.error('Failed to load leaderboards');
    }
  };

  const getMedalColor = (rank) => {
    if (rank === 1) return 'text-amber-400';
    if (rank === 2) return 'text-slate-400';
    if (rank === 3) return 'text-orange-600';
    return 'text-slate-600';
  };

  const getMedalBg = (rank) => {
    if (rank === 1) return 'bg-amber-600/20 border-amber-600';
    if (rank === 2) return 'bg-slate-600/20 border-slate-500';
    if (rank === 3) return 'bg-orange-600/20 border-orange-600';
    return 'bg-slate-800/50 border-slate-700';
  };

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-4xl font-black mb-2">
            <span className="text-amber-400 glow-text">LEADERBOARDS</span>
          </h1>
          <p className="text-slate-400 text-lg">Top players and traders on the server</p>
        </div>

        <Tabs defaultValue="richest" className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-slate-800/50 max-w-2xl" data-testid="scoreboard-tabs">
            <TabsTrigger value="richest" data-testid="tab-richest">
              <Trophy className="mr-2" size={18} />
              Richest
            </TabsTrigger>
            <TabsTrigger value="traders" data-testid="tab-traders">
              <TrendingUp className="mr-2" size={18} />
              Top Traders
            </TabsTrigger>
            <TabsTrigger value="houses" data-testid="tab-houses">
              <Home className="mr-2" size={18} />
              House Owners
            </TabsTrigger>
          </TabsList>

          <TabsContent value="richest" className="mt-6">
            <Card className="glass-card border-amber-600/20">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl flex items-center gap-2">
                      <Trophy className="text-amber-400" />
                      Richest Players
                    </CardTitle>
                    <CardDescription>Top 10 players by currency balance</CardDescription>
                  </div>
                  <Select value={selectedCurrency} onValueChange={setSelectedCurrency}>
                    <SelectTrigger className="w-32 bg-slate-800 border-slate-700" data-testid="currency-filter">
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
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {richest.map((player, index) => {
                    const rank = index + 1;
                    const isCurrentUser = player.minecraft_username === user.username;
                    return (
                      <div
                        key={index}
                        className={`p-4 rounded-lg border-2 flex items-center justify-between ${
                          isCurrentUser
                            ? 'bg-purple-600/20 border-purple-600'
                            : getMedalBg(rank)
                        }`}
                        data-testid={`richest-${index}`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-full flex items-center justify-center font-black text-2xl ${
                            isCurrentUser ? 'bg-purple-600' : rank <= 3 ? getMedalBg(rank) : 'bg-slate-700'
                          }`}>
                            <span className={isCurrentUser ? 'text-white' : getMedalColor(rank)}>
                              {rank <= 3 ? ['🥇', '🥈', '🥉'][rank - 1] : rank}
                            </span>
                          </div>
                          <div>
                            <div className={`font-bold text-lg ${
                              isCurrentUser ? 'text-purple-400' : 'text-slate-200'
                            }`}>
                              {player.minecraft_username}
                              {isCurrentUser && <span className="ml-2 text-xs">(You)</span>}
                            </div>
                            <div className="text-sm text-slate-500">{player.currency_type} User</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-black text-amber-400">
                            {(player.balances[selectedCurrency] || 0).toLocaleString()}
                          </div>
                          <div className="text-sm text-slate-500">{selectedCurrency}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="traders" className="mt-6">
            <Card className="glass-card border-cyan-600/20">
              <CardHeader>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <TrendingUp className="text-cyan-400" />
                  Top Traders
                </CardTitle>
                <CardDescription>Players with the most transactions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {topTraders.map((player, index) => {
                    const rank = index + 1;
                    const isCurrentUser = player.minecraft_username === user.username;
                    return (
                      <div
                        key={index}
                        className={`p-4 rounded-lg border-2 flex items-center justify-between ${
                          isCurrentUser
                            ? 'bg-purple-600/20 border-purple-600'
                            : getMedalBg(rank)
                        }`}
                        data-testid={`trader-${index}`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-full flex items-center justify-center font-black text-2xl ${
                            isCurrentUser ? 'bg-purple-600' : rank <= 3 ? getMedalBg(rank) : 'bg-slate-700'
                          }`}>
                            <span className={isCurrentUser ? 'text-white' : getMedalColor(rank)}>
                              {rank <= 3 ? ['🥇', '🥈', '🥉'][rank - 1] : rank}
                            </span>
                          </div>
                          <div>
                            <div className={`font-bold text-lg ${
                              isCurrentUser ? 'text-purple-400' : 'text-slate-200'
                            }`}>
                              {player.minecraft_username}
                              {isCurrentUser && <span className="ml-2 text-xs">(You)</span>}
                            </div>
                            <div className="text-sm text-slate-500">
                              ${(player.total_spent || 0).toFixed(2)} spent
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-black text-cyan-400">
                            {player.total_transactions || 0}
                          </div>
                          <div className="text-sm text-slate-500">Transactions</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="houses" className="mt-6">
            <Card className="glass-card border-rose-600/20">
              <CardHeader>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <Home className="text-rose-400" />
                  House Owners
                </CardTitle>
                <CardDescription>Players with the most properties</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {houseOwners.map((player, index) => {
                    const rank = index + 1;
                    const isCurrentUser = player.minecraft_username === user.username;
                    return (
                      <div
                        key={index}
                        className={`p-4 rounded-lg border-2 flex items-center justify-between ${
                          isCurrentUser
                            ? 'bg-purple-600/20 border-purple-600'
                            : getMedalBg(rank)
                        }`}
                        data-testid={`house-owner-${index}`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-full flex items-center justify-center font-black text-2xl ${
                            isCurrentUser ? 'bg-purple-600' : rank <= 3 ? getMedalBg(rank) : 'bg-slate-700'
                          }`}>
                            <span className={isCurrentUser ? 'text-white' : getMedalColor(rank)}>
                              {rank <= 3 ? ['🥇', '🥈', '🥉'][rank - 1] : rank}
                            </span>
                          </div>
                          <div>
                            <div className={`font-bold text-lg ${
                              isCurrentUser ? 'text-purple-400' : 'text-slate-200'
                            }`}>
                              {player.minecraft_username}
                              {isCurrentUser && <span className="ml-2 text-xs">(You)</span>}
                            </div>
                            <div className="text-sm text-slate-500">Property Owner</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-black text-rose-400">
                            {player.house_count || 0}
                          </div>
                          <div className="text-sm text-slate-500">Houses</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Scoreboard;
