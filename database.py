import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd


class F1Database:
    """Gerencia cache de dados da F1 em SQLite"""

    def __init__(self, db_path='data/f1_cache.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inicializa o banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabela para cache de sessões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                event_name TEXT,
                session_type TEXT,
                data_type TEXT,
                data TEXT,
                cached_at TIMESTAMP,
                UNIQUE(year, event_name, session_type, data_type)
            )
        ''')

        # Tabela para classificação de pilotos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS driver_standings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                driver_name TEXT,
                team_name TEXT,
                points REAL,
                wins INTEGER,
                cached_at TIMESTAMP,
                UNIQUE(year, driver_name)
            )
        ''')

        # Tabela para classificação de construtores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS constructor_standings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                team_name TEXT,
                points REAL,
                wins INTEGER,
                cached_at TIMESTAMP,
                UNIQUE(year, team_name)
            )
        ''')

        conn.commit()
        conn.close()

    def get_cached_session(self, year, event_name, session_type, data_type, max_age_hours=24):
        """Recupera dados de sessão do cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        cursor.execute('''
            SELECT data, cached_at FROM session_cache
            WHERE year = ? AND event_name = ? AND session_type = ? AND data_type = ?
            AND cached_at > ?
        ''', (year, event_name, session_type, data_type, cutoff_time))

        result = cursor.fetchone()
        conn.close()

        if result:
            return json.loads(result[0])
        return None

    def cache_session(self, year, event_name, session_type, data_type, data):
        """Armazena dados de sessão no cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data_json = json.dumps(data)
        now = datetime.now()

        cursor.execute('''
            INSERT OR REPLACE INTO session_cache
            (year, event_name, session_type, data_type, data, cached_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (year, event_name, session_type, data_type, data_json, now))

        conn.commit()
        conn.close()

    def get_driver_standings(self, year, max_age_hours=24):
        """Recupera classificação de pilotos do cache"""
        conn = sqlite3.connect(self.db_path)

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        df = pd.read_sql_query('''
            SELECT driver_name, team_name, points, wins
            FROM driver_standings
            WHERE year = ? AND cached_at > ?
            ORDER BY points DESC
        ''', conn, params=(year, cutoff_time))

        conn.close()

        return df if len(df) > 0 else None

    def cache_driver_standings(self, year, standings_df):
        """Armazena classificação de pilotos no cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now()

        for _, row in standings_df.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO driver_standings
                (year, driver_name, team_name, points, wins, cached_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (year, row['Piloto'], row['Equipe'], row['Pontos'], row['Vitórias'], now))

        conn.commit()
        conn.close()

    def get_constructor_standings(self, year, max_age_hours=24):
        """Recupera classificação de construtores do cache"""
        conn = sqlite3.connect(self.db_path)

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        df = pd.read_sql_query('''
            SELECT team_name, points, wins
            FROM constructor_standings
            WHERE year = ? AND cached_at > ?
            ORDER BY points DESC
        ''', conn, params=(year, cutoff_time))

        conn.close()

        return df if len(df) > 0 else None

    def cache_constructor_standings(self, year, standings_df):
        """Armazena classificação de construtores no cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now()

        for _, row in standings_df.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO constructor_standings
                (year, team_name, points, wins, cached_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (year, row['Equipe'], row['Pontos'], row['Vitórias'], now))

        conn.commit()
        conn.close()
