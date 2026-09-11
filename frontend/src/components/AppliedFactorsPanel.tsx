import './AppliedFactorsPanel.css';

export interface AppliedFactor {
  key: string;
  label: string;
  effect: 'positivo' | 'negativo' | 'incerteza' | 'neutro';
  positionDelta: number;
  probMultiplier: number;
  uncertaintyDelta: number;
  explanation: string;
  enabled: boolean;
}

const FACTOR_ICON: Record<string, string> = {
  regulation: '🚩',
  car_update: '🔧',
  weather: '🌤️',
  strategy: '⏱️',
  current_form: '📈',
};

const EFFECT_META: Record<AppliedFactor['effect'], { label: string; color: string; icon: string }> = {
  positivo: { label: 'Favorável', color: 'var(--status-success, #16a34a)', icon: '📈' },
  negativo: { label: 'Desfavorável', color: 'var(--status-error, #dc2626)', icon: '⚠️' },
  incerteza: { label: 'Mais incerteza', color: 'var(--status-warning, #d97706)', icon: '❓' },
  neutro: { label: 'Neutro', color: 'var(--text-secondary)', icon: 'ℹ️' },
};

interface Props {
  factors: AppliedFactor[];
}

export default function AppliedFactorsPanel({ factors }: Props) {
  if (!factors || factors.length === 0) return null;

  return (
    <div className="applied-factors">
      <h3>
        🧭 Fatores Contextuais Considerados
      </h3>
      <p className="applied-factors-hint">
        Ajustes aplicados sobre a previsão estatística. Fatores desativados nos parâmetros
        aparecem apenas como referência.
      </p>
      <div className="applied-factors-grid">
        {factors.map((f) => {
          const meta = EFFECT_META[f.effect];
          return (
            <div
              key={f.key}
              className={`applied-factor-card${f.enabled ? '' : ' is-disabled'}`}
            >
              <div className="applied-factor-head">
                <span className="applied-factor-title">
                  {FACTOR_ICON[f.key] || 'ℹ️'} {f.label}
                </span>
                <span className="applied-factor-badge" style={{ color: meta.color }}>
                  {meta.icon} {f.enabled ? meta.label : 'Desativado'}
                </span>
              </div>
              <p className="applied-factor-text">{f.explanation}</p>
              {f.enabled && (f.positionDelta !== 0 || f.uncertaintyDelta > 0) && (
                <div className="applied-factor-metrics">
                  {f.positionDelta !== 0 && (
                    <span>
                      Posição: {f.positionDelta > 0 ? '+' : ''}
                      {f.positionDelta.toFixed(1)}
                    </span>
                  )}
                  {f.uncertaintyDelta > 0 && (
                    <span>Incerteza: +{f.uncertaintyDelta.toFixed(1)}</span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
