// frontend/src/App.jsx
import { useEffect, useState, useRef } from "react";
import Login from "./Login";
import { fetchConsultations, createConsultation, deleteConsultation, logout, fetchCurrentUser, fetchPatients, createPatient, updatePatient, deletePatient, sendChatMessage, fetchChatSessions, createChatSession, fetchChatSession, deleteChatSession, changePassword, deleteAccount, joinMeetingWithBot, disconnectBot, updateConsultationStatus } from "./api";
import Sidebar from "./Sidebar";
import MicPermission from "./MicPermission";

function Consultations({ onLogout, focusedConsultationId, setFocusedConsultationId }) {
  const [view, setView] = useState("list"); // "list", "create", "detail"
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedConsultation, setSelectedConsultation] = useState(null);

  useEffect(() => {
    if (focusedConsultationId && consultations.length > 0) {
      const target = consultations.find(c => c.id === focusedConsultationId);
      if (target) {
        setSelectedConsultation(target);
        setView("detail");
        if (setFocusedConsultationId) setFocusedConsultationId(null);
      }
    }
  }, [focusedConsultationId, consultations, setFocusedConsultationId]);

  // For Creation
  const [createStep, setCreateStep] = useState(1);
  const [title, setTitle] = useState("");
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  // Recall Bot State
  const [meetingUrl, setMeetingUrl] = useState('');
  const [isJoining, setIsJoining] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [botError, setBotError] = useState('');

  const activeConsultationObj = consultations.find(c => c.status === 'draft');

  const loadData = () => {
    fetchConsultations()
      .then(setConsultations)
      .catch((err) => {
        if (err.message === "unauthorized") onLogout();
        else setError(err.message);
      })
      .finally(() => setLoading(false));
  };

  const loadPatients = () => {
    fetchPatients().then(setPatients).catch(console.error);
  };

  useEffect(() => {
    loadData();
    const intervalId = setInterval(loadData, 5000);
    const handleStatusChanged = () => loadData();
    window.addEventListener('consultationStatusChanged', handleStatusChanged);
    return () => {
      clearInterval(intervalId);
      window.removeEventListener('consultationStatusChanged', handleStatusChanged);
    };
  }, [onLogout]);

  const handleCreateView = () => {
    if (activeConsultationObj) {
      setError("Please finish your current active consultation before starting a new one.");
      return;
    }
    loadPatients();
    setCreateStep(1);
    setTitle("");
    setSelectedPatientId("");
    setView("create");
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    if (activeConsultationObj) {
      setError("An active consultation already exists.");
      return;
    }
    setError("");
    try {
      let finalPatientId = selectedPatientId;

      const created = await createConsultation(title, finalPatientId || null);
      setConsultations((prev) => [created, ...prev]);
      setView("list");
    } catch (err) {
      if (err.message === "unauthorized") onLogout();
      else setError(err.message);
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this consultation?")) return;
    try {
      await deleteConsultation(id);
      setConsultations((prev) => prev.filter((c) => c.id !== id));
      if (selectedConsultation?.id === id) setView("list");
    } catch (err) {
      if (err.message === "unauthorized") onLogout();
      else setError(err.message);
    }
  };

  const handleViewDetail = (c) => {
    setSelectedConsultation(c);
    setMeetingUrl('');
    setBotError('');
    setView("detail");
  };

  const handleJoinBot = async (consultationId) => {
    if (!meetingUrl.trim()) return;
    setIsJoining(true);
    setBotError('');
    try {
      await joinMeetingWithBot(consultationId, meetingUrl);
      setMeetingUrl('');
      // The periodic loadData will update the recall_bot_id in the consultations list
    } catch (e) {
      setBotError(e.message || "Failed to join meeting");
    } finally {
      setIsJoining(false);
    }
  };

  const handleDisconnectBot = async (consultationId) => {
    setIsDisconnecting(true);
    try {
      await disconnectBot(consultationId);
    } catch (e) {
      console.error("Failed to disconnect bot", e);
    } finally {
      setIsDisconnecting(false);
    }
  };

  const handleFinish = async (e, id) => {
    if (e) e.stopPropagation();
    if (!window.confirm("Mark this consultation as finished?")) return;
    try {
      const updated = await updateConsultationStatus(id, "completed");
      setConsultations(prev => prev.map(c => c.id === id ? { ...c, ...updated } : c));
      window.dispatchEvent(new Event('consultationStatusChanged'));
    } catch (err) {
      if (err.message === "unauthorized") onLogout();
      else setError(err.message);
    }
  };

  const formatTime = (seconds) => {
    if (!isFinite(seconds)) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  if (view === "create") {
    return (
      <div style={{ padding: "32px 24px", width: "100%", maxWidth: "800px", margin: "0 auto" }}>
        <button onClick={() => setView("list")} style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", marginBottom: "24px" }}>
          <span>←</span> Back to list
        </button>
        <h1 style={{ fontSize: "32px", fontWeight: 700, marginBottom: "24px", color: "#f8fafc" }}>Create Consultation</h1>

        <div className="glass-panel" style={{ padding: "32px" }}>
          <form onSubmit={handleCreateSubmit} style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Consultation Title *</label>
              <input
                style={{ padding: "12px", borderRadius: "8px", border: "1px solid rgba(148, 163, 184, 0.2)", backgroundColor: "rgba(15, 23, 42, 0.4)", color: "#f8fafc", outline: "none" }}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Follow-up for Hypertension"
                required
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "20px", padding: "24px", borderRadius: "12px", backgroundColor: "rgba(30, 41, 59, 0.3)", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
              <label style={{ fontSize: "16px", color: "#f8fafc", fontWeight: 600, display: "flex", alignItems: "center", gap: "8px" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                Patient Selection
              </label>

              <div style={{ display: "flex", flexWrap: "wrap", gap: "24px" }}>
                <label style={{ display: "flex", alignItems: "center", gap: "10px", color: (selectedPatientId !== "") ? "#f8fafc" : "#94a3b8", cursor: "pointer", fontSize: "15px", transition: "color 0.2s" }}>
                  <input
                    type="radio"
                    name="patient-mode"
                    checked={selectedPatientId !== ""}
                    onChange={() => {
                      setSelectedPatientId(patients.length > 0 ? patients[0].id : "none_selected");
                    }}
                    style={{ cursor: "pointer", width: "18px", height: "18px", accentColor: "#3b82f6" }}
                  />
                  Select Existing
                </label>
                <label style={{ display: "flex", alignItems: "center", gap: "10px", color: (selectedPatientId === "") ? "#f8fafc" : "#94a3b8", cursor: "pointer", fontSize: "15px", transition: "color 0.2s" }}>
                  <input
                    type="radio"
                    name="patient-mode"
                    checked={selectedPatientId === ""}
                    onChange={() => {
                      setSelectedPatientId("");
                    }}
                    style={{ cursor: "pointer", width: "18px", height: "18px", accentColor: "#3b82f6" }}
                  />
                  Skip (Anonymous)
                </label>
              </div>

              {selectedPatientId !== "" && (
                <div style={{ marginTop: "4px", animation: "fadeIn 0.2s ease" }}>
                  {patients.length > 0 ? (
                    <select
                      style={{ width: "100%", padding: "14px", borderRadius: "10px", border: "1px solid rgba(59, 130, 246, 0.4)", backgroundColor: "rgba(15, 23, 42, 0.6)", color: "#f8fafc", outline: "none", fontSize: "15px", cursor: "pointer", boxShadow: "0 0 0 2px rgba(59,130,246,0.1)" }}
                      value={selectedPatientId}
                      onChange={(e) => setSelectedPatientId(e.target.value)}
                    >
                      {patients.map(p => (
                        <option key={p.id} value={p.id}>{p.name ? `${p.name} (${p.display_id})` : p.display_id}</option>
                      ))}
                    </select>
                  ) : (
                    <div style={{ padding: "14px", borderRadius: "10px", border: "1px solid rgba(239, 68, 68, 0.3)", backgroundColor: "rgba(239, 68, 68, 0.05)", color: "#fca5a5", fontSize: "14px" }}>
                      No patients are present in the system. Please create a patient in the Patients section first.
                    </div>
                  )}
                </div>
              )}
            </div>

            {error && <div style={{ color: "#ef4444", fontSize: "14px" }}>{error}</div>}

            <button
              type="submit"
              disabled={!title.trim() || selectedPatientId === "none_selected"}
              style={{
                background: "var(--primary-gradient)",
                border: "none",
                padding: "12px 24px",
                borderRadius: "8px",
                color: "white",
                fontWeight: 600,
                fontSize: "16px",
                cursor: "pointer",
                marginTop: "16px",
                alignSelf: "flex-end",
                opacity: (!title.trim() || selectedPatientId === "none_selected") ? 0.6 : 1
              }}
            >
              Start Consultation
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (view === "detail" && selectedConsultation) {
    const c = selectedConsultation;
    // ensure c gets updated when consultations refresh
    const updatedC = consultations.find(cons => cons.id === c.id) || c;


    return (
      <div style={{ padding: "32px 24px", width: "100%", maxWidth: "1200px", margin: "0 auto", boxSizing: "border-box", animation: "fadeIn 0.3s ease" }}>
        <button onClick={() => setView("list")} style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", marginBottom: "24px" }}>
          <span>←</span> Back to all consultations
        </button>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "40px" }}>
          <div>
            <h1 style={{ fontSize: "36px", fontWeight: 700, margin: "0 0 12px 0", color: "#f8fafc" }}>
              {updatedC.title}
            </h1>
            <div style={{ display: "flex", gap: "16px", color: "#94a3b8", fontSize: "14px", alignItems: "center" }}>
              <span>{new Date(updatedC.created_at).toLocaleString()}</span>
              {updatedC.patient && (
                <>
                  <span style={{ color: "#475569" }}>|</span>
                  <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    {updatedC.patient.name ? `${updatedC.patient.name} (${updatedC.patient.display_id})` : updatedC.patient.display_id}
                  </span>
                </>
              )}
              <span style={{ color: "#475569" }}>|</span>
              <span style={{ padding: "4px 8px", backgroundColor: updatedC.status === 'completed' ? "rgba(16, 185, 129, 0.1)" : "rgba(234, 179, 8, 0.1)", color: updatedC.status === 'completed' ? "#34d399" : "#facc15", borderRadius: "4px", fontSize: "12px", textTransform: "uppercase", fontWeight: 600 }}>
                {updatedC.status === 'completed' ? 'Finished' : (updatedC.status === 'draft' ? 'Active' : updatedC.status)}
              </span>
            </div>
          </div>
          <div style={{ display: "flex", gap: "12px" }}>
            {updatedC.status === 'draft' && (
              <button
                onClick={(e) => handleFinish(e, updatedC.id)}
                style={{ background: "var(--success-gradient)", border: "none", color: "white", padding: "8px 20px", borderRadius: "8px", fontSize: "14px", fontWeight: 600, cursor: "pointer", boxShadow: "0 4px 12px rgba(16, 185, 129, 0.3)" }}
              >
                Finish Consultation
              </button>
            )}
            <button
              onClick={(e) => handleDelete(e, updatedC.id)}
              style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)", color: "#ef4444", padding: "8px 16px", borderRadius: "8px", fontSize: "14px", fontWeight: 600, cursor: "pointer" }}
              className="hover-bg-danger"
            >
              Delete
            </button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: "24px" }}>
          {/* Left Column: Summary & Patient Details */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

            {updatedC.patient && (
              <div className="glass-panel" style={{ padding: "24px" }}>
                <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em", display: "flex", alignItems: "center", gap: "8px" }}>
                  Patient Info
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", color: "#f1f5f9", fontSize: "15px" }}>
                  <div>
                    <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>Display ID</div>
                    <div>{updatedC.patient.display_id}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>Full Name</div>
                    <div>{updatedC.patient.name || "N/A"}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>DOB</div>
                    <div>{updatedC.patient.date_of_birth || "N/A"}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>Gender</div>
                    <div>{updatedC.patient.gender || "N/A"}</div>
                  </div>
                </div>
              </div>
            )}

            <div className="glass-panel" style={{ padding: "24px", flex: 1, display: "flex", flexDirection: "column" }}>
              <h3 style={{ margin: "0 0 20px 0", fontSize: "16px", fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Transcript Moments ({updatedC.transcripts?.length || 0})
              </h3>

              <div style={{ maxHeight: "calc(67.5vh - 60px)", overflowY: "auto", paddingRight: "12px", marginRight: "-12px" }} className="custom-scrollbar">
                {updatedC.transcripts && updatedC.transcripts.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                    {[...updatedC.transcripts].sort((a, b) => a.start_time - b.start_time).map((t) => (
                      <div key={t.id} style={{ display: "flex", gap: "16px", fontSize: "15px" }}>
                        <div style={{ color: "#3b82f6", fontWeight: 600, minWidth: "100px", fontSize: "14px" }}>
                          {t.speaker}
                          <div style={{ fontSize: "12px", color: "#64748b", fontWeight: "normal", marginTop: "4px" }}>
                            {formatTime(t.start_time)}
                          </div>
                        </div>
                        <div style={{ color: "#f8fafc", lineHeight: "1.6", flex: 1, backgroundColor: "rgba(15, 23, 42, 0.4)", padding: "16px", borderRadius: "12px", border: "1px solid rgba(148, 163, 184, 0.1)", overflowWrap: "anywhere", wordBreak: "break-word" }}>
                          {t.text}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ padding: "40px 20px", textAlign: "center", color: "#64748b", fontSize: "15px", fontStyle: "italic", backgroundColor: "rgba(15, 23, 42, 0.4)", borderRadius: "12px", border: "1px dashed rgba(148, 163, 184, 0.2)" }}>
                    No transcript moments recorded for this consultation.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Transcripts & Bot Control */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div className="glass-panel" style={{ padding: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: (updatedC.recall_bot_id || botError) ? "12px" : "0" }}>
                <h3 style={{ margin: 0, fontSize: "13px", fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em", display: "flex", alignItems: "center", gap: "6px" }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 0 0-10 10v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-7a10 10 0 0 0-10-10z" /><path d="M12 8v4" /><path d="M12 16h.01" /></svg>
                  Recall Bot
                  <div className="tooltip-container" style={{ position: "relative", display: "inline-flex", alignItems: "center", cursor: "help" }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "#64748b" }}><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>
                    <div className="tooltip-text" style={{
                      visibility: "hidden",
                      width: "220px",
                      backgroundColor: "#1e293b",
                      color: "#f1f5f9",
                      textAlign: "left",
                      borderRadius: "8px",
                      padding: "12px",
                      position: "absolute",
                      zIndex: 100,
                      bottom: "125%",
                      left: "50%",
                      marginLeft: "-110px",
                      opacity: 0,
                      transition: "opacity 0.2s",
                      fontSize: "12px",
                      lineHeight: "1.5",
                      fontWeight: 400,
                      textTransform: "none",
                      letterSpacing: "normal",
                      boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.2)",
                      border: "1px solid rgba(148, 163, 184, 0.2)"
                    }}>
                      <strong style={{ display: "block", marginBottom: "4px", color: "#3b82f6" }}>How to connect:</strong>
                      1. Copy your Google Meet link.<br />
                      2. Paste it in the input below.<br />
                      3. Click "Invite" to bring the bot in.<br />
                      4. Admit the bot (Recall.ai) to the meeting.
                    </div>
                  </div>
                </h3>
                <style dangerouslySetInnerHTML={{
                  __html: `
                  .tooltip-container:hover .tooltip-text {
                    visibility: visible !important;
                    opacity: 1 !important;
                  }
                `}} />
                {updatedC.recall_bot_id && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#818cf8', fontSize: '12px', fontWeight: 500 }}>
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#818cf8', boxShadow: '0 0 6px #818cf8' }}></div>
                    Listening...
                  </div>
                )}
              </div>

              {updatedC.status !== 'draft' ? (
                <div style={{ padding: '12px', backgroundColor: 'rgba(148, 163, 184, 0.05)', border: '1px solid rgba(148, 163, 184, 0.1)', borderRadius: '8px', color: '#94a3b8', fontSize: '13px', textAlign: 'center', fontStyle: 'italic', marginTop: '10px' }}>
                  Bot only available for active consultations.
                </div>
              ) : updatedC.recall_bot_id ? (
                <button
                  onClick={() => handleDisconnectBot(updatedC.id)}
                  disabled={isDisconnecting}
                  style={{
                    width: "100%",
                    padding: '8px 16px',
                    borderRadius: '6px',
                    background: isDisconnecting ? 'rgba(239, 68, 68, 0.05)' : 'rgba(239, 68, 68, 0.1)',
                    color: '#ef4444',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: isDisconnecting ? 'not-allowed' : 'pointer',
                    marginTop: '10px'
                  }}
                >
                  {isDisconnecting ? 'Disconnecting...' : 'Disconnect Bot'}
                </button>
              ) : (
                <>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                    <div className="input-group" style={{
                      flex: 1,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                      backgroundColor: 'rgba(15, 23, 42, 0.4)',
                      transition: 'all 0.2s ease',
                      position: 'relative',
                      minWidth: 0
                    }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#64748b', flexShrink: 0 }}><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" /><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" /></svg>
                      <input
                        type="text"
                        placeholder="Meeting link..."
                        value={meetingUrl}
                        onChange={(e) => setMeetingUrl(e.target.value)}
                        style={{
                          flex: 1,
                          background: 'transparent',
                          border: 'none',
                          color: '#f8fafc',
                          fontFamily: "'Inter', system-ui, sans-serif",
                          fontSize: '14px',
                          letterSpacing: '0.01em',
                          outline: 'none',
                          padding: 0,
                          minWidth: 0
                        }}
                      />
                    </div>
                    <button
                      onClick={() => handleJoinBot(updatedC.id)}
                      disabled={isJoining || !meetingUrl.trim()}
                      style={{
                        padding: '8px 20px',
                        borderRadius: '8px',
                        background: isJoining ? 'rgba(59, 130, 246, 0.2)' : 'var(--primary-gradient)',
                        color: 'white',
                        border: 'none',
                        fontSize: '13px',
                        fontWeight: 700,
                        cursor: isJoining ? 'not-allowed' : 'pointer',
                        whiteSpace: 'nowrap',
                        transition: 'all 0.2s ease',
                        boxShadow: '0 4px 12px rgba(59, 130, 246, 0.2)'
                      }}
                    >
                      {isJoining ? 'Joining...' : 'Invite'}
                    </button>
                  </div>
                  <style dangerouslySetInnerHTML={{
                    __html: `
                    .input-group:focus-within {
                      border-color: rgba(59, 130, 246, 0.5) !important;
                      background-color: rgba(15, 23, 42, 0.6) !important;
                      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
                    }
                    .input-group:hover {
                      border-color: rgba(148, 163, 184, 0.4);
                    }
                  `}} />
                </>
              )}
              {botError && <div style={{ color: '#ef4444', fontSize: '11px', marginTop: '8px' }}>{botError}</div>}
            </div>

            <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column" }}>
              <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em", display: "flex", alignItems: "center", gap: "8px" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                AI Summary & Insights
              </h3>
              <div style={{ padding: "16px", backgroundColor: "rgba(15, 23, 42, 0.4)", borderRadius: "10px", border: "1px solid rgba(148, 163, 184, 0.1)", flex: 1, overflowY: "auto", overflowX: "hidden", minHeight: "450px", maxHeight: "70vh" }}>
                {updatedC.insights ? (
                  <div style={{ color: "#f1f5f9", lineHeight: "1.6", fontSize: "15px", whiteSpace: "pre-wrap", overflowWrap: "anywhere", wordBreak: "break-word" }}>
                    {updatedC.insights.summary}
                  </div>
                ) : (
                  <div style={{ color: "#64748b", fontStyle: "italic", fontSize: "14px", display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
                    No insights generated yet. Recordings will automatically generate insights.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }



  // List View
  return (
    <div style={{ padding: "32px 24px", width: "100%", maxWidth: "1200px", margin: "0 auto", boxSizing: "border-box" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "40px" }} className="animate-fade-in">
        <div>
          <h1 style={{ fontSize: "36px", fontWeight: 700, margin: "0 0 8px 0" }}>
            Manage <span className="text-gradient">Consultations</span>
          </h1>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: "16px" }}>
            View, create, and manage your patient records.
          </p>
        </div>
        <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
          <button
            onClick={handleCreateView}
            disabled={!!activeConsultationObj}
            style={{
              background: activeConsultationObj ? "rgba(148, 163, 184, 0.1)" : "var(--primary-gradient)",
              border: activeConsultationObj ? "1px solid rgba(148, 163, 184, 0.2)" : "none",
              padding: "12px 24px",
              borderRadius: "8px",
              color: activeConsultationObj ? "#64748b" : "white",
              fontWeight: 600,
              fontSize: "15px",
              cursor: activeConsultationObj ? "not-allowed" : "pointer",
              boxShadow: activeConsultationObj ? "none" : "0 4px 12px rgba(59, 130, 246, 0.3)",
              transition: "all 0.2s ease"
            }}
          >
            + New Consultation
          </button>
          {activeConsultationObj && (
            <div style={{ padding: "8px 12px", backgroundColor: "rgba(234, 179, 8, 0.1)", border: "1px solid rgba(234, 179, 8, 0.2)", borderRadius: "8px", color: "#facc15", fontSize: "13px", display: "flex", alignItems: "center", gap: "6px", fontWeight: 500 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
              Complete "{activeConsultationObj.title}" to start another
            </div>
          )}
        </div>
      </div>

      <div className="glass-panel animate-fade-in stagger-1" style={{ padding: "32px" }}>
        <h2 style={{ fontSize: "20px", fontWeight: 600, margin: "0 0 24px 0", color: "#f8fafc" }}>All Consultations</h2>

        {error && (
          <div style={{ padding: "12px", backgroundColor: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "8px", color: "#ef4444", marginBottom: "24px", fontSize: "14px" }}>
            {error}
          </div>
        )}

        {loading && consultations.length === 0 ? (
          <div style={{ textAlign: "center", padding: "48px", color: "#64748b" }}>Loading consultations...</div>
        ) : consultations.length === 0 ? (
          <div style={{ textAlign: "center", padding: "64px", border: "1px dashed rgba(148, 163, 184, 0.2)", borderRadius: "12px", color: "#64748b" }}>
            No consultations found. Start by creating a new one.
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))", gap: "20px" }}>
            {consultations.map((c, index) => (
              <div
                key={c.id}
                className="animate-fade-in glass-panel"
                style={{
                  animationDelay: `${(index % 5) * 0.1}s`,
                  padding: "24px",
                  cursor: "pointer",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease",
                  border: "1px solid rgba(148, 163, 184, 0.1)",
                  backgroundColor: "rgba(30, 41, 59, 0.4)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "16px"
                }}
                onClick={() => handleViewDetail(c)}
                onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-4px)"; e.currentTarget.style.borderColor = "rgba(59, 130, 246, 0.4)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.borderColor = "rgba(148, 163, 184, 0.1)"; }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                  <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 600, color: "#f1f5f9" }}>{c.title}</h3>
                  <span style={{
                    padding: "2px 8px",
                    backgroundColor: c.status === 'completed' ? "rgba(16, 185, 129, 0.1)" : "rgba(59, 130, 246, 0.1)",
                    color: c.status === 'completed' ? "#34d399" : "#60a5fa",
                    borderRadius: "4px",
                    fontSize: "11px",
                    textTransform: "uppercase",
                    fontWeight: 700,
                    border: `1px solid ${c.status === 'completed' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.2)'}`
                  }}>
                    {c.status === 'completed' ? 'Finished' : 'Active'}
                  </span>
                </div>
                <div style={{ fontSize: "13px", color: "#94a3b8", display: "flex", gap: "8px", alignItems: "center" }}>
                  <span>{new Date(c.created_at).toLocaleDateString()}</span>
                  {(c.transcripts?.length > 0 || c.insights) && <span>•</span>}
                  {c.transcripts?.length > 0 && <span style={{ color: "#60a5fa" }}>{c.transcripts.length} Moments</span>}
                  {c.insights && <span style={{ color: "#34d399" }}>Has Insights</span>}
                </div>

                {c.patient ? (
                  <div style={{ padding: "12px", backgroundColor: "rgba(0,0,0,0.2)", borderRadius: "8px", fontSize: "14px", display: "flex", flexDirection: "column", gap: "4px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#94a3b8" }}>Patient ID:</span>
                      <span style={{ color: "#e2e8f0", fontWeight: 500 }}>{c.patient.display_id}</span>
                    </div>
                    {c.patient.name && (
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#94a3b8" }}>Name:</span>
                        <span style={{ color: "#e2e8f0" }}>{c.patient.name}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ padding: "12px", backgroundColor: "rgba(0,0,0,0.2)", borderRadius: "8px", fontSize: "14px", color: "#64748b", fontStyle: "italic", textAlign: "center" }}>
                    No patient assigned
                  </div>
                )}

              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Patients({ onLogout, onNavigateToConsultation }) {
  const [view, setView] = useState("list");
  const [patients, setPatients] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [newPatient, setNewPatient] = useState({ display_id: "", name: "", date_of_birth: "", gender: "", key_history: "" });
  const [patientToDelete, setPatientToDelete] = useState(null);

  const loadData = () => {
    Promise.all([fetchPatients(), fetchConsultations()])
      .then(([pts, cons]) => {
        setPatients(pts.sort((a, b) => new Date(a.created_at) - new Date(b.created_at)));
        setConsultations(cons);
      })
      .catch((err) => {
        if (err.message === "unauthorized") onLogout();
        else setError(err.message);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
    const intervalId = setInterval(loadData, 5000);
    return () => clearInterval(intervalId);
  }, []);

  const handleViewDetail = (patient) => {
    setSelectedPatient(patient);
    setView("detail");
  };

  const filteredPatients = patients.filter(p =>
    p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.display_id?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCreatePatientSubmit = async (e) => {
    e.preventDefault();
    if (!newPatient.display_id.trim()) return;
    setError("");
    try {
      const payload = { ...newPatient };
      if (!payload.date_of_birth) delete payload.date_of_birth;
      const createdP = await createPatient(payload);
      setPatients(prev => [...prev, createdP].sort((a, b) => new Date(a.created_at) - new Date(b.created_at)));
      setView("list");
    } catch (err) {
      if (err.message === "unauthorized") onLogout();
      else setError(err.message);
    }
  };

  const handleUpdatePatientSubmit = async (e) => {
    e.preventDefault();
    if (!newPatient.display_id.trim()) return;
    setError("");
    try {
      const payload = { ...newPatient };
      if (!payload.date_of_birth) delete payload.date_of_birth;
      const updatedP = await updatePatient(selectedPatient.id, payload);
      setPatients(prev => prev.map(p => p.id === updatedP.id ? updatedP : p).sort((a, b) => new Date(a.created_at) - new Date(b.created_at)));
      setSelectedPatient(updatedP);
      setView("detail");
    } catch (err) {
      if (err.message === "unauthorized") onLogout();
      else setError(err.message);
    }
  };

  const handleDeletePatient = async (id) => {
    try {
      await deletePatient(id);
      setPatients(prev => prev.filter(p => p.id !== id));
      setConsultations(prev => prev.filter(c => !c.patient || c.patient.id !== id));
      setView("list");
      setSelectedPatient(null);
      setPatientToDelete(null);
      setSuccessMessage("patient and associated data deleted");
      setTimeout(() => setSuccessMessage(""), 5000);
    } catch (err) {
      if (err.message === "unauthorized") onLogout();
      else setError(err.message);
      setPatientToDelete(null);
    }
  };

  if (view === "detail" && selectedPatient) {
    const p = selectedPatient;
    const patientConsultations = consultations
      .filter(c => c.patient && c.patient.id === p.id)
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

    return (
      <div style={{ padding: "32px 24px", width: "100%", maxWidth: "1200px", margin: "0 auto", boxSizing: "border-box", animation: "fadeIn 0.3s ease" }}>
        <button onClick={() => setView("list")} style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", marginBottom: "24px" }}>
          <span>←</span> Back to all patients
        </button>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
          <h1 style={{ fontSize: "36px", fontWeight: 700, margin: "0", color: "#f8fafc" }}>
            Patient Details: {p.name || p.display_id}
          </h1>
          <div style={{ display: "flex", gap: "12px" }}>
            <button
              onClick={() => { setNewPatient({ ...p, date_of_birth: p.date_of_birth || "" }); setView("edit"); }}
              style={{ padding: "8px 16px", borderRadius: "8px", border: "1px solid rgba(148, 163, 184, 0.2)", backgroundColor: "rgba(15, 23, 42, 0.4)", color: "#f1f5f9", cursor: "pointer", fontWeight: 600, fontSize: "14px" }}
              className="hover-bg"
            >
              Edit Details
            </button>
            <button
              onClick={() => setPatientToDelete(p.id)}
              style={{ padding: "8px 16px", borderRadius: "8px", border: "1px solid rgba(239, 68, 68, 0.2)", backgroundColor: "rgba(239, 68, 68, 0.1)", color: "#ef4444", cursor: "pointer", fontWeight: 600, fontSize: "14px" }}
              className="hover-bg-danger"
            >
              Delete Patient
            </button>
          </div>
        </div>

        {patientToDelete === p.id && (
          <div className="animate-fade-in" style={{ padding: "24px", backgroundColor: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "12px", marginBottom: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <h3 style={{ margin: 0, color: "#ef4444", fontSize: "18px", display: "flex", alignItems: "center", gap: "8px" }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
              CRITICAL WARNING
            </h3>
            <p style={{ color: "#f8fafc", margin: 0, fontSize: "15px", lineHeight: "1.5" }}>
              Are you sure you want to delete this patient? This will physically delete the patient AND all of their associated consultations, transcripts, and insights permanently. This CANNOT be reversed.
            </p>
            <div style={{ display: "flex", gap: "12px", marginTop: "8px" }}>
              <button
                onClick={() => setPatientToDelete(null)}
                style={{ padding: "8px 16px", borderRadius: "8px", border: "1px solid rgba(148, 163, 184, 0.3)", backgroundColor: "transparent", color: "#f8fafc", cursor: "pointer", fontWeight: 600 }}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeletePatient(p.id)}
                style={{ padding: "8px 16px", borderRadius: "8px", border: "none", backgroundColor: "#ef4444", color: "white", cursor: "pointer", fontWeight: 600 }}
              >
                Yes, Delete Permanently
              </button>
            </div>
          </div>
        )}

        {error && (
          <div style={{ padding: "12px", backgroundColor: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "8px", color: "#ef4444", marginBottom: "24px", fontSize: "14px" }}>
            {error}
          </div>
        )}

        <div className="glass-panel" style={{ padding: "24px", marginBottom: "24px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "16px", color: "#f1f5f9", fontSize: "15px" }}>
          <div>
            <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>Display ID</div>
            <div>{p.display_id}</div>
          </div>
          <div>
            <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>Full Name</div>
            <div>{p.name || "N/A"}</div>
          </div>
          <div>
            <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>Date of Birth</div>
            <div>{p.date_of_birth || "N/A"}</div>
          </div>
          <div>
            <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>Gender</div>
            <div>{p.gender || "N/A"}</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "24px", marginBottom: "24px" }}>
          <h3 style={{ margin: "0 0 12px 0", fontSize: "16px", fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em", display: "flex", alignItems: "center", gap: "8px" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>
            Key Insights
          </h3>
          <div style={{ color: p.key_history ? "#f1f5f9" : "#64748b", fontSize: "15px", lineHeight: "1.6", whiteSpace: "pre-wrap", fontStyle: p.key_history ? "normal" : "italic" }}>
            {p.key_history || "No key insights or history recorded for this patient yet."}
          </div>
        </div>

        <h2 style={{ fontSize: "20px", fontWeight: 600, margin: "0 0 16px 0", color: "#f8fafc" }}>Consultations History</h2>
        {patientConsultations.length === 0 ? (
          <div style={{ padding: "24px", color: "#64748b", backgroundColor: "rgba(15, 23, 42, 0.4)", borderRadius: "12px", border: "1px dashed rgba(148, 163, 184, 0.2)" }}>No consultations found for this patient.</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {patientConsultations.map((c, index) => (
              <div
                key={c.id}
                className="animate-fade-in glass-panel hover-bg"
                style={{ animationDelay: `${(index % 5) * 0.1}s`, padding: "16px", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", transition: "transform 0.2s ease", border: "1px solid rgba(148, 163, 184, 0.1)", backgroundColor: "rgba(30, 41, 59, 0.4)" }}
                onClick={() => onNavigateToConsultation(c.id)}
              >
                <div>
                  <div style={{ fontWeight: 600, color: "#f1f5f9", fontSize: "16px" }}>{c.title}</div>
                  <div style={{ fontSize: "13px", color: "#94a3b8", marginTop: "4px" }}>Taken on: {new Date(c.created_at).toLocaleString()}</div>
                </div>
                <div>
                  <span style={{ padding: "4px 8px", backgroundColor: c.status === 'completed' ? "rgba(16, 185, 129, 0.1)" : "rgba(234, 179, 8, 0.1)", color: c.status === 'completed' ? "#34d399" : "#facc15", borderRadius: "4px", fontSize: "12px", textTransform: "uppercase", fontWeight: 600 }}>
                    {c.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (view === "create" || view === "edit") {
    const isEditing = view === "edit";
    return (
      <div style={{ padding: "32px 24px", width: "100%", maxWidth: "800px", margin: "0 auto", boxSizing: "border-box", animation: "fadeIn 0.3s ease" }}>
        <button onClick={() => setView(isEditing ? "detail" : "list")} style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", marginBottom: "24px" }}>
          <span>←</span> Back to {isEditing ? "patient details" : "list"}
        </button>
        <h1 style={{ fontSize: "36px", fontWeight: 700, margin: "0 0 24px 0", color: "#f8fafc" }}>
          {isEditing ? "Edit Patient Details" : "Create New Patient"}
        </h1>
        <div className="glass-panel" style={{ padding: "32px" }}>
          <form onSubmit={isEditing ? handleUpdatePatientSubmit : handleCreatePatientSubmit} style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Patient ID {isEditing ? "" : "*"}</label>
                <input
                  style={{ padding: "12px", borderRadius: "8px", border: "1px solid rgba(148, 163, 184, 0.2)", backgroundColor: "rgba(15, 23, 42, 0.4)", color: isEditing ? "#64748b" : "#f8fafc", outline: "none", cursor: isEditing ? "not-allowed" : "text" }}
                  value={newPatient.display_id}
                  onChange={(e) => !isEditing && setNewPatient({ ...newPatient, display_id: e.target.value })}
                  placeholder="e.g. P-001"
                  required
                  disabled={isEditing}
                />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Full Name</label>
                <input
                  style={{ padding: "12px", borderRadius: "8px", border: "1px solid rgba(148, 163, 184, 0.2)", backgroundColor: "rgba(15, 23, 42, 0.4)", color: "#f8fafc", outline: "none" }}
                  value={newPatient.name}
                  onChange={(e) => setNewPatient({ ...newPatient, name: e.target.value })}
                  placeholder="e.g. Jane Doe"
                />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Date of Birth</label>
                <input
                  type="date"
                  style={{ padding: "12px", borderRadius: "8px", border: "1px solid rgba(148, 163, 184, 0.2)", backgroundColor: "rgba(15, 23, 42, 0.4)", color: "#f8fafc", outline: "none", colorScheme: "dark" }}
                  value={newPatient.date_of_birth}
                  onChange={(e) => setNewPatient({ ...newPatient, date_of_birth: e.target.value })}
                />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Gender</label>
                <select
                  style={{ padding: "12px", borderRadius: "8px", border: "1px solid rgba(148, 163, 184, 0.2)", backgroundColor: "rgba(15, 23, 42, 0.4)", color: "#f8fafc", outline: "none" }}
                  value={newPatient.gender}
                  onChange={(e) => setNewPatient({ ...newPatient, gender: e.target.value })}
                >
                  <option value="">-- Select --</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Key History / Notes</label>
              <textarea
                style={{ padding: "12px", borderRadius: "8px", border: "1px solid rgba(148, 163, 184, 0.2)", backgroundColor: "rgba(15, 23, 42, 0.4)", color: "#f8fafc", outline: "none", minHeight: "100px", resize: "vertical" }}
                value={newPatient.key_history}
                onChange={(e) => setNewPatient({ ...newPatient, key_history: e.target.value })}
                placeholder="Important medical history, allergies, or ongoing conditions..."
              />
            </div>

            {error && <div style={{ color: "#ef4444", fontSize: "14px" }}>{error}</div>}

            <button
              type="submit"
              disabled={!newPatient.display_id.trim()}
              style={{
                background: "var(--primary-gradient)",
                border: "none",
                padding: "12px 24px",
                borderRadius: "8px",
                color: "white",
                fontWeight: 600,
                fontSize: "16px",
                cursor: "pointer",
                marginTop: "16px",
                alignSelf: "flex-end",
                opacity: !newPatient.display_id.trim() ? 0.6 : 1
              }}
            >
              {isEditing ? "Save Changes" : "Create Patient"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: "32px 24px", width: "100%", maxWidth: "1200px", margin: "0 auto", boxSizing: "border-box" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "40px" }} className="animate-fade-in">
        <div>
          <h1 style={{ fontSize: "36px", fontWeight: 700, margin: "0 0 8px 0" }}>
            Patient <span className="text-gradient">Records</span>
          </h1>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: "16px" }}>
            Find and manage patient profiles.
          </p>
        </div>
        <button
          onClick={() => {
            setNewPatient({ display_id: "", name: "", date_of_birth: "", gender: "", key_history: "" });
            setView("create");
          }}
          style={{
            background: "var(--primary-gradient)",
            border: "none",
            padding: "12px 24px",
            borderRadius: "8px",
            color: "white",
            fontWeight: 600,
            fontSize: "15px",
            cursor: "pointer",
            boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)",
          }}
        >
          + New Patient
        </button>
      </div>
      <div className="glass-panel animate-fade-in stagger-1" style={{ padding: "32px" }}>
        {successMessage && (
          <div className="animate-fade-in" style={{ padding: "16px", backgroundColor: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: "8px", color: "#34d399", marginBottom: "24px", fontSize: "15px", display: "flex", alignItems: "center", gap: "8px" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            {successMessage}
          </div>
        )}
        <input
          type="text"
          placeholder="Search by ID or Name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ width: "100%", padding: "12px", marginBottom: "32px", borderRadius: "8px", border: "1px solid rgba(148, 163, 184, 0.2)", backgroundColor: "rgba(15, 23, 42, 0.4)", color: "#f8fafc", outline: "none", boxSizing: "border-box" }}
        />
        {loading && patients.length === 0 ? (
          <div style={{ textAlign: "center", padding: "48px", color: "#64748b" }}>Loading patients...</div>
        ) : filteredPatients.length === 0 ? (
          <div style={{ textAlign: "center", padding: "48px", border: "1px dashed rgba(148, 163, 184, 0.2)", borderRadius: "12px", color: "#64748b" }}>No patients found.</div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "20px" }}>
            {filteredPatients.map((p, index) => (
              <div
                key={p.id}
                className="animate-fade-in glass-panel"
                style={{
                  animationDelay: `${(index % 5) * 0.1}s`,
                  padding: "24px",
                  cursor: "pointer",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease",
                  border: "1px solid rgba(148, 163, 184, 0.1)",
                  backgroundColor: "rgba(30, 41, 59, 0.4)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px"
                }}
                onClick={() => handleViewDetail(p)}
                onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-4px)"; e.currentTarget.style.borderColor = "rgba(59, 130, 246, 0.4)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.borderColor = "rgba(148, 163, 184, 0.1)"; }}
              >
                <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 600, color: "#f1f5f9", display: "flex", alignItems: "center", gap: "8px" }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                  {p.name || p.display_id}
                </h3>
                <div style={{ padding: "12px", backgroundColor: "rgba(0,0,0,0.2)", borderRadius: "8px", fontSize: "14px", display: "flex", flexDirection: "column", gap: "6px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}><span style={{ color: "#94a3b8" }}>ID:</span> <span style={{ color: "#e2e8f0", fontWeight: 500 }}>{p.display_id}</span></div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}><span style={{ color: "#94a3b8" }}>Created:</span> <span style={{ color: "#e2e8f0" }}>{new Date(p.created_at).toLocaleDateString()}</span></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AIAnalytics() {
  return (
    <div style={{ padding: "32px 24px", width: "100%", maxWidth: "1200px", margin: "0 auto", boxSizing: "border-box" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "40px" }} className="animate-fade-in">
        <div>
          <h1 style={{ fontSize: "36px", fontWeight: 700, margin: "0 0 8px 0" }}>
            AI <span className="text-gradient">Analytics</span>
          </h1>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: "16px" }}>
            Advanced health patterns and consultation intelligence.
          </p>
        </div>
      </div>

      <div className="glass-panel animate-fade-in stagger-1" style={{ padding: "48px", textAlign: "center" }}>
        <div style={{
          width: "80px",
          height: "80px",
          margin: "0 auto 32px auto",
          background: "rgba(59, 130, 246, 0.1)",
          borderRadius: "20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#3b82f6"
        }}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /><polyline points="3.27 6.96 12 12.01 20.73 6.96" /><line x1="12" y1="22.08" x2="12" y2="12" /></svg>
        </div>

        <h2 style={{ fontSize: "24px", fontWeight: 600, color: "#f8fafc", marginBottom: "16px" }}>Intellectual Analysis Coming Soon</h2>

        <div style={{ maxWidth: "600px", margin: "0 auto", color: "#94a3b8", lineHeight: "1.8", fontSize: "16px" }}>
          <p>
            The **AI Analytics Engine** is currently under development. This section will feature a
            specialized Large Language Model designed to securely process your historical
            consultation data.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginTop: "40px", textAlign: "left" }}>
            <div style={{ padding: "20px", backgroundColor: "rgba(15, 23, 42, 0.4)", borderRadius: "12px", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
              <div style={{ fontWeight: 600, color: "#f1f5f9", marginBottom: "8px" }}>📊 Pattern Recognition</div>
              <div style={{ fontSize: "14px" }}>Identify recurring patient symptoms and diagnosis trends across your entire practice history.</div>
            </div>
            <div style={{ padding: "20px", backgroundColor: "rgba(15, 23, 42, 0.4)", borderRadius: "12px", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
              <div style={{ fontWeight: 600, color: "#f1f5f9", marginBottom: "8px" }}>📈 Practice Growth</div>
              <div style={{ fontSize: "14px" }}>Visual statistics on consultation volume, average session times, and automated reporting.</div>
            </div>
            <div style={{ padding: "20px", backgroundColor: "rgba(15, 23, 42, 0.4)", borderRadius: "12px", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
              <div style={{ fontWeight: 600, color: "#f1f5f9", marginBottom: "8px" }}>🧬 Health Insights</div>
              <div style={{ fontSize: "14px" }}>LLM-driven analysis of transcript data to suggest potential treatment paths and drug interactions.</div>
            </div>
            <div style={{ padding: "20px", backgroundColor: "rgba(15, 23, 42, 0.4)", borderRadius: "12px", border: "1px solid rgba(148, 163, 184, 0.1)" }}>
              <div style={{ fontWeight: 600, color: "#f1f5f9", marginBottom: "8px" }}>🔒 Private & Secure</div>
              <div style={{ fontSize: "14px" }}>Local-first processing ensuring patient data never leaves your secure environment.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AskAI() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  const loadSessions = async () => {
    try {
      const data = await fetchChatSessions();
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        handleSelectSession(data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleSelectSession = async (id) => {
    setActiveSessionId(id);
    try {
      const session = await fetchChatSession(id);
      setMessages(session.messages || []);
    } catch (err) {
      console.error("Failed to load session messages", err);
    }
  };

  const handleNewChat = async () => {
    try {
      const newSession = await createChatSession("New Conversation");
      setSessions([newSession, ...sessions]);
      setActiveSessionId(newSession.id);
      setMessages([]);
    } catch (err) {
      console.error("Failed to create new chat", err);
    }
  };

  const handleDeleteSession = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this conversation?")) return;
    try {
      await deleteChatSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (activeSessionId === id) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to delete chat", err);
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    let targetSessionId = activeSessionId;
    if (!targetSessionId) {
      try {
        const title = input.substring(0, 30) + (input.length > 30 ? "..." : "");
        const newSession = await createChatSession(title);
        setSessions([newSession, ...sessions]);
        setActiveSessionId(newSession.id);
        targetSessionId = newSession.id;
      } catch (err) {
        console.error("Failed to implicitly create chat", err);
        return;
      }
    }

    const userMessage = { role: "user", content: input.trim() };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChatMessage(targetSessionId, userMessage.content);
      setMessages([...newMessages, response]);
    } catch (err) {
      console.error(err);
      setMessages([...newMessages, { role: "assistant", content: "Sorry, I encountered an error answering your question." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", height: "100%", maxWidth: "1400px", margin: "0 auto", width: "100%", padding: "24px", boxSizing: "border-box", gap: "24px" }}>
      {/* Sidebar for Sessions */}
      <div className="glass-panel animate-fade-in stagger-1" style={{ width: "300px", display: "flex", flexDirection: "column", borderRadius: "16px", overflow: "hidden" }}>
        <div style={{ padding: "20px", borderBottom: "1px solid rgba(148, 163, 184, 0.1)" }}>
          <button
            onClick={handleNewChat}
            style={{
              width: "100%",
              background: "var(--primary-gradient)",
              border: "none",
              padding: "12px",
              borderRadius: "8px",
              color: "white",
              fontWeight: 600,
              fontSize: "15px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px"
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            New Chat
          </button>
        </div>

        <div className="custom-scrollbar" style={{ flex: 1, overflowY: "auto", padding: "12px", display: "flex", flexDirection: "column", gap: "8px" }}>
          {sessions.length === 0 ? (
            <div style={{ color: "#64748b", textAlign: "center", fontStyle: "italic", fontSize: "14px", marginTop: "20px" }}>No past conversations</div>
          ) : (
            sessions.map(s => (
              <div
                key={s.id}
                onClick={() => handleSelectSession(s.id)}
                style={{
                  padding: "12px 16px",
                  borderRadius: "10px",
                  cursor: "pointer",
                  backgroundColor: activeSessionId === s.id ? "rgba(59, 130, 246, 0.15)" : "transparent",
                  border: activeSessionId === s.id ? "1px solid rgba(59, 130, 246, 0.3)" : "1px solid transparent",
                  transition: "all 0.2s ease",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center"
                }}
                className="hover-bg"
              >
                <div style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: activeSessionId === s.id ? "#60a5fa" : "#e2e8f0", fontSize: "14px", fontWeight: activeSessionId === s.id ? 600 : 400 }}>
                  {s.title}
                </div>
                <button
                  onClick={(e) => handleDeleteSession(e, s.id)}
                  style={{
                    background: "transparent", border: "none", color: "#64748b", cursor: "pointer", padding: "4px", display: "flex", alignItems: "center", justifyContent: "center", borderRadius: "4px"
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; e.currentTarget.style.backgroundColor = "rgba(239, 68, 68, 0.1)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "#64748b"; e.currentTarget.style.backgroundColor = "transparent"; }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ marginBottom: "20px" }} className="animate-fade-in">
          <h1 style={{ fontSize: "32px", fontWeight: 700, margin: "0 0 8px 0" }}>
            Ask <span className="text-gradient">AI</span>
          </h1>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: "15px" }}>
            Chat with your intelligent assistant.
          </p>
        </div>

        <div className="glass-panel animate-fade-in stagger-2" style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", borderRadius: "16px" }}>
          {/* Chat window */}
          <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
            {messages.length === 0 && !loading && (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "#64748b", gap: "16px", padding: "20px", textAlign: "center" }}>
                <div style={{ width: "64px", height: "64px", borderRadius: "16px", background: "rgba(139, 92, 246, 0.1)", display: "flex", alignItems: "center", justifyContent: "center", color: "#8b5cf6" }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /><path d="M12 7v5" /><path d="M12 16h.01" /></svg>
                </div>
                <div>
                  <h3 style={{ margin: "0 0 8px 0", color: "#f8fafc", fontSize: "18px" }}>How can I help you today?</h3>
                  <p style={{ margin: 0, fontSize: "15px" }}>Start a new conversation or select one from the history.</p>
                </div>
              </div>
            )}

            {messages.map((msg, index) => {
              const isUser = msg.role === "user";
              return (
                <div key={index} style={{ display: "flex", gap: "16px", alignSelf: isUser ? "flex-end" : "flex-start", maxWidth: "85%" }}>
                  {!isUser && (
                    <div style={{
                      width: "36px", height: "36px", borderRadius: "10px", background: "rgba(139, 92, 246, 0.2)",
                      display: "flex", alignItems: "center", justifyContent: "center", color: "#8b5cf6", flexShrink: 0
                    }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /><path d="M12 7v5" /><path d="M12 16h.01" /></svg>
                    </div>
                  )}
                  <div style={{
                    padding: "16px 20px",
                    backgroundColor: isUser ? "var(--primary-gradient)" : "rgba(30, 41, 59, 0.5)",
                    background: isUser ? "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)" : undefined,
                    borderRadius: isUser ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
                    color: "#f8fafc",
                    fontSize: "15px",
                    lineHeight: "1.6",
                    border: isUser ? "none" : "1px solid rgba(148, 163, 184, 0.1)",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                    whiteSpace: "pre-wrap",
                    overflowWrap: "anywhere",
                  }}>
                    {msg.content}
                  </div>
                  {isUser && (
                    <div style={{
                      width: "36px", height: "36px", borderRadius: "10px", background: "rgba(59, 130, 246, 0.2)",
                      display: "flex", alignItems: "center", justifyContent: "center", color: "#3b82f6", flexShrink: 0
                    }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    </div>
                  )}
                </div>
              );
            })}

            {loading && (
              <div style={{ display: "flex", gap: "16px", alignSelf: "flex-start", maxWidth: "80%" }}>
                <div style={{
                  width: "36px", height: "36px", borderRadius: "10px", background: "rgba(139, 92, 246, 0.2)",
                  display: "flex", alignItems: "center", justifyContent: "center", color: "#8b5cf6", flexShrink: 0
                }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /><path d="M12 7v5" /><path d="M12 16h.01" /></svg>
                </div>
                <div style={{
                  padding: "16px 20px",
                  backgroundColor: "rgba(30, 41, 59, 0.5)",
                  borderRadius: "20px 20px 20px 4px",
                  color: "#94a3b8",
                  fontSize: "15px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  border: "1px solid rgba(148, 163, 184, 0.1)"
                }}>
                  <div className="typing-dot" style={{ width: "6px", height: "6px", backgroundColor: "#8b5cf6", borderRadius: "50%" }}></div>
                  <div className="typing-dot" style={{ width: "6px", height: "6px", backgroundColor: "#8b5cf6", borderRadius: "50%" }}></div>
                  <div className="typing-dot" style={{ width: "6px", height: "6px", backgroundColor: "#8b5cf6", borderRadius: "50%" }}></div>
                </div>
              </div>
            )}
          </div>

          {/* Input area */}
          <div style={{ padding: "20px", borderTop: "1px solid rgba(148, 163, 184, 0.1)", backgroundColor: "rgba(15, 23, 42, 0.4)" }}>
            <form onSubmit={handleSubmit} style={{ display: "flex", gap: "12px", position: "relative" }}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything..."
                style={{
                  flex: 1,
                  padding: "16px 24px",
                  paddingRight: "60px",
                  borderRadius: "999px",
                  border: "1px solid rgba(148, 163, 184, 0.2)",
                  backgroundColor: "rgba(15, 23, 42, 0.6)",
                  color: "#f8fafc",
                  fontSize: "15px",
                  outline: "none",
                  transition: "all 0.2s ease"
                }}
                disabled={loading}
                onFocus={(e) => { e.target.style.borderColor = "rgba(139, 92, 246, 0.5)"; e.target.style.boxShadow = "0 0 0 2px rgba(139, 92, 246, 0.1)"; }}
                onBlur={(e) => { e.target.style.borderColor = "rgba(148, 163, 184, 0.2)"; e.target.style.boxShadow = "none"; }}
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                style={{
                  position: "absolute",
                  right: "8px",
                  top: "8px",
                  bottom: "8px",
                  width: "40px",
                  borderRadius: "50%",
                  border: "none",
                  background: (!input.trim() || loading) ? "rgba(148, 163, 184, 0.1)" : "var(--primary-gradient)",
                  backgroundImage: (!input.trim() || loading) ? "none" : "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)",
                  color: (!input.trim() || loading) ? "#64748b" : "white",
                  cursor: (!input.trim() || loading) ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.2s ease"
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              </button>
            </form>
            <div style={{ textAlign: "center", marginTop: "12px", fontSize: "12px", color: "#64748b" }}>
              AI can make mistakes. Consider verifying important information.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Settings({ onLogout }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");
    if (newPassword !== confirmNewPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }
    setChangingPassword(true);
    try {
      await changePassword(currentPassword, newPassword);
      setPasswordSuccess("Password changed successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
    } catch (err) {
      if (err.message === "unauthorized") {
        if (onLogout) onLogout();
      } else {
        setPasswordError(err.message || "Failed to change password");
      }
    } finally {
      setChangingPassword(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch((err) => {
        if (err.message === "unauthorized") {
          if (onLogout) onLogout();
        } else {
          setError(err.message);
        }
      })
      .finally(() => setLoading(false));
  }, [onLogout]);

  return (
    <div style={{ padding: "32px 24px", width: "100%", maxWidth: "1200px", margin: "0 auto", boxSizing: "border-box" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "40px" }} className="animate-fade-in">
        <div>
          <h1 style={{ fontSize: "36px", fontWeight: 700, margin: "0 0 8px 0" }}>
            Settings
          </h1>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: "16px" }}>
            Manage your account and preferences.
          </p>
        </div>
      </div>
      <div className="glass-panel animate-fade-in stagger-1" style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
        {loading ? (
          <div style={{ textAlign: "center", padding: "48px", color: "#64748b" }}>Loading your data...</div>
        ) : error ? (
          <div style={{ padding: "12px", backgroundColor: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "8px", color: "#ef4444", fontSize: "14px" }}>
            {error}
          </div>
        ) : user ? (
          <div>
            <h2 style={{ fontSize: "20px", fontWeight: 600, margin: "0 0 24px 0", color: "#f8fafc" }}>Profile Information</h2>

            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "16px", maxWidth: "600px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Full Name</label>
                <div style={{ padding: "12px 16px", backgroundColor: "rgba(15, 23, 42, 0.4)", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9", fontSize: "15px" }}>
                  {user.name}
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Email Address</label>
                <div style={{ padding: "12px 16px", backgroundColor: "rgba(15, 23, 42, 0.4)", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9", fontSize: "15px" }}>
                  {user.email}
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Role</label>
                <div style={{ padding: "12px 16px", backgroundColor: "rgba(15, 23, 42, 0.4)", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9", fontSize: "15px", textTransform: "capitalize" }}>
                  {user.role}
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Account Created</label>
                <div style={{ padding: "12px 16px", backgroundColor: "rgba(15, 23, 42, 0.4)", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9", fontSize: "15px" }}>
                  {new Date(user.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
                </div>
              </div>
            </div>

            <h2 style={{ fontSize: "20px", fontWeight: 600, margin: "32px 0 24px 0", color: "#f8fafc" }}>Change Password</h2>
            <form onSubmit={handlePasswordChange} style={{ display: "flex", flexDirection: "column", gap: "16px", maxWidth: "600px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Current Password</label>
                <input
                  type="password"
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                  style={{ padding: "12px 16px", backgroundColor: "rgba(15, 23, 42, 0.4)", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9", fontSize: "15px", outline: "none", transition: "border-color 0.2s" }}
                  onFocus={(e) => e.target.style.borderColor = "#3b82f6"}
                  onBlur={(e) => e.target.style.borderColor = "rgba(148, 163, 184, 0.2)"}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>New Password</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  style={{ padding: "12px 16px", backgroundColor: "rgba(15, 23, 42, 0.4)", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9", fontSize: "15px", outline: "none", transition: "border-color 0.2s" }}
                  onFocus={(e) => e.target.style.borderColor = "#3b82f6"}
                  onBlur={(e) => e.target.style.borderColor = "rgba(148, 163, 184, 0.2)"}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500 }}>Confirm New Password</label>
                <input
                  type="password"
                  required
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  placeholder="••••••••"
                  style={{ padding: "12px 16px", backgroundColor: "rgba(15, 23, 42, 0.4)", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: "8px", color: "#f1f5f9", fontSize: "15px", outline: "none", transition: "border-color 0.2s" }}
                  onFocus={(e) => e.target.style.borderColor = "#3b82f6"}
                  onBlur={(e) => e.target.style.borderColor = "rgba(148, 163, 184, 0.2)"}
                />
              </div>

              {passwordError && (
                <div style={{ padding: "10px", backgroundColor: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "6px", color: "#ef4444", fontSize: "13px", textAlign: "center" }}>
                  {passwordError}
                </div>
              )}
              {passwordSuccess && (
                <div style={{ padding: "10px", backgroundColor: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: "6px", color: "#34d399", fontSize: "13px", textAlign: "center" }}>
                  {passwordSuccess}
                </div>
              )}

              <button
                type="submit"
                disabled={changingPassword || !currentPassword || !newPassword || !confirmNewPassword}
                style={{
                  background: "var(--primary-gradient)",
                  border: "none",
                  padding: "12px 24px",
                  borderRadius: "8px",
                  color: "white",
                  fontWeight: 600,
                  fontSize: "15px",
                  cursor: (changingPassword || !currentPassword || !newPassword || !confirmNewPassword) ? "default" : "pointer",
                  marginTop: "8px",
                  opacity: (changingPassword || !currentPassword || !newPassword || !confirmNewPassword) ? 0.6 : 1,
                  boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)",
                }}
              >
                {changingPassword ? "Updating..." : "Change Password"}
              </button>
            </form>

            <h2 style={{ fontSize: "20px", fontWeight: 600, margin: "48px 0 24px 0", color: "#f8fafc" }}>Danger Zone</h2>
            <div style={{ padding: "24px", backgroundColor: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "12px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "24px" }}>
              <div>
                <h4 style={{ margin: "0 0 4px 0", color: "#ef4444", fontSize: "16px", fontWeight: 600 }}>Delete Account</h4>
                <p style={{ margin: 0, color: "#94a3b8", fontSize: "14px" }}>Once you delete your account, there is no going back. Please be certain.</p>
              </div>
              <button
                onClick={async () => {
                  if (window.confirm("ARE YOU SURE? This will permanently delete your account and all associated data, including consultations and patients. This action cannot be undone.")) {
                    try {
                      await deleteAccount();
                      if (onLogout) onLogout();
                    } catch (err) {
                      alert(err.message || "Failed to delete account");
                    }
                  }
                }}
                style={{
                  padding: "10px 20px",
                  backgroundColor: "rgba(239, 68, 68, 0.1)",
                  color: "#ef4444",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  borderRadius: "8px",
                  fontSize: "14px",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s ease"
                }}
                onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "rgba(239, 68, 68, 0.2)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "rgba(239, 68, 68, 0.1)"; }}
              >
                Delete Permanently
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function Dashboard({ onLogout }) {
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState(null);

  const loadData = () => {
    fetchConsultations()
      .then(setConsultations)
      .catch((err) => {
        if (err.message === "unauthorized") {
          onLogout();
        } else {
          setError(err.message);
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();

    // Poll for updates every 3 seconds
    const intervalId = setInterval(() => {
      loadData();
    }, 3000);
    const handleStatusChanged = () => loadData();
    window.addEventListener('consultationStatusChanged', handleStatusChanged);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener('consultationStatusChanged', handleStatusChanged);
    };
  }, [onLogout]);

  // Calculate stats for the welcome summary
  const totalConsultations = consultations.length;
  const totalTranscripts = consultations.reduce(
    (acc, c) => acc + (c.transcripts?.length || 0),
    0
  );
  const totalInsights = consultations.filter((c) => c.insights).length;

  const handleToggleExpand = (id) => {
    setExpandedId((prevId) => (prevId === id ? null : id));
  };

  const handleFinish = async (e, id) => {
    if (e) e.stopPropagation();
    if (!window.confirm("Mark this consultation as finished?")) return;
    try {
      await updateConsultationStatus(id, "completed");
      loadData(); // Dashboard's loadData
      window.dispatchEvent(new Event('consultationStatusChanged'));
    } catch (err) {
      if (err.message === "unauthorized") onLogout();
      else setError(err.message);
    }
  };

  const formatTime = (seconds) => {
    if (!isFinite(seconds)) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div style={{ padding: "32px 24px", width: "100%", maxWidth: "1200px", margin: "0 auto", boxSizing: "border-box" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "40px" }} className="animate-fade-in">
        <div>
          <h1 style={{ fontSize: "36px", fontWeight: 700, margin: "0 0 8px 0" }}>
            Welcome back <span className="text-gradient">Doctor</span>
          </h1>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: "16px" }}>
            Here is an overview of your recent patient consultations.
          </p>
        </div>
      </div>

      {/* Stats Overview */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "24px", marginBottom: "40px" }} className="animate-fade-in stagger-1">
        <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>Total Consultations</div>
          <div style={{ fontSize: "36px", fontWeight: 700, color: "#f8fafc" }}>{loading ? "-" : totalConsultations}</div>
        </div>
        <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>Transcript Moments</div>
          <div style={{ fontSize: "36px", fontWeight: 700, color: "#f8fafc" }}>{loading ? "-" : totalTranscripts}</div>
        </div>
        <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>Insights Generated</div>
          <div style={{ fontSize: "36px", fontWeight: 700, color: "#f8fafc" }}>{loading ? "-" : totalInsights}</div>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr)", gap: "24px" }} className="animate-fade-in stagger-2">
        <div className="glass-panel" style={{ padding: "32px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
            <h2 style={{ fontSize: "20px", fontWeight: 600, margin: 0, color: "#f8fafc" }}>Recent Consultations</h2>
          </div>

          {error && (
            <div style={{ padding: "12px", backgroundColor: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "8px", color: "#ef4444", marginBottom: "24px", fontSize: "14px" }}>
              {error}
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: "center", padding: "48px", color: "#64748b" }}>Loading your data...</div>
          ) : consultations.length === 0 ? (
            <div style={{ textAlign: "center", padding: "64px", border: "1px dashed rgba(148, 163, 184, 0.2)", borderRadius: "12px", color: "#64748b" }}>
              No recent consultations found.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {consultations.map((c, index) => (
                <div key={c.id} className="animate-fade-in" style={{ animationDelay: `${(index % 5 + 3) * 0.1}s` }}>
                  <div
                    onClick={() => handleToggleExpand(c.id)}
                    style={{
                      padding: "20px",
                      backgroundColor: "rgba(30, 41, 59, 0.4)",
                      border: "1px solid rgba(148, 163, 184, 0.1)",
                      borderRadius: expandedId === c.id ? "12px 12px 0 0" : "12px",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      flexWrap: "wrap",
                      gap: "16px",
                      cursor: "pointer",
                      transition: "all 0.2s ease"
                    }}
                  >
                    <div>
                      <h3 style={{ margin: "0 0 6px 0", fontSize: "16px", fontWeight: 600, color: "#f1f5f9" }}>{c.title}</h3>
                      <div style={{ display: "flex", gap: "16px", fontSize: "13px", color: "#94a3b8" }}>
                        <span>Started: {new Date(c.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</span>
                      </div>
                    </div>

                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      {c.transcripts?.length > 0 ? (
                        <span style={{ padding: "4px 10px", backgroundColor: "rgba(59, 130, 246, 0.1)", color: "#60a5fa", borderRadius: "999px", fontSize: "12px", fontWeight: 500, border: "1px solid rgba(59, 130, 246, 0.2)" }}>
                          {c.transcripts.length} Moments
                        </span>
                      ) : (
                        <span style={{ padding: "4px 10px", backgroundColor: "rgba(148, 163, 184, 0.05)", color: "#64748b", borderRadius: "999px", fontSize: "12px", fontWeight: 500, border: "1px solid rgba(148, 163, 184, 0.1)" }}>
                          No Recording
                        </span>
                      )}

                      {c.insights ? (
                        <span style={{ padding: "4px 10px", backgroundColor: "rgba(16, 185, 129, 0.1)", color: "#34d399", borderRadius: "999px", fontSize: "12px", fontWeight: 500, border: "1px solid rgba(16, 185, 129, 0.2)" }}>
                          Insight Ready
                        </span>
                      ) : (
                        <span style={{ padding: "4px 10px", backgroundColor: "rgba(148, 163, 184, 0.05)", color: "#64748b", borderRadius: "999px", fontSize: "12px", fontWeight: 500, border: "1px solid rgba(148, 163, 184, 0.1)" }}>
                          Processing
                        </span>
                      )}

                      {c.status === 'draft' && (
                        <button
                          onClick={(e) => handleFinish(e, c.id)}
                          style={{
                            padding: "4px 12px",
                            backgroundColor: "rgba(16, 185, 129, 0.15)",
                            color: "#34d399",
                            borderRadius: "6px",
                            fontSize: "12px",
                            fontWeight: 700,
                            border: "1px solid rgba(16, 185, 129, 0.3)",
                            cursor: "pointer",
                            transition: "all 0.2s ease",
                            textTransform: "uppercase",
                            letterSpacing: "0.02em"
                          }}
                          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "rgba(16, 185, 129, 0.25)"; }}
                          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "rgba(16, 185, 129, 0.15)"; }}
                        >
                          End Session
                        </button>
                      )}

                      <span style={{ marginLeft: "8px", color: "#94a3b8", transform: expandedId === c.id ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s ease" }}>
                        ▼
                      </span>
                    </div>
                  </div>

                  {expandedId === c.id && (
                    <div style={{
                      padding: "20px",
                      backgroundColor: "rgba(15, 23, 42, 0.6)",
                      border: "1px solid rgba(148, 163, 184, 0.1)",
                      borderTop: "none",
                      borderRadius: "0 0 12px 12px",
                    }}>
                      <h4 style={{ margin: "0 0 16px 0", fontSize: "14px", fontWeight: 600, color: "#e2e8f0" }}>Transcripts</h4>
                      {c.transcripts && c.transcripts.length > 0 ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                          {[...c.transcripts].sort((a, b) => a.start_time - b.start_time).map((t) => (
                            <div key={t.id} style={{ display: "flex", gap: "12px", fontSize: "14px" }}>
                              <div style={{ color: "#3b82f6", fontWeight: 500, minWidth: "80px" }}>
                                {t.speaker}
                                <div style={{ fontSize: "12px", color: "#94a3b8", fontWeight: "normal" }}>
                                  [{formatTime(t.start_time)}]
                                </div>
                              </div>
                              <div style={{ color: "#f8fafc", lineHeight: "1.5", flex: 1, backgroundColor: "rgba(255,255,255,0.02)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                                {t.text}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ color: "#94a3b8", fontSize: "14px", fontStyle: "italic" }}>
                          No transcripts available for this consultation.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div >
  );
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    document.cookie.includes("logged_in=1")
  );
  const [activeTab, setActiveTab] = useState("dashboard");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [user, setUser] = useState(null);
  const [focusedConsultationId, setFocusedConsultationId] = useState(null);

  useEffect(() => {
    if (isLoggedIn) {
      fetchCurrentUser()
        .then(setUser)
        .catch((err) => {
          if (err.message === "unauthorized") {
            handleLogout();
          }
        });
    }
  }, [isLoggedIn]);

  const handleLogin = () => {
    setIsLoggedIn(true);
    setActiveTab("dashboard");
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (e) {
      console.error(e);
    }
    document.cookie = "logged_in=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    setIsLoggedIn(false);
  };

  if (window.location.pathname === "/mic") {
    return <MicPermission />;
  }

  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div style={{ display: "flex", width: "100%", height: "100vh", overflow: "hidden", margin: 0, padding: 0 }}>
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLogout={handleLogout}
        isCollapsed={!isSidebarOpen}
        toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        user={user}
        onNavigateToConsultation={(id) => { setFocusedConsultationId(id); setActiveTab("consultations"); }}
      />
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", height: "100%" }}>
        {activeTab === "dashboard" && <Dashboard onLogout={handleLogout} />}
        {activeTab === "consultations" && <Consultations onLogout={handleLogout} focusedConsultationId={focusedConsultationId} setFocusedConsultationId={setFocusedConsultationId} />}
        {activeTab === "patients" && <Patients onLogout={handleLogout} onNavigateToConsultation={(id) => { setFocusedConsultationId(id); setActiveTab("consultations"); }} />}
        {activeTab === "ai-insights" && <AIAnalytics />}
        {activeTab === "ask-ai" && <AskAI />}
        {activeTab === "settings" && <Settings onLogout={handleLogout} />}
      </div>
    </div>
  );
}

export default App;
