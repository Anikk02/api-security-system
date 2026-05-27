import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import { MapPin, Activity, AlertTriangle } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import './ViolatorMap.css';

// Fix for default marker icons in react-leaflet
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const ViolatorMap = ({ violators = [], onViolatorClick }) => {
  const [center, setCenter] = useState([20, 0]);
  const [zoom, setZoom] = useState(2);
  const [selectedViolator, setSelectedViolator] = useState(null);

  // Mock geolocation data for violators
  const getCoordinatesForLocation = (location) => {
    const coordinates = {
      'New York': [40.7128, -74.0060],
      'London': [51.5074, -0.1278],
      'Tokyo': [35.6895, 139.6917],
      'Shanghai': [31.2304, 121.4737],
      'Mumbai': [19.0760, 72.8777],
      'Sydney': [-33.8688, 151.2093],
      'Sao Paulo': [-23.5505, -46.6333],
      'Moscow': [55.7558, 37.6173],
      'Berlin': [52.5200, 13.4050],
      'Paris': [48.8566, 2.3522],
      'Dubai': [25.2048, 55.2708],
      'Singapore': [1.3521, 103.8198],
      'Toronto': [43.6532, -79.3832],
      'Mexico City': [19.4326, -99.1332],
      'Johannesburg': [-26.2041, 28.0473],
    };
    return coordinates[location] || [Math.random() * 180 - 90, Math.random() * 360 - 180];
  };

  // Generate violator locations data
  const violatorLocations = violators.length > 0 ? violators : [
    { id: 'Bot-10554096', location: 'New York', threatScore: 0.88, violations: 25, status: 'active', ip: '192.168.1.1', lastSeen: new Date() },
    { id: 'Anon-44939162', location: 'London', threatScore: 0.92, violations: 18, status: 'active', ip: '192.168.1.2', lastSeen: new Date() },
    { id: 'user-johndoe', location: 'Tokyo', threatScore: 0.79, violations: 12, status: 'monitoring', ip: '192.168.1.3', lastSeen: new Date() },
    { id: 'Guest-34915749', location: 'Shanghai', threatScore: 0.76, violations: 10, status: 'active', ip: '192.168.1.4', lastSeen: new Date() },
    { id: 'user-bob', location: 'Mumbai', threatScore: 0.72, violations: 9, status: 'warning', ip: '192.168.1.5', lastSeen: new Date() },
    { id: 'Attacker-001', location: 'Sao Paulo', threatScore: 0.95, violations: 45, status: 'critical', ip: '192.168.1.6', lastSeen: new Date() },
    { id: 'Scanner-Probe', location: 'Moscow', threatScore: 0.87, violations: 32, status: 'active', ip: '192.168.1.7', lastSeen: new Date() },
    { id: 'Crawler-X', location: 'Berlin', threatScore: 0.65, violations: 8, status: 'monitoring', ip: '192.168.1.8', lastSeen: new Date() },
    { id: 'API-Abuser', location: 'Paris', threatScore: 0.81, violations: 22, status: 'active', ip: '192.168.1.9', lastSeen: new Date() },
    { id: 'Spam-Bot', location: 'Dubai', threatScore: 0.73, violations: 15, status: 'warning', ip: '192.168.1.10', lastSeen: new Date() },
    { id: 'Brute-Force', location: 'Singapore', threatScore: 0.91, violations: 38, status: 'critical', ip: '192.168.1.11', lastSeen: new Date() },
    { id: 'DDoS-Source', location: 'Toronto', threatScore: 0.94, violations: 52, status: 'critical', ip: '192.168.1.12', lastSeen: new Date() },
  ];

  const getMarkerColor = (threatScore) => {
    if (threatScore >= 0.9) return '#ef4444'; // Critical - Red
    if (threatScore >= 0.7) return '#f59e0b'; // High - Orange
    if (threatScore >= 0.5) return '#eab308'; // Medium - Yellow
    return '#3b82f6'; // Low - Blue
  };

  const getMarkerSize = (violations) => {
    const baseSize = 8;
    const size = baseSize + Math.min(violations / 5, 20);
    return size;
  };

  const getPulseAnimation = (threatScore) => {
    if (threatScore >= 0.8) return 'pulse-critical';
    if (threatScore >= 0.6) return 'pulse-high';
    return '';
  };

  const handleViolatorClick = (violator) => {
    setSelectedViolator(violator);
    if (onViolatorClick) {
      onViolatorClick(violator);
    }
  };

  return (
    <div className="violator-map card">
      <div className="violator-map__header">
        <div className="violator-map__title-section">
          <MapPin size={20} className="violator-map__header-icon" />
          <h3 className="violator-map__title">Live Threat Map</h3>
          <span className="violator-map__badge">Real-time</span>
        </div>
        <div className="violator-map__legend">
          <div className="violator-map__legend-item">
            <div className="violator-map__legend-color violator-map__legend-color--critical"></div>
            <span>Critical (≥0.9)</span>
          </div>
          <div className="violator-map__legend-item">
            <div className="violator-map__legend-color violator-map__legend-color--high"></div>
            <span>High (0.7-0.89)</span>
          </div>
          <div className="violator-map__legend-item">
            <div className="violator-map__legend-color violator-map__legend-color--medium"></div>
            <span>Medium (0.5-0.69)</span>
          </div>
          <div className="violator-map__legend-item">
            <div className="violator-map__legend-color violator-map__legend-color--low"></div>
            <span>Low (&lt;0.5)</span>
          </div>
        </div>
      </div>

      <div className="violator-map__container">
        <MapContainer
          center={center}
          zoom={zoom}
          style={{ height: '100%', width: '100%' }}
          className="violator-map__leaflet"
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
            subdomains="abcd"
          />
          
          {violatorLocations.map((violator, index) => {
            const coords = getCoordinatesForLocation(violator.location);
            const color = getMarkerColor(violator.threatScore);
            const size = getMarkerSize(violator.violations);
            const pulseClass = getPulseAnimation(violator.threatScore);
            
            return (
              <CircleMarker
                key={index}
                center={coords}
                radius={size}
                fillColor={color}
                color={color}
                weight={2}
                opacity={0.8}
                fillOpacity={0.6}
                eventHandlers={{
                  click: () => handleViolatorClick(violator),
                }}
              >
                <Tooltip 
                  permanent={false} 
                  direction="top" 
                  offset={[0, -10]}
                  className="violator-map__tooltip"
                >
                  <div className="violator-map__tooltip-content">
                    <strong>{violator.id}</strong>
                    <div>Score: {(violator.threatScore * 100).toFixed(0)}%</div>
                    <div>Violations: {violator.violations}</div>
                    <div>Location: {violator.location}</div>
                  </div>
                </Tooltip>
                <Popup className="violator-map__popup">
                  <div className="violator-map__popup-content">
                    <div className="violator-map__popup-header">
                      <AlertTriangle size={16} color={color} />
                      <strong>{violator.id}</strong>
                    </div>
                    <div className="violator-map__popup-details">
                      <div className="violator-map__popup-row">
                        <span>Threat Score:</span>
                        <span className="violator-map__popup-value" style={{ color }}>
                          {(violator.threatScore * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="violator-map__popup-row">
                        <span>Violations:</span>
                        <span className="violator-map__popup-value">{violator.violations}</span>
                      </div>
                      <div className="violator-map__popup-row">
                        <span>Location:</span>
                        <span className="violator-map__popup-value">{violator.location}</span>
                      </div>
                      <div className="violator-map__popup-row">
                        <span>IP Address:</span>
                        <span className="violator-map__popup-value">{violator.ip}</span>
                      </div>
                      <div className="violator-map__popup-row">
                        <span>Status:</span>
                        <span className={`violator-map__popup-status violator-map__popup-status--${violator.status}`}>
                          {violator.status}
                        </span>
                      </div>
                    </div>
                    <button 
                      className="violator-map__popup-btn"
                      onClick={() => handleViolatorClick(violator)}
                    >
                      View Details
                    </button>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>

      {selectedViolator && (
        <div className="violator-map__sidebar">
          <div className="violator-map__sidebar-header">
            <h4>Selected Violator</h4>
            <button onClick={() => setSelectedViolator(null)}>×</button>
          </div>
          <div className="violator-map__sidebar-content">
            <div className="violator-map__sidebar-field">
              <label>User ID:</label>
              <span>{selectedViolator.id}</span>
            </div>
            <div className="violator-map__sidebar-field">
              <label>Location:</label>
              <span>{selectedViolator.location}</span>
            </div>
            <div className="violator-map__sidebar-field">
              <label>Threat Score:</label>
              <div className="violator-map__sidebar-score">
                <div className="violator-map__sidebar-score-bar">
                  <div style={{ width: `${selectedViolator.threatScore * 100}%`, backgroundColor: getMarkerColor(selectedViolator.threatScore) }} />
                </div>
                <span>{(selectedViolator.threatScore * 100).toFixed(0)}%</span>
              </div>
            </div>
            <div className="violator-map__sidebar-field">
              <label>Violations:</label>
              <span>{selectedViolator.violations}</span>
            </div>
            <div className="violator-map__sidebar-field">
              <label>IP Address:</label>
              <span>{selectedViolator.ip}</span>
            </div>
            <div className="violator-map__sidebar-field">
              <label>Last Seen:</label>
              <span>{selectedViolator.lastSeen.toLocaleTimeString()}</span>
            </div>
          </div>
        </div>
      )}

      <div className="violator-map__stats">
        <div className="violator-map__stat">
          <Activity size={16} />
          <span>Active Threats: {violatorLocations.filter(v => v.threatScore >= 0.7).length}</span>
        </div>
        <div className="violator-map__stat">
          <MapPin size={16} />
          <span>Locations: {new Set(violatorLocations.map(v => v.location)).size}</span>
        </div>
        <div className="violator-map__stat">
          <AlertTriangle size={16} />
          <span>Critical: {violatorLocations.filter(v => v.threatScore >= 0.9).length}</span>
        </div>
      </div>
    </div>
  );
};

export default ViolatorMap;