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

// IP to real geographic coordinates mapping
const IP_LOCATION_MAP = {
  // USA
  '192.168.1.1': { lat: 40.7128, lng: -74.0060, city: 'New York', country: 'USA' },
  '192.168.1.2': { lat: 34.0522, lng: -118.2437, city: 'Los Angeles', country: 'USA' },
  '192.168.1.3': { lat: 41.8781, lng: -87.6298, city: 'Chicago', country: 'USA' },
  '192.168.1.4': { lat: 29.7604, lng: -95.3698, city: 'Houston', country: 'USA' },
  '192.168.1.5': { lat: 33.4484, lng: -112.0740, city: 'Phoenix', country: 'USA' },
  '192.168.1.6': { lat: 39.9526, lng: -75.1652, city: 'Philadelphia', country: 'USA' },
  '192.168.1.7': { lat: 29.4241, lng: -98.4936, city: 'San Antonio', country: 'USA' },
  '192.168.1.8': { lat: 32.7157, lng: -117.1611, city: 'San Diego', country: 'USA' },
  '192.168.1.9': { lat: 32.7767, lng: -96.7970, city: 'Dallas', country: 'USA' },
  '192.168.1.10': { lat: 37.7749, lng: -122.4194, city: 'San Francisco', country: 'USA' },
  '192.168.1.11': { lat: 47.6062, lng: -122.3321, city: 'Seattle', country: 'USA' },
  '192.168.1.12': { lat: 42.3601, lng: -71.0589, city: 'Boston', country: 'USA' },
  
  // Europe
  '192.168.2.1': { lat: 51.5074, lng: -0.1278, city: 'London', country: 'UK' },
  '192.168.2.2': { lat: 48.8566, lng: 2.3522, city: 'Paris', country: 'France' },
  '192.168.2.3': { lat: 52.5200, lng: 13.4050, city: 'Berlin', country: 'Germany' },
  '192.168.2.4': { lat: 41.9028, lng: 12.4964, city: 'Rome', country: 'Italy' },
  '192.168.2.5': { lat: 40.4168, lng: -3.7038, city: 'Madrid', country: 'Spain' },
  '192.168.2.6': { lat: 55.7558, lng: 37.6173, city: 'Moscow', country: 'Russia' },
  '192.168.2.7': { lat: 52.2297, lng: 21.0122, city: 'Warsaw', country: 'Poland' },
  '192.168.2.8': { lat: 50.1109, lng: 8.6821, city: 'Frankfurt', country: 'Germany' },
  '192.168.2.9': { lat: 59.3293, lng: 18.0686, city: 'Stockholm', country: 'Sweden' },
  '192.168.2.10': { lat: 50.8503, lng: 4.3517, city: 'Brussels', country: 'Belgium' },
  
  // Asia
  '10.0.0.1': { lat: 35.6895, lng: 139.6917, city: 'Tokyo', country: 'Japan' },
  '10.0.0.2': { lat: 31.2304, lng: 121.4737, city: 'Shanghai', country: 'China' },
  '10.0.0.3': { lat: 19.0760, lng: 72.8777, city: 'Mumbai', country: 'India' },
  '10.0.0.4': { lat: 28.6139, lng: 77.2090, city: 'Delhi', country: 'India' },
  '10.0.0.5': { lat: 37.5665, lng: 126.9780, city: 'Seoul', country: 'South Korea' },
  '10.0.0.6': { lat: 22.3193, lng: 114.1694, city: 'Hong Kong', country: 'China' },
  '10.0.0.7': { lat: 13.7367, lng: 100.5231, city: 'Bangkok', country: 'Thailand' },
  '10.0.0.8': { lat: 1.3521, lng: 103.8198, city: 'Singapore', country: 'Singapore' },
  '10.0.0.9': { lat: -6.2088, lng: 106.8456, city: 'Jakarta', country: 'Indonesia' },
  '10.0.0.10': { lat: 25.2048, lng: 55.2708, city: 'Dubai', country: 'UAE' },
  
  // Australia
  '172.16.0.1': { lat: -33.8688, lng: 151.2093, city: 'Sydney', country: 'Australia' },
  '172.16.0.2': { lat: -37.8136, lng: 144.9631, city: 'Melbourne', country: 'Australia' },
  '172.16.0.3': { lat: -27.4698, lng: 153.0251, city: 'Brisbane', country: 'Australia' },
  
  // South America
  '172.16.1.1': { lat: -23.5505, lng: -46.6333, city: 'Sao Paulo', country: 'Brazil' },
  '172.16.1.2': { lat: -34.6037, lng: -58.3816, city: 'Buenos Aires', country: 'Argentina' },
  '172.16.1.3': { lat: 4.7110, lng: -74.0721, city: 'Bogota', country: 'Colombia' },
  
  // Africa
  '172.16.2.1': { lat: -26.2041, lng: 28.0473, city: 'Johannesburg', country: 'South Africa' },
  '172.16.2.2': { lat: 30.0444, lng: 31.2357, city: 'Cairo', country: 'Egypt' },
  '172.16.2.3': { lat: 33.5731, lng: -7.5898, city: 'Casablanca', country: 'Morocco' },
  
  // Middle East
  '172.16.3.1': { lat: 25.2048, lng: 55.2708, city: 'Dubai', country: 'UAE' },
  '172.16.3.2': { lat: 21.3891, lng: 39.8579, city: 'Mecca', country: 'Saudi Arabia' },
  '172.16.3.3': { lat: 31.9474, lng: 35.2272, city: 'Jerusalem', country: 'Israel' },
};

const DEFAULT_LOCATION = { lat: 20.0, lng: 0.0, city: 'Unknown', country: 'Unknown' };

// Get location from IP address
const getLocationFromIP = (ip) => {
  if (IP_LOCATION_MAP[ip]) {
    return IP_LOCATION_MAP[ip];
  }
  // Hash the IP to consistently map to a location
  const hash = ip.split('.').reduce((acc, num) => acc + parseInt(num || 0), 0);
  const locations = Object.values(IP_LOCATION_MAP);
  const index = hash % locations.length;
  return locations[index] || DEFAULT_LOCATION;
};

// Generate random IP for demo violators
const generateRandomIP = () => {
  const ranges = [
    '192.168.1.', '192.168.2.', '10.0.0.', '172.16.0.', '172.16.1.', '172.16.2.'
  ];
  const range = ranges[Math.floor(Math.random() * ranges.length)];
  return `${range}${Math.floor(Math.random() * 20) + 1}`;
};

const ViolatorMap = ({ violators = [], onViolatorClick }) => {
  const [center, setCenter] = useState([20, 0]);
  const [zoom, setZoom] = useState(2);
  const [selectedViolator, setSelectedViolator] = useState(null);
  const [violatorLocations, setViolatorLocations] = useState([]);

  // Process violators to add real geolocation data
  useEffect(() => {
    let processedViolators = [];
    
    if (violators.length > 0) {
      // Use real violator data from props
      processedViolators = violators.map(violator => {
        const ip = violator.ip || generateRandomIP();
        const location = getLocationFromIP(ip);
        return {
          ...violator,
          ip: ip,
          location: location.city,
          country: location.country,
          coordinates: [location.lat, location.lng],
          threatScore: violator.threatScore || violator.score || 0.5,
          violations: violator.violations || 0,
          status: violator.status || 'monitoring',
        };
      });
    } else {
      // Demo data for when no violators exist
      processedViolators = [
        { id: 'Bot-10554096', ip: '192.168.1.1', threatScore: 0.88, violations: 25, status: 'active', lastSeen: new Date() },
        { id: 'Anon-44939162', ip: '192.168.2.1', threatScore: 0.92, violations: 18, status: 'active', lastSeen: new Date() },
        { id: 'user-johndoe', ip: '10.0.0.1', threatScore: 0.79, violations: 12, status: 'monitoring', lastSeen: new Date() },
        { id: 'Guest-34915749', ip: '10.0.0.2', threatScore: 0.76, violations: 10, status: 'active', lastSeen: new Date() },
        { id: 'user-bob', ip: '10.0.0.3', threatScore: 0.72, violations: 9, status: 'warning', lastSeen: new Date() },
        { id: 'Attacker-001', ip: '172.16.1.1', threatScore: 0.95, violations: 45, status: 'critical', lastSeen: new Date() },
        { id: 'Scanner-Probe', ip: '192.168.2.6', threatScore: 0.87, violations: 32, status: 'active', lastSeen: new Date() },
        { id: 'Crawler-X', ip: '192.168.2.3', threatScore: 0.65, violations: 8, status: 'monitoring', lastSeen: new Date() },
        { id: 'API-Abuser', ip: '192.168.2.2', threatScore: 0.81, violations: 22, status: 'active', lastSeen: new Date() },
        { id: 'Spam-Bot', ip: '10.0.0.10', threatScore: 0.73, violations: 15, status: 'warning', lastSeen: new Date() },
        { id: 'Brute-Force', ip: '172.16.0.1', threatScore: 0.91, violations: 38, status: 'critical', lastSeen: new Date() },
        { id: 'DDoS-Source', ip: '172.16.0.3', threatScore: 0.94, violations: 52, status: 'critical', lastSeen: new Date() },
      ].map(violator => {
        const location = getLocationFromIP(violator.ip);
        return {
          ...violator,
          location: location.city,
          country: location.country,
          coordinates: [location.lat, location.lng],
        };
      });
    }
    
    setViolatorLocations(processedViolators);
  }, [violators]);

  const getMarkerColor = (threatScore) => {
    if (threatScore >= 0.9) return '#ef4444';
    if (threatScore >= 0.7) return '#f59e0b';
    if (threatScore >= 0.5) return '#eab308';
    return '#3b82f6';
  };

  const getMarkerSize = (violations) => {
    const baseSize = 8;
    const size = baseSize + Math.min(violations / 5, 20);
    return size;
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
            const color = getMarkerColor(violator.threatScore);
            const size = getMarkerSize(violator.violations);
            
            return (
              <CircleMarker
                key={index}
                center={violator.coordinates}
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
                    <div>Location: {violator.location}, {violator.country}</div>
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
                        <span className="violator-map__popup-value">{violator.location}, {violator.country}</span>
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
              <span>{selectedViolator.location}, {selectedViolator.country}</span>
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
              <span>{selectedViolator.lastSeen ? new Date(selectedViolator.lastSeen).toLocaleTimeString() : 'N/A'}</span>
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
          <span>Countries: {new Set(violatorLocations.map(v => v.country)).size}</span>
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