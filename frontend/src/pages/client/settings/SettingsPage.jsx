import React from 'react';

import ProfileSection from '../../../components/client/settings/ProfileSection';
import PreferencesSection from '../../../components/client/settings/PreferencesSection';
import SecuritySection from '../../../components/client/settings/SecuritySection';

import { useSettings } from '../../../hooks/client/useSettings';
import SkeletonCard from '../../../components/shared/Skeleton/SkeletonCard';

import './settingsPage.css';

function SettingsPage() {
  const { data, loading, error, regenerateKey } = useSettings();

  if (loading) {
    return (
      <div className="settings-container">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  return (
    <div className="settings-container animate-fade-in">

      <div className="settings-header">
        <h1 className="settings-title">⚙️ Settings</h1>
        <p className="settings-subtitle">
          Manage your profile and account configuration
        </p>
      </div>

      {error && (
        <p className="warning-text">
          ⚠️ Showing demo data (backend offline)
        </p>
      )}

      <ProfileSection />

      <SecuritySection
        profile={data?.profile}
        apiKey={data?.api_key}
        onRegenerateKey={regenerateKey}
      />

      <PreferencesSection />
    </div>
  );
}

export default SettingsPage;