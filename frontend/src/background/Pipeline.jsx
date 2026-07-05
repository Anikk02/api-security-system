// frontend/src/background/Pipeline.jsx
import React from 'react';
import PipelineNode from './PipelineNode';
import AnimatedConnection from './AnimatedConnection';
import '../styles/pipeline.css';

const Pipeline = ({ pipelineState }) => {
  const nodes = [
    { id: 'identity', label: 'Identity Engine', x: 10, y: 10 },
    { id: 'featureBuilder', label: 'Feature Builder', x: 10, y: 25 },
    { id: 'riskEngine', label: 'Risk Engine', x: 10, y: 40 },
    { id: 'trustEngine', label: 'Trust Engine', x: 10, y: 55 },
    { id: 'policyEngine', label: 'Policy Engine', x: 10, y: 70 },
    { id: 'penaltyManager', label: 'Penalty Manager', x: 10, y: 85 }
  ];

  return (
    <div className="pipeline-container">
      {nodes.map((node, index) => (
        <React.Fragment key={node.id}>
          <PipelineNode
            id={node.id}
            label={node.label}
            x={node.x}
            y={node.y}
            isActive={pipelineState[node.id]}
          />
          {index < nodes.length - 1 && (
            <AnimatedConnection
              x1={node.x + 15}
              y1={node.y + 6}
              x2={nodes[index + 1].x + 15}
              y2={nodes[index + 1].y}
              isActive={pipelineState[nodes[index + 1].id]}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export default Pipeline;