import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Header } from "./components/Header";
import { Dashboard } from "./pages/Dashboard";
import { AnalysisPage } from "./pages/AnalysisPage";

export function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analysis/:id" element={<AnalysisPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
