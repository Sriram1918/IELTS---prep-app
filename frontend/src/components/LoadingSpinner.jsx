import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ fullScreen = false }) {
  if (fullScreen) {
    return (
      <div className="loading-screen">
        <Loader2 className="spinner" size={48} />
        <p>Loading Momentum...</p>
      </div>
    );
  }
  return <Loader2 className="spinner" size={24} />;
}
