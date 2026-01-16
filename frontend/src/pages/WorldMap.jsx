import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { 
  Map, ZoomIn, ZoomOut, Search, Crosshair, Layers, Mountain, Flag, Pickaxe, 
  Eye, RefreshCw, X, Navigation, Ruler, Info, Database, Globe, BarChart3
} from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const WorldMap = ({ user, onLogout }) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  
  // Map state
  const [viewMode, setViewMode] = useState('borders'); // borders, ores, density, satellite
  const [zoom, setZoom] = useState(0.05); // Start zoomed out to see all territories
  const [offset, setOffset] = useState({ x: 5000, z: 5000 }); // Center on the map
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  
  // Data state
  const [config, setConfig] = useState(null);
  const [territories, setTerritories] = useState([]);
  const [markers, setMarkers] = useState([]);
  const [countries, setCountries] = useState([]);
  const [microRegions, setMicroRegions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // UI state
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [selectedTerritory, setSelectedTerritory] = useState(null);
  const [selectedMicroRegion, setSelectedMicroRegion] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [coordInput, setCoordInput] = useState({ x: '', z: '' });
  const [hoveredItem, setHoveredItem] = useState(null);
  const [showLegend, setShowLegend] = useState(true);
  
  // Distance measurement
  const [measureMode, setMeasureMode] = useState(false);
  const [measurePoint1, setMeasurePoint1] = useState(null);
  const [measurePoint2, setMeasurePoint2] = useState(null);
  const [measuredDistance, setMeasuredDistance] = useState(null);
  
  // Layer toggles
  const [showOres, setShowOres] = useState(true);
  const [showMarkers, setShowMarkers] = useState(true);
  const [showRegions, setShowRegions] = useState(true);
  const [showGrid, setShowGrid] = useState(true);

  // Constants
  const BLOCK_SIZE = 1;
  const GRID_SIZE = 1000;
  const MAP_SIZE = 15000;

  useEffect(() => {
    loadMapData();
  }, []);

  useEffect(() => {
    drawMap();
  }, [territories, markers, microRegions, viewMode, zoom, offset, hoveredItem, selectedTerritory, selectedMicroRegion, measurePoint1, measurePoint2, showOres, showMarkers, showRegions, showGrid]);

  const loadMapData = async () => {
    try {
      const [configRes, territoriesRes, markersRes, countriesRes, regionsRes] = await Promise.all([
        axios.get(`${API}/map/config`),
        axios.get(`${API}/map/territories`),
        axios.get(`${API}/map/markers`),
        axios.get(`${API}/map/countries-with-territories`),
        axios.get(`${API}/map/micro-regions`)
      ]);
      
      setConfig(configRes.data);
      setTerritories(territoriesRes.data.territories || []);
      setMarkers(markersRes.data.markers || []);
      setCountries(countriesRes.data.countries || []);
      setMicroRegions(regionsRes.data.micro_regions || []);
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
    
    // Clear canvas with background
    ctx.fillStyle = viewMode === 'satellite' ? '#1a3a1a' : '#0f172a';
    ctx.fillRect(0, 0, width, height);
    
    // Draw grid
    if (showGrid) {
      ctx.strokeStyle = '#1e293b';
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
    }
    
    // Draw territories
    if (showRegions) {
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
        
        // Fill with territory/state color
        const color = territory.color || config?.states?.[territory.state]?.color || '#9333ea';
        const isSelected = selectedTerritory?.id === territory.id;
        
        if (viewMode === 'density') {
          // Show density based on infrastructure
          const region = microRegions.find(r => r.state === territory.state);
          const density = region?.infrastructure_density || 0.5;
          const alpha = Math.floor(density * 200).toString(16).padStart(2, '0');
          ctx.fillStyle = color + alpha;
        } else if (viewMode === 'ores' && showOres) {
          // Show ore richness
          const region = microRegions.find(r => r.state === territory.state);
          const totalValue = region?.available_value_grp || 0;
          const intensity = Math.min(totalValue / 1000000000, 1);
          const alpha = Math.floor(40 + intensity * 160).toString(16).padStart(2, '0');
          ctx.fillStyle = color + alpha;
        } else {
          ctx.fillStyle = isSelected ? color + 'aa' : color + '55';
        }
        ctx.fill();
        
        // Border
        ctx.strokeStyle = color;
        ctx.lineWidth = isSelected ? 4 : 2;
        ctx.stroke();
        
        // Territory name
        if (zoom > 0.02) {
          const centerX = polygon.reduce((sum, p) => sum + p.x, 0) / polygon.length;
          const centerZ = polygon.reduce((sum, p) => sum + p.z, 0) / polygon.length;
          const screenCenter = worldToScreen(centerX, centerZ);
          
          ctx.fillStyle = '#fff';
          ctx.font = `bold ${Math.max(10, 16 * zoom)}px sans-serif`;
          ctx.textAlign = 'center';
          ctx.shadowColor = 'black';
          ctx.shadowBlur = 4;
          ctx.fillText(territory.name, screenCenter.x, screenCenter.y);
          ctx.shadowBlur = 0;
          
          // Show economic multiplier
          const stateInfo = config?.states?.[territory.state];
          if (stateInfo && zoom > 0.03) {
            ctx.font = `${Math.max(8, 12 * zoom)}px sans-serif`;
            ctx.fillStyle = '#fbbf24';
            ctx.fillText(`×${stateInfo.economic_multiplier}`, screenCenter.x, screenCenter.y + 20 * zoom);
          }
        }
      });
    }
    
    // Draw micro-regions (ore deposits)
    if (viewMode === 'ores' && showOres) {
      microRegions.forEach(region => {
        const center = region.center || [0, 0];
        const screen = worldToScreen(center[0], center[1]);
        const isSelected = selectedMicroRegion?.region_id === region.region_id;
        
        // Draw region circle
        const radius = Math.max(15, 50 * zoom);
        ctx.beginPath();
        ctx.arc(screen.x, screen.y, radius, 0, Math.PI * 2);
        
        // Color based on total value
        const totalValue = region.available_value_grp || 0;
        const intensity = Math.min(totalValue / 500000000, 1);
        const hue = 120 - intensity * 120; // Green to red
        ctx.fillStyle = `hsla(${hue}, 70%, 50%, ${isSelected ? 0.8 : 0.5})`;
        ctx.fill();
        
        ctx.strokeStyle = isSelected ? '#fff' : '#888';
        ctx.lineWidth = isSelected ? 3 : 1;
        ctx.stroke();
        
        // Region label
        if (zoom > 0.03) {
          ctx.fillStyle = '#fff';
          ctx.font = `bold ${Math.max(8, 10 * zoom)}px sans-serif`;
          ctx.textAlign = 'center';
          ctx.fillText(region.region_id, screen.x, screen.y);
          
          // Value
          ctx.font = `${Math.max(6, 8 * zoom)}px sans-serif`;
          ctx.fillStyle = '#4ade80';
          const valueStr = formatValue(totalValue);
          ctx.fillText(valueStr, screen.x, screen.y + 12 * zoom);
        }
      });
    }
    
    // Draw markers
    if (showMarkers) {
      const allMarkers = [...markers];
      territories.forEach(t => {
        (t.markers || []).forEach(m => {
          allMarkers.push({ ...m, territory_name: t.name });
        });
      });
      
      allMarkers.forEach(marker => {
        if (viewMode === 'ores' && !marker.ore_type) return;
        
        const screen = worldToScreen(marker.x, marker.z);
        const markerType = config?.marker_types?.[marker.marker_type] || { icon: '📍' };
        const isSelected = selectedMarker?.id === marker.id;
        const isHovered = hoveredItem?.id === marker.id;
        
        // Draw marker
        ctx.beginPath();
        const radius = isSelected || isHovered ? 12 : 8;
        ctx.arc(screen.x, screen.y, radius * zoom, 0, Math.PI * 2);
        
        if (marker.ore_type) {
          const oreInfo = config?.ore_prices?.[marker.ore_type] || {};
          ctx.fillStyle = oreInfo.color || '#888';
        } else {
          ctx.fillStyle = isSelected ? '#9333ea' : '#6366f1';
        }
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw icon
        if (zoom > 0.03) {
          ctx.font = `${Math.max(12, 18 * zoom)}px sans-serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(markerType.icon, screen.x, screen.y);
        }
        
        // Draw name on hover/select
        if ((isSelected || isHovered) && zoom > 0.02) {
          ctx.fillStyle = '#fff';
          ctx.font = `bold ${12 * zoom}px sans-serif`;
          ctx.shadowColor = 'black';
          ctx.shadowBlur = 3;
          ctx.fillText(marker.name, screen.x, screen.y - 25 * zoom);
          ctx.shadowBlur = 0;
        }
      });
    }
    
    // Draw spawn point (0, 0)
    const spawnScreen = worldToScreen(0, 0);
    ctx.beginPath();
    ctx.arc(spawnScreen.x, spawnScreen.y, 12 * zoom, 0, Math.PI * 2);
    ctx.fillStyle = '#22c55e';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
    if (zoom > 0.02) {
      ctx.font = `${16 * zoom}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.fillText('🌟', spawnScreen.x, spawnScreen.y + 4);
    }
    
    // Draw measurement points and line
    if (measureMode || measurePoint1 || measurePoint2) {
      if (measurePoint1) {
        const p1Screen = worldToScreen(measurePoint1.x, measurePoint1.z);
        ctx.beginPath();
        ctx.arc(p1Screen.x, p1Screen.y, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#ef4444';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      
      if (measurePoint2) {
        const p2Screen = worldToScreen(measurePoint2.x, measurePoint2.z);
        ctx.beginPath();
        ctx.arc(p2Screen.x, p2Screen.y, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#ef4444';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw line between points
        if (measurePoint1) {
          const p1Screen = worldToScreen(measurePoint1.x, measurePoint1.z);
          ctx.beginPath();
          ctx.moveTo(p1Screen.x, p1Screen.y);
          ctx.lineTo(p2Screen.x, p2Screen.y);
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 2;
          ctx.setLineDash([5, 5]);
          ctx.stroke();
          ctx.setLineDash([]);
          
          // Draw distance label
          const midX = (p1Screen.x + p2Screen.x) / 2;
          const midY = (p1Screen.y + p2Screen.y) / 2;
          if (measuredDistance) {
            ctx.fillStyle = 'rgba(0,0,0,0.8)';
            ctx.fillRect(midX - 60, midY - 12, 120, 24);
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 12px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(`${measuredDistance.distance_blocks.toLocaleString()} blocks`, midX, midY + 4);
          }
        }
      }
    }
    
    // Draw coordinates overlay
    ctx.fillStyle = 'rgba(0,0,0,0.8)';
    ctx.fillRect(10, height - 35, 280, 28);
    ctx.fillStyle = '#fff';
    ctx.font = '12px monospace';
    ctx.textAlign = 'left';
    const centerWorld = screenToWorld(width / 2, height / 2);
    ctx.fillText(`Center: X: ${centerWorld.x}, Z: ${centerWorld.z} | Zoom: ${(zoom * 100).toFixed(1)}%`, 15, height - 15);
    
  }, [territories, markers, microRegions, config, viewMode, zoom, offset, selectedMarker, selectedTerritory, selectedMicroRegion, hoveredItem, measurePoint1, measurePoint2, measuredDistance, showOres, showMarkers, showRegions, showGrid]);

  const formatValue = (value) => {
    if (value >= 1e12) return (value / 1e12).toFixed(1) + 'T';
    if (value >= 1e9) return (value / 1e9).toFixed(1) + 'B';
    if (value >= 1e6) return (value / 1e6).toFixed(1) + 'M';
    if (value >= 1e3) return (value / 1e3).toFixed(1) + 'K';
    return value.toFixed(0);
  };

  // Mouse handlers
  const handleMouseDown = (e) => {
    if (!measureMode) {
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
    }
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
      const worldPos = screenToWorld(mouseX, mouseY);
      let found = null;
      
      // Check markers
      const allMarkers = [...markers];
      territories.forEach(t => (t.markers || []).forEach(m => allMarkers.push(m)));
      
      for (const marker of allMarkers) {
        const dist = Math.sqrt((marker.x - worldPos.x) ** 2 + (marker.z - worldPos.z) ** 2);
        if (dist < 100 / zoom) {
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

  const handleClick = async (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const worldPos = screenToWorld(mouseX, mouseY);
    
    // Measure mode
    if (measureMode) {
      if (!measurePoint1) {
        setMeasurePoint1(worldPos);
        setMeasurePoint2(null);
        setMeasuredDistance(null);
      } else if (!measurePoint2) {
        setMeasurePoint2(worldPos);
        // Calculate distance
        try {
          const res = await axios.get(`${API}/map/distance`, {
            params: { x1: measurePoint1.x, z1: measurePoint1.z, x2: worldPos.x, z2: worldPos.z }
          });
          setMeasuredDistance(res.data);
        } catch (err) {
          console.error('Distance calculation failed:', err);
        }
      } else {
        // Reset and start new measurement
        setMeasurePoint1(worldPos);
        setMeasurePoint2(null);
        setMeasuredDistance(null);
      }
      return;
    }
    
    // Check if clicked on a marker
    const allMarkers = [...markers];
    territories.forEach(t => (t.markers || []).forEach(m => allMarkers.push({ ...m, territory_name: t.name })));
    
    for (const marker of allMarkers) {
      const dist = Math.sqrt((marker.x - worldPos.x) ** 2 + (marker.z - worldPos.z) ** 2);
      if (dist < 100 / zoom) {
        setSelectedMarker(marker);
        setSelectedTerritory(null);
        setSelectedMicroRegion(null);
        return;
      }
    }
    
    // Check micro-regions
    for (const region of microRegions) {
      const center = region.center || [0, 0];
      const dist = Math.sqrt((center[0] - worldPos.x) ** 2 + (center[1] - worldPos.z) ** 2);
      if (dist < 200 / zoom) {
        setSelectedMicroRegion(region);
        setSelectedMarker(null);
        setSelectedTerritory(null);
        return;
      }
    }
    
    // Check if clicked on a territory
    for (const territory of territories) {
      const polygon = territory.polygon?.points || [];
      if (isPointInPolygon(worldPos.x, worldPos.z, polygon)) {
        setSelectedTerritory(territory);
        setSelectedMarker(null);
        setSelectedMicroRegion(null);
        return;
      }
    }
    
    setSelectedMarker(null);
    setSelectedTerritory(null);
    setSelectedMicroRegion(null);
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
    const delta = e.deltaY > 0 ? 0.85 : 1.15;
    setZoom(prev => Math.max(0.01, Math.min(2, prev * delta)));
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
      setZoom(0.1);
    } else if (result.polygon?.points?.length > 0) {
      const points = result.polygon.points;
      const centerX = points.reduce((sum, p) => sum + p.x, 0) / points.length;
      const centerZ = points.reduce((sum, p) => sum + p.z, 0) / points.length;
      setOffset({ x: centerX, z: centerZ });
      setZoom(0.05);
    }
    setSearchResults([]);
  };

  const clearMeasurement = () => {
    setMeasureMode(false);
    setMeasurePoint1(null);
    setMeasurePoint2(null);
    setMeasuredDistance(null);
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
            <p className="text-slate-400 text-sm">
              Seed: {config?.world_seed} | Server: KapitalistCraftRP.aternos.me
            </p>
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
                <SelectItem value="density"><BarChart3 className="inline mr-2" size={16} />Density</SelectItem>
                <SelectItem value="satellite"><Globe className="inline mr-2" size={16} />Satellite</SelectItem>
              </SelectContent>
            </Select>
            
            {/* Zoom controls */}
            <div className="flex gap-1">
              <Button variant="outline" size="icon" onClick={() => setZoom(z => Math.min(2, z * 1.3))}>
                <ZoomIn size={18} />
              </Button>
              <Button variant="outline" size="icon" onClick={() => setZoom(z => Math.max(0.01, z / 1.3))}>
                <ZoomOut size={18} />
              </Button>
              <Button variant="outline" size="icon" onClick={() => { setZoom(0.05); setOffset({ x: 5000, z: 5000 }); }}>
                <Navigation size={18} />
              </Button>
            </div>
            
            {/* Measure tool */}
            <Button 
              variant={measureMode ? "default" : "outline"} 
              size="icon"
              onClick={() => {
                if (measureMode) {
                  clearMeasurement();
                } else {
                  setMeasureMode(true);
                }
              }}
              className={measureMode ? "bg-red-600 hover:bg-red-700" : ""}
            >
              <Ruler size={18} />
            </Button>
            
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
            
            <Button variant="outline" onClick={loadMapData}>
              <RefreshCw size={18} />
            </Button>
          </div>
        </div>

        {/* Measurement info bar */}
        {measureMode && (
          <div className="mb-2 p-2 bg-red-900/30 border border-red-600/30 rounded-lg flex items-center gap-4">
            <Ruler className="text-red-400" size={20} />
            <span className="text-red-300">
              {!measurePoint1 && "Click to set first point"}
              {measurePoint1 && !measurePoint2 && `Point 1: (${measurePoint1.x}, ${measurePoint1.z}) - Click for second point`}
              {measuredDistance && `Distance: ${measuredDistance.distance_blocks.toLocaleString()} blocks (${measuredDistance.distance_km} km)`}
            </span>
            <Button size="sm" variant="destructive" onClick={clearMeasurement} className="ml-auto">
              <X size={14} className="mr-1" /> Clear
            </Button>
          </div>
        )}

        {/* Map Container */}
        <div className="flex gap-4">
          {/* Main Map */}
          <div 
            ref={containerRef}
            className="flex-1 h-[calc(100vh-220px)] bg-slate-900 rounded-lg border border-slate-700 overflow-hidden relative"
          >
            <canvas
              ref={canvasRef}
              className={measureMode ? "cursor-crosshair" : "cursor-grab active:cursor-grabbing"}
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
            <div className="w-80 space-y-4 max-h-[calc(100vh-220px)] overflow-y-auto">
              {/* Layer Toggles */}
              <Card className="glass-card border-purple-600/20">
                <CardHeader className="py-3">
                  <CardTitle className="text-sm">Layer Controls</CardTitle>
                </CardHeader>
                <CardContent className="py-2 space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Show Regions</Label>
                    <Switch checked={showRegions} onCheckedChange={setShowRegions} />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Show Markers</Label>
                    <Switch checked={showMarkers} onCheckedChange={setShowMarkers} />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Show Ores</Label>
                    <Switch checked={showOres} onCheckedChange={setShowOres} />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Show Grid</Label>
                    <Switch checked={showGrid} onCheckedChange={setShowGrid} />
                  </div>
                </CardContent>
              </Card>

              {/* States Legend */}
              <Card className="glass-card border-purple-600/20">
                <CardHeader className="py-3">
                  <CardTitle className="text-sm flex items-center justify-between">
                    States
                    <Button variant="ghost" size="sm" onClick={() => setShowLegend(false)}>
                      <X size={14} />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="py-2 space-y-2">
                  {Object.entries(config?.states || {}).map(([key, state]) => (
                    <div key={key} className="flex items-center gap-2 p-2 hover:bg-slate-800/30 rounded">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: state.color }} />
                      <span className="text-sm text-slate-300 flex-1">{state.name}</span>
                      <Badge variant="outline" className="text-xs text-yellow-400">
                        ×{state.economic_multiplier}
                      </Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Selected Item Info */}
              {selectedMicroRegion && (
                <Card className="glass-card border-green-600/20">
                  <CardHeader className="py-3">
                    <CardTitle className="text-sm flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Database size={16} className="text-green-400" />
                        {selectedMicroRegion.region_id}
                      </span>
                      <Button variant="ghost" size="sm" onClick={() => setSelectedMicroRegion(null)}>
                        <X size={14} />
                      </Button>
                    </CardTitle>
                    <CardDescription>{selectedMicroRegion.name}</CardDescription>
                  </CardHeader>
                  <CardContent className="py-2 space-y-3">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="p-2 bg-slate-800/50 rounded">
                        <p className="text-slate-400 text-xs">State</p>
                        <p className="font-bold">{selectedMicroRegion.state}</p>
                      </div>
                      <div className="p-2 bg-slate-800/50 rounded">
                        <p className="text-slate-400 text-xs">Multiplier</p>
                        <p className="font-bold text-yellow-400">×{selectedMicroRegion.economic_multiplier}</p>
                      </div>
                      <div className="p-2 bg-slate-800/50 rounded">
                        <p className="text-slate-400 text-xs">Available Value</p>
                        <p className="font-bold text-green-400">{formatValue(selectedMicroRegion.available_value_grp)} GRP</p>
                      </div>
                      <div className="p-2 bg-slate-800/50 rounded">
                        <p className="text-slate-400 text-xs">Total Value</p>
                        <p className="font-bold text-blue-400">{formatValue(selectedMicroRegion.total_value_grp)} GRP</p>
                      </div>
                    </div>
                    
                    <div className="text-xs text-slate-400">Top Minerals:</div>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {Object.entries(selectedMicroRegion.minerals || {})
                        .sort((a, b) => (b[1].available * b[1].base_price) - (a[1].available * a[1].base_price))
                        .slice(0, 6)
                        .map(([ore, data]) => {
                          const oreInfo = config?.ore_prices?.[ore] || {};
                          const availRatio = data.available / Math.max(data.total, 1);
                          return (
                            <div key={ore} className="p-2 bg-slate-800/30 rounded">
                              <div className="flex items-center justify-between mb-1">
                                <span className="flex items-center gap-1">
                                  <span>{oreInfo.icon}</span>
                                  <span className="text-sm" style={{ color: oreInfo.color }}>{oreInfo.name}</span>
                                </span>
                                <span className="text-xs text-green-400">
                                  {formatValue((data.available / 100) * data.base_price * selectedMicroRegion.economic_multiplier)} GRP
                                </span>
                              </div>
                              <Progress value={availRatio * 100} className="h-1" />
                              <div className="flex justify-between text-xs text-slate-500 mt-1">
                                <span>{formatValue(data.available)} avail</span>
                                <span>{(availRatio * 100).toFixed(1)}%</span>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </CardContent>
                </Card>
              )}

              {selectedTerritory && !selectedMicroRegion && (
                <Card className="glass-card border-purple-600/20">
                  <CardHeader className="py-3">
                    <CardTitle className="text-sm flex items-center justify-between">
                      Territory Info
                      <Button variant="ghost" size="sm" onClick={() => setSelectedTerritory(null)}>
                        <X size={14} />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="py-2">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded" style={{ backgroundColor: selectedTerritory.color }} />
                        <div>
                          <p className="font-bold text-white">{selectedTerritory.name}</p>
                          <p className="text-xs text-slate-400">{selectedTerritory.country_name || selectedTerritory.state}</p>
                        </div>
                      </div>
                      {config?.states?.[selectedTerritory.state] && (
                        <div className="p-2 bg-slate-800/50 rounded">
                          <p className="text-xs text-slate-400">Economic Multiplier</p>
                          <p className="font-bold text-yellow-400">×{config.states[selectedTerritory.state].economic_multiplier}</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {selectedMarker && (
                <Card className="glass-card border-purple-600/20">
                  <CardHeader className="py-3">
                    <CardTitle className="text-sm flex items-center justify-between">
                      Marker Info
                      <Button variant="ghost" size="sm" onClick={() => setSelectedMarker(null)}>
                        <X size={14} />
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="py-2">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">{config?.marker_types?.[selectedMarker.marker_type]?.icon || '📍'}</span>
                        <div>
                          <p className="font-bold text-white">{selectedMarker.name}</p>
                          <p className="text-xs text-slate-400">{config?.marker_types?.[selectedMarker.marker_type]?.name}</p>
                        </div>
                      </div>
                      <p className="text-sm text-slate-300 font-mono bg-slate-800/50 p-2 rounded">
                        X: {selectedMarker.x}, Z: {selectedMarker.z}
                      </p>
                      {selectedMarker.description && (
                        <p className="text-sm text-slate-400">{selectedMarker.description}</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Ore Prices Reference */}
              {viewMode === 'ores' && (
                <Card className="glass-card border-purple-600/20">
                  <CardHeader className="py-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Pickaxe size={16} /> Ore Prices
                    </CardTitle>
                    <CardDescription className="text-xs">Base price per 100 blocks³</CardDescription>
                  </CardHeader>
                  <CardContent className="py-2 max-h-48 overflow-y-auto">
                    <div className="space-y-1">
                      {Object.entries(config?.ore_prices || {})
                        .sort((a, b) => b[1].price - a[1].price)
                        .map(([key, ore]) => (
                        <div key={key} className="flex items-center justify-between p-1 hover:bg-slate-800/30 rounded text-xs">
                          <div className="flex items-center gap-1">
                            <span>{ore.icon}</span>
                            <span style={{ color: ore.color }}>{ore.name}</span>
                          </div>
                          <span className="font-mono text-green-400">{ore.price.toLocaleString()} GRP</span>
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
