// frontend/src/background/hooks/useParticles.js
import { useState, useEffect } from 'react';

export const useParticles = (count = 30) => {
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    const newParticles = Array.from({ length: count }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      speed: Math.random() * 2 + 1,
      opacity: Math.random() * 0.5 + 0.1
    }));
    setParticles(newParticles);
  }, [count]);

  return particles;
};