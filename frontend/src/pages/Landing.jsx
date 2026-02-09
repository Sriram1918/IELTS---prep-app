import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { Flame, Target, Users, Zap, ChevronRight, Star, Play } from 'lucide-react';
import { useEffect, useState } from 'react';
import { client } from '../api/client';
import LandingNavbar from '../components/LandingNavbar';

export default function Landing() {
  const { user, login } = useUser();
  const navigate = useNavigate();
  const [demoLoading, setDemoLoading] = useState(false);

  // Redirect logged in users to dashboard
  useEffect(() => {
    if (user) {
      navigate(`/dashboard/${user.id}`);
    }
  }, [user, navigate]);

  // Handle demo login
  const handleDemoLogin = async () => {
    setDemoLoading(true);
    try {
      // Create demo user using diagnostic endpoint
      const demoUserData = {
        name: 'John Doe',
        email: 'johndoe@gmail.com',
        diagnostic_score: 6.0,  // Current band
        days_until_exam: 60,
        test_type: 'academic',
        daily_availability_minutes: 30
      };
      
      const response = await client.post('/onboarding/diagnostic', demoUserData);
      
      // Build user object from response
      const userData = {
        id: response.user_id,
        name: demoUserData.name,
        email: demoUserData.email,
        current_track: response.assigned_track,
        predicted_band: response.predicted_band
      };
      
      login(userData);
      navigate(`/dashboard/${response.user_id}`);
    } catch (error) {
      console.error('Demo login failed:', error);
      alert('Demo login failed. Please try again.');
    } finally {
      setDemoLoading(false);
    }
  };

  const features = [
    {
      icon: <Target size={32} />,
      title: 'Personalized Tracks',
      description: 'AI assigns you the perfect learning path based on your diagnostic score and timeline'
    },
    {
      icon: <Users size={32} />,
      title: 'Cohort Competition',
      description: 'Compare with peers at your level and stay motivated together'
    },
    {
      icon: <Zap size={32} />,
      title: 'L-AIMS Mock Tests',
      description: 'Weekly low-stakes IELTS simulations with real-time leaderboards'
    }
  ];

  const testimonials = [
    { name: 'Priya S.', score: '7.5', quote: 'Went from 6.0 to 7.5 in just 8 weeks!' },
    { name: 'Alex M.', score: '8.0', quote: 'The daily tasks kept me accountable every day.' },
    { name: 'Chen W.', score: '7.0', quote: 'Best IELTS prep platform I have used.' },
  ];

  return (
    <div className="landing">
      <LandingNavbar />
      
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <h1 className="hero-title">
              Master IELTS with <span className="gradient-text">Momentum</span>
            </h1>
            <p className="hero-subtitle">
              Personalized learning tracks, gamified progress, and AI coaching 
              to help you achieve your target band score.
            </p>
            <div className="hero-actions">
              <button 
                className="btn btn-primary btn-lg"
                onClick={handleDemoLogin}
                disabled={demoLoading}
              >
                <Play size={18} />
                {demoLoading ? 'Loading...' : 'Try Live Demo'}
                <ChevronRight size={20} />
              </button>
            </div>
            <div className="hero-stats">
              <div className="stat">
                <span className="stat-value">10,000+</span>
                <span className="stat-label">Students</span>
              </div>
              <div className="stat">
                <span className="stat-value">0.8+</span>
                <span className="stat-label">Avg. Band Increase</span>
              </div>
              <div className="stat">
                <span className="stat-value">95%</span>
                <span className="stat-label">Goal Achievement</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="container">
          <h2 className="section-title">Why Momentum?</h2>
          <div className="features-grid">
            {features.map((feature, i) => (
              <div key={i} className="feature-card glass-card">
                <div className="feature-icon">{feature.icon}</div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials">
        <div className="container">
          <h2 className="section-title">Success Stories</h2>
          <div className="testimonials-grid">
            {testimonials.map((t, i) => (
              <div key={i} className="testimonial-card glass-card">
                <div className="testimonial-score">
                  <Star size={16} fill="currentColor" />
                  <span>Band {t.score}</span>
                </div>
                <p className="testimonial-quote">"{t.quote}"</p>
                <span className="testimonial-name">{t.name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta">
        <div className="container">
          <div className="cta-card glass-card">
            <h2>Ready to Start Your IELTS Journey?</h2>
            <p>Take a free 5-minute diagnostic and get your personalized study plan.</p>
            <button 
              className="btn btn-primary btn-lg"
              onClick={() => navigate('/onboarding')}
            >
              Begin Now
              <ChevronRight size={20} />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
