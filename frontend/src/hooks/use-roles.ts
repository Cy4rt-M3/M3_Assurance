import { create } from 'zustand';

export type UserRole = 'super_admin' | 'compliance_manager' | 'security_analyst' | 'auditor' | 'executive' | 'viewer';

export interface RoleInfo {
  id: UserRole;
  label: string;
  description: string;
  color: string;
  bgColor: string;
  borderColor: string;
  initials: string;
  permissions: {
    canEdit: boolean;
    canDelete: boolean;
    canGenerate: boolean;
    canApprove: boolean;
    canManageUsers: boolean;
    canExport: boolean;
  };
}

export const ROLES: Record<UserRole, RoleInfo> = {
  super_admin: {
    id: 'super_admin',
    label: 'Super Admin',
    description: 'Full system access with all permissions',
    color: 'text-danger',
    bgColor: 'bg-danger/15',
    borderColor: 'border-danger/30',
    initials: 'SA',
    permissions: { canEdit: true, canDelete: true, canGenerate: true, canApprove: true, canManageUsers: true, canExport: true },
  },
  compliance_manager: {
    id: 'compliance_manager',
    label: 'Compliance Manager',
    description: 'Manage frameworks, evidence, and generate reports',
    color: 'text-primary',
    bgColor: 'bg-primary/15',
    borderColor: 'border-primary/30',
    initials: 'CM',
    permissions: { canEdit: true, canDelete: false, canGenerate: true, canApprove: true, canManageUsers: false, canExport: true },
  },
  security_analyst: {
    id: 'security_analyst',
    label: 'Security Analyst',
    description: 'Review risks, evidence, and compliance status',
    color: 'text-cyber',
    bgColor: 'bg-cyber/15',
    borderColor: 'border-cyber/30',
    initials: 'SA',
    permissions: { canEdit: true, canDelete: false, canGenerate: false, canApprove: false, canManageUsers: false, canExport: true },
  },
  auditor: {
    id: 'auditor',
    label: 'Auditor',
    description: 'Read-only access to audit trails and reports',
    color: 'text-warning',
    bgColor: 'bg-warning/15',
    borderColor: 'border-warning/30',
    initials: 'AU',
    permissions: { canEdit: false, canDelete: false, canGenerate: false, canApprove: false, canManageUsers: false, canExport: true },
  },
  executive: {
    id: 'executive',
    label: 'Executive',
    description: 'View dashboards and high-level reports',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/15',
    borderColor: 'border-purple-500/30',
    initials: 'EX',
    permissions: { canEdit: false, canDelete: false, canGenerate: false, canApprove: true, canManageUsers: false, canExport: true },
  },
  viewer: {
    id: 'viewer',
    label: 'Read-Only Viewer',
    description: 'Read-only access to all sections',
    color: 'text-muted-foreground',
    bgColor: 'bg-muted',
    borderColor: 'border-muted-foreground/30',
    initials: 'VW',
    permissions: { canEdit: false, canDelete: false, canGenerate: false, canApprove: false, canManageUsers: false, canExport: false },
  },
};

interface RoleState {
  currentRole: UserRole;
  setRole: (role: UserRole) => void;
}

export const useRoleStore = create<RoleState>((set) => ({
  currentRole: 'compliance_manager',
  setRole: (role) => set({ currentRole: role }),
}));
