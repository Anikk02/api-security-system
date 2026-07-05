// frontend/src/background/index.js
export { default as SecurityBackground } from './SecurityBackground';
export { default as Pipeline } from './Pipeline';
export { default as PipelineNode } from './PipelineNode';
export { default as AnimatedConnection } from './AnimatedConnection';
export { default as RequestPacket } from './RequestPacket';
export { default as RequestStream } from './RequestStream';
export { default as MetricsPanel } from './MetricsPanel';
export { default as ActivityFeed } from './ActivityFeed';
export { default as FloatingParticles } from './FloatingParticles';
export { default as GridOverlay } from './GridOverlay';
export { default as GlowLayer } from './GlowLayer';
export { default as DecisionNode } from './DecisionNode';
export { default as RiskGauge } from './RiskGauge';
export { default as TrustGauge } from './TrustGauge';
export { default as BackgroundWrapper } from './BackgroundWrapper';

// Hooks
export { usePipelineAnimation } from './hooks/usePipelineAnimation';
export { useMetrics } from './hooks/useMetrics';
export { useActivityFeed } from './hooks/useActivityFeed';
export { usePackets } from './hooks/usePackets';
export { useParticles } from './hooks/useParticles';
// Data
export * from './data/metrics';
export * from './data/packets';
export * from './data/requests';
export * from './data/pipeline';

// Utils
export * from './utils/colors';
export * from './utils/animations';
export * from './utils/generators';
export * from './utils/constants';