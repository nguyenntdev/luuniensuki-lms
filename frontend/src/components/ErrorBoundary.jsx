"use client";

import { Component } from "react";

/**
 * Generic error boundary for the new feature pages.
 *
 * Logs to the console (Next.js will surface it in dev) and renders a polite
 * fallback. Keeps the rest of the page chrome intact when one widget blows
 * up.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    if (typeof window !== "undefined") {
      // eslint-disable-next-line no-console
      console.error("[ErrorBoundary] caught:", error, info);
    }
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      const message =
        this.state.error?.message || "Có lỗi xảy ra khi hiển thị nội dung.";
      return (
        <div
          role="alert"
          aria-live="assertive"
          className="m-6 rounded-lg border border-destructive bg-card p-6"
        >
          <h2 className="text-lg font-semibold text-destructive">
            Lỗi hiển thị
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">{message}</p>
          <button
            type="button"
            onClick={this.reset}
            className="mt-4 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Thử lại
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
