import React, { useState } from 'react';

const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setResetToken('');
    try {
      const response = await fetch('http://localhost:8000/api/v1/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to request password reset');
      }
      setMessage(data.message || 'Check your email for the reset link.');
      setResetToken(data.reset_token || '');
    } catch (err: any) {
      setError(err.message || 'Something went wrong.');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-12 p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Forgot Password</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          className="w-full p-2 border rounded mb-4"
        />
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition">Request Reset</button>
      </form>
      {message && <div className="mt-4 text-green-600">{message}</div>}
      {resetToken && (
        <div className="mt-2 text-xs text-gray-500">
          <strong>Demo Token:</strong> {resetToken}
        </div>
      )}
      {error && <div className="mt-4 text-red-600">{error}</div>}
    </div>
  );
};

export default ForgotPassword; 