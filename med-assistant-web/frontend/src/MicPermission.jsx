// frontend/src/MicPermission.jsx
import { useEffect, useState } from "react";

function MicPermission() {
    const [status, setStatus] = useState("Requesting microphone permission...");
    const [error, setError] = useState("");

    const requestPermission = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            setStatus("Permission granted! You can now close this tab and return to the extension to start capture.");
            // Stop tracks immediately
            stream.getTracks().forEach((track) => track.stop());
        } catch (err) {
            console.error(err);
            setError("Permission denied. Please click the button below to try again, or check your browser settings.");
            setStatus("");
        }
    };

    useEffect(() => {
        requestPermission();
    }, []);

    return (
        <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
            width: "100%",
            backgroundColor: "#0f172a",
            color: "#f8fafc",
            fontFamily: "system-ui, sans-serif",
            textAlign: "center"
        }}>
            <div style={{
                backgroundColor: "#1e293b",
                padding: "2rem",
                borderRadius: "12px",
                boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                maxWidth: "400px",
                width: "90%"
            }}>
                <h2 style={{ margin: "0 0 1rem 0", fontSize: "1.5rem", fontWeight: 600 }}>
                    Med Consult Assistant
                </h2>
                <p style={{ color: "#cbd5e1", marginBottom: "1.5rem", lineHeight: "1.5" }}>
                    The Chrome extension needs microphone access to mix your voice with the consultation audio.
                </p>

                {status && (
                    <div style={{ color: "#4ade80", marginBottom: "1rem", fontWeight: 500 }}>
                        {status}
                    </div>
                )}

                {error && (
                    <div style={{ color: "#ef4444", marginBottom: "1rem", fontWeight: 500 }}>
                        {error}
                    </div>
                )}

                <button
                    onClick={requestPermission}
                    style={{
                        backgroundColor: "#3b82f6",
                        color: "white",
                        border: "none",
                        padding: "0.75rem 1.5rem",
                        borderRadius: "8px",
                        fontSize: "1rem",
                        fontWeight: 600,
                        cursor: "pointer",
                        transition: "background-color 0.2s"
                    }}
                    onMouseOver={(e) => (e.target.style.backgroundColor = "#2563eb")}
                    onMouseOut={(e) => (e.target.style.backgroundColor = "#3b82f6")}
                >
                    Grant Microphone Access
                </button>
            </div>
        </div>
    );
}

export default MicPermission;
