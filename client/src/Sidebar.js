import { Link } from 'react-router-dom';
import './Sidebar.css';
import { NavLink } from 'react-router-dom';

function Sidebar() {
  return (
  
<ul className="sidebar">
  <h1>Menu</h1>
  <li><Link to="/users">Users</Link></li>
  <li><Link to="/containers">List of Shipper units</Link></li>
  <li><Link to="/manifests/">Manifests</Link></li>
  
  <li>
    <span>Shippers by Manifest</span>
    <ul className="submenu">
      <li><Link to="/manifests/manifest_id">By Manifest Id</Link></li>      
      <li><Link to="/manifests/date">By date</Link></li>
      <li><Link to="/manifests/location">By Origin</Link></li>
    </ul>
    <span>Shippers by Transit</span>
    <ul className="submenu">
      <li><Link to="/transit/pickup-date">By pickup date</Link></li>
      <li><Link to="/transit/pickup-location">By pickup location</Link></li>
      <li><Link to="/transit/dropoff-date">By dropoff date</Link></li>
      <li><Link to="/transit/dropoff-location">By dropoff location</Link></li>
    </ul>    
    <span>Events</span>
    <ul className="submenu">
      <li><Link to="/create-manifest/">Create Manifest</Link></li>
      <li><NavLink to="/events/pickup-events" activeClassName="active">Create Pickup Event</NavLink></li>
      <li><NavLink to="/events/dropoff-events" activeClassName="active">Create Dropoff Event</NavLink></li>
    </ul>
    <ul>
      <li><NavLink to="/routes/shipper-routes" activeClassName="active">Shipper Routes</NavLink></li>
    </ul>
    <ul>
      <li><NavLink to="/routes/evaporation-rates" activeClassName="active">Evaporation Rates</NavLink></li>
    </ul>
    <ul>
      <li><NavLink to="/routes/ai-chat" activeClassName="active">AI chat</NavLink></li>
    </ul>

  </li>
</ul>
  );
}

export default Sidebar;
