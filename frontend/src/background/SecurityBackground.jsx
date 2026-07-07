// frontend/src/background/SecurityBackground.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Pipeline from './Pipeline';
import RequestStream from './RequestStream';
import MetricsPanel from './MetricsPanel';
import ActivityFeed from './ActivityFeed';
import FloatingParticles from './FloatingParticles';
import GridOverlay from './GridOverlay';
import GlowLayer from './GlowLayer';
import RiskGauge from './RiskGauge';
import TrustGauge from './TrustGauge';
import DecisionNode from './DecisionNode';
import { usePipelineAnimation } from './hooks/usePipelineAnimation';
import { useMetrics } from './hooks/useMetrics';
import { useActivityFeed } from './hooks/useActivityFeed';
import { usePackets } from './hooks/usePackets';
import '../styles/background.css';

const SecurityBackground = () => {
  const { pipelineState, triggerPipeline } = usePipelineAnimation();
  const { metrics, updateMetrics } = useMetrics();
  const { activities, addActivity } = useActivityFeed();
  const { packets, generatePacket } = usePackets();
  
  const [isMounted, setIsMounted] = useState(false);

  // Mark as mounted after initial render
  useEffect(() => {
    setIsMounted(true);
    return () => setIsMounted(false);
  }, []);

  // Use useCallback to prevent unnecessary re-renders
  const handlePacketGeneration = useCallback(() => {
    if (!isMounted) return;
    
    const packet = generatePacket();
    addActivity(packet);
    updateMetrics(packet);
    triggerPipeline(packet);
  }, [generatePacket, addActivity, updateMetrics, triggerPipeline, isMounted]);

  // Set up the interval with cleanup
  useEffect(() => {
    if (!isMounted) return;
    
    const interval = setInterval(handlePacketGeneration, 4000);
    
    // Generate first packet immediately
    const initialTimer = setTimeout(handlePacketGeneration, 500);
    
    return () => {
      clearInterval(interval);
      clearTimeout(initialTimer);
    };
  }, [isMounted, handlePacketGeneration]);

  // Memoize the last packet to prevent unnecessary re-renders
  const lastPacket = useMemo(() => {
    return packets.length > 0 ? packets[packets.length - 1] : null;
  }, [packets]);

  // If not mounted, show loading state
  if (!isMounted) {
    return <div className="background-loading" />;
  }

  return (
    <div className="background-wrapper">
      <GridOverlay />
      <GlowLayer />
      <FloatingParticles />
      
      <div className="background-container">
        <div className="left-section">
          <RequestStream packets={packets} />
          <Pipeline pipelineState={pipelineState} />
          <div className="gauges-section">
            <RiskGauge value={lastPacket?.riskScore || 50} />
            <TrustGauge value={lastPacket?.trustScore || 50} />
          </div>
          <DecisionNode pipelineState={pipelineState} />
        </div>
        
        <div className="right-section">
          <ActivityFeed activities={activities} />
        </div>
        
        <MetricsPanel metrics={metrics} />
      </div>
    </div>
  );
};

export default SecurityBackground;