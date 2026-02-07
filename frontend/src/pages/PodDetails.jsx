import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  Trophy, Users, ArrowLeft, Medal, Flame, Target, Crown
} from 'lucide-react';

export default function PodDetails() {
  const { podId } = useParams();
  const navigate = useNavigate();
  const [pod, setPod] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get user ID from localStorage
  const storedUser = localStorage.getItem('momentum_user');
  const userId = storedUser ? JSON.parse(storedUser).id : null;

  useEffect(() => {
    const fetchPod = async () => {
      if (!userId) {
        setError('User not found');
        setLoading(false);
        return;
      }

      try {
        const data = await client.get(`/pods/user/${userId}`);
        if (data.has_pod) {
          setPod(data);
        } else {
          setError('You are not in a pod yet');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPod();
  }, [userId]);

  if (loading) return <LoadingSpinner />;
  
  if (error) {
    return (
      <div className="pod-details">
        <div className="container">
          <Link to={`/dashboard/${userId}`} className="back-link">
            <ArrowLeft size={20} />
            Back to Dashboard
          </Link>
          <div className="error-state glass-card">
            <Users size={48} />
            <h2>{error}</h2>
            <p>Join a pod from your dashboard to compete with peers!</p>
            <button 
              className="btn btn-primary"
              onClick={() => navigate(`/dashboard/${userId}`)}
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  const getRankIcon = (rank) => {
    if (rank === 1) return <Crown size={20} className="rank-gold" />;
    if (rank === 2) return <Medal size={20} className="rank-silver" />;
    if (rank === 3) return <Medal size={20} className="rank-bronze" />;
    return <span className="rank-number">#{rank}</span>;
  };

  return (
    <div className="pod-details">
      <div className="container">
        <Link to={`/dashboard/${userId}`} className="back-link">
          <ArrowLeft size={20} />
          Back to Dashboard
        </Link>

        {/* Pod Header */}
        <div className="pod-header glass-card">
          <div className="pod-icon">
            <Trophy size={32} />
          </div>
          <div className="pod-info">
            <h1>{pod.pod_name}</h1>
            <p className="pod-meta">
              <Users size={16} />
              {pod.member_count} / {pod.max_members} members
              <span className="separator">•</span>
              <Target size={16} />
              {pod.track?.replace(/_/g, ' ')} track
            </p>
          </div>
          <div className="your-rank">
            <span className="rank-label">Your Rank</span>
            <span className="rank-value">#{pod.user_rank}</span>
          </div>
        </div>

        {/* Leaderboard */}
        <section className="leaderboard-section glass-card">
          <div className="section-header">
            <Trophy size={24} />
            <h2>Pod Leaderboard</h2>
          </div>

          <div className="leaderboard-list">
            {pod.members.map((member, idx) => (
              <div 
                key={member.user_id}
                className={`leaderboard-row ${member.is_current_user ? 'current-user' : ''} ${idx < 3 ? `top-${idx + 1}` : ''}`}
              >
                <div className="rank-cell">
                  {getRankIcon(idx + 1)}
                </div>
                <div className="user-cell">
                  <span className="user-name">{member.name}</span>
                  {member.is_current_user && <span className="you-tag">You</span>}
                </div>
                <div className="stats-cell">
                  <div className="stat">
                    <Target size={14} />
                    <span>{member.tasks_completed} tasks</span>
                  </div>
                  <div className="stat">
                    <Flame size={14} />
                    <span>{member.streak_days}d streak</span>
                  </div>
                </div>
                <div className="points-cell">
                  <span className="points-value">{member.points}</span>
                  <span className="points-label">pts</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* How Points Work */}
        <section className="points-info glass-card">
          <h3>How to Earn Points</h3>
          <div className="points-grid">
            <div className="point-item">
              <span className="point-value">+10</span>
              <span className="point-desc">Complete a task</span>
            </div>
            <div className="point-item">
              <span className="point-value">+5</span>
              <span className="point-desc">Maintain streak</span>
            </div>
            <div className="point-item">
              <span className="point-value">+15</span>
              <span className="point-desc">Score 80%+</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
