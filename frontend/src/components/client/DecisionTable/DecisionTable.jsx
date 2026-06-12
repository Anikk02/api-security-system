import React, { useState } from 'react';
import { AlertTriangle, Eye, Shield, Clock } from 'lucide-react';
import './DecisionTable.css';

const DecisionTable = ({ data, title = 'Recent Decisions' }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');

  const getRiskBadgeClass = (score) => {
    if (score >= 0.8) return 'risk-badge--critical';
    if (score >= 0.6) return 'risk-badge--high';
    if (score >= 0.4) return 'risk-badge--medium';
    return 'risk-badge--low';
  };

  const getRiskLabel = (score) => {
    if (score >= 0.8) return 'Critical';
    if (score >= 0.6) return 'High';
    if (score >= 0.4) return 'Medium';
    return 'Low';
  };

  const filteredData = data.filter(item => {
    const matchesSearch = item.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filter === 'all' || 
      (filter === 'high' && item.threatScore >= 0.6) ||
      (filter === 'medium' && item.threatScore >= 0.4 && item.threatScore < 0.6) ||
      (filter === 'low' && item.threatScore < 0.4);
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="decision-table card">
      <div className="decision-table__header">
        <h3 className="decision-table__title">{title}</h3>
        <div className="decision-table__controls">
          <input
            type="text"
            placeholder="Search users..."
            className="decision-table__search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select className="decision-table__filter" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All Risks</option>
            <option value="high">High+</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>
      <div className="decision-table__table-wrapper">
        <table className="decision-table__table">
          <thead>
            <tr>
              <th>User ID / Account</th>
              <th>Violations</th>
              <th>Threat Score</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((user, index) => (
              <tr key={index}>
                <td className="decision-table__user">
                  <div className="decision-table__user-info">
                    <AlertTriangle size={16} className="decision-table__user-icon" />
                    <span>{user.id}</span>
                  </div>
                </td>
                <td>{user.violations}</td>
                <td>
                  <div className="decision-table__score">
                    <div className="decision-table__score-bar">
                      <div 
                        className="decision-table__score-fill" 
                        style={{ width: `${user.threatScore * 100}%` }}
                      />
                    </div>
                    <span>{(user.threatScore * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td>
                  <span className={`risk-badge ${getRiskBadgeClass(user.threatScore)}`}>
                    {getRiskLabel(user.threatScore)}
                  </span>
                </td>
                <td>
                  <button className="decision-table__action-btn">
                    <Eye size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DecisionTable;