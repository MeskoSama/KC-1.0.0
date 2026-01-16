import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Map, ZoomIn, ZoomOut, Search, Crosshair, Layers, Mountain, Flag, Pickaxe, Eye, RefreshCw, X, Navigation } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const WorldMap = ({ user, onLogout }) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  
  // Map state
  const [viewMode, setViewMode] = useState('borders'); // borders, ores, height
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, z: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  
  // Data state
  const [config, setConfig] = useState(null);
  const [territories, setTerritories] = useState([]);
  const [markers, setMarkers] = useState([]);
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // UI state
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [selectedTerritory, setSelectedTerritory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [coordInput, setCoordInput] = useState({ x: '', z: '' });
  const [hoveredItem, setHoveredItem] = useState(null);
  const [showLegend, setShowLegend] = useState(true);

  // Constants
  const BLOCK_SIZE = 1; // 1 pixel = 1 block at zoom 1
  const GRID_SIZE = 100; // Grid line every 100 blocks
  const MAP_SIZE = 30000; // -15000 to 15000

  useEffect(() => {
    loadMapData();
  }, []);

  useEffect(() => {
    drawMap();
  }, [territories, markers, viewMode, zoom, offset, hoveredItem, selectedTerritory]);

  const loadMapData = async () => {
    try {
      const [configRes, territoriesRes, markersRes, countriesRes] = await Promise.all([
        axios.get(`${API}/map/config`),
        axios.get(`${API}/map/territories`),
        axios.get(`${API}/map/markers`),
        axios.get(`${API}/map/countries-with-territories`)
      ]);
      
      setConfig(configRes.data);
      setTerritories(territoriesRes.data.territories || []);
      setMarkers(markersRes.data.markers || []);
      setCountries(countriesRes.data.countries || []);
    } catch (error) {
      console.error('Failed to load map data:', error);
    } finally {
      setLoading(false);
    }
  };

  const worldToScreen = (worldX, worldZ) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    return {
      x: centerX + (worldX - offset.x) * zoom * BLOCK_SIZE,
      y: centerY + (worldZ - offset.z) * zoom * BLOCK_SIZE
    };
  };

  const screenToWorld = (screenX, screenY) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, z: 0 };
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    return {
      x: Math.round((screenX - centerX) / (zoom * BLOCK_SIZE) + offset.x),
      z: Math.round((screenY - centerY) / (zoom * BLOCK_SIZE) + offset.z)
    };
  };

  const drawMap = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, width, height);
    
    // Draw grid
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    
    const gridSpacing = GRID_SIZE * zoom * BLOCK_SIZE;
    const startX = (width / 2 - offset.x * zoom * BLOCK_SIZE) % gridSpacing;
    const startY = (height / 2 - offset.z * zoom * BLOCK_SIZE) % gridSpacing;
    
    for (let x = startX; x < width; x += gridSpacing) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = startY; y < height; y += gridSpacing) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    
    // Draw territories (borders mode)
    if (viewMode === 'borders' || viewMode === 'ores') {
      territories.forEach(territory => {
        const polygon = territory.polygon?.points || [];
        if (polygon.length < 3) return;
        
        ctx.beginPath();
        const firstPoint = worldToScreen(polygon[0].x, polygon[0].z);
        ctx.moveTo(firstPoint.x, firstPoint.y);
        
        polygon.forEach((point, idx) => {
          if (idx > 0) {
            const screenPoint = worldToScreen(point.x, point.z);
            ctx.lineTo(screenPoint.x, screenPoint.y);
          }
        });
        ctx.closePath();
        
        // Fill with country color
        const color = territory.color || territory.country_color || '#9333ea';
        ctx.fillStyle = selectedTerritory?.id === territory.id 
          ? color + 'aa' 
          : color + '44';
        ctx.fill();
        
        // Border
        ctx.strokeStyle = color;
        ctx.lineWidth = selectedTerritory?.id === territory.id ? 3 : 2;
        ctx.stroke();
        
        // Territory name
        if (zoom > 0.3) {
          const centerX = polygon.reduce((sum, p) => sum + p.x, 0) / polygon.length;
          const centerZ = polygon.reduce((sum, p) => sum + p.z, 0) / polygon.length;
          const screenCenter = worldToScreen(centerX, centerZ);
          
          ctx.fillStyle = '#fff';
          ctx.font = `bold ${Math.max(10, 14 * zoom)}px sans-serif`;
          ctx.textAlign = 'center';
          ctx.fillText(territory.name, screenCenter.x, screenCenter.y);
        }
      });
    }
    
    // Draw markers
    const allMarkers = [...markers];
    territories.forEach(t => {
      (t.markers || []).forEach(m => {
        allMarkers.push({ ...m, territory_name: t.name });
      });
    });
    
    allMarkers.forEach(marker => {
      // Filter by view mode
      if (viewMode === 'ores' && !marker.ore_type) return;
      if (viewMode === 'height') return; // Height map doesn't show markers
      
      const screen = worldToScreen(marker.x, marker.z);
      const markerType = config?.marker_types?.[marker.marker_type] || { icon: '📍' };
      const isSelected = selectedMarker?.id === marker.id;
      const isHovered = hoveredItem?.id === marker.id;
      
      // Draw marker circle
      ctx.beginPath();
      const radius = isSelected || isHovered ? 12 : 8;
      ctx.arc(screen.x, screen.y, radius * zoom, 0, Math.PI * 2);
      
      if (marker.ore_type) {
        const oreInfo = config?.ore_prices?.[marker.ore_type] || {};
        ctx.fillStyle = oreInfo.color || '#888';
      } else {
        ctx.fillStyle = isSelected ? '#9333ea' : '#4c1d95';
      }
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
      
      // Draw icon/emoji
      if (zoom > 0.5) {
        ctx.font = `${Math.max(12, 16 * zoom)}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(markerType.icon, screen.x, screen.y);
      }
      
      // Draw name on hover
      if ((isSelected || isHovered) && zoom > 0.3) {
        ctx.fillStyle = '#fff';
        ctx.font = `bold ${12 * zoom}px sans-serif`;
        ctx.fillText(marker.name, screen.x, screen.y - 20 * zoom);
      }
    });
    
    // Draw spawn point (0, 0)
    const spawnScreen = worldToScreen(0, 0);
    ctx.beginPath();
    ctx.arc(spawnScreen.x, spawnScreen.y, 10 * zoom, 0, Math.PI * 2);
    ctx.fillStyle = '#22c55e';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.font = `${14 * zoom}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText('🌟', spawnScreen.x, spawnScreen.y + 4);
    
    // Draw coordinates overlay
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    ctx.fillRect(10, height - 30, 200, 25);
    ctx.fillStyle = '#fff';
    ctx.font = '12px monospace';
    ctx.textAlign = 'left';
    const centerWorld = screenToWorld(width / 2, height / 2);
    ctx.fillText(`Center: X: ${centerWorld.x}, Z: ${centerWorld.z} | Zoom: ${zoom.toFixed(2)}x`, 15, height - 12);
    
  }, [territories, markers, config, viewMode, zoom, offset, selectedMarker, selectedTerritory, hoveredItem]);

  // Mouse handlers
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    if (isDragging) {
      const dx = (e.clientX - dragStart.x) / (zoom * BLOCK_SIZE);
      const dy = (e.clientY - dragStart.y) / (zoom * BLOCK_SIZE);
      setOffset(prev => ({ x: prev.x - dx, z: prev.z - dy }));
      setDragStart({ x: e.clientX, y: e.clientY });
    } else {
      // Check for hover
      const worldPos = screenToWorld(mouseX, mouseY);
      let found = null;
      
      // Check markers
      const allMarkers = [...markers];
      territories.forEach(t => (t.markers || []).forEach(m => allMarkers.push(m)));
      
      for (const marker of allMarkers) {
        const dist = Math.sqrt((marker.x - worldPos.x) ** 2 + (marker.z - worldPos.z) ** 2);
        if (dist < 20 / zoom) {
          found = marker;
          break;
        }
      }
      
      setHoveredItem(found);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleClick = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const worldPos = screenToWorld(mouseX, mouseY);
    
    // Check if clicked on a marker
    const allMarkers = [...markers];
    territories.forEach(t => (t.markers || []).forEach(m => allMarkers.push({ ...m, territory_name: t.name })));
    
    for (const marker of allMarkers) {
      const dist = Math.sqrt((marker.x - worldPos.x) ** 2 + (marker.z - worldPos.z) ** 2);
      if (dist < 20 / zoom) {
        setSelectedMarker(marker);
        return;
      }
    }
    
    // Check if clicked on a territory
    for (const territory of territories) {
      const polygon = territory.polygon?.points || [];
      if (isPointInPolygon(worldPos.x, worldPos.z, polygon)) {
        setSelectedTerritory(territory);
        return;
      }
    }
    
    setSelectedMarker(null);
    setSelectedTerritory(null);
  };

  const isPointInPolygon = (x, z, polygon) => {
    if (polygon.length < 3) return false;
    
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const xi = polygon[i].x, zi = polygon[i].z;
      const xj = polygon[j].x, zj = polygon[j].z;
      
      if (((zi > z) !== (zj > z)) && (x < (xj - xi) * (z - zi) / (zj - zi) + xi)) {
        inside = !inside;
      }
    }
    return inside;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(prev => Math.max(0.1, Math.min(10, prev * delta)));
  };

  const goToCoordinates = () => {
    const x = parseInt(coordInput.x) || 0;
    const z = parseInt(coordInput.z) || 0;
    setOffset({ x, z });
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      const response = await axios.get(`${API}/map/search?query=${encodeURIComponent(searchQuery)}`);
      setSearchResults(response.data.results || []);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const goToSearchResult = (result) => {
    if (result.x !== undefined && result.z !== undefined) {
      setOffset({ x: result.x, z: result.z });
    } else if (result.polygon?.points?.length > 0) {
      const points = result.polygon.points;
      const centerX = points.reduce((sum, p) => sum + p.x, 0) / points.length;
      const centerZ = points.reduce((sum, p) => sum + p.z, 0) / points.length;
      setOffset({ x: centerX, z: centerZ });
    }
    setSearchResults([]);
  };

  // Resize canvas
  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      const container = containerRef.current;
      if (canvas && container) {
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;
        drawMap();
      }
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [drawMap]);

  if (loading) {
    return (
      <div className="min-h-screen kapitalist-bg">
        <Navbar user={user} onLogout={onLogout} />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center">
          <RefreshCw className="animate-spin text-purple-400" size={32} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen kapitalist-bg">
      <Navbar user={user} onLogout={onLogout} />
      
      <div className="container mx-auto px-4 py-4">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent flex items-center gap-2">
              <Map /> World Map
            </h1>
            <p className="text-slate-400 text-sm">Seed: {config?.world_seed} | Minecraft 1.21.1</p>
          </div>
          
          {/* Controls */}
          <div className="flex flex-wrap gap-2">
            {/* View Mode */}
            <Select value={viewMode} onValueChange={setViewMode}>
              <SelectTrigger className="w-40 bg-slate-800 border-slate-700">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="borders"><Flag className="inline mr-2" size={16} />Borders</SelectItem>
                <SelectItem value="ores"><Pickaxe className="inline mr-2" size={16} />Ores</SelectItem>
                <SelectItem value="height"><Mountain className="inline mr-2" size={16} />Height</SelectItem>
              </SelectContent>
            </Select>
            
            {/* Zoom controls */}
            <div className="flex gap-1">
              <Button variant="outline" size="icon" onClick={() => setZoom(z => Math.min(10, z * 1.2))}>
                <ZoomIn size={18} />
              </Button>
              <Button variant="outline" size="icon" onClick={() => setZoom(z => Math.max(0.1, z / 1.2))}>
                <ZoomOut size={18} />
              </Button>
              <Button variant="outline" size="icon" onClick={() => { setZoom(1); setOffset({ x: 0, z: 0 }); }}>
                <Navigation size={18} />
              </Button>
            </div>
            
            {/* Coordinate input */}
            <div className="flex gap-1">
              <Input
                placeholder="X"
                className="w-20 bg-slate-800 border-slate-700"
                value={coordInput.x}
                onChange={(e) => setCoordInput(prev => ({ ...prev, x: e.target.value }))}
              />
              <Input
                placeholder="Z"
                className="w-20 bg-slate-800 border-slate-700"
                value={coordInput.z}
                onChange={(e) => setCoordInput(prev => ({ ...prev, z: e.target.value }))}
              />
              <Button variant="outline" onClick={goToCoordinates}>
                <Crosshair size={18} />
              </Button>
            </div>
            
            {/* Search */}
            <div className="flex gap-1 relative">
              <Input
                placeholder="Search..."
                className="w-40 bg-slate-800 border-slate-700"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button variant="outline" onClick={handleSearch}>
                <Search size={18} />
              </Button>
              
              {searchResults.length > 0 && (
                <div className="absolute top-full left-0 mt-1 w-72 bg-slate-900 border border-slate-700 rounded-lg shadow-xl z-50 max-h-60 overflow-y-auto">
                  {searchResults.map((result, idx) => (
                    <div
                      key={idx}
                      className="p-2 hover:bg-slate-800 cursor-pointer border-b border-slate-700 last:border-0"
                      onClick={() => goToSearchResult(result)}
                    >
                      <p className="font-medium text-white">{result.name}</p>
                      <p className="text-xs text-slate-400">
                        {result.type} {result.x !== undefined && `(${result.x}, ${result.z})`}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <Button variant="outline" onClick={() => setShowLegend(!showLegend)}>
              <Layers size={18} />
            </Button>
          </div>
        </div>

        {/* Map Container */}
        <div className="flex gap-4">
          {/* Main Map */}
          <div 
            ref={containerRef}
            className="flex-1 h-[calc(100vh-200px)] bg-slate-900 rounded-lg border border-slate-700 overflow-hidden relative"
          >
            <canvas
              ref={canvasRef}
              className="cursor-grab active:cursor-grabbing"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onClick={handleClick}
              onWheel={handleWheel}
            />
          </div>
          
          {/* Side Panel */}
          {showLegend && (
            <div className="w-80 space-y-4">
              {/* Legend */}
              <Card className="glass-card border-purple-600/20">
                <CardHeader className="py-3">
                  <CardTitle className="text-sm flex items-center justify-between">
                    Legend
                    <Button variant="ghost" size="sm" onClick={() => setShowLegend(false)}>
                      <X size={14} />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="py-2 space-y-2">
                  {/* Countries */}
                  <div className="text-xs text-slate-400 mb-1">Countries</div>
                  {countries.map(country => (
                    <div key={country.country_id} className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: country.color }} />
                      <span className="text-sm text-slate-300">{country.country_name}</span>
                      <Badge variant="outline" className="text-xs ml-auto">
                        {country.territories?.length || 0}
                      </Badge>
                    </div>
                  ))}
                  
                  {/* Markers */}
                  <div className="text-xs text-slate-400 mt-3 mb-1">Markers</div>
                  <div className="grid grid-cols-2 gap-1 text-xs">
                    {Object.entries(config?.marker_types || {}).slice(0, 8).map(([key, val]) => (
                      <div key={key} className="flex items-center gap-1">
                        <span>{val.icon}</span>
                        <span className="text-slate-400 truncate">{val.name}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
              
              {/* Selected Item Info */}
              {(selectedMarker || selectedTerritory) && (
                <Card className="glass-card border-purple-600/20">
                  <CardHeader className="py-3">
                    <CardTitle className="text-sm flex items-center justify-between">
                      {selectedMarker ? 'Marker Info' : 'Territory Info'}
                      <Button variant="ghost" size="sm" onClick={() => { setSelectedMarker(null); setSelectedTerritory(null); }}>
                        <X size={14} />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="py-2">
                    {selectedMarker && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{config?.marker_types?.[selectedMarker.marker_type]?.icon || '📍'}</span>
                          <div>
                            <p className="font-bold text-white">{selectedMarker.name}</p>
                            <p className="text-xs text-slate-400">{config?.marker_types?.[selectedMarker.marker_type]?.name}</p>
                          </div>
                        </div>
                        <p className="text-sm text-slate-300 font-mono">
                          X: {selectedMarker.x}, Z: {selectedMarker.z}
                        </p>
                        {selectedMarker.description && (
                          <p className="text-sm text-slate-400">{selectedMarker.description}</p>
                        )}
                        {selectedMarker.ore_type && (
                          <div className="mt-2 p-2 bg-slate-800/50 rounded">
                            <p className="text-sm font-bold" style={{ color: config?.ore_prices?.[selectedMarker.ore_type]?.color }}>
                              {config?.ore_prices?.[selectedMarker.ore_type]?.icon} {config?.ore_prices?.[selectedMarker.ore_type]?.name}
                            </p>
                            <p className="text-xs text-slate-400">
                              Quantity: {selectedMarker.ore_quantity?.toLocaleString()} blocks³
                            </p>
                            <p className="text-sm text-green-400 font-bold">
                              Price: {config?.ore_prices?.[selectedMarker.ore_type]?.price} GRP per 100 blocks³
                            </p>
                            <p className="text-sm text-yellow-400">
                              Total Value: {((config?.ore_prices?.[selectedMarker.ore_type]?.price || 0) * (selectedMarker.ore_quantity || 0) / 100).toLocaleString()} GRP
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                    {selectedTerritory && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded" style={{ backgroundColor: selectedTerritory.color || selectedTerritory.country_color }} />
                          <div>
                            <p className="font-bold text-white">{selectedTerritory.name}</p>
                            <p className="text-xs text-slate-400">{selectedTerritory.country_name}</p>
                          </div>
                        </div>
                        <p className="text-sm text-slate-400">
                          Markers: {selectedTerritory.markers?.length || 0}
                        </p>
                        {selectedTerritory.markers?.length > 0 && (
                          <div className="space-y-1 mt-2">
                            {selectedTerritory.markers.map((m, idx) => (
                              <div 
                                key={idx} 
                                className="flex items-center gap-2 p-1 hover:bg-slate-800/50 rounded cursor-pointer"
                                onClick={() => { setSelectedMarker(m); setOffset({ x: m.x, z: m.z }); }}
                              >
                                <span>{config?.marker_types?.[m.marker_type]?.icon || '📍'}</span>
                                <span className="text-sm text-slate-300 truncate">{m.name}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
              
              {/* Ore Prices */}
              {viewMode === 'ores' && (
                <Card className="glass-card border-purple-600/20">
                  <CardHeader className="py-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Pickaxe size={16} /> Ore Prices
                    </CardTitle>
                    <CardDescription className="text-xs">Per 100 blocks³</CardDescription>
                  </CardHeader>
                  <CardContent className="py-2 max-h-60 overflow-y-auto">
                    <div className="space-y-1">
                      {Object.entries(config?.ore_prices || {}).map(([key, ore]) => (
                        <div key={key} className="flex items-center justify-between p-1 hover:bg-slate-800/30 rounded">
                          <div className="flex items-center gap-2">
                            <span>{ore.icon}</span>
                            <span className="text-sm" style={{ color: ore.color }}>{ore.name}</span>
                          </div>
                          <span className="text-sm font-mono text-green-400">{ore.price.toLocaleString()} GRP</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorldMap;
