import { useState, useEffect } from "react";
import { C } from "./styles";

interface LayoutProps {
  children: React.ReactNode;
  active: string;
  setActive: (id: string) => void;
  navItems: { id: string; label: string; icon?: string }[];
}

export default function Layout({ children, active, setActive, navItems }: LayoutProps) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ display: "flex", height: "100vh", background: C.bg, color: C.text, fontFamily: C.font, overflow: "hidden" }}>
      
      {/* Sidebar */}
      <div style={{ 
        width: 240, 
        minWidth: 240, 
        background: C.sidebar, 
        borderRight: `1px solid ${C.cardBorder}`,
        display: "flex",
        flexDirection: "column",
        overflowY: "auto",
        padding: "24px 0",
      }}>
        {/* Logo */}
        <div style={{ padding: "0 20px 24px", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ 
            width: 32, 
            height: 32, 
            borderRadius: 8, 
            background: "linear-gradient(135deg, #6c63ff, #3b82f6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 14,
          }}>◈</div>
          <span style={{ fontWeight: 700, fontSize: 15 }}>SignalIQ</span>
        </div>

        {/* Navegación */}
        {navItems.map((item) => (
          <div
            key={item.id}
            onClick={() => setActive(item.id)}
            style={{
              padding: "10px 20px",
              margin: "2px 12px",
              borderRadius: 8,
              fontSize: 13,
              cursor: "pointer",
              background: active === item.id ? C.accentBg : "transparent",
              color: active === item.id ? C.text : C.muted,
              borderLeft: active === item.id ? `2px solid ${C.accent}` : "2px solid transparent",
              transition: "all 0.15s",
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            {item.icon && <span>{item.icon}</span>}
            <span>{item.label}</span>
          </div>
        ))}

        {/* Footer */}
        <div style={{ marginTop: "auto", padding: "20px", borderTop: `1px solid ${C.cardBorder}`, fontSize: 10, color: C.muted, textAlign: "center" }}>
          <div>{time.toLocaleTimeString("en-US", { hour12: false })}</div>
          <div style={{ marginTop: 4 }}>© 2026 SignalIQ</div>
        </div>
      </div>

      {/* Main */}
      <div style={{ flex: 1, overflow: "auto", display: "flex", flexDirection: "column" }}>
        {children}
      </div>
    </div>
  );
}