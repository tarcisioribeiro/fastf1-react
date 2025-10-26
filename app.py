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
    """Aplica tema customizado com suporte a modo claro/escuro"""

    # Cores baseadas no tema
    if theme_mode == 'light':
        bg_color = '#FFFFFF'
        text_color = '#000000'
        secondary_bg = '#F5F5F5'
        accent_color = '#E10600'  # Vermelho F1
        sidebar_bg = '#F8F8F8'
        card_bg = '#FAFAFA'
    else:  # dark
        bg_color = '#0E1117'
        text_color = '#FAFAFA'
        secondary_bg = '#262730'
        accent_color = '#E10600'  # Vermelho F1
        sidebar_bg = '#1E1E1E'
        card_bg = '#1C1C1C'

    st.markdown(f"""
        <style>
        /* Tema principal */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg};
        }}

        /* Ajustes sutis nas tabelas */
        .stDataFrame {{
            border-radius: 8px;
            background-color: {card_bg};
        }}

        /* Cards e metrics */
        [data-testid="stMetric"] {{
            background-color: {card_bg};
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid {accent_color}40;
        }}

        /* Melhor espaçamento */
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}

        /* Tabs mais bonitas */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: {secondary_bg};
            padding: 0.5rem;
            border-radius: 8px;
        }}

        .stTabs [data-baseweb="tab"] {{
            padding: 12px 24px;
            border-radius: 8px 8px 0 0;
            background-color: {card_bg};
        }}

        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background-color: {accent_color};
            color: white;
        }}

        /* Título com cor F1 */
        h1 {{
            color: {accent_color} !important;
        }}

        /* Dividers */
        hr {{
            border-color: {accent_color}40;
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
        """Renderiza sidebar"""
        with st.sidebar:
            st.title("🏁 F1 Dashboard")
            st.divider()

            # Switch de tema
            st.subheader("⚙️ Configurações")

            # Inicializar theme no session_state se não existir
            if 'theme' not in st.session_state:
                st.session_state.theme = 'dark'

            # Toggle de tema
            theme_label = "🌙 Modo Escuro" if st.session_state.theme == 'dark' else "☀️ Modo Claro"
            if st.button(theme_label, use_container_width=True):
                st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
                st.rerun()

            st.divider()

            st.subheader("Sobre")
            st.write("""
            Dashboard com dados da Fórmula 1, incluindo:
            - Resultados de corridas
            - Qualificações
            - Classificações de pilotos e construtores
            """)

            st.divider()

            st.caption("**Dados:** FastF1 API")
            st.caption("**Temporada:** 2025")
            st.caption("**Cache:** SQLite + API Local")

    def render_race_tab(self):
        """Renderiza aba de corrida"""
        st.header("Última Corrida")

        with st.spinner("Carregando dados da corrida..."):
            race_session = self.data_manager.get_latest_race()

            if race_session:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Grande Prêmio", race_session.event['EventName'])
                with col2:
                    st.metric("Localização", race_session.event['Location'])
                with col3:
                    # Formatar data em português brasileiro
                    data_corrida = race_session.date
                    data_formatada = data_corrida.strftime("%d/%m/%Y")
                    st.metric("Data", data_formatada)

                st.divider()

                df_race = self.data_manager.format_race_results(race_session)

                if df_race is not None:
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
        """Renderiza aba de qualificação"""
        st.header("Última Qualificação")

        with st.spinner("Carregando dados da qualificação..."):
            quali_session = self.data_manager.get_latest_qualifying()

            if quali_session:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Grande Prêmio", quali_session.event['EventName'])
                with col2:
                    st.metric("Localização", quali_session.event['Location'])
                with col3:
                    # Formatar data em português brasileiro
                    data_quali = quali_session.date
                    data_formatada = data_quali.strftime("%d/%m/%Y")
                    st.metric("Data", data_formatada)

                st.divider()

                df_quali = self.data_manager.format_qualifying_results(quali_session)

                if df_quali is not None:
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
        """Renderiza aba de classificação de pilotos"""
        st.header("Classificação de Pilotos 2025")

        with st.spinner("Carregando classificação..."):
            df_standings = self.data_manager.get_driver_standings()

            if df_standings is not None:
                # Top 3
                st.subheader("Pódio do Campeonato")

                col1, col2, col3 = st.columns(3)

                if len(df_standings) >= 1:
                    with col1:
                        pontos = df_standings.iloc[0]['Pontos']
                        st.metric(
                            "🥇 1º Lugar",
                            df_standings.iloc[0]['Piloto'],
                            f"{pontos} pts"
                        )
                        st.caption(df_standings.iloc[0]['Equipe'])

                if len(df_standings) >= 2:
                    with col2:
                        pontos = df_standings.iloc[1]['Pontos']
                        st.metric(
                            "🥈 2º Lugar",
                            df_standings.iloc[1]['Piloto'],
                            f"{pontos} pts"
                        )
                        st.caption(df_standings.iloc[1]['Equipe'])

                if len(df_standings) >= 3:
                    with col3:
                        pontos = df_standings.iloc[2]['Pontos']
                        st.metric(
                            "🥉 3º Lugar",
                            df_standings.iloc[2]['Piloto'],
                            f"{pontos} pts"
                        )
                        st.caption(df_standings.iloc[2]['Equipe'])

                st.divider()

                # Tabela completa
                st.subheader("Classificação Completa")

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
        """Renderiza aba de classificação de construtores"""
        st.header("Classificação de Construtores 2025")

        with st.spinner("Carregando classificação..."):
            df_standings = self.data_manager.get_constructor_standings()

            if df_standings is not None:
                # Top 3
                st.subheader("Pódio do Campeonato")

                col1, col2, col3 = st.columns(3)

                if len(df_standings) >= 1:
                    with col1:
                        pontos = df_standings.iloc[0]['Pontos']
                        vitorias = df_standings.iloc[0]['Vitórias']
                        st.metric(
                            "🥇 1º Lugar",
                            df_standings.iloc[0]['Equipe'],
                            f"{pontos} pts"
                        )
                        st.caption(f"{vitorias} vitórias")

                if len(df_standings) >= 2:
                    with col2:
                        pontos = df_standings.iloc[1]['Pontos']
                        vitorias = df_standings.iloc[1]['Vitórias']
                        st.metric(
                            "🥈 2º Lugar",
                            df_standings.iloc[1]['Equipe'],
                            f"{pontos} pts"
                        )
                        st.caption(f"{vitorias} vitórias")

                if len(df_standings) >= 3:
                    with col3:
                        pontos = df_standings.iloc[2]['Pontos']
                        vitorias = df_standings.iloc[2]['Vitórias']
                        st.metric(
                            "🥉 3º Lugar",
                            df_standings.iloc[2]['Equipe'],
                            f"{pontos} pts"
                        )
                        st.caption(f"{vitorias} vitórias")

                st.divider()

                # Tabela completa
                st.subheader("Classificação Completa")

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

        # Título principal
        st.title("🏎️ Fórmula 1 Dashboard")
        st.caption("Acompanhe resultados e classificações da temporada 2025")

        st.divider()

        # Sidebar
        self.render_sidebar()

        # Tabs principais
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
