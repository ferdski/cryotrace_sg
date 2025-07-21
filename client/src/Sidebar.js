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
    <span>Records</span>
    <ul className="submenu">
      <li><Link to="/records/date">By date</Link></li>
      <li><Link to="/records/location">By location</Link></li>
      <li><Link to="/records/All">All</Link></li>
      <li><NavLink to="/pickup-events" activeClassName="active">Pickup Events</NavLink></li>
      <li><NavLink to="/dropoff-events" activeClassName="active">Dropoff Events</NavLink></li>
    </ul>
  </li>
</ul>
  );
}

export default Sidebar;
