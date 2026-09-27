import { useEffect, useState } from 'react';
import { Building2, LoaderCircle, Pencil, Save } from 'lucide-react';
import api from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import {
  DEPENDENCY_CATEGORIES,
  DEPENDENCY_LABELS,
  INDUSTRIES,
  emptyDependencies,
  toggleDependency,
} from '@/lib/riskInvestigation';

export default function CompanyProfilePage() {
  const [companyName, setCompanyName] = useState('');
  const [industry, setIndustry] = useState(INDUSTRIES[0]);
  const [dependencies, setDependencies] = useState(emptyDependencies());
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [hasProfile, setHasProfile] = useState(false);

  useEffect(() => {
    let active = true;
    api
      .get('/company-profile')
      .then((response) => {
        if (!active) return;
        setCompanyName(response.data.company_name || '');
        setIndustry(response.data.industry || INDUSTRIES[0]);
        setDependencies({ ...emptyDependencies(), ...(response.data.dependencies || {}) });
        setHasProfile(true);
      })
      .catch(() => {
        if (active) setHasProfile(false);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const handleSave = async (event) => {
    event.preventDefault();
    setError('');
    setMessage('');
    setIsSaving(true);
    try {
      const response = await api.put('/company-profile', {
        company_name: companyName,
        industry,
        dependencies,
      });
      setDependencies({ ...emptyDependencies(), ...(response.data.dependencies || {}) });
      setHasProfile(true);
      setIsEditing(false);
      setMessage('Company profile updated.');
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Company profile could not be saved.');
    } finally {
      setIsSaving(false);
    }
  };

  const renderEditor = () => (
    <form onSubmit={handleSave} className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Edit Company Profile</CardTitle>
          <CardDescription>These selections drive company-relevant intelligence.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="profile-company-name">Company Name</label>
              <Input
                id="profile-company-name"
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="profile-industry">Industry</label>
              <select
                id="profile-industry"
                value={industry}
                onChange={(event) => setIndustry(event.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
              >
                {INDUSTRIES.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>
          </div>
          <DependencyEditor dependencies={dependencies} setDependencies={setDependencies} />
          <div className="flex gap-2">
            <Button type="submit" disabled={isSaving}>
              <Save className="mr-2 h-4 w-4" /> {isSaving ? 'Saving...' : 'Save Company Profile'}
            </Button>
            <Button type="button" variant="outline" onClick={() => setIsEditing(false)} disabled={isSaving}>
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </form>
  );

  if (isLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <LoaderCircle className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-center gap-4">
        <div className="rounded-full bg-primary/10 p-3">
          <Building2 className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Company Profile</h2>
          <p className="text-muted-foreground">
            The business context SupplySentry uses to identify company-relevant intelligence.
          </p>
        </div>
      </div>

      {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
      {message && <div className="rounded-md bg-green-500/10 p-3 text-sm text-green-600">{message}</div>}

      {isEditing ? renderEditor() : null}

      {hasProfile && !isEditing ? (
        <Card>
          <CardHeader className="flex-row items-start justify-between space-y-0">
            <div>
              <CardTitle className="text-2xl">{companyName}</CardTitle>
              <CardDescription>{industry}</CardDescription>
            </div>
            <Button onClick={() => setIsEditing(true)}>
              <Pencil className="mr-2 h-4 w-4" /> Edit Company Profile
            </Button>
          </CardHeader>
          <CardContent className="grid gap-5 md:grid-cols-2">
            {Object.entries(DEPENDENCY_CATEGORIES).map(([category]) => {
              const values = dependencies[category] || [];
              const shared = (values || []).filter(
                (value) => Object.entries(dependencies).filter(
                  ([otherCategory, list]) => otherCategory !== category && (list || []).includes(value),
                ).length > 0,
              );
              return (
                <div key={category} className="rounded-xl border border-border/60 p-4">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                    {DEPENDENCY_LABELS[category]}
                  </h3>
                  {values.length ? (
                    <ul className="mt-2 space-y-1 text-sm">
                      {values.map((value) => (
                        <li key={value} className="flex flex-wrap items-center gap-2">
                          <span className="text-emerald-500">✓</span>
                          <span>{value}</span>
                          {shared.includes(value) && (
                            <Badge variant="outline" className="text-[10px]">
                              also {Object.entries(dependencies)
                                .filter(([otherCategory, list]) => otherCategory !== category && (list || []).includes(value))
                                .map(([otherCategory]) => DEPENDENCY_LABELS[otherCategory] || otherCategory)
                                .join(', ')}
                            </Badge>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-sm text-muted-foreground">None</p>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      ) : null}

      {!hasProfile && !isEditing ? (
        <Card>
          <CardHeader>
            <CardTitle>No company profile yet</CardTitle>
            <CardDescription>
              Complete company setup to enable company-relevant intelligence.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => setIsEditing(true)}>
              <Pencil className="mr-2 h-4 w-4" /> Set up company profile
            </Button>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function DependencyEditor({ dependencies, setDependencies }) {
  return (
    <div className="grid gap-5 md:grid-cols-2">
      {Object.entries(DEPENDENCY_CATEGORIES).map(([category, options]) => (
        <fieldset key={category} className="rounded-xl border border-border/60 p-4">
          <legend className="px-1 text-sm font-semibold">{DEPENDENCY_LABELS[category]}</legend>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {options.map((option) => {
              const selected = (dependencies[category] || []).includes(option);
              return (
                <label key={option} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() => setDependencies((current) => toggleDependency(current, category, option))}
                  />
                  {option}
                </label>
              );
            })}
          </div>
        </fieldset>
      ))}
    </div>
  );
}
