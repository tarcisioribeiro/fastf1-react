import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import Sidebar from './components/Sidebar';
import Home from './pages/Home';
import Race from './pages/Race';
import Qualifying from './pages/Qualifying';
import Drivers from './pages/Drivers';
import Constructors from './pages/Constructors';
import Status from './pages/Status';
import HistoryRaces from './pages/HistoryRaces';
import HistoryQualifying from './pages/HistoryQualifying';
import HistorySprints from './pages/HistorySprints';
import AnalyticsStandings from './pages/AnalyticsStandings';
import AnalyticsWeather from './pages/AnalyticsWeather';
import AnalyticsPitStops from './pages/AnalyticsPitStops';
import PredictionsDriver from './pages/PredictionsDriver';
import PredictionsConstructor from './pages/PredictionsConstructor';
import './styles/globals.css';

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <div className="app">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/race" element={<Race />} />
              <Route path="/qualifying" element={<Qualifying />} />
              <Route path="/drivers" element={<Drivers />} />
              <Route path="/constructors" element={<Constructors />} />
              <Route path="/status" element={<Status />} />

              {/* Histórico */}
              <Route path="/history/races" element={<HistoryRaces />} />
              <Route path="/history/qualifying" element={<HistoryQualifying />} />
              <Route path="/history/sprints" element={<HistorySprints />} />

              {/* Analytics */}
              <Route path="/analytics/standings" element={<AnalyticsStandings />} />
              <Route path="/analytics/weather" element={<AnalyticsWeather />} />
              <Route path="/analytics/pitstops" element={<AnalyticsPitStops />} />

              {/* Predictions */}
              <Route path="/predictions/driver" element={<PredictionsDriver />} />
              <Route path="/predictions/constructor" element={<PredictionsConstructor />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}
