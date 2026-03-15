import React, { useState, useEffect } from 'react';
import { fetchActiveConsultation, updateConsultationStatus } from './api';

export default function Sidebar({ activeTab, setActiveTab, onLogout, isCollapsed, toggleSidebar, user, onNavigateToConsultation }) {
    const [activeConsultation, setActiveConsultation] = useState(null);

    useEffect(() => {
        const loadActive = async () => {
            try {
                const data = await fetchActiveConsultation();
                setActiveConsultation(data);
            } catch (e) {
                console.error("Failed to load active consultation", e);
            }
        };
        loadActive();
        const interval = setInterval(loadActive, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleEndSession = async (e) => {
        if (e) e.stopPropagation();
        if (!activeConsultation) return;
        if (!window.confirm("Are you sure you want to end this session?")) return;
        try {
            await updateConsultationStatus(activeConsultation.id, "completed");
            setActiveConsultation(null);
            window.dispatchEvent(new Event('consultationStatusChanged'));
        } catch (e) {
            console.error("Failed to end session", e);
        }
    };


    const navItems = [
        {
            id: 'dashboard', label: 'Dashboard', icon: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" /><rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="16" width="7" height="5" rx="1" /></svg>
            )
        },
        {
            id: 'consultations', label: 'Consultations', icon: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" /></svg>
            )
        },
        {
            id: 'patients', label: 'Patients', icon: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
            )
        },
        {
            id: 'ai-insights', label: 'AI Analytics', icon: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /><polyline points="3.27 6.96 12 12.01 20.73 6.96" /><line x1="12" y1="22.08" x2="12" y2="12" /></svg>
            )
        },
        {
            id: 'ask-ai', label: 'Ask AI', icon: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /><path d="M12 7v5" /><path d="M12 16h.01" /></svg>
            )
        }
    ];

    return (
        <div className="glass-panel" style={{
            width: isCollapsed ? '70px' : '230px',
            height: '100vh',
            position: 'sticky',
            top: 0,
            display: 'flex',
            flexDirection: 'column',
            transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            borderRight: '1px solid var(--glass-border)',
            borderTop: 'none',
            borderBottom: 'none',
            borderLeft: 'none',
            borderRadius: 0,
            zIndex: 50,
            overflow: 'hidden',
            flexShrink: 0
        }}>
            {/* Header / Logo */}
            <div style={{
                padding: isCollapsed ? '16px 0' : '20px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: isCollapsed ? 'center' : 'space-between',
                borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                minHeight: '70px',
                boxSizing: 'border-box'
            }}>
                {!isCollapsed && (
                    <div style={{ fontWeight: 700, fontSize: '22px', whiteSpace: 'nowrap', color: 'var(--text-main)' }}>
                        <span className="text-gradient">Med</span> Assist
                    </div>
                )}
                <button
                    onClick={toggleSidebar}
                    style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '6px',
                        borderRadius: '8px',
                    }}
                    className="hover-bg"
                    title="Toggle Sidebar"
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>
            </div>

            {/* Navigation Links */}
            <div className="custom-scrollbar" style={{
                padding: isCollapsed ? '24px 0' : '16px 12px',
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                gap: isCollapsed ? '16px' : '4px',
                overflowY: 'auto'
            }}>
                {navItems.map(item => (
                    <button
                        key={item.id}
                        onClick={() => setActiveTab(item.id)}
                        className="hover-bg"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            padding: isCollapsed ? '12px 0' : '10px 12px',
                            width: '100%',
                            borderRadius: '10px',
                            border: 'none',
                            background: activeTab === item.id ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                            color: activeTab === item.id ? '#60a5fa' : 'var(--text-muted)',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            justifyContent: isCollapsed ? 'center' : 'flex-start',
                        }}
                        title={isCollapsed ? item.label : undefined}
                    >
                        <div style={{ minWidth: isCollapsed ? '32px' : '20px', display: 'flex', justifyContent: 'center' }}>
                            {React.cloneElement(item.icon, { width: isCollapsed ? 24 : 20, height: isCollapsed ? 24 : 20 })}
                        </div>
                        {!isCollapsed && (
                            <span style={{ fontWeight: 500, fontSize: '14px' }}>{item.label}</span>
                        )}
                    </button>
                ))}

                {!isCollapsed && (
                    <div style={{ marginTop: '24px', marginBottom: '6px', padding: '0 12px', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Current Session
                    </div>
                )}

                {activeConsultation ? (
                    <div
                        onClick={() => { if (onNavigateToConsultation) onNavigateToConsultation(activeConsultation.id); }}
                        className="hover-bg"
                        style={{
                            padding: isCollapsed ? '12px' : '12px',
                            margin: isCollapsed ? '0 8px' : '0 4px',
                            borderRadius: '10px',
                            background: 'rgba(59, 130, 246, 0.05)',
                            border: '1px solid rgba(59, 130, 246, 0.1)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '10px',
                            alignItems: isCollapsed ? 'center' : 'stretch',
                            cursor: 'pointer'
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }}></div>
                            {!isCollapsed && (
                                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                    {activeConsultation.title}
                                </div>
                            )}
                        </div>

                        {!isCollapsed && (
                            <button
                                onClick={handleEndSession}
                                style={{
                                    marginTop: '8px',
                                    padding: '8px 12px',
                                    borderRadius: '8px',
                                    background: 'rgba(239, 68, 68, 0.1)',
                                    color: '#ef4444',
                                    border: '1px solid rgba(239, 68, 68, 0.3)',
                                    fontSize: '11px',
                                    fontWeight: 700,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.05em',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease',
                                    width: '100%'
                                }}
                                className="hover-bg-danger"
                            >
                                End Session
                            </button>
                        )}
                    </div>
                ) : (
                    !isCollapsed && (
                        <div style={{ padding: '0 12px', fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            No active session
                        </div>
                    )
                )}

            </div>

            {/* Footer / User Profile & Logout */}
            <div style={{ padding: '12px', borderTop: '1px solid rgba(148, 163, 184, 0.1)', display: 'flex', flexDirection: 'column', gap: isCollapsed ? '20px' : '4px' }}>
                {user && (
                    <div style={{
                        padding: isCollapsed ? '8px 0' : '10px',
                        borderRadius: '10px',
                        background: isCollapsed ? 'transparent' : 'var(--bg-panel)',
                        border: isCollapsed ? 'none' : '1px solid var(--border-main)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: isCollapsed ? 'center' : 'flex-start',
                        gap: '10px',
                        marginBottom: isCollapsed ? '0' : '2px'
                    }} title={isCollapsed ? user.name : undefined}>
                        <div style={{
                            width: isCollapsed ? '32px' : '28px',
                            height: isCollapsed ? '32px' : '28px',
                            borderRadius: '50%',
                            background: 'var(--primary-gradient)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: isCollapsed ? '14px' : '12px',
                            fontWeight: 700,
                            color: 'white',
                            flexShrink: 0
                        }}>
                            {user.name.charAt(0)}
                        </div>
                        {!isCollapsed && (
                            <div style={{ overflow: 'hidden' }}>
                                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user.name}</div>
                                <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'capitalize' }}>{user.role}</div>
                            </div>
                        )}
                    </div>
                )}

                <button
                    onClick={() => setActiveTab('settings')}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: isCollapsed ? '12px 0' : '10px 12px',
                        width: '100%',
                        borderRadius: '10px',
                        border: 'none',
                        background: activeTab === 'settings' ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                        color: activeTab === 'settings' ? '#60a5fa' : 'var(--text-muted)',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        justifyContent: isCollapsed ? 'center' : 'flex-start',
                    }}
                    className="hover-bg"
                    title={isCollapsed ? 'Settings' : undefined}
                >
                    <div style={{ minWidth: isCollapsed ? '32px' : '20px', display: 'flex', justifyContent: 'center' }}>
                        <svg width={isCollapsed ? 24 : 18} height={isCollapsed ? 24 : 18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
                    </div>
                    {!isCollapsed && (
                        <span style={{ fontWeight: 500, fontSize: '14px' }}>Settings</span>
                    )}
                </button>

                <button
                    onClick={onLogout}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: isCollapsed ? '12px 0' : '10px 12px',
                        width: '100%',
                        borderRadius: '10px',
                        border: 'none',
                        background: 'transparent',
                        color: '#ef4444',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        justifyContent: isCollapsed ? 'center' : 'flex-start',
                    }}
                    className="hover-bg-danger"
                    title={isCollapsed ? 'Logout' : undefined}
                >
                    <div style={{ minWidth: isCollapsed ? '32px' : '20px', display: 'flex', justifyContent: 'center' }}>
                        <svg width={isCollapsed ? 24 : 18} height={isCollapsed ? 24 : 18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
                    </div>
                    {!isCollapsed && (
                        <span style={{ fontWeight: 500, fontSize: '14px' }}>Logout</span>
                    )}
                </button>
            </div>
        </div>
    );
}
