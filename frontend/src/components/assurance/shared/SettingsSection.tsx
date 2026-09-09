'use client';

import React, { useState } from 'react';
import { Settings as SettingsIcon, User, Shield, Bell, Palette, Database, Key, Globe } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export function SettingsSection() {
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [slackNotifications, setSlackNotifications] = useState(false);
  const [autoSync, setAutoSync] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [evidenceExpiry, setEvidenceExpiry] = useState('90');

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Configure platform preferences and integrations
        </p>
      </div>

      <Tabs defaultValue="general" className="space-y-4">
        <TabsList className="bg-card border border-border">
          <TabsTrigger value="general" className="text-xs">General</TabsTrigger>
          <TabsTrigger value="notifications" className="text-xs">Notifications</TabsTrigger>
          <TabsTrigger value="integrations" className="text-xs">Integrations</TabsTrigger>
          <TabsTrigger value="security" className="text-xs">Security</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-4">
          {/* Profile */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-primary" />
                <CardTitle className="text-sm">Profile</CardTitle>
              </div>
              <CardDescription className="text-xs">Your account information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Full Name</Label>
                  <Input defaultValue="Alex Kowalski" className="h-8 text-xs bg-surface border-border" />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Email</Label>
                  <Input defaultValue="alex.kowalski@cybreach.io" className="h-8 text-xs bg-surface border-border" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Role</Label>
                  <Input defaultValue="GRC Analyst" className="h-8 text-xs bg-surface border-border" disabled />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Department</Label>
                  <Input defaultValue="Security & Compliance" className="h-8 text-xs bg-surface border-border" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Appearance */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Palette className="h-4 w-4 text-primary" />
                <CardTitle className="text-sm">Appearance</CardTitle>
              </div>
              <CardDescription className="text-xs">Customize the look and feel</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-xs text-foreground">Dark Mode</Label>
                  <p className="text-[11px] text-muted-foreground">Use dark theme for the interface</p>
                </div>
                <Switch checked={darkMode} onCheckedChange={setDarkMode} />
              </div>
              <Separator className="bg-border" />
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-xs text-foreground">Compact Mode</Label>
                  <p className="text-[11px] text-muted-foreground">Reduce spacing for higher information density</p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>

          {/* Data Management */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-primary" />
                <CardTitle className="text-sm">Data Management</CardTitle>
              </div>
              <CardDescription className="text-xs">Configure data retention and sync</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-xs text-foreground">Auto-sync Frameworks</Label>
                  <p className="text-[11px] text-muted-foreground">Automatically sync framework definitions</p>
                </div>
                <Switch checked={autoSync} onCheckedChange={setAutoSync} />
              </div>
              <Separator className="bg-border" />
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-xs text-foreground">Evidence Expiry Period</Label>
                  <p className="text-[11px] text-muted-foreground">Days before evidence requires revalidation</p>
                </div>
                <Input
                  type="number"
                  value={evidenceExpiry}
                  onChange={(e) => setEvidenceExpiry(e.target.value)}
                  className="w-20 h-8 text-xs bg-surface border-border text-center"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-primary" />
                <CardTitle className="text-sm">Notification Channels</CardTitle>
              </div>
              <CardDescription className="text-xs">Configure how you receive alerts</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-xs text-foreground">Email Notifications</Label>
                  <p className="text-[11px] text-muted-foreground">Receive alerts via email</p>
                </div>
                <Switch checked={emailNotifications} onCheckedChange={setEmailNotifications} />
              </div>
              <Separator className="bg-border" />
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-xs text-foreground">Slack Integration</Label>
                  <p className="text-[11px] text-muted-foreground">Send notifications to Slack channels</p>
                </div>
                <Switch checked={slackNotifications} onCheckedChange={setSlackNotifications} />
              </div>
              <Separator className="bg-border" />
              <div className="space-y-2">
                <Label className="text-xs text-foreground">Alert Types</Label>
                <div className="grid grid-cols-2 gap-2">
                  {['Missing Evidence', 'Validation Failed', 'Risk Increased', 'Framework Updated', 'Report Generated', 'Approval Required'].map((type) => (
                    <div key={type} className="flex items-center justify-between p-2 rounded-lg bg-surface border border-border/50">
                      <span className="text-xs text-foreground">{type}</span>
                      <Switch defaultChecked className="scale-75" />
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrations" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-primary" />
                <CardTitle className="text-sm">Connected Services</CardTitle>
              </div>
              <CardDescription className="text-xs">Manage platform integrations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { name: 'Strike Engine (Module 1)', status: 'connected', desc: 'Security scanning and event generation' },
                { name: 'Validator (Module 2)', status: 'connected', desc: 'Evidence validation and verification' },
                { name: 'SIEM Integration', status: 'connected', desc: 'Security event forwarding' },
                { name: 'JIRA Integration', status: 'disconnected', desc: 'Issue tracking and remediation' },
                { name: 'Slack Integration', status: 'disconnected', desc: 'Real-time notification alerts' },
              ].map((integration) => (
                <div key={integration.name} className="flex items-center justify-between p-3 rounded-lg bg-surface border border-border/50">
                  <div>
                    <p className="text-xs font-medium text-foreground">{integration.name}</p>
                    <p className="text-[11px] text-muted-foreground">{integration.desc}</p>
                  </div>
                  <Badge variant="outline" className={`text-[10px] ${
                    integration.status === 'connected'
                      ? 'bg-success/15 text-success border-success/30'
                      : 'bg-muted text-muted-foreground border-muted-foreground/30'
                  }`}>
                    {integration.status}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-primary" />
                <CardTitle className="text-sm">Security Settings</CardTitle>
              </div>
              <CardDescription className="text-xs">Manage security and access controls</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-xs text-foreground">Multi-Factor Authentication</Label>
                  <p className="text-[11px] text-muted-foreground">Require MFA for all users</p>
                </div>
                <Switch defaultChecked />
              </div>
              <Separator className="bg-border" />
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-xs text-foreground">Session Timeout</Label>
                  <p className="text-[11px] text-muted-foreground">Auto-lock after inactivity</p>
                </div>
                <Input defaultValue="30 min" className="w-24 h-8 text-xs bg-surface border-border text-center" />
              </div>
              <Separator className="bg-border" />
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-xs text-foreground">Audit Log Retention</Label>
                  <p className="text-[11px] text-muted-foreground">How long to keep audit records</p>
                </div>
                <Input defaultValue="365 days" className="w-24 h-8 text-xs bg-surface border-border text-center" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Key className="h-4 w-4 text-primary" />
                <CardTitle className="text-sm">API Keys</CardTitle>
              </div>
              <CardDescription className="text-xs">Manage API access for external integrations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-3 rounded-lg bg-surface border border-border/50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-foreground">Production API Key</p>
                    <p className="text-[11px] text-muted-foreground font-mono">cb_prod_**** **** **** a3f7</p>
                  </div>
                  <Button variant="outline" size="sm" className="text-xs h-7">Regenerate</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
