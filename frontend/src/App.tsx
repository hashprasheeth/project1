import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ErrorBoundary from '@/components/ErrorBoundary';
import LoadingSpinner from '@/components/LoadingSpinner';
import AppShell from '@/components/layout/AppShell';

const HomePage = lazy(() => import('@/pages/HomePage'));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'));
const ClassExplorerPage = lazy(() => import('@/pages/ClassExplorerPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <AppShell>
                <Suspense fallback={<LoadingSpinner message="Loading page..." />}>
                  <HomePage />
                </Suspense>
              </AppShell>
            }
          />
          <Route
            path="/analytics"
            element={
              <AppShell>
                <Suspense fallback={<LoadingSpinner message="Loading page..." />}>
                  <AnalyticsPage />
                </Suspense>
              </AppShell>
            }
          />
          <Route
            path="/classes"
            element={
              <AppShell>
                <Suspense fallback={<LoadingSpinner message="Loading page..." />}>
                  <ClassExplorerPage />
                </Suspense>
              </AppShell>
            }
          />
          <Route
            path="*"
            element={
              <Suspense fallback={<LoadingSpinner message="Loading page..." />}>
                <NotFoundPage />
              </Suspense>
            }
          />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
