import React from "react";
import "./UsageHeader.css";

const UsageHeader = ({ title, subtitle }) => {
  return (
    <div className="usage-header">
      <div className="usage-header-text">
        <h1 className="usage-title">{title}</h1>
        <p className="usage-subtitle">{subtitle}</p>
      </div>
    </div>
  );
};

export default UsageHeader;