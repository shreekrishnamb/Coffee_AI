import React, { useState } from 'react';

const ResetPassword: React.FC = () => {
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      const response = await fetch('http://localhost:8000/api/v1/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to reset password');
      }
      setMessage(data.message || 'Password has been reset. You can now log in.');
    } catch (err: any) {
      setError(err.message || 'Something went wrong.');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-12 p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Reset Password</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Enter your reset token"
          value={token}
          onChange={e => setToken(e.target.value)}
          required
          className="w-full p-2 border rounded mb-4"
        />
        <input
          type="password"
          placeholder="Enter new password"
          value={newPassword}
          onChange={e => setNewPassword(e.target.value)}
          required
          className="w-full p-2 border rounded mb-4"
        />
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition">Reset Password</button>
      </form>
      {message && <div className="mt-4 text-green-600">{message}</div>}
      {error && <div className="mt-4 text-red-600">{error}</div>}
    </div>
  );
};

export default ResetPassword; 