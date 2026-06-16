import { useState } from "react";
import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import EconomicFoundation from "./components/EconomicFoundation";
import Methodology from "./components/Methodology";
import DataRecovery from "./components/DataRecovery";
import TechStack from "./components/TechStack";
import Architecture from "./components/Architecture";
import About from "./components/About";

const navItems = [
  { id: "dashboard", label: "📊 Dashboard" },
  { id: "foundation", label: "📚 Economic Foundation" },
  { id: "statistics", label: "📈 Methodology" },
  { id: "data", label: "📡 Data Recovery" },
  { id: "tech", label: "⚙️ Tech Stack" },
  { id: "architecture", label: "🏗️ Architecture" },
  { id: "about", label: "📖 About" },
];

const components: Record<string, React.ComponentType> = {
  dashboard: Dashboard,
  foundation: EconomicFoundation,
  statistics: Methodology,
  data: DataRecovery,
  tech: TechStack,
  architecture: Architecture,
  about: About,
};

export default function App() {
  const [active, setActive] = useState("dashboard");
  const ActiveComponent = components[active] || Dashboard;

  return (
    <Layout active={active} setActive={setActive} navItems={navItems}>
      <ActiveComponent />
    </Layout>
  );
}