import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { UserProvider, useUser } from './context/UserContext';
import Navbar from './components/Navbar';
import Landing from './pages/Landing';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import LAIMS from './pages/LAIMS';
import Analytics from './pages/Analytics';
import TrackDetails from './pages/TrackDetails';
import PodDetails from './pages/PodDetails';
import LoadingSpinner from './components/LoadingSpinner';
import './index.css';

// Protected route wrapper
function ProtectedRoute({ children }) {
  const { user, loading } = useUser();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (!user) {
    return <Navigate to="/" replace />;
  }
  
  return children;
}

function AppContent() {
  const { loading } = useUser();
  
  if (loading) {
    return (
      <div className="app-loading">
        <LoadingSpinner />
      </div>
    );
  }
  
  return (
    <>
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route 
            path="/dashboard/:userId" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/laims" 
            element={
              <ProtectedRoute>
                <LAIMS />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/analytics/:userId" 
            element={
              <ProtectedRoute>
                <Analytics />
              </ProtectedRoute>
            } 
          />
          <Route path="/tracks/:trackName" element={<TrackDetails />} />
          <Route 
            path="/pod" 
            element={
              <ProtectedRoute>
                <PodDetails />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </main>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <UserProvider>
        <AppContent />
      </UserProvider>
    </BrowserRouter>
  );
}
