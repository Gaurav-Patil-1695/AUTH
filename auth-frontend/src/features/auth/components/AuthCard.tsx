import React from 'react';

interface AuthCardProps {
  children: React.ReactNode;
}

function AuthCard({ children }: AuthCardProps): JSX.Element {
  return (
    <div className="auth-layout">
      <div className="auth-card">
        {children}
      </div>
    </div>
  );
}

export default AuthCard;
