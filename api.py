from flask import Flask, jsonify, request
from flask_cors import CORS
from database import F1Database
import pandas as pd
from datetime import datetime
import fastf1

app = Flask(__name__)
CORS(app)  # Permitir requisições do frontend React

db = F1Database()

# Cores oficiais das equipes F1 (2024/2025)
TEAM_COLORS = {
    'Red Bull Racing': '3671C6',
    'Ferrari': 'E8002D',
    'Mercedes': '27F4D2',
    'McLaren': 'FF8000',
    'Aston Martin': '229971',
    'Alpine': 'FF87BC',
    'Williams': '64C4FF',
    'RB': '6692FF',
    'Kick Sauber': '52E252',
    'Haas F1 Team': 'B6BABD',
    'Red Bull': '3671C6',
    'Alfa Romeo': '52E252',
    'AlphaTauri': '6692FF',
    'Sauber': '52E252',
}


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/api/driver-standings/<int:year>', methods=['GET'])
def get_driver_standings(year):
    """Retorna classificação de pilotos com cache"""
    try:
        df = db.get_driver_standings(year)

        if df is not None and len(df) > 0:
            # Converter DataFrame para formato esperado pelo frontend
            data = []
            for idx, row in df.iterrows():
                data.append({
                    'position': idx + 1,
                    'name': row['driver_name'],
                    'team': row['team_name'],
                    'points': float(row['points']),
                    'wins': int(row['wins']),
                    'teamColor': TEAM_COLORS.get(row['team_name'], 'FFFFFF')
                })

            return jsonify(data)
        else:
            return jsonify([]), 404

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/driver-standings/<int:year>', methods=['POST'])
def update_driver_standings(year):
    """Atualiza classificação de pilotos no cache"""
    try:
        data = request.json

        if not data or 'standings' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing standings data'
            }), 400

        # Converter dados para DataFrame
        df = pd.DataFrame(data['standings'])

        # Armazenar no cache
        db.cache_driver_standings(year, df)

        return jsonify({
            'status': 'success',
            'message': 'Driver standings cached successfully',
            'year': year,
            'count': len(df)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/constructor-standings/<int:year>', methods=['GET'])
def get_constructor_standings(year):
    """Retorna classificação de construtores com cache"""
    try:
        df = db.get_constructor_standings(year)

        if df is not None and len(df) > 0:
            # Converter DataFrame para formato esperado pelo frontend
            data = []
            for idx, row in df.iterrows():
                data.append({
                    'position': idx + 1,
                    'team': row['team_name'],
                    'points': float(row['points']),
                    'wins': int(row['wins']),
                    'teamColor': TEAM_COLORS.get(row['team_name'], 'FFFFFF')
                })

            return jsonify(data)
        else:
            return jsonify([]), 404

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/constructor-standings/<int:year>', methods=['POST'])
def update_constructor_standings(year):
    """Atualiza classificação de construtores no cache"""
    try:
        data = request.json

        if not data or 'standings' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing standings data'
            }), 400

        # Converter dados para DataFrame
        df = pd.DataFrame(data['standings'])

        # Armazenar no cache
        db.cache_constructor_standings(year, df)

        return jsonify({
            'status': 'success',
            'message': 'Constructor standings cached successfully',
            'year': year,
            'count': len(df)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/race/<int:year>/<event>', methods=['GET'])
def get_race_results(year, event):
    """Retorna resultados de corrida do cache"""
    try:
        cached = db.get_cached_session(year, event, 'R', 'results')

        if cached:
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'year': year,
                'event': event,
                'data': cached
            })
        else:
            return jsonify({
                'status': 'no_data',
                'source': 'cache',
                'year': year,
                'event': event,
                'data': None
            }), 404

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/race/<int:year>/<event>', methods=['POST'])
def update_race_results(year, event):
    """Atualiza resultados de corrida no cache"""
    try:
        data = request.json

        if not data or 'results' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing results data'
            }), 400

        # Armazenar no cache
        db.cache_session(year, event, 'R', 'results', data['results'])

        return jsonify({
            'status': 'success',
            'message': 'Race results cached successfully',
            'year': year,
            'event': event
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/qualifying/<int:year>/<event>', methods=['GET'])
def get_qualifying_results(year, event):
    """Retorna resultados de qualificação do cache"""
    try:
        cached = db.get_cached_session(year, event, 'Q', 'results')

        if cached:
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'year': year,
                'event': event,
                'data': cached
            })
        else:
            return jsonify({
                'status': 'no_data',
                'source': 'cache',
                'year': year,
                'event': event,
                'data': None
            }), 404

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/qualifying/<int:year>/<event>', methods=['POST'])
def update_qualifying_results(year, event):
    """Atualiza resultados de qualificação no cache"""
    try:
        data = request.json

        if not data or 'results' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing results data'
            }), 400

        # Armazenar no cache
        db.cache_session(year, event, 'Q', 'results', data['results'])

        return jsonify({
            'status': 'success',
            'message': 'Qualifying results cached successfully',
            'year': year,
            'event': event
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/drivers/standings', methods=['GET'])
def get_drivers_standings():
    """Retorna classificação de pilotos do ano atual"""
    year = datetime.now().year
    return get_driver_standings(year)


@app.route('/api/constructors/standings', methods=['GET'])
def get_constructors_standings():
    """Retorna classificação de construtores do ano atual"""
    year = datetime.now().year
    return get_constructor_standings(year)


@app.route('/api/races/latest', methods=['GET'])
def get_latest_race():
    """Retorna dados da última corrida disponível"""
    try:
        # Configurar cache do FastF1
        import os
        cache_dir = '.fastf1_cache'
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        fastf1.Cache.enable_cache(cache_dir)

        # Tentar encontrar a última corrida com dados
        for try_year in [2025, 2024]:
            for round_num in range(24, 0, -1):
                try:
                    session = fastf1.get_session(try_year, round_num, 'R')

                    # Verificar se a corrida já aconteceu
                    race_date = session.event.get('EventDate')
                    if race_date and race_date > datetime.now():
                        continue

                    session.load()

                    if session.results is not None and len(session.results) > 0:
                        # Formatar dados da corrida
                        results = session.results.copy()

                        race_results = []
                        for idx, row in results.iterrows():
                            race_results.append({
                                'position': int(row['Position']) if pd.notna(row['Position']) else 0,
                                'driver': str(row['BroadcastName']),
                                'team': str(row['TeamName']),
                                'time': str(row.get('Time', 'N/A')),
                                'points': float(row['Points']),
                                'teamColor': TEAM_COLORS.get(str(row['TeamName']), 'FFFFFF')
                            })

                        race_info = {
                            'eventName': session.event['EventName'],
                            'location': session.event['Location'],
                            'date': session.date.strftime('%Y-%m-%d'),
                            'round': session.event['RoundNumber']
                        }

                        return jsonify({
                            'status': 'success',
                            'raceInfo': race_info,
                            'results': race_results
                        })
                except Exception as e:
                    continue

        return jsonify({
            'status': 'no_data',
            'message': 'No race data available'
        }), 404

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/qualifying/latest', methods=['GET'])
def get_latest_qualifying():
    """Retorna dados da última qualificação disponível"""
    try:
        # Configurar cache do FastF1
        import os
        cache_dir = '.fastf1_cache'
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        fastf1.Cache.enable_cache(cache_dir)

        # Tentar encontrar a última qualificação com dados
        for try_year in [2025, 2024]:
            for round_num in range(24, 0, -1):
                try:
                    session = fastf1.get_session(try_year, round_num, 'Q')

                    # Verificar se a qualificação já aconteceu
                    event_date = session.event.get('EventDate')
                    if event_date and event_date > datetime.now():
                        continue

                    session.load()

                    if session.results is not None and len(session.results) > 0:
                        # Formatar dados da qualificação
                        results = session.results.copy()

                        qualifying_results = []
                        for idx, row in results.iterrows():
                            q1 = str(row.get('Q1', '')).split()[-1] if pd.notna(row.get('Q1')) else None
                            q2 = str(row.get('Q2', '')).split()[-1] if pd.notna(row.get('Q2')) else None
                            q3 = str(row.get('Q3', '')).split()[-1] if pd.notna(row.get('Q3')) else None

                            qualifying_results.append({
                                'position': int(row['Position']) if pd.notna(row['Position']) else 0,
                                'driver': str(row['BroadcastName']),
                                'team': str(row['TeamName']),
                                'q1': q1,
                                'q2': q2,
                                'q3': q3,
                                'teamColor': TEAM_COLORS.get(str(row['TeamName']), 'FFFFFF')
                            })

                        race_info = {
                            'eventName': session.event['EventName'],
                            'location': session.event['Location'],
                            'date': session.date.strftime('%Y-%m-%d'),
                            'round': session.event['RoundNumber']
                        }

                        return jsonify({
                            'status': 'success',
                            'raceInfo': race_info,
                            'results': qualifying_results
                        })
                except Exception as e:
                    continue

        return jsonify({
            'status': 'no_data',
            'message': 'No qualifying data available'
        }), 404

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
