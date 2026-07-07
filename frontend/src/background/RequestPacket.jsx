// frontend/src/background/RequestPacket.jsx
import React from 'react';
import { motion } from 'framer-motion';
import '../styles/packets.css';

const RequestPacket = ({ packet, index }) => {
  const getMethodColor = (method) => {
    const colors = {
      GET: '#3498db',
      POST: '#2ecc71',
      PUT: '#f1c40f',
      DELETE: '#e74c3c'
    };
    return colors[method] || '#00ff88';
  };

  const getStatusColor = (status) => {
    const colors = {
      Allowed: '#2ecc71',
      Blocked: '#e74c3c',
      Throttled: '#f1c40f'
    };
    return colors[status] || '#00ff88';
  };

  return (
    <motion.div
      className={`request-packet packet-${packet.method.toLowerCase()}`}
      initial={{ opacity: 0, x: -100 }}
      animate={{ 
        opacity: 1, 
        x: 0,
        transition: { duration: 0.5, delay: index * 0.1 }
      }}
      exit={{ 
        opacity: 0, 
        x: 100,
        transition: { duration: 0.3 }
      }}
      style={{
        position: 'relative',
        marginBottom: '6px',
        padding: '8px 12px',
        background: 'rgba(0, 255, 136, 0.05)',
        border: `1px solid ${getMethodColor(packet.method)}33`,
        borderRadius: '6px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        fontSize: '11px',
        color: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(5px)',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)'
      }}
    >
      <span 
        className="packet-method"
        style={{ color: getMethodColor(packet.method), fontWeight: 700 }}
      >
        {packet.method}
      </span>
      
      <span className="packet-endpoint" style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
        {packet.endpoint}
      </span>
      
      <span className="packet-ip" style={{ color: 'rgba(255, 255, 255, 0.3)', fontSize: '10px' }}>
        {packet.ip}
      </span>
      
      <span 
        className="packet-status"
        style={{
          padding: '2px 8px',
          borderRadius: '3px',
          background: `${getStatusColor(packet.status)}22`,
          color: getStatusColor(packet.status),
          fontSize: '9px',
          fontWeight: 600,
          textTransform: 'uppercase',
          marginLeft: 'auto'
        }}
      >
        {packet.status}
      </span>
    </motion.div>
  );
};

export default RequestPacket;