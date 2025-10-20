// src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';  

function App() {
  const [tag, setTag]           = useState('');
  const [users, setUsers]       = useState([]);
  const [recs, setRecs]         = useState([]);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  const addUser = async () => {
    if (!tag.trim()) {
      setError('Please enter a user tag');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await axios.post('http://localhost:8000/users/', { tag });
      setUsers(u => Array.from(new Set([...u, tag])));
    } catch (e) {
      setError(e.response?.data.detail || e.message);
    } finally {
      setLoading(false);
    }
  };
  
  const getRecs = async () => {
    if (!tag) {
      setError('Select a user first');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const res = await axios.get(`http://localhost:8000/recommend/${tag}`);
      setRecs(res.data.recommendations || []);
    } catch (e) {
      setError(e.response?.data.detail || e.message);
      setRecs([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1>🎵 Social Sync</h1>

      {/* Add User */}
      <div className="form-row">
        <input
          type="text"
          placeholder="Enter Spotify user tag"
          value={tag}
          onChange={e => setTag(e.target.value)}
          disabled={loading}
        />
        <button onClick={addUser} disabled={loading}>
          Add User
        </button>
      </div>

      {/* Select & Recommend */}
      {users.length > 0 && (
        <div className="form-row">
          <select
            value={tag}
            onChange={e => setTag(e.target.value)}
            disabled={loading}
          >
            <option value="">— Select user —</option>
            {users.map(u => (
              <option key={u} value={u}>{u}</option>
            ))}
          </select>
          <button onClick={getRecs} disabled={loading}>
            Get Recommendations
          </button>
        </div>
      )}

      {/* Feedback */}
      {loading && <p>Loading…</p>}
      {error && <p className="error">{error}</p>}

      {/* Recommendation List */}
      {recs.length > 0 && (
        <ul className="recommendations">
          {recs.map((s, idx) => (
            <li key={idx}>
              <strong>{s.title}</strong> by {s.artist}{' '}
              <a href={s.uri} target="_blank" rel="noreferrer">▶️ Listen</a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;