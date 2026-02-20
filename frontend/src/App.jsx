import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import AdminSchedules from './pages/AdminSchedules';
import AdminPapers from './pages/AdminPapers';
import AdminPaperDetails from './pages/AdminPaperDetails';
import AdminCandidates from './pages/AdminCandidates';
import AdminGhostMode from './pages/AdminGhostMode';
import CandidateDashboard from './pages/CandidateDashboard';
import CandidateHistory from './pages/CandidateHistory';
import InterviewSession from './pages/InterviewSession';
import InterviewResults from './pages/InterviewResults';
import './index.css';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/interview/:token" element={<InterviewSession />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/login" replace />} />
          <Route path="admin" element={<AdminDashboard />} />
          <Route path="admin/schedules" element={<AdminSchedules />} />
          <Route path="admin/papers" element={<AdminPapers />} />
          <Route path="admin/papers/:id" element={<AdminPaperDetails />} />
          <Route path="admin/candidates" element={<AdminCandidates />} />
          <Route path="admin/ghost/:id" element={<AdminGhostMode />} />
          <Route path="candidate" element={<CandidateDashboard />} />
          <Route path="candidate/history" element={<CandidateHistory />} />
          <Route path="interview/result/:id" element={<InterviewResults />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App;
