import React from 'react';
import { render, screen } from '@testing-library/react';
import AuthCard from './AuthCard';

describe('AuthCard', () => {
  it('renders children inside the card', () => {
    render(<AuthCard><span>Hello World</span></AuthCard>);
    expect(screen.getByText('Hello World')).toBeTruthy();
  });

  it('renders the auth-layout wrapper', () => {
    const { container } = render(<AuthCard><div>content</div></AuthCard>);
    expect(container.querySelector('.auth-layout')).toBeTruthy();
  });

  it('renders the auth-card inner div', () => {
    const { container } = render(<AuthCard><div>content</div></AuthCard>);
    expect(container.querySelector('.auth-card')).toBeTruthy();
  });

  it('auth-card is nested inside auth-layout', () => {
    const { container } = render(<AuthCard><div>content</div></AuthCard>);
    const layout = container.querySelector('.auth-layout');
    expect(layout?.querySelector('.auth-card')).toBeTruthy();
  });

  it('renders multiple children', () => {
    render(
      <AuthCard>
        <span>Child 1</span>
        <span>Child 2</span>
      </AuthCard>
    );
    expect(screen.getByText('Child 1')).toBeTruthy();
    expect(screen.getByText('Child 2')).toBeTruthy();
  });
});
