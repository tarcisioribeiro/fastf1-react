import { useEffect, useState } from 'react';
import './LoadingWithRetry.css';

interface LoadingWithRetryProps {
  message?: string;
  hint?: string;
}

export default function LoadingWithRetry({
  message = 'Carregando dados...',
  hint = 'A aplicação está tentando se conectar à API. Por favor, aguarde.'
}: LoadingWithRetryProps) {
  const [dots, setDots] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '' : prev + '.'));
    }, 500);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const retryInterval = setInterval(() => {
      setRetryCount((prev) => prev + 1);
    }, 2000);

    return () => clearInterval(retryInterval);
  }, []);

  return (
    <div className="loading-retry-container">
      <div className="loading-spinner"></div>
      <h2 className="loading-title">
        {message}
        {dots}
      </h2>
      <p className="loading-hint">{hint}</p>
      {retryCount > 3 && (
        <div className="retry-info">
          <p className="retry-message">
            Ainda conectando... A API pode estar processando dados ou iniciando.
          </p>
          <p className="retry-details">
            Tentativas: {retryCount} • A aplicação continuará tentando automaticamente
          </p>
        </div>
      )}
      <div className="loading-tips">
        <p>💡 Dica: Os dados da FastF1 API podem levar até 2 minutos para carregar na primeira vez</p>
      </div>
    </div>
  );
}
