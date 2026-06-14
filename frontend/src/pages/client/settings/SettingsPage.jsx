import React from 'react';
import MainLayout from '../../../layouts/client/MainLayout';

import ApiKeySection from '../../../components/client/settings/ApiKeySection/ApiKeySection';
import ProfileSection from '../../../components/client/settings/ProfileSection/ProfileSection';
import IntegrationSection from '../../../components/client/settings/IntegrationSection/IntegrationSection';

import { useSettings } from '../../../hooks/client/useSettings';
import SkeletonCard from '../../../components/shared/Skeleton/SkeletonCard';

import './SettingsPage.css';

function SettingsPage() {
  const { data, loading, error, regenerateKey, updateProfile } = useSettings();

  if (loading) {
    return (
      <div className="settings-container">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (error) {
    return (
      <div className="settings-container">
        <p className="error-text">{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="settings-container empty-state">
        <h2>⚙️ Settings Not Available</h2>
        <p>
            Settings will be available after authentication and onboarding are completed.
        </p>
      </div>
    );
  }

  return (
    <div className="settings-container animate-fade-in">
      <h1 className="settings-title">Settings</h1>

      <ApiKeySection
        apiKey={data.api_key?.masked}
        onRegenerate={regenerateKey}
      />

      <ProfileSection
        email={data.profile?.email}
        onSave={updateProfile}
      />

      <IntegrationSection
        apiKey={data.api_key?.masked}
      />
    </div>
  );
}

export default SettingsPage;