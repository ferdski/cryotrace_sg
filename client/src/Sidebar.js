import { Link } from 'react-router-dom';
import './Sidebar.css';

function Sidebar() {
  return (
  
<ul className="sidebar">
  <h1>Menu</h1>
  <li><Link to="/users">Users</Link></li>
  <li><Link to="/containers">Containers</Link></li>
  <li>
    <span>Records</span>
    <ul className="submenu">
      <li><Link to="/records/date">By date</Link></li>
      <li><Link to="/records/location">By location</Link></li>
    </ul>
  </li>
</ul>
  );
}

export default Sidebar;
