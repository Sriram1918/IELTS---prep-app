import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { client } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import WeeklyReport from '../components/WeeklyReport';
import { 
  Flame, Target, Clock, CheckCircle2, Circle, 
  TrendingUp, Users, Award, Calendar, ChevronRight, Trophy
} from 'lucide-react';

export default function Dashboard() {
  const { userId } = useParams();
  const { user, updateUser } = useUser();
  const [dashboard, setDashboard] = useState(null);
  const [tracks, setTracks] = useState([]);
  const [pod, setPod] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showReport, setShowReport] = useState(false);

  useEffect(() => {
    // Skip if no valid user ID
    if (!userId || userId === 'undefined' || !user) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        // Fetch dashboard, tracks, and pod in parallel
        const [dashboardData, tracksData, podData] = await Promise.all([
          client.get(`/dashboard/${userId}`),
          client.get('/tracks'),
          client.get(`/pods/user/${userId}`)
        ]);
        setDashboard(dashboardData);
        setTracks(tracksData.tracks || tracksData || []);
        setPod(podData.has_pod ? podData : null);
        
        // Update user context with latest streak
        updateUser({ current_streak: dashboardData.streak?.current_streak || 0 });

        // Check if we should show the weekly report (Day 7 Aha Moment)
        // In production, this would be based on day_in_journey % 7 === 0
        // For now, let's just check if it's available via API or trigger it
        try {
           // We can optimistically try to fetch it to see if it's "Day 7"
           // Or just rely on the user clicking a "View Report" button for demo
        } catch (e) {
           // ignore
        }

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [userId, user, updateUser]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="error-state container">{error}</div>;
  if (!dashboard) return null;

  const { streak, progress, todays_tasks, ghost_comparison } = dashboard;

  return (
    <div className="dashboard">
      <div className="container">
        {/* Welcome Header */}
        <header className="dashboard-header">
          <div>
            <h1>Welcome back, {dashboard.user_name}!</h1>
            <p className="subtitle">
              Day {progress?.day_in_journey || 1} of your{' '}
              <Link to={`/tracks/${dashboard.current_track}`} className="track-link">
                {dashboard.current_track?.replace(/_/g, ' ')} track
                <ChevronRight size={16} />
              </Link>
            </p>
          </div>
          <div className="header-stats">
            <div className="stat-badge exam-countdown">
              <Calendar size={18} />
              <span>{progress?.days_until_exam || 0} days to exam</span>
            </div>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="stats-grid">
          {/* Streak Card */}
          <div className={`stat-card glass-card streak-card ${streak?.streak_status}`}>
            <div className="stat-icon">
              <Flame size={32} fill={streak?.current_streak > 0 ? 'currentColor' : 'none'} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{streak?.current_streak || 0}</span>
              <span className="stat-label">Day Streak</span>
              {streak?.streak_status === 'at_risk' && (
                <span className="streak-warning">Complete a task to save your streak!</span>
              )}
            </div>
          </div>

          {/* Tasks Completed */}
          <div className="stat-card glass-card">
            <div className="stat-icon">
              <CheckCircle2 size={32} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{progress?.tasks_completed || 0}</span>
              <span className="stat-label">Tasks Completed</span>
            </div>
          </div>

          {/* Practice Time */}
          <div className="stat-card glass-card">
            <div className="stat-icon">
              <Clock size={32} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{Math.round((progress?.total_practice_minutes || 0) / 60)}h</span>
              <span className="stat-label">Practice Time</span>
            </div>
          </div>

          {/* Predicted Band */}
          <div className="stat-card glass-card highlight">
            <div className="stat-icon">
              <Target size={32} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{progress?.predicted_band?.toFixed(1) || '—'}</span>
              <span className="stat-label">Predicted Band</span>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="dashboard-content">
          {/* Today's Tasks */}
          <section className="tasks-section glass-card">
            <div className="section-header">
              <h2>Today's Tasks</h2>
              <span className="task-count">
                {todays_tasks?.filter(t => t.completed).length || 0} / {todays_tasks?.length || 0}
              </span>
            </div>
            <div className="tasks-list">
              {todays_tasks && todays_tasks.length > 0 ? (
                todays_tasks.map((task, i) => (
                  <div key={task.id || i} className={`task-item ${task.completed ? 'completed' : ''}`}>
                    <div className="task-status">
                      {task.completed ? (
                        <CheckCircle2 size={24} className="text-success" />
                      ) : (
                        <Circle size={24} />
                      )}
                    </div>
                    <div className="task-info">
                      <span className="task-title">{task.title}</span>
                      <div className="task-meta">
                        <span className={`task-type ${task.type}`}>{task.type}</span>
                        <span className={`task-difficulty ${task.difficulty}`}>{task.difficulty}</span>
                        <span className="task-time">{task.estimated_minutes} min</span>
                      </div>
                    </div>
                    {!task.completed && (
                      <button className="btn btn-primary btn-sm">Start</button>
                    )}
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <p>No tasks for today. Check back tomorrow!</p>
                </div>
              )}
            </div>
          </section>

          {/* Ghost Comparison */}
          <aside className="sidebar">
            <div className="ghost-section glass-card">
              <div className="section-header">
                <Users size={20} />
                <h3>Peer Comparison</h3>
              </div>
              {ghost_comparison ? (
                <div className="ghost-stats">
                  <div className="ghost-stat">
                    <span className="ghost-label">Cohort Avg Tasks</span>
                    <span className="ghost-value">{ghost_comparison.avg_tasks_completed || '—'}</span>
                  </div>
                  <div className="ghost-stat">
                    <span className="ghost-label">Your Rank</span>
                    <span className="ghost-value">#{ghost_comparison.rank || '—'}</span>
                  </div>
                </div>
              ) : (
                <p className="ghost-placeholder">
                  Complete a few more tasks to see how you compare with peers at your level!
                </p>
              )}
            </div>

            {/* Progress Bar */}
            <div className="progress-section glass-card">
              <div className="section-header">
                <TrendingUp size={20} />
                <h3>Journey Progress</h3>
              </div>
              <div className="progress-bar-container">
                <div 
                  className="progress-bar" 
                  style={{ width: `${Math.min(100, progress?.completion_percentage || 0)}%` }}
                />
              </div>
              <span className="progress-label">
                {Math.round(progress?.completion_percentage || 0)}% complete
              </span>
            </div>

            {/* Weekly Report Card */}
            <div 
              className="weekly-report-card glass-card"
              onClick={() => setShowReport(true)}
            >
              <div className="section-header">
                <Award size={20} />
                <h3>Weekly Report</h3>
              </div>
              <p className="report-preview">
                See your progress, cohort comparison, and personalized insights.
              </p>
              <button className="btn btn-primary btn-sm btn-full">
                View Report
              </button>
            </div>

            {/* Your Pod Section */}
            <div className="pod-section glass-card">
              <div className="section-header">
                <Trophy size={20} />
                <h3>Your Pod</h3>
              </div>
              {pod ? (
                <Link to="/pod" className="pod-content pod-link">
                  <p className="pod-name">{pod.pod_name}</p>
                  <p className="pod-rank">
                    You're <strong>#{pod.user_rank}</strong> of {pod.member_count}
                  </p>
                  <div className="pod-leaderboard">
                    {pod.members.slice(0, 3).map((member, idx) => (
                      <div 
                        key={member.user_id} 
                        className={`pod-member ${member.is_current_user ? 'current' : ''}`}
                      >
                        <span className="member-rank">#{idx + 1}</span>
                        <span className="member-name">
                          {member.name}
                          {member.is_current_user && <span className="you-badge">You</span>}
                        </span>
                        <span className="member-points">{member.points} pts</span>
                      </div>
                    ))}
                  </div>
                  <p className="view-full">View full leaderboard →</p>
                </Link>
              ) : (
                <div className="pod-empty">
                  <p>Join a Challenge Pod to compete with peers on your track!</p>
                  <button 
                    className="btn btn-primary btn-sm"
                    onClick={async () => {
                      try {
                        const result = await client.post('/pods/join', {
                          user_id: userId,
                          track_name: dashboard.current_track
                        });
                        if (result.joined || result.already_member) {
                          const podData = await client.get(`/pods/user/${userId}`);
                          setPod(podData.has_pod ? podData : null);
                        }
                      } catch (err) {
                        console.error('Failed to join pod:', err);
                      }
                    }}
                  >
                    Join Pod
                  </button>
                </div>
              )}
            </div>
          </aside>
        </div>

        {/* Browse All Tracks Section */}
        <section className="tracks-browser glass-card">
          <div className="section-header">
            <Target size={24} />
            <h2>Browse All Tracks</h2>
            <span className="track-count">{tracks.length} tracks available</span>
          </div>
          <p className="section-description">
            Choose the perfect learning path based on your timeline, availability, and goals.
          </p>
          <div className="tracks-grid">
            {tracks.map(track => (
              <Link 
                key={track.name} 
                to={`/tracks/${track.name}`} 
                className={`track-card ${track.name === dashboard.current_track ? 'current' : ''}`}
              >
                <div className="track-card-header">
                  <h4>{track.name.replace(/_/g, ' ')}</h4>
                  {track.name === dashboard.current_track && (
                    <span className="current-badge">Your Track</span>
                  )}
                </div>
                <p className="track-card-description">{track.description}</p>
                <div className="track-card-stats">
                  <div className="track-stat">
                    <Calendar size={14} />
                    <span>{track.duration_weeks}w</span>
                  </div>
                  <div className="track-stat">
                    <Clock size={14} />
                    <span>{track.daily_minutes} min/day</span>
                  </div>
                  <div className="track-stat success">
                    <Award size={14} />
                    <span>{Math.round((track.success_rate || 0.85) * 100)}%</span>
                  </div>
                </div>
                <ChevronRight size={20} className="track-arrow" />
              </Link>
            ))}
          </div>
        </section>
        {/* Weekly Report Modal */}
        {showReport && (
          <WeeklyReport 
            userId={userId} 
            onClose={() => setShowReport(false)} 
          />
        )}
      </div>
    </div>
  );
}
