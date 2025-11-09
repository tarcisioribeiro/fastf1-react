import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Hero from '../components/Hero';
import Card from '../components/Card';
import { f1Api } from '../services/api';
import { formatDateBR } from '../utils/dateFormatter';
import './Home.css';

export default function Home() {
  const [leaderDriver, setLeaderDriver] = useState<any>(null);
  const [leaderConstructor, setLeaderConstructor] = useState<any>(null);
  const [latestRace, setLatestRace] = useState<any>(null);
  const [latestQualifying, setLatestQualifying] = useState<any>(null);
  const [latestSprint, setLatestSprint] = useState<any>(null);
  const [topDrivers, setTopDrivers] = useState<any[]>([]);
  const [topConstructors, setTopConstructors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    loadHomeData();
    const interval = setInterval(loadHomeData, 300000); // Atualizar a cada 5 minutos
    return () => clearInterval(interval);
  }, []);

  const loadHomeData = async () => {
    try {
      setLoading(true);

      // Carregar dados em paralelo
      const [drivers, constructors, race, qualifying, sprint, status] = await Promise.all([
        f1Api.getDriverStandings().catch(() => []),
        f1Api.getConstructorStandings().catch(() => []),
        f1Api.getLatestRace().catch(() => null),
        f1Api.getLatestQualifying().catch(() => null),
        f1Api.getLatestSprint().catch(() => null),
        f1Api.getStatus().catch(() => null),
      ]);

      if (drivers.length > 0) {
        setLeaderDriver(drivers[0]);
        setTopDrivers(drivers.slice(0, 5)); // Top 5
      }
      if (constructors.length > 0) {
        setLeaderConstructor(constructors[0]);
        setTopConstructors(constructors.slice(0, 5)); // Top 5
      }
      if (race) setLatestRace(race);
      if (qualifying) setLatestQualifying(qualifying);
      if (sprint) setLatestSprint(sprint);
      if (status) setSystemStatus(status);
    } catch (error) {
      console.error('Erro ao carregar dados da home:', error);
    } finally {
      setLoading(false);
    }
  };

  const sections = [
    {
      title: '🏆 Última Corrida',
      description: latestRace
        ? `${latestRace.raceInfo.eventName} - ${latestRace.raceInfo.location}`
        : 'Confira os resultados da última corrida disponível',
      link: '/race',
      badge: latestRace ? formatDateBR(latestRace.raceInfo.date) : null,
    },
    {
      title: '⏱️ Qualificação',
      description: latestQualifying
        ? `${latestQualifying.raceInfo.eventName} - ${latestQualifying.raceInfo.location}`
        : 'Veja os tempos de qualificação e o grid de largada',
      link: '/qualifying',
      badge: latestQualifying ? formatDateBR(latestQualifying.raceInfo.date) : null,
    },
    {
      title: '🚀 Sprint',
      description: latestSprint
        ? `${latestSprint.raceInfo.eventName} - ${latestSprint.raceInfo.location}`
        : 'Resultados do último sprint disponível',
      link: '/sprint',
      badge: latestSprint ? formatDateBR(latestSprint.raceInfo.date) : null,
    },
    {
      title: '👤 Pilotos',
      description: leaderDriver
        ? `Líder: ${leaderDriver.name} (${leaderDriver.points} pts)`
        : 'Classificação completa do campeonato de pilotos',
      link: '/drivers',
      badge: leaderDriver ? `${topDrivers.length} pilotos` : null,
    },
    {
      title: '🏁 Construtores',
      description: leaderConstructor
        ? `Líder: ${leaderConstructor.team} (${leaderConstructor.points} pts)`
        : 'Classificação das equipes no campeonato de construtores',
      link: '/constructors',
      badge: leaderConstructor ? `${topConstructors.length} equipes` : null,
    },
    {
      title: '📚 Histórico de Corridas',
      description: 'Explore todas as corridas históricas com filtros avançados',
      link: '/history/races',
      badge: systemStatus ? `${systemStatus.stats.database.race_results} resultados` : null,
    },
    {
      title: '⏱️ Histórico de Qualificações',
      description: 'Veja os resultados de todas as qualificações',
      link: '/history/qualifying',
      badge: systemStatus ? `${systemStatus.stats.database.qualifying_results} resultados` : null,
    },
    {
      title: '🚀 Histórico de Sprints',
      description: 'Confira todos os sprints realizados',
      link: '/history/sprints',
      badge: systemStatus ? `${systemStatus.stats.database.sprint_results} resultados` : null,
    },
    {
      title: '⚙️ Status do Sistema',
      description: 'Verifique o status do banco de dados e tarefas de coleta',
      link: '/status',
      badge: systemStatus ? `${systemStatus.stats.database.sessions} sessões` : null,
    },
  ];

  return (
    <div className="home">
      <Hero />

      {!loading && (leaderDriver || leaderConstructor) && (
        <>

          {/* Top 5 Pilotos */}
          {topDrivers.length > 0 && (
            <div className="home-section">
              <h2 className="section-title">🏆 Top 5 Pilotos</h2>
              <div className="standings-mini">
                {topDrivers.map((driver, index) => (
                  <div key={driver.code} className="standing-item">
                    <div className="standing-position">{index + 1}</div>
                    <div className="standing-info">
                      <div className="standing-name">{driver.name}</div>
                      <div className="standing-team" style={{ color: 'var(--text-secondary)' }}>
                        {driver.team}
                      </div>
                    </div>
                    <div className="standing-stats">
                      <div className="standing-points">{driver.points} pts</div>
                      <div className="standing-wins">{driver.wins} vitórias</div>
                    </div>
                  </div>
                ))}
              </div>
              <Link to="/drivers" className="section-link">Ver todos os pilotos →</Link>
            </div>
          )}

          {/* Top 5 Construtores */}
          {topConstructors.length > 0 && (
            <div className="home-section">
              <h2 className="section-title">🏁 Top 5 Construtores</h2>
              <div className="standings-mini">
                {topConstructors.map((constructor, index) => (
                  <div key={constructor.team} className="standing-item">
                    <div className="standing-position">{index + 1}</div>
                    <div className="standing-info">
                      <div className="standing-name">{constructor.team}</div>
                    </div>
                    <div className="standing-stats">
                      <div className="standing-points">{constructor.points} pts</div>
                      <div className="standing-wins">{constructor.wins} vitórias</div>
                    </div>
                  </div>
                ))}
              </div>
              <Link to="/constructors" className="section-link">Ver todas as equipes →</Link>
            </div>
          )}

          {/* Últimas Corridas */}
          {(latestRace || latestQualifying || latestSprint) && (
            <div className="home-section">
              <h2 className="section-title">📅 Últimas Sessões</h2>
              <div className="recent-sessions">
                {latestRace && (
                  <Link to="/race" className="session-card">
                    <div className="session-type">🏆 Corrida</div>
                    <div className="session-name">{latestRace.raceInfo.eventName}</div>
                    <div className="session-location">{latestRace.raceInfo.location}</div>
                    <div className="session-date">{formatDateBR(latestRace.raceInfo.date)}</div>
                    {latestRace.results && latestRace.results[0] && (
                      <div className="session-winner">
                        Vencedor: {latestRace.results[0].driver}
                      </div>
                    )}
                  </Link>
                )}
                {latestQualifying && (
                  <Link to="/qualifying" className="session-card">
                    <div className="session-type">⏱️ Qualificação</div>
                    <div className="session-name">{latestQualifying.raceInfo.eventName}</div>
                    <div className="session-location">{latestQualifying.raceInfo.location}</div>
                    <div className="session-date">{formatDateBR(latestQualifying.raceInfo.date)}</div>
                    {latestQualifying.results && latestQualifying.results[0] && (
                      <div className="session-winner">
                        Pole: {latestQualifying.results[0].driver}
                      </div>
                    )}
                  </Link>
                )}
                {latestSprint && (
                  <Link to="/sprint" className="session-card">
                    <div className="session-type">🚀 Sprint</div>
                    <div className="session-name">{latestSprint.raceInfo.eventName}</div>
                    <div className="session-location">{latestSprint.raceInfo.location}</div>
                    <div className="session-date">{formatDateBR(latestSprint.raceInfo.date)}</div>
                    {latestSprint.results && latestSprint.results[0] && (
                      <div className="session-winner">
                        Vencedor: {latestSprint.results[0].driver}
                      </div>
                    )}
                  </Link>
                )}
              </div>
            </div>
          )}

          {/* Estatísticas do Sistema */}
          {systemStatus && (
            <div className="home-section">
              <h2 className="section-title">📊 Estatísticas do Banco de Dados</h2>
              <div className="stats-grid">
                <div className="stat-item">
                  <div className="stat-value">{systemStatus.stats.database.seasons}</div>
                  <div className="stat-label">Temporadas</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{systemStatus.stats.database.events}</div>
                  <div className="stat-label">Eventos</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{systemStatus.stats.database.drivers}</div>
                  <div className="stat-label">Pilotos</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{systemStatus.stats.database.teams}</div>
                  <div className="stat-label">Equipes</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{systemStatus.stats.database.race_results}</div>
                  <div className="stat-label">Resultados de Corrida</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{systemStatus.stats.database.pit_stops}</div>
                  <div className="stat-label">Pit Stops</div>
                </div>
              </div>
              <Link to="/status" className="section-link">Ver status completo do sistema →</Link>
            </div>
          )}
        </>
      )}

      <div className="home-section">
        <h2 className="section-title">🔍 Explore os Dados</h2>
        <div className="home-grid">
          {sections.map((section) => (
            <Link key={section.link} to={section.link} className="home-card-link">
              <Card className="home-card">
                <div className="card-header">
                  <h3 className="home-card-title">{section.title}</h3>
                  {section.badge && (
                    <span className="card-badge">{section.badge}</span>
                  )}
                </div>
                <p className="home-card-description">{section.description}</p>
                <span className="home-card-arrow">→</span>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      <div className="home-footer">
        <p>Powered by FastF1 • Dados históricos de F1</p>
        <p className="update-info">
          Dados atualizados automaticamente a cada 5 minutos
        </p>
      </div>
    </div>
  );
}
