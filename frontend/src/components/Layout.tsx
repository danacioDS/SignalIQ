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
  const [isMobile, setIsMobile] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => {
      clearInterval(timer);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // ── Sidebar (Desktop) ──
  const Sidebar = () => (
    <div style={{ 
      width: 240, 
      minWidth: 240, 
      background: C.sidebar, 
      borderRight: `1px solid ${C.cardBorder}`,
      display: "flex",
      flexDirection: "column",
      overflowY: "auto",
      padding: "24px 0",
      height: "100vh",
      position: "sticky",
      top: 0,
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
          onClick={() => {
            setActive(item.id);
            if (isMobile) setMenuOpen(false);
          }}
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
  );

  // ── Header Mobile ──
  const MobileHeader = () => (
    <div style={{
      background: C.sidebar,
      borderBottom: `1px solid ${C.cardBorder}`,
      padding: "12px 16px",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      position: "sticky",
      top: 0,
      zIndex: 100,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ 
          width: 28, 
          height: 28, 
          borderRadius: 8, 
          background: "linear-gradient(135deg, #6c63ff, #3b82f6)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 12,
        }}>◈</div>
        <span style={{ fontWeight: 700, fontSize: 16 }}>SignalIQ</span>
      </div>
      <button 
        onClick={() => setMenuOpen(!menuOpen)}
        style={{ 
          background: "none", 
          border: "none", 
          color: C.text, 
          fontSize: 24,
          cursor: "pointer",
          padding: "4px 8px",
        }}
      >
        {menuOpen ? "✕" : "☰"}
      </button>
    </div>
  );

  // ── Menú Mobile ──
  const MobileMenu = () => (
    <div style={{
      position: "fixed",
      top: 60,
      left: 0,
      right: 0,
      background: C.sidebar,
      borderBottom: `1px solid ${C.cardBorder}`,
      padding: "8px 0",
      zIndex: 99,
      maxHeight: "calc(100vh - 60px)",
      overflowY: "auto",
    }}>
      {navItems.map((item) => (
        <div
          key={item.id}
          onClick={() => {
            setActive(item.id);
            setMenuOpen(false);
          }}
          style={{
            padding: "12px 20px",
            fontSize: 13,
            cursor: "pointer",
            background: active === item.id ? C.accentBg : "transparent",
            color: active === item.id ? C.text : C.muted,
            borderLeft: active === item.id ? `3px solid ${C.accent}` : "3px solid transparent",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          {item.icon && <span>{item.icon}</span>}
          <span>{item.label}</span>
        </div>
      ))}
      <div style={{ padding: "16px 20px", borderTop: `1px solid ${C.cardBorder}`, fontSize: 10, color: C.muted, textAlign: "center" }}>
        {time.toLocaleTimeString("en-US", { hour12: false })} · © 2026 SignalIQ
      </div>
    </div>
  );

  // ── Render ──
  return (
    <div style={{ 
      display: "flex", 
      flexDirection: isMobile ? "column" : "row",
      height: "100vh", 
      background: C.bg, 
      color: C.text, 
      fontFamily: C.font, 
      overflow: "hidden" 
    }}>
      {isMobile ? (
        // ── Mobile ──
        <>
          <MobileHeader />
          {menuOpen && <MobileMenu />}
          <div style={{ flex: 1, overflow: "auto" }}>
            {children}
          </div>
        </>
      ) : (
        // ── Desktop ──
        <>
          <Sidebar />
          <div style={{ flex: 1, overflow: "auto" }}>
            {children}
          </div>
        </>
      )}
    </div>
  );
}