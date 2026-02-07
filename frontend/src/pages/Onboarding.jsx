import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { client } from '../api/client';
import { ChevronRight, ChevronLeft, User, Calendar, Clock, BookOpen } from 'lucide-react';

const STEPS = ['Profile', 'Exam Details', 'Availability'];

export default function Onboarding() {
  const navigate = useNavigate();
  const { login } = useUser();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    diagnostic_score: 6.0,
    days_until_exam: 60,
    test_type: 'academic',
    weak_module: null,
    daily_availability_minutes: 45,
    weekend_availability: true
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  const handleNext = () => {
    if (step < STEPS.length - 1) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await client.post('/onboarding/diagnostic', formData);
      
      // Create user object for context
      const userData = {
        id: result.user_id,
        name: formData.name,
        email: formData.email,
        current_track: result.assigned_track,
        diagnostic_score: formData.diagnostic_score,
        exam_date: result.exam_date,
        current_streak: 0,
        predicted_band: result.predicted_band
      };
      
      login(userData);
      navigate(`/dashboard/${result.user_id}`);
    } catch (err) {
      setError(err.message || 'Failed to complete onboarding. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="onboarding">
      <div className="container">
        <div className="onboarding-card glass-card">
          {/* Progress */}
          <div className="onboarding-progress">
            {STEPS.map((s, i) => (
              <div 
                key={s} 
                className={`progress-step ${i <= step ? 'active' : ''} ${i < step ? 'completed' : ''}`}
              >
                <div className="step-number">{i + 1}</div>
                <span>{s}</span>
              </div>
            ))}
          </div>

          {/* Step Content */}
          <div className="onboarding-content">
            {step === 0 && (
              <div className="step-content">
                <div className="step-header">
                  <User size={32} />
                  <h2>Tell us about yourself</h2>
                </div>
                <div className="form-group">
                  <label>Full Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="Enter your name"
                    className="input"
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleChange('email', e.target.value)}
                    placeholder="you@example.com"
                    className="input"
                  />
                </div>
                <div className="form-group">
                  <label>Current IELTS Score (Mock/Diagnostic)</label>
                  <select 
                    value={formData.diagnostic_score}
                    onChange={(e) => handleChange('diagnostic_score', parseFloat(e.target.value))}
                    className="input"
                  >
                    {[5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0].map(score => (
                      <option key={score} value={score}>Band {score}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {step === 1 && (
              <div className="step-content">
                <div className="step-header">
                  <Calendar size={32} />
                  <h2>Your Exam Details</h2>
                </div>
                <div className="form-group">
                  <label>Days Until Exam</label>
                  <select 
                    value={formData.days_until_exam}
                    onChange={(e) => handleChange('days_until_exam', parseInt(e.target.value))}
                    className="input"
                  >
                    <option value={14}>2 weeks</option>
                    <option value={30}>1 month</option>
                    <option value={45}>6 weeks</option>
                    <option value={60}>2 months</option>
                    <option value={90}>3 months</option>
                    <option value={120}>4+ months</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Test Type</label>
                  <div className="radio-group">
                    {['academic', 'general'].map(type => (
                      <label key={type} className="radio-option">
                        <input
                          type="radio"
                          checked={formData.test_type === type}
                          onChange={() => handleChange('test_type', type)}
                        />
                        <span className="radio-label">{type.charAt(0).toUpperCase() + type.slice(1)}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <label>Weakest Module (Optional)</label>
                  <select 
                    value={formData.weak_module || ''}
                    onChange={(e) => handleChange('weak_module', e.target.value || null)}
                    className="input"
                  >
                    <option value="">No specific weakness</option>
                    <option value="reading">Reading</option>
                    <option value="writing">Writing</option>
                    <option value="speaking">Speaking</option>
                    <option value="listening">Listening</option>
                  </select>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="step-content">
                <div className="step-header">
                  <Clock size={32} />
                  <h2>Your Availability</h2>
                </div>
                <div className="form-group">
                  <label>Daily Study Time</label>
                  <select 
                    value={formData.daily_availability_minutes}
                    onChange={(e) => handleChange('daily_availability_minutes', parseInt(e.target.value))}
                    className="input"
                  >
                    <option value={15}>15 minutes</option>
                    <option value={30}>30 minutes</option>
                    <option value={45}>45 minutes</option>
                    <option value={60}>1 hour</option>
                    <option value={90}>1.5 hours</option>
                    <option value={120}>2+ hours</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.weekend_availability}
                      onChange={(e) => handleChange('weekend_availability', e.target.checked)}
                    />
                    <span>I can study on weekends</span>
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && <div className="error-message">{error}</div>}

          {/* Navigation */}
          <div className="onboarding-actions">
            {step > 0 && (
              <button className="btn btn-secondary" onClick={handleBack}>
                <ChevronLeft size={20} />
                Back
              </button>
            )}
            {step < STEPS.length - 1 ? (
              <button 
                className="btn btn-primary"
                onClick={handleNext}
                disabled={step === 0 && (!formData.name || !formData.email)}
              >
                Next
                <ChevronRight size={20} />
              </button>
            ) : (
              <button 
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading ? 'Creating Plan...' : 'Get My Plan'}
                <BookOpen size={20} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
