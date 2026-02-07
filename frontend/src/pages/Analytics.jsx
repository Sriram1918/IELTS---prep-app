import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { client } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  TrendingUp, BookOpen, Mic, Pencil, Headphones, 
  Target, Calendar, Award
} from 'lucide-react';

const MODULE_ICONS = {
  reading: BookOpen,
  writing: Pencil,
  speaking: Mic,
  listening: Headphones
};

const MODULE_COLORS = {
  reading: '#10b981',
  writing: '#f59e0b',
  speaking: '#8b5cf6',
  listening: '#3b82f6'
};

export default function Analytics() {
  const { userId } = useParams();
  const [metrics, setMetrics] = useState(null);
  const [progress, setProgress] = useState(null);
  const [breakdown, setBreakdown] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [metricsData, progressData, breakdownData] = await Promise.all([
          client.get(`/analytics/${userId}/metrics`),
          client.get(`/analytics/${userId}/progress`),
          client.get(`/analytics/${userId}/module-breakdown`)
        ]);
        setMetrics(metricsData);
        setProgress(progressData);
        setBreakdown(breakdownData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [userId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="error-state container">{error}</div>;

  return (
    <div className="analytics">
      <div className="container">
        <header className="page-header">
          <div>
            <h1>Your Analytics</h1>
            <p className="subtitle">Track your progress and identify areas for improvement</p>
          </div>
        </header>

        {/* Key Metrics */}
        <section className="metrics-section">
          <h2>Key Performance Indicators</h2>
          <div className="metrics-grid">
            <div className="metric-card glass-card">
              <div className="metric-icon" style={{ color: '#10b981' }}>
                <TrendingUp size={28} />
              </div>
              <div className="metric-info">
                <span className="metric-value">
                  {metrics?.lvs?.toFixed(2) || '—'}
                </span>
                <span className="metric-label">Learning Velocity Score</span>
                <span className="metric-desc">How fast you're progressing</span>
              </div>
            </div>

            <div className="metric-card glass-card">
              <div className="metric-icon" style={{ color: '#8b5cf6' }}>
                <Target size={28} />
              </div>
              <div className="metric-info">
                <span className="metric-value">
                  {metrics?.macr ? `${(metrics.macr * 100).toFixed(0)}%` : '—'}
                </span>
                <span className="metric-label">Task Completion Rate</span>
                <span className="metric-desc">Daily task completion</span>
              </div>
            </div>

            <div className="metric-card glass-card">
              <div className="metric-icon" style={{ color: '#f59e0b' }}>
                <Award size={28} />
              </div>
              <div className="metric-info">
                <span className="metric-value">
                  {progress?.predicted_band?.toFixed(1) || '—'}
                </span>
                <span className="metric-label">Predicted Band</span>
                <span className="metric-desc">Based on your performance</span>
              </div>
            </div>

            <div className="metric-card glass-card">
              <div className="metric-icon" style={{ color: '#3b82f6' }}>
                <Calendar size={28} />
              </div>
              <div className="metric-info">
                <span className="metric-value">
                  {progress?.days_active || '—'}
                </span>
                <span className="metric-label">Days Active</span>
                <span className="metric-desc">Your consistency</span>
              </div>
            </div>
          </div>
        </section>

        {/* Module Breakdown */}
        <section className="breakdown-section glass-card">
          <h2>Module Performance</h2>
          <div className="modules-grid">
            {breakdown?.modules ? (
              Object.entries(breakdown.modules).map(([module, data]) => {
                const Icon = MODULE_ICONS[module] || BookOpen;
                const color = MODULE_COLORS[module] || '#6b7280';
                const accuracy = data.accuracy || 0;
                
                return (
                  <div key={module} className="module-card">
                    <div className="module-header">
                      <div className="module-icon" style={{ color }}>
                        <Icon size={24} />
                      </div>
                      <span className="module-name">{module.charAt(0).toUpperCase() + module.slice(1)}</span>
                    </div>
                    <div className="module-stats">
                      <div className="module-accuracy">
                        <div className="accuracy-bar-bg">
                          <div 
                            className="accuracy-bar"
                            style={{ 
                              width: `${accuracy}%`,
                              backgroundColor: color
                            }}
                          />
                        </div>
                        <span className="accuracy-value">{accuracy}%</span>
                      </div>
                      <div className="module-meta">
                        <span>{data.tasks_completed || 0} tasks</span>
                        <span>{data.time_spent || 0} min</span>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="empty-state full-width">
                <p>Complete more tasks to see your module breakdown</p>
              </div>
            )}
          </div>
        </section>

        {/* Progress Over Time */}
        <section className="progress-section glass-card">
          <h2>Progress Timeline</h2>
          {progress?.timeline && progress.timeline.length > 0 ? (
            <div className="timeline-chart">
              {/* Simple bar chart visualization */}
              <div className="chart-container">
                {progress.timeline.map((point, i) => (
                  <div key={i} className="chart-bar-container">
                    <div 
                      className="chart-bar"
                      style={{ 
                        height: `${Math.max(10, (point.tasks_completed / 5) * 100)}%`
                      }}
                    />
                    <span className="chart-label">{point.date?.slice(5) || `Day ${i + 1}`}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <TrendingUp size={48} />
              <p>Keep practicing to see your progress over time!</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
