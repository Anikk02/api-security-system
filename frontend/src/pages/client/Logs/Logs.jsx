import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';
import { dashboardService } from '../../../services/client/dashboardService';
import toast from 'react-hot-toast';
import './Logs.css';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const limit = 20;
  
  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await dashboardService.getDecisionLogs(currentPage, limit);
      setLogs(data);
      // Assuming total count from API or calculate from response length
      setTotalPages(Math.ceil(data.length / limit) || 1);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      toast.error('Failed to load logs');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchLogs();
  }, [currentPage]);
  
  const getActionBadge = (action) => {
    switch(action) {
      case 'block': return <span className="logs__badge logs__badge--blocked">Blocked</span>;
      case 'throttle': return <span className="logs__badge logs__badge--throttled">Throttled</span>;
      default: return <span className="logs__badge logs__badge--allowed">Allowed</span>;
    }
  };
  
  const filteredLogs = logs.filter(log =>
    log.userId?.toString().includes(searchTerm.toLowerCase()) ||
    log.ip?.includes(searchTerm) ||
    log.endpoint?.includes(searchTerm)
  );

  const formatFeature = (key) => {
    return key
    .replace(/ _/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  const formatValue = (val) => {
  if (val === null || val === undefined) return '-';

  if (typeof val === 'number') {
    // If it's a probability/score → show %
    if (val >= 0 && val <= 1) {
      return `${(val * 100).toFixed(0)}%`;
    }
    // Otherwise normal number
    return val.toFixed(2);
  }

  if (typeof val === 'boolean') {
    return val ? 'Yes' : 'No';
  }

  return String(val);
  };
  
  return (
    <div className="logs">
      <div className="logs__header">
        <h1 className="logs__title">Security Logs</h1>
        <div className="logs__controls">
          <div className="logs__search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Search logs by user, IP, or endpoint..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="logs__filter-btn" onClick={fetchLogs}>
            <RefreshCw size={18} />
            Refresh
          </button>
          <button className="logs__export-btn">
            <Download size={18} />
            Export
          </button>
        </div>
      </div>
      
      <div className="logs__table-wrapper">
        {loading ? (
          <div className="logs__loading">Loading logs...</div>
        ) : (
          <table className="logs__table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>User ID</th>
                <th>Endpoint</th>
                <th>IP Address</th>
                <th>Risk Score</th>
                <th>Action</th>
                <th>Explanation</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => (
                <tr key={log.id}>
                  <td>{log.timestamp?.toLocaleString()}</td>
                  <td>{log.userId || 'anonymous'}</td>
                  <td>{log.endpoint}</td>
                  <td>{log.ip}</td>
                  <td>
                    <div className="logs__score">
                      <div className="logs__score-bar">
                        <div className="logs__score-fill" style={{ width: `${log.riskScore * 100}%` }} />
                      </div>
                      <span>{(log.riskScore * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td>{getActionBadge(log.action)}</td>
                  <td className="logs__explanation">
                    <div className="logs__summary">
                      {log.explanation?.summary || log.explanation || "No explanation"}
                    </div>

                    {/*Factors*/}
                    {log.explanation?.details?.factors?.length > 0 && (
                      <ul className="logs__factors">
                        {log.explanation.details.factors.slice(0, 2).map((factor, i) => (
                          <li key={i}>⚠ {factor}</li>
                        ))}
                      </ul>
                    )}

                    {/*contributions (only top 2, readable */}
                    {log.explanation?.details?.feature_contributions && (
                      <div className="logs__contributions">
                        {Object.entries(log.explanation.details.feature_contributions)
                        .slice(0, 2)
                        .map(([key, val]) => (
                          <span key={key}>
                            {formatFeature(key)}:{formatValue(val)}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      
      {totalPages > 1 && (
        <div className="logs__pagination">
          <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>
            <ChevronLeft size={18} />
          </button>
          <span>Page {currentPage} of {totalPages}</span>
          <button onClick={() => setCurrentPage(p => p + 1)} disabled={currentPage === totalPages}>
            <ChevronRight size={18} />
          </button>
        </div>
      )}
    </div>
  );
};

export default Logs;