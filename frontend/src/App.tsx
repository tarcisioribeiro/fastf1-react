import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { NotificationProvider } from './contexts/NotificationContext';
import Sidebar from './components/Sidebar';
import NotificationToast from './components/NotificationToast';
import Home from './pages/Home';
import Race from './pages/Race';
import Qualifying from './pages/Qualifying';
import Sprint from './pages/Sprint';
import Drivers from './pages/Drivers';
import Constructors from './pages/Constructors';
import Status from './pages/Status';
import HistoryRaces from './pages/HistoryRaces';
import HistoryQualifying from './pages/HistoryQualifying';
import HistorySprints from './pages/HistorySprints';
import TeamHistory from './pages/TeamHistory';
import DriverCareer from './pages/DriverCareer';
import AnalyticsStandings from './pages/AnalyticsStandings';
import AnalyticsWeather from './pages/AnalyticsWeather';
import AnalyticsPitStops from './pages/AnalyticsPitStops';
import PredictionsDriver from './pages/PredictionsDriver';
import PredictionsConstructor from './pages/PredictionsConstructor';
import PredictionsPoleDriver from './pages/PredictionsPoleDriver';
import PredictionsPoleConstructor from './pages/PredictionsPoleConstructor';
import PeriodicTasks from './pages/PeriodicTasks';
import DataAudit from './pages/DataAudit';
import './styles/globals.css';

export default function App() {
  return (
    <ThemeProvider>
      <NotificationProvider>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <NotificationToast />
          <div className="app">
            <Sidebar />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/race" element={<Race />} />
                <Route path="/qualifying" element={<Qualifying />} />
                <Route path="/sprint" element={<Sprint />} />
                <Route path="/drivers" element={<Drivers />} />
                <Route path="/constructors" element={<Constructors />} />
                <Route path="/status" element={<Status />} />
                <Route path="/periodic-tasks" element={<PeriodicTasks />} />
                <Route path="/data-audit" element={<DataAudit />} />

                {/* Histórico */}
                <Route path="/history/races" element={<HistoryRaces />} />
                <Route path="/history/qualifying" element={<HistoryQualifying />} />
                <Route path="/history/sprints" element={<HistorySprints />} />
                <Route path="/history/teams" element={<TeamHistory />} />
                <Route path="/history/drivers" element={<DriverCareer />} />

                {/* Analytics */}
                <Route path="/analytics/standings" element={<AnalyticsStandings />} />
                <Route path="/analytics/weather" element={<AnalyticsWeather />} />
                <Route path="/analytics/pitstops" element={<AnalyticsPitStops />} />

                {/* Predictions */}
                <Route path="/predictions/driver" element={<PredictionsDriver />} />
                <Route path="/predictions/constructor" element={<PredictionsConstructor />} />
                <Route path="/predictions/pole-driver" element={<PredictionsPoleDriver />} />
                <Route path="/predictions/pole-constructor" element={<PredictionsPoleConstructor />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </NotificationProvider>
    </ThemeProvider>
  );
}
