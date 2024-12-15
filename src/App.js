import './App.css';
import ChordPage from './pages/chord.js'
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<div></div>} />
        <Route path="/chord/:id" element={<ChordPage/>} />  {/* Dynamic Route */}
      </Routes>
    </Router>
  );
}

export default App;
