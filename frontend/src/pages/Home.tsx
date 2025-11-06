import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Hero from '../components/Hero';
import Card from '../components/Card';
import { f1Api } from '../services/api';
import './Home.css';

export default function Home() {
  const [leaderDriver, setLeaderDriver] = useState<any>(null);
  const [leaderConstructor, setLeaderConstructor] = useState<any>(null);
  const [latestRace, setLatestRace] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHomeData();
    const interval = setInterval(loadHomeData, 300000); // Atualizar a cada 5 minutos
    return () => clearInterval(interval);
  }, []);

  const loadHomeData = async () => {
    try {
      setLoading(true);

      // Carregar dados em paralelo
      const [drivers, constructors, race] = await Promise.all([
        f1Api.getDriverStandings().catch(() => []),
        f1Api.getConstructorStandings().catch(() => []),
        f1Api.getLatestRace().catch(() => null),
      ]);

      if (drivers.length > 0) setLeaderDriver(drivers[0]);
      if (constructors.length > 0) setLeaderConstructor(constructors[0]);
      if (race) setLatestRace(race);
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
        : 'Confira os resultados da última corrida da temporada 2025',
      link: '/race',
    },
    {
      title: '⏱️ Qualificação',
      description: 'Veja os tempos de qualificação e o grid de largada',
      link: '/qualifying',
    },
    {
      title: '👤 Pilotos',
      description: leaderDriver
        ? `Líder: ${leaderDriver.name} (${leaderDriver.points} pts)`
        : 'Classificação completa do campeonato de pilotos',
      link: '/drivers',
    },
    {
      title: '🏁 Construtores',
      description: leaderConstructor
        ? `Líder: ${leaderConstructor.team} (${leaderConstructor.points} pts)`
        : 'Classificação das equipes no campeonato de construtores',
      link: '/constructors',
    },
  ];

  return (
    <div className="home">
      <Hero />

      {!loading && (leaderDriver || leaderConstructor) && (
        <div className="home-leaders">
          {leaderDriver && (
            <Card
              title="🏆 Líder de Pilotos"
              subtitle={leaderDriver.team}
              value={leaderDriver.name}
              footer={`${leaderDriver.points} pontos • ${leaderDriver.wins} vitórias`}
              color="gold"
            />
          )}
          {leaderConstructor && (
            <Card
              title="🏁 Líder de Construtores"
              value={leaderConstructor.team}
              footer={`${leaderConstructor.points} pontos • ${leaderConstructor.wins} vitórias`}
              color="red"
            />
          )}
        </div>
      )}

      <div className="home-grid">
        {sections.map((section) => (
          <Link key={section.link} to={section.link} className="home-card-link">
            <Card className="home-card">
              <h3 className="home-card-title">{section.title}</h3>
              <p className="home-card-description">{section.description}</p>
              <span className="home-card-arrow">→</span>
            </Card>
          </Link>
        ))}
      </div>

      <div className="home-footer">
        <p>Temporada 2025 • Powered by FastF1</p>
        <p className="update-info">
          Dados atualizados automaticamente a cada 5 minutos
        </p>
      </div>
    </div>
  );
}
