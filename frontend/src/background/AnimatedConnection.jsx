// frontend/src/background/AnimatedConnection.jsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import '../styles/pipeline.css';

const AnimatedConnection = ({ x1, y1, x2, y2, isActive }) => {
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    if (isActive) {
      const interval = setInterval(() => {
        setParticles(prev => {
          const newParticle = {
            id: Date.now(),
            progress: 0
          };
          return [...prev, newParticle];
        });
      }, 800);

      return () => clearInterval(interval);
    }
  }, [isActive]);

  useEffect(() => {
    if (particles.length > 0) {
      const timer = setInterval(() => {
        setParticles(prev => 
          prev
            .map(p => ({ ...p, progress: p.progress + 0.02 }))
            .filter(p => p.progress <= 1)
        );
      }, 50);

      return () => clearInterval(timer);
    }
  }, [particles]);

  return (
    <svg
      className="animated-connection"
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none'
      }}
    >
      <defs>
        <linearGradient id={`gradient-${x1}-${y1}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="rgba(0, 255, 136, 0.1)" />
          <stop offset="100%" stopColor="rgba(0, 255, 136, 0.4)" />
        </linearGradient>
      </defs>
      
      <line
        x1={`${x1}%`}
        y1={`${y1}%`}
        x2={`${x2}%`}
        y2={`${y2}%`}
        className={`connection-line ${isActive ? 'active' : ''}`}
        stroke={isActive ? `url(#gradient-${x1}-${y1})` : 'rgba(0, 255, 136, 0.1)'}
        strokeWidth={isActive ? 2 : 1.5}
      />

      {particles.map((particle) => {
        const x = x1 + (x2 - x1) * particle.progress;
        const y = y1 + (y2 - y1) * particle.progress;
        return (
          <circle
            key={particle.id}
            cx={`${x}%`}
            cy={`${y}%`}
            r="3"
            fill="#00ff88"
            opacity="0.8"
          >
            <animate
              attributeName="opacity"
              values="0.8;0"
              dur="0.5s"
              begin="0s"
              repeatCount="1"
            />
          </circle>
        );
      })}
    </svg>
  );
};

export default AnimatedConnection;