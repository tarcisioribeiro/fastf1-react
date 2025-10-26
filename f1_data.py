import fastf1
import pandas as pd
import streamlit as st
from database import F1Database
import os


class F1DataManager:
    """Gerencia dados da F1 com cache em SQLite"""

    def __init__(self):
        # Criar diretório de cache do FastF1
        cache_dir = '.fastf1_cache'
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        fastf1.Cache.enable_cache(cache_dir)
        self.db = F1Database()

    def get_latest_race(self, year=2025, event=None):
        """Obtém dados da última corrida que realmente aconteceu"""
        try:
            # Se não especificar evento, buscar a última corrida com dados disponíveis
            if event is None:
                from datetime import datetime

                # Tentar encontrar a última corrida que aconteceu (com dados disponíveis)
                # Começar pelo ano atual e ir voltando
                for try_year in [2025, 2024]:
                    # Buscar de trás para frente até encontrar uma corrida que já aconteceu
                    for round_num in range(24, 0, -1):
                        try:
                            session = fastf1.get_session(try_year, round_num, 'R')

                            # Verificar se a corrida já aconteceu comparando com data atual
                            race_date = session.event.get('EventDate')
                            if race_date and race_date > datetime.now():
                                # Corrida ainda não aconteceu, pular
                                continue

                            # Tentar carregar dados
                            session.load()

                            # Se conseguiu carregar e tem dados de resultados
                            if session.results is not None and len(session.results) > 0:
                                if try_year == 2024:
                                    st.info(f"📅 Mostrando última corrida de 2024: {session.event['EventName']}")
                                return session
                        except Exception as e:
                            # Se der erro, continuar tentando outras corridas
                            continue

                # Se não encontrou nada, mostrar erro
                st.error("Nenhuma corrida com dados disponíveis encontrada")
                return None
            else:
                session = fastf1.get_session(year, event, 'R')
                session.load()
                return session
        except Exception as e:
            st.error(f"Erro ao carregar corrida: {e}")
            return None

    def get_latest_qualifying(self, year=2025, event=None):
        """Obtém dados da última qualificação que realmente aconteceu"""
        try:
            # Se não especificar evento, buscar a última qualificação com dados disponíveis
            if event is None:
                from datetime import datetime

                # Tentar encontrar a última qualificação que aconteceu (com dados disponíveis)
                for try_year in [2025, 2024]:
                    for round_num in range(24, 0, -1):
                        try:
                            session = fastf1.get_session(try_year, round_num, 'Q')

                            # Verificar se a qualificação já aconteceu comparando com data atual
                            event_date = session.event.get('EventDate')
                            if event_date and event_date > datetime.now():
                                # Qualificação ainda não aconteceu, pular
                                continue

                            # Tentar carregar dados
                            session.load()

                            # Se conseguiu carregar e tem dados de resultados
                            if session.results is not None and len(session.results) > 0:
                                if try_year == 2024:
                                    st.info(f"📅 Mostrando última qualificação de 2024: {session.event['EventName']}")
                                return session
                        except Exception as e:
                            # Se der erro, continuar tentando outras qualificações
                            continue

                # Se não encontrou nada, mostrar erro
                st.error("Nenhuma qualificação com dados disponíveis encontrada")
                return None
            else:
                session = fastf1.get_session(year, event, 'Q')
                session.load()
                return session
        except Exception as e:
            st.error(f"Erro ao carregar qualificação: {e}")
            return None

    def format_race_results(self, session):
        """Formata resultados da corrida"""
        if session is None:
            return None

        results = session.results.copy()

        # Verificar quais colunas estão disponíveis
        columns_to_show = ['Position', 'DriverNumber', 'BroadcastName', 'TeamName',
                          'GridPosition', 'Status', 'Points']

        # Adicionar TeamColor se disponível
        if 'TeamColor' in results.columns:
            columns_to_show.append('TeamColor')

        column_translation = {
            'Position': 'Posição',
            'DriverNumber': 'Número',
            'BroadcastName': 'Piloto',
            'TeamName': 'Equipe',
            'GridPosition': 'Grid',
            'Status': 'Status',
            'Points': 'Pontos',
            'TeamColor': 'Cor'
        }

        df = results[columns_to_show].copy()
        df = df.rename(columns=column_translation)

        # Se não houver coluna Cor, adicionar uma vazia
        if 'Cor' not in df.columns:
            df['Cor'] = None

        # Formatar posição
        df['Posição'] = pd.to_numeric(df['Posição'], errors='coerce').fillna(0).astype(int)

        # Formatar número do piloto como inteiro
        df['Número'] = pd.to_numeric(df['Número'], errors='coerce').fillna(0).astype(int)

        # Formatar grid como inteiro
        df['Grid'] = pd.to_numeric(df['Grid'], errors='coerce').fillna(0).astype(int)

        # Formatar pontos (1 decimal apenas se necessário)
        df['Pontos'] = df['Pontos'].apply(lambda x: int(x) if x % 1 == 0 else round(x, 1))

        status_translation = {
            'Finished': '✓ Completou',
            '+1 Lap': '+1 Volta',
            '+2 Laps': '+2 Voltas',
            'Retired': 'Abandonou',
            'Did not finish': 'Não terminou',
            'Disqualified': 'Desqualificado'
        }

        df['Status'] = df['Status'].apply(lambda x: status_translation.get(x, x) if isinstance(x, str) else x)

        return df

    def format_qualifying_results(self, session):
        """Formata resultados da qualificação"""
        if session is None:
            return None

        results = session.results.copy()

        # Verificar quais colunas estão disponíveis
        columns_to_show = ['Position', 'DriverNumber', 'BroadcastName', 'TeamName', 'Q1', 'Q2', 'Q3']

        # Adicionar TeamColor se disponível
        if 'TeamColor' in results.columns:
            columns_to_show.append('TeamColor')

        column_translation = {
            'Position': 'Posição',
            'DriverNumber': 'Número',
            'BroadcastName': 'Piloto',
            'TeamName': 'Equipe',
            'Q1': 'Q1',
            'Q2': 'Q2',
            'Q3': 'Q3',
            'TeamColor': 'Cor'
        }

        df = results[columns_to_show].copy()
        df = df.rename(columns=column_translation)

        # Se não houver coluna Cor, adicionar uma vazia
        if 'Cor' not in df.columns:
            df['Cor'] = None

        # Formatar posição
        df['Posição'] = pd.to_numeric(df['Posição'], errors='coerce').fillna(0).astype(int)

        # Formatar número do piloto como inteiro
        df['Número'] = pd.to_numeric(df['Número'], errors='coerce').fillna(0).astype(int)

        for col in ['Q1', 'Q2', 'Q3']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: str(x).split()[-1] if pd.notna(x) else '-')

        return df

    def get_driver_standings(self, year=2025):
        """Obtém classificação de pilotos com cache"""
        from datetime import datetime

        # Determinar qual ano usar (se 2025 não tiver dados, usar 2024)
        actual_year = year

        # Tentar cache primeiro
        cached = self.db.get_driver_standings(actual_year)
        if cached is not None and len(cached) > 0:
            cached.insert(0, 'Posição', range(1, len(cached) + 1))
            cached = cached.rename(columns={'driver_name': 'Piloto', 'team_name': 'Equipe', 'points': 'Pontos', 'wins': 'Vitórias'})
            # Formatar pontos e vitórias
            cached['Pontos'] = cached['Pontos'].apply(lambda x: int(x) if x % 1 == 0 else round(x, 1))
            cached['Vitórias'] = cached['Vitórias'].astype(int)
            return cached

        # Se não houver cache, calcular
        try:
            standings = {}
            races_found = 0

            # Tentar carregar corridas até encontrar dados
            for round_num in range(1, 25):
                try:
                    session = fastf1.get_session(actual_year, round_num, 'R')

                    # Verificar se a corrida já aconteceu
                    race_date = session.event.get('EventDate')
                    if race_date and race_date > datetime.now():
                        # Corrida ainda não aconteceu
                        continue

                    session.load()
                    results = session.results

                    if results is not None and len(results) > 0:
                        races_found += 1
                        for idx, row in results.iterrows():
                            driver = row['BroadcastName']
                            points = row['Points']
                            team = row['TeamName']

                            if driver not in standings:
                                standings[driver] = {'Equipe': team, 'Pontos': 0, 'Vitórias': 0}

                            standings[driver]['Pontos'] += points
                            if row['Position'] == 1:
                                standings[driver]['Vitórias'] += 1
                except:
                    continue

            # Se não encontrou nenhuma corrida em 2025, tentar 2024
            if races_found == 0 and actual_year == 2025:
                st.info("📅 Dados de 2025 não disponíveis. Mostrando classificação de 2024.")
                return self.get_driver_standings(2024)

            df = pd.DataFrame.from_dict(standings, orient='index')
            df = df.reset_index().rename(columns={'index': 'Piloto'})
            df = df.sort_values('Pontos', ascending=False).reset_index(drop=True)

            # Formatar pontos e vitórias
            df['Pontos'] = df['Pontos'].apply(lambda x: int(x) if x % 1 == 0 else round(x, 1))
            df['Vitórias'] = df['Vitórias'].astype(int)

            # Armazenar no cache
            self.db.cache_driver_standings(year, df)

            df.insert(0, 'Posição', range(1, len(df) + 1))

            return df

        except Exception as e:
            st.warning(f"Erro ao carregar classificação de pilotos: {e}")
            return None

    def get_constructor_standings(self, year=2025):
        """Obtém classificação de construtores com cache"""
        from datetime import datetime

        # Determinar qual ano usar
        actual_year = year

        # Tentar cache primeiro
        cached = self.db.get_constructor_standings(actual_year)
        if cached is not None and len(cached) > 0:
            cached.insert(0, 'Posição', range(1, len(cached) + 1))
            cached = cached.rename(columns={'team_name': 'Equipe', 'points': 'Pontos', 'wins': 'Vitórias'})
            # Formatar pontos e vitórias
            cached['Pontos'] = cached['Pontos'].apply(lambda x: int(x) if x % 1 == 0 else round(x, 1))
            cached['Vitórias'] = cached['Vitórias'].astype(int)
            return cached

        # Se não houver cache, calcular
        try:
            standings = {}
            races_found = 0

            for round_num in range(1, 25):
                try:
                    session = fastf1.get_session(actual_year, round_num, 'R')

                    # Verificar se a corrida já aconteceu
                    race_date = session.event.get('EventDate')
                    if race_date and race_date > datetime.now():
                        # Corrida ainda não aconteceu
                        continue

                    session.load()
                    results = session.results

                    if results is not None and len(results) > 0:
                        races_found += 1
                        for idx, row in results.iterrows():
                            team = row['TeamName']
                            points = row['Points']

                            if team not in standings:
                                standings[team] = {'Pontos': 0, 'Vitórias': 0}

                            standings[team]['Pontos'] += points
                            if row['Position'] == 1:
                                standings[team]['Vitórias'] += 1
                except:
                    continue

            # Se não encontrou nenhuma corrida em 2025, tentar 2024
            if races_found == 0 and actual_year == 2025:
                st.info("📅 Dados de 2025 não disponíveis. Mostrando classificação de 2024.")
                return self.get_constructor_standings(2024)

            df = pd.DataFrame.from_dict(standings, orient='index')
            df = df.reset_index().rename(columns={'index': 'Equipe'})
            df = df.sort_values('Pontos', ascending=False).reset_index(drop=True)

            # Formatar pontos e vitórias
            df['Pontos'] = df['Pontos'].apply(lambda x: int(x) if x % 1 == 0 else round(x, 1))
            df['Vitórias'] = df['Vitórias'].astype(int)

            # Armazenar no cache
            self.db.cache_constructor_standings(year, df)

            df.insert(0, 'Posição', range(1, len(df) + 1))

            return df

        except Exception as e:
            st.warning(f"Erro ao carregar classificação de construtores: {e}")
            return None
