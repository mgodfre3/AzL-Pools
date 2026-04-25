import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';

function App() {
  const [stats, setStats] = useState(null);
  const [leads, setLeads] = useState([]);

  useEffect(() => {
    fetch('/api/stats').then(r => r.json()).then(setStats);
    fetch('/api/leads?limit=20').then(r => r.json()).then(d => setLeads(d.leads || []));
  }, []);

  return (
    <div style={{ fontFamily: 'system-ui', padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>🏊 AzL Pools Dashboard</h1>

      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
          <StatCard label="Total Properties" value={stats.total_properties} />
          <StatCard label="$1M+ Homes" value={stats.million_plus} />
          <StatCard label="No Pool (Candidates)" value={stats.no_pool_candidates} />
          <StatCard label="Designs Generated" value={stats.designs_generated} />
          <StatCard label="Contacts Enriched" value={stats.contacts_enriched} />
          <StatCard label="Outreach Sent" value={stats.outreach_sent} />
        </div>
      )}

      <h2>Top Leads</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #333' }}>
            <th style={th}>Address</th>
            <th style={th}>City</th>
            <th style={th}>County</th>
            <th style={th}>Value</th>
            <th style={th}>Owner</th>
            <th style={th}>Contact</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
              <td style={td}>{lead.address}</td>
              <td style={td}>{lead.city}</td>
              <td style={td}>{lead.county}</td>
              <td style={td}>${(lead.home_value || 0).toLocaleString()}</td>
              <td style={td}>{lead.owner_name}</td>
              <td style={td}>{lead.phone || lead.email || lead.mailing_address || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div style={{ background: '#f0f4ff', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
      <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{(value || 0).toLocaleString()}</div>
      <div style={{ color: '#666' }}>{label}</div>
    </div>
  );
}

const th = { textAlign: 'left', padding: '0.5rem' };
const td = { padding: '0.5rem' };

createRoot(document.getElementById('root')).render(<App />);
