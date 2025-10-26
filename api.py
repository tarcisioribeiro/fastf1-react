from flask import Flask, jsonify, request
from flask_cors import CORS
from database import F1Database
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permitir requisições do Streamlit

db = F1Database()


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
            # Converter DataFrame para dicionário
            data = df.to_dict('records')
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'year': year,
                'data': data
            })
        else:
            return jsonify({
                'status': 'no_data',
                'source': 'cache',
                'year': year,
                'data': []
            }), 404

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
            # Converter DataFrame para dicionário
            data = df.to_dict('records')
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'year': year,
                'data': data
            })
        else:
            return jsonify({
                'status': 'no_data',
                'source': 'cache',
                'year': year,
                'data': []
            }), 404

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
