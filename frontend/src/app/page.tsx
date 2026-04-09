'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/lib/auth/authContext';
import { getApiBaseUrl } from '@/lib/api/base-url';

type FeatureCard = {
  title: string;
  description: string;
  route: string;
};

type EndpointGroup = {
  title: string;
  endpoints: string[];
};

const FEATURE_CARDS: FeatureCard[] = [
  {
    title: 'AI Chat Triage',
    description: 'Start symptom conversations and emergency triage assistance.',
    route: '/dashboard',
  },
  {
    title: 'New Diagnosis',
    description: 'Run complete multi-agent diagnosis with treatment planning.',
    route: '/diagnosis',
  },
  {
    title: 'Voice Consultation',
    description: 'Use speech-to-text and voice diagnosis workflows.',
    route: '/voice',
  },
  {
    title: 'X-Ray Analysis',
    description: 'Upload and analyze X-ray images with AI support.',
    route: '/xray',
  },
  {
    title: 'RAG Assistant',
    description: 'Ask grounded questions over uploaded medical documents.',
    route: '/rag',
  },
  {
    title: 'Admin Monitoring',
    description: 'Review audit logs, clinician feedback, and bias monitoring.',
    route: '/admin',
  },
];

const ENDPOINT_GROUPS: EndpointGroup[] = [
  {
    title: 'Auth',
    endpoints: [
      '/auth/login',
      '/auth/register',
      '/auth/me',
      '/auth/change-password',
      '/auth/forgot-password',
      '/auth/reset-password',
    ],
  },
  {
    title: 'Chat & Triage',
    endpoints: ['/chat/chat', '/chat/analyze-symptoms', '/chat/history/{session_id}'],
  },
  {
    title: 'Diagnosis Agents',
    endpoints: ['/agents/diagnose', '/agents/diagnose/simple', '/agents/health'],
  },
  {
    title: 'Voice',
    endpoints: ['/voice/transcribe', '/voice/speak', '/voice/diagnose', '/voice/history/{session_id}'],
  },
  {
    title: 'Vision',
    endpoints: ['/vision/analyze', '/vision/xray/analyze', '/vision/analysis/{analysis_id}', '/vision/history'],
  },
  {
    title: 'RAG',
    endpoints: ['/rag/upload-pdf', '/rag/query'],
  },
  {
    title: 'User Data & Reports',
    endpoints: [
      '/users/dashboard',
      '/users/history/diagnoses',
      '/users/history/diagnosis/{diagnosis_id}',
      '/reports/diagnosis/{diagnosis_id}/pdf',
    ],
  },
  {
    title: 'Admin Audit & Monitoring',
    endpoints: [
      '/admin/stats/overview',
      '/admin/stats/diagnoses-by-day',
      '/admin/stats/distribution',
      '/admin/users/recent',
      '/admin/diagnoses/recent',
      '/admin/audit/logs',
      '/admin/audit/sessions/{session_id}',
      '/admin/audit/{audit_id}/feedback',
      '/admin/analytics/bias-check',
      '/admin/audit/seed-demo',
    ],
  },
];

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, loading, user } = useAuth();

  const apiBase = useMemo(() => getApiBaseUrl(), []);

  const handleFeatureAccess = (route: string) => {
    if (!isAuthenticated) {
      router.push(`/login?next=${encodeURIComponent(route)}`);
      return;
    }
    router.push(route);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 space-y-8">
        <section className="rounded-xl border bg-white p-8 shadow-sm">
          <h1 className="text-3xl font-bold text-gray-900">Welcome to Rural AI Doctor</h1>
          <p className="mt-3 text-gray-600 max-w-3xl">
            Central access page for all clinical and admin features. You can browse available API endpoints
            below. Feature usage from this page is allowed only after login.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            {!isAuthenticated && !loading ? (
              <>
                <Button asChild>
                  <Link href="/login">Login to Continue</Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link href="/register">Create Account</Link>
                </Button>
              </>
            ) : null}
            {isAuthenticated ? (
              <div className="rounded-md border bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                Logged in as {user?.email}
              </div>
            ) : null}
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-gray-900">Feature Access</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {FEATURE_CARDS.map((feature) => (
              <Card key={feature.route} className="h-full">
                <CardHeader className="gap-1">
                  <CardTitle>{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button className="w-full" onClick={() => handleFeatureAccess(feature.route)}>
                    {isAuthenticated ? 'Open Feature' : 'Login Required'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-gray-900">Project API Endpoints</h2>
          <div className="rounded-xl border bg-white p-5 shadow-sm">
            <p className="text-sm text-gray-600">
              Base URL: <span className="font-mono text-gray-800">{apiBase}</span>
            </p>
            <div className="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
              {ENDPOINT_GROUPS.map((group) => (
                <Card key={group.title}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg">{group.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <ul className="space-y-2">
                      {group.endpoints.map((endpoint) => (
                        <li key={endpoint} className="rounded-md bg-gray-50 px-3 py-2 font-mono text-sm text-gray-800">
                          {apiBase}
                          {endpoint}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
