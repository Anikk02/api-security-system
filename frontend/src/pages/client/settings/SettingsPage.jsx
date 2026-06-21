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

  const apiKey = data?.api_key?.masked;
  const createdAt = data?.api_key?.created_at;
  const isActive = data?.api_key?.is_active;

  return (
    <div className="settings-container animate-fade-in">

      <div className="settings-header">
        <h1 className="settings-title">⚙️ Settings</h1>
        <p className="settings-subtitle">
          Manage your API access and account configuration
        </p>
      </div>

      {error && (
        <p className="warning-text">
          ⚠️ Showing demo data (backend offline)
        </p>
      )}

      <ProfileSection
        profile={data?.profile}
        onSave={updateProfile}
      />

      <ApiKeySection
        apiKey={apiKey}
        createdAt={createdAt}
        isActive={isActive}
        onRegenerate={regenerateKey}
      />

      <IntegrationSection
        apiKey={apiKey}
      />
    </div>
  );
}

export default SettingsPage;