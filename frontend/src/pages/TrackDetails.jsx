import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { client } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  Clock, Calendar, Target, Users, TrendingUp, 
  CheckCircle2, BookOpen, Award, ChevronLeft, Flame
} from 'lucide-react';

export default function TrackDetails() {
  const { trackName } = useParams();
  const [track, setTrack] = useState(null);
  const [peers, setPeers] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTrackDetails = async () => {
      try {
        const data = await client.get(`/tracks/${trackName}`);
        setTrack(data);
        // Get peer count on this track
        const peersData = await client.get(`/tracks/${trackName}/users/count`);
        setPeers(peersData.count || 0);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTrackDetails();
  }, [trackName]);

  if (loading) return <LoadingSpinner fullScreen />;
  if (error) return <div className="error-state container">{error}</div>;
  if (!track) return <div className="error-state container">Track not found</div>;

  // Generate curriculum weeks based on track duration
  const generateCurriculum = () => {
    const weeks = [];
    const modules = ['Reading', 'Writing', 'Speaking', 'Listening'];
    for (let i = 1; i <= track.duration_weeks; i++) {
      const weekFocus = modules[(i - 1) % 4];
      weeks.push({
        week: i,
        focus: weekFocus,
        tasks: Math.floor(track.daily_minutes / 10) * 5,
        milestone: i === track.duration_weeks ? 'Final Assessment' : 
                   i === Math.floor(track.duration_weeks / 2) ? 'Mid-Track Review' : null
      });
    }
    return weeks;
  };

  const curriculum = generateCurriculum();
  const successPercent = Math.round((track.success_rate || 0.85) * 100);

  return (
    <div className="track-details">
      <div className="container">
        {/* Back Link */}
        <Link to="/dashboard" className="back-link">
          <ChevronLeft size={20} />
          Back to Dashboard
        </Link>

        {/* Track Header */}
        <header className="track-header glass-card">
          <div className="track-badge">
            <Flame size={32} />
          </div>
          <div className="track-title">
            <h1>{track.name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h1>
            <p className="track-description">{track.description}</p>
          </div>
          <div className="track-success-badge">
            <Award size={24} />
            <span>{successPercent}% Success Rate</span>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="stats-grid">
          <div className="stat-card glass-card">
            <Calendar size={28} />
            <div className="stat-content">
              <span className="stat-value">{track.duration_weeks}</span>
              <span className="stat-label">Weeks</span>
            </div>
          </div>
          <div className="stat-card glass-card">
            <Clock size={28} />
            <div className="stat-content">
              <span className="stat-value">{track.daily_minutes}</span>
              <span className="stat-label">Daily Minutes</span>
            </div>
          </div>
          <div className="stat-card glass-card">
            <TrendingUp size={28} />
            <div className="stat-content">
              <span className="stat-value">+{track.avg_band_improvement || 1.0}</span>
              <span className="stat-label">Avg. Band Improvement</span>
            </div>
          </div>
          <div className="stat-card glass-card">
            <Users size={28} />
            <div className="stat-content">
              <span className="stat-value">{peers}</span>
              <span className="stat-label">Active Learners</span>
            </div>
          </div>
        </div>

        {/* Success Metrics */}
        <section className="success-section glass-card">
          <h2><Target size={24} /> Historical Performance</h2>
          <div className="success-stats">
            <div className="success-stat">
              <div className="success-circle" style={{ '--progress': successPercent }}>
                <span>{successPercent}%</span>
              </div>
              <p>Achieved Target Band</p>
            </div>
            <div className="success-stat">
              <div className="success-number">
                <span>{track.total_completions || 0}</span>
              </div>
              <p>Total Completions</p>
            </div>
            <div className="success-stat">
              <div className="success-number highlight">
                <span>+{track.avg_band_improvement || 1.0}</span>
              </div>
              <p>Average Improvement</p>
            </div>
          </div>
        </section>

        {/* Curriculum Timeline */}
        <section className="curriculum-section glass-card">
          <h2><BookOpen size={24} /> Weekly Curriculum</h2>
          <div className="curriculum-timeline">
            {curriculum.map((week, i) => (
              <div key={i} className={`curriculum-week ${week.milestone ? 'milestone' : ''}`}>
                <div className="week-marker">
                  {week.milestone ? <CheckCircle2 size={20} /> : <span>{week.week}</span>}
                </div>
                <div className="week-content">
                  <h4>Week {week.week}: {week.focus} Focus</h4>
                  <p>{week.tasks} practice tasks</p>
                  {week.milestone && (
                    <span className="milestone-badge">{week.milestone}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <div className="track-cta">
          <Link to="/onboarding" className="btn btn-primary btn-lg">
            Start This Track
            <ChevronLeft size={20} style={{ transform: 'rotate(180deg)' }} />
          </Link>
        </div>
      </div>
    </div>
  );
}
