import { useNavigate, useLocation } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { Flame, LayoutDashboard, Trophy, BarChart2, LogOut, Menu, X } from 'lucide-react';
import { useState } from 'react';

export default function Navbar() {
  const { user, logout } = useUser();
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  if (!user) return null;

  const links = [
    { path: `/dashboard/${user.id}`, icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { path: '/laims', icon: <Trophy size={20} />, label: 'L-AIMS' },
    { path: `/analytics/${user.id}`, icon: <BarChart2 size={20} />, label: 'Analytics' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="navbar glass-card">
      <div className="container nav-content">
        <div className="nav-brand" onClick={() => navigate('/')}>
          <Flame className="brand-icon" />
          <span>Momentum</span>
        </div>

        {/* Desktop Menu */}
        <div className="nav-links desktop-only">
          {links.map((link) => (
            <button
              key={link.path}
              className={`nav-link ${location.pathname === link.path ? 'active' : ''}`}
              onClick={() => navigate(link.path)}
            >
              {link.icon}
              {link.label}
            </button>
          ))}
        </div>

        <div className="nav-actions desktop-only">
          <div className="streak-badge">
            <Flame size={16} fill="currentColor" />
            <span>{user.current_streak || 0}</span>
          </div>
          <button className="btn-icon" onClick={handleLogout}>
            <LogOut size={20} />
          </button>
        </div>

        {/* Mobile Toggle */}
        <button className="mobile-toggle" onClick={() => setIsOpen(!isOpen)}>
          {isOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="mobile-menu glass-card">
          {links.map((link) => (
            <button
              key={link.path}
              className={`mobile-link ${location.pathname === link.path ? 'active' : ''}`}
              onClick={() => {
                navigate(link.path);
                setIsOpen(false);
              }}
            >
              {link.icon}
              {link.label}
            </button>
          ))}
          <div className="mobile-footer">
            <div className="streak-badge">
              <Flame size={16} fill="currentColor" />
              <span>{user.current_streak || 0} Day Streak</span>
            </div>
            <button className="btn btn-secondary" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
