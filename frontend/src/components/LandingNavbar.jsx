import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, ChevronDown, User, BookOpen } from 'lucide-react';

export default function LandingNavbar() {
  const navigate = useNavigate();
  const [activeDropdown, setActiveDropdown] = useState(null);

  const menuItems = [
    {
      label: 'Features',
      items: [
        { title: 'ADAPTIVE LEARNING', links: [
          { label: 'AI-Powered Study Plans', href: '#' },
          { label: 'Dynamic Task Swapping', href: '#' },
          { label: 'Personalized Tracks', href: '#' },
          { label: 'Smart Progress Tracking', href: '#' },
        ]},
        { title: 'MOTIVATION SYSTEM', links: [
          { label: 'Daily Streak Rewards', href: '#' },
          { label: 'Challenge Pods', href: '#' },
          { label: 'Weekly Reports', href: '#' },
        ]}
      ]
    },
    {
      label: 'Practice',
      items: [
        { title: 'SKILL MODULES', links: [
          { label: 'Reading Strategies', href: '#' },
          { label: 'Writing Task 1 & 2', href: '#' },
          { label: 'Listening Drills', href: '#' },
          { label: 'Speaking Simulations', href: '#' },
        ]},
        { title: 'MOCK TESTS', links: [
          { label: 'L-AIMS Weekly Mocks', href: '#' },
          { label: 'Full Practice Tests', href: '#' },
          { label: 'Band Score Predictor', href: '#' },
          { label: 'Performance Analytics', href: '#' },
        ]}
      ]
    },
    {
      label: 'Community',
      items: [
        { title: 'SOCIAL LEARNING', links: [
          { label: 'Study Pods', href: '#' },
          { label: 'Peer Leaderboards', href: '#' },
          { label: 'Success Stories', href: '#' },
          { label: 'Discussion Forums', href: '#' },
        ]},
        { title: 'EXPERT SUPPORT', links: [
          { label: 'Writing Feedback', href: '#' },
          { label: 'Speaking Evaluation', href: '#' },
          { label: 'Study Tips Blog', href: '#' },
        ]}
      ]
    },
    {
      label: 'About',
      items: [
        { title: 'MOMENTUM ENGINE', links: [
          { label: 'How It Works', href: '#' },
          { label: 'Our Methodology', href: '#' },
          { label: 'Student Results', href: '#' },
          { label: 'Pricing Plans', href: '#' },
        ]},
        { title: 'HELP', links: [
          { label: 'Getting Started', href: '#' },
          { label: 'FAQs', href: '#' },
          { label: 'Contact Support', href: '#' },
          { label: 'Privacy & Terms', href: '#' },
        ]}
      ]
    }
  ];


  return (
    <nav className="landing-navbar">
      {/* Top Banner */}
      <div className="navbar-banner">
        <span>🎯 New: AI-Powered Band Score Prediction is here! </span>
        <a href="#" onClick={() => navigate('/onboarding')}>Try it free →</a>
      </div>

      {/* Main Navbar */}
      <div className="navbar-main">
        <div className="container navbar-container">
          {/* Brand */}
          <div className="navbar-brand" onClick={() => navigate('/')}>
            <Flame className="brand-icon" />
            <span className="brand-text">Momentum</span>
          </div>

          {/* Menu Items */}
          <div className="navbar-menu">
            {menuItems.map((menu, idx) => (
              <div 
                key={idx}
                className={`navbar-item ${activeDropdown === idx ? 'active' : ''}`}
                onMouseEnter={() => setActiveDropdown(idx)}
                onMouseLeave={() => setActiveDropdown(null)}
              >
                <button className="navbar-link">
                  {menu.label}
                  <ChevronDown size={14} />
                </button>

                {/* Dropdown */}
                {activeDropdown === idx && (
                  <div className="navbar-dropdown">
                    <div className="dropdown-content">
                      {menu.items.map((section, sIdx) => (
                        <div key={sIdx} className="dropdown-section">
                          <h4 className="section-title">{section.title}</h4>
                          <ul className="section-links">
                            {section.links.map((link, lIdx) => (
                              <li key={lIdx}>
                                <a href={link.href}>{link.label}</a>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="navbar-actions">
            <button 
              className="btn-signin"
              onClick={() => navigate('/onboarding')}
            >
              <User size={16} />
              Sign In
            </button>
            <button 
              className="btn btn-primary btn-sm"
              onClick={() => navigate('/onboarding')}
            >
              <BookOpen size={16} />
              Start Free
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
