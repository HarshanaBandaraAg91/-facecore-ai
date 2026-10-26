import React from 'react';

interface BadgeProps {
  variant?: 'crimson' | 'emerald' | 'amber' | 'slate';
  children: React.ReactNode;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'slate',
  children,
  icon,
}) => {
  return (
    <span className={`badge-tag ${variant}`}>
      {icon && <span style={{ display: 'inline-flex' }}>{icon}</span>}
      {children}
    </span>
  );
};
