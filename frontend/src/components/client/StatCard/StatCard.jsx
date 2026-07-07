import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import './StatCard.css';

const StatCard = ({ title, value, trend, icon: Icon, color = 'info' }) => {
  const isPositive = trend > 0;
  
  return (
    <div className={`stat-card stat-card--${color}`}>
      <div className="stat-card__header">
        <div className="stat-card__icon">
          <Icon size={24} />
        </div>
        {trend !== undefined && (
          <div className={`stat-card__trend stat-card__trend--${isPositive ? 'up' : 'down'}`}>
            {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
            <span>{Math.abs(trend)}%</span>
          </div>
        )}
      </div>
      <div className="stat-card__value">{value}</div>
      <div className="stat-card__title">{title}</div>
    </div>
  );
};

export default StatCard;