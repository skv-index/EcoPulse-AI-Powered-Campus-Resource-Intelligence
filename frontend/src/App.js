import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Buildings from "./pages/Buildings";
import AIInsights from "./pages/AIInsights";
import Issues from "./pages/Issues";
import Reports from "./pages/Reports";
import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/buildings" element={<Buildings />} />
          <Route path="/ai-insights" element={<AIInsights />} />
          <Route path="/issues" element={<Issues />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}
