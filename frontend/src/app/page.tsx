'use client';

import React from 'react';
import { AppLayout } from '@/components/assurance/layout/AppLayout';
import { useNavigationStore } from '@/hooks/use-navigation';
import { DashboardSection } from '@/components/assurance/dashboard/DashboardSection';
import { FrameworkSection } from '@/components/assurance/framework/FrameworkSection';
import { EvidenceSection } from '@/components/assurance/evidence/EvidenceSection';
import { RiskSection } from '@/components/assurance/risk/RiskSection';
import { ReportsSection } from '@/components/assurance/reports/ReportsSection';
import { TasksSection } from '@/components/assurance/tasks/TasksSection';
import { NotificationsSection } from '@/components/assurance/shared/NotificationsSection';
import { AuditLogsSection } from '@/components/assurance/shared/AuditLogsSection';
import { SettingsSection } from '@/components/assurance/shared/SettingsSection';

function SectionContent() {
  const { activeSection } = useNavigationStore();

  switch (activeSection) {
    case 'dashboard':
      return <DashboardSection />;
    case 'frameworks':
      return <FrameworkSection />;
    case 'evidence':
      return <EvidenceSection />;
    case 'risk':
      return <RiskSection />;
    case 'reports':
      return <ReportsSection />;
    case 'tasks':
      return <TasksSection />;
    case 'notifications':
      return <NotificationsSection />;
    case 'audit-logs':
      return <AuditLogsSection />;
    case 'settings':
      return <SettingsSection />;
    default:
      return <DashboardSection />;
  }
}

export default function Home() {
  return (
    <AppLayout>
      <SectionContent />
    </AppLayout>
  );
}
