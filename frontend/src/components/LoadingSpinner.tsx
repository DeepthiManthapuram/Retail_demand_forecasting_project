// components/LoadingSpinner.tsx — Reusable loading indicator

interface Props {
  label?: string;
  size?: number;
}

export default function LoadingSpinner({ label = 'Loading…', size = 40 }: Props) {
  return (
    <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:'1rem', padding:'3rem 0' }}>
      <div style={{
        width: size, height: size,
        border: '3px solid rgba(59,130,246,0.2)',
        borderTop: '3px solid #3b82f6',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <p style={{ color:'var(--color-text-muted)', fontSize:'0.9rem' }}>{label}</p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
