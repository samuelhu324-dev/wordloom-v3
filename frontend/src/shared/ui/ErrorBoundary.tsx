import React from 'react';

type FallbackRenderArgs = {
  error: Error | null;
  reset: () => void;
};

type FallbackRender = (args: FallbackRenderArgs) => React.ReactNode;

interface ErrorBoundaryProps {
  fallback: React.ReactNode | FallbackRender;
  resetKeys?: unknown[];
  children?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

const arrayShallowEqual = (a?: unknown[], b?: unknown[]) => {
  if (!a && !b) return true;
  if (!a || !b) return false;
  if (a.length !== b.length) return false;
  return a.every((value, index) => Object.is(value, b[index]));
};

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false,
    error: null,
  };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary] captured error', error, info);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    if (this.state.hasError && !arrayShallowEqual(this.props.resetKeys, prevProps.resetKeys)) {
      this.reset();
    }
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      const { fallback } = this.props;
      if (typeof fallback === 'function') {
        return (fallback as FallbackRender)({ error: this.state.error, reset: this.reset });
      }
      return fallback;
    }

    return this.props.children;
  }
}
