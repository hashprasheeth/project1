import React from 'react';

interface ErrorBoundaryProps {
  readonly children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary] Unhandled render error:', error, info);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-background-dark p-8">
          <div className="flex flex-col items-center gap-4 bg-panel-dark border border-danger p-10 max-w-md text-center">
            <span className="material-symbols-outlined text-danger text-5xl">warning</span>
            <h2 className="text-xl font-bold text-white">Something went wrong</h2>
            <p className="text-text-dim text-sm">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <button
              className="mt-2 bg-primary text-black px-6 py-2 font-bold text-sm uppercase tracking-widest hover:bg-primary-dark transition-colors"
              onClick={this.handleRetry}
            >
              Retry
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
