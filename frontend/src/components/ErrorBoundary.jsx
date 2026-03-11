import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', color: 'var(--error-color, #ef4444)' }}>
          <h3>Something went wrong</h3>
          <pre style={{ fontSize: '0.8rem', opacity: 0.7 }}>
            {this.state.error?.message}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}
