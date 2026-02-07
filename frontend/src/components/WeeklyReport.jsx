import { useState, useEffect } from 'react';
import { 
  X, CheckCircle2, TrendingUp, Users, BrainCircuit, 
  ArrowRight, Clock, Target, Award
} from 'lucide-react';
import { client } from '../api/client';
import './WeeklyReport.css'; // We'll add this CSS later or use inline/index.css

export default function WeeklyReport({ userId, onClose }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(0); // 0: Intro, 1: Progress, 2: Social, 3: Adaptive, 4: Summary

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await client.get(`/analytics/${userId}/weekly-report`);
        setReport(data);
      } catch (err) {
        console.error("Failed to load report", err);
        // If 404 or error, we might just close it as it's not ready
        // But for development/demo we want to see it
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [userId]);

  if (loading) return null;
  if (!report) return null;

  // We can force show it for demo purposes if needed, 
  // but logically it should only show if is_aha_moment is true
  // For now, let's assume the parent component controls visibility based on triggers

  const nextStep = () => setStep(s => s + 1);

  const renderContent = () => {
    switch(step) {
      case 0: // Intro / Hook
        return (
          <div className="report-slide intro-slide">
            <div className="slide-icon-bg">
              <CheckCircle2 size={48} className="text-success" />
            </div>
            <h2>Week {report.week_number} Complete!</h2>
            <p className="slide-subtitle">You've hit a major milestone in your prep.</p>
            <div className="stat-highlight">
              <span className="stat-value">{report.concrete_progress.practice_minutes_this_week}</span>
              <span className="stat-label">Minutes Practiced</span>
            </div>
            <button className="btn btn-primary" onClick={nextStep}>
              See Your Highlights <ArrowRight size={16} />
            </button>
          </div>
        );

      case 1: // Anchor 1: Concrete Progress
        return (
          <div className="report-slide progress-slide">
             <div className="slide-header">
              <TrendingUp size={24} className="text-primary" />
              <h3>Concrete Progress</h3>
            </div>
            <div className="chart-visual">
              {/* Simple visual representation */}
              <div className="progress-ring-container">
                <div className="circle-bg"></div>
                <div className="circle-fill" style={{height: '100%'}}></div>
                <div className="content">
                    <span className="big-num">{report.concrete_progress.tasks_completed_this_week}</span>
                    <span className="sub-text">Tasks Done</span>
                </div>
              </div>
            </div>
            <p className="impact-text">
              That's <strong>{report.concrete_progress.practice_minutes_this_week} minutes</strong> of focused effort invested in your future.
            </p>
            <button className="btn btn-primary btn-full" onClick={nextStep}>Continue</button>
          </div>
        );

      case 2: // Anchor 2: Social Calibration
        const { ahead_behind, difference_percent, successful_users_avg_minutes } = report.social_calibration;
        const isAhead = ahead_behind === 'ahead';
        
        return (
          <div className="report-slide social-slide">
             <div className="slide-header">
              <Users size={24} className="text-warning" />
              <h3>Cohort Comparison</h3>
            </div>
            
            <div className="calibration-graph">
               <div className="bar-group">
                 <div className="bar-label">Success Avg</div>
                 <div className="bar ghost-bar" style={{height: '60%'}}>
                    <span>{successful_users_avg_minutes}m</span>
                 </div>
               </div>
               <div className="bar-group">
                 <div className="bar-label">You</div>
                 <div className={`bar user-bar ${isAhead ? 'success' : 'warning'}`} style={{height: isAhead ? '80%' : '40%'}}>
                    <span>{report.concrete_progress.practice_minutes_this_week}m</span>
                 </div>
               </div>
            </div>

            <p className="impact-text">
               You are <strong>{difference_percent}% {ahead_behind}</strong> of regular users who achieved their target Band 7.0 score.
            </p>
            <p className="subtitle-text">
              {report.social_calibration.benchmark_message}
            </p>
            <button className="btn btn-primary btn-full" onClick={nextStep}>Next</button>
          </div>
        );

      case 3: // Anchor 3: Adaptive Intelligence
         const { next_action, personalization_signal } = report.adaptive_intelligence;
         
        return (
          <div className="report-slide adaptive-slide">
             <div className="slide-header">
              <BrainCircuit size={24} className="text-accent" />
              <h3>Plan Adapted</h3>
            </div>
            
            <div className="ai-card glass-card">
              <div className="ai-pulse"></div>
              <p className="ai-signal">{personalization_signal}</p>
            </div>

            <div className="next-action-card">
              <Clock size={20} />
              <p>{next_action}</p>
            </div>

            <button className="btn btn-primary btn-full" onClick={nextStep}>See Full Summary</button>
          </div>
        );

      case 4: // Summary / Notification View
         return (
          <div className="report-slide summary-slide">
            <Award size={48} className="text-gold mb-4" />
            <h2>Great work, Fighter!</h2>
            <div className="summary-card glass-card">
                <p>
                  "{report.notification_message}"
                </p>
            </div>
            <button className="btn btn-primary btn-full" onClick={onClose}>
              Back to Dashboard
            </button>
          </div>
         );
    }
  };

  return (
    <div className="weekly-report-overlay">
      <div className="weekly-report-modal">
        <button className="close-btn" onClick={onClose}><X size={20}/></button>
        {renderContent()}
        <div className="step-indicators">
           {[0,1,2,3,4].map(s => (
             <div key={s} className={`step-dot ${s === step ? 'active' : ''} ${s < step ? 'completed' : ''}`}></div>
           ))}
        </div>
      </div>
    </div>
  );
}
