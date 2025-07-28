import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './Sidebar';
import MainContent from './MainContent';
import './App.css';
import UsersList from './components/UsersList';  // ← import your component
import ContainersList from './components/ContainersList';  // ← import your component
import RecordsByDate from './components/RecordsByDate';
import RecordsByLocation from './components/RecordsByLocation';
import RecordsByManifestId from './components/RecordsByManifestId';
import RecordsAll from './components/RecordsAll';
import PickupEventsPage from './pages/PickupEventsPage';
import DropoffEventsPage from './pages/DropoffEventsPage';
import TransitShipperTableDate from './components/TransitShipperTableDate';
import TransitShipperTableLocation from './components/TransitShipperTableLocation';
import ShipperRoutesPage from './pages/ShipperRoutesPage';
import EvaporationRatePage from './pages/EvaporationRatePage';
import AskAiPage from './pages/AskAI';

const App = () => {
  return (
    <Router>
      <div className="app">
        <Sidebar />
        <div className="content">
          <Routes>
            <Route path="/users" element={<UsersList />} />
            <Route path="/containers" element={<ContainersList />} />
              <Route path="/manifests/date" element={<RecordsByDate />} />
              <Route path="/manifests/location" element={<RecordsByLocation />} />
              <Route path="/manifests/manifestid" element={<RecordsByManifestId />} />
              <Route path="/manifests" element={<RecordsAll/>} />
              <Route path="/transit/date" element={<TransitShipperTableDate/>} />
              <Route path="/transit/location" element={<TransitShipperTableLocation/>} />
              <Route path="/events/pickup-events" element={<PickupEventsPage />} />   
              <Route path="/events/dropoff-events" element={<DropoffEventsPage />} />
              <Route path="/routes/shipper-routes" element={<ShipperRoutesPage />} />
              <Route path="/routes/evaporation-rates" element={<EvaporationRatePage />} />
              <Route path="/routes/ai-chat" element={<AskAiPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
};

export default App;

