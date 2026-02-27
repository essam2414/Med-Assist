import React from 'react';

export default function Sidebar({ activeTab, setActiveTab, onLogout, isCollapsed, toggleSidebar }) {
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
            id: 'settings', label: 'Settings', icon: (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
            )
        }
    ];

    return (
        <div className="glass-panel" style={{
            width: isCollapsed ? '80px' : '260px',
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
                padding: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: isCollapsed ? 'center' : 'space-between',
                borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                minHeight: '80px',
                boxSizing: 'border-box'
            }}>
                {!isCollapsed && (
                    <div style={{ fontWeight: 700, fontSize: '20px', whiteSpace: 'nowrap' }}>
                        <span className="text-gradient">Med</span> Assistant
                    </div>
                )}
                <button
                    onClick={toggleSidebar}
                    style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#94a3b8',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '8px',
                        borderRadius: '8px',
                    }}
                    className="hover-bg"
                    title="Toggle Sidebar"
                >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>
            </div>

            {/* Navigation Links */}
            <div style={{ padding: '24px 16px', flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {navItems.map(item => (
                    <button
                        key={item.id}
                        onClick={() => setActiveTab(item.id)}
                        className="hover-bg"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '16px',
                            padding: '12px 16px',
                            width: '100%',
                            borderRadius: '12px',
                            border: 'none',
                            background: activeTab === item.id ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                            color: activeTab === item.id ? '#60a5fa' : '#94a3b8',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            justifyContent: isCollapsed ? 'center' : 'flex-start',
                        }}
                        title={isCollapsed ? item.label : undefined}
                    >
                        <div style={{ minWidth: '24px', display: 'flex', justifyContent: 'center' }}>
                            {item.icon}
                        </div>
                        {!isCollapsed && (
                            <span style={{ fontWeight: 500, fontSize: '15px' }}>{item.label}</span>
                        )}
                    </button>
                ))}
            </div>

            {/* Footer / Logout */}
            <div style={{ padding: '24px 16px', borderTop: '1px solid rgba(148, 163, 184, 0.1)' }}>
                <button
                    onClick={onLogout}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '16px',
                        padding: '12px 16px',
                        width: '100%',
                        borderRadius: '12px',
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
                    <div style={{ minWidth: '24px', display: 'flex', justifyContent: 'center' }}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
                    </div>
                    {!isCollapsed && (
                        <span style={{ fontWeight: 500, fontSize: '15px' }}>Logout</span>
                    )}
                </button>
            </div>
        </div>
    );
}
