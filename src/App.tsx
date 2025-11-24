import { useState } from "react";
import { HomePage } from "./components/HomePage";
import { TranslationMode } from "./components/TranslationMode";
import { PracticeMode } from "./components/PracticeMode";
import { ProgressDashboard } from "./components/ProgressDashboard";
import { BottomTabBar } from "./components/BottomTabBar";

export default function App() {
  const [activeTab, setActiveTab] = useState<
    "home" | "translate" | "practice" | "progress"
  >("home");

  console.log("App component rendering, activeTab:", activeTab);

  return (
    <div className="size-full bg-white max-w-md mx-auto relative overflow-hidden">
      {/* Main Content */}
      <div className="h-full overflow-hidden">
        {activeTab === "home" && (
          <HomePage onNavigate={(tab) => setActiveTab(tab)} />
        )}

        {activeTab === "translate" && (
          <TranslationMode onBack={() => setActiveTab("home")} />
        )}

        {activeTab === "practice" && (
          <PracticeMode onBack={() => setActiveTab("home")} />
        )}

        {activeTab === "progress" && <ProgressDashboard />}
      </div>

      {/* Bottom Navigation */}
      <BottomTabBar activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
}
