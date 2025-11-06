import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Race from './pages/Race';
import Qualifying from './pages/Qualifying';
import Drivers from './pages/Drivers';
import Constructors from './pages/Constructors';
import './styles/globals.css';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Navbar />
        <main className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/race" element={<Race />} />
            <Route path="/qualifying" element={<Qualifying />} />
            <Route path="/drivers" element={<Drivers />} />
            <Route path="/constructors" element={<Constructors />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
