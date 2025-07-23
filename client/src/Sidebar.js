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
      <li><Link to="/manifests/date">By date</Link></li>
      <li><Link to="/manifests/location">By location</Link></li>
    </ul>
    <span>Shippers by Transit</span>
    <ul className="submenu">
      <li><Link to="/transit/date">By date</Link></li>
      <li><Link to="/transit/location">By location</Link></li>
    </ul>    
    <span>Events</span>
    <ul className="submenu">
      <li><NavLink to="/events/pickup-events" activeClassName="active">Create Pickup Event</NavLink></li>
      <li><NavLink to="/events/dropoff-events" activeClassName="active">Create Dropoff Event</NavLink></li>
    </ul>
  </li>
</ul>
  );
}

export default Sidebar;
