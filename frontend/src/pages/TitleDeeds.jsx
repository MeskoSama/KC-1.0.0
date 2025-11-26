import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, MapPin, Calendar, User, DollarSign } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const TitleDeeds = ({ user, onLogout }) => {
  const [titleDeeds, setTitleDeeds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTitleDeeds();
  }, []);

  const loadTitleDeeds = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/title-deeds`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTitleDeeds(response.data.title_deeds);
    } catch (error) {
      toast.error('Failed to load title deeds');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-4xl font-black mb-2">
            <span className="text-purple-400 glow-text">TITLE DEEDS</span>
          </h1>
          <p className="text-slate-400 text-lg">Your property ownership documents</p>
        </div>

        {loading ? (
          <Card className="glass-card border-purple-600/20">
            <CardContent className="py-12 text-center">
              <p className="text-slate-400">Loading title deeds...</p>
            </CardContent>
          </Card>
        ) : titleDeeds.length === 0 ? (
          <Card className="glass-card border-purple-600/20">
            <CardContent className="py-12 text-center">
              <FileText size={48} className="mx-auto mb-4 text-slate-600" />
              <p className="text-slate-400 text-lg">No title deeds yet</p>
              <p className="text-slate-500 text-sm mt-2">Purchase a house to receive your first title deed</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {titleDeeds.map((deed) => (
              <Card
                key={deed.id}
                className="glass-card border-purple-600/30 hover:border-purple-500 transition-all"
                data-testid={`title-deed-${deed.id}`}
              >
                <CardHeader className="bg-gradient-to-r from-purple-900/30 to-pink-900/30">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <Badge className="mb-2 bg-purple-600">OFFICIAL TITLE DEED</Badge>
                      <CardTitle className="text-2xl text-white">{deed.house_name}</CardTitle>
                      <CardDescription className="text-slate-300 mt-2">
                        <MapPin size={14} className="inline mr-1" />
                        {deed.location}
                      </CardDescription>
                    </div>
                    <FileText size={40} className="text-purple-400" />
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-2 text-sm text-slate-500 mb-1">
                        <User size={14} />
                        Owner
                      </div>
                      <div className="font-bold text-purple-400">{deed.owner_username}</div>
                    </div>

                    <div className="p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-2 text-sm text-slate-500 mb-1">
                        <Calendar size={14} />
                        Issued
                      </div>
                      <div className="font-bold text-white">
                        {new Date(deed.issued_date).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-purple-600/10 border border-purple-600/30 rounded-lg">
                    <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
                      <DollarSign size={14} />
                      Purchase Details
                    </div>
                    <div className="text-2xl font-black text-purple-400">
                      {deed.purchase_price.toLocaleString()} {deed.purchase_currency}
                    </div>
                  </div>

                  {deed.previous_owner_username && (
                    <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700">
                      <div className="text-xs text-slate-500 mb-1">Previous Owner</div>
                      <div className="text-sm text-slate-300">{deed.previous_owner_username}</div>
                    </div>
                  )}

                  <div className="pt-4 border-t border-slate-700">
                    <div className="text-xs text-slate-500 text-center">
                      Title Deed ID: {deed.id}
                    </div>
                    <div className="text-xs text-slate-600 text-center mt-1">
                      Property ID: {deed.house_id}
                    </div>
                  </div>

                  <div className="bg-purple-600/5 p-3 rounded-lg border border-purple-600/20">
                    <p className="text-xs text-slate-400 text-center">
                      🔒 This official document certifies legal ownership of the property listed above.
                      Issued by KapitalistCraft Trade Center.
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TitleDeeds;
