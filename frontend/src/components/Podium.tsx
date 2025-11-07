import Card from './Card';
import './Podium.css';

interface PodiumEntry {
  position: number;
  name: string;
  team?: string;
  teamColor?: string;
  driverNumber?: number;
  points: number;
  wins?: number;
}

interface PodiumProps {
  entries: PodiumEntry[];
  title?: string;
}

export default function Podium({ entries, title = 'Pódio do Campeonato' }: PodiumProps) {
  const getVariant = (position: number) => {
    switch (position) {
      case 1: return 'gold';
      case 2: return 'silver';
      case 3: return 'bronze';
      default: return 'default';
    }
  };

  const getEmoji = (position: number) => {
    switch (position) {
      case 1: return '🥇';
      case 2: return '🥈';
      case 3: return '🥉';
      default: return '';
    }
  };

  return (
    <div className="podium-section">
      <h3 className="podium-title">{title}</h3>
      <div className="podium-grid">
        {entries.slice(0, 3).map((entry) => (
          <Card key={entry.position} variant={getVariant(entry.position)}>
            <div className="podium-card">
              <div className="podium-emoji">{getEmoji(entry.position)}</div>

              {/* Driver number badge if available */}
              {entry.driverNumber && (
                <div className="podium-number" style={entry.teamColor ? {
                  backgroundColor: entry.teamColor,
                  color: '#fff'
                } : undefined}>
                  {entry.driverNumber}
                </div>
              )}

              <h3 className="podium-name">{entry.name}</h3>

              {entry.team && (
                <div className="podium-team-container">
                  {entry.teamColor && (
                    <div className="team-color-bar" style={{ backgroundColor: entry.teamColor }} />
                  )}
                  <p className="podium-team">{entry.team}</p>
                </div>
              )}

              <p className="podium-points">{entry.points} pts</p>
              {entry.wins !== undefined && (
                <p className="podium-wins">{entry.wins} {entry.wins === 1 ? 'vitória' : 'vitórias'}</p>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
