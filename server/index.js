// /server/index.js
const path = require('path');
require('dotenv').config({
  path: path.resolve(__dirname, '.env')
});
const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const mysql = require('mysql2/promise');


const app = express();

debugger;
console.log("🚀 Server started");

app.use(express.json());

app.use(cors({
  origin: `${process.env.CORS_USE_REACT_FRONT_END}` // Match your React app's URL
}));


console.log('DB_USER is:', process.env.DB_USER);
// MySQL connection pool
const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  port: process.env.DB_PORT || 3306,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});


// API route to get all users
app.get('/api/users', async (req, res) => {
  try {

    const [rows, fields] = await pool.query('SELECT * FROM Users ORDER BY user_id');
    console.log("data from users query: ",rows);

    res.json(rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Database error' });
  }
});

app.get('/api/records', async (req, res) => {
  const filter = req.query.filter;
  const containerId = req.query.containerId?.trim(); // <-- sanitize input

  console.log("Filter type:", filter);
  console.log("Container ID:", `"${containerId}"`); // show quotes to catch trailing spaces

  let query = '';
  let params = [];

  if (filter === 'date') {
    query = 'SELECT * FROM Shipment_Records WHERE container_id = ? ORDER BY timestamp';
    params = [containerId];
  } else if (filter === 'location') {
    query = 'SELECT * FROM Shipment_Records WHERE container_id = ? ORDER BY location';
    params = [containerId];
  } else {
    return res.status(400).json({ error: 'Invalid filter type' });
  }

  console.log("Final SQL:", query);
  console.log("Params:", params);

  try {
    const [rows] = await pool.query(query, params);
    console.log("✅ Query results:", rows);
    res.json(rows);
  } catch (err) {
    console.error('❌ Database error:', err);
    res.status(500).json({ error: 'Database error' });
  }
});

app.get('/api/containers', async (req, res) => {
  try {
    const [rows, fields] = await pool.query('SELECT * FROM Containers ORDER BY container_id');
    console.log("data from records query:", rows);
    res.json(rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Database error' });
  }
});

// add post here to receive data
app.post('/api/record', async (req, res) => {
  try {
    const {
      record_id,
      container_id,
      timestamp,
      weight,
      ship_or_receive,
      location,
      notes
    } = req.body;

    // Validate required fields
    if (!record_id || !container_id || !timestamp || !weight || !ship_or_receive || !location) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const query = `
      INSERT INTO Shipment_Records 
      (record_id, container_id, timestamp, weight, ship_or_receive, location, notes)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `;

    const params = [
      record_id,
      container_id,
      timestamp,
      weight,
      ship_or_receive,
      location,
      notes || null // notes is optional
    ];

    const [result] = await pool.query(query, params);
    
    console.log("✅ Record created successfully:", result);
    res.status(201).json({ 
      message: 'Record created successfully',
      record_id: record_id
    });

  } catch (err) {
    console.error('❌ Error creating record:', err);
    res.status(500).json({ error: 'Database error' });
  }
});

// CalculateEvapRate here

// Start the server
const PORT = 3001;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
