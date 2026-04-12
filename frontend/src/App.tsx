import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";
import { ResultPage } from "./pages/ResultPage";
import { SubmittedPage } from "./pages/SubmittedPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/requests/:requestId" element={<SubmittedPage />} />
        <Route path="/requests/:requestId/result" element={<ResultPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
