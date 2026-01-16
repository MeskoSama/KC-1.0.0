import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Map, Plus, Edit2, Trash2, MapPin, Flag, Pickaxe, RefreshCw } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const AdminMapManagement = () => {
  const [territories, setTerritories] = useState([]);
  const [countries, setCountries] = useState([]);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Dialog states
  const [addTerritoryOpen, setAddTerritoryOpen] = useState(false);
  const [addMarkerOpen, setAddMarkerOpen] = useState(false);
  const [selectedTerritory, setSelectedTerritory] = useState(null);
  
  // Form states
  const [newTerritory, setNewTerritory] = useState({
    name: '',
    country_id: '',
    color: '#9333ea',
    points: [{ x: 0, z: 0 }]
  });
  
  const [newMarker, setNewMarker] = useState({
    name: '',
    marker_type: 'custom',
    x: 0,
    z: 0,
    description: '',
    ore_type: '',
    ore_quantity: 0
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [territoriesRes, configRes, countriesRes] = await Promise.all([
        axios.get(`${API}/map/territories`),
        axios.get(`${API}/map/config`),
        axios.get(`${API}/countries`)
      ]);
      
      setTerritories(territoriesRes.data.territories || []);
      setConfig(configRes.data);
      setCountries(countriesRes.data.countries || []);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load map data');
    }
  };

  const handleAddTerritory = async () => {
    if (!newTerritory.name || !newTerritory.country_id || newTerritory.points.length < 3) {
      toast.error('Please fill all fields and add at least 3 polygon points');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/map/territories`, {
        name: newTerritory.name,
        country_id: newTerritory.country_id,
        color: newTerritory.color,
        polygon: {
          points: newTerritory.points.map(p => ({ x: parseInt(p.x), z: parseInt(p.z) }))
        }
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Territory created!');
      setAddTerritoryOpen(false);
      setNewTerritory({ name: '', country_id: '', color: '#9333ea', points: [{ x: 0, z: 0 }] });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create territory');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTerritory = async (territoryId) => {
    if (!window.confirm('Delete this territory and all its markers?')) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/map/territories/${territoryId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Territory deleted');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    } finally {
      setLoading(false);
    }
  };

  const handleAddMarker = async () => {
    if (!newMarker.name || !selectedTerritory) {
      toast.error('Please fill all required fields');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const markerData = {
        name: newMarker.name,
        marker_type: newMarker.marker_type,
        x: parseInt(newMarker.x),
        z: parseInt(newMarker.z),
        description: newMarker.description
      };
      
      if (newMarker.marker_type === 'ore_deposit' && newMarker.ore_type) {
        markerData.ore_type = newMarker.ore_type;
        markerData.ore_quantity = parseFloat(newMarker.ore_quantity) || 0;
      }
      
      await axios.post(`${API}/admin/map/territories/${selectedTerritory.id}/markers`, markerData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Marker added!');
      setAddMarkerOpen(false);
      setNewMarker({ name: '', marker_type: 'custom', x: 0, z: 0, description: '', ore_type: '', ore_quantity: 0 });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add marker');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMarker = async (territoryId, markerId) => {
    if (!window.confirm('Delete this marker?')) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/map/territories/${territoryId}/markers/${markerId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Marker deleted');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete marker');
    } finally {
      setLoading(false);
    }
  };

  const addPolygonPoint = () => {
    setNewTerritory(prev => ({
      ...prev,
      points: [...prev.points, { x: 0, z: 0 }]
    }));
  };

  const removePolygonPoint = (index) => {
    setNewTerritory(prev => ({
      ...prev,
      points: prev.points.filter((_, i) => i !== index)
    }));
  };

  const updatePolygonPoint = (index, field, value) => {
    setNewTerritory(prev => ({
      ...prev,
      points: prev.points.map((p, i) => i === index ? { ...p, [field]: value } : p)
    }));
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="territories">
        <TabsList className="bg-slate-800/50">
          <TabsTrigger value="territories"><Flag size={16} className="mr-2" />Territories</TabsTrigger>
          <TabsTrigger value="markers"><MapPin size={16} className="mr-2" />Markers</TabsTrigger>
          <TabsTrigger value="ores"><Pickaxe size={16} className="mr-2" />Ore Prices</TabsTrigger>
        </TabsList>

        {/* Territories Tab */}
        <TabsContent value="territories" className="space-y-4">
          <Card className="glass-card border-purple-600/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Map className="text-purple-400" />
                  Territory Management
                </CardTitle>
                <CardDescription>Create and manage map territories for countries</CardDescription>
              </div>
              <Dialog open={addTerritoryOpen} onOpenChange={setAddTerritoryOpen}>
                <DialogTrigger asChild>
                  <Button className="btn-kapitalist" size="sm">
                    <Plus size={16} className="mr-1" /> Add Territory
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-slate-900 border-purple-600/30 max-w-2xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Create New Territory</DialogTitle>
                    <DialogDescription>Define a territory with polygon coordinates</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Territory Name</Label>
                        <Input
                          placeholder="e.g., Germania Mainland"
                          value={newTerritory.name}
                          onChange={(e) => setNewTerritory({ ...newTerritory, name: e.target.value })}
                          className="bg-slate-800 border-slate-700"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Country</Label>
                        <Select 
                          value={newTerritory.country_id} 
                          onValueChange={(v) => setNewTerritory({ ...newTerritory, country_id: v })}
                        >
                          <SelectTrigger className="bg-slate-800 border-slate-700">
                            <SelectValue placeholder="Select country" />
                          </SelectTrigger>
                          <SelectContent>
                            {countries.map(c => (
                              <SelectItem key={c} value={c}>{c}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Color</Label>
                      <div className="flex gap-2">
                        <Input
                          type="color"
                          value={newTerritory.color}
                          onChange={(e) => setNewTerritory({ ...newTerritory, color: e.target.value })}
                          className="w-12 h-10 p-1 bg-slate-800 border-slate-700"
                        />
                        <Input
                          value={newTerritory.color}
                          onChange={(e) => setNewTerritory({ ...newTerritory, color: e.target.value })}
                          className="bg-slate-800 border-slate-700 font-mono"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Polygon Points (X, Z coordinates)</Label>
                      <p className="text-xs text-slate-400">Define the boundary of the territory (minimum 3 points)</p>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {newTerritory.points.map((point, idx) => (
                          <div key={idx} className="flex gap-2 items-center">
                            <span className="text-xs text-slate-500 w-6">{idx + 1}.</span>
                            <Input
                              type="number"
                              placeholder="X"
                              value={point.x}
                              onChange={(e) => updatePolygonPoint(idx, 'x', e.target.value)}
                              className="bg-slate-800 border-slate-700 w-28"
                            />
                            <Input
                              type="number"
                              placeholder="Z"
                              value={point.z}
                              onChange={(e) => updatePolygonPoint(idx, 'z', e.target.value)}
                              className="bg-slate-800 border-slate-700 w-28"
                            />
                            <Button 
                              variant="destructive" 
                              size="sm" 
                              onClick={() => removePolygonPoint(idx)}
                              disabled={newTerritory.points.length <= 1}
                            >
                              <Trash2 size={14} />
                            </Button>
                          </div>
                        ))}
                      </div>
                      <Button variant="outline" size="sm" onClick={addPolygonPoint}>
                        <Plus size={14} className="mr-1" /> Add Point
                      </Button>
                    </div>
                    <Button onClick={handleAddTerritory} disabled={loading} className="w-full btn-kapitalist">
                      {loading ? 'Creating...' : 'Create Territory'}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Territory</TableHead>
                    <TableHead>Country</TableHead>
                    <TableHead>Color</TableHead>
                    <TableHead>Points</TableHead>
                    <TableHead>Markers</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {territories.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-slate-500">
                        No territories created yet
                      </TableCell>
                    </TableRow>
                  ) : (
                    territories.map(territory => (
                      <TableRow key={territory.id}>
                        <TableCell className="font-bold">{territory.name}</TableCell>
                        <TableCell>{territory.country_name || territory.country_id}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded" style={{ backgroundColor: territory.color }} />
                            <span className="font-mono text-xs">{territory.color}</span>
                          </div>
                        </TableCell>
                        <TableCell>{territory.polygon?.points?.length || 0}</TableCell>
                        <TableCell>{territory.markers?.length || 0}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex gap-1 justify-end">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => { setSelectedTerritory(territory); setAddMarkerOpen(true); }}
                            >
                              <MapPin size={14} className="mr-1" /> Add Marker
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleDeleteTerritory(territory.id)}
                              disabled={loading}
                            >
                              <Trash2 size={14} />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Markers Tab */}
        <TabsContent value="markers" className="space-y-4">
          <Card className="glass-card border-purple-600/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="text-purple-400" />
                All Markers
              </CardTitle>
              <CardDescription>Markers across all territories</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Icon</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Coordinates</TableHead>
                    <TableHead>Territory</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {territories.flatMap(territory => 
                    (territory.markers || []).map(marker => (
                      <TableRow key={marker.id}>
                        <TableCell className="text-xl">
                          {config?.marker_types?.[marker.marker_type]?.icon || '📍'}
                        </TableCell>
                        <TableCell className="font-bold">{marker.name}</TableCell>
                        <TableCell>{config?.marker_types?.[marker.marker_type]?.name || marker.marker_type}</TableCell>
                        <TableCell className="font-mono text-sm">
                          X: {marker.x}, Z: {marker.z}
                        </TableCell>
                        <TableCell>{territory.name}</TableCell>
                        <TableCell className="text-right">
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => handleDeleteMarker(territory.id, marker.id)}
                            disabled={loading}
                          >
                            <Trash2 size={14} />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                  {territories.every(t => !t.markers?.length) && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-slate-500">
                        No markers created yet
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Ore Prices Tab */}
        <TabsContent value="ores" className="space-y-4">
          <Card className="glass-card border-purple-600/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Pickaxe className="text-purple-400" />
                Ore Prices
              </CardTitle>
              <CardDescription>Price per 100 blocks³ in GRP</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {Object.entries(config?.ore_prices || {}).map(([key, ore]) => (
                  <div key={key} className="p-4 bg-slate-800/30 rounded-lg border border-slate-700/30">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">{ore.icon}</span>
                      <span className="font-bold" style={{ color: ore.color }}>{ore.name}</span>
                    </div>
                    <p className="text-2xl font-bold text-green-400">{ore.price.toLocaleString()} GRP</p>
                    <p className="text-xs text-slate-500">per 100 blocks³</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Marker Dialog */}
      <Dialog open={addMarkerOpen} onOpenChange={setAddMarkerOpen}>
        <DialogContent className="bg-slate-900 border-purple-600/30">
          <DialogHeader>
            <DialogTitle>Add Marker to {selectedTerritory?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Marker Name</Label>
              <Input
                placeholder="e.g., Capital City"
                value={newMarker.name}
                onChange={(e) => setNewMarker({ ...newMarker, name: e.target.value })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div className="space-y-2">
              <Label>Marker Type</Label>
              <Select 
                value={newMarker.marker_type} 
                onValueChange={(v) => setNewMarker({ ...newMarker, marker_type: v })}
              >
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(config?.marker_types || {}).map(([key, val]) => (
                    <SelectItem key={key} value={key}>
                      {val.icon} {val.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>X Coordinate</Label>
                <Input
                  type="number"
                  value={newMarker.x}
                  onChange={(e) => setNewMarker({ ...newMarker, x: e.target.value })}
                  className="bg-slate-800 border-slate-700"
                />
              </div>
              <div className="space-y-2">
                <Label>Z Coordinate</Label>
                <Input
                  type="number"
                  value={newMarker.z}
                  onChange={(e) => setNewMarker({ ...newMarker, z: e.target.value })}
                  className="bg-slate-800 border-slate-700"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Description (optional)</Label>
              <Input
                placeholder="Description..."
                value={newMarker.description}
                onChange={(e) => setNewMarker({ ...newMarker, description: e.target.value })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            
            {newMarker.marker_type === 'ore_deposit' && (
              <>
                <div className="space-y-2">
                  <Label>Ore Type</Label>
                  <Select 
                    value={newMarker.ore_type} 
                    onValueChange={(v) => setNewMarker({ ...newMarker, ore_type: v })}
                  >
                    <SelectTrigger className="bg-slate-800 border-slate-700">
                      <SelectValue placeholder="Select ore type" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(config?.ore_prices || {}).map(([key, ore]) => (
                        <SelectItem key={key} value={key}>
                          {ore.icon} {ore.name} ({ore.price} GRP/100)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Quantity (blocks³)</Label>
                  <Input
                    type="number"
                    value={newMarker.ore_quantity}
                    onChange={(e) => setNewMarker({ ...newMarker, ore_quantity: e.target.value })}
                    className="bg-slate-800 border-slate-700"
                  />
                </div>
              </>
            )}
            
            <Button onClick={handleAddMarker} disabled={loading} className="w-full btn-kapitalist">
              {loading ? 'Adding...' : 'Add Marker'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminMapManagement;
