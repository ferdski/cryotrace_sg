import React, { useEffect, useState } from 'react';
import './UsersList.css';

function UsersList() {
  const [users, setUsers] = useState([]);

  console.log(`ip = `, process.env.REACT_APP_API_BASE_URL);

  console.log(`baseUrl: ${process.env.REACT_APP_API_BASE_URL}`);

  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  const fullUrl = `${baseUrl}/api/users`;

  console.log("Fetching from:", fullUrl); // ✅ Confirm this prints

  useEffect(() => {
    fetch(`${fullUrl}`)
      .then((res) => res.json())
      .then((data) => setUsers(data))
      .catch((err) => console.error('Error fetching users:', err));
  }, []);

  return (
    <div>
      <h2>Users</h2>
      <ul className="users-list">
        {users.map(u => (
          <li key={u.user_id}>
            <span className="username">{u.username}</span>
            <span className="role">{u.role}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default UsersList;
