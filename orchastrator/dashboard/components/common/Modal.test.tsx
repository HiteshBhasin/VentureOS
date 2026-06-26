import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Modal } from './Modal';

describe('Modal', () => {
  it('renders nothing when closed', () => {
    const { container } = render(
      <Modal isOpen={false} title="Hidden" onClose={() => {}}>
        content
      </Modal>
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('renders title and children when open', () => {
    render(
      <Modal isOpen title="My Title" onClose={() => {}}>
        <span>body content</span>
      </Modal>
    );
    expect(screen.getByText('My Title')).toBeInTheDocument();
    expect(screen.getByText('body content')).toBeInTheDocument();
  });

  it('calls onClose when the close button is clicked', () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen title="My Title" onClose={onClose}>
        body
      </Modal>
    );
    screen.getByLabelText('Close').click();
    expect(onClose).toHaveBeenCalledOnce();
  });
});
