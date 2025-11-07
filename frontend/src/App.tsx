import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Race from './pages/Race';
import Qualifying from './pages/Qualifying';
import Drivers from './pages/Drivers';
import Constructors from './pages/Constructors';
import Status from './pages/Status';
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
          <Navbar />
          <main className="container">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/race" element={<Race />} />
              <Route path="/qualifying" element={<Qualifying />} />
              <Route path="/drivers" element={<Drivers />} />
              <Route path="/constructors" element={<Constructors />} />
              <Route path="/status" element={<Status />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}
