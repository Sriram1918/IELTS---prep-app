import { useEffect, useState } from 'react';
import { client } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import { Trophy, Medal, Calendar, Users, ChevronRight, Award } from 'lucide-react';

export default function LAIMS() {
  const [competitions, setCompetitions] = useState([]);
  const [selectedCompetition, setSelectedCompetition] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [leaderboardLoading, setLeaderboardLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCompetitions = async () => {
      try {
        const response = await client.get('/laims/competitions');
        const data = response.competitions || response || [];
        setCompetitions(data);
        // Auto-select active competition
        const active = data.find(c => c.status === 'active');
        if (active) {
          setSelectedCompetition(active);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCompetitions();
  }, []);

  useEffect(() => {
    if (selectedCompetition) {
      const fetchLeaderboard = async () => {
        setLeaderboardLoading(true);
        try {
          const data = await client.get(`/laims/competitions/${selectedCompetition.id}/leaderboard?limit=20`);
          setLeaderboard(data.leaderboard || data.entries || data || []);
        } catch (err) {
          console.error('Failed to fetch leaderboard:', err);
        } finally {
          setLeaderboardLoading(false);
        }
      };

      fetchLeaderboard();
    }
  }, [selectedCompetition]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="error-state container">{error}</div>;

  const getStatusBadge = (status) => {
    const styles = {
      active: { bg: 'var(--color-success)', label: 'Live Now' },
      upcoming: { bg: 'var(--color-primary)', label: 'Upcoming' },
      completed: { bg: 'var(--color-text-muted)', label: 'Completed' }
    };
    return styles[status] || styles.upcoming;
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return <Trophy size={20} className="gold" />;
    if (rank === 2) return <Medal size={20} className="silver" />;
    if (rank === 3) return <Medal size={20} className="bronze" />;
    return <span className="rank-number">{rank}</span>;
  };

  return (
    <div className="laims">
      <div className="container">
        <header className="page-header">
          <div>
            <h1>L-AIMS Mock Tests</h1>
            <p className="subtitle">Low-stakes IELTS simulations with real-time leaderboards</p>
          </div>
        </header>

        <div className="laims-content">
          {/* Competitions List */}
          <section className="competitions-section glass-card">
            <h2>Competitions</h2>
            <div className="competitions-list">
              {competitions.length > 0 ? (
                competitions.map(comp => {
                  const badge = getStatusBadge(comp.status);
                  return (
                    <div 
                      key={comp.id} 
                      className={`competition-card ${selectedCompetition?.id === comp.id ? 'selected' : ''}`}
                      onClick={() => setSelectedCompetition(comp)}
                    >
                      <div className="competition-info">
                        <div 
                          className="status-badge"
                          style={{ backgroundColor: badge.bg }}
                        >
                          {badge.label}
                        </div>
                        <h3>{comp.name}</h3>
                        <div className="competition-dates">
                          <Calendar size={14} />
                          <span>
                            {new Date(comp.start_date).toLocaleDateString()} - {new Date(comp.end_date).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <ChevronRight size={20} />
                    </div>
                  );
                })
              ) : (
                <div className="empty-state">
                  <p>No competitions available</p>
                </div>
              )}
            </div>
          </section>

          {/* Leaderboard */}
          <section className="leaderboard-section glass-card">
            <div className="section-header">
              <Trophy size={24} />
              <h2>
                {selectedCompetition?.name || 'Select a Competition'}
              </h2>
            </div>

            {leaderboardLoading ? (
              <LoadingSpinner />
            ) : leaderboard.length > 0 ? (
              <div className="leaderboard">
                {/* Top 3 Podium */}
                <div className="podium">
                  {leaderboard.slice(0, 3).map((entry, i) => (
                    <div key={entry.id || i} className={`podium-position pos-${i + 1}`}>
                      <div className="podium-avatar">
                        {getRankIcon(i + 1)}
                      </div>
                      <span className="podium-name">{entry.user_name || `User ${i + 1}`}</span>
                      <span className="podium-score">Band {entry.score?.toFixed(1) || '—'}</span>
                    </div>
                  ))}
                </div>

                {/* Rest of Leaderboard */}
                {leaderboard.length > 3 && (
                  <div className="leaderboard-list">
                    {leaderboard.slice(3).map((entry, i) => (
                      <div key={entry.id || i} className="leaderboard-row">
                        <span className="row-rank">{i + 4}</span>
                        <span className="row-name">{entry.user_name || `User ${i + 4}`}</span>
                        <span className="row-score">Band {entry.score?.toFixed(1) || '—'}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <Award size={48} />
                <p>No entries yet. Be the first to submit!</p>
                {selectedCompetition?.status === 'active' && (
                  <button className="btn btn-primary">Take Mock Test</button>
                )}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
