import React, { useEffect } from 'react';
import './LandingPage.css';

export default function LandingPage({ onSignInClick }) {
    useEffect(() => {
        // Add scroll listener for revealing elements
        const handleScroll = () => {
            const reveals = document.querySelectorAll('.reveal');
            for (let i = 0; i < reveals.length; i++) {
                const windowHeight = window.innerHeight;
                const elementTop = reveals[i].getBoundingClientRect().top;
                const elementVisible = 100;
                if (elementTop < windowHeight - elementVisible) {
                    reveals[i].classList.add('active');
                }
            }
        };
        window.addEventListener('scroll', handleScroll);
        handleScroll(); // Trigger once on load
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToSection = (id) => {
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
    };

    return (
        <div className="landing-container">
            {/* Navbar */}
            <nav className="landing-nav">
                <div className="nav-logo">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                    </svg>
                    <span>MedAssist</span>
                </div>
                <div className="nav-links">
                    <button onClick={() => scrollToSection('how-it-works')} className="nav-link">How it works</button>
                    <button onClick={() => scrollToSection('benefits')} className="nav-link">Benefits</button>
                    <button onClick={() => scrollToSection('safety')} className="nav-link">Safety</button>
                    <button onClick={onSignInClick} className="nav-cta">Sign In</button>
                </div>
            </nav>

            {/* Hero Section */}
            <header className="hero-section">
                <div className="hero-bg-glow"></div>
                <div className="hero-content">
                    <div className="badge pulse">For Clinicians Only</div>
                    <h1 className="hero-headline text-gradient">
                        AI‑assisted consultation notes for busy doctors
                    </h1>
                    <p className="hero-subheadline">
                        Summarise online consultations, quickly review patient history, and ask natural‑language questions about your own records.
                    </p>
                    <div className="hero-actions">
                        <button className="btn-primary glow-effect" onClick={onSignInClick}>
                            Sign in to dashboard
                        </button>
                        <button className="btn-secondary" onClick={() => scrollToSection('how-it-works')}>
                            Learn how it works
                        </button>
                    </div>
                </div>
            </header>

            {/* How It Works Section */}
            <section id="how-it-works" className="section bg-glass reveal">
                <div className="section-container">
                    <h2 className="section-title">How it works</h2>
                    <div className="steps-grid">
                        <div className="card step-card">
                            <div className="step-icon">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="3" width="20" height="14" rx="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" /></svg>
                            </div>
                            <h3>Step 1 – Connect your consultations</h3>
                            <p>Link your online consultations (for example, Google Meet) so the assistant can securely capture transcripts of each visit.</p>
                        </div>
                        <div className="card step-card">
                            <div className="step-icon">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" /></svg>
                            </div>
                            <h3>Step 2 – We structure the visit</h3>
                            <p>The system organises what was discussed into clear, searchable notes tied to each patient and consultation.</p>
                        </div>
                        <div className="card step-card">
                            <div className="step-icon">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /><path d="M11 8v4" /></svg>
                            </div>
                            <h3>Step 3 – You ask questions</h3>
                            <p>Ask questions like "What were this patient’s main concerns over the last three visits?" and get concise answers based only on their records.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Benefits Section */}
            <section id="benefits" className="section reveal">
                <div className="section-container layout-split">
                    <div className="split-text">
                        <h2 className="section-title text-left">Why doctors use it</h2>
                        <ul className="benefit-list">
                            <li>
                                <div className="check-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg></div>
                                <span>Save time reviewing and documenting consultations.</span>
                            </li>
                            <li>
                                <div className="check-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg></div>
                                <span>Quickly recall what was said in previous visits.</span>
                            </li>

                            <li>
                                <div className="check-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg></div>
                                <span>Receive live AI insights and clinical reminders during the consultation.</span>
                            </li>
                            <li>
                                <div className="check-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg></div>
                                <span>Reduce cognitive load with clear, structured summaries of each consultation.</span>
                            </li>
                        </ul>
                    </div>
                    <div className="split-visual ui-mockup glass-panel">
                        <div className="mockup-header">
                            <div className="dot"></div><div className="dot"></div><div className="dot"></div>
                        </div>
                        <div className="mockup-content">
                            <div className="mockup-title">AI Summary</div>
                            <div className="mockup-line skeleton"></div>
                            <div className="mockup-line skeleton" style={{ width: '90%' }}></div>

                            <div className="live-insight-mockup">
                                <div className="live-badge">Live Insight</div>
                                <div className="mockup-line skeleton" style={{ width: '85%', height: '8px', background: 'rgba(59, 130, 246, 0.4)' }}></div>
                                <div className="mockup-line skeleton" style={{ width: '60%', height: '8px', background: 'rgba(59, 130, 246, 0.4)' }}></div>
                            </div>

                            <div className="mockup-title" style={{ marginTop: '16px' }}>Patient History</div>
                            <div className="history-item">
                                <div className="marker"></div>
                                <div className="mockup-line skeleton" style={{ width: '100%' }}></div>
                            </div>
                            <div className="history-item">
                                <div className="marker"></div>
                                <div className="mockup-line skeleton" style={{ width: '80%' }}></div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Outline */}
            <section className="section bg-glass reveal">
                <div className="section-container">
                    <h2 className="section-title">What the assistant can do</h2>
                    <div className="features-grid">
                        <div className="feature-item">
                            <div className="f-icon">🎤</div>
                            <h4>Live transcription of online consultations.</h4>
                        </div>
                        <div className="feature-item">
                            <div className="f-icon">🔍</div>
                            <h4>“Ask AI” search over patient and consultation data.</h4>
                        </div>
                        <div className="feature-item">
                            <div className="f-icon">📝</div>
                            <h4>Automatic summaries of each consultation for your review.</h4>
                        </div>
                        <div className="feature-item">
                            <div className="f-icon">⚡</div>
                            <h4>Live AI insights generated during the encounter.</h4>
                        </div>

                    </div>
                </div>
            </section>

            {/* Safety & Compliance */}
            <section id="safety" className="section reveal">
                <div className="section-container safety-box">
                    <div className="safety-icon">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
                    </div>
                    <h2 className="section-title">Built with privacy and safety in mind</h2>
                    <div className="safety-bullets">
                        <p><strong>AI outputs summarise existing notes and transcripts;</strong> they do not provide medical advice or diagnoses.</p>
                        <p><strong>Patient data is processed securely</strong> and is not used to train external models.</p>
                        <p><strong>Clinicians remain responsible</strong> for all clinical decisions; the assistant is for support only.</p>
                    </div>

                </div>
            </section>

            {/* About Project */}
            <section className="section section-small bg-glass reveal">
                <div className="section-container about-box">
                    <h2 className="section-title">About this project</h2>
                    <p>This application is a proof‑of‑concept exploring how AI can assist clinicians with consultation documentation and patient history review. It is not a replacement for clinical judgement and is not yet integrated with live electronic medical record systems.</p>
                </div>
            </section>

            {/* Footer */}
            <footer className="landing-footer">
                <div className="footer-content">
                    <div className="footer-brand">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                        </svg>
                        <span>MedAssist</span>
                    </div>
                    <div className="footer-links">
                        <a href="#about">About</a>
                        <a href="#contact">Contact</a>
                        <a href="#privacy">Privacy</a>
                        <a href="#terms">Terms</a>
                    </div>
                </div>
                <div className="footer-bottom">
                    <p>© {new Date().getFullYear()} MedAssist Project. For clinicians only.</p>
                </div>
            </footer>
        </div>
    );
}
