'use client';

import React from 'react';
import { Lock } from 'lucide-react';
import { useRoleStore, ROLES } from '@/hooks/use-roles';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

type PermissionKey = 'canEdit' | 'canDelete' | 'canGenerate' | 'canApprove' | 'canManageUsers' | 'canExport';

/**
 * Hook to check if the current role has a specific permission.
 */
export function usePermission(permission: PermissionKey): boolean {
  const currentRole = useRoleStore((s) => s.currentRole);
  return ROLES[currentRole].permissions[permission];
}

/**
 * Hook to get current role info.
 */
export function useCurrentRole() {
  const currentRole = useRoleStore((s) => s.currentRole);
  return ROLES[currentRole];
}

interface PermissionGateProps {
  permission: PermissionKey;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showLock?: boolean;
}

/**
 * Conditionally renders children based on whether the current role has the required permission.
 * If showLock is true, renders a locked version instead of hiding completely.
 */
export function PermissionGate({ permission, children, fallback, showLock = false }: PermissionGateProps) {
  const hasPermission = usePermission(permission);

  if (hasPermission) {
    return <>{children}</>;
  }

  if (showLock) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="inline-flex items-center gap-1 opacity-50 cursor-not-allowed">
              <Lock className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Restricted</span>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p className="text-xs">Your role does not have permission to perform this action</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return <>{fallback}</>;
}

/**
 * Renders a permission indicator badge for buttons/actions.
 */
export function PermissionIndicator({ permission }: { permission: PermissionKey }) {
  const hasPermission = usePermission(permission);
  if (hasPermission) return null;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Lock className="h-3 w-3 text-muted-foreground/50" />
        </TooltipTrigger>
        <TooltipContent>
          <p className="text-xs">Requires {permission.replace('can', '').toLowerCase()} permission</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
