import { useState } from 'react';
import { Activity } from 'lucide-react';
import api from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import {
  DEPENDENCY_CATEGORIES,
  DEPENDENCY_LABELS,
  INDUSTRIES,
  emptyDependencies,
  toggleDependency,
} from '@/lib/riskInvestigation';

export default function CompanySetup() {
  const [companyName, setCompanyName] = useState('');
  const [industry, setIndustry] = useState(INDUSTRIES[0]);
  const [dependencies, setDependencies] = useState(emptyDependencies());
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsSaving(true);
    try {
      await api.put('/company-profile', { company_name: companyName, industry, dependencies });
      window.location.href = '/';
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Company profile could not be saved.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-3xl shadow-lg">
        <CardHeader className="space-y-2 text-center">
          <div className="flex justify-center mb-2">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Activity className="h-6 w-6 text-primary" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">Company Profile</CardTitle>
          <CardDescription>Tell SupplySentry which dependencies matter to your business.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6 text-left">
            {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="company-name">Company Name</label>
                <Input id="company-name" value={companyName} onChange={(event) => setCompanyName(event.target.value)} placeholder="TechNova Electronics" required />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="industry">Industry</label>
                <select id="industry" value={industry} onChange={(event) => setIndustry(event.target.value)} className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm">
                  {INDUSTRIES.map((option) => <option key={option} value={option}>{option}</option>)}
                </select>
              </div>
            </div>
            <div className="grid gap-5 md:grid-cols-2">
              {Object.entries(DEPENDENCY_CATEGORIES).map(([category, options]) => (
                <fieldset key={category} className="rounded-xl border border-border/60 p-4">
                  <legend className="px-1 text-sm font-semibold">{DEPENDENCY_LABELS[category]}</legend>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    {options.map((option) => {
                      const selected = (dependencies[category] || []).includes(option);
                      return (
                        <label key={option} className="flex items-center gap-2 text-sm">
                          <input type="checkbox" checked={selected} onChange={() => setDependencies((current) => toggleDependency(current, category, option))} />
                          {option}
                        </label>
                      );
                    })}
                  </div>
                </fieldset>
              ))}
            </div>
            <Button type="submit" className="w-full" disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save & Continue'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
