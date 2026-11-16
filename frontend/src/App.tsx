import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { LandingPage } from "./pages/LandingPage";
import { ResultPage } from "./pages/ResultPage";
import { SubmittedPage } from "./pages/SubmittedPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route element={<Layout />}>
        <Route path="/requests/:requestId" element={<SubmittedPage />} />
        <Route path="/requests/:requestId/result" element={<ResultPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
