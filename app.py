import streamlit as st
from f1_data import F1DataManager
from datetime import datetime
import locale
import pandas as pd
import os

# Configurar locale para formato brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except:
        pass  # Se não conseguir, usa o padrão


# Configuração da página
st.set_page_config(
    page_title="F1 Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def apply_theme(theme_mode='dark'):
    """Aplica tema customizado inspirado no design oficial da F1"""

    # Cores baseadas no tema oficial da F1
    if theme_mode == 'light':
        bg_color = '#FFFFFF'
        text_color = '#15151E'
        surface_neutral_1 = '#F7F4F1'
        surface_neutral_2 = '#E8E8E8'
        surface_neutral_3 = '#D0D0D2'
        accent_red = '#E10600'
        accent_magenta = '#D946EF'
        accent_purple = '#9333EA'
        card_bg = '#FFFFFF'
        sidebar_bg = '#F7F4F1'
        border_color = '#E8E8E8'
    else:  # dark - paleta oficial F1
        bg_color = '#15151E'
        text_color = '#FAFAFA'
        surface_neutral_1 = '#1A1A24'
        surface_neutral_2 = '#252530'
        surface_neutral_3 = '#38383F'
        accent_red = '#E10600'
        accent_magenta = '#D946EF'
        accent_purple = '#9333EA'
        card_bg = '#1E1E28'
        sidebar_bg = '#15151E'
        border_color = '#38383F'

    st.markdown(f"""
        <style>
        /* Import Google Fonts - Titillium Web usado pela F1 */
        @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@200;300;400;600;700;900&display=swap');

        /* Reset e Tema Base */
        * {{
            font-family: 'Titillium Web', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}

        .stApp {{
            background: linear-gradient(135deg, {bg_color} 0%, {surface_neutral_1} 100%);
            color: {text_color};
        }}

        /* Sidebar Premium */
        [data-testid="stSidebar"] {{
            background: {sidebar_bg};
            border-right: 1px solid {border_color};
        }}

        [data-testid="stSidebar"] .stMarkdown {{
            color: {text_color};
        }}

        /* Hero Section */
        .hero-section {{
            background: linear-gradient(135deg, {accent_red} 0%, {accent_magenta} 50%, {accent_purple} 100%);
            padding: 3rem 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 20px 60px rgba(225, 6, 0, 0.3);
            position: relative;
            overflow: hidden;
        }}

        .hero-section::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            border-radius: 50%;
        }}

        .hero-title {{
            font-size: 3.5rem;
            font-weight: 900;
            color: white;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: -2px;
            line-height: 1.1;
            position: relative;
            z-index: 1;
        }}

        .hero-subtitle {{
            font-size: 1.25rem;
            font-weight: 300;
            color: rgba(255,255,255,0.9);
            margin-top: 0.5rem;
            position: relative;
            z-index: 1;
        }}

        /* Cards Premium com Gradiente */
        [data-testid="stMetric"] {{
            background: linear-gradient(135deg, {card_bg} 0%, {surface_neutral_2} 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid {border_color};
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}

        [data-testid="stMetric"]::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, {accent_red} 0%, {accent_magenta} 100%);
        }}

        [data-testid="stMetric"]:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(225, 6, 0, 0.2);
            border-color: {accent_red};
        }}

        /* Tipografia Premium */
        h1 {{
            font-size: 2.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, {accent_red} 0%, {accent_magenta} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-transform: uppercase;
            letter-spacing: -1px;
            margin-bottom: 0.5rem;
        }}

        h2 {{
            font-size: 1.75rem;
            font-weight: 700;
            color: {text_color};
            text-transform: uppercase;
            letter-spacing: -0.5px;
            margin-bottom: 1rem;
        }}

        h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: {text_color};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Tabs Estilo F1 */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 12px;
            background-color: {surface_neutral_1};
            padding: 0.75rem;
            border-radius: 16px;
            border: 1px solid {border_color};
            box-shadow: 0 4px 16px rgba(0,0,0,0.05);
        }}

        .stTabs [data-baseweb="tab"] {{
            padding: 14px 28px;
            border-radius: 12px;
            background-color: transparent;
            color: {text_color};
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            border: none;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            background-color: {surface_neutral_2};
        }}

        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background: linear-gradient(135deg, {accent_red} 0%, {accent_magenta} 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(225, 6, 0, 0.3);
        }}

        /* Tabelas Premium */
        .stDataFrame {{
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid {border_color};
        }}

        .stDataFrame table {{
            font-size: 0.95rem;
        }}

        .stDataFrame th {{
            background: linear-gradient(135deg, {surface_neutral_2} 0%, {surface_neutral_3} 100%);
            color: {text_color};
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.85rem;
            padding: 1rem !important;
        }}

        .stDataFrame td {{
            padding: 0.75rem 1rem !important;
            border-bottom: 1px solid {border_color};
        }}

        /* Container Principal */
        .block-container {{
            padding-top: 3rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }}

        /* Dividers Elegantes */
        hr {{
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, {accent_red} 50%, transparent 100%);
            margin: 2rem 0;
        }}

        /* Botões Premium */
        .stButton button {{
            background: linear-gradient(135deg, {accent_red} 0%, {accent_magenta} 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 1.5rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(225, 6, 0, 0.3);
        }}

        .stButton button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(225, 6, 0, 0.4);
        }}

        /* Captions */
        .stCaption {{
            color: {text_color};
            opacity: 0.7;
            font-size: 0.85rem;
            font-weight: 400;
        }}

        /* Spinner Loading */
        .stSpinner > div {{
            border-top-color: {accent_red} !important;
        }}

        /* Scrollbar Premium */
        ::-webkit-scrollbar {{
            width: 12px;
            height: 12px;
        }}

        ::-webkit-scrollbar-track {{
            background: {surface_neutral_1};
        }}

        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(135deg, {accent_red} 0%, {accent_magenta} 100%);
            border-radius: 6px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(135deg, {accent_magenta} 0%, {accent_purple} 100%);
        }}

        /* Animações */
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .element-container {{
            animation: fadeIn 0.5s ease-out;
        }}
        </style>
    """, unsafe_allow_html=True)


class F1Dashboard:
    """Dashboard principal da F1"""

    def __init__(self):
        # Configurar URL da API via variável de ambiente (útil para Docker)
        api_url = os.getenv('F1_API_URL', 'http://localhost:5000')
        self.data_manager = F1DataManager(api_url=api_url)

    def render_sidebar(self):
        """Renderiza sidebar premium"""
        with st.sidebar:
            # Logo/Título
            st.markdown("""
                <div style="text-align: center; padding: 1rem 0;">
                    <h1 style="font-size: 2rem; margin: 0;">🏎️</h1>
                    <h2 style="font-size: 1.5rem; margin: 0.5rem 0 0 0;">F1 DASHBOARD</h2>
                </div>
            """, unsafe_allow_html=True)

            st.divider()

            # Switch de tema
            st.markdown("### ⚙️ Configurações")

            # Inicializar theme no session_state se não existir
            if 'theme' not in st.session_state:
                st.session_state.theme = 'dark'

            # Toggle de tema
            theme_label = "🌙 Modo Escuro" if st.session_state.theme == 'dark' else "☀️ Modo Claro"
            if st.button(theme_label, use_container_width=True):
                st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
                st.rerun()

            st.divider()

            # Informações com ícones
            st.markdown("### 📊 Sobre")
            st.markdown("""
            <div style="line-height: 2;">
                🏆 <strong>Resultados de corridas</strong><br>
                ⏱️ <strong>Qualificações</strong><br>
                👤 <strong>Classificação de pilotos</strong><br>
                🏁 <strong>Classificação de construtores</strong>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            # Footer
            st.markdown("""
                <div style="text-align: center; padding-top: 2rem; opacity: 0.7;">
                    <p style="font-size: 0.75rem; margin: 0.25rem 0;">
                        <strong>Temporada 2025</strong>
                    </p>
                    <p style="font-size: 0.75rem; margin: 0.25rem 0;">
                        Powered by FastF1
                    </p>
                </div>
            """, unsafe_allow_html=True)

    def render_race_tab(self):
        """Renderiza aba de corrida com design premium"""
        st.markdown("## 🏆 Última Corrida")

        with st.spinner("Carregando dados da corrida..."):
            race_session = self.data_manager.get_latest_race()

            if race_session:
                # Card de informações da corrida
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("📍 Grande Prêmio", race_session.event['EventName'])
                with col2:
                    st.metric("🌍 Localização", race_session.event['Location'])
                with col3:
                    # Formatar data em português brasileiro
                    data_corrida = race_session.date
                    data_formatada = data_corrida.strftime("%d/%m/%Y")
                    st.metric("📅 Data", data_formatada)

                st.divider()

                df_race = self.data_manager.format_race_results(race_session)

                if df_race is not None:
                    # Pódio em destaque
                    if len(df_race) >= 3:
                        st.markdown("### 🏆 Pódio")

                        pod1, pod2, pod3 = st.columns(3)

                        with pod1:
                            st.markdown(f"""
                                <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); border-radius: 12px; margin-bottom: 1rem;">
                                    <h1 style="margin: 0; color: #000; font-size: 3rem;">🥇</h1>
                                    <h3 style="margin: 0.5rem 0; color: #000;">{df_race.iloc[0]['Piloto']}</h3>
                                    <p style="margin: 0; color: #000; opacity: 0.8;">{df_race.iloc[0]['Equipe']}</p>
                                </div>
                            """, unsafe_allow_html=True)

                        with pod2:
                            st.markdown(f"""
                                <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #C0C0C0 0%, #A9A9A9 100%); border-radius: 12px; margin-bottom: 1rem;">
                                    <h1 style="margin: 0; color: #000; font-size: 3rem;">🥈</h1>
                                    <h3 style="margin: 0.5rem 0; color: #000;">{df_race.iloc[1]['Piloto']}</h3>
                                    <p style="margin: 0; color: #000; opacity: 0.8;">{df_race.iloc[1]['Equipe']}</p>
                                </div>
                            """, unsafe_allow_html=True)

                        with pod3:
                            st.markdown(f"""
                                <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%); border-radius: 12px; margin-bottom: 1rem;">
                                    <h1 style="margin: 0; color: #000; font-size: 3rem;">🥉</h1>
                                    <h3 style="margin: 0.5rem 0; color: #000;">{df_race.iloc[2]['Piloto']}</h3>
                                    <p style="margin: 0; color: #000; opacity: 0.8;">{df_race.iloc[2]['Equipe']}</p>
                                </div>
                            """, unsafe_allow_html=True)

                        st.divider()

                    # Tabela completa de resultados
                    st.markdown("### 📊 Resultados Completos")

                    # Resetar índice para evitar problemas
                    df_race_reset = df_race.reset_index(drop=True)

                    # Aplicar cores das equipes e destacar pódio
                    def apply_team_colors(row):
                        # Acessar dados diretamente da row (que já tem a coluna Cor)
                        idx = row.name
                        team_color = df_race_reset.loc[idx, 'Cor'] if 'Cor' in df_race_reset.columns else None
                        posicao = row['Posição']

                        # Se for pódio, usar cor especial
                        if posicao == 1:
                            bg_color = '#FFD700'
                            text_color = 'black'
                        elif posicao == 2:
                            bg_color = '#C0C0C0'
                            text_color = 'black'
                        elif posicao == 3:
                            bg_color = '#CD7F32'
                            text_color = 'black'
                        else:
                            # Usar cor da equipe
                            if pd.notna(team_color) and team_color:
                                bg_color = f"#{team_color}" if not team_color.startswith('#') else team_color
                                text_color = 'white'
                            else:
                                bg_color = 'transparent'
                                text_color = 'inherit'

                        return [f'background-color: {bg_color}; color: {text_color}'] * len(row)

                    # Remover coluna Cor antes de exibir (se existir)
                    df_display = df_race_reset.drop(columns=['Cor'], errors='ignore')

                    st.dataframe(
                        df_display.style.apply(apply_team_colors, axis=1),
                        hide_index=True,
                        use_container_width=True,
                        height=500
                    )

    def render_qualifying_tab(self):
        """Renderiza aba de qualificação com design premium"""
        st.markdown("## ⏱️ Última Qualificação")

        with st.spinner("Carregando dados da qualificação..."):
            quali_session = self.data_manager.get_latest_qualifying()

            if quali_session:
                # Card de informações da qualificação
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("📍 Grande Prêmio", quali_session.event['EventName'])
                with col2:
                    st.metric("🌍 Localização", quali_session.event['Location'])
                with col3:
                    # Formatar data em português brasileiro
                    data_quali = quali_session.date
                    data_formatada = data_quali.strftime("%d/%m/%Y")
                    st.metric("📅 Data", data_formatada)

                st.divider()

                df_quali = self.data_manager.format_qualifying_results(quali_session)

                if df_quali is not None:
                    # Pole Position em destaque
                    if len(df_quali) >= 1:
                        st.markdown("### 🏁 Pole Position")

                        pole_col1, pole_col2, pole_col3 = st.columns([1, 2, 1])

                        with pole_col2:
                            st.markdown(f"""
                                <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); border-radius: 16px; margin-bottom: 1.5rem; box-shadow: 0 8px 32px rgba(255, 215, 0, 0.3);">
                                    <h1 style="margin: 0; color: #000; font-size: 4rem;">🏁</h1>
                                    <h2 style="margin: 1rem 0 0.5rem 0; color: #000; font-size: 2rem;">{df_quali.iloc[0]['Piloto']}</h2>
                                    <p style="margin: 0; color: #000; opacity: 0.8; font-size: 1.1rem;">{df_quali.iloc[0]['Equipe']}</p>
                                    <p style="margin: 0.5rem 0 0 0; color: #000; font-weight: 700; font-size: 1.3rem;">{df_quali.iloc[0]['Q3']}</p>
                                </div>
                            """, unsafe_allow_html=True)

                        st.divider()

                    # Tabela completa de resultados
                    st.markdown("### 📊 Resultados Completos")

                    # Resetar índice para evitar problemas
                    df_quali_reset = df_quali.reset_index(drop=True)

                    # Aplicar cores das equipes e destacar pole
                    def apply_team_colors_quali(row):
                        # Acessar dados diretamente da row
                        idx = row.name
                        team_color = df_quali_reset.loc[idx, 'Cor'] if 'Cor' in df_quali_reset.columns else None
                        posicao = row['Posição']

                        # Se for pole position, usar ouro
                        if posicao == 1:
                            bg_color = '#FFD700'
                            text_color = 'black'
                        else:
                            # Usar cor da equipe
                            if pd.notna(team_color) and team_color:
                                bg_color = f"#{team_color}" if not team_color.startswith('#') else team_color
                                text_color = 'white'
                            else:
                                bg_color = 'transparent'
                                text_color = 'inherit'

                        return [f'background-color: {bg_color}; color: {text_color}'] * len(row)

                    # Remover coluna Cor antes de exibir (se existir)
                    df_display = df_quali_reset.drop(columns=['Cor'], errors='ignore')

                    st.dataframe(
                        df_display.style.apply(apply_team_colors_quali, axis=1),
                        hide_index=True,
                        use_container_width=True,
                        height=500
                    )

    def render_driver_standings_tab(self):
        """Renderiza aba de classificação de pilotos com design premium"""
        st.markdown("## 👤 Classificação de Pilotos 2025")

        with st.spinner("Carregando classificação..."):
            df_standings = self.data_manager.get_driver_standings()

            if df_standings is not None:
                # Top 3 Pódio
                st.markdown("### 🏆 Pódio do Campeonato")

                col1, col2, col3 = st.columns(3)

                if len(df_standings) >= 1:
                    with col1:
                        pontos = df_standings.iloc[0]['Pontos']
                        st.markdown(f"""
                            <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); border-radius: 12px; box-shadow: 0 8px 24px rgba(255, 215, 0, 0.3);">
                                <h1 style="margin: 0; color: #000; font-size: 2.5rem;">🥇</h1>
                                <h3 style="margin: 0.5rem 0; color: #000; font-size: 1.3rem;">{df_standings.iloc[0]['Piloto']}</h3>
                                <p style="margin: 0.25rem 0; color: #000; opacity: 0.8;">{df_standings.iloc[0]['Equipe']}</p>
                                <p style="margin: 0.5rem 0 0 0; color: #000; font-weight: 700; font-size: 1.5rem;">{pontos} pts</p>
                            </div>
                        """, unsafe_allow_html=True)

                if len(df_standings) >= 2:
                    with col2:
                        pontos = df_standings.iloc[1]['Pontos']
                        st.markdown(f"""
                            <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #C0C0C0 0%, #A9A9A9 100%); border-radius: 12px; box-shadow: 0 8px 24px rgba(192, 192, 192, 0.3);">
                                <h1 style="margin: 0; color: #000; font-size: 2.5rem;">🥈</h1>
                                <h3 style="margin: 0.5rem 0; color: #000; font-size: 1.3rem;">{df_standings.iloc[1]['Piloto']}</h3>
                                <p style="margin: 0.25rem 0; color: #000; opacity: 0.8;">{df_standings.iloc[1]['Equipe']}</p>
                                <p style="margin: 0.5rem 0 0 0; color: #000; font-weight: 700; font-size: 1.5rem;">{pontos} pts</p>
                            </div>
                        """, unsafe_allow_html=True)

                if len(df_standings) >= 3:
                    with col3:
                        pontos = df_standings.iloc[2]['Pontos']
                        st.markdown(f"""
                            <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%); border-radius: 12px; box-shadow: 0 8px 24px rgba(205, 127, 50, 0.3);">
                                <h1 style="margin: 0; color: #000; font-size: 2.5rem;">🥉</h1>
                                <h3 style="margin: 0.5rem 0; color: #000; font-size: 1.3rem;">{df_standings.iloc[2]['Piloto']}</h3>
                                <p style="margin: 0.25rem 0; color: #000; opacity: 0.8;">{df_standings.iloc[2]['Equipe']}</p>
                                <p style="margin: 0.5rem 0 0 0; color: #000; font-weight: 700; font-size: 1.5rem;">{pontos} pts</p>
                            </div>
                        """, unsafe_allow_html=True)

                st.divider()

                # Tabela completa
                st.markdown("### 📊 Classificação Completa")

                # Resetar índice para evitar problemas
                df_standings_reset = df_standings.reset_index(drop=True)

                def apply_team_colors_standings(row):
                    # Acessar dados diretamente da row
                    idx = row.name
                    team_color = df_standings_reset.loc[idx, 'Cor'] if 'Cor' in df_standings_reset.columns else None
                    posicao = row['Posição']

                    # Se for pódio, usar cor especial
                    if posicao == 1:
                        bg_color = '#FFD700'
                        text_color = 'black'
                    elif posicao == 2:
                        bg_color = '#C0C0C0'
                        text_color = 'black'
                    elif posicao == 3:
                        bg_color = '#CD7F32'
                        text_color = 'black'
                    else:
                        # Usar cor da equipe
                        if pd.notna(team_color) and team_color:
                            bg_color = f"#{team_color}" if not team_color.startswith('#') else team_color
                            text_color = 'white'
                        else:
                            bg_color = 'transparent'
                            text_color = 'inherit'

                    return [f'background-color: {bg_color}; color: {text_color}'] * len(row)

                # Remover coluna Cor antes de exibir (se existir)
                df_display = df_standings_reset.drop(columns=['Cor'], errors='ignore')

                st.dataframe(
                    df_display.style.apply(apply_team_colors_standings, axis=1),
                    hide_index=True,
                    use_container_width=True,
                    height=500
                )

    def render_constructor_standings_tab(self):
        """Renderiza aba de classificação de construtores com design premium"""
        st.markdown("## 🏁 Classificação de Construtores 2025")

        with st.spinner("Carregando classificação..."):
            df_standings = self.data_manager.get_constructor_standings()

            if df_standings is not None:
                # Top 3 Pódio
                st.markdown("### 🏆 Pódio do Campeonato")

                col1, col2, col3 = st.columns(3)

                if len(df_standings) >= 1:
                    with col1:
                        pontos = df_standings.iloc[0]['Pontos']
                        vitorias = df_standings.iloc[0]['Vitórias']
                        st.markdown(f"""
                            <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); border-radius: 12px; box-shadow: 0 8px 24px rgba(255, 215, 0, 0.3);">
                                <h1 style="margin: 0; color: #000; font-size: 2.5rem;">🥇</h1>
                                <h3 style="margin: 0.5rem 0; color: #000; font-size: 1.3rem;">{df_standings.iloc[0]['Equipe']}</h3>
                                <p style="margin: 0.5rem 0; color: #000; font-weight: 700; font-size: 1.5rem;">{pontos} pts</p>
                                <p style="margin: 0; color: #000; opacity: 0.8;">{vitorias} vitórias</p>
                            </div>
                        """, unsafe_allow_html=True)

                if len(df_standings) >= 2:
                    with col2:
                        pontos = df_standings.iloc[1]['Pontos']
                        vitorias = df_standings.iloc[1]['Vitórias']
                        st.markdown(f"""
                            <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #C0C0C0 0%, #A9A9A9 100%); border-radius: 12px; box-shadow: 0 8px 24px rgba(192, 192, 192, 0.3);">
                                <h1 style="margin: 0; color: #000; font-size: 2.5rem;">🥈</h1>
                                <h3 style="margin: 0.5rem 0; color: #000; font-size: 1.3rem;">{df_standings.iloc[1]['Equipe']}</h3>
                                <p style="margin: 0.5rem 0; color: #000; font-weight: 700; font-size: 1.5rem;">{pontos} pts</p>
                                <p style="margin: 0; color: #000; opacity: 0.8;">{vitorias} vitórias</p>
                            </div>
                        """, unsafe_allow_html=True)

                if len(df_standings) >= 3:
                    with col3:
                        pontos = df_standings.iloc[2]['Pontos']
                        vitorias = df_standings.iloc[2]['Vitórias']
                        st.markdown(f"""
                            <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%); border-radius: 12px; box-shadow: 0 8px 24px rgba(205, 127, 50, 0.3);">
                                <h1 style="margin: 0; color: #000; font-size: 2.5rem;">🥉</h1>
                                <h3 style="margin: 0.5rem 0; color: #000; font-size: 1.3rem;">{df_standings.iloc[2]['Equipe']}</h3>
                                <p style="margin: 0.5rem 0; color: #000; font-weight: 700; font-size: 1.5rem;">{pontos} pts</p>
                                <p style="margin: 0; color: #000; opacity: 0.8;">{vitorias} vitórias</p>
                            </div>
                        """, unsafe_allow_html=True)

                st.divider()

                # Tabela completa
                st.markdown("### 📊 Classificação Completa")

                # Resetar índice para evitar problemas
                df_standings_reset = df_standings.reset_index(drop=True)

                def apply_team_colors_constructor(row):
                    # Acessar dados diretamente da row
                    idx = row.name
                    team_color = df_standings_reset.loc[idx, 'Cor'] if 'Cor' in df_standings_reset.columns else None
                    posicao = row['Posição']

                    # Se for pódio, usar cor especial
                    if posicao == 1:
                        bg_color = '#FFD700'
                        text_color = 'black'
                    elif posicao == 2:
                        bg_color = '#C0C0C0'
                        text_color = 'black'
                    elif posicao == 3:
                        bg_color = '#CD7F32'
                        text_color = 'black'
                    else:
                        # Usar cor da equipe
                        if pd.notna(team_color) and team_color:
                            bg_color = f"#{team_color}" if not team_color.startswith('#') else team_color
                            text_color = 'white'
                        else:
                            bg_color = 'transparent'
                            text_color = 'inherit'

                    return [f'background-color: {bg_color}; color: {text_color}'] * len(row)

                # Remover coluna Cor antes de exibir (se existir)
                df_display = df_standings_reset.drop(columns=['Cor'], errors='ignore')

                st.dataframe(
                    df_display.style.apply(apply_team_colors_constructor, axis=1),
                    hide_index=True,
                    use_container_width=True,
                    height=500
                )

    def render(self):
        """Renderiza o dashboard completo"""
        # Inicializar theme no session_state se não existir
        if 'theme' not in st.session_state:
            st.session_state.theme = 'dark'

        # Aplicar tema baseado no session_state
        apply_theme(st.session_state.theme)

        # Sidebar
        self.render_sidebar()

        # Hero Section
        st.markdown("""
            <div class="hero-section">
                <h1 class="hero-title">Fórmula 1</h1>
                <p class="hero-subtitle">Acompanhe resultados em tempo real, classificações e estatísticas da temporada 2025</p>
            </div>
        """, unsafe_allow_html=True)

        # Tabs principais com novo design
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏆 Última Corrida",
            "⏱️ Última Qualificação",
            "👤 Pilotos",
            "🏁 Construtores"
        ])

        with tab1:
            self.render_race_tab()

        with tab2:
            self.render_qualifying_tab()

        with tab3:
            self.render_driver_standings_tab()

        with tab4:
            self.render_constructor_standings_tab()


if __name__ == "__main__":
    dashboard = F1Dashboard()
    dashboard.render()
