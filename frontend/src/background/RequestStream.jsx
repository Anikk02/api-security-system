// frontend/src/background/RequestStream.jsx
import React from 'react';
import { AnimatePresence } from 'framer-motion';
import RequestPacket from './RequestPacket';
import '../styles/packets.css';

const RequestStream = ({ packets }) => {
  return (
    <div className="request-stream">
      <div className="stream-header">
        <span className="stream-title">Live Request Stream</span>
        <span className="stream-count">{packets.length} requests</span>
      </div>
      <div className="stream-container">
        <AnimatePresence>
          {packets.slice(-5).reverse().map((packet, index) => (
            <RequestPacket key={packet.id} packet={packet} index={index} />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default RequestStream;