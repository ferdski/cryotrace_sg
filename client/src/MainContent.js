import React, { useEffect, useState } from 'react';

const MainContent = ({ dataUrl }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!dataUrl) return;

    fetch(dataUrl)
      .then(res => res.json())  // Make sure the response is parsed as JSON
      .then(json => {
        console.log("Fetched data:", json); 
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch data:', err);
        setLoading(false);
      });
  }, [dataUrl]);

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <h2>Users</h2>
      {data.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Role</th>
              <th>Email</th>
            </tr>
          </thead>
          <tbody>
            {data.map(user => (
              <tr key={user.user_id}>
                <td>{user.username}</td>
                <td>{user.role}</td>
                <td>{user.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No users found.</p>
      )}
    </div>
  );
};

export default MainContent;
