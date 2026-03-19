// frontend/src/AIAnalytics.jsx
import React, { useState, useEffect } from 'react';
import { fetchWeeklyAnalytics } from './api';

const AIAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [targetDate, setTargetDate] = useState(() => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  });

  const loadAnalytics = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchWeeklyAnalytics(targetDate, false);
      setAnalytics(data);
    } catch (err) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const generateSummary = async () => {
    setGenerating(true);
    setError('');
    try {
      const data = await fetchWeeklyAnalytics(targetDate, true);
      setAnalytics(data);
    } catch (err) {
      setError(err.message || 'Failed to generate summary');
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [targetDate]);

  const jumpToCurrentWeek = () => {
    const today = new Date();
    setTargetDate(today.toISOString().split('T')[0]);
  };

  const shiftWeek = (direction) => {
    const current = new Date(targetDate);
    current.setDate(current.getDate() + (direction * 7));
    setTargetDate(current.toISOString().split('T')[0]);
  };

  const isCurrentWeek = () => {
    const today = new Date();
    const d = new Date(targetDate);

    const todayDay = today.getDay();
    const todayStart = new Date(today);
    todayStart.setDate(today.getDate() - todayDay + (todayDay === 0 ? -6 : 1));
    todayStart.setHours(0, 0, 0, 0);

    const targetDay = d.getDay();
    const targetStart = new Date(d);
    targetStart.setDate(d.getDate() - targetDay + (targetDay === 0 ? -6 : 1));
    targetStart.setHours(0, 0, 0, 0);

    return targetStart.getTime() >= todayStart.getTime();
  };

  const formatWeekRange = (dateString) => {
    const d = new Date(dateString);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    const startOfWeek = new Date(d.setDate(diff));
    const endOfWeek = new Date(new Date(startOfWeek).setDate(startOfWeek.getDate() + 6));

    const startStr = startOfWeek.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    const endStr = endOfWeek.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });

    return `${startStr} — ${endStr}`;
  };

  return (
    <div style={{ padding: "32px 24px", width: "100%", maxWidth: "1000px", margin: "0 auto", animation: "fadeIn 0.3s ease" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" }}>
        <h1 style={{ fontSize: "32px", fontWeight: 700, margin: 0, color: "var(--text-main)" }}>AI Analytics</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button
            onClick={jumpToCurrentWeek}
            style={{
              padding: "8px 16px",
              borderRadius: "8px",
              border: "1px solid rgba(59, 130, 246, 0.3)",
              background: "linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.2) 100%)",
              color: "#60a5fa",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "14px",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              boxShadow: "0 2px 8px rgba(59, 130, 246, 0.15)",
              transition: "all 0.2s ease"
            }}
            className="hover-bg-panel-light"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            Current Week
          </button>
          <div style={{
            display: "flex", alignItems: "center", gap: "16px",
            background: "linear-gradient(180deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%)",
            padding: "6px 8px",
            borderRadius: "40px",
            border: "1px solid rgba(148, 163, 184, 0.15)",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)"
          }}>
            <button
              onClick={() => shiftWeek(-1)}
              style={{
                background: "var(--bg-panel)", border: "1px solid rgba(255,255,255,0.05)", color: "var(--text-muted)", cursor: "pointer",
                padding: "8px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.2s",
                boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-main)"; e.currentTarget.style.background = "rgba(255,255,255,0.1)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)"; e.currentTarget.style.background = "var(--bg-panel)"; }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
            </button>
            <span style={{
              fontSize: "14px", fontWeight: 600, color: "var(--text-main)", minWidth: "160px", textAlign: "center", letterSpacing: "0.02em"
            }}>
              {formatWeekRange(targetDate)}
            </span>
            <button
              onClick={() => !isCurrentWeek() && shiftWeek(1)}
              style={{
                background: "var(--bg-panel)", border: "1px solid rgba(255,255,255,0.05)",
                color: isCurrentWeek() ? "rgba(148, 163, 184, 0.2)" : "var(--text-muted)",
                cursor: isCurrentWeek() ? "not-allowed" : "pointer",
                padding: "8px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.2s",
                boxShadow: isCurrentWeek() ? "none" : "0 2px 4px rgba(0,0,0,0.1)",
                opacity: isCurrentWeek() ? 0.5 : 1
              }}
              onMouseEnter={(e) => { if (!isCurrentWeek()) { e.currentTarget.style.color = "var(--text-main)"; e.currentTarget.style.background = "rgba(255,255,255,0.1)"; } }}
              onMouseLeave={(e) => { if (!isCurrentWeek()) { e.currentTarget.style.color = "var(--text-muted)"; e.currentTarget.style.background = "var(--bg-panel)"; } }}
              disabled={isCurrentWeek()}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </button>
          </div>
        </div>
      </div>

      {loading && (
        <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)", background: "var(--bg-panel)", borderRadius: "12px", border: "1px solid var(--border-main)" }}>
          <div style={{ width: "24px", height: "24px", border: "3px solid rgba(59, 130, 246, 0.3)", borderTopColor: "#3b82f6", borderRadius: "50%", animation: "spin 1s linear infinite", margin: "0 auto 16px" }}></div>
          Loading weekly metrics and AI summary...
        </div>
      )}

      {error && !loading && (
        <div style={{ padding: "16px 20px", background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "12px", color: "#ef4444", marginBottom: "24px" }}>
          {error}
        </div>
      )}

      {!loading && analytics && (
        <div style={{ display: 'flex', flexDirection: 'row', gap: '24px', alignItems: 'stretch' }}>

          {/* Left Column: Weekly Activity & Lists */}
          <div style={{ flex: '0 0 320px', display: 'flex' }}>
            <div className="glass-panel" style={{
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
              flex: 1,
              maxHeight: '100%',
              overflowY: 'auto'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>Weekly Activity</h3>
              </div>
              <div style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text-main)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                  <span style={{ color: '#3b82f6', fontSize: '28px' }}>{analytics.consultation_count}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>consultations across</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                  <span style={{ color: '#10b981', fontSize: '28px' }}>{analytics.patient_count}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>patients seen</span>
                </div>
              </div>

              {/* Patient List */}
              <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-main)' }}>
                <div style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '8px', letterSpacing: '0.05em' }}>Patients</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {analytics.patient_names?.length > 0 ? analytics.patient_names.map((name, i) => (
                    <div key={i} style={{ fontSize: '13px', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: '#10b981' }} />
                      {name}
                    </div>
                  )) : <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No patients seen</div>}
                </div>
              </div>

              {/* Consultation List */}
              <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-main)' }}>
                <div style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '8px', letterSpacing: '0.05em' }}>Consultations</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {analytics.consultation_details?.length > 0 ? analytics.consultation_details.map((c, i) => (
                    <div key={i} style={{ fontSize: '13px', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: '#3b82f6' }} />
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.title}</span>
                    </div>
                  )) : <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No consultations</div>}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: AI Summary Section */}
          <div style={{ flex: 1, display: 'flex' }}>
            <div className="glass-panel" style={{ padding: '32px', minHeight: '400px', display: 'flex', flexDirection: 'column', flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', borderBottom: '1px solid var(--border-main)', paddingBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    background: 'var(--primary-gradient)',
                    padding: '8px',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
                  }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                  </div>
                  <div>
                    <h2 style={{ fontSize: '20px', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>Weekly AI Summary</h2>
                  </div>
                </div>

                <button
                  onClick={generateSummary}
                  disabled={generating || analytics.consultation_count === 0}
                  style={{
                    background: 'transparent',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    color: '#3b82f6',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: (generating || analytics.consultation_count === 0) ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'all 0.2s',
                    opacity: (generating || analytics.consultation_count === 0) ? 0.5 : 1
                  }}
                  className={!(generating || analytics.consultation_count === 0) ? "hover-bg-primary-light" : ""}
                >
                  {generating ? (
                    <div style={{ width: "14px", height: "14px", border: "2px solid rgba(59,130,246,0.3)", borderTopColor: "#3b82f6", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
                  )}
                  {analytics.summary ? 'Regenerate Summary' : 'Generate Summary'}
                </button>
              </div>

              <div style={{
                lineHeight: '1.7',
                fontSize: '15px',
                color: analytics.summary ? 'var(--text-main)' : 'var(--text-muted)',
                whiteSpace: 'pre-wrap',
                background: 'rgba(15, 23, 42, 0.4)',
                padding: '24px',
                borderRadius: '12px',
                border: '1px solid rgba(148, 163, 184, 0.1)',
                boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)',
                flex: 1
              }}>
                {generating ? "Generating comprehensive weekly summary, this may take a moment..." : (analytics.summary || "Click 'Generate Summary' to analyze the selected week's consultations.")}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAnalytics;
