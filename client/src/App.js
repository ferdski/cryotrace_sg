import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './Sidebar';
import MainContent from './MainContent';
import './App.css';
import UsersList from './components/UsersList';  // ← import your component
import ContainersList from './components/ContainersList';  // ← import your component
import RecordsByDate from './components/RecordsByDate';
import RecordsByLocation from './components/RecordsByLocation';

const App = () => {
  return (
    <Router>
      <div className="app">
        <Sidebar />
        <div className="content">
          <Routes>
            <Route path="/users" element={<UsersList />} />
            <Route path="/containers" element={<ContainersList />} />
              <Route path="/records/date" element={<RecordsByDate />} />
              <Route path="/records/location" element={<RecordsByLocation />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
};

export default App;

