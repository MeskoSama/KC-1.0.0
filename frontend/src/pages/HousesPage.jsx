import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Building2, Plus, MapPin, DollarSign, CheckCircle } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const HousesPage = ({ user, onLogout, onUpdateUser }) => {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [listDialogOpen, setListDialogOpen] = useState(false);
  const [newHouse, setNewHouse] = useState({
    name: '',
    description: '',
    location: '',
    price_usd: 10.0,
    price_currency: { NIM: 10000, GRP: 10000, VDD: 10000, KKD: 10000 }
  });

  useEffect(() => {
    loadHouses();
  }, []);

  const loadHouses = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/houses?status=available`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHouses(response.data.houses);
    } catch (error) {
      toast.error('Failed to load houses');
    }
  };

  const handleListHouse = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/houses/list`, newHouse, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('House listed successfully! Waiting for admin approval.');
      setListDialogOpen(false);
      setNewHouse({
        name: '',
        description: '',
        location: '',
        price_usd: 10.0,
        price_currency: { NIM: 10000, GRP: 10000, VDD: 10000, KKD: 10000 }
      });
      loadHouses();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to list house');
    } finally {
      setLoading(false);
    }
  };

  const handleBuyHouse = async (houseId, paymentType) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/houses/${houseId}/buy`,
        { payment_type: paymentType },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('House purchased successfully!');
      loadHouses();
      onUpdateUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to purchase house');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black mb-2">
              <span className="text-cyan-400 glow-text">HOUSES</span>
            </h1>
            <p className="text-slate-400 text-lg">Buy, sell, and rent virtual properties</p>
          </div>
          <Dialog open={listDialogOpen} onOpenChange={setListDialogOpen}>
            <DialogTrigger asChild>
              <Button className="btn-minecraft" data-testid="list-house-button">
                <Plus className="mr-2" size={18} />
                List Property
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-slate-900 border-cyan-600/30 max-w-2xl">
              <DialogHeader>
                <DialogTitle className="text-2xl">List Your House</DialogTitle>
                <DialogDescription>Create a listing for other players (requires admin approval)</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleListHouse} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="house-name">House Name</Label>
                  <Input
                    id="house-name"
                    data-testid="house-name-input"
                    value={newHouse.name}
                    onChange={(e) => setNewHouse({ ...newHouse, name: e.target.value })}
                    className="bg-slate-800 border-slate-700"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="house-location">Location</Label>
                  <Input
                    id="house-location"
                    data-testid="house-location-input"
                    placeholder="e.g., X: 100, Y: 64, Z: -200"
                    value={newHouse.location}
                    onChange={(e) => setNewHouse({ ...newHouse, location: e.target.value })}
                    className="bg-slate-800 border-slate-700"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="house-description">Description</Label>
                  <Textarea
                    id="house-description"
                    data-testid="house-description-input"
                    value={newHouse.description}
                    onChange={(e) => setNewHouse({ ...newHouse, description: e.target.value })}
                    className="bg-slate-800 border-slate-700 min-h-24"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="house-price-usd">Price (USD) - Optional</Label>
                  <Input
                    id="house-price-usd"
                    data-testid="house-price-usd-input"
                    type="number"
                    step="0.01"
                    min="0"
                    value={newHouse.price_usd}
                    onChange={(e) => setNewHouse({ ...newHouse, price_usd: parseFloat(e.target.value) })}
                    className="bg-slate-800 border-slate-700"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {Object.keys(newHouse.price_currency).map((currency) => (
                    <div key={currency} className="space-y-2">
                      <Label htmlFor={`price-${currency}`}>Price ({currency})</Label>
                      <Input
                        id={`price-${currency}`}
                        type="number"
                        min="0"
                        value={newHouse.price_currency[currency]}
                        onChange={(e) =>
                          setNewHouse({
                            ...newHouse,
                            price_currency: { ...newHouse.price_currency, [currency]: parseFloat(e.target.value) }
                          })
                        }
                        className="bg-slate-800 border-slate-700"
                      />
                    </div>
                  ))}
                </div>

                <Button type="submit" disabled={loading} className="w-full btn-minecraft">
                  {loading ? 'Listing...' : 'List House'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {houses.map((house) => (
            <Card key={house.id} className="glass-card border-cyan-600/20" data-testid={`house-${house.id}`}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <Building2 size={32} className="text-cyan-400" />
                  <Badge variant="default" className="bg-purple-600">
                    {house.status}
                  </Badge>
                </div>
                <CardTitle className="text-xl mt-2">{house.name}</CardTitle>
                <CardDescription className="flex items-center gap-1 text-sm">
                  <MapPin size={14} />
                  {house.location}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-slate-400 text-sm">{house.description}</p>

                {house.owner_username && (
                  <div className="text-sm">
                    <span className="text-slate-500">Owner: </span>
                    <span className="font-bold text-purple-400">{house.owner_username}</span>
                  </div>
                )}

                <div className="space-y-2">
                  {house.price_usd && (
                    <div className="p-3 bg-amber-600/10 border border-amber-600/30 rounded-lg">
                      <div className="text-sm text-slate-400 mb-1">USD Price</div>
                      <div className="text-2xl font-bold text-amber-400 flex items-center gap-1">
                        <DollarSign size={20} />
                        {house.price_usd.toFixed(2)}
                      </div>
                    </div>
                  )}

                  {house.price_currency && (
                    <div className="p-3 bg-cyan-600/10 border border-cyan-600/30 rounded-lg">
                      <div className="text-sm text-slate-400 mb-2">Currency Prices</div>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(house.price_currency).map(([currency, price]) => (
                          <div key={currency} className="text-sm">
                            <span className="text-slate-400">{currency}: </span>
                            <span className="font-bold text-cyan-400">{price.toLocaleString()}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {house.price_currency && (
                  <Button
                    onClick={() => handleBuyHouse(house.id, 'currency')}
                    disabled={loading || user.balances[user.currency_type] < house.price_currency[user.currency_type]}
                    className="w-full btn-minecraft"
                    data-testid={`buy-house-currency-${house.id}`}
                  >
                    <CheckCircle className="mr-2" size={18} />
                    Buy with {user.currency_type}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {houses.length === 0 && (
          <Card className="glass-card border-slate-700">
            <CardContent className="py-12 text-center">
              <Building2 size={48} className="mx-auto mb-4 text-slate-600" />
              <p className="text-slate-400 text-lg">No houses available</p>
              <p className="text-slate-500 text-sm mt-2">Be the first to list a property!</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default HousesPage;
