// frontend/src/background/ActivityFeed.jsx
import React, { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import '../styles/activity.css';

const ActivityFeed = ({ activities }) => {
  const feedRef = useRef(null);

  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = 0;
    }
  }, [activities]);

  const getStatusIcon = (status) => {
    const icons = {
      Allowed: '✅',
      Blocked: '❌',
      Throttled: '⚠️'
    };
    return icons[status] || '●';
  };

  return (
    <div className="activity-feed">
      <div className="activity-header">
        <h4>Live Activity Feed</h4>
        <span className="activity-dot">●</span>
      </div>
      
      <div className="feed-content" ref={feedRef}>
        <AnimatePresence initial={false}>
          {activities.slice(0, 8).map((activity, index) => (
            <motion.div
              key={activity.id || index}
              className={`feed-item status-${activity.status.toLowerCase()}`}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <span className="feed-time">{activity.timestamp}</span>
              <span className="feed-status-icon">{getStatusIcon(activity.status)}</span>
              <span className="feed-status">{activity.status}</span>
              <span className="feed-endpoint">{activity.endpoint}</span>
              <span className="feed-ip">{activity.ip}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ActivityFeed;