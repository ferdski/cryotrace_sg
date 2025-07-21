import { Link } from 'react-router-dom';
import './Sidebar.css';
import { NavLink } from 'react-router-dom';

function Sidebar() {
  return (
  
<ul className="sidebar">
  <h1>Menu</h1>
  <li><Link to="/users">Users</Link></li>
  <li><Link to="/containers">List of Shipper units</Link></li>
  <li>
    <span>Manifests</span>
    <ul className="submenu">
      <li><Link to="/manifests/date">By date</Link></li>
      <li><Link to="/manifests/location">By location</Link></li>
      <li><Link to="/manifests/All">All</Link></li>
    </ul>
    <span>Events</span>
    <ul className="submenu">
      <li><NavLink to="/events/pickup-events" activeClassName="active">Pickup Events</NavLink></li>
      <li><NavLink to="/events/dropoff-events" activeClassName="active">Dropoff Events</NavLink></li>
    </ul>
  </li>
</ul>
  );
}

export default Sidebar;
