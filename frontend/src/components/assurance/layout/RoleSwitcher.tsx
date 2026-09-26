'use client';

import React from 'react';
import { Shield, ChevronDown, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { useRoleStore, ROLES, type UserRole } from '@/hooks/use-roles';

export function RoleSwitcher() {
  const { currentRole, setRole } = useRoleStore();
  const role = ROLES[currentRole];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="h-8 gap-1.5 px-2 hover:bg-accent/50"
        >
          <div className={`flex h-5 w-5 items-center justify-center rounded ${role.bgColor}`}>
            <Shield className={`h-3 w-3 ${role.color}`} />
          </div>
          <span className="text-xs font-medium text-foreground hidden sm:inline">{role.label}</span>
          <ChevronDown className="h-3 w-3 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Switch Role
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {Object.values(ROLES).map((r) => (
          <DropdownMenuItem
            key={r.id}
            onClick={() => setRole(r.id as UserRole)}
            className="flex items-start gap-2.5 py-2 cursor-pointer"
          >
            <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded ${r.bgColor} mt-0.5`}>
              <Shield className={`h-3.5 w-3.5 ${r.color}`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-medium text-foreground">{r.label}</span>
                {currentRole === r.id && (
                  <Check className="h-3.5 w-3.5 text-primary shrink-0" />
                )}
              </div>
              <p className="text-[10px] text-muted-foreground mt-0.5 leading-tight">{r.description}</p>
            </div>
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <div className="p-2">
          <p className="text-[10px] text-muted-foreground text-center">
            Role affects available actions across the platform
          </p>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
