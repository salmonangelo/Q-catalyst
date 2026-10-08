import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import React from 'react';
import App from '../App';

describe('Q-Catalyst React Application', () => {
  it('renders brand header and title', async () => {
    render(<App />);
    const brandElements = screen.getAllByText(/Q-CATALYST/i);
    expect(brandElements.length).toBeGreaterThan(0);
    const titleElements = screen.getAllByText(/Mechanism-Aware Quantum–AI Triage for PETase Engineering/i);
    expect(titleElements.length).toBeGreaterThan(0);
  });

  it('renders navigation links across all primary views', async () => {
    render(<App />);
    expect(screen.getByText('Candidate Triage')).toBeInTheDocument();
    expect(screen.getByText('Candidate Deep Dive')).toBeInTheDocument();
    expect(screen.getByText('Quantum Lab')).toBeInTheDocument();
    expect(screen.getByText('Structural Mechanism')).toBeInTheDocument();
    expect(screen.getByText('Pipeline')).toBeInTheDocument();
    expect(screen.getByText('Provenance')).toBeInTheDocument();
  });
});
