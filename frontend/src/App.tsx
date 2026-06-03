import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import ErrorBoundary from './components/common/ErrorBoundary';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import { Dashboard, Settings, Register } from './pages';
import InterviewPrep from './pages/InterviewPrep';
import SkillsPage from './pages/SkillsPage';
import RoadmapPage from './pages/RoadmapPage';

function App() {
    return (
        <ErrorBoundary>
            <Routes>
                {/* Public Route */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected Routes */}
                <Route
                    path="/"
                    element={
                        <ProtectedRoute>
                            <Layout />
                        </ProtectedRoute>
                    }
                >
                    <Route index element={<Dashboard />} />

                    <Route path="interview" element={<InterviewPrep />} />
                    <Route path="skills" element={<SkillsPage />} />
                    <Route path="roadmap" element={<RoadmapPage />} />
                    <Route path="settings" element={<Settings />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
            </Routes>
        </ErrorBoundary>
    );
}

export default App;
